"""draft.md 用の論文図を生成するスクリプト。

既存の metrics.csv を読み込み、各実験の出力ディレクトリに保存する。
再実験不要。python experiments/make_figures.py で実行。
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RES = ROOT / "experiments" / "results"
EXP001 = RES / "exp001_cartpole_noise"
EXP002 = RES / "exp002_spurious_gridworld"
EXP003 = RES / "exp003_cartpole_gravity"

plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "legend.fontsize": 9,
    "figure.dpi": 120,
})


def stats(df_sub, cond_col, cond_val, metric):
    sub = df_sub[df_sub[cond_col] == cond_val][metric]
    return sub.mean(), sub.std()


# ---------------------------------------------------------------------------
# Fig.1: exp001 — AA heatmap (N x depth, K=4)
# ---------------------------------------------------------------------------
def make_fig1_exp001():
    df = pd.read_csv(EXP001 / "metrics.csv")
    df4 = df[df["n_experts"] == 4]
    pivot = (
        df4.groupby(["noise_dim", "max_depth"])["action_agreement"]
        .mean()
        .unstack()
    )

    fig, ax = plt.subplots(figsize=(5.5, 3.5))
    im = ax.imshow(pivot.values, vmin=0.75, vmax=1.0, cmap="RdYlGn", aspect="auto")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_xlabel("Tree depth $d$")
    ax.set_ylabel("Noise dimensions $N$")
    ax.set_title("Action Agreement (AA), $K=4$, mean over 3 seeds")

    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            val = pivot.values[i, j]
            color = "white" if val < 0.84 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=9, color=color)

    plt.colorbar(im, ax=ax, label="AA")
    plt.tight_layout()
    out = EXP001 / "fig1_aa_heatmap.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"saved: {out}")


# ---------------------------------------------------------------------------
# Fig.2: exp002 — AA and J across eval conditions (p=0.0, K=4, d=5)
# ---------------------------------------------------------------------------
def make_fig2_exp002():
    df = pd.read_csv(EXP002 / "metrics.csv")
    d = df[(df["spurious_p"] == 0.0) & (df["n_experts"] == 4) & (df["max_depth"] == 5)]

    conds = ["train", "random_c", "reversed_c"]
    aa = [stats(d, "eval_condition", c, "action_agreement") for c in conds]
    ji = [stats(d, "eval_condition", c, "j_intuitive") for c in conds]
    jr = [stats(d, "eval_condition", c, "j_reasoned") for c in conds]

    x = np.arange(3)
    width = 0.35

    fig, axes = plt.subplots(1, 2, figsize=(9, 4))

    ax = axes[0]
    ax.bar(x, [a[0] for a in aa], width * 1.8, yerr=[a[1] for a in aa],
           capsize=5, color="steelblue", alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(conds)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Action Agreement (AA)")
    ax.set_title("AA across eval conditions")
    ax.axhline(1.0, color="gray", linestyle=":", linewidth=0.8)

    ax = axes[1]
    ax.bar(x - width / 2, [j[0] for j in ji], width, yerr=[j[1] for j in ji],
           capsize=5, color="steelblue", alpha=0.85, label="$J_{\\mathrm{intuitive}}$")
    ax.bar(x + width / 2, [j[0] for j in jr], width, yerr=[j[1] for j in jr],
           capsize=5, color="tomato", alpha=0.85, label="$J_{\\mathrm{reasoned}}$")
    ax.set_xticks(x)
    ax.set_xticklabels(conds)
    ax.set_ylabel("Mean episode reward")
    ax.set_title("Episode reward across eval conditions")
    ax.axhline(0, color="black", linestyle="--", linewidth=0.7)
    ax.legend()

    fig.suptitle(
        "GridWorld ($p=0.0$, $K=4$, $d=5$): spurious feature $c$ under distribution shift",
        fontsize=11,
    )
    plt.tight_layout()
    out = EXP002 / "fig2_j_shift_p0.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"saved: {out}")


# ---------------------------------------------------------------------------
# Fig.3: diagnostic comparison
#   left col: exp002 spurious (train / reversed_c)
#   right col: exp003 all 5 physics-shift conditions
# ---------------------------------------------------------------------------
def make_fig3_comparison():
    df2 = pd.read_csv(EXP002 / "metrics.csv")
    df3 = pd.read_csv(EXP003 / "metrics.csv")

    d2 = df2[(df2["spurious_p"] == 0.0) & (df2["n_experts"] == 4) & (df2["max_depth"] == 5)]

    conds2   = ["train", "reversed_c"]
    xlabels2 = ["train", "reversed_c"]

    conds3   = ["train", "gravity_lo", "gravity_hi", "pole_short", "pole_long"]
    xlabels3 = ["train", "grav\nlo", "grav\nhi", "pole\nshort", "pole\nlong"]

    aa2 = [stats(d2, "eval_condition", c, "action_agreement") for c in conds2]
    ji2 = [stats(d2, "eval_condition", c, "j_intuitive")      for c in conds2]
    jr2 = [stats(d2, "eval_condition", c, "j_reasoned")       for c in conds2]
    aa3 = [stats(df3, "condition", c, "action_agreement")     for c in conds3]
    ji3 = [stats(df3, "condition", c, "j_intuitive")          for c in conds3]
    jr3 = [stats(df3, "condition", c, "j_reasoned")           for c in conds3]

    fig, axes = plt.subplots(2, 2, figsize=(11, 7),
                             gridspec_kw={"hspace": 0.55, "wspace": 0.38,
                                          "width_ratios": [1, 2.5]})
    width = 0.35

    def plot_aa(ax, aa_list, xlabels, color, title):
        x = np.arange(len(aa_list))
        ax.bar(x, [a[0] for a in aa_list], width * 1.6,
               yerr=[a[1] for a in aa_list], capsize=5, color=color, alpha=0.82)
        ax.set_xticks(x)
        ax.set_xticklabels(xlabels, fontsize=10)
        ax.set_ylim(0, 1.12)
        ax.set_ylabel("Action Agreement (AA)")
        ax.set_title(title, fontsize=10.5)
        ax.axhline(1.0, color="gray", linestyle=":", linewidth=0.8)

    def plot_j(ax, ji_list, jr_list, xlabels, y_lim, title):
        x = np.arange(len(ji_list))
        ax.bar(x - width / 2, [j[0] for j in ji_list], width,
               yerr=[j[1] for j in ji_list], capsize=5,
               color="steelblue", alpha=0.85, label="$J_{\\mathrm{intuitive}}$")
        ax.bar(x + width / 2, [j[0] for j in jr_list], width,
               yerr=[j[1] for j in jr_list], capsize=5,
               color="tomato", alpha=0.85, label="$J_{\\mathrm{reasoned}}$")
        ax.set_xticks(x)
        ax.set_xticklabels(xlabels, fontsize=10)
        ax.set_ylim(*y_lim)
        ax.set_ylabel("Mean episode reward")
        ax.set_title(title, fontsize=10.5)
        ax.axhline(0, color="black", linestyle="--", linewidth=0.7)
        ax.legend(fontsize=9)

    plot_aa(axes[0, 0], aa2, xlabels2, "darkorange", "GridWorld (spurious): AA")
    plot_aa(axes[0, 1], aa3, xlabels3, "seagreen",   "CartPole N=0 (no spurious): AA")
    plot_j(axes[1, 0], ji2, jr2, xlabels2, (-1.15, 1.15),
           "GridWorld (spurious): episode reward")
    plot_j(axes[1, 1], ji3, jr3, xlabels3, (-1.15, 380),
           "CartPole N=0 (no spurious): episode reward")

    for ax, label in zip(axes[0], [
        "High Reprod. $\\times$ Low Invar.  [spurious, $p{=}0.0$]",
        "High Reprod. $\\times$ High Invar.  [no spurious, $N{=}0$]",
    ]):
        ax.annotate(label, xy=(0.5, 1.28), xycoords="axes fraction",
                    ha="center", fontsize=10.5, fontweight="bold",
                    annotation_clip=False)

    fig.suptitle(
        "Diagnostic comparison: spurious vs. spurious-free under distribution shift",
        fontsize=12, y=1.04,
    )
    out = EXP003 / "fig3_diagnostic_comparison.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"saved: {out}")


# ---------------------------------------------------------------------------
# Fig.4: SHAP importance (p=0.0, train vs reversed_c)
# ---------------------------------------------------------------------------
def make_fig4_shap():
    shap_path = EXP002 / "shap_values.csv"
    if not shap_path.exists():
        print(f"skip: {shap_path} not found")
        return

    df = pd.read_csv(shap_path)
    if "feature" in df.columns:
        df_p0 = df[df["spurious_p"] == 0.0]
        features = df_p0["feature"].unique().tolist()
        conds = ["train", "reversed_c"]
        colors = ["steelblue", "tomato"]
        x = np.arange(len(features))
        width = 0.35
        fig, ax = plt.subplots(figsize=(5.5, 3.5))
        for i, (cond, color) in enumerate(zip(conds, colors)):
            sub = df_p0[df_p0["eval_condition"] == cond]
            means = [sub[sub["feature"] == f]["mean_abs_shap"].mean() for f in features]
            ax.bar(x + i * width - width / 2, means, width,
                   color=color, alpha=0.85, label=cond)
    else:
        df_p0 = df[df["spurious_p"] == 0.0]
        feat_cols = [c for c in df_p0.columns
                     if c not in ("spurious_p", "eval_condition", "seed")]
        conds = ["train", "reversed_c"]
        colors = ["steelblue", "tomato"]
        x = np.arange(len(feat_cols))
        width = 0.35
        fig, ax = plt.subplots(figsize=(5.5, 3.5))
        for i, (cond, color) in enumerate(zip(conds, colors)):
            sub = df_p0[df_p0["eval_condition"] == cond]
            means = [sub[f].mean() for f in feat_cols]
            ax.bar(x + i * width - width / 2, means, width,
                   color=color, alpha=0.85, label=cond)
        features = feat_cols

    ax.set_xticks(x)
    ax.set_xticklabels(features, fontsize=10)
    ax.set_ylabel("Mean |SHAP value|")
    ax.set_title("SHAP importance ($p=0.0$): train vs. reversed_c")
    ax.legend()
    plt.tight_layout()
    out = EXP002 / "fig4_shap_p0.png"
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"saved: {out}")


if __name__ == "__main__":
    print("=== Generating publication figures ===")
    make_fig1_exp001()
    make_fig2_exp002()
    make_fig3_comparison()
    make_fig4_shap()
    print("=== Done ===")
