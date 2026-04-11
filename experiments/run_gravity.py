"""exp003 エントリポイント: CartPole N=0 + 物理パラメータシフト実験。

「スプリアスのない環境での分布シフト」= 再現性高 × 不変性高 セルを埋める。
重力・ポール長など複数の物理パラメータを変えて、高不変性が偶然でないことを示す。

使い方:
    python experiments/run_gravity.py --config experiments/configs/exp003_cartpole_gravity.yaml
"""

import argparse
import sys
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

from experiments.src.cartpole_env import NoisyCartPoleEnv
from experiments.src.cartpole_intuitive import train_intuitive, collect_transitions
from experiments.src.shifted_cartpole_env import ShiftedCartPoleEnv
from experiments.src.moet import SoftMoET
from experiments.src.distill import distill
from experiments.src.evaluate import (
    action_agreement,
    kl_divergence,
    evaluate_rollout,
    relative_perf_drop,
)

DEFAULT_GRAVITY = 9.8
DEFAULT_POLE_LENGTH = 0.5


def collect_transitions_shifted(
    model: DQN,
    gravity: float,
    pole_length: float,
    n_samples: int,
    seed: int,
) -> tuple:
    """指定パラメータの CartPole 環境でロールアウトし (obs, action) を収集する。"""
    np.random.seed(seed)
    env = ShiftedCartPoleEnv(gravity=gravity, pole_length=pole_length)
    obs_list, action_list = [], []
    obs, _ = env.reset(seed=seed)
    collected = 0
    while collected < n_samples:
        action, _ = model.predict(obs, deterministic=True)
        obs_list.append(obs.copy())
        action_list.append(int(action))
        obs, _, terminated, truncated, _ = env.step(int(action))
        collected += 1
        if terminated or truncated:
            obs, _ = env.reset()
    env.close()
    return np.array(obs_list, dtype=np.float32), np.array(action_list, dtype=np.int64)


def run_experiment(cfg: dict) -> None:
    output_dir = ROOT / cfg["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    # shift_conditions: {name: {gravity: float, pole_length: float}}
    # 旧形式 gravity_conditions: {name: gravity_value} にも対応
    raw_conditions = cfg["env"].get("shift_conditions") or cfg["env"].get("gravity_conditions", {})
    shift_conditions: dict[str, dict] = {}
    for name, val in raw_conditions.items():
        if isinstance(val, dict):
            shift_conditions[name] = val
        else:
            shift_conditions[name] = {"gravity": float(val), "pole_length": DEFAULT_POLE_LENGTH}

    train_params = shift_conditions.get("train", {"gravity": DEFAULT_GRAVITY, "pole_length": DEFAULT_POLE_LENGTH})

    expert_counts: list[int] = cfg["moet"]["expert_counts"]
    tree_depths: list[int] = cfg["moet"]["tree_depths"]
    seeds: list[int] = cfg["evaluation"]["seeds"]
    n_steps: int = cfg["intuitive"]["n_steps"]
    distill_epochs: int = cfg["moet"]["distill_epochs"]
    distill_n_samples: int = cfg["moet"]["distill_n_samples"]
    eval_n_samples: int = cfg["moet"].get("eval_n_samples", 5000)
    n_eval_episodes: int = cfg["evaluation"]["n_eval_episodes"]
    reuse_from: str | None = cfg["intuitive"].get("reuse_from")
    n_actions = 2
    noise_dim = 0
    input_dim = 4

    records = []

    for seed in seeds:
        # --- Intuitive policy の取得 ---
        model_path = output_dir / f"intuitive_N0_seed{seed}"
        reuse_path = None
        if reuse_from:
            candidate = ROOT / reuse_from / f"intuitive_N0_seed{seed}.zip"
            if candidate.exists():
                reuse_path = candidate

        if reuse_path and reuse_path.exists():
            print(f"\n[seed={seed}] exp001 の学習済みモデルを再利用: {reuse_path}")
            env = NoisyCartPoleEnv(noise_dim=0)
            model = DQN.load(str(reuse_path), env=env)
        else:
            print(f"\n[seed={seed}] Intuitive 学習中 (N=0)...")
            model = train_intuitive(noise_dim, n_steps, seed, model_path)

        # --- 訓練分布 J_intuitive の評価 ---
        train_env = ShiftedCartPoleEnv(**train_params)
        eval_seed = seed + 10000
        j_intuitive_train = evaluate_rollout(model, train_env, n_eval_episodes, eval_seed)
        train_env.close()
        print(f"  J_intuitive (train) = {j_intuitive_train:.2f}")

        # --- 蒸留用データ（訓練パラメータで収集）---
        print(f"  蒸留用データ収集中 ({distill_n_samples} samples)...")
        obs_distill, action_distill = collect_transitions(
            model, noise_dim, distill_n_samples, seed
        )

        for n_experts in expert_counts:
            for max_depth in tree_depths:
                moet = SoftMoET(input_dim, n_actions, n_experts, max_depth)
                moet = distill(moet, obs_distill, action_distill, epochs=distill_epochs)
                print(f"  [K={n_experts}, d={max_depth}] 蒸留完了")

                for cond_name, params in shift_conditions.items():
                    g = params.get("gravity", DEFAULT_GRAVITY)
                    pl = params.get("pole_length", DEFAULT_POLE_LENGTH)

                    eval_obs, eval_actions = collect_transitions_shifted(
                        model, g, pl, eval_n_samples, eval_seed
                    )

                    aa = action_agreement(eval_obs, eval_actions, moet)
                    kl = kl_divergence(eval_obs, model, moet, n_actions)

                    eval_env = ShiftedCartPoleEnv(gravity=g, pole_length=pl)
                    j_intuitive = evaluate_rollout(model, eval_env, n_eval_episodes, eval_seed)
                    j_reasoned  = evaluate_rollout(moet, eval_env, n_eval_episodes, eval_seed)
                    eval_env.close()

                    rpd = relative_perf_drop(j_intuitive, j_reasoned)

                    records.append({
                        "condition": cond_name,
                        "gravity": g,
                        "pole_length": pl,
                        "n_experts": n_experts,
                        "max_depth": max_depth,
                        "seed": seed,
                        "j_intuitive": j_intuitive,
                        "j_reasoned": j_reasoned,
                        "action_agreement": aa,
                        "kl_divergence": kl,
                        "relative_perf_drop": rpd,
                    })
                    print(
                        f"    {cond_name} (g={g}, len={pl}): "
                        f"AA={aa:.3f}, J_I={j_intuitive:.1f}, J_R={j_reasoned:.1f}, "
                        f"RPD={rpd:.3f}"
                    )

    df = pd.DataFrame(records)
    csv_path = output_dir / "metrics.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nmetrics.csv を保存: {csv_path}")

    _save_comparison_plot(df, shift_conditions, output_dir)
    _save_summary(df, shift_conditions, output_dir)

    print(f"\n実験完了。結果: {output_dir}")


