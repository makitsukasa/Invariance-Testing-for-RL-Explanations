"""モデル比較実験: MoET vs Linear vs SingleTree。

CartPole / GridWorld の両環境で同一条件のもと三種の Reasoned model を比較する。
既存の学習済み Intuitive policy モデルを再利用可能。

使い方:
    python experiments/run_comparison.py --config experiments/configs/exp004_cartpole_comparison.yaml
    python experiments/run_comparison.py --config experiments/configs/exp005_gridworld_comparison.yaml
"""

from __future__ import annotations

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

from experiments.src.moet import SoftMoET
from experiments.src.distill import distill
from experiments.src.baselines import LinearReasonedModel, SingleTreeReasonedModel
from experiments.src.evaluate import (
    action_agreement,
    kl_divergence,
    evaluate_rollout,
    relative_perf_drop,
)

MODEL_LABEL = {
    "moet": "MoET",
    "linear": "Linear",
    "tree": "Tree",
}


# ---------------------------------------------------------------------------
# モデルファクトリ
# ---------------------------------------------------------------------------

def make_model(model_type: str, input_dim: int, n_actions: int, comp_cfg: dict):
    if model_type == "moet":
        return SoftMoET(
            input_dim, n_actions,
            comp_cfg["moet"]["n_experts"],
            comp_cfg["moet"]["max_depth"],
        )
    elif model_type == "linear":
        return LinearReasonedModel(input_dim, n_actions)
    elif model_type == "tree":
        return SingleTreeReasonedModel(
            input_dim, n_actions,
            comp_cfg["tree"]["max_depth"],
        )
    else:
        raise ValueError(f"Unknown model_type: {model_type}")


def fit_model(model, obs: np.ndarray, actions: np.ndarray, comp_cfg: dict):
    if isinstance(model, SoftMoET):
        return distill(model, obs, actions, epochs=comp_cfg["distill_epochs"])
    else:
        return model.fit(obs, actions)


# ---------------------------------------------------------------------------
# CartPole 比較
# ---------------------------------------------------------------------------

def run_cartpole_comparison(cfg: dict) -> None:
    from experiments.src.cartpole_env import NoisyCartPoleEnv
    from experiments.src.cartpole_intuitive import train_intuitive, collect_transitions, evaluate_intuitive

    output_dir = ROOT / cfg["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    noise_dims: list[int] = cfg["env"]["noise_dims"]
    seeds: list[int] = cfg["evaluation"]["seeds"]
    n_steps: int = cfg["intuitive"]["n_steps"]
    reuse_from: str | None = cfg["intuitive"].get("reuse_from")
    comp_cfg: dict = cfg["comparison"]
    model_types: list[str] = comp_cfg["model_types"]
    distill_n_samples: int = comp_cfg["distill_n_samples"]
    eval_n_samples: int = comp_cfg.get("eval_n_samples", 5000)
    n_eval_episodes: int = cfg["evaluation"]["n_eval_episodes"]
    n_actions = 2

    records = []

    for noise_dim in noise_dims:
        input_dim = 4 + noise_dim

        for seed in seeds:
            # --- Intuitive policy の取得 ---
            model_path = output_dir / f"intuitive_N{noise_dim}_seed{seed}"
            reuse_path = None
            if reuse_from:
                candidate = ROOT / reuse_from / f"intuitive_N{noise_dim}_seed{seed}.zip"
                if candidate.exists():
                    reuse_path = candidate

            if reuse_path:
                print(f"\n[N={noise_dim}, seed={seed}] 既存モデルを再利用: {reuse_path}")
                env = NoisyCartPoleEnv(noise_dim=noise_dim)
                model = DQN.load(str(reuse_path), env=env)
            else:
                print(f"\n[N={noise_dim}, seed={seed}] Intuitive 学習中...")
                model = train_intuitive(noise_dim, n_steps, seed, model_path)

            j_intuitive = evaluate_intuitive(model, noise_dim, n_eval_episodes, seed)
            eval_seed = seed + 10000

            # 蒸留・評価データ収集
            obs_distill, action_distill = collect_transitions(
                model, noise_dim, distill_n_samples, seed
            )
            obs_eval, action_eval = collect_transitions(
                model, noise_dim, eval_n_samples, eval_seed
            )

            for model_type in model_types:
                rm = make_model(model_type, input_dim, n_actions, comp_cfg)
                rm = fit_model(rm, obs_distill, action_distill, comp_cfg)

                aa = action_agreement(obs_eval, action_eval, rm)
                kl = kl_divergence(obs_eval, model, rm, n_actions)

                eval_env = NoisyCartPoleEnv(noise_dim=noise_dim)
                j_reasoned = evaluate_rollout(rm, eval_env, n_eval_episodes, eval_seed)
                eval_env.close()

                rpd = relative_perf_drop(j_intuitive, j_reasoned)

                records.append({
                    "model_type": model_type,
                    "noise_dim": noise_dim,
                    "seed": seed,
                    "j_intuitive": j_intuitive,
                    "j_reasoned": j_reasoned,
                    "action_agreement": aa,
                    "kl_divergence": kl,
                    "relative_perf_drop": rpd,
                })
                print(
                    f"  [{MODEL_LABEL[model_type]:6s}, N={noise_dim}, seed={seed}] "
                    f"AA={aa:.3f}  KL={kl:.4f}  RPD={rpd:.3f}"
                )

    df = pd.DataFrame(records)
    csv_path = output_dir / "metrics.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nmetrics.csv を保存: {csv_path}")

    _save_cartpole_comparison_plot(df, output_dir)
    _save_summary(df, ["model_type", "noise_dim"], output_dir)


