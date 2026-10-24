"""Sweep spurious_p and noise dimensions for candidate discovery on GridWorld.

Usage:
    python experiments/run_gridworld_candidate_discovery_noise_p_sweep.py \
        --config experiments/configs/exp024_gridworld_candidate_discovery_noise_p_sweep.yaml
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

ROOT = Path(__file__).parent.parent
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


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _config_hash(cfg: dict) -> str:
    return json.dumps(cfg, sort_keys=True, ensure_ascii=False).encode("utf-8").hex()[:32]


def _feature_names(n_noise: int) -> list[str]:
    return ["agent_x", "agent_y", "c_spurious"] + [f"noise_{i}" for i in range(n_noise)]


def _condition_slug(spurious_p: float, n_noise: int) -> str:
    p_tag = str(spurious_p).replace(".", "p")
    return f"p_{p_tag}__noise_{n_noise:02d}"


def _task_label(task: tuple[int, float, int]) -> str:
    seed, spurious_p, n_noise = task
    return f"seed={seed}, p={spurious_p:.2f}, noise={n_noise}"


def _estimate_minutes_per_task(cfg: dict, n_noise: int) -> float:
    runtime_cfg = cfg.get("runtime", {})
    explicit = runtime_cfg.get("estimated_minutes_per_task")
    if explicit is not None:
        return float(explicit)

    oracle_steps = cfg["oracle"]["n_steps"]
    distill_samples = cfg["surrogate"]["n_distill_samples"]
    distill_epochs = cfg["surrogate"]["distill_epochs"]
    n_eval_samples = cfg["evaluation"]["n_eval_samples"]
    n_eval_episodes = cfg["evaluation"]["n_eval_episodes"]
    max_steps = cfg["env"]["max_steps"]
    n_features = 3 + n_noise

    seconds = 0.0
    seconds += oracle_steps / 7000.0
    seconds += (distill_samples * distill_epochs) / 50000.0
    seconds += n_eval_samples / 900.0
    seconds += (n_eval_episodes * n_features * max_steps) / 4200.0
    return max(0.5, seconds / 60.0)


def _estimate_remaining_minutes(cfg: dict, tasks: list[tuple[int, float, int]], n_workers: int) -> float:
    total = sum(_estimate_minutes_per_task(cfg, n_noise) for _, _, n_noise in tasks)
    return total / max(1, n_workers)


def _make_env(cfg: dict, spurious_p: float, n_noise: int, eval_mode: str | None = None) -> SpuriousGridWorld:
    env_cfg = cfg["env"]
    return SpuriousGridWorld(
        spurious_p=spurious_p,
        grid_size=env_cfg["grid_size"],
        max_steps=env_cfg["max_steps"],
        eval_mode=eval_mode,
        n_noise=n_noise,
    )


def _oracle_paths(output_dir: Path, spurious_p: float, n_noise: int, seed: int) -> tuple[Path, Path]:
    cond_dir = output_dir / "checkpoints" / _condition_slug(spurious_p, n_noise) / "oracle"
    cond_dir.mkdir(parents=True, exist_ok=True)
    return cond_dir / f"seed_{seed:03d}.zip", cond_dir / f"seed_{seed:03d}.meta.json"


def _surrogate_paths(output_dir: Path, spurious_p: float, n_noise: int, seed: int) -> tuple[Path, Path]:
    cond_dir = output_dir / "checkpoints" / _condition_slug(spurious_p, n_noise) / "surrogate"
    cond_dir.mkdir(parents=True, exist_ok=True)
    return cond_dir / f"seed_{seed:03d}.pkl", cond_dir / f"seed_{seed:03d}.meta.json"


def _seed_log_path(output_dir: Path, spurious_p: float, n_noise: int, seed: int) -> Path:
    log_dir = output_dir / "seed_logs" / _condition_slug(spurious_p, n_noise)
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"seed_{seed:03d}.log"


def _save_oracle(model: DQN, cfg: dict, output_dir: Path, spurious_p: float, n_noise: int, seed: int) -> Path:
    model_path, meta_path = _oracle_paths(output_dir, spurious_p, n_noise, seed)
    model.save(str(model_path))
    meta = {
        "seed": int(seed),
        "spurious_p": float(spurious_p),
        "n_noise": int(n_noise),
        "saved_at": _now_str(),
        "config_hash": _config_hash(cfg),
        "path": str(model_path).replace("\\", "/"),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return model_path


def _load_oracle_if_available(cfg: dict, output_dir: Path, spurious_p: float, n_noise: int, seed: int) -> DQN | None:
    model_path, meta_path = _oracle_paths(output_dir, spurious_p, n_noise, seed)
    if not model_path.exists() or not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if meta.get("config_hash") != _config_hash(cfg):
        return None
    return DQN.load(str(model_path))


def _save_surrogate(
    model: SoftMoET,
    cfg: dict,
    output_dir: Path,
    spurious_p: float,
    n_noise: int,
    seed: int,
) -> Path:
    model_path, meta_path = _surrogate_paths(output_dir, spurious_p, n_noise, seed)
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    meta = {
        "seed": int(seed),
        "spurious_p": float(spurious_p),
        "n_noise": int(n_noise),
        "saved_at": _now_str(),
        "config_hash": _config_hash(cfg),
        "path": str(model_path).replace("\\", "/"),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return model_path


def _load_surrogate_if_available(
    cfg: dict,
    output_dir: Path,
    spurious_p: float,
    n_noise: int,
    seed: int,
) -> SoftMoET | None:
    model_path, meta_path = _surrogate_paths(output_dir, spurious_p, n_noise, seed)
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


def _train_oracle(seed: int, cfg: dict, spurious_p: float, n_noise: int) -> DQN:
    env = _make_env(cfg, spurious_p, n_noise)
    model = DQN("MlpPolicy", env, seed=seed, verbose=0, learning_starts=1000)
    model.learn(total_timesteps=cfg["oracle"]["n_steps"])
    env.close()
    return model


def _collect_transitions(
    model: DQN,
    cfg: dict,
    spurious_p: float,
    n_noise: int,
    seed: int,
    n_samples: int,
) -> tuple[np.ndarray, np.ndarray]:
    env = _make_env(cfg, spurious_p, n_noise)
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
    spurious_p: float,
    n_noise: int,
    feature_idx: int,
    n_episodes: int,
    seed: int,
) -> float:
    rng = np.random.default_rng(seed + 17)
    env = _make_env(cfg, spurious_p, n_noise)
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


def _performance_check_profile(
    surrogate: SoftMoET,
    cfg: dict,
    spurious_p: float,
    n_noise: int,
    seed: int,
) -> dict[str, float]:
    feat_names = _feature_names(n_noise)
    n_episodes = cfg["evaluation"]["n_eval_episodes"]

    train_env = _make_env(cfg, spurious_p, n_noise)
    j_s_train = evaluate_rollout(surrogate, train_env, n_episodes, seed + 20_000)
    train_env.close()

    deltas: dict[str, float] = {}
    for idx, feat_name in enumerate(feat_names):
        perturbed = _eval_intervention(
            surrogate, cfg, spurious_p, n_noise, idx, n_episodes, seed + 30_000 + idx * 1000
        )
        deltas[feat_name] = float(j_s_train - perturbed)
    deltas["j_s_train"] = float(j_s_train)
    return deltas


def _rank_position(ordered_features: list[str], target: str) -> int:
    return int(ordered_features.index(target) + 1)


def _load_or_build_oracle(
    seed: int,
    cfg: dict,
    output_dir: Path,
    spurious_p: float,
    n_noise: int,
    logs: list[str],
) -> tuple[DQN, Path]:
    cached = _load_oracle_if_available(cfg, output_dir, spurious_p, n_noise, seed)
    if cached is not None:
        logs.append("  [1/5] Oracle load from checkpoint...")
        path, _ = _oracle_paths(output_dir, spurious_p, n_noise, seed)
        return cached, path
    logs.append("  [1/5] Oracle training...")
    oracle = _train_oracle(seed, cfg, spurious_p, n_noise)
    path = _save_oracle(oracle, cfg, output_dir, spurious_p, n_noise, seed)
    logs.append(f"    Saved oracle: {path}")
    return oracle, path


def _load_or_build_surrogate(
    seed: int,
    cfg: dict,
    output_dir: Path,
    spurious_p: float,
    n_noise: int,
    n_obs: int,
    obs_distill: np.ndarray,
    act_distill: np.ndarray,
    logs: list[str],
) -> tuple[SoftMoET, Path]:
    cached = _load_surrogate_if_available(cfg, output_dir, spurious_p, n_noise, seed)
    if cached is not None:
        logs.append("  [3/5] Surrogate load from checkpoint...")
        path, _ = _surrogate_paths(output_dir, spurious_p, n_noise, seed)
        return cached, path
    logs.append("  [3/5] Surrogate distillation...")
    surrogate = SoftMoET(n_obs, 4, cfg["surrogate"]["n_experts"], cfg["surrogate"]["max_depth"])
    surrogate = distill(
        surrogate,
        obs_distill,
        act_distill,
        epochs=cfg["surrogate"]["distill_epochs"],
    )
    path = _save_surrogate(surrogate, cfg, output_dir, spurious_p, n_noise, seed)
    logs.append(f"    Saved surrogate: {path}")
    return surrogate, path


def run_one_task(seed: int, spurious_p: float, n_noise: int, cfg: dict, output_dir: str) -> tuple[list[dict], list[str]]:
    outdir = Path(output_dir)
    logs = [
        f"\n{'=' * 60}",
        f"Seed {seed} / p={spurious_p:.2f} / noise={n_noise}",
        f"{'=' * 60}",
    ]
    feat_names = _feature_names(n_noise)
    n_obs = len(feat_names)
    n_eval = cfg["evaluation"]["n_eval_samples"]
    n_distill = cfg["surrogate"]["n_distill_samples"]
    methods = cfg["candidate_discovery"]["methods"]
    top_k = cfg["candidate_discovery"]["top_k"]
    t0 = time.time()

    oracle, oracle_path = _load_or_build_oracle(seed, cfg, outdir, spurious_p, n_noise, logs)

    logs.append("  [2/5] Data collection...")
    obs_distill, act_distill = _collect_transitions(oracle, cfg, spurious_p, n_noise, seed, n_distill)
    obs_eval, _ = _collect_transitions(oracle, cfg, spurious_p, n_noise, seed + 10_000, n_eval)

    surrogate, surrogate_path = _load_or_build_surrogate(
        seed, cfg, outdir, spurious_p, n_noise, n_obs, obs_distill, act_distill, logs
    )

    oracle_actions, _ = oracle.predict(obs_eval, deterministic=True)
    aa_train = action_agreement(obs_eval, oracle_actions, surrogate)
    logs.append(f"    Stage 1 agreement: AA={aa_train:.3f}")

    logs.append("  [4/5] PerformanceCheck profile...")
    pc_profile = _performance_check_profile(surrogate, cfg, spurious_p, n_noise, seed)
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
    records: list[dict] = []
    for method_idx, method in enumerate(methods):
        ranking = rank_candidates(method, obs_eval, oracle_actions, feat_names, seed + method_idx * 100)
        top_feature = ranking.top_feature
        record = {
            "seed": int(seed),
            "spurious_p": float(spurious_p),
            "n_noise": int(n_noise),
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
            "task_elapsed_sec": time.time() - t0,
        }
        for feat_name in feat_names:
            record[f"score_{feat_name}"] = ranking.scores[feat_name]
            record[f"pc_delta_{feat_name}"] = pc_profile[feat_name]
        records.append(record)
        logs.append(
            f"    {method}: top={top_feature}, spurious_rank={record['spurious_rank']}, "
            f"top1_hit={record['top1_hit']}, pc_rank={record['selected_pc_rank']}"
        )

    logs.append(f"    Task elapsed: {time.time() - t0:.1f} sec")
    return records, logs


def _save_seed_log(output_dir: Path, spurious_p: float, n_noise: int, seed: int, logs: list[str]) -> None:
    _seed_log_path(output_dir, spurious_p, n_noise, seed).write_text("\n".join(logs) + "\n", encoding="utf-8")


def _save_records(records: list[dict], path: Path) -> pd.DataFrame:
    df = pd.DataFrame(records)
    if df.empty:
        df.to_csv(path, index=False)
        return df
    df = df.drop_duplicates(subset=["spurious_p", "n_noise", "seed", "method"], keep="last")
    df = df.sort_values(["spurious_p", "n_noise", "seed", "method"]).reset_index(drop=True)
    df.to_csv(path, index=False)
    return df


def _completed_tasks(df: pd.DataFrame, methods: list[str]) -> set[tuple[int, float, int]]:
    if df.empty:
        return set()
    completed: set[tuple[int, float, int]] = set()
    grouped = df.groupby(["seed", "spurious_p", "n_noise"])
    for (seed, spurious_p, n_noise), group in grouped:
        if set(group["method"].tolist()) == set(methods):
            completed.add((int(seed), float(spurious_p), int(n_noise)))
    return completed


def _update_meta(
    meta_path: Path,
    cfg: dict,
    state: str,
    output_dir: Path,
    session_id: str,
    started_at: str,
    planned_tasks: list[tuple[int, float, int]],
    completed_tasks: list[tuple[int, float, int]],
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
        "planned_tasks": [
            {"seed": s, "spurious_p": p, "n_noise": n} for s, p, n in planned_tasks
        ],
        "completed_tasks": [
            {"seed": s, "spurious_p": p, "n_noise": n} for s, p, n in completed_tasks
        ],
        "n_workers": int(n_workers),
        "estimated_minutes_total": float(estimate_minutes),
        "estimated_minutes_per_task": float(cfg.get("runtime", {}).get("estimated_minutes_per_task", 0.0)),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def _append_runtime_session(
    runtime_path: Path,
    session_id: str,
    started_at: str,
    ended_at: str,
    elapsed_sec: float,
    state: str,
    completed_task_count: int,
    planned_task_count: int,
    note: str,
) -> None:
    record = {
        "session_id": session_id,
        "started_at": started_at,
        "ended_at": ended_at,
        "elapsed_sec": round(elapsed_sec, 3),
        "elapsed_hms": time.strftime("%H:%M:%S", time.gmtime(max(0.0, elapsed_sec))),
        "state": state,
        "completed_tasks": int(completed_task_count),
        "planned_tasks": int(planned_task_count),
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
    p_values = cfg["env"]["p_values"]
    noise_values = cfg["env"]["n_noise_values"]
    lines = [
        f"=== {cfg['name']} ===",
        cfg.get("description", ""),
        "",
        f"Seeds    : {cfg['evaluation']['seeds']}",
        f"p_values : {p_values}",
        f"noise    : {noise_values}",
        f"Methods  : {methods}",
        f"Elapsed  : {elapsed_sec / 60.0:.1f} min",
        "",
    ]
    for method in methods:
        lines.append(f"[{method}]")
        lines.append(f"{'p':>5} | {'noise':>5} | {'top1':>6} | {'topk':>6} | {'mean rank':>9}")
        lines.append("-" * 44)
        sub = df[df["method"] == method]
        for spurious_p in p_values:
            for n_noise in noise_values:
                cond = sub[(sub["spurious_p"] == spurious_p) & (sub["n_noise"] == n_noise)]
                if cond.empty:
                    continue
                lines.append(
                    f"{spurious_p:>5.2f} | {n_noise:>5d} | "
                    f"{cond['top1_hit'].mean():>6.0%} | "
                    f"{cond['topk_hit'].mean():>6.0%} | "
                    f"{cond['spurious_rank'].mean():>9.2f}"
                )
        lines.append("")
    (output_dir / "summary.txt").write_text("\n".join(lines), encoding="utf-8")


def _plot(df: pd.DataFrame, cfg: dict, output_dir: Path) -> None:
    if df.empty:
        return
    methods = cfg["candidate_discovery"]["methods"]
    p_values = cfg["env"]["p_values"]
    noise_values = cfg["env"]["n_noise_values"]

    fig, axes = plt.subplots(len(methods), 2, figsize=(12, 3.5 * len(methods)))
    if len(methods) == 1:
        axes = np.array([axes])

    for row_idx, method in enumerate(methods):
        sub = df[df["method"] == method]
        top1_grid = np.zeros((len(noise_values), len(p_values)))
        rank_grid = np.zeros((len(noise_values), len(p_values)))
        for i, n_noise in enumerate(noise_values):
            for j, spurious_p in enumerate(p_values):
                cond = sub[(sub["spurious_p"] == spurious_p) & (sub["n_noise"] == n_noise)]
                if cond.empty:
                    top1_grid[i, j] = np.nan
                    rank_grid[i, j] = np.nan
                else:
                    top1_grid[i, j] = cond["top1_hit"].mean()
                    rank_grid[i, j] = cond["spurious_rank"].mean()

        ax = axes[row_idx, 0]
        im = ax.imshow(top1_grid, vmin=0.0, vmax=1.0, aspect="auto", cmap="viridis")
        ax.set_title(f"{method}: top-1 hit")
        ax.set_xticks(range(len(p_values)))
        ax.set_xticklabels([f"{p:.2f}" for p in p_values])
        ax.set_yticks(range(len(noise_values)))
        ax.set_yticklabels([str(n) for n in noise_values])
        ax.set_xlabel("spurious_p")
        ax.set_ylabel("n_noise")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

        ax = axes[row_idx, 1]
        im = ax.imshow(rank_grid, aspect="auto", cmap="magma_r")
        ax.set_title(f"{method}: mean rank")
        ax.set_xticks(range(len(p_values)))
        ax.set_xticklabels([f"{p:.2f}" for p in p_values])
        ax.set_yticks(range(len(noise_values)))
        ax.set_yticklabels([str(n) for n in noise_values])
        ax.set_xlabel("spurious_p")
        ax.set_ylabel("n_noise")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    plt.tight_layout()
    plt.savefig(output_dir / "results.png", dpi=140)
    plt.close(fig)


def _worker(args):
    seed, spurious_p, n_noise, cfg, output_dir = args
    return run_one_task(seed, spurious_p, n_noise, cfg, output_dir)


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
    p_values = [float(p) for p in cfg["env"]["p_values"]]
    noise_values = [int(n) for n in cfg["env"]["n_noise_values"]]
    methods = cfg["candidate_discovery"]["methods"]
    n_workers = int(cfg.get("n_workers", 1))
    tasks = [(seed, spurious_p, n_noise) for n_noise in noise_values for spurious_p in p_values for seed in seeds]

    existing_records: list[dict] = []
    completed = set()
    if partial_path.exists() and not args.no_resume:
        try:
            existing_df = pd.read_csv(partial_path)
            if not existing_df.empty:
                existing_records = existing_df.to_dict("records")
                completed = _completed_tasks(existing_df, methods)
                print(f"[RESUME] loaded {len(existing_records)} rows from {partial_path}", flush=True)
        except Exception as e:
            print(f"[RESUME] failed to load partial results: {e}", flush=True)
    elif args.no_resume and partial_path.exists():
        print(f"[NO-RESUME] ignoring existing {partial_path}", flush=True)

    pending = [task for task in tasks if task not in completed]
    estimate_remaining = _estimate_remaining_minutes(cfg, pending, n_workers)
    session_id = f"{cfg['name']}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    started_at = _now_str()

    print(f"Experiment : {cfg['name']}", flush=True)
    print(f"Outdir     : {output_dir}", flush=True)
    print(f"Seeds      : {seeds}", flush=True)
    print(f"p_values   : {p_values}", flush=True)
    print(f"n_noise    : {noise_values}", flush=True)
    print(f"Workers    : {n_workers}", flush=True)
    print(f"Pending    : {len(pending)} / {len(tasks)} tasks", flush=True)
    print(f"Estimated remaining runtime: {estimate_remaining:.1f} minutes", flush=True)

    _update_meta(
        meta_path=meta_path,
        cfg=cfg,
        state="running",
        output_dir=output_dir,
        session_id=session_id,
        started_at=started_at,
        planned_tasks=tasks,
        completed_tasks=sorted(completed),
        n_workers=n_workers,
        estimate_minutes=estimate_remaining,
        no_resume=args.no_resume,
    )

    t0 = time.time()
    records = list(existing_records)
    all_logs: dict[tuple[int, float, int], list[str]] = {}

    if n_workers <= 1:
        for task in pending:
            seed, spurious_p, n_noise = task
            task_records, logs = run_one_task(seed, spurious_p, n_noise, cfg, str(output_dir))
            records.extend(task_records)
            all_logs[task] = logs
            df_partial = _save_records(records, partial_path)
            _save_seed_log(output_dir, spurious_p, n_noise, seed, logs)
            _update_meta(
                meta_path=meta_path,
                cfg=cfg,
                state="running",
                output_dir=output_dir,
                session_id=session_id,
                started_at=started_at,
                planned_tasks=tasks,
                completed_tasks=sorted(_completed_tasks(df_partial, methods)),
                n_workers=n_workers,
                estimate_minutes=estimate_remaining,
                no_resume=args.no_resume,
            )
            print(f"[DONE] {_task_label(task)}", flush=True)
    else:
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            futures = {executor.submit(_worker, (*task, cfg, str(output_dir))): task for task in pending}
            for future in as_completed(futures):
                task = futures[future]
                seed, spurious_p, n_noise = task
                task_records, logs = future.result()
                records.extend(task_records)
                all_logs[task] = logs
                df_partial = _save_records(records, partial_path)
                _save_seed_log(output_dir, spurious_p, n_noise, seed, logs)
                _update_meta(
                    meta_path=meta_path,
                    cfg=cfg,
                    state="running",
                    output_dir=output_dir,
                    session_id=session_id,
                    started_at=started_at,
                    planned_tasks=tasks,
                    completed_tasks=sorted(_completed_tasks(df_partial, methods)),
                    n_workers=n_workers,
                    estimate_minutes=estimate_remaining,
                    no_resume=args.no_resume,
                )
                print(f"[DONE] {_task_label(task)}", flush=True)

    for task in sorted(all_logs):
        for line in all_logs[task]:
            print(line, flush=True)

    final_df = _save_records(records, results_path)
    _save_summary(final_df, cfg, output_dir, elapsed_sec=time.time() - t0)
    _plot(final_df, cfg, output_dir)

    ended_at = _now_str()
    elapsed_sec = time.time() - t0
    completed_final = sorted(_completed_tasks(final_df, methods))
    _update_meta(
        meta_path=meta_path,
        cfg=cfg,
        state="completed",
        output_dir=output_dir,
        session_id=session_id,
        started_at=started_at,
        planned_tasks=tasks,
        completed_tasks=completed_final,
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
        completed_task_count=len(completed_final),
        planned_task_count=len(tasks),
        note="Main sweep session.",
    )

    print(f"\nResults: {output_dir}", flush=True)
    print(f"Elapsed: {elapsed_sec / 60.0:.1f} minutes", flush=True)


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    main()
