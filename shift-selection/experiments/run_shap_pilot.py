"""SHAP-based shift auto-selection — pilot experiment.

Usage:
    python experiments/run_shap_pilot.py --config experiments/configs/exp001_shap_gridworld.yaml
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import shap
import torch
import yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from stable_baselines3 import DQN

from experiments.src.gridworld_env import SpuriousGridWorld
from experiments.src.moet import SoftMoET
from experiments.src.distill import distill
from experiments.src.evaluate import action_agreement, evaluate_rollout

FEATURE_NAMES = ["agent_x", "agent_y", "c (spurious)"]
SPURIOUS_IDX = 2

# ---------------------------------------------------------------------------
# Oracle
# ---------------------------------------------------------------------------

def _train_oracle(seed: int, cfg: dict) -> DQN:
    env = SpuriousGridWorld(spurious_p=cfg["env"]["spurious_p"])
    model = DQN("MlpPolicy", env, seed=seed, verbose=0, learning_starts=1000)
    model.learn(total_timesteps=cfg["oracle"]["n_steps"])
    env.close()
    return model


def _collect_transitions(
    model: DQN, spurious_p: float, seed: int, n_samples: int
) -> tuple[np.ndarray, np.ndarray]:
    env = SpuriousGridWorld(spurious_p=spurious_p)
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
    return np.array(obs_list, dtype=np.float32), np.array(act_list, dtype=np.int64)

# ---------------------------------------------------------------------------
# SHAP
# ---------------------------------------------------------------------------

def _compute_shap_ranking(
    model: DQN, obs: np.ndarray, shap_cfg: dict
) -> tuple[list[int], np.ndarray]:
    def q_fn(x: np.ndarray) -> np.ndarray:
        with torch.no_grad():
            return model.q_net(torch.FloatTensor(x)).numpy()

    n_features = obs.shape[1]
    bg   = obs[:shap_cfg["n_background"]]
    test = obs[:shap_cfg["n_eval"]]
    explainer = shap.KernelExplainer(q_fn, bg)
    shap_vals = explainer.shap_values(test, nsamples=shap_cfg["n_samples"], silent=True)

    if isinstance(shap_vals, list):
        stacked = np.stack([np.abs(np.array(sv, dtype=float)) for sv in shap_vals])
        mean_abs = stacked.mean(axis=(0, 1))
    else:
        arr = np.abs(np.array(shap_vals, dtype=float))
        feat_axes = [i for i, s in enumerate(arr.shape) if s == n_features]
        if feat_axes:
            feat_axis  = feat_axes[-1]
            other_axes = tuple(i for i in range(arr.ndim) if i != feat_axis)
            mean_abs   = arr.mean(axis=other_axes)
        else:
            mean_abs = arr.reshape(-1, n_features).mean(axis=0)

    mean_abs = mean_abs.flatten()[:n_features]
    ranking  = list(np.argsort(mean_abs)[::-1])
    return ranking, mean_abs

# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def _perturb_obs(obs: np.ndarray, feature_idx: int, mode: str) -> np.ndarray:
    out = obs.copy()
    if mode == "reversed":
        out[:, feature_idx] = 1.0 - out[:, feature_idx]
    elif mode == "random":
        lo, hi = float(obs[:, feature_idx].min()), float(obs[:, feature_idx].max())
        out[:, feature_idx] = np.random.uniform(lo, hi, len(obs)).astype(np.float32)
    return out


def _eval_c_shift(
    model: DQN,
    surrogate: SoftMoET,
    obs_base: np.ndarray,
    spurious_p: float,
    seed: int,
    n_episodes: int,
) -> dict:
    obs_p = _perturb_obs(obs_base, SPURIOUS_IDX, "reversed")
    oracle_actions, _ = model.predict(obs_p, deterministic=True)
    aa = action_agreement(obs_p, oracle_actions, surrogate)

    oracle_env = SpuriousGridWorld(spurious_p=spurious_p, eval_mode="reversed")
    j_oracle   = evaluate_rollout(model, oracle_env, n_episodes, seed)
    oracle_env.close()

    surr_env = SpuriousGridWorld(spurious_p=spurious_p, eval_mode="reversed")
    j_s      = evaluate_rollout(surrogate, surr_env, n_episodes, seed)
    surr_env.close()

    return {"aa": aa, "j_oracle": j_oracle, "j_s": j_s}


def _eval_position_shift(
    model: DQN, surrogate: SoftMoET, obs_base: np.ndarray, feature_idx: int
) -> float:
    obs_p = _perturb_obs(obs_base, feature_idx, "random")
    oracle_actions, _ = model.predict(obs_p, deterministic=True)
    return action_agreement(obs_p, oracle_actions, surrogate)

# ---------------------------------------------------------------------------
# Single-seed pipeline  (top-level so ProcessPoolExecutor can pickle it)
# ---------------------------------------------------------------------------

def run_one_seed(seed: int, cfg: dict) -> tuple[dict, list[str]]:
    """1 seed 分のパイプラインを実行し (result_dict, log_lines) を返す。"""
    logs: list[str] = [f"\n{'='*60}", f"Seed {seed}", f"{'='*60}"]

    spurious_p  = cfg["env"]["spurious_p"]
    n_episodes  = cfg["evaluation"]["n_eval_episodes"]
    n_eval      = cfg["evaluation"]["n_eval_samples"]
    n_distill   = cfg["surrogate"]["n_distill_samples"]

    logs.append("  [1/5] Oracle training...")
    model = _train_oracle(seed, cfg)

    logs.append("  [2/5] Data collection...")
    obs_distill, act_distill = _collect_transitions(model, spurious_p, seed,          n_distill)
    obs_eval, _              = _collect_transitions(model, spurious_p, seed + 10_000, n_eval)

    logs.append("  [3/5] SHAP analysis...")
    ranking, mean_abs = _compute_shap_ranking(model, obs_eval, cfg["shap"])
    top_idx      = ranking[0]
    shap_correct = (top_idx == SPURIOUS_IDX)
    logs.append(f"    Ranking : {[FEATURE_NAMES[i] for i in ranking]}")
    logs.append(f"    Mean |SHAP|: " + ", ".join(f"{FEATURE_NAMES[i]}={mean_abs[i]:.4f}" for i in range(3)))
    logs.append(f"    Auto-selected: {FEATURE_NAMES[top_idx]} -> {'CORRECT (c)' if shap_correct else 'WRONG'}")

    logs.append("  [4/5] Surrogate training (MoET)...")
    moet = SoftMoET(3, 4, cfg["surrogate"]["n_experts"], cfg["surrogate"]["max_depth"])
    moet = distill(moet, obs_distill, act_distill, epochs=cfg["surrogate"]["distill_epochs"])

    oracle_actions_train, _ = model.predict(obs_eval, deterministic=True)
    aa_train    = action_agreement(obs_eval, oracle_actions_train, moet)
    train_env   = SpuriousGridWorld(spurious_p=spurious_p)
    j_oracle_tr = evaluate_rollout(model,   train_env, n_episodes, seed + 20_000)
    j_s_train   = evaluate_rollout(moet,    train_env, n_episodes, seed + 20_000)
    train_env.close()
    stage1_pass = aa_train >= 0.9
    logs.append(f"  [5/5] Stage 1: AA={aa_train:.3f} ({'PASS' if stage1_pass else 'FAIL'}), "
                f"J_oracle={j_oracle_tr:.3f}, J_S={j_s_train:.3f}")

    res_c     = _eval_c_shift(model, moet, obs_eval, spurious_p, seed + 30_000, n_episodes)
    c_collapse = j_s_train > 0 and res_c["j_s"] < 0.5 * j_s_train
    logs.append(f"    Stage 2 (c reversed): AA={res_c['aa']:.3f}, "
                f"J_oracle={res_c['j_oracle']:.3f}, J_S={res_c['j_s']:.3f} "
                f"-> {'COLLAPSE DETECTED' if c_collapse else 'no collapse'}")

    aa_x = _eval_position_shift(model, moet, obs_eval, 0)
    aa_y = _eval_position_shift(model, moet, obs_eval, 1)
    logs.append(f"    Control (x random): AA={aa_x:.3f}")
    logs.append(f"    Control (y random): AA={aa_y:.3f}")

    result = {
        "seed": seed,
        "shap_rank_1st": FEATURE_NAMES[ranking[0]],
        "shap_rank_2nd": FEATURE_NAMES[ranking[1]],
        "shap_rank_3rd": FEATURE_NAMES[ranking[2]],
        "shap_c": float(mean_abs[SPURIOUS_IDX]),
        "shap_x": float(mean_abs[0]),
        "shap_y": float(mean_abs[1]),
        "shap_correct": shap_correct,
        "aa_train":       aa_train,
        "stage1_pass":    stage1_pass,
        "j_oracle_train": j_oracle_tr,
        "j_s_train":      j_s_train,
        "aa_c_reversed":       res_c["aa"],
        "j_oracle_c_reversed": res_c["j_oracle"],
        "j_s_c_reversed":      res_c["j_s"],
        "c_collapse":  c_collapse,
        "aa_x_random": aa_x,
        "aa_y_random": aa_y,
    }
    return result, logs

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    output_dir = ROOT / cfg["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    seeds    = cfg["evaluation"]["seeds"]
    n_workers = cfg.get("n_workers", 4)

    print(f"Experiment : {cfg.get('name', 'unknown')}")
    print(f"Seeds      : {seeds}")
    print(f"Workers    : {n_workers}")

    records: list[dict] = []
    seed_logs: dict[int, list[str]] = {}

    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = {executor.submit(run_one_seed, s, cfg): s for s in seeds}
        for future in as_completed(futures):
            seed = futures[future]
            rec, logs = future.result()
            records.append(rec)
            seed_logs[seed] = logs
            print(f"[DONE] seed={seed}: SHAP_1st={rec['shap_rank_1st']}, "
                  f"AA_train={rec['aa_train']:.3f}, Stage1={'PASS' if rec['stage1_pass'] else 'FAIL'}, "
                  f"collapse={rec['c_collapse']}")

    for seed in sorted(seed_logs):
        for line in seed_logs[seed]:
            print(line)

    df = pd.DataFrame(records).sort_values("seed").reset_index(drop=True)
    df.to_csv(output_dir / "results.csv", index=False)

    _print_summary(df)
    _save_summary_txt(df, cfg, output_dir)
    _plot(df, output_dir)
    print(f"\nResults: {output_dir}")


def _print_summary(df: pd.DataFrame) -> None:
    n = len(df)
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Stage 1 pass (AA >= 0.9): {df['stage1_pass'].mean():.0%}  ({df['stage1_pass'].sum()}/{n} seeds)")
    print(f"Q1. SHAP correctly ranked c as top: "
          f"{df['shap_correct'].mean():.0%}  ({df['shap_correct'].sum()}/{n} seeds)")
    print(f"    Mean |SHAP|: x={df['shap_x'].mean():.4f}, y={df['shap_y'].mean():.4f}, c={df['shap_c'].mean():.4f}")
    print(f"Q2. Stage 2 collapse (c reversed):  "
          f"{df['c_collapse'].mean():.0%}  ({df['c_collapse'].sum()}/{n} seeds)")
    print(f"    J_S train={df['j_s_train'].mean():.3f}, reversed={df['j_s_c_reversed'].mean():.3f}")
    print(f"Q3. Control AA: AA_x={df['aa_x_random'].mean():.3f}, AA_y={df['aa_y_random'].mean():.3f}")


def _save_summary_txt(df: pd.DataFrame, cfg: dict, output_dir: Path) -> None:
    n = len(df)
    lines = [
        f"=== {cfg.get('name', 'experiment')} ===",
        cfg.get("description", ""),
        "",
        f"Seeds  : {list(df['seed'])}",
        f"Oracle : DQN {cfg['oracle']['n_steps']} steps",
        f"Surrogate: MoET K={cfg['surrogate']['n_experts']}, d={cfg['surrogate']['max_depth']}, "
        f"epochs={cfg['surrogate']['distill_epochs']}, n={cfg['surrogate']['n_distill_samples']}",
        "",
        f"Stage 1 pass (AA>=0.9): {df['stage1_pass'].mean():.0%} ({df['stage1_pass'].sum()}/{n})",
        "",
        f"Q1. SHAP correctly identified c as top: {df['shap_correct'].mean():.0%} ({df['shap_correct'].sum()}/{n})",
        f"    Mean |SHAP|: x={df['shap_x'].mean():.4f}+-{df['shap_x'].std():.4f}",
        f"               y={df['shap_y'].mean():.4f}+-{df['shap_y'].std():.4f}",
        f"               c={df['shap_c'].mean():.4f}+-{df['shap_c'].std():.4f}",
        "",
        f"Q2. Collapse (c reversed): {df['c_collapse'].mean():.0%} ({df['c_collapse'].sum()}/{n})",
        f"    J_S train   = {df['j_s_train'].mean():.3f}+-{df['j_s_train'].std():.3f}",
        f"    J_S reversed= {df['j_s_c_reversed'].mean():.3f}+-{df['j_s_c_reversed'].std():.3f}",
        "",
        f"Q3. Control AA: AA_x={df['aa_x_random'].mean():.3f}+-{df['aa_x_random'].std():.3f}, "
        f"AA_y={df['aa_y_random'].mean():.3f}+-{df['aa_y_random'].std():.3f}",
        "",
        "Per-seed:",
    ]
    for _, row in df.iterrows():
        lines.append(
            f"  seed={int(row['seed'])}: SHAP_1st={row['shap_rank_1st']}, "
            f"Stage1={'PASS' if row['stage1_pass'] else 'FAIL'}, AA={row['aa_train']:.3f}, "
            f"J_S_train={row['j_s_train']:.3f}, J_S_rev={row['j_s_c_reversed']:.3f}, "
            f"collapse={row['c_collapse']}"
        )
    (output_dir / "summary.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"summary.txt -> {output_dir / 'summary.txt'}")


def _plot(df: pd.DataFrame, output_dir: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    ax = axes[0]
    means  = [df["shap_x"].mean(), df["shap_y"].mean(), df["shap_c"].mean()]
    stds   = [df["shap_x"].std(),  df["shap_y"].std(),  df["shap_c"].std()]
    colors = ["steelblue", "steelblue", "tomato"]
    ax.bar(FEATURE_NAMES, means, yerr=stds, color=colors, capsize=5)
    ax.set_title("SHAP importance (mean ± SD)")
    ax.set_ylabel("Mean |SHAP|")

    x = np.arange(len(df))
    w = 0.35

    ax = axes[1]
    ax.bar(x - w/2, df["j_s_train"],      w, label="train",     color="steelblue")
    ax.bar(x + w/2, df["j_s_c_reversed"], w, label="c reversed", color="tomato")
    ax.set_xticks(x)
    ax.set_xticklabels([f"s={int(s)}" for s in df["seed"]], rotation=30, fontsize=8)
    ax.set_title("J_S: train vs c-reversed")
    ax.set_ylabel("Mean episode reward")
    ax.legend()

    ax = axes[2]
    ax.bar(x - w/2, df["aa_train"],      w, label="train",     color="steelblue")
    ax.bar(x + w/2, df["aa_c_reversed"], w, label="c reversed", color="tomato")
    ax.axhline(0.9, color="black", linestyle="--", linewidth=1, label="AA=0.9")
    ax.set_xticks(x)
    ax.set_xticklabels([f"s={int(s)}" for s in df["seed"]], rotation=30, fontsize=8)
    ax.set_title("Action Agreement: train vs c-reversed")
    ax.set_ylabel("AA")
    ax.set_ylim(0, 1.1)
    ax.legend()

    plt.tight_layout()
    path = output_dir / "results.png"
    plt.savefig(path, dpi=120)
    plt.close()


if __name__ == "__main__":
    main()
