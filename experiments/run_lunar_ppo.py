"""Per-feature Intervention Test on SpuriousLunarLander with PPO oracle — exp006.

exp003（DQN）の失敗を受け、PPO + gamma=0.999 に切替。
- GAE で長期信用割り当てを改善
- gamma=0.999 で 0.999^400≈0.67（DQN の 0.99^400≈0.018 から大幅改善）

Usage:
    python experiments/run_lunar_ppo.py --config experiments/configs/exp006_ppo_lunar.yaml
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
from stable_baselines3 import PPO

from experiments.src.spurious_lunar_env import (
    SpuriousLunarLander, FEATURE_NAMES, SPURIOUS_IDX, N_OBS, N_ACTIONS
)
from experiments.src.moet import SoftMoET
from experiments.src.distill import distill
from experiments.src.evaluate import action_agreement, evaluate_rollout

# ---------------------------------------------------------------------------
# Oracle + Data collection
# ---------------------------------------------------------------------------

def _train_oracle(seed: int, cfg: dict) -> PPO:
    env = SpuriousLunarLander(spurious_p=cfg["env"]["spurious_p"])
    model = PPO(
        "MlpPolicy", env, seed=seed, verbose=0,
        gamma=cfg["oracle"]["gamma"],
        gae_lambda=cfg["oracle"]["gae_lambda"],
        ent_coef=cfg["oracle"]["ent_coef"],
        n_steps=cfg["oracle"]["n_steps_per_rollout"],
        batch_size=cfg["oracle"]["batch_size"],
        n_epochs=cfg["oracle"]["n_epochs"],
    )
    model.learn(total_timesteps=cfg["oracle"]["n_steps"])
    env.close()
    return model


def _collect_transitions(
    model: PPO,
    spurious_p: float,
    seed: int,
    n_samples: int,
) -> tuple[np.ndarray, np.ndarray]:
    env = SpuriousLunarLander(spurious_p=spurious_p)
    obs_list, act_list = [], []
    rng = np.random.default_rng(seed)
    obs, _ = env.reset(seed=int(rng.integers(1_000_000)))
    while len(obs_list) < n_samples:
        action, _ = model.predict(obs, deterministic=True)
        obs_list.append(obs.copy())
        act_list.append(int(action))
        obs, _, terminated, truncated, _ = env.step(int(action))
        if terminated or truncated:
            obs, _ = env.reset(seed=int(rng.integers(1_000_000)))
    env.close()
    return np.array(obs_list, dtype=np.float32), np.array(act_list, dtype=np.int64)

# ---------------------------------------------------------------------------
# Per-feature intervention rollout
# ---------------------------------------------------------------------------

def _eval_intervention(
    surrogate: SoftMoET,
    spurious_p: float,
    feature_idx: int,
    feat_range: tuple[float, float],
    n_episodes: int,
    seed: int,
    rng: np.random.Generator,
) -> float:
    env = SpuriousLunarLander(spurious_p=spurious_p)
    lo, hi = feat_range
    total_reward = 0.0
    for ep in range(n_episodes):
        obs, _ = env.reset(seed=seed + ep)
        done = False
        while not done:
            obs_p = obs.copy()
            obs_p[feature_idx] = float(rng.uniform(lo, hi))
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
    n_episodes = cfg["evaluation"]["n_eval_episodes"]
    n_distill  = cfg["surrogate"]["n_distill_samples"]
    n_eval     = cfg["evaluation"]["n_eval_samples"]

    logs.append("  [1/4] Oracle training (PPO)...")
    model = _train_oracle(seed, cfg)

    logs.append("  [2/4] Data collection...")
    obs_distill, act_distill = _collect_transitions(model, spurious_p, seed,          n_distill)
    obs_eval, _              = _collect_transitions(model, spurious_p, seed + 10_000, n_eval)

    logs.append("  [3/4] Surrogate training (MoET)...")
    moet = SoftMoET(N_OBS, N_ACTIONS, cfg["surrogate"]["n_experts"], cfg["surrogate"]["max_depth"])
    moet = distill(moet, obs_distill, act_distill, epochs=cfg["surrogate"]["distill_epochs"])

    oracle_actions, _ = model.predict(obs_eval, deterministic=True)
    aa_train    = action_agreement(obs_eval, oracle_actions, moet)
    stage1_pass = aa_train >= 0.9

    train_env      = SpuriousLunarLander(spurious_p=spurious_p)
    j_oracle_train = evaluate_rollout(model, train_env, n_episodes, seed + 20_000)
    j_s_train      = evaluate_rollout(moet,  train_env, n_episodes, seed + 20_000)
    train_env.close()
    logs.append(f"    Stage 1: AA={aa_train:.3f} ({'PASS' if stage1_pass else 'FAIL'}), "
                f"J_oracle={j_oracle_train:.1f}, J_S_train={j_s_train:.1f}")

    rev_env   = SpuriousLunarLander(spurious_p=spurious_p, eval_mode="reversed")
    j_s_rev   = evaluate_rollout(moet, rev_env, n_episodes, seed + 30_000)
    rev_env.close()
    c_collapse = j_s_train > 0 and j_s_rev < 0.5 * j_s_train
    logs.append(f"    Stage 2 (c reversed): J_S={j_s_rev:.1f} -> "
                f"{'COLLAPSE DETECTED' if c_collapse else 'no collapse'}")

    logs.append("  [4/4] Per-feature intervention test...")
    feat_ranges = [
        (float(obs_distill[:, i].min()), float(obs_distill[:, i].max()))
        for i in range(N_OBS)
    ]
    rng = np.random.default_rng(seed + 40_000)
    j_s_feat: list[float] = []
    for fi in range(N_OBS):
        j_f = _eval_intervention(
            moet, spurious_p,
            fi, feat_ranges[fi],
            n_episodes, seed + 50_000 + fi * 1000, rng,
        )
        j_s_feat.append(j_f)
        logs.append(f"    {FEATURE_NAMES[fi]}: J_S_perturbed={j_f:.1f}")

    delta = [j_s_train - j_f for j_f in j_s_feat]
    top_idx = int(np.argmax(delta))
    intervention_correct = (top_idx == SPURIOUS_IDX)
    delta_str = ", ".join(f"{FEATURE_NAMES[i]}={delta[i]:.2f}" for i in range(N_OBS))
    logs.append(f"    Δ: {delta_str}")
    logs.append(f"    Auto-selected: {FEATURE_NAMES[top_idx]} -> "
                f"{'CORRECT (c)' if intervention_correct else 'WRONG'}")

    result = {
        "seed": seed,
        "aa_train": aa_train,
        "stage1_pass": stage1_pass,
        "j_oracle_train": j_oracle_train,
        "j_s_train": j_s_train,
        "j_s_c_reversed": j_s_rev,
        "c_collapse": c_collapse,
        **{f"j_s_{FEATURE_NAMES[i]}_perturbed": j_s_feat[i] for i in range(N_OBS)},
        **{f"delta_{FEATURE_NAMES[i]}": delta[i] for i in range(N_OBS)},
        "intervention_selected": FEATURE_NAMES[top_idx],
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

    print(f"Experiment : {cfg.get('name', 'unknown')}")
    print(f"Seeds      : {seeds}")
    print(f"Workers    : {n_workers}")

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
                  f"correct={rec['intervention_correct']}, "
                  f"AA={rec['aa_train']:.3f}, J_oracle={rec['j_oracle_train']:.1f}")

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
    print(f"Stage 2 collapse (c rev): {df['c_collapse'].mean():.0%}  ({df['c_collapse'].sum()}/{n} seeds)")
    print(f"    J_oracle={df['j_oracle_train'].mean():.1f}, J_S_train={df['j_s_train'].mean():.1f}, J_S_rev={df['j_s_c_reversed'].mean():.1f}")
    print(f"Q1. Intervention correctly selected c: "
          f"{df['intervention_correct'].mean():.0%}  ({df['intervention_correct'].sum()}/{n} seeds)")
    delta_means = {f: df[f"delta_{f}"].mean() for f in FEATURE_NAMES}
    top = max(delta_means, key=delta_means.get)
    print(f"    Δ means: " + ", ".join(f"{f}={delta_means[f]:.2f}" for f in FEATURE_NAMES))
    print(f"    Largest mean Δ: {top}")


def _save_summary_txt(df: pd.DataFrame, cfg: dict, output_dir: Path) -> None:
    n = len(df)
    lines = [
        f"=== {cfg.get('name', 'experiment')} ===",
        cfg.get("description", ""),
        "",
        f"Seeds  : {list(df['seed'])}",
        f"Oracle : PPO {cfg['oracle']['n_steps']} steps, gamma={cfg['oracle']['gamma']}, gae_lambda={cfg['oracle']['gae_lambda']}",
        f"Surrogate: MoET K={cfg['surrogate']['n_experts']}, d={cfg['surrogate']['max_depth']}, "
        f"epochs={cfg['surrogate']['distill_epochs']}, n={cfg['surrogate']['n_distill_samples']}",
        "",
        f"Stage 1 pass (AA>=0.9): {df['stage1_pass'].mean():.0%} ({df['stage1_pass'].sum()}/{n})",
        f"Stage 2 collapse (c rev): {df['c_collapse'].mean():.0%} ({df['c_collapse'].sum()}/{n})",
        f"  J_oracle={df['j_oracle_train'].mean():.1f}+-{df['j_oracle_train'].std():.1f}",
        f"  J_S_train={df['j_s_train'].mean():.1f}+-{df['j_s_train'].std():.1f}",
        f"  J_S_rev  ={df['j_s_c_reversed'].mean():.1f}+-{df['j_s_c_reversed'].std():.1f}",
        "",
        f"Q1. Intervention correctly selected c: "
        f"{df['intervention_correct'].mean():.0%} ({df['intervention_correct'].sum()}/{n})",
    ]
    for f in FEATURE_NAMES:
        lines.append(f"  Δ_{f}={df[f'delta_{f}'].mean():.2f}+-{df[f'delta_{f}'].std():.2f}")
    lines += ["", "Per-seed:"]
    for _, row in df.iterrows():
        lines.append(
            f"  seed={int(row['seed'])}: selected={row['intervention_selected']}, "
            f"correct={row['intervention_correct']}, "
            f"AA={row['aa_train']:.3f}, J_oracle={row['j_oracle_train']:.1f}, "
            f"J_S_train={row['j_s_train']:.1f}, collapse={row['c_collapse']}"
        )
    (output_dir / "summary.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"summary.txt -> {output_dir / 'summary.txt'}")


def _plot(df: pd.DataFrame, output_dir: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax = axes[0]
    delta_means = [df[f"delta_{f}"].mean() for f in FEATURE_NAMES]
    delta_stds  = [df[f"delta_{f}"].std()  for f in FEATURE_NAMES]
    colors = ["tomato" if i == SPURIOUS_IDX else "steelblue" for i in range(len(FEATURE_NAMES))]
    ax.bar(range(len(FEATURE_NAMES)), delta_means, yerr=delta_stds, color=colors, capsize=4)
    ax.set_xticks(range(len(FEATURE_NAMES)))
    ax.set_xticklabels(FEATURE_NAMES, rotation=30, ha="right", fontsize=8)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_title("Mean Δ (J_S drop) per feature (± SD)")
    ax.set_ylabel("Δ J_S")

    ax = axes[1]
    x = np.arange(len(df))
    w = 0.25
    ax.bar(x - w,   df["j_oracle_train"],   w, label="oracle",     color="seagreen")
    ax.bar(x,       df["j_s_train"],        w, label="surrogate",   color="steelblue")
    ax.bar(x + w,   df["j_s_c_reversed"],   w, label="c reversed",  color="tomato")
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_xticks(x)
    ax.set_xticklabels([f"s={int(s)}" for s in df["seed"]], rotation=30, fontsize=8)
    ax.set_title("J: oracle / surrogate / c-reversed")
    ax.set_ylabel("Mean episode reward")
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_dir / "results.png", dpi=120)
    plt.close()


if __name__ == "__main__":
    main()