def _save_cartpole_comparison_plot(df: pd.DataFrame, output_dir: Path) -> None:
    noise_dims = sorted(df["noise_dim"].unique())
    model_types = df["model_type"].unique().tolist()
    colors = {"moet": "steelblue", "linear": "tomato", "tree": "seagreen"}

    fig, axes = plt.subplots(1, len(noise_dims), figsize=(5 * len(noise_dims), 4), sharey=True)
    if len(noise_dims) == 1:
        axes = [axes]

    for ax, nd in zip(axes, noise_dims):
        x = np.arange(len(model_types))
        means, stds = [], []
        for mt in model_types:
            sub = df[(df["noise_dim"] == nd) & (df["model_type"] == mt)]["action_agreement"]
            means.append(sub.mean())
            stds.append(sub.std())
        ax.bar(x, means, yerr=stds, capsize=5,
               color=[colors.get(m, "gray") for m in model_types], alpha=0.85)
        ax.set_xticks(x)
        ax.set_xticklabels([MODEL_LABEL.get(m, m) for m in model_types])
        ax.set_ylim(0, 1.1)
        ax.set_title(f"N={nd}")
        ax.set_ylabel("Action Agreement (AA)")
        ax.axhline(1.0, color="gray", linestyle=":", linewidth=0.8)

    fig.suptitle("CartPole: AA by model type and noise dimension")
    plt.tight_layout()
    out = output_dir / "comparison_aa_cartpole.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"図を保存: {out}")


# ---------------------------------------------------------------------------
# GridWorld 比較
# ---------------------------------------------------------------------------

