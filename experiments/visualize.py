"""実験結果の可視化スクリプト。

既存の metrics.csv を読み込んで図を生成する。実験を再実行しない。

使い方:
    # 実験1（CartPole）
    python experiments/visualize.py --exp exp001

    # 実験2（GridWorld）
    python experiments/visualize.py --exp exp002

    # 両方
    python experiments/visualize.py --exp all
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import font_manager

# Windows 日本語フォント設定
_JP_FONTS = ["Yu Gothic", "Meiryo", "MS Gothic", "IPAexGothic", "Noto Sans CJK JP"]
for _f in _JP_FONTS:
    if any(_f.lower() in f.name.lower() for f in font_manager.fontManager.ttflist):
        matplotlib.rcParams["font.family"] = _f
        break


# ---------------------------------------------------------------------------
# 実験1：CartPole
# ---------------------------------------------------------------------------

def visualize_cartpole(results_dir: Path) -> None:
    csv_path = results_dir / "metrics.csv"
    if not csv_path.exists():
        print(f"[CartPole] metrics.csv が見つかりません: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    out = results_dir

    # --- J_intuitive / J_reasoned の絶対値サマリー ---
    _cartpole_j_summary(df, out)

    # --- AA × ノイズ次元 の折れ線（depth別） ---
    _cartpole_aa_by_noise(df, out)

    # --- AA ヒートマップ（noise_dim × d, K=4 固定） ---
    _cartpole_aa_heatmap_by_noise(df, out)

    print(f"[CartPole] 可視化完了: {out}")


def _cartpole_j_summary(df: pd.DataFrame, out: Path) -> None:
    """J_intuitive と J_reasoned を noise_dim × depth で表示。"""
    mean_df = df.groupby(["noise_dim", "max_depth"])[
        ["j_intuitive", "j_reasoned"]
    ].mean().reset_index()

    noise_dims = sorted(mean_df["noise_dim"].unique())
    depths = sorted(mean_df["max_depth"].unique())

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    for ax, col, label in zip(axes, ["j_intuitive", "j_reasoned"], ["J_intuitive", "J_reasoned"]):
        pivot = mean_df.pivot(index="noise_dim", columns="max_depth", values=col)
        im = ax.imshow(pivot.values, aspect="auto", cmap="YlGn")
        ax.set_xticks(range(len(depths)))
        ax.set_xticklabels(depths)
        ax.set_yticks(range(len(noise_dims)))
        ax.set_yticklabels(noise_dims)
        ax.set_xlabel("max_depth")
        ax.set_ylabel("noise_dim (N)")
        ax.set_title(label)
        plt.colorbar(im, ax=ax)
        # セル内に数値を表示
        for i in range(len(noise_dims)):
            for j in range(len(depths)):
                val = pivot.values[i, j]
                ax.text(j, i, f"{val:.0f}", ha="center", va="center",
                        fontsize=8, color="black")

    fig.suptitle("CartPole: 平均エピソード報酬（K=2,3,4 の平均）")
    plt.tight_layout()
    path = out / "j_values_cartpole.png"
    plt.savefig(path, dpi=100)
    plt.close()
    print(f"  保存: {path}")

    # テキストサマリーも更新
    lines = ["=== J_intuitive / J_reasoned サマリー (CartPole) ===\n"]
    summary = df.groupby(["noise_dim", "max_depth"])[
        ["j_intuitive", "j_reasoned", "action_agreement", "relative_perf_drop"]
    ].agg(["mean", "std"])
    for (nd, d), row in summary.iterrows():
        ji = row[("j_intuitive", "mean")]
        jr = row[("j_reasoned", "mean")]
        aa = row[("action_agreement", "mean")]
        lines.append(
            f"N={nd:2d}, d={d}: J_i={ji:6.1f}  J_r={jr:6.1f}  "
            f"diff={ji-jr:+6.1f}  AA={aa:.3f}"
        )
    (out / "j_summary_cartpole.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"  保存: {out / 'j_summary_cartpole.txt'}")


def _cartpole_aa_by_noise(df: pd.DataFrame, out: Path) -> None:
    """AA を noise_dim の関数として、depth ごとに折れ線プロット。"""
    mean_df = df.groupby(["noise_dim", "max_depth"])["action_agreement"].mean().reset_index()
    depths = sorted(mean_df["max_depth"].unique())
    noise_dims = sorted(mean_df["noise_dim"].unique())

    fig, ax = plt.subplots(figsize=(7, 5))
    for d in depths:
        sub = mean_df[mean_df["max_depth"] == d]
        ax.plot(sub["noise_dim"], sub["action_agreement"], marker="o", label=f"depth={d}")
    ax.set_xlabel("Noise dimensions (N)")
    ax.set_ylabel("Action Agreement (mean over K, seeds)")
    ax.set_title("CartPole: Action Agreement vs Noise Dimensions")
    ax.legend()
    ax.set_ylim(0.7, 1.0)
    ax.grid(True, alpha=0.3)
    path = out / "aa_vs_noise_cartpole.png"
    plt.tight_layout()
    plt.savefig(path, dpi=100)
    plt.close()
    print(f"  保存: {path}")


def _cartpole_aa_heatmap_by_noise(df: pd.DataFrame, out: Path) -> None:
    """noise_dim × depth のヒートマップ（K=4 固定）。"""
    sub = df[df["n_experts"] == 4].groupby(
        ["noise_dim", "max_depth"]
    )["action_agreement"].mean().unstack()

    fig, ax = plt.subplots(figsize=(7, 4))
    im = ax.imshow(sub.values, vmin=0.75, vmax=1.0, aspect="auto", cmap="RdYlGn")
    ax.set_xticks(range(len(sub.columns)))
    ax.set_xticklabels(sub.columns)
    ax.set_yticks(range(len(sub.index)))
    ax.set_yticklabels(sub.index)
    ax.set_xlabel("max_depth")
    ax.set_ylabel("noise_dim (N)")
    ax.set_title("CartPole: Action Agreement Heatmap (K=4)")
    for i in range(len(sub.index)):
        for j in range(len(sub.columns)):
            ax.text(j, i, f"{sub.values[i,j]:.2f}", ha="center", va="center", fontsize=9)
    plt.colorbar(im, ax=ax)
    plt.tight_layout()
    path = out / "aa_heatmap_nd_cartpole.png"
    plt.savefig(path, dpi=100)
    plt.close()
    print(f"  保存: {path}")


# ---------------------------------------------------------------------------
# 実験2：GridWorld
# ---------------------------------------------------------------------------

def visualize_gridworld(results_dir: Path) -> None:
    csv_path = results_dir / "metrics.csv"
    if not csv_path.exists():
        print(f"[GridWorld] metrics.csv が見つかりません: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    out = results_dir

    _gridworld_j_summary(df, out)
    _gridworld_aa_shift(df, out)
    _gridworld_aa_depth_transition(df, out)

    print(f"[GridWorld] 可視化完了: {out}")


def _gridworld_j_summary(df: pd.DataFrame, out: Path) -> None:
    """J_intuitive / J_reasoned を条件・spurious_p ごとに表示。"""
    mean_df = df.groupby(["spurious_p", "eval_condition"])[
        ["j_intuitive", "j_reasoned"]
    ].mean().reset_index()

    conditions = ["train", "random_c", "reversed_c"]
    sp_values = sorted(mean_df["spurious_p"].unique())

    fig, axes = plt.subplots(1, len(sp_values), figsize=(5 * len(sp_values), 5))
    if len(sp_values) == 1:
        axes = [axes]

    for ax, sp in zip(axes, sp_values):
        sub = mean_df[mean_df["spurious_p"] == sp].set_index("eval_condition")
        x = range(len(conditions))
        ji_vals = [sub.loc[c, "j_intuitive"] if c in sub.index else 0 for c in conditions]
        jr_vals = [sub.loc[c, "j_reasoned"] if c in sub.index else 0 for c in conditions]
        width = 0.35
        ax.bar([i - width/2 for i in x], ji_vals, width, label="J_intuitive", color="steelblue")
        ax.bar([i + width/2 for i in x], jr_vals, width, label="J_reasoned", color="coral")
        ax.set_xticks(list(x))
        ax.set_xticklabels(conditions, rotation=15)
        ax.set_ylabel("Mean episode reward")
        ax.set_title(f"spurious_p={sp}")
        ax.legend()
        ax.axhline(0, color="black", linewidth=0.8, linestyle="--")

    fig.suptitle("GridWorld: J_intuitive vs J_reasoned by eval condition")
    plt.tight_layout()
    path = out / "j_values_gridworld.png"
    plt.savefig(path, dpi=100)
    plt.close()
    print(f"  保存: {path}")

    # テキストサマリー
    lines = ["=== J_intuitive / J_reasoned サマリー (GridWorld) ===\n"]
    summary = df.groupby(["spurious_p", "eval_condition", "max_depth"])[
        ["j_intuitive", "j_reasoned", "action_agreement"]
    ].mean()
    for (sp, cond, d), row in summary.iterrows():
        lines.append(
            f"p={sp}, {cond:12s}, d={d}: "
            f"J_i={row['j_intuitive']:7.3f}  J_r={row['j_reasoned']:7.3f}  "
            f"diff={row['j_intuitive']-row['j_reasoned']:+7.3f}  AA={row['action_agreement']:.3f}"
        )
    (out / "j_summary_gridworld.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"  保存: {out / 'j_summary_gridworld.txt'}")


def _gridworld_aa_shift(df: pd.DataFrame, out: Path) -> None:
    """評価条件（train / random_c / reversed_c）間での AA の変化を spurious_p 別に表示。"""
    mean_df = df.groupby(["spurious_p", "eval_condition", "max_depth"])[
        "action_agreement"
    ].mean().reset_index()

    sp_values = sorted(mean_df["spurious_p"].unique())
    conditions = ["train", "random_c", "reversed_c"]
    depths = sorted(mean_df["max_depth"].unique())
    colors = plt.cm.viridis(np.linspace(0.2, 0.9, len(depths)))

    fig, axes = plt.subplots(1, len(sp_values), figsize=(5 * len(sp_values), 5), sharey=True)
    if len(sp_values) == 1:
        axes = [axes]

    for ax, sp in zip(axes, sp_values):
        sub = mean_df[mean_df["spurious_p"] == sp]
        for d, color in zip(depths, colors):
            row = sub[sub["max_depth"] == d]
            vals = [
                row[row["eval_condition"] == c]["action_agreement"].values[0]
                if len(row[row["eval_condition"] == c]) > 0 else np.nan
                for c in conditions
            ]
            ax.plot(conditions, vals, marker="o", label=f"d={d}", color=color)
        ax.set_title(f"spurious_p={sp}")
        ax.set_ylabel("Action Agreement")
        ax.set_ylim(0.3, 1.05)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    fig.suptitle("GridWorld: AA across eval conditions (K=4)")
    plt.tight_layout()
    path = out / "aa_shift_gridworld.png"
    plt.savefig(path, dpi=100)
    plt.close()
    print(f"  保存: {path}")


def _gridworld_aa_depth_transition(df: pd.DataFrame, out: Path) -> None:
    """p=0.2 の reversed_c 条件での depth 別 AA 遷移（「再現できるが間違っている」境界）。"""
    sub = df[
        (df["spurious_p"] == 0.2) & (df["eval_condition"] == "reversed_c")
    ].groupby("max_depth")["action_agreement"].mean().reset_index()

    if sub.empty:
        return

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(sub["max_depth"], sub["action_agreement"], marker="o", color="tomato", linewidth=2)
    ax.axhline(0.5, color="gray", linestyle="--", linewidth=1, label="AA=0.5 (chance)")
    ax.set_xlabel("max_depth")
    ax.set_ylabel("Action Agreement (reversed_c)")
    ax.set_title("GridWorld (p=0.2): AA under reversed_c by depth\n"
                 "→ 浅い木はスプリアス再現できず乖離、深い木は誤りを忠実に再現")
    ax.set_ylim(0.3, 1.05)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    path = out / "aa_depth_reversed_gridworld.png"
    plt.savefig(path, dpi=100)
    plt.close()
    print(f"  保存: {path}")


# ---------------------------------------------------------------------------
# エントリポイント
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--exp",
        choices=["exp001", "exp002", "all"],
        default="all",
        help="可視化する実験を指定",
    )
    args = parser.parse_args()

    base = ROOT / "experiments" / "results"

    if args.exp in ("exp001", "all"):
        visualize_cartpole(base / "exp001_cartpole_noise")

    if args.exp in ("exp002", "all"):
        visualize_gridworld(base / "exp002_spurious_gridworld")


if __name__ == "__main__":
    main()