def _save_comparison_plot(
    df: pd.DataFrame,
    shift_conditions: dict,
    output_dir: Path,
) -> None:
    """AA・J を条件ごとに棒グラフで比較する。"""
    cond_names = list(shift_conditions.keys())
    x = np.arange(len(cond_names))
    width = 0.35

    mean_df = df.groupby("condition")[
        ["action_agreement", "j_intuitive", "j_reasoned"]
    ].agg(["mean", "std"])

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))

    # AA
    ax = axes[0]
    aa_mean = [mean_df.loc[c, ("action_agreement", "mean")] for c in cond_names]
    aa_std  = [mean_df.loc[c, ("action_agreement", "std")]  for c in cond_names]
    ax.bar(x, aa_mean, width * 1.6, yerr=aa_std, capsize=4,
           color="steelblue", alpha=0.82)
    ax.set_xticks(x)
    ax.set_xticklabels(cond_names, rotation=15, ha="right")
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Action Agreement (AA)")
    ax.set_title("AA under physics shift")
    ax.axhline(0.95, color="darkorange", linestyle="--", linewidth=1.0,
               label="exp002 reversed_c")
    ax.legend(fontsize=9)

    # J
    ax = axes[1]
    ji_mean = [mean_df.loc[c, ("j_intuitive", "mean")] for c in cond_names]
    jr_mean = [mean_df.loc[c, ("j_reasoned",  "mean")] for c in cond_names]
    ji_std  = [mean_df.loc[c, ("j_intuitive", "std")]  for c in cond_names]
    jr_std  = [mean_df.loc[c, ("j_reasoned",  "std")]  for c in cond_names]
    ax.bar(x - width / 2, ji_mean, width, yerr=ji_std, capsize=4,
           color="steelblue", alpha=0.85, label="$J_{\\mathrm{intuitive}}$")
    ax.bar(x + width / 2, jr_mean, width, yerr=jr_std, capsize=4,
           color="tomato", alpha=0.85, label="$J_{\\mathrm{reasoned}}$")
    ax.set_xticks(x)
    ax.set_xticklabels(cond_names, rotation=15, ha="right")
    ax.set_ylabel("Mean episode reward")
    ax.set_title("Episode reward under physics shift")
    ax.axhline(-1.0, color="darkorange", linestyle="--", linewidth=1.0,
               label="exp002 reversed_c J")
    ax.legend(fontsize=9)

    plt.suptitle("CartPole N=0: multiple physics shifts (no spurious features)")
    plt.tight_layout()
    path = output_dir / "physics_shift_comparison.png"
    plt.savefig(path, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"比較グラフを保存: {path}")


def _save_summary(
    df: pd.DataFrame,
    shift_conditions: dict,
    output_dir: Path,
) -> None:
    lines = [
        "=== exp003: CartPole N=0 + 物理パラメータシフト ===",
        "診断: 再現性高 × 不変性高（スプリアスなし）",
        "",
        "【比較】exp002 reversed_c: AA=0.954, J_I=-1.000, J_R=-1.000",
        "",
    ]

    mean_df = df.groupby("condition")[
        ["action_agreement", "j_intuitive", "j_reasoned", "relative_perf_drop"]
    ].agg(["mean", "std"])

    for cond_name, params in shift_conditions.items():
        if cond_name not in mean_df.index:
            continue
        row = mean_df.loc[cond_name]
        g  = params.get("gravity", DEFAULT_GRAVITY)
        pl = params.get("pole_length", DEFAULT_POLE_LENGTH)
        aa_m  = row[("action_agreement",   "mean")]
        aa_s  = row[("action_agreement",   "std")]
        ji_m  = row[("j_intuitive",        "mean")]
        jr_m  = row[("j_reasoned",         "mean")]
        rpd_m = row[("relative_perf_drop", "mean")]
        rpd_s = row[("relative_perf_drop", "std")]
        lines.append(
            f"{cond_name} (g={g}, len={pl}): "
            f"AA={aa_m:.3f}±{aa_s:.3f}  "
            f"J_I={ji_m:.1f}  J_R={jr_m:.1f}  "
            f"RPD={rpd_m:.3f}±{rpd_s:.3f}"
        )

    summary_path = output_dir / "summary.txt"
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"summary.txt を保存: {summary_path}")
    print("\n" + "\n".join(lines))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    run_experiment(cfg)


if __name__ == "__main__":
    main()
