"""Compute 95% Wilson CI and paired McNemar test from results.csv.

Handles GridWorld/ColoredMNIST (p-sweep, with spurious_p column)
and Waterbirds (single-p, delta_ok/shap_ok columns).

Usage:
    python experiments/compute_stats.py PATH/results.csv [...]
    python experiments/compute_stats.py PATH/results.csv --save   # saves stats.txt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2, norm

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Statistics primitives
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


def mcnemar_test(b: int, c: int) -> tuple[float, float]:
    """b = Δ=OK & SHAP=NG, c = Δ=NG & SHAP=OK. Returns (chi2_stat, p_value)."""
    if b + c == 0:
        return float("nan"), float("nan")
    # with continuity correction (Yates)
    stat = (abs(b - c) - 1) ** 2 / (b + c)
    return float(stat), float(chi2.sf(stat, df=1))


def recall_at_k(df: pd.DataFrame, feat_cols: list[str], target: str, k: int) -> int:
    numeric = df[feat_cols].apply(pd.to_numeric, errors="coerce")
    ranks = numeric.rank(axis=1, ascending=False, method="min")
    return int((ranks[target] <= k).sum())


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

def _ci_str(k: int, n: int) -> str:
    lo, hi = wilson_ci(k, n)
    return f"{k}/{n}({k/n:.0%})[{lo:.2f},{hi:.2f}]"


def _pval_str(pval: float) -> str:
    if np.isnan(pval):
        return "N/A    "
    s = f"{pval:.4f}"
    return s + (" *" if pval < 0.05 else "  ")


# ---------------------------------------------------------------------------
# P-sweep analysis (GridWorld / ColoredMNIST)
# ---------------------------------------------------------------------------

def analyze_psweep(df: pd.DataFrame,
                   delta_col: str, shap_col: str,
                   delta_feat_cols: list[str], shap_feat_cols: list[str],
                   delta_target: str, shap_target: str) -> list[str]:

    has_features = bool(delta_feat_cols and delta_target and delta_target in df.columns)
    p_values = sorted(df["spurious_p"].unique())
    lines: list[str] = []

    if has_features:
        header = (f"{'p':>4}  {'n':>3}  "
                  f"{'Δ@1':>14}  {'Δ@2':>14}  "
                  f"{'SHAP@1':>14}  {'SHAP@2':>14}  "
                  f"{'McNemar p':>10}")
        lines += [header, "-" * len(header)]
    else:
        header = (f"{'p':>4}  {'n':>3}  "
                  f"{'Δ detect':>14}  {'SHAP detect':>14}  "
                  f"{'McNemar p':>10}")
        lines += [header, "-" * len(header)]

    all_b = all_c = 0

    for p in p_values:
        sub = df[df["spurious_p"] == p]
        n = len(sub)
        d1 = int(sub[delta_col].sum())
        s1 = int(sub[shap_col].sum())
        b = int((sub[delta_col] & ~sub[shap_col]).sum())
        c = int((~sub[delta_col] & sub[shap_col]).sum())
        all_b += b
        all_c += c
        _, pval = mcnemar_test(b, c)

        if has_features:
            d2 = recall_at_k(sub, delta_feat_cols, delta_target, 2)
            s2 = recall_at_k(sub, shap_feat_cols, shap_target, 2)
            lines.append(f"{p:>4}  {n:>3}  "
                         f"{_ci_str(d1,n):>14}  {_ci_str(d2,n):>14}  "
                         f"{_ci_str(s1,n):>14}  {_ci_str(s2,n):>14}  "
                         f"{_pval_str(pval)}")
        else:
            lines.append(f"{p:>4}  {n:>3}  "
                         f"{_ci_str(d1,n):>14}  "
                         f"{_ci_str(s1,n):>14}  "
                         f"{_pval_str(pval)}")

    # Overall row
    n_all = len(df)
    d_all = int(df[delta_col].sum())
    s_all = int(df[shap_col].sum())
    _, pval_all = mcnemar_test(all_b, all_c)
    lines.append("-" * len(header))
    if has_features:
        d2_all = recall_at_k(df, delta_feat_cols, delta_target, 2)
        s2_all = recall_at_k(df, shap_feat_cols, shap_target, 2)
        lines.append(f"{'ALL':>4}  {n_all:>3}  "
                     f"{_ci_str(d_all,n_all):>14}  {_ci_str(d2_all,n_all):>14}  "
                     f"{_ci_str(s_all,n_all):>14}  {_ci_str(s2_all,n_all):>14}  "
                     f"{_pval_str(pval_all)}")
    else:
        lines.append(f"{'ALL':>4}  {n_all:>3}  "
                     f"{_ci_str(d_all,n_all):>14}  "
                     f"{_ci_str(s_all,n_all):>14}  "
                     f"{_pval_str(pval_all)}")

    lines.append("")
    lines.append("McNemar: H0 = Δ@1 と SHAP@1 の検出率に差がない (paired, Yates補正あり)")
    lines.append("* p < 0.05")
    return lines


# ---------------------------------------------------------------------------
# Waterbirds analysis (no spurious_p sweep)
# ---------------------------------------------------------------------------

def analyze_waterbirds(df: pd.DataFrame) -> list[str]:
    delta_col = "delta_ok" if "delta_ok" in df.columns else "delta_correct"
    shap_col  = "shap_ok"  if "shap_ok"  in df.columns else "shap_correct"

    n = len(df)
    d = int(df[delta_col].sum())
    s = int(df[shap_col].sum())
    b = int((df[delta_col] & ~df[shap_col]).sum())
    c = int((~df[delta_col] & df[shap_col]).sum())
    both    = int((df[delta_col] & df[shap_col]).sum())
    neither = int((~df[delta_col] & ~df[shap_col]).sum())
    _, pval = mcnemar_test(b, c)

    lines = [
        f"{'n':>4}  {'Δ detect':>14}  {'SHAP detect':>14}  {'McNemar p':>10}",
        "-" * 55,
        f"{n:>4}  {_ci_str(d,n):>14}  {_ci_str(s,n):>14}  {_pval_str(pval)}",
        "",
        "Cross-tab:",
        f"  Δ=OK & SHAP=OK : {both}",
        f"  Δ=OK & SHAP=NG : {b}   <- Δ のみ検出",
        f"  Δ=NG & SHAP=OK : {c}   <- SHAP のみ検出",
        f"  Δ=NG & SHAP=NG : {neither}",
        "",
        "McNemar: H0 = Δ と SHAP の検出率に差がない (paired, Yates補正あり)",
        "* p < 0.05",
    ]
    return lines


# ---------------------------------------------------------------------------
# Third-method helper (LIME vs Δ McNemar)
# ---------------------------------------------------------------------------

def _analyze_third_method(df: pd.DataFrame,
                           method_col: str, method_name: str) -> list[str]:
    """Append per-p detection rates + McNemar(Δ vs method) for a third method."""
    p_values = sorted(df["spurious_p"].unique())
    lines = [f"", f"--- {method_name} ---"]
    header = f"{'p':>4}  {'n':>3}  {method_name+' detect':>16}  {'McNemar(Δ/'+method_name+') p':>22}"
    lines += [header, "-" * len(header)]
    all_b = all_c = 0
    for p in p_values:
        sub = df[df["spurious_p"] == p]
        n = len(sub)
        m = int(sub[method_col].sum())
        b = int((sub["delta_correct"] & ~sub[method_col]).sum())
        c = int((~sub["delta_correct"] & sub[method_col]).sum())
        all_b += b; all_c += c
        _, pval = mcnemar_test(b, c)
        lines.append(f"{p:>4}  {n:>3}  {_ci_str(m,n):>16}  {_pval_str(pval):>22}")
    n_all = len(df)
    m_all = int(df[method_col].sum())
    _, pval_all = mcnemar_test(all_b, all_c)
    lines.append("-" * len(header))
    lines.append(f"{'ALL':>4}  {n_all:>3}  {_ci_str(m_all,n_all):>16}  {_pval_str(pval_all):>22}")
    lines.append("McNemar: H0 = Δ と " + method_name + " の検出率に差がない (paired, Yates補正あり)")
    return lines


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def process_csv(path: Path) -> list[str]:
    df = pd.read_csv(path)
    lines = [f"\n{'='*60}", f"  {path.parent.name}/{path.name}", f"{'='*60}"]

    if "spurious_p" not in df.columns:
        lines += analyze_waterbirds(df)
        return lines

    # GridWorld: has 'delta_c (spurious)'
    if "delta_c (spurious)" in df.columns:
        delta_feat_cols = [c for c in df.columns
                           if c.startswith("delta_")
                           and c not in ("delta_selected", "delta_correct")]
        shap_feat_cols  = [c for c in df.columns
                           if c.startswith("shap_")
                           and c not in ("shap_selected", "shap_correct")]
        lines += analyze_psweep(df, "delta_correct", "shap_correct",
                                 delta_feat_cols, shap_feat_cols,
                                 "delta_c (spurious)", "shap_c (spurious)")
    # ColoredMNIST: has 'delta_hue'
    elif "delta_hue" in df.columns:
        lines += analyze_psweep(df, "delta_correct", "shap_correct",
                                 [], [], "", "")
        if "lime_ok" in df.columns:
            lines += _analyze_third_method(df, "lime_ok", "LIME (channel)")
    else:
        lines += analyze_psweep(df, "delta_correct", "shap_correct",
                                 [], [], "", "")

    return lines


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="95% CI + McNemar test for detection results")
    parser.add_argument("csvs", nargs="+", type=Path, metavar="CSV",
                        help="results.csv file(s)")
    parser.add_argument("--save", action="store_true",
                        help="Save stats.txt in the same directory as each CSV")
    args = parser.parse_args()

    for csv_path in args.csvs:
        if not csv_path.exists():
            print(f"[SKIP] {csv_path} not found")
            continue
        lines = process_csv(csv_path)
        output = "\n".join(lines)
        print(output)
        if args.save:
            out = csv_path.parent / "stats.txt"
            out.write_text(output, encoding="utf-8")
            print(f"  -> {out}")


if __name__ == "__main__":
    main()
