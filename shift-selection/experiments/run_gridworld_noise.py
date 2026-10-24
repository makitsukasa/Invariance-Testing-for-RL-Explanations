"""Per-feature Intervention Test on GridWorld + noise features — exp004.

obs = (agent_x, agent_y, c_spurious, noise_0, ..., noise_{N-1})
ノイズ特徴は毎ステップ i.i.d. uniform [0,1] で再サンプリング。

Usage:
    python experiments/run_gridworld_noise.py --config experiments/configs/exp004_noise_gridworld.yaml
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
import yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from stable_baselines3 import DQN

from experiments.src.gridworld_env import SpuriousGridWorld
from experiments.src.moet import SoftMoET
from experiments.src.distill import distill
from experiments.src.evaluate import action_agreement, evaluate_rollout

SPURIOUS_IDX = 2


def _feature_names(n_noise: int) -> list[str]:
    return ["agent_x", "agent_y", "c (spurious)"] + [f"noise_{i}" for i in range(n_noise)]


# ---------------------------------------------------------------------------
# Oracle + Data collection
# ---------------------------------------------------------------------------

def _train_oracle(seed: int, cfg: dict) -> DQN:
    env = SpuriousGridWorld(
        spurious_p=cfg["env"]["spurious_p"],
        n_noise=cfg["env"]["n_noise"],
    )
    model = DQN("MlpPolicy", env, seed=seed, verbose=0, learning_starts=1000)
    model.learn(total_timesteps=cfg["oracle"]["n_steps"])
    env.close()
    return model


def _collect_transitions(
    model: DQN, spurious_p: float, n_noise: int, seed: int, n_samples: int
) -> tuple[np.ndarray, np.ndarray]:
    env = SpuriousGridWorld(spurious_p=spurious_p, n_noise=n_noise)
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
    n_noise: int,
    feature_idx: int,
    n_episodes: int,
    seed: int,
    rng: np.random.Generator,
) -> float:
    env = SpuriousGridWorld(spurious_p=spurious_p, n_noise=n_noise)
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

# ---------------------------------------------------------------------------
# Single-seed pipeline
# ---------------------------------------------------------------------------

def run_one_seed(seed: int, cfg: dict) -> tuple[dict, list[str]]:
    logs: list[str] = [f"\n{'='*60}", f"Seed {seed}", f"{'='*60}"]

    spurious_p = cfg["env"]["spurious_p"]
    n_noise    = cfg["env"]["n_noise"]
    n_obs      = 3 + n_noise
    feat_names = _feature_names(n_noise)
    n_episodes = cfg["evaluation"]["n_eval_episodes"]
    n_distill  = cfg["surrogate"]["n_distill_samples"]
    n_eval     = cfg["evaluation"]["n_eval_samples"]

    logs.append("  [1/4] Oracle training...")
    model = _train_oracle(seed, cfg)

    logs.append("  [2/4] Data collection...")
    obs_distill, act_distill = _collect_transitions(model, spurious_p, n_noise, seed,          n_distill)
    obs_eval, _              = _collect_transitions(model, spurious_p, n_noise, seed + 10_000, n_eval)

    logs.append("  [3/4] Surrogate training (MoET)...")
    moet = SoftMoET(n_obs, 4, cfg["surrogate"]["n_experts"], cfg["surrogate"]["max_depth"])
    moet = distill(moet, obs_distill, act_distill, epochs=cfg["surrogate"]["distill_epochs"])

    oracle_actions, _ = model.predict(obs_eval, deterministic=True)
    aa_train    = action_agreement(obs_eval, oracle_actions, moet)
    train_env   = SpuriousGridWorld(spurious_p=spurious_p, n_noise=n_noise)
    j_s_train   = evaluate_rollout(moet, train_env, n_episodes, seed + 20_000)
    train_env.close()
    stage1_pass = aa_train >= 0.9
    logs.append(f"    Stage 1: AA={aa_train:.3f} ({'PASS' if stage1_pass else 'FAIL'}), J_S_train={j_s_train:.3f}")

    logs.append("  [4/4] Per-feature intervention test...")
    rng = np.random.default_rng(seed + 30_000)
    j_s_feat: list[float] = []
    for fi in range(n_obs):
        j_f = _eval_intervention(
            moet, spurious_p, n_noise,
            fi, n_episodes, seed + 40_000 + fi * 1000, rng,
        )
        j_s_feat.append(j_f)
        logs.append(f"    {feat_names[fi]}: J_S_perturbed={j_f:.3f}")

    delta = [j_s_train - j_f for j_f in j_s_feat]
    top_idx = int(np.argmax(delta))
    intervention_correct = (top_idx == SPURIOUS_IDX)
    delta_str = ", ".join(f"{feat_names[i]}={delta[i]:.3f}" for i in range(n_obs))
    logs.append(f"    Δ: {delta_str}")
    logs.append(f"    Auto-selected: {feat_names[top_idx]} -> "
                f"{'CORRECT (c)' if intervention_correct else 'WRONG'}")

    result = {
        "seed": seed,
        "aa_train": aa_train,
        "stage1_pass": stage1_pass,
        "j_s_train": j_s_train,
        **{f"j_s_{feat_names[i]}_perturbed": j_s_feat[i] for i in range(n_obs)},
        **{f"delta_{feat_names[i]}": delta[i] for i in range(n_obs)},
        "intervention_selected": feat_names[top_idx],
        "intervention_correct": intervention_correct,
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
    n_noise   = cfg["env"]["n_noise"]
    feat_names = _feature_names(n_noise)

    print(f"Experiment : {cfg.get('name', 'unknown')}")
    print(f"Seeds      : {seeds}")
    print(f"Workers    : {n_workers}")
    print(f"Features   : {feat_names}")

    records:   list[dict]           = []
    seed_logs: dict[int, list[str]] = {}

    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = {executor.submit(run_one_seed, s, cfg): s for s in seeds}
        for future in as_completed(futures):
            seed = futures[future]
            rec, logs = future.result()
            records.append(rec)
            seed_logs[seed] = logs
            print(f"[DONE] seed={seed}: selected={rec['intervention_selected']}, "
                  f"correct={rec['intervention_correct']}, AA={rec['aa_train']:.3f}")

    for seed in sorted(seed_logs):
        for line in seed_logs[seed]:
            print(line)

    df = pd.DataFrame(records).sort_values("seed").reset_index(drop=True)
    df.to_csv(output_dir / "results.csv", index=False)

    _print_summary(df, feat_names)
    _save_summary_txt(df, cfg, output_dir, feat_names)
    _plot(df, output_dir, feat_names)
    print(f"\nResults: {output_dir}")


def _print_summary(df: pd.DataFrame, feat_names: list[str]) -> None:
    n = len(df)
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Stage 1 pass (AA >= 0.9): {df['stage1_pass'].mean():.0%}  ({df['stage1_pass'].sum()}/{n} seeds)")
    print(f"Q1. Intervention correctly selected c: "
          f"{df['intervention_correct'].mean():.0%}  ({df['intervention_correct'].sum()}/{n} seeds)")
    delta_means = {f: df[f"delta_{f}"].mean() for f in feat_names}
    top = max(delta_means, key=delta_means.get)
    print("    Δ means: " + ", ".join(f"{f}={delta_means[f]:.3f}" for f in feat_names))
    print(f"    Largest mean Δ: {top}")


def _save_summary_txt(df: pd.DataFrame, cfg: dict, output_dir: Path, feat_names: list[str]) -> None:
    n = len(df)
    lines = [
        f"=== {cfg.get('name', 'experiment')} ===",
        cfg.get("description", ""),
        "",
        f"Seeds  : {list(df['seed'])}",
        f"n_noise: {cfg['env']['n_noise']} (total obs dim: {3 + cfg['env']['n_noise']})",
        f"Oracle : DQN {cfg['oracle']['n_steps']} steps",
        f"Surrogate: MoET K={cfg['surrogate']['n_experts']}, d={cfg['surrogate']['max_depth']}, "
        f"epochs={cfg['surrogate']['distill_epochs']}, n={cfg['surrogate']['n_distill_samples']}",
        "",
        f"Stage 1 pass (AA>=0.9): {df['stage1_pass'].mean():.0%} ({df['stage1_pass'].sum()}/{n})",
        "",
        f"Q1. Intervention correctly selected c: "
        f"{df['intervention_correct'].mean():.0%} ({df['intervention_correct'].sum()}/{n})",
    ]
    for f in feat_names:
        lines.append(f"  Δ_{f}={df[f'delta_{f}'].mean():.3f}+-{df[f'delta_{f}'].std():.3f}")
    lines += ["", "Per-seed:"]
    for _, row in df.iterrows():
        lines.append(
            f"  seed={int(row['seed'])}: selected={row['intervention_selected']}, "
            f"correct={row['intervention_correct']}, "
            f"AA={row['aa_train']:.3f}, J_S_train={row['j_s_train']:.3f}"
        )
    (output_dir / "summary.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"summary.txt -> {output_dir / 'summary.txt'}")


def _plot(df: pd.DataFrame, output_dir: Path, feat_names: list[str]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Δ per feature (bar)
    ax = axes[0]
    delta_means = [df[f"delta_{f}"].mean() for f in feat_names]
    delta_stds  = [df[f"delta_{f}"].std()  for f in feat_names]
    colors = ["tomato" if i == SPURIOUS_IDX else "steelblue" for i in range(len(feat_names))]
    ax.bar(range(len(feat_names)), delta_means, yerr=delta_stds, color=colors, capsize=4)
    ax.set_xticks(range(len(feat_names)))
    ax.set_xticklabels(feat_names, rotation=30, ha="right", fontsize=8)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_title("Mean Δ (J_S drop) per feature (± SD)\n[red = c (spurious)]")
    ax.set_ylabel("Δ J_S")

    # J_S: train vs c-perturbed per seed
    ax = axes[1]
    x = np.arange(len(df))
    w = 0.35
    ax.bar(x - w/2, df["j_s_train"],                     w, label="train",      color="steelblue")
    ax.bar(x + w/2, df["j_s_c (spurious)_perturbed"],    w, label="c perturbed", color="tomato")
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_xticks(x)
    ax.set_xticklabels([f"s={int(s)}" for s in df["seed"]], rotation=30, fontsize=8)
    ax.set_title("J_S: train vs c-perturbed")
    ax.set_ylabel("Mean episode reward")
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_dir / "results.png", dpi=120)
    plt.close()


if __name__ == "__main__":
    main()
