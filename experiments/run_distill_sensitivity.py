"""実験6: 蒸留データ量の感度分析。

distill_n_samples ∈ [1k, 5k, 10k, 20k] で
CartPole (N=0) と GridWorld (p=0.0, 0.5) に対して
MoET / Tree / Linear の AA がどう変化するかを調べる。
Intuitive policy は exp001 / exp002 の学習済みモデルを再利用する。

使い方:
    python experiments/run.py --config experiments/configs/exp006_distill_sensitivity.yaml
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from stable_baselines3 import DQN

from experiments.src.moet import SoftMoET
from experiments.src.distill import distill
from experiments.src.baselines import LinearReasonedModel, SingleTreeReasonedModel
from experiments.src.evaluate import action_agreement, kl_divergence, evaluate_rollout, relative_perf_drop
from experiments.run_comparison import make_model, fit_model

MODEL_LABEL = {"moet": "MoET", "linear": "Linear", "tree": "Tree"}
COLORS = {"moet": "steelblue", "linear": "tomato", "tree": "seagreen"}


# ---------------------------------------------------------------------------
# CartPole 感度分析
# ---------------------------------------------------------------------------

def run_cartpole_sensitivity(cfg: dict, output_dir: Path) -> pd.DataFrame:
    from experiments.src.cartpole_env import NoisyCartPoleEnv
    from experiments.src.cartpole_intuitive import collect_transitions, evaluate_intuitive

    noise_dim: int = cfg["cartpole"]["noise_dim"]
    reuse_from: str = cfg["cartpole"]["reuse_from"]
    input_dim = 4 + noise_dim
    n_actions = 2

    seeds: list[int] = cfg["evaluation"]["seeds"]
    n_eval_episodes: int = cfg["evaluation"]["n_eval_episodes"]
    distill_n_samples_list: list[int] = cfg["distill_n_samples_list"]
    eval_n_samples: int = cfg["comparison"]["eval_n_samples"]
    comp_cfg: dict = cfg["comparison"]

    records = []

    for seed in seeds:
        # Intuitive policy の読み込み
        candidate = ROOT / reuse_from / f"intuitive_N{noise_dim}_seed{seed}.zip"
        if not candidate.exists():
            print(f"  [CartPole seed={seed}] モデルが見つかりません: {candidate}", flush=True)
            continue
        env = NoisyCartPoleEnv(noise_dim=noise_dim)
        model = DQN.load(str(candidate), env=env)
        j_intuitive = evaluate_intuitive(model, noise_dim, n_eval_episodes, seed)
        eval_seed = seed + 10000

        # 最大サンプル数を一度収集しておき、サブセットで使い回す
        max_n = max(distill_n_samples_list)
        obs_all, act_all = collect_transitions(model, noise_dim, max_n, seed)
        obs_eval, act_eval = collect_transitions(model, noise_dim, eval_n_samples, eval_seed)

        for n_distill in distill_n_samples_list:
            obs_d = obs_all[:n_distill]
            act_d = act_all[:n_distill]

            for model_type in comp_cfg["model_types"]:
                rm = make_model(model_type, input_dim, n_actions, comp_cfg)
                rm = fit_model(rm, obs_d, act_d, comp_cfg)

                aa = action_agreement(obs_eval, act_eval, rm)
                kl = kl_divergence(obs_eval, model, rm, n_actions)

                eval_env = NoisyCartPoleEnv(noise_dim=noise_dim)
                j_reasoned = evaluate_rollout(rm, eval_env, n_eval_episodes, eval_seed)
                eval_env.close()

                rpd = relative_perf_drop(j_intuitive, j_reasoned)

                records.append({
                    "env": "cartpole",
                    "model_type": model_type,
                    "distill_n_samples": n_distill,
                    "seed": seed,
                    "j_intuitive": j_intuitive,
                    "j_reasoned": j_reasoned,
                    "action_agreement": aa,
                    "kl_divergence": kl,
                    "relative_perf_drop": rpd,
                })
                print(
                    f"  [CartPole, {MODEL_LABEL[model_type]:6s}, n={n_distill:5d}, seed={seed}]"
                    f"  AA={aa:.3f}  KL={kl:.4f}",
                    flush=True,
                )

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# GridWorld 感度分析
# ---------------------------------------------------------------------------

def run_gridworld_sensitivity(cfg: dict, output_dir: Path) -> pd.DataFrame:
    from experiments.src.gridworld_env import SpuriousGridWorld
    from experiments.run_gridworld import collect_gridworld_transitions, eval_states_for_condition, evaluate_intuitive_gridworld

    spurious_p_values: list[float] = cfg["gridworld"]["spurious_p_values"]
    eval_conditions: list[str] = cfg["gridworld"]["eval_conditions"]
    reuse_from: str = cfg["gridworld"]["reuse_from"]

    seeds: list[int] = cfg["evaluation"]["seeds"]
    n_eval_episodes: int = cfg["evaluation"]["n_eval_episodes"]
    distill_n_samples_list: list[int] = cfg["distill_n_samples_list"]
    eval_n_samples: int = cfg["comparison"]["eval_n_samples"]
    comp_cfg: dict = cfg["comparison"]
    n_actions = 4

    records = []

    for spurious_p in spurious_p_values:
        for seed in seeds:
            # Intuitive policy の読み込み（ディレクトリ形式）
            candidate = ROOT / reuse_from / f"intuitive_p{spurious_p}_seed{seed}"
            if not candidate.exists():
                candidate_zip = ROOT / reuse_from / f"intuitive_p{spurious_p}_seed{seed}.zip"
                if candidate_zip.exists():
                    candidate = candidate_zip
                else:
                    print(f"  [GridWorld p={spurious_p} seed={seed}] モデルが見つかりません", flush=True)
                    continue

            env = SpuriousGridWorld(spurious_p=spurious_p)
            model = DQN.load(str(candidate), env=env)
            env.close()
            eval_seed = seed + 10000

            # 最大サンプル数を一度収集
            max_n = max(distill_n_samples_list)
            obs_all, act_all = collect_gridworld_transitions(model, spurious_p, max_n, seed)
            obs_eval_base, _ = collect_gridworld_transitions(model, spurious_p, eval_n_samples, eval_seed)
            input_dim = obs_all.shape[1]

            for n_distill in distill_n_samples_list:
                obs_d = obs_all[:n_distill]
                act_d = act_all[:n_distill]

                for model_type in comp_cfg["model_types"]:
                    rm = make_model(model_type, input_dim, n_actions, comp_cfg)
                    rm = fit_model(rm, obs_d, act_d, comp_cfg)

                    for condition in eval_conditions:
                        obs_shifted = eval_states_for_condition(obs_eval_base, condition)
                        intuitive_actions, _ = model.predict(obs_shifted, deterministic=True)
                        aa = action_agreement(obs_shifted, intuitive_actions, rm)
                        kl = kl_divergence(obs_shifted, model, rm, n_actions)

                        eval_mode_str = None if condition == "train" else (
                            "random" if condition == "random_c" else "reversed"
                        )
                        j_intuitive = evaluate_intuitive_gridworld(
                            model, spurious_p, eval_mode_str, n_eval_episodes, eval_seed
                        )
                        eval_env = SpuriousGridWorld(spurious_p=spurious_p, eval_mode=eval_mode_str)
                        j_reasoned = evaluate_rollout(rm, eval_env, n_eval_episodes, eval_seed)
                        eval_env.close()

                        rpd = relative_perf_drop(j_intuitive, j_reasoned)

                        records.append({
                            "env": "gridworld",
                            "model_type": model_type,
                            "spurious_p": spurious_p,
                            "eval_condition": condition,
                            "distill_n_samples": n_distill,
                            "seed": seed,
                            "j_intuitive": j_intuitive,
                            "j_reasoned": j_reasoned,
                            "action_agreement": aa,
                            "kl_divergence": kl,
                            "relative_perf_drop": rpd,
                        })

                    print(
                        f"  [GridWorld p={spurious_p}, {MODEL_LABEL[model_type]:6s},"
                        f" n={n_distill:5d}, seed={seed}]"
                        f"  AA(train)={records[-3]['action_agreement']:.3f}"
                        f"  AA(rev)={records[-1]['action_agreement']:.3f}",
                        flush=True,
                    )

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# 可視化
# ---------------------------------------------------------------------------

def _plot_sensitivity(df: pd.DataFrame, output_dir: Path) -> None:
    """AA vs distill_n_samples の折れ線グラフを保存する。"""
    # --- CartPole ---
    cp = df[df["env"] == "cartpole"]
    if not cp.empty:
        fig, ax = plt.subplots(figsize=(6, 4))
        for mt in cp["model_type"].unique():
            sub = cp[cp["model_type"] == mt].groupby("distill_n_samples")["action_agreement"]
            means = sub.mean()
            stds = sub.std()
            ax.plot(means.index, means.values, marker="o", label=MODEL_LABEL.get(mt, mt),
                    color=COLORS.get(mt, "gray"))
            ax.fill_between(means.index, means - stds, means + stds,
                            alpha=0.15, color=COLORS.get(mt, "gray"))
        ax.set_xlabel("Distillation samples")
        ax.set_ylabel("Action Agreement (AA)")
        ax.set_xscale("log")
        ax.set_ylim(0.5, 1.05)
        ax.set_title("CartPole (N=0): AA vs distillation data size")
        ax.legend()
        ax.axhline(1.0, color="gray", linestyle=":", linewidth=0.8)
        plt.tight_layout()
        out = output_dir / "sensitivity_cartpole.png"
        plt.savefig(out, dpi=120, bbox_inches="tight")
        plt.close()
        print(f"図を保存: {out}", flush=True)

    # --- GridWorld ---
    gw = df[df["env"] == "gridworld"]
    if not gw.empty:
        for p_val in sorted(gw["spurious_p"].unique()):
            fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=True)
            for ax, cond in zip(axes, ["train", "random_c", "reversed_c"]):
                sub_cond = gw[(gw["spurious_p"] == p_val) & (gw["eval_condition"] == cond)]
                for mt in sub_cond["model_type"].unique():
                    sub = sub_cond[sub_cond["model_type"] == mt].groupby("distill_n_samples")["action_agreement"]
                    means = sub.mean()
                    stds = sub.std()
                    ax.plot(means.index, means.values, marker="o",
                            label=MODEL_LABEL.get(mt, mt), color=COLORS.get(mt, "gray"))
                    ax.fill_between(means.index, means - stds, means + stds,
                                    alpha=0.15, color=COLORS.get(mt, "gray"))
                ax.set_xlabel("Distillation samples")
                ax.set_ylabel("Action Agreement (AA)")
                ax.set_xscale("log")
                ax.set_ylim(0.3, 1.05)
                ax.set_title(f"{cond}")
                ax.legend(fontsize=8)
                ax.axhline(1.0, color="gray", linestyle=":", linewidth=0.8)
            fig.suptitle(f"GridWorld (p={p_val}): AA vs distillation data size")
            plt.tight_layout()
            p_str = str(p_val).replace(".", "")
            out = output_dir / f"sensitivity_gridworld_p{p_str}.png"
            plt.savefig(out, dpi=120, bbox_inches="tight")
            plt.close()
            print(f"図を保存: {out}", flush=True)


def _save_summary(df: pd.DataFrame, output_dir: Path) -> None:
    lines = ["=== 蒸留データ量感度分析サマリー ===\n"]

    # CartPole
    cp = df[df["env"] == "cartpole"]
    if not cp.empty:
        lines.append("【CartPole N=0】")
        grp = cp.groupby(["model_type", "distill_n_samples"])["action_agreement"].agg(["mean", "std"])
        for (mt, n), row in grp.iterrows():
            lines.append(f"  {MODEL_LABEL.get(mt, mt):6s}  n={n:5d}  AA={row['mean']:.3f}±{row['std']:.3f}")
        lines.append("")

    # GridWorld
    gw = df[df["env"] == "gridworld"]
    if not gw.empty:
        for p_val in sorted(gw["spurious_p"].unique()):
            lines.append(f"【GridWorld p={p_val}】")
            grp = gw[gw["spurious_p"] == p_val].groupby(
                ["model_type", "distill_n_samples", "eval_condition"]
            )["action_agreement"].agg(["mean", "std"])
            for (mt, n, cond), row in grp.iterrows():
                lines.append(
                    f"  {MODEL_LABEL.get(mt, mt):6s}  n={n:5d}  {cond:12s}"
                    f"  AA={row['mean']:.3f}±{row['std']:.3f}"
                )
            lines.append("")

    path = output_dir / "summary.txt"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"summary.txt を保存: {path}", flush=True)
    print("\n" + "\n".join(lines[:40]))


# ---------------------------------------------------------------------------
# エントリポイント
# ---------------------------------------------------------------------------

def run_experiment(cfg: dict) -> None:
    output_dir = ROOT / cfg["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    all_records = []

    print("=== CartPole 感度分析 ===", flush=True)
    cp_df = run_cartpole_sensitivity(cfg, output_dir)
    all_records.append(cp_df)

    print("\n=== GridWorld 感度分析 ===", flush=True)
    gw_df = run_gridworld_sensitivity(cfg, output_dir)
    all_records.append(gw_df)

    df = pd.concat([d for d in all_records if not d.empty], ignore_index=True)
    csv_path = output_dir / "metrics.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nmetrics.csv を保存: {csv_path}", flush=True)

    _plot_sensitivity(df, output_dir)
    _save_summary(df, output_dir)
