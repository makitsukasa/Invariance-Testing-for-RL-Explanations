"""Generate paper-quality figures from results.csv.

Handles three dataset types:
  GridWorld  : has spurious_p + delta_c (spurious) + per-feature delta/shap cols
  ColoredMNIST: has spurious_p + delta_hue + delta_struct cols
  Waterbirds : no spurious_p; has delta_bg/delta_fg/shap_bg/shap_fg
  exp022 Waterbirds GrabCut sensitivity -> fig_grabcut_sensitivity.pdf, fig_grabcut_sensitivity.png

Figures produced per CSV
  GridWorld    -> fig_psweep.pdf, fig_crosstab.pdf
  ColoredMNIST -> fig_psweep.pdf
  Waterbirds   -> fig_scatter.pdf, fig_delta_dist.pdf
  exp021 Waterbirds specialized baseline -> fig_specialized_baseline.pdf, fig_specialized_baseline_pca.pdf

Usage:
    python experiments/plot_results.py PATH/results.csv [...]
    python experiments/plot_results.py PATH/results.csv --show   # display interactively
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------

STYLE = {
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "legend.fontsize": 9,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "lines.linewidth": 1.8,
    "lines.markersize": 6,
}

DELTA_COLOR = "#2166ac"
SHAP_COLOR  = "#d6604d"
BOTH_COLOR  = "#4dac26"
NEITHER_COLOR = "#b2b2b2"
DELTA_ONLY_COLOR = "#2166ac"
SHAP_ONLY_COLOR  = "#d6604d"

# ---------------------------------------------------------------------------
# Wilson CI
# ---------------------------------------------------------------------------

def wilson_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    z = norm.ppf(1 - alpha / 2)
    p = k / n
    denom = 1 + z ** 2 / n
    center = (p + z ** 2 / (2 * n)) / denom
    margin = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / denom
    return float(max(0.0, center - margin)), float(min(1.0, center + margin))


def rate_with_ci(k: int, n: int) -> tuple[float, float, float]:
    """Returns (rate, lower_err, upper_err) for error bars."""
    rate = k / n if n > 0 else 0.0
    lo, hi = wilson_ci(k, n)
    return rate, max(0.0, rate - lo), max(0.0, hi - rate)


def recall_at_k(df: pd.DataFrame, feat_cols: list[str], target: str, k: int) -> int:
    numeric = df[feat_cols].apply(pd.to_numeric, errors="coerce")
    ranks = numeric.rank(axis=1, ascending=False, method="min")
    return int((ranks[target] <= k).sum())


# ---------------------------------------------------------------------------
# Figure 1: p-sweep line chart  (GridWorld + ColoredMNIST)
# ---------------------------------------------------------------------------

def fig_psweep_gridworld(df: pd.DataFrame, outdir: Path, show: bool) -> None:
    delta_feat_cols = [c for c in df.columns
                       if c.startswith("delta_")
                       and c not in ("delta_selected", "delta_correct")]
    shap_feat_cols  = [c for c in df.columns
                       if c.startswith("shap_")
                       and c not in ("shap_selected", "shap_correct")]
    delta_target = "delta_c (spurious)"
    shap_target  = "shap_c (spurious)"

    p_values = sorted(df["spurious_p"].unique())
    metrics: dict[str, list] = {k: [] for k in
                                  ("d1", "d1_lo", "d1_hi",
                                   "d2", "d2_lo", "d2_hi",
                                   "s1", "s1_lo", "s1_hi",
                                   "s2", "s2_lo", "s2_hi")}

    for p in p_values:
        sub = df[df["spurious_p"] == p]
        n = len(sub)
        d1, d1_lo, d1_hi = rate_with_ci(int(sub["delta_correct"].sum()), n)
        d2, d2_lo, d2_hi = rate_with_ci(recall_at_k(sub, delta_feat_cols, delta_target, 2), n)
        s1, s1_lo, s1_hi = rate_with_ci(int(sub["shap_correct"].sum()), n)
        s2, s2_lo, s2_hi = rate_with_ci(recall_at_k(sub, shap_feat_cols, shap_target, 2), n)
        for key, val in zip(metrics.keys(), [d1, d1_lo, d1_hi, d2, d2_lo, d2_hi,
                                              s1, s1_lo, s1_hi, s2, s2_lo, s2_hi]):
            metrics[key].append(val)

    x = np.array(p_values)
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(5, 3.5))

        ax.errorbar(x, metrics["d1"], yerr=[metrics["d1_lo"], metrics["d1_hi"]],
                    fmt="o-", color=DELTA_COLOR, label="Δ@1", capsize=3)
        ax.errorbar(x, metrics["d2"], yerr=[metrics["d2_lo"], metrics["d2_hi"]],
                    fmt="s--", color=DELTA_COLOR, alpha=0.6, label="Δ@2", capsize=3)
        ax.errorbar(x, metrics["s1"], yerr=[metrics["s1_lo"], metrics["s1_hi"]],
                    fmt="o-", color=SHAP_COLOR, label="SHAP@1", capsize=3)
        ax.errorbar(x, metrics["s2"], yerr=[metrics["s2_lo"], metrics["s2_hi"]],
                    fmt="s--", color=SHAP_COLOR, alpha=0.6, label="SHAP@2", capsize=3)

        ax.set_xlabel("Spurious correlation strength p")
        ax.set_ylabel("Detection rate (95% Wilson CI)")
        ax.set_xticks(x)
        ax.set_ylim(-0.05, 1.05)
        ax.axhline(0.5, color="gray", lw=0.8, ls=":", alpha=0.7)
        ax.legend(loc="lower left", ncol=2)
        ax.set_title("GridWorld: Δ vs SHAP detection rate")

        fig.tight_layout()
        out = outdir / "fig_psweep.pdf"
        fig.savefig(out, bbox_inches="tight")
        fig.savefig(out.with_suffix(".png"), bbox_inches="tight")
        print(f"  -> {out}")
        if show:
            plt.show()
        plt.close(fig)


LIME_COLOR = "#2ca25f"


def fig_psweep_cmnist(df: pd.DataFrame, outdir: Path, show: bool) -> None:
    p_values = sorted(df["spurious_p"].unique())
    has_lime = "lime_ok" in df.columns

    d1_vals, d1_lo_vals, d1_hi_vals = [], [], []
    s1_vals, s1_lo_vals, s1_hi_vals = [], [], []
    li_vals, li_lo_vals, li_hi_vals = [], [], []

    for p in p_values:
        sub = df[df["spurious_p"] == p]
        n = len(sub)
        d1, lo, hi = rate_with_ci(int(sub["delta_correct"].sum()), n)
        d1_vals.append(d1); d1_lo_vals.append(lo); d1_hi_vals.append(hi)
        s1, lo, hi = rate_with_ci(int(sub["shap_correct"].sum()), n)
        s1_vals.append(s1); s1_lo_vals.append(lo); s1_hi_vals.append(hi)
        if has_lime:
            li, lo, hi = rate_with_ci(int(sub["lime_ok"].sum()), n)
            li_vals.append(li); li_lo_vals.append(lo); li_hi_vals.append(hi)

    x = np.array(p_values)
    title = "ColoredMNIST: Δ vs SHAP" + (" vs LIME" if has_lime else "") + " detection rate"
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(5, 3.5))

        ax.errorbar(x, d1_vals, yerr=[d1_lo_vals, d1_hi_vals],
                    fmt="o-", color=DELTA_COLOR, label="Δ (intervention)", capsize=3)
        ax.errorbar(x, s1_vals, yerr=[s1_lo_vals, s1_hi_vals],
                    fmt="o-", color=SHAP_COLOR, label="SHAP", capsize=3)
        if has_lime:
            ax.errorbar(x, li_vals, yerr=[li_lo_vals, li_hi_vals],
                        fmt="s--", color=LIME_COLOR, label="LIME (channel)", capsize=3)

        ax.set_xlabel("Spurious correlation strength p")
        ax.set_ylabel("Detection rate (95% Wilson CI)")
        ax.set_xticks(x)
        ax.set_ylim(-0.05, 1.05)
        ax.axhline(0.5, color="gray", lw=0.8, ls=":", alpha=0.7)
        ax.legend(loc="lower left")
        ax.set_title(title)

        fig.tight_layout()
        out = outdir / "fig_psweep.pdf"
        fig.savefig(out, bbox_inches="tight")
        fig.savefig(out.with_suffix(".png"), bbox_inches="tight")
        print(f"  -> {out}")
        if show:
            plt.show()
        plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 2: Complementarity stacked bar (GridWorld)
# ---------------------------------------------------------------------------

def fig_crosstab(df: pd.DataFrame, outdir: Path, show: bool) -> None:
    p_values = sorted(df["spurious_p"].unique())
    both_vals, d_only_vals, s_only_vals, neither_vals = [], [], [], []

    for p in p_values:
        sub = df[df["spurious_p"] == p]
        n = len(sub)
        d = sub["delta_correct"].astype(bool)
        s = sub["shap_correct"].astype(bool)
        both_vals.append(int((d & s).sum()) / n)
        d_only_vals.append(int((d & ~s).sum()) / n)
        s_only_vals.append(int((~d & s).sum()) / n)
        neither_vals.append(int((~d & ~s).sum()) / n)

    x = np.arange(len(p_values))
    labels = [str(p) for p in p_values]

    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(5, 3.5))

        ax.bar(x, both_vals,   color=BOTH_COLOR,     label="Both correct")
        ax.bar(x, d_only_vals, bottom=both_vals,      color=DELTA_ONLY_COLOR, alpha=0.7, label="Δ only")
        ax.bar(x, s_only_vals,
               bottom=[b + d for b, d in zip(both_vals, d_only_vals)],
               color=SHAP_ONLY_COLOR, alpha=0.7, label="SHAP only")
        ax.bar(x, neither_vals,
               bottom=[b + d + s for b, d, s in zip(both_vals, d_only_vals, s_only_vals)],
               color=NEITHER_COLOR, label="Neither")

        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_xlabel("Spurious correlation strength p")
        ax.set_ylabel("Fraction of seeds")
        ax.set_ylim(0, 1.0)
        ax.legend(loc="upper right", fontsize=8)
        ax.set_title("GridWorld: complementarity of Δ and SHAP")

        fig.tight_layout()
        out = outdir / "fig_crosstab.pdf"
        fig.savefig(out, bbox_inches="tight")
        fig.savefig(out.with_suffix(".png"), bbox_inches="tight")
        print(f"  -> {out}")
        if show:
            plt.show()
        plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 3: Waterbirds scatter (delta_bg vs delta_fg per seed)
# ---------------------------------------------------------------------------

def fig_waterbirds_scatter(df: pd.DataFrame, outdir: Path, show: bool) -> None:
    delta_ok = df["delta_ok"].astype(bool)
    shap_ok  = df["shap_ok"].astype(bool)

    colors = np.where(delta_ok, DELTA_COLOR, "#cccccc")

    with plt.rc_context(STYLE):
        fig, axes = plt.subplots(1, 2, figsize=(7, 3.5))

        # Left: Δ scatter
        ax = axes[0]
        ax.scatter(df["delta_fg"], df["delta_bg"],
                   c=colors, edgecolors="white", linewidths=0.5, zorder=3, s=45)
        lo = min(df["delta_fg"].min(), df["delta_bg"].min()) - 0.02
        hi = max(df["delta_fg"].max(), df["delta_bg"].max()) + 0.02
        ax.plot([lo, hi], [lo, hi], "k--", lw=0.8, alpha=0.5, label="y = x")
        ax.set_xlabel("Δ foreground (causal)")
        ax.set_ylabel("Δ background (spurious)")
        ax.set_title("Δ intervention")
        correct_patch   = mpatches.Patch(color=DELTA_COLOR, label=f"Correct (bg > fg): {delta_ok.sum()}/{len(df)}")
        incorrect_patch = mpatches.Patch(color="#cccccc", label=f"Incorrect: {(~delta_ok).sum()}/{len(df)}")
        ax.legend(handles=[correct_patch, incorrect_patch], fontsize=8, loc="upper left")

        # Right: SHAP scatter
        ax = axes[1]
        shap_colors = np.where(shap_ok, SHAP_COLOR, "#cccccc")
        ax.scatter(df["shap_fg"], df["shap_bg"],
                   c=shap_colors, edgecolors="white", linewidths=0.5, zorder=3, s=45)
        lo = min(df["shap_fg"].min(), df["shap_bg"].min()) - 0.01
        hi = max(df["shap_fg"].max(), df["shap_bg"].max()) + 0.01
        ax.plot([lo, hi], [lo, hi], "k--", lw=0.8, alpha=0.5)
        ax.set_xlabel("SHAP foreground (causal)")
        ax.set_ylabel("SHAP background (spurious)")
        ax.set_title("SHAP attribution")
        correct_patch2   = mpatches.Patch(color=SHAP_COLOR, label=f"Correct (bg > fg): {shap_ok.sum()}/{len(df)}")
        incorrect_patch2 = mpatches.Patch(color="#cccccc", label=f"Incorrect: {(~shap_ok).sum()}/{len(df)}")
        ax.legend(handles=[correct_patch2, incorrect_patch2], fontsize=8, loc="upper left")

        fig.suptitle("Waterbirds: per-seed feature attribution", fontsize=11)
        fig.tight_layout()
        out = outdir / "fig_scatter.pdf"
        fig.savefig(out, bbox_inches="tight")
        fig.savefig(out.with_suffix(".png"), bbox_inches="tight")
        print(f"  -> {out}")
        if show:
            plt.show()
        plt.close(fig)


def fig_waterbirds_delta_dist(df: pd.DataFrame, outdir: Path, show: bool) -> None:
    """Strip + mean bar: distribution of delta_bg and delta_fg values."""
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(4, 3.5))

        jitter = 0.06
        rng = np.random.default_rng(0)
        xs_bg = rng.uniform(-jitter, jitter, size=len(df))
        xs_fg = rng.uniform(-jitter, jitter, size=len(df))

        ax.scatter(0.8 + xs_bg, df["delta_bg"], color=DELTA_COLOR, alpha=0.5, s=20, zorder=3)
        ax.scatter(1.2 + xs_fg, df["delta_fg"], color=SHAP_COLOR,  alpha=0.5, s=20, zorder=3)

        # Mean bars
        ax.hlines(df["delta_bg"].mean(), 0.7, 0.9, colors=DELTA_COLOR, lw=2.5, zorder=4)
        ax.hlines(df["delta_fg"].mean(), 1.1, 1.3, colors=SHAP_COLOR,  lw=2.5, zorder=4)

        ax.axhline(0, color="gray", lw=0.8, ls=":")
        ax.set_xticks([0.8, 1.2])
        ax.set_xticklabels(["Δ background\n(spurious)", "Δ foreground\n(causal)"])
        ax.set_ylabel("Performance drop Δ")
        ax.set_title("Waterbirds: Δ distribution per-seed")

        fig.tight_layout()
        out = outdir / "fig_delta_dist.pdf"
        fig.savefig(out, bbox_inches="tight")
        fig.savefig(out.with_suffix(".png"), bbox_inches="tight")
        print(f"  -> {out}")
        if show:
            plt.show()
        plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 3b: Waterbirds GrabCut sensitivity (exp022)
# ---------------------------------------------------------------------------

def _mean_ci(values: np.ndarray, alpha: float = 0.05) -> tuple[float, float, float]:
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return 0.0, 0.0, 0.0
    mean = float(values.mean())
    if values.size == 1:
        return mean, 0.0, 0.0
    z = norm.ppf(1 - alpha / 2)
    se = float(values.std(ddof=1) / np.sqrt(values.size))
    lo = mean - z * se
    hi = mean + z * se
    return mean, max(0.0, mean - lo), max(0.0, hi - mean)


def fig_waterbirds_grabcut_sensitivity(df: pd.DataFrame, outdir: Path, show: bool) -> None:
    if "mask_radius" not in df.columns or "delta_bg" not in df.columns or "delta_fg" not in df.columns:
        print("  [SKIP] exp022 grabcut sensitivity requires mask_radius, delta_bg, delta_fg")
        return

    radii = sorted(int(r) for r in df["mask_radius"].unique())
    mean_bg, lo_bg, hi_bg = [], [], []
    mean_fg, lo_fg, hi_fg = [], [], []
    mean_gap, lo_gap, hi_gap = [], [], []
    ok_rates, ok_lo, ok_hi = [], [], []
    n_per_radius = []

    for r in radii:
        sub = df[df["mask_radius"] == r]
        n = len(sub)
        n_per_radius.append(n)
        m, lo, hi = _mean_ci(sub["delta_bg"].to_numpy())
        mean_bg.append(m); lo_bg.append(lo); hi_bg.append(hi)
        m, lo, hi = _mean_ci(sub["delta_fg"].to_numpy())
        mean_fg.append(m); lo_fg.append(lo); hi_fg.append(hi)
        m, lo, hi = _mean_ci(sub["delta_gap"].to_numpy())
        mean_gap.append(m); lo_gap.append(lo); hi_gap.append(hi)
        rate, lo, hi = rate_with_ci(int(sub["delta_correct"].sum()), n)
        ok_rates.append(rate); ok_lo.append(lo); ok_hi.append(hi)

    x = np.array(radii)
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))

        ax[0].errorbar(x, mean_bg, yerr=[lo_bg, hi_bg], fmt="o-", capsize=3, label="Δ_bg")
        ax[0].errorbar(x, mean_fg, yerr=[lo_fg, hi_fg], fmt="s--", capsize=3, label="Δ_fg")
        ax[0].errorbar(x, mean_gap, yerr=[lo_gap, hi_gap], fmt="d-", capsize=3, label="Δ_gap")
        ax[0].axhline(0.0, color="black", linewidth=1, alpha=0.6)
        ax[0].set_xlabel("mask radius (px)")
        ax[0].set_ylabel("mean Δ (95% CI)")
        ax[0].set_title("GrabCut perturbation effect")
        ax[0].legend(loc="best")
        ax[0].grid(alpha=0.3)

        ax[1].errorbar(x, ok_rates, yerr=[ok_lo, ok_hi], fmt="o-", color=DELTA_COLOR, capsize=3)
        ax[1].axhline(0.5, color="gray", linewidth=1, linestyle=":", alpha=0.7)
        ax[1].set_xlabel("mask radius (px)")
        ax[1].set_ylabel("P(Δ_bg > Δ_fg) (95% Wilson CI)")
        ax[1].set_ylim(-0.05, 1.05)
        ax[1].set_title("Decision stability")
        ax[1].grid(alpha=0.3)

        fig.suptitle("Waterbirds exp022: GrabCut mask sensitivity over seeds", fontsize=11)
        fig.tight_layout()
        out = outdir / "fig_grabcut_sensitivity.pdf"
        fig.savefig(out, bbox_inches="tight")
        fig.savefig(out.with_suffix(".png"), bbox_inches="tight")
        print(f"  -> {out}")
        if show:
            plt.show()
        plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 4: Waterbirds specialized baseline comparison (exp021)
# ---------------------------------------------------------------------------

def fig_waterbirds_specialized_compare(df: pd.DataFrame, outdir: Path, show: bool) -> None:
    required = {"delta_ok", "shap_ok", "spec_ok"}
    if not required.issubset(df.columns):
        print("  [SKIP] exp021 specialized comparison requires delta_ok, shap_ok, spec_ok")
        return

    has_pca = "pca_ok" in df.columns
    n = len(df)
    methods = [
        ("Δ", "delta_ok", DELTA_COLOR),
        ("SHAP", "shap_ok", SHAP_COLOR),
        ("Spec", "spec_ok", "#4e79a7"),
    ]
    if has_pca:
        methods.append(("PCA", "pca_ok", "#9c755f"))

    labels = [m[0] for m in methods]
    rates, lo_errs, hi_errs = [], [], []
    for _, col, _ in methods:
        k = int(df[col].astype(bool).sum())
        rate, lo, hi = rate_with_ci(k, n)
        rates.append(rate)
        lo_errs.append(lo)
        hi_errs.append(hi)

    discordant_delta_spec = {
        "delta_only": int(((df["delta_ok"] == 1) & (df["spec_ok"] == 0)).sum()),
        "spec_only": int(((df["delta_ok"] == 0) & (df["spec_ok"] == 1)).sum()),
    }
    discordant_delta_pca = None
    if has_pca:
        discordant_delta_pca = {
            "delta_only": int(((df["delta_ok"] == 1) & (df["pca_ok"] == 0)).sum()),
            "pca_only": int(((df["delta_ok"] == 0) & (df["pca_ok"] == 1)).sum()),
        }

    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(5.5, 3.5))
        x = np.arange(len(methods))
        colors = [m[2] for m in methods]
        ax.bar(x, rates, color=colors, alpha=0.85, width=0.7, zorder=2)
        ax.errorbar(
            x,
            rates,
            yerr=[lo_errs, hi_errs],
            fmt="none",
            ecolor="black",
            elinewidth=1,
            capsize=4,
            zorder=3,
        )
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_ylim(0, 1.05)
        ax.set_ylabel("Detection rate (95% Wilson CI)")
        ax.set_title("Waterbirds exp021: specialized baseline comparison")
        ax.text(
            0.02,
            0.02,
            f"Δ vs Spec discordant: {discordant_delta_spec['delta_only']} / {discordant_delta_spec['spec_only']}",
            transform=ax.transAxes,
            fontsize=8,
            va="bottom",
        )
        fig.tight_layout()
        out = outdir / "fig_specialized_baseline.pdf"
        fig.savefig(out, bbox_inches="tight")
        fig.savefig(out.with_suffix(".png"), bbox_inches="tight")
        print(f"  -> {out}")
        if show:
            plt.show()
        plt.close(fig)

        if has_pca:
            fig, ax = plt.subplots(figsize=(6.1, 3.5))
            x = np.arange(len(methods))
            ax.bar(x, rates, color=colors, alpha=0.85, width=0.7, zorder=2)
            ax.errorbar(
                x,
                rates,
                yerr=[lo_errs, hi_errs],
                fmt="none",
                ecolor="black",
                elinewidth=1,
                capsize=4,
                zorder=3,
            )
            ax.set_xticks(x)
            ax.set_xticklabels(labels)
            ax.set_ylim(0, 1.05)
            ax.set_ylabel("Detection rate (95% Wilson CI)")
            ax.set_title("Waterbirds exp021: specialized baseline + PCA proxy")
            pca_text = discordant_delta_pca or {}
            ax.text(
                0.02,
                0.02,
                f"Δ vs PCA discordant: {pca_text.get('delta_only', 0)} / {pca_text.get('pca_only', 0)}",
                transform=ax.transAxes,
                fontsize=8,
                va="bottom",
            )
            fig.tight_layout()
            out = outdir / "fig_specialized_baseline_pca.pdf"
            fig.savefig(out, bbox_inches="tight")
            fig.savefig(out.with_suffix(".png"), bbox_inches="tight")
            print(f"  -> {out}")
            if show:
                plt.show()
            plt.close(fig)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def process_csv(path: Path, show: bool) -> None:
    df = pd.read_csv(path)
    outdir = path.parent
    print(f"\n{'='*50}\n  {path.parent.name}/{path.name}\n{'='*50}")

    if "mask_radius" in df.columns and {"delta_bg", "delta_fg", "delta_gap", "delta_correct"}.issubset(df.columns):
        fig_waterbirds_grabcut_sensitivity(df, outdir, show)
        return

    if "spurious_p" not in df.columns:
        # Waterbirds / exp021 specialized baseline
        if "spec_ok" in df.columns:
            fig_waterbirds_specialized_compare(df, outdir, show)
            return
        fig_waterbirds_scatter(df, outdir, show)
        fig_waterbirds_delta_dist(df, outdir, show)
        return

    if "delta_c (spurious)" in df.columns:
        # GridWorld
        fig_psweep_gridworld(df, outdir, show)
        fig_crosstab(df, outdir, show)
    elif "delta_hue" in df.columns:
        # ColoredMNIST
        fig_psweep_cmnist(df, outdir, show)
    else:
        # Unknown p-sweep — try CMNIST-style if delta_correct exists
        if "delta_correct" in df.columns:
            fig_psweep_cmnist(df, outdir, show)
        else:
            print("  [SKIP] unrecognized schema")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Plot detection results")
    parser.add_argument("csvs", nargs="+", type=Path, metavar="CSV")
    parser.add_argument("--show", action="store_true", help="Display figures interactively")
    args = parser.parse_args()

    for csv_path in args.csvs:
        if not csv_path.exists():
            print(f"[SKIP] {csv_path} not found")
            continue
        process_csv(csv_path, args.show)


if __name__ == "__main__":
    main()
