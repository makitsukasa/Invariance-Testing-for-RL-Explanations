"""GridWorld 実験エントリポイント。

使い方:
    python experiments/run_gridworld.py --config experiments/configs/exp002_spurious_gridworld.yaml
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
from experiments.src.gridworld_env import SpuriousGridWorld
from experiments.src.moet import SoftMoET
from experiments.src.distill import distill
from experiments.src.evaluate import action_agreement, kl_divergence, evaluate_rollout, relative_perf_drop


# ---------------------------------------------------------------------------
# データ収集・評価ユーティリティ（GridWorld 専用）
# ---------------------------------------------------------------------------

def train_dqn_gridworld(spurious_p: float, n_steps: int, seed: int, save_path: Path) -> DQN:
    env = SpuriousGridWorld(spurious_p=spurious_p)
    model = DQN("MlpPolicy", env, seed=seed, verbose=0, learning_starts=1000)
    model.learn(total_timesteps=n_steps)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(save_path))
    env.close()
    return model


def collect_gridworld_transitions(
    model: DQN, spurious_p: float, n_samples: int, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    """Intuitive policy でロールアウトし (obs, action) を収集する。"""
    np.random.seed(seed)
    env = SpuriousGridWorld(spurious_p=spurious_p)
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


def eval_states_for_condition(obs_eval: np.ndarray, condition: str) -> np.ndarray:
    """eval_states の c 列（インデックス 2）を条件に応じて変換する。

    位置 (x, y) は固定し、c のみ変化させることで「c の効果だけ」を測定。
    """
    obs = obs_eval.copy()
    if condition == "train":
        pass  # そのまま
    elif condition == "random_c":
        obs[:, 2] = np.random.randint(0, 2, len(obs)).astype(np.float32)
    elif condition == "reversed_c":
        obs[:, 2] = 1.0 - obs[:, 2]
    return obs


def evaluate_intuitive_gridworld(
    model: DQN, spurious_p: float, eval_mode: str | None, n_episodes: int, seed: int
) -> float:
    env = SpuriousGridWorld(spurious_p=spurious_p, eval_mode=eval_mode)
    total = 0.0
    for ep in range(n_episodes):
        obs, _ = env.reset(seed=seed + ep)
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, _ = env.step(int(action))
            total += reward
            done = terminated or truncated
    env.close()
    return total / n_episodes


# ---------------------------------------------------------------------------
# メイン実験ループ
# ---------------------------------------------------------------------------

def run_experiment(cfg: dict) -> None:
    output_dir = ROOT / cfg["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    spurious_p_values: list[float] = cfg["env"]["spurious_p_values"]
    grid_size: int = cfg["env"].get("grid_size", 5)
    expert_counts: list[int] = cfg["moet"]["expert_counts"]
    tree_depths: list[int] = cfg["moet"]["tree_depths"]
    seeds: list[int] = cfg["evaluation"]["seeds"]
    n_steps: int = cfg["intuitive"]["n_steps"]
    distill_epochs: int = cfg["moet"]["distill_epochs"]
    distill_n_samples: int = cfg["moet"]["distill_n_samples"]
    eval_n_samples: int = cfg["moet"].get("eval_n_samples", 5000)
    n_eval_episodes: int = cfg["evaluation"]["n_eval_episodes"]
    eval_conditions: list[str] = cfg["evaluation"].get("eval_conditions", ["train"])
    n_actions = 4  # GridWorld: 上下左右

    records = []
    total_configs = len(spurious_p_values) * len(seeds) * len(expert_counts) * len(tree_depths)
    done_count = 0

    for spurious_p in spurious_p_values:
        for seed in seeds:
            print(f"\n[spurious_p={spurious_p}, seed={seed}] Intuitive 学習中 ({n_steps} steps)...")
            model_path = output_dir / f"intuitive_p{spurious_p}_seed{seed}"
            model = train_dqn_gridworld(spurious_p, n_steps, seed, model_path)

            # Intuitive 性能を train 条件で測定（基準）
            j_intuitive_train = evaluate_intuitive_gridworld(
                model, spurious_p, None, n_eval_episodes, seed
            )
            print(f"  J_intuitive (train) = {j_intuitive_train:.3f}")

            # 蒸留用データ
            print(f"  蒸留用データ収集中 (seed={seed})...")
            obs_distill, action_distill = collect_gridworld_transitions(
                model, spurious_p, distill_n_samples, seed
            )

            # 評価用データ（別シード）
            eval_seed = seed + 10000
            print(f"  評価用データ収集中 (seed={eval_seed})...")
            obs_eval_base, _ = collect_gridworld_transitions(
                model, spurious_p, eval_n_samples, eval_seed
            )
            np.save(output_dir / f"eval_states_p{spurious_p}_seed{seed}.npy", obs_eval_base)

            # Intuitive の各条件での性能を事前計算
            j_intuitive_by_cond = {"train": j_intuitive_train}
            for cond in eval_conditions:
                if cond == "train":
                    continue
                eval_mode = "random" if cond == "random_c" else "reversed"
                j_intuitive_by_cond[cond] = evaluate_intuitive_gridworld(
                    model, spurious_p, eval_mode, n_eval_episodes, eval_seed
                )

            for n_experts in expert_counts:
                for max_depth in tree_depths:
                    moet = SoftMoET(3, n_actions, n_experts, max_depth)  # 入力次元=3
                    moet = distill(moet, obs_distill, action_distill, epochs=distill_epochs)

                    # 各 eval 条件で評価
                    for cond in eval_conditions:
                        obs_eval_cond = eval_states_for_condition(obs_eval_base, cond)

                        # Intuitive の行動を eval_states 上で取得（比較基準）
                        intuitive_actions_eval, _ = model.predict(obs_eval_cond, deterministic=True)

                        aa = action_agreement(obs_eval_cond, intuitive_actions_eval, moet)
                        kl = kl_divergence(obs_eval_cond, model, moet, n_actions)

                        # RPD: rollout ベース（eval_mode を env に渡す）
                        eval_mode_str = None if cond == "train" else (
                            "random" if cond == "random_c" else "reversed"
                        )
                        eval_env = SpuriousGridWorld(spurious_p=spurious_p, eval_mode=eval_mode_str)
                        j_reasoned = evaluate_rollout(moet, eval_env, n_eval_episodes, eval_seed)
                        eval_env.close()

                        j_int = j_intuitive_by_cond[cond]
                        rpd = relative_perf_drop(j_int, j_reasoned)

                        records.append({
                            "spurious_p": spurious_p,
                            "n_experts": n_experts,
                            "max_depth": max_depth,
                            "seed": seed,
                            "eval_condition": cond,
                            "j_intuitive": j_int,
                            "j_reasoned": j_reasoned,
                            "action_agreement": aa,
                            "kl_divergence": kl,
                            "relative_perf_drop": rpd,
                        })

                    done_count += 1
                    print(
                        f"  [K={n_experts}, d={max_depth}] train AA={records[-3]['action_agreement']:.3f} "
                        f"| random AA={records[-2]['action_agreement']:.3f} "
                        f"| reversed AA={records[-1]['action_agreement']:.3f}  "
                        f"({done_count}/{total_configs})"
                    )

    # --- 結果保存 ---
    df = pd.DataFrame(records)
    csv_path = output_dir / "metrics.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nmetrics.csv 保存: {csv_path}")

    _save_heatmaps(df, output_dir)
    _save_summary(df, output_dir)
    print(f"\n実験完了。結果: {output_dir}")


def _save_heatmaps(df: pd.DataFrame, output_dir: Path) -> None:
    """spurious_p × eval_condition ごとに action_agreement ヒートマップを保存。"""
    for cond in df["eval_condition"].unique():
        sub_cond = df[df["eval_condition"] == cond]
        spurious_p_vals = sorted(sub_cond["spurious_p"].unique())
        n_plots = len(spurious_p_vals)
        fig, axes = plt.subplots(1, n_plots, figsize=(5 * n_plots, 4))
        if n_plots == 1:
            axes = [axes]

        for ax, sp in zip(axes, spurious_p_vals):
            sub = sub_cond[sub_cond["spurious_p"] == sp].groupby(
                ["n_experts", "max_depth"]
            )["action_agreement"].mean().unstack()
            im = ax.imshow(sub.values, vmin=0, vmax=1, aspect="auto", cmap="RdYlGn")
            ax.set_xticks(range(len(sub.columns)))
            ax.set_xticklabels(sub.columns)
            ax.set_yticks(range(len(sub.index)))
            ax.set_yticklabels(sub.index)
            ax.set_xlabel("max_depth")
            ax.set_ylabel("n_experts")
            ax.set_title(f"spurious_p={sp}")
            plt.colorbar(im, ax=ax)

        fig.suptitle(f"Action Agreement — eval_condition={cond}")
        plt.tight_layout()
        path = output_dir / f"heatmap_aa_{cond}.png"
        plt.savefig(path, dpi=100)
        plt.close()

    print(f"ヒートマップ保存完了: {output_dir}")


def _save_summary(df: pd.DataFrame, output_dir: Path) -> None:
    lines = ["=== 実験サマリー（GridWorld） ===\n"]
    mean_df = df.groupby(["spurious_p", "eval_condition", "n_experts", "max_depth"])[
        ["action_agreement", "kl_divergence", "relative_perf_drop"]
    ].agg(["mean", "std"])

    for (sp, cond, k, d), row in mean_df.iterrows():
        aa_m, aa_s = row[("action_agreement", "mean")], row[("action_agreement", "std")]
        rpd_m, rpd_s = row[("relative_perf_drop", "mean")], row[("relative_perf_drop", "std")]
        lines.append(
            f"p={sp}, {cond:12s}, K={k}, d={d}: "
            f"AA={aa_m:.3f}±{aa_s:.3f}  RPD={rpd_m:.3f}±{rpd_s:.3f}"
        )

    summary_path = output_dir / "summary.txt"
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"summary.txt 保存: {summary_path}")
    print("\n" + "\n".join(lines[:30]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    run_experiment(cfg)


if __name__ == "__main__":
    main()