def run_gridworld_comparison(cfg: dict) -> None:
    from experiments.src.gridworld_env import SpuriousGridWorld
    from experiments.run_gridworld import (
        train_dqn_gridworld,
        collect_gridworld_transitions,
        eval_states_for_condition,
        evaluate_intuitive_gridworld,
    )

    output_dir = ROOT / cfg["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    spurious_p_values: list[float] = cfg["env"]["spurious_p_values"]
    eval_conditions: list[str] = cfg["evaluation"]["eval_conditions"]
    seeds: list[int] = cfg["evaluation"]["seeds"]
    n_steps: int = cfg["intuitive"]["n_steps"]
    reuse_from: str | None = cfg["intuitive"].get("reuse_from")
    comp_cfg: dict = cfg["comparison"]
    model_types: list[str] = comp_cfg["model_types"]
    distill_n_samples: int = comp_cfg["distill_n_samples"]
    eval_n_samples: int = comp_cfg.get("eval_n_samples", 5000)
    n_eval_episodes: int = cfg["evaluation"]["n_eval_episodes"]
    n_actions = 4  # GridWorld: 上下左右

    records = []

    for spurious_p in spurious_p_values:
        for seed in seeds:
            # --- Intuitive policy の取得 ---
            model_path = output_dir / f"intuitive_p{spurious_p}_seed{seed}"
            reuse_path = None
            if reuse_from:
                # exp002 saves models as directories (SB3 default), not .zip
                candidate_dir = ROOT / reuse_from / f"intuitive_p{spurious_p}_seed{seed}"
                candidate_zip = ROOT / reuse_from / f"intuitive_p{spurious_p}_seed{seed}.zip"
                if candidate_dir.exists():
                    reuse_path = candidate_dir
                elif candidate_zip.exists():
                    reuse_path = candidate_zip

            if reuse_path:
                print(f"\n[p={spurious_p}, seed={seed}] 既存モデルを再利用: {reuse_path}")
                env = SpuriousGridWorld(spurious_p=spurious_p)
                model = DQN.load(str(reuse_path), env=env)
                env.close()
            else:
                print(f"\n[p={spurious_p}, seed={seed}] Intuitive 学習中...")
                model = train_dqn_gridworld(spurious_p, n_steps, seed, model_path)

            eval_seed = seed + 10000

            # 蒸留データ（訓練分布）
            obs_distill, action_distill = collect_gridworld_transitions(
                model, spurious_p, distill_n_samples, seed
            )
            # 評価用ベース状態
            obs_eval_base, _ = collect_gridworld_transitions(
                model, spurious_p, eval_n_samples, eval_seed
            )

            input_dim = obs_distill.shape[1]

            for model_type in model_types:
                rm = make_model(model_type, input_dim, n_actions, comp_cfg)
                rm = fit_model(rm, obs_distill, action_distill, comp_cfg)

                for condition in eval_conditions:
                    obs_shifted = eval_states_for_condition(obs_eval_base, condition)

                    # Intuitive の行動（シフト後の状態でも同じモデル）
                    intuitive_actions, _ = model.predict(obs_shifted, deterministic=True)
                    aa = action_agreement(obs_shifted, intuitive_actions, rm)
                    kl = kl_divergence(obs_shifted, model, rm, n_actions)

                    # condition ("random_c"/"reversed_c") → eval_mode ("random"/"reversed")
                    eval_mode_str = None if condition == "train" else (
                        "random" if condition == "random_c" else "reversed"
                    )
                    j_intuitive = evaluate_intuitive_gridworld(
                        model, spurious_p, eval_mode_str, n_eval_episodes, eval_seed
                    )

                    # GridWorld の evaluate_rollout はシフト条件を別途渡す必要があるため
                    # condition に応じた環境でロールアウト
                    eval_env = SpuriousGridWorld(
                        spurious_p=spurious_p,
                        eval_mode=eval_mode_str,
                    )
                    j_reasoned = evaluate_rollout(rm, eval_env, n_eval_episodes, eval_seed)
                    eval_env.close()

                    rpd = relative_perf_drop(j_intuitive, j_reasoned)

                    records.append({
                        "model_type": model_type,
                        "spurious_p": spurious_p,
                        "eval_condition": condition,
                        "seed": seed,
                        "j_intuitive": j_intuitive,
                        "j_reasoned": j_reasoned,
                        "action_agreement": aa,
                        "kl_divergence": kl,
                        "relative_perf_drop": rpd,
                    })
                    print(
                        f"  [{MODEL_LABEL[model_type]:6s}, p={spurious_p}, {condition:10s}] "
                        f"AA={aa:.3f}  J_I={j_intuitive:.3f}  J_R={j_reasoned:.3f}"
                    )

    df = pd.DataFrame(records)
    csv_path = output_dir / "metrics.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nmetrics.csv を保存: {csv_path}")

    _save_gridworld_comparison_plot(df, output_dir)
    _save_summary(df, ["model_type", "spurious_p", "eval_condition"], output_dir)


