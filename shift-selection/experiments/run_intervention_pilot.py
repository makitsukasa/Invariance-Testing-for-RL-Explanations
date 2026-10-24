"""Per-feature Intervention Test for shift auto-selection — exp002.

各特徴をロールアウト中に摂動し J_S 降下量を測定する。
降下量最大の特徴をスプリアス候補として自動選択する。

Usage:
    python experiments/run_intervention_pilot.py --config experiments/configs/exp002_intervention_gridworld.yaml
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

# 全特徴を同一方法（uniform random）で摂動する。特徴の型に関する事前知識を使わない。
FEATURE_INFO = [
    {"name": "agent_x",      "mode": "random", "range": (0.0, 1.0)},
    {"name": "agent_y",      "mode": "random", "range": (0.0, 1.0)},
    {"name": "c (spurious)", "mode": "random", "range": (0.0, 1.0)},
]

# ---------------------------------------------------------------------------
# Oracle + Data collection (exp001 と同一)
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
# Per-feature intervention rollout
# ---------------------------------------------------------------------------

def _eval_intervention(
    surrogate: SoftMoET,
    spurious_p: float,
    feature_idx: int,
    mode: str,
    feat_range: tuple[float, float],
    n_episodes: int,
    seed: int,
    rng: np.random.Generator,
) -> float:
    """ロールアウト中に feature_idx を摂動して J_S を測定する。"""
    env = SpuriousGridWorld(spurious_p=spurious_p)
    total_reward = 0.0
    for ep in range(n_episodes):
        obs, _ = env.reset(seed=seed + ep)
        done = False
        while not done:
            obs_p = obs.copy()
            if mode == "reversed":
                obs_p[feature_idx] = 1.0 - obs_p[feature_idx]
            else:
                lo, hi = feat_range
                obs_p[feature_idx] = float(rng.uniform(lo, hi))
            action = int(surrogate.predict(obs_p[np.newaxis])[0])
            obs, reward, terminated, truncated, _ = env.step(action)
            total_reward += reward
            done = terminated or truncated
    env.close()
    return total_reward / n_episodes

# ---------------------------------------------------------------------------
# Single-seed pipeline (top-level for ProcessPoolExecutor)
# ---------------------------------------------------------------------------

def run_one_seed(seed: int, cfg: dict) -> tuple[dict, list[str]]:
    logs: list[str] = [f"\n{'='*60}", f"Seed {seed}", f"{'='*60}"]

    spurious_p = cfg["env"]["spurious_p"]
    n_episodes = cfg["evaluation"]["n_eval_episodes"]
    n_distill  = cfg["surrogate"]["n_distill_samples"]
    n_eval     = cfg["evaluation"]["n_eval_samples"]

    logs.append("  [1/4] Oracle training...")
    model = _train_oracle(seed, cfg)

    logs.append("  [2/4] Data collection...")
    obs_distill, act_distill = _collect_transitions(model, spurious_p, seed,          n_distill)
    obs_eval, _              = _collect_transitions(model, spurious_p, seed + 10_000, n_eval)

    logs.append("  [3/4] Surrogate training (MoET)...")
    moet = SoftMoET(3, 4, cfg["surrogate"]["n_experts"], cfg["surrogate"]["max_depth"])
    moet = distill(moet, obs_distill, act_distill, epochs=cfg["surrogate"]["distill_epochs"])

    oracle_actions_train, _ = model.predict(obs_eval, deterministic=True)
    aa_train    = action_agreement(obs_eval, oracle_actions_train, moet)
    train_env   = SpuriousGridWorld(spurious_p=spurious_p)
    j_s_train   = evaluate_rollout(moet, train_env, n_episodes, seed + 20_000)
    train_env.close()
    stage1_pass = aa_train >= 0.9
    logs.append(f"    Stage 1: AA={aa_train:.3f} ({'PASS' if stage1_pass else 'FAIL'}), J_S_train={j_s_train:.3f}")

    logs.append("  [4/4] Per-feature intervention test...")
    rng = np.random.default_rng(seed + 30_000)
    j_s_feat: list[float] = []
    for fi, finfo in enumerate(FEATURE_INFO):
        j_f = _eval_intervention(
            moet, spurious_p,
            fi, finfo["mode"], finfo["range"],
            n_episodes, seed + 40_000 + fi * 1000, rng,
        )
        j_s_feat.append(j_f)
        logs.append(f"    {finfo['name']}: J_S_perturbed={j_f:.3f}")

    delta = [j_s_train - j_f for j_f in j_s_feat]
    top_idx = int(np.argmax(delta))
    intervention_correct = (top_idx == SPURIOUS_IDX)
    logs.append("    Δ(J_S_train - J_S_perturbed): " +
                ", ".join(f"{FEATURE_NAMES[i]}={delta[i]:.3f}" for i in range(3)))
    logs.append(f"    Auto-selected: {FEATURE_NAMES[top_idx]} -> "
                f"{'CORRECT (c)' if intervention_correct else 'WRONG'}")

    result = {
        "seed":                  seed,
        "aa_train":              aa_train,
        "stage1_pass":           stage1_pass,
        "j_s_train":             j_s_train,
        "j_s_x_perturbed":       j_s_feat[0],
        "j_s_y_perturbed":       j_s_feat[1],
        "j_s_c_perturbed":       j_s_feat[2],
        "delta_x":               delta[0],
        "delta_y":               delta[1],
        "delta_c":               delta[2],
        "intervention_selected": FEATURE_NAMES[top_idx],
        "intervention_correct":  intervention_correct,
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

    seeds     = cfg["evaluation"]["seeds"]
    n_workers = cfg.get("n_workers", 4)

    print(f"Experiment : {cfg.get('name', 'unknown')}")
    print(f"Seeds      : {seeds}")
    print(f"Workers    : {n_workers}")

    records:   list[dict]       = []
    seed_logs: dict[int, list[str]] = {}

    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = {executor.submit(run_one_seed, s, cfg): s for s in seeds}
        for future in as_completed(futures):
            seed = futures[future]
            rec, logs = future.result()
            records.append(rec)
            seed_logs[seed] = logs
            print(f"[DONE] seed={seed}: selected={rec['intervention_selected']}, "
                  f"correct={rec['intervention_correct']}, "
                  f"AA={rec['aa_train']:.3f}, Stage1={'PASS' if rec['stage1_pass'] else 'FAIL'}")

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
    print(f"Q1. Intervention correctly selected c: "
          f"{df['intervention_correct'].mean():.0%}  ({df['intervention_correct'].sum()}/{n} seeds)")
    print(f"    Mean Δ: x={df['delta_x'].mean():.3f}, y={df['delta_y'].mean():.3f}, c={df['delta_c'].mean():.3f}")
    print(f"    J_S_train={df['j_s_train'].mean():.3f}, "
          f"J_S_x={df['j_s_x_perturbed'].mean():.3f}, "
          f"J_S_y={df['j_s_y_perturbed'].mean():.3f}, "
          f"J_S_c={df['j_s_c_perturbed'].mean():.3f}")


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
        f"Q1. Intervention correctly selected c: "
        f"{df['intervention_correct'].mean():.0%} ({df['intervention_correct'].sum()}/{n})",
        f"    Mean Δ(J_S_train - J_S_perturbed):",
        f"      x={df['delta_x'].mean():.3f}+-{df['delta_x'].std():.3f}",
        f"      y={df['delta_y'].mean():.3f}+-{df['delta_y'].std():.3f}",
        f"      c={df['delta_c'].mean():.3f}+-{df['delta_c'].std():.3f}",
        "",
        f"    J_S_train  = {df['j_s_train'].mean():.3f}+-{df['j_s_train'].std():.3f}",
        f"    J_S_x_pert = {df['j_s_x_perturbed'].mean():.3f}+-{df['j_s_x_perturbed'].std():.3f}",
        f"    J_S_y_pert = {df['j_s_y_perturbed'].mean():.3f}+-{df['j_s_y_perturbed'].std():.3f}",
        f"    J_S_c_pert = {df['j_s_c_perturbed'].mean():.3f}+-{df['j_s_c_perturbed'].std():.3f}",
        "",
        "Per-seed:",
    ]
    for _, row in df.iterrows():
        lines.append(
            f"  seed={int(row['seed'])}: selected={row['intervention_selected']}, "
            f"correct={row['intervention_correct']}, "
            f"AA={row['aa_train']:.3f}, J_S_train={row['j_s_train']:.3f}, "
            f"Δx={row['delta_x']:.3f}, Δy={row['delta_y']:.3f}, Δc={row['delta_c']:.3f}"
        )
    (output_dir / "summary.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"summary.txt -> {output_dir / 'summary.txt'}")


def _plot(df: pd.DataFrame, output_dir: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # J_S per feature
    ax = axes[0]
    x = np.arange(len(df))
    w = 0.2
    ax.bar(x - w,    df["j_s_train"],       w, label="train",    color="steelblue")
    ax.bar(x,        df["j_s_x_perturbed"], w, label="x random",  color="skyblue")
    ax.bar(x + w,    df["j_s_y_perturbed"], w, label="y random",  color="lightgreen")
    ax.bar(x + 2*w,  df["j_s_c_perturbed"], w, label="c reversed", color="tomato")
    ax.set_xticks(x + w / 2)
    ax.set_xticklabels([f"s={int(s)}" for s in df["seed"]], rotation=30, fontsize=8)
    ax.set_title("J_S by feature perturbation")
    ax.set_ylabel("Mean episode reward")
    ax.legend(fontsize=8)

    # Δ (J_S drop) per feature
    ax = axes[1]
    means = [df["delta_x"].mean(), df["delta_y"].mean(), df["delta_c"].mean()]
    stds  = [df["delta_x"].std(),  df["delta_y"].std(),  df["delta_c"].std()]
    colors = ["skyblue", "lightgreen", "tomato"]
    ax.bar(FEATURE_NAMES, means, yerr=stds, color=colors, capsize=5)
    ax.set_title("Mean Δ (J_S drop) per feature (± SD)")
    ax.set_ylabel("Δ J_S")

    plt.tight_layout()
    path = output_dir / "results.png"
    plt.savefig(path, dpi=120)
    plt.close()


if __name__ == "__main__":
    main()
