"""SHAP による特徴寄与度分析。

既存の学習済みモデル・eval_states を使って SHAP 値を計算し、
「SHAP が c（スプリアス特徴）を重要と評価するが、その依存が正当かは判定できない」
ことを定量的に示す。

使い方:
    python experiments/shap_analysis.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import shap
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from stable_baselines3 import DQN

# 日本語フォント設定
_JP_FONTS = ["Yu Gothic", "Meiryo", "MS Gothic", "IPAexGothic", "Noto Sans CJK JP"]
for _f in _JP_FONTS:
    if any(_f.lower() in f.name.lower() for f in font_manager.fontManager.ttflist):
        matplotlib.rcParams["font.family"] = _f
        break

RESULTS_DIR = ROOT / "experiments" / "results" / "exp002_spurious_gridworld"
FEATURE_NAMES = ["agent_x", "agent_y", "c (spurious)"]
N_ACTIONS = 4
SHAP_BG_SAMPLES = 200   # KernelExplainer のバックグラウンドサンプル数
SHAP_EVAL_SAMPLES = 500  # SHAP 値を計算するサンプル数


# ---------------------------------------------------------------------------
# モデルのQ値出力関数（SHAP に渡す予測関数）
# ---------------------------------------------------------------------------

def make_predict_fn(model: DQN):
    """DQN の Q値を返す関数を作る（SHAP 用）。"""
    def predict_fn(obs: np.ndarray) -> np.ndarray:
        obs_t = torch.FloatTensor(obs)
        with torch.no_grad():
            q_values = model.q_net(obs_t).numpy()
        return q_values  # shape: (n_samples, n_actions)
    return predict_fn


# ---------------------------------------------------------------------------
# SHAP 分析
# ---------------------------------------------------------------------------

def compute_shap_for_condition(
    model: DQN,
    obs_eval: np.ndarray,
    condition: str,
) -> np.ndarray:
    """指定した eval 条件の状態で SHAP 値を計算する。

    Returns
    -------
    shap_values : np.ndarray, shape (n_samples, n_features)
        各サンプル・各特徴の SHAP 値（行動ごとの絶対値平均）
    """
    obs = _apply_condition(obs_eval, condition)
    obs_bg = obs[:SHAP_BG_SAMPLES]
    obs_test = obs[:SHAP_EVAL_SAMPLES]

    predict_fn = make_predict_fn(model)
    explainer = shap.KernelExplainer(predict_fn, obs_bg)

    # shap_values: list of (n_samples, n_features) per action, or ndarray of various shapes
    shap_vals = explainer.shap_values(obs_test, nsamples=100, silent=True)

    # 行動ごとの |SHAP| を平均して特徴の「平均的な重要度」とする
    if isinstance(shap_vals, list):
        # list of arrays, each (n_samples, n_features)
        stacked = np.stack([np.abs(np.array(sv, dtype=float)) for sv in shap_vals], axis=0)
        abs_mean = stacked.mean(axis=0)  # (n_samples, n_features)
    else:
        arr = np.array(shap_vals, dtype=float)
        if arr.ndim == 3:
            # (n_actions, n_samples, n_features) or (n_samples, n_features, n_actions)
            if arr.shape[0] == N_ACTIONS:
                abs_mean = np.abs(arr).mean(axis=0)
            else:
                abs_mean = np.abs(arr).mean(axis=-1)
        else:
            abs_mean = np.abs(arr)

    # 確実に (n_samples, n_features) になるよう整形
    abs_mean = np.array(abs_mean, dtype=float)
    if abs_mean.ndim == 1:
        abs_mean = abs_mean.reshape(1, -1)
    return abs_mean  # (n_samples, n_features)


def _apply_condition(obs: np.ndarray, condition: str) -> np.ndarray:
    obs = obs.copy()
    if condition == "random_c":
        obs[:, 2] = np.random.randint(0, 2, len(obs)).astype(np.float32)
    elif condition == "reversed_c":
        obs[:, 2] = 1.0 - obs[:, 2]
    return obs


# ---------------------------------------------------------------------------
# メイン分析
# ---------------------------------------------------------------------------

def run_shap_analysis():
    spurious_p_values = [0.0, 0.2, 0.5]
    seeds = [42, 123, 456]
    conditions = ["train", "random_c", "reversed_c"]

    records = []

    for sp in spurious_p_values:
        for seed in seeds:
            # モデルをロード
            model_path = RESULTS_DIR / f"intuitive_p{sp}_seed{seed}"
            if not model_path.with_suffix(".zip").exists():
                # SB3 は .zip を自動付与するが、保存時のパスに依存
                model_path_zip = str(model_path)
            else:
                model_path_zip = str(model_path)

            from experiments.src.gridworld_env import SpuriousGridWorld
            env = SpuriousGridWorld(spurious_p=sp)
            model = DQN.load(model_path_zip, env=env)

            # eval_states をロード
            eval_states_path = RESULTS_DIR / f"eval_states_p{sp}_seed{seed}.npy"
            if not eval_states_path.exists():
                print(f"  eval_states が見つかりません: {eval_states_path}")
                continue
            obs_eval = np.load(eval_states_path)

            print(f"[p={sp}, seed={seed}] SHAP 計算中...")

            for cond in conditions:
                shap_abs = compute_shap_for_condition(model, obs_eval, cond)
                mean_importance = shap_abs.mean(axis=0).flatten()  # (n_features,)

                for feat_idx, feat_name in enumerate(FEATURE_NAMES):
                    records.append({
                        "spurious_p": sp,
                        "seed": seed,
                        "eval_condition": cond,
                        "feature": feat_name,
                        "mean_abs_shap": float(mean_importance[feat_idx]),
                    })

            env.close()

    df = pd.DataFrame(records)
    csv_path = RESULTS_DIR / "shap_values.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nSHAP 値を保存: {csv_path}")

    _plot_shap_importance(df)
    _plot_shap_vs_validity(df)
    _save_shap_summary(df)

    print(f"\nSHAP 分析完了: {RESULTS_DIR}")


# ---------------------------------------------------------------------------
# 可視化
# ---------------------------------------------------------------------------

def _plot_shap_importance(df: pd.DataFrame) -> None:
    """spurious_p × eval_condition ごとの特徴重要度棒グラフ。"""
    mean_df = df.groupby(["spurious_p", "eval_condition", "feature"])[
        "mean_abs_shap"
    ].mean().reset_index()

    sp_values = [0.0, 0.2, 0.5]
    conditions = ["train", "random_c", "reversed_c"]
    features = FEATURE_NAMES
    x = np.arange(len(features))
    colors = {"train": "steelblue", "random_c": "orange", "reversed_c": "tomato"}

    fig, axes = plt.subplots(1, len(sp_values), figsize=(5 * len(sp_values), 5), sharey=False)

    for ax, sp in zip(axes, sp_values):
        width = 0.25
        for i, cond in enumerate(conditions):
            sub = mean_df[
                (mean_df["spurious_p"] == sp) & (mean_df["eval_condition"] == cond)
            ].set_index("feature")
            vals = [sub.loc[f, "mean_abs_shap"] if f in sub.index else 0 for f in features]
            ax.bar(x + i * width, vals, width, label=cond, color=colors[cond])
        ax.set_xticks(x + width)
        ax.set_xticklabels(features, fontsize=9)
        ax.set_ylabel("Mean |SHAP value|")
        ax.set_title(f"spurious_p={sp}")
        ax.legend(fontsize=8)

    fig.suptitle("SHAP 特徴重要度：評価条件別")
    plt.tight_layout()
    path = RESULTS_DIR / "shap_importance_gridworld.png"
    plt.savefig(path, dpi=100)
    plt.close()
    print(f"  保存: {path}")


def _plot_shap_vs_validity(df: pd.DataFrame) -> None:
    """c の SHAP 重要度 vs 実際の説明妥当性の対比図。

    左軸：c の mean |SHAP|（train 条件）
    右軸：reversed_c での AA（既存 metrics.csv から取得）
    """
    # SHAP 側：train 条件での c の重要度
    shap_c = df[
        (df["eval_condition"] == "train") & (df["feature"] == "c (spurious)")
    ].groupby("spurious_p")["mean_abs_shap"].mean()

    # AA 側：metrics.csv から reversed_c での AA を取得
    metrics_path = RESULTS_DIR / "metrics.csv"
    if not metrics_path.exists():
        print("  metrics.csv が見つかりません、AA プロットをスキップ")
        return
    mdf = pd.read_csv(metrics_path)
    aa_reversed = mdf[mdf["eval_condition"] == "reversed_c"].groupby("spurious_p")[
        "action_agreement"
    ].mean()

    sp_vals = [0.0, 0.2, 0.5]
    shap_vals = [shap_c.get(sp, 0) for sp in sp_vals]
    aa_vals = [aa_reversed.get(sp, 0) for sp in sp_vals]

    fig, ax1 = plt.subplots(figsize=(7, 5))
    ax2 = ax1.twinx()

    color_shap = "steelblue"
    color_aa = "tomato"

    ax1.plot(sp_vals, shap_vals, "o-", color=color_shap, linewidth=2, label="c の SHAP 重要度")
    ax1.set_xlabel("Spurious strength p")
    ax1.set_ylabel("Mean |SHAP| of c (train)", color=color_shap)
    ax1.tick_params(axis="y", labelcolor=color_shap)

    ax2.plot(sp_vals, aa_vals, "s--", color=color_aa, linewidth=2, label="AA (reversed_c)")
    ax2.set_ylabel("Action Agreement under reversed_c", color=color_aa)
    ax2.tick_params(axis="y", labelcolor=color_aa)
    ax2.set_ylim(0, 1.1)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

    ax1.set_title(
        "SHAP 重要度 vs 分布シフト下での AA\n"
        "→ SHAP が c を重要と評価しても、依存の正当性は判定できない"
    )
    ax1.grid(True, alpha=0.3)
    plt.tight_layout()
    path = RESULTS_DIR / "shap_vs_validity_gridworld.png"
    plt.savefig(path, dpi=100)
    plt.close()
    print(f"  保存: {path}")


def _save_shap_summary(df: pd.DataFrame) -> None:
    mean_df = df.groupby(["spurious_p", "eval_condition", "feature"])[
        "mean_abs_shap"
    ].mean().reset_index()

    lines = ["=== SHAP 特徴重要度サマリー（GridWorld） ===\n"]
    for sp in [0.0, 0.2, 0.5]:
        lines.append(f"\n--- spurious_p={sp} ---")
        for cond in ["train", "random_c", "reversed_c"]:
            sub = mean_df[
                (mean_df["spurious_p"] == sp) & (mean_df["eval_condition"] == cond)
            ].set_index("feature")
            vals = "  ".join(
                f"{f}: {sub.loc[f, 'mean_abs_shap']:.4f}"
                for f in FEATURE_NAMES
                if f in sub.index
            )
            lines.append(f"  {cond:12s}: {vals}")

    path = RESULTS_DIR / "shap_summary.txt"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  保存: {path}")


if __name__ == "__main__":
    run_shap_analysis()
