"""Minimal candidate discovery experiment on Spurious GridWorld.

Pipeline per seed:
  1. Train or load an oracle policy on a tabular spurious environment.
  2. Distill or load a MoET surrogate.
  3. Rank candidate features with several discovery baselines.
  4. Connect the selected top candidate to PerformanceCheck-style intervention.

Usage:
    python experiments/entrypoints/run_gridworld_candidate_discovery.py \
        --config experiments/configs/exp001_gridworld_candidate_discovery.yaml
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from stable_baselines3 import DQN

from experiments.src.candidate_discovery import rank_candidates
from experiments.src.distill import distill
from experiments.src.evaluate import action_agreement, evaluate_rollout
from experiments.src.gridworld_env import SpuriousGridWorld
from experiments.src.moet import SoftMoET

SPURIOUS_IDX = 2


def _feature_names(n_noise: int) -> list[str]:
    return ["agent_x", "agent_y", "c_spurious"] + [f"noise_{i}" for i in range(n_noise)]


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _config_hash(cfg: dict) -> str:
    return json.dumps(cfg, sort_keys=True, ensure_ascii=False).encode("utf-8").hex()[:32]


def _estimate_minutes_per_seed(cfg: dict) -> float:
    runtime_cfg = cfg.get("runtime", {})
    explicit = runtime_cfg.get("estimated_minutes_per_seed")
    if explicit is not None:
        return float(explicit)

    oracle_steps = cfg["oracle"]["n_steps"]
    distill_samples = cfg["surrogate"]["n_distill_samples"]
    distill_epochs = cfg["surrogate"]["distill_epochs"]
    n_eval_samples = cfg["evaluation"]["n_eval_samples"]
    n_eval_episodes = cfg["evaluation"]["n_eval_episodes"]
    n_features = 3 + cfg["env"]["n_noise"]
    max_steps = cfg["env"]["max_steps"]

    seconds = 0.0
    seconds += oracle_steps / 6000.0
    seconds += (distill_samples * distill_epochs) / 45000.0
    seconds += n_eval_samples / 700.0
    seconds += (n_eval_episodes * n_features * max_steps) / 3500.0
    return max(1.0, seconds / 60.0)


def _estimate_remaining_minutes(cfg: dict, remaining_seeds: int, n_workers: int) -> float:
    return _estimate_minutes_per_seed(cfg) * remaining_seeds / max(1, n_workers)


def _make_env(cfg: dict, eval_mode: str | None = None) -> SpuriousGridWorld:
    env_cfg = cfg["env"]
    return SpuriousGridWorld(
        spurious_p=env_cfg["spurious_p"],
        grid_size=env_cfg["grid_size"],
        max_steps=env_cfg["max_steps"],
        eval_mode=eval_mode,
        n_noise=env_cfg["n_noise"],
    )


def _oracle_paths(output_dir: Path, seed: int) -> tuple[Path, Path]:
    ckpt_dir = output_dir / "checkpoints" / "oracle"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    return ckpt_dir / f"seed_{seed:03d}.zip", ckpt_dir / f"seed_{seed:03d}.meta.json"


def _surrogate_paths(output_dir: Path, seed: int) -> tuple[Path, Path]:
    ckpt_dir = output_dir / "checkpoints" / "surrogate"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    return ckpt_dir / f"seed_{seed:03d}.pkl", ckpt_dir / f"seed_{seed:03d}.meta.json"


def _seed_log_path(output_dir: Path, seed: int) -> Path:
    log_dir = output_dir / "seed_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"seed_{seed:03d}.log"


def _save_oracle(model: DQN, cfg: dict, output_dir: Path, seed: int) -> Path:
    model_path, meta_path = _oracle_paths(output_dir, seed)
    model.save(str(model_path))
    meta = {
        "seed": int(seed),
        "saved_at": _now_str(),
        "config_hash": _config_hash(cfg),
        "path": str(model_path).replace("\\", "/"),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return model_path


def _load_oracle_if_available(cfg: dict, output_dir: Path, seed: int) -> DQN | None:
    model_path, meta_path = _oracle_paths(output_dir, seed)
    if not model_path.exists() or not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if meta.get("config_hash") != _config_hash(cfg):
        return None
    return DQN.load(str(model_path))


def _save_surrogate(model: SoftMoET, cfg: dict, output_dir: Path, seed: int) -> Path:
    model_path, meta_path = _surrogate_paths(output_dir, seed)
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    meta = {
        "seed": int(seed),
        "saved_at": _now_str(),
        "config_hash": _config_hash(cfg),
        "path": str(model_path).replace("\\", "/"),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return model_path


def _load_surrogate_if_available(cfg: dict, output_dir: Path, seed: int) -> SoftMoET | None:
    model_path, meta_path = _surrogate_paths(output_dir, seed)
    if not model_path.exists() or not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if meta.get("config_hash") != _config_hash(cfg):
        return None
    with open(model_path, "rb") as f:
        return pickle.load(f)


def _train_oracle(seed: int, cfg: dict) -> DQN:
    env = _make_env(cfg)
    model = DQN("MlpPolicy", env, seed=seed, verbose=0, learning_starts=1000)
    model.learn(total_timesteps=cfg["oracle"]["n_steps"])
    env.close()
    return model


def _collect_transitions(
    model: DQN,
    cfg: dict,
    seed: int,
    n_samples: int,
) -> tuple[np.ndarray, np.ndarray]:
    env = _make_env(cfg)
    obs_list, act_list = [], []
    obs, _ = env.reset(seed=seed)
    while len(obs_list) < n_samples:
        action, _ = model.predict(obs, deterministic=True)
        obs_list.append(obs.copy())
        act_list.append(int(action))
        obs, _, terminated, truncated, _ = env.step(int(action))
        if terminated or truncated:
            obs, _ = env.reset()
    env.close()
    return np.asarray(obs_list, dtype=np.float32), np.asarray(act_list, dtype=np.int64)


def _eval_intervention(
    surrogate: SoftMoET,
    cfg: dict,
    feature_idx: int,
    n_episodes: int,
    seed: int,
) -> float:
    rng = np.random.default_rng(seed + 17)
    env = _make_env(cfg)
    total_reward = 0.0
    for ep in range(n_episodes):
        obs, _ = env.reset(seed=seed + ep)
        done = False
        while not done:
            obs_p = obs.copy()
            obs_p[feature_idx] = float(rng.uniform(0.0, 1.0))
            action = int(surrogate.predict(obs_p[np.newaxis])[0])
            obs, reward, terminated, truncated, _ = env.step(action)
            total_reward += reward
            done = terminated or truncated
    env.close()
    return total_reward / n_episodes


def _performance_check_profile(surrogate: SoftMoET, cfg: dict, seed: int) -> dict[str, float]:
    feat_names = _feature_names(cfg["env"]["n_noise"])
    n_episodes = cfg["evaluation"]["n_eval_episodes"]

    train_env = _make_env(cfg)
    j_s_train = evaluate_rollout(surrogate, train_env, n_episodes, seed + 20_000)
    train_env.close()

    deltas: dict[str, float] = {}
    for idx, feat_name in enumerate(feat_names):
        perturbed = _eval_intervention(surrogate, cfg, idx, n_episodes, seed + 30_000 + idx * 1000)
        deltas[feat_name] = float(j_s_train - perturbed)
    deltas["j_s_train"] = float(j_s_train)
    return deltas


def _rank_position(ordered_features: list[str], target: str) -> int:
    return int(ordered_features.index(target) + 1)


def _load_or_build_oracle(seed: int, cfg: dict, output_dir: Path, logs: list[str]) -> tuple[DQN, Path]:
    cached = _load_oracle_if_available(cfg, output_dir, seed)
    if cached is not None:
        logs.append("  [1/5] Oracle load from checkpoint...")
        path, _ = _oracle_paths(output_dir, seed)
        return cached, path
    logs.append("  [1/5] Oracle training...")
    oracle = _train_oracle(seed, cfg)
    path = _save_oracle(oracle, cfg, output_dir, seed)
    logs.append(f"    Saved oracle: {path}")
    return oracle, path


def _load_or_build_surrogate(
    seed: int,
    cfg: dict,
    output_dir: Path,
    oracle: DQN,
    n_obs: int,
    obs_distill: np.ndarray,
    act_distill: np.ndarray,
    logs: list[str],
) -> tuple[SoftMoET, Path]:
    cached = _load_surrogate_if_available(cfg, output_dir, seed)
    if cached is not None:
        logs.append("  [3/5] Surrogate load from checkpoint...")
        path, _ = _surrogate_paths(output_dir, seed)
        return cached, path
    logs.append("  [3/5] Surrogate distillation...")
    surrogate = SoftMoET(n_obs, 4, cfg["surrogate"]["n_experts"], cfg["surrogate"]["max_depth"])
    surrogate = distill(
        surrogate,
        obs_distill,
        act_distill,
        epochs=cfg["surrogate"]["distill_epochs"],
    )
    path = _save_surrogate(surrogate, cfg, output_dir, seed)
    logs.append(f"    Saved surrogate: {path}")
    return surrogate, path


def run_one_seed(seed: int, cfg: dict, output_dir: str) -> tuple[list[dict], list[str]]:
    outdir = Path(output_dir)
    logs = [f"\n{'=' * 60}", f"Seed {seed}", f"{'=' * 60}"]
    feat_names = _feature_names(cfg["env"]["n_noise"])
    n_obs = len(feat_names)
    n_eval = cfg["evaluation"]["n_eval_samples"]
    n_distill = cfg["surrogate"]["n_distill_samples"]
    methods = cfg["candidate_discovery"]["methods"]
    top_k = cfg["candidate_discovery"]["top_k"]
    t0 = time.time()

    oracle, oracle_path = _load_or_build_oracle(seed, cfg, outdir, logs)

    logs.append("  [2/5] Data collection...")
    obs_distill, act_distill = _collect_transitions(oracle, cfg, seed, n_distill)
    obs_eval, _ = _collect_transitions(oracle, cfg, seed + 10_000, n_eval)

    surrogate, surrogate_path = _load_or_build_surrogate(
        seed, cfg, outdir, oracle, n_obs, obs_distill, act_distill, logs
    )

    oracle_actions, _ = oracle.predict(obs_eval, deterministic=True)
    aa_train = action_agreement(obs_eval, oracle_actions, surrogate)
    logs.append(f"    Stage 1 agreement: AA={aa_train:.3f}")

    logs.append("  [4/5] PerformanceCheck profile...")
    pc_profile = _performance_check_profile(surrogate, cfg, seed)
    spurious_name = feat_names[SPURIOUS_IDX]
    ordered_pc = sorted(
        ((name, score) for name, score in pc_profile.items() if name != "j_s_train"),
        key=lambda item: (-item[1], item[0]),
    )
    logs.append(
        "    PerformanceCheck top deltas: "
        + ", ".join(f"{name}={score:.3f}" for name, score in ordered_pc[:3])
    )

    logs.append("  [5/5] Candidate discovery ranking...")
    results: list[dict] = []
    for method_idx, method in enumerate(methods):
        ranking = rank_candidates(method, obs_eval, oracle_actions, feat_names, seed + method_idx * 100)
        top_feature = ranking.top_feature
        record = {
            "seed": seed,
            "method": method,
            "aa_train": aa_train,
            "j_s_train": pc_profile["j_s_train"],
            "oracle_checkpoint": str(oracle_path).replace("\\", "/"),
            "surrogate_checkpoint": str(surrogate_path).replace("\\", "/"),
            "selected_feature": top_feature,
            "selected_score": ranking.scores[top_feature],
            "selected_pc_delta": pc_profile[top_feature],
            "selected_pc_rank": _rank_position([name for name, _ in ordered_pc], top_feature),
            "spurious_feature": spurious_name,
            "spurious_rank": _rank_position(ranking.ordered_features, spurious_name),
            "spurious_score": ranking.scores[spurious_name],
            "spurious_pc_delta": pc_profile[spurious_name],
            "top1_hit": top_feature == spurious_name,
            "topk_hit": _rank_position(ranking.ordered_features, spurious_name) <= top_k,
            "pc_top1_alignment": top_feature == ordered_pc[0][0],
            "seed_elapsed_sec": time.time() - t0,
        }
        for feat_name in feat_names:
            record[f"score_{feat_name}"] = ranking.scores[feat_name]
            record[f"pc_delta_{feat_name}"] = pc_profile[feat_name]
        results.append(record)
        logs.append(
            f"    {method}: top={top_feature}, spurious_rank={record['spurious_rank']}, "
            f"top1_hit={record['top1_hit']}, pc_rank={record['selected_pc_rank']}"
        )

    logs.append(f"    Seed elapsed: {time.time() - t0:.1f} sec")
    return results, logs


def _save_seed_log(output_dir: Path, seed: int, logs: list[str]) -> None:
    _seed_log_path(output_dir, seed).write_text("\n".join(logs) + "\n", encoding="utf-8")


def _save_records(records: list[dict], path: Path) -> pd.DataFrame:
    df = pd.DataFrame(records)
    if df.empty:
        df.to_csv(path, index=False)
        return df
    df = df.drop_duplicates(subset=["seed", "method"], keep="last")
    df = df.sort_values(["seed", "method"]).reset_index(drop=True)
    df.to_csv(path, index=False)
    return df


def _completed_seeds(df: pd.DataFrame, methods: list[str]) -> set[int]:
    if df.empty:
        return set()
    completed = set()
    for seed, group in df.groupby("seed"):
        if set(group["method"].tolist()) == set(methods):
            completed.add(int(seed))
    return completed


def _update_meta(
    meta_path: Path,
    cfg: dict,
    state: str,
    output_dir: Path,
    session_id: str,
    started_at: str,
    planned_seeds: list[int],
    completed_seeds: list[int],
    n_workers: int,
    estimate_minutes: float,
    no_resume: bool,
    completed_at: str | None = None,
) -> None:
    meta = {
        "experiment": cfg["name"],
        "state": state,
        "session_id": session_id,
        "started_at": started_at,
        "completed_at": completed_at,
        "output_dir": str(output_dir).replace("\\", "/"),
        "config_hash": _config_hash(cfg),
        "resume_enabled": not no_resume,
        "planned_seeds": planned_seeds,
        "completed_seeds": completed_seeds,
        "n_workers": int(n_workers),
        "estimated_minutes_total": float(estimate_minutes),
        "estimated_minutes_per_seed": float(_estimate_minutes_per_seed(cfg)),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def _append_runtime_session(
    runtime_path: Path,
    session_id: str,
    started_at: str,
    ended_at: str,
    elapsed_sec: float,
    state: str,
    completed_seed_count: int,
    planned_seed_count: int,
    note: str,
) -> None:
    record = {
        "session_id": session_id,
        "started_at": started_at,
        "ended_at": ended_at,
        "elapsed_sec": round(elapsed_sec, 3),
        "elapsed_hms": time.strftime("%H:%M:%S", time.gmtime(max(0.0, elapsed_sec))),
        "state": state,
        "completed_seeds": int(completed_seed_count),
        "planned_seeds": int(planned_seed_count),
        "note": note,
    }
    if runtime_path.exists():
        df = pd.read_csv(runtime_path)
        df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    else:
        df = pd.DataFrame([record])
    df.to_csv(runtime_path, index=False)


def _save_summary(df: pd.DataFrame, cfg: dict, output_dir: Path, elapsed_sec: float) -> None:
    methods = cfg["candidate_discovery"]["methods"]
    lines = [
        f"=== {cfg['name']} ===",
        cfg.get("description", ""),
        "",
        f"Seeds   : {sorted(df['seed'].unique().tolist()) if not df.empty else []}",
        f"Methods : {methods}",
        f"Env     : p={cfg['env']['spurious_p']}, n_noise={cfg['env']['n_noise']}, grid={cfg['env']['grid_size']}",
        f"Elapsed : {elapsed_sec / 60.0:.1f} min",
        "",
        f"{'method':<18} | {'top1':>6} | {'topk':>6} | {'mean rank':>9} | {'pc top1':>7}",
        "-" * 62,
    ]
    for method in methods:
        sub = df[df["method"] == method]
        if sub.empty:
            continue
        lines.append(
            f"{method:<18} | "
            f"{sub['top1_hit'].mean():>6.0%} | "
            f"{sub['topk_hit'].mean():>6.0%} | "
            f"{sub['spurious_rank'].mean():>9.2f} | "
            f"{sub['pc_top1_alignment'].mean():>7.0%}"
        )
    (output_dir / "summary.txt").write_text("\n".join(lines), encoding="utf-8")


def _plot(df: pd.DataFrame, cfg: dict, output_dir: Path) -> None:
    if df.empty:
        return
    methods = cfg["candidate_discovery"]["methods"]
    top1 = [df[df["method"] == method]["top1_hit"].mean() for method in methods]
    topk = [df[df["method"] == method]["topk_hit"].mean() for method in methods]
    ranks = [df[df["method"] == method]["spurious_rank"].mean() for method in methods]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    x = np.arange(len(methods))
    width = 0.35
    axes[0].bar(x - width / 2, top1, width, label="top-1 hit", color="steelblue")
    axes[0].bar(x + width / 2, topk, width, label=f"top-{cfg['candidate_discovery']['top_k']} hit", color="seagreen")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(methods, rotation=15, ha="right")
    axes[0].set_ylim(0.0, 1.05)
    axes[0].set_ylabel("Rate")
    axes[0].set_title("Spurious candidate recovery")
    axes[0].legend()

    axes[1].bar(methods, ranks, color="tomato")
    axes[1].axhline(1.0, color="black", linestyle="--", linewidth=0.8)
    axes[1].set_ylabel("Average rank of true spurious feature")
    axes[1].set_title("Lower is better")
    axes[1].tick_params(axis="x", rotation=15)

    plt.tight_layout()
    plt.savefig(output_dir / "results.png", dpi=140)
    plt.close(fig)


def _worker(args):
    seed, cfg, output_dir = args
    return run_one_seed(seed, cfg, output_dir)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--outdir", default=None)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    output_dir = ROOT / (args.outdir or cfg["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    partial_path = output_dir / "results_partial.csv"
    results_path = output_dir / "results.csv"
    runtime_path = output_dir / "runtime_sessions.csv"
    meta_path = output_dir / "meta.json"

    seeds = [int(seed) for seed in cfg["evaluation"]["seeds"]]
    methods = cfg["candidate_discovery"]["methods"]
    n_workers = int(cfg.get("n_workers", 1))
    if os.name == "nt" and n_workers > 1:
        # Windows sandboxed runs can reject multiprocessing IPC. Keep the user-configured
        # value in metadata but fall back only when required by the current session.
        pass

    existing_records: list[dict] = []
    completed = set()
    if partial_path.exists() and not args.no_resume:
        try:
            existing_df = pd.read_csv(partial_path)
            if not existing_df.empty:
                existing_records = existing_df.to_dict("records")
                completed = _completed_seeds(existing_df, methods)
                print(f"[RESUME] loaded {len(existing_records)} rows from {partial_path}", flush=True)
        except Exception as e:
            print(f"[RESUME] failed to load partial results: {e}", flush=True)
    elif args.no_resume and partial_path.exists():
        print(f"[NO-RESUME] ignoring existing {partial_path}", flush=True)

    pending = [seed for seed in seeds if seed not in completed]
    estimate_remaining = _estimate_remaining_minutes(cfg, len(pending), n_workers)
    session_id = f"{cfg['name']}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    started_at = _now_str()

    print(f"Experiment : {cfg['name']}", flush=True)
    print(f"Outdir     : {output_dir}", flush=True)
    print(f"Seeds      : {seeds}", flush=True)
    print(f"Pending    : {pending}", flush=True)
    print(f"Workers    : {n_workers}", flush=True)
    print(f"Estimated remaining runtime: {estimate_remaining:.1f} minutes", flush=True)

    _update_meta(
        meta_path=meta_path,
        cfg=cfg,
        state="running",
        output_dir=output_dir,
        session_id=session_id,
        started_at=started_at,
        planned_seeds=seeds,
        completed_seeds=sorted(completed),
        n_workers=n_workers,
        estimate_minutes=estimate_remaining,
        no_resume=args.no_resume,
    )

    t0 = time.time()
    records = list(existing_records)
    all_logs: dict[int, list[str]] = {}

    if n_workers <= 1:
        for seed in pending:
            seed_records, logs = run_one_seed(seed, cfg, str(output_dir))
            records.extend(seed_records)
            all_logs[seed] = logs
            df_partial = _save_records(records, partial_path)
            _save_seed_log(output_dir, seed, logs)
            _update_meta(
                meta_path=meta_path,
                cfg=cfg,
                state="running",
                output_dir=output_dir,
                session_id=session_id,
                started_at=started_at,
                planned_seeds=seeds,
                completed_seeds=sorted(_completed_seeds(df_partial, methods)),
                n_workers=n_workers,
                estimate_minutes=estimate_remaining,
                no_resume=args.no_resume,
            )
            print(f"[DONE] seed={seed}", flush=True)
    else:
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            futures = {executor.submit(_worker, (seed, cfg, str(output_dir))): seed for seed in pending}
            for future in as_completed(futures):
                seed = futures[future]
                seed_records, logs = future.result()
                records.extend(seed_records)
                all_logs[seed] = logs
                df_partial = _save_records(records, partial_path)
                _save_seed_log(output_dir, seed, logs)
                _update_meta(
                    meta_path=meta_path,
                    cfg=cfg,
                    state="running",
                    output_dir=output_dir,
                    session_id=session_id,
                    started_at=started_at,
                    planned_seeds=seeds,
                    completed_seeds=sorted(_completed_seeds(df_partial, methods)),
                    n_workers=n_workers,
                    estimate_minutes=estimate_remaining,
                    no_resume=args.no_resume,
                )
                print(f"[DONE] seed={seed}", flush=True)

    for seed in sorted(all_logs):
        for line in all_logs[seed]:
            print(line, flush=True)

    final_df = _save_records(records, results_path)
    _save_summary(final_df, cfg, output_dir, elapsed_sec=time.time() - t0)
    _plot(final_df, cfg, output_dir)

    ended_at = _now_str()
    elapsed_sec = time.time() - t0
    completed_final = sorted(_completed_seeds(final_df, methods))
    _update_meta(
        meta_path=meta_path,
        cfg=cfg,
        state="completed",
        output_dir=output_dir,
        session_id=session_id,
        started_at=started_at,
        planned_seeds=seeds,
        completed_seeds=completed_final,
        n_workers=n_workers,
        estimate_minutes=estimate_remaining,
        no_resume=args.no_resume,
        completed_at=ended_at,
    )
    _append_runtime_session(
        runtime_path=runtime_path,
        session_id=session_id,
        started_at=started_at,
        ended_at=ended_at,
        elapsed_sec=elapsed_sec,
        state="completed",
        completed_seed_count=len(completed_final),
        planned_seed_count=len(seeds),
        note="Main experiment session.",
    )

    print(f"\nResults: {output_dir}", flush=True)
    print(f"Elapsed: {elapsed_sec / 60.0:.1f} minutes", flush=True)


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    main()