def _save_gridworld_comparison_plot(df: pd.DataFrame, output_dir: Path) -> None:
    """p=0.0 の train / reversed_c 条件で AA・J を比較するバーチャート。"""
    d = df[(df["spurious_p"] == 0.0)]
    model_types = d["model_type"].unique().tolist()
    conditions = ["train", "reversed_c"]
    colors = {"moet": "steelblue", "linear": "tomato", "tree": "seagreen"}

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    # AA
    ax = axes[0]
    x = np.arange(len(conditions))
    width = 0.25
    for i, mt in enumerate(model_types):
        means = [
            d[(d["model_type"] == mt) & (d["eval_condition"] == c)]["action_agreement"].mean()
            for c in conditions
        ]
        stds = [
            d[(d["model_type"] == mt) & (d["eval_condition"] == c)]["action_agreement"].std()
            for c in conditions
        ]
        offset = (i - len(model_types) / 2 + 0.5) * width
        ax.bar(x + offset, means, width, yerr=stds, capsize=4,
               color=colors.get(mt, "gray"), alpha=0.85, label=MODEL_LABEL.get(mt, mt))
    ax.set_xticks(x)
    ax.set_xticklabels(conditions)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Action Agreement (AA)")
    ax.set_title("AA: train vs reversed_c  (p=0.0)")
    ax.legend()
    ax.axhline(1.0, color="gray", linestyle=":", linewidth=0.8)

    # J_reasoned
    ax = axes[1]
    for i, mt in enumerate(model_types):
        means = [
            d[(d["model_type"] == mt) & (d["eval_condition"] == c)]["j_reasoned"].mean()
            for c in conditions
        ]
        stds = [
            d[(d["model_type"] == mt) & (d["eval_condition"] == c)]["j_reasoned"].std()
            for c in conditions
        ]
        offset = (i - len(model_types) / 2 + 0.5) * width
        ax.bar(x + offset, means, width, yerr=stds, capsize=4,
               color=colors.get(mt, "gray"), alpha=0.85, label=MODEL_LABEL.get(mt, mt))
    ax.set_xticks(x)
    ax.set_xticklabels(conditions)
    ax.set_ylabel("Mean episode reward ($J_R$)")
    ax.set_title("$J_R$: train vs reversed_c  (p=0.0)")
    ax.legend()
    ax.axhline(0, color="black", linestyle="--", linewidth=0.7)

    fig.suptitle("GridWorld model comparison (p=0.0)")
    plt.tight_layout()
    out = output_dir / "comparison_gridworld_p0.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"図を保存: {out}")


# ---------------------------------------------------------------------------
# 共通サマリー
# ---------------------------------------------------------------------------

def _save_summary(df: pd.DataFrame, group_keys: list[str], output_dir: Path) -> None:
    lines = ["=== モデル比較サマリー ===\n"]
    mean_df = df.groupby(group_keys)[
        ["action_agreement", "j_intuitive", "j_reasoned", "relative_perf_drop"]
    ].agg(["mean", "std"])

    for idx, row in mean_df.iterrows():
        key_str = "  ".join(f"{k}={v}" for k, v in zip(group_keys, (idx if isinstance(idx, tuple) else (idx,))))
        aa = f"AA={row[('action_agreement','mean')]:.3f}±{row[('action_agreement','std')]:.3f}"
        ji = f"J_I={row[('j_intuitive','mean')]:.2f}"
        jr = f"J_R={row[('j_reasoned','mean')]:.2f}"
        rpd = f"RPD={row[('relative_perf_drop','mean')]:.3f}±{row[('relative_perf_drop','std')]:.3f}"
        lines.append(f"  {key_str}  |  {aa}  {ji}  {jr}  {rpd}")

    summary_path = output_dir / "summary.txt"
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"summary.txt を保存: {summary_path}")
    print("\n" + "\n".join(lines[:30]))


# ---------------------------------------------------------------------------
# エントリポイント
# ---------------------------------------------------------------------------

def run_experiment(cfg: dict) -> None:
    env_cfg = cfg.get("env", {})
    if "noise_dims" in env_cfg:
        run_cartpole_comparison(cfg)
    elif "spurious_p_values" in env_cfg:
        run_gridworld_comparison(cfg)
    else:
        raise ValueError("config の env に noise_dims または spurious_p_values が必要です。")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    run_experiment(cfg)


if __name__ == "__main__":
    main()
