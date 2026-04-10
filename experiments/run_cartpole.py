"""CartPole 実験エントリポイント。

使い方:
    python experiments/run_cartpole.py --config experiments/configs/exp001_cartpole_noise.yaml
"""

import argparse
import sys
from pathlib import Path

# プロジェクトルートを sys.path に追加
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from experiments.src.cartpole_env import NoisyCartPoleEnv
from experiments.src.cartpole_intuitive import (
    train_intuitive,
    evaluate_intuitive,
    collect_transitions,
)
from experiments.src.moet import SoftMoET
from experiments.src.distill import distill
from experiments.src.evaluate import (
    action_agreement,
    kl_divergence,
    evaluate_rollout,
    relative_perf_drop,
)


def run_experiment(cfg: dict) -> None:
    output_dir = ROOT / cfg["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    noise_dims: list[int] = cfg["env"]["noise_dims"]
    expert_counts: list[int] = cfg["moet"]["expert_counts"]
    tree_depths: list[int] = cfg["moet"]["tree_depths"]
    seeds: list[int] = cfg["evaluation"]["seeds"]
    n_steps: int = cfg["intuitive"]["n_steps"]
    distill_epochs: int = cfg["moet"]["distill_epochs"]
    distill_n_samples: int = cfg["moet"]["distill_n_samples"]
    eval_n_samples: int = cfg["moet"].get("eval_n_samples", 5000)
    n_eval_episodes: int = cfg["evaluation"]["n_eval_episodes"]
    n_actions = 2  # CartPole

    records = []
    total = len(noise_dims) * len(expert_counts) * len(tree_depths) * len(seeds)
    done = 0

    for noise_dim in noise_dims:
        input_dim = 4 + noise_dim

        for seed in seeds:
            print(f"\n[noise_dim={noise_dim}, seed={seed}] Intuitive 学習中...")
            model_path = output_dir / f"intuitive_N{noise_dim}_seed{seed}"
            model = train_intuitive(noise_dim, n_steps, seed, model_path)
            j_intuitive = evaluate_intuitive(model, noise_dim, n_eval_episodes, seed)
            print(f"  J_intuitive = {j_intuitive:.2f}")

            # 蒸留用データ（seed そのまま）
            print(f"  蒸留用データ収集中 ({distill_n_samples} samples, seed={seed})...")
            obs_distill, action_distill = collect_transitions(
                model, noise_dim, distill_n_samples, seed
            )

            # 評価用データ（別シード = seed + 10000 で固定）
            eval_seed = seed + 10000
            print(f"  評価用データ収集中 ({eval_n_samples} samples, seed={eval_seed})...")
            obs_eval, action_eval = collect_transitions(
                model, noise_dim, eval_n_samples, eval_seed
            )
            # eval states を保存（条件間で再利用可能に）
            eval_states_path = output_dir / f"eval_states_N{noise_dim}_seed{seed}.npy"
            np.save(eval_states_path, obs_eval)

            for n_experts in expert_counts:
                for max_depth in tree_depths:
                    moet = SoftMoET(input_dim, n_actions, n_experts, max_depth)
                    # 蒸留は distill データで
                    moet = distill(moet, obs_distill, action_distill, epochs=distill_epochs)

                    # AA・KL は eval データ（固定、蒸留データと独立）で計算
                    aa = action_agreement(obs_eval, action_eval, moet)
                    kl = kl_divergence(obs_eval, model, moet, n_actions)

                    # RPD は軌跡ベースの rollout（固定シード）
                    eval_env = NoisyCartPoleEnv(noise_dim=noise_dim)
                    j_reasoned = evaluate_rollout(moet, eval_env, n_eval_episodes, eval_seed)
                    eval_env.close()

                    rpd = relative_perf_drop(j_intuitive, j_reasoned)

                    records.append({
                        "noise_dim": noise_dim,
                        "n_experts": n_experts,
                        "max_depth": max_depth,
                        "seed": seed,
                        "j_intuitive": j_intuitive,
                        "j_reasoned": j_reasoned,
                        "action_agreement": aa,
                        "kl_divergence": kl,
                        "relative_perf_drop": rpd,
                    })
                    done += 1
                    print(
                        f"  [K={n_experts}, d={max_depth}] "
                        f"AA={aa:.3f}, KL={kl:.4f}, RPD={rpd:.3f}  "
                        f"({done}/{total})"
                    )

    # --- 結果保存 ---
    df = pd.DataFrame(records)
    csv_path = output_dir / "metrics.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nmetrics.csv を保存しました: {csv_path}")

    # ヒートマップ: noise_dim=0 の場合の action_agreement (K×d の平均)
    _save_heatmap(df, output_dir)

    # サマリー
    _save_summary(df, output_dir)

    print(f"\n実験完了。結果: {output_dir}")


def _save_heatmap(df: pd.DataFrame, output_dir: Path) -> None:
    """各 noise_dim ごとに action_agreement のヒートマップ（K × d）を保存する。"""
    noise_dims = sorted(df["noise_dim"].unique())
    n_plots = len(noise_dims)
    fig, axes = plt.subplots(1, n_plots, figsize=(5 * n_plots, 4))
    if n_plots == 1:
        axes = [axes]

    for ax, nd in zip(axes, noise_dims):
        sub = df[df["noise_dim"] == nd].groupby(
            ["n_experts", "max_depth"]
        )["action_agreement"].mean().unstack()
        im = ax.imshow(sub.values, vmin=0, vmax=1, aspect="auto", cmap="RdYlGn")
        ax.set_xticks(range(len(sub.columns)))
        ax.set_xticklabels(sub.columns)
        ax.set_yticks(range(len(sub.index)))
        ax.set_yticklabels(sub.index)
        ax.set_xlabel("max_depth")
        ax.set_ylabel("n_experts")
        ax.set_title(f"noise_dim={nd}")
        plt.colorbar(im, ax=ax)

    fig.suptitle("Action Agreement (mean over seeds)")
    plt.tight_layout()
    path = output_dir / "heatmap_action_agreement.png"
    plt.savefig(path, dpi=100)
    plt.close()
    print(f"heatmap を保存しました: {path}")


def _save_summary(df: pd.DataFrame, output_dir: Path) -> None:
    lines = ["=== 実験サマリー ===\n"]
    mean_df = df.groupby(["noise_dim", "n_experts", "max_depth"])[
        ["action_agreement", "kl_divergence", "relative_perf_drop"]
    ].agg(["mean", "std"])

    for (nd, k, d), row in mean_df.iterrows():
        aa_m, aa_s = row[("action_agreement", "mean")], row[("action_agreement", "std")]
        kl_m, kl_s = row[("kl_divergence", "mean")], row[("kl_divergence", "std")]
        rpd_m, rpd_s = row[("relative_perf_drop", "mean")], row[("relative_perf_drop", "std")]
        lines.append(
            f"noise_dim={nd:2d}, K={k}, depth={d}: "
            f"AA={aa_m:.3f}±{aa_s:.3f}  "
            f"KL={kl_m:.4f}±{kl_s:.4f}  "
            f"RPD={rpd_m:.3f}±{rpd_s:.3f}"
        )

    summary_path = output_dir / "summary.txt"
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"summary.txt を保存しました: {summary_path}")
    print("\n" + "\n".join(lines[:20]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to YAML config file")
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    run_experiment(cfg)


if __name__ == "__main__":
    main()
