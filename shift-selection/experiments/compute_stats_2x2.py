"""exp029 の集計：2×2（モデル × 手法）の検出率と、対応のある McNemar 検定。

検出率は c (spurious) が top-1 / top-2 に入った割合（Wilson 95% CI）。
McNemar は compute_stats.py と同じ（Yates 補正あり）。--exp016 を渡すと、
exp029 の delta_sur・shap_ora_legacy が exp016 の delta・shap と一致するかも照合する。

Usage:
    python experiments/compute_stats_2x2.py PATH/results.csv [--exp016 PATH/results.csv] [--save]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from experiments.compute_stats import _ci_str, _pval_str, mcnemar_test, recall_at_k

TARGET = "c (spurious)"
SCORES = {
    "delta_sur":       "Δ（サロゲート）",
    "shap_sur":        "SHAP（サロゲート、行動確率・全行動）",
    "delta_ora":       "Δ（オラクル）",
    "shap_ora":        "SHAP（オラクル、Q 値・全行動）",
    "shap_sur_pred":   "SHAP（サロゲート、予測行動の確率のみ）",
    "shap_ora_pred":   "SHAP（オラクル、greedy 行動の Q 値のみ）",
    "shap_ora_legacy": "SHAP（オラクル、run_shap_psweep.py の集約をそのまま適用）",
}
PAIRS = [
    ("delta_sur", "shap_sur",        "同じサロゲート上"),
    ("delta_ora", "shap_ora",        "同じオラクル上"),
    ("delta_sur", "shap_ora",        "exp016 の組み合わせ（集約を修正）"),
    ("delta_sur", "shap_ora_legacy", "exp016 の組み合わせ（exp016 と同じ集約）"),
    ("delta_sur", "shap_sur_pred",   "同じサロゲート上（SHAP は予測行動のみ）"),
    ("delta_ora", "shap_ora_pred",   "同じオラクル上（SHAP は greedy 行動のみ）"),
    ("delta_ora", "delta_sur",       "Δ のオラクルとサロゲート"),
    ("shap_ora",  "shap_sur",        "SHAP のオラクルとサロゲート"),
]


def _feat_cols(df: pd.DataFrame, key: str) -> list[str]:
    cols = [c for c in df.columns if c.startswith(key + "_")
            and not c.endswith(("_selected", "_correct", "_target"))]
    # shap_ora_* が shap_ora_pred_* などを含まないようにする
    others = [k for k in SCORES if k != key and k.startswith(key + "_")]
    return [c for c in cols if not any(c.startswith(o + "_") for o in others)]


def detection_table(df: pd.DataFrame) -> list[str]:
    lines = ["## 検出率（c が top-1 / top-2）", ""]
    groups = [(p, df[df["spurious_p"] == p]) for p in sorted(df["spurious_p"].unique())] + [("ALL", df)]
    for key, label in SCORES.items():
        cols = _feat_cols(df, key)
        lines.append(f"### {key}：{label}")
        lines.append(f"{'p':>4}  {'n':>3}  {'@1':>26}  {'@2':>26}")
        for p, sub in groups:
            n = len(sub)
            k1 = int(sub[f"{key}_correct"].sum())
            k2 = recall_at_k(sub, cols, f"{key}_{TARGET}", 2)
            lines.append(f"{p!s:>4}  {n:>3}  {_ci_str(k1, n):>26}  {_ci_str(k2, n):>26}")
        lines.append("")
    return lines


def mcnemar_table(df: pd.DataFrame) -> list[str]:
    lines = ["## 対応のある McNemar 検定（top-1、Yates 補正あり）", "",
             "b = 左だけ正解、c = 右だけ正解", ""]
    groups = [(p, df[df["spurious_p"] == p]) for p in sorted(df["spurious_p"].unique())] + [("ALL", df)]
    for a, b_key, label in PAIRS:
        lines.append(f"### {a} vs {b_key}：{label}")
        lines.append(f"{'p':>4}  {'n':>3}  {'左 @1':>8}  {'右 @1':>8}  {'b':>3}  {'c':>3}  {'McNemar p':>10}")
        for p, sub in groups:
            x = sub[f"{a}_correct"].astype(bool)
            y = sub[f"{b_key}_correct"].astype(bool)
            b = int((x & ~y).sum())
            c = int((~x & y).sum())
            _, pval = mcnemar_test(b, c)
            lines.append(f"{p!s:>4}  {len(sub):>3}  {int(x.sum()):>8}  {int(y.sum()):>8}  "
                         f"{b:>3}  {c:>3}  {_pval_str(pval):>10}")
        lines.append("")
    return lines


def reproduction_check(df: pd.DataFrame, ref_path: Path) -> list[str]:
    ref = pd.read_csv(ref_path)
    merged = df.merge(ref, on=["seed", "spurious_p"], suffixes=("", "_exp016"))
    feats = [c[len("delta_"):] for c in ref.columns
             if c.startswith("delta_") and c not in ("delta_selected", "delta_correct")]
    lines = ["## exp016 との照合", "",
             f"共通の (seed, p)：{len(merged)} 件 / exp029 {len(df)} 件", ""]
    checks = [("aa_train", ["aa_train"], ["aa_train_exp016"]),
              ("j_s_train", ["j_s_train"], ["j_s_train_exp016"]),
              ("delta_sur vs exp016 delta", [f"delta_sur_{f}" for f in feats], [f"delta_{f}" for f in feats]),
              ("shap_ora_legacy vs exp016 shap", [f"shap_ora_legacy_{f}" for f in feats], [f"shap_{f}" for f in feats]),
              ("shap_ora vs exp016 shap", [f"shap_ora_{f}" for f in feats], [f"shap_{f}" for f in feats])]
    for name, mine, theirs in checks:
        diff = np.abs(merged[mine].to_numpy(float) - merged[theirs].to_numpy(float))
        lines.append(f"- {name}：最大絶対差 {diff.max():.3g}、一致した行 {(diff.max(axis=1) < 1e-6).sum()}/{len(merged)}")
    for mine, theirs in [("delta_sur_correct", "delta_correct"), ("shap_ora_legacy_correct", "shap_correct")]:
        same = (merged[mine].astype(bool) == merged[theirs].astype(bool)).sum()
        lines.append(f"- {mine} と exp016 {theirs} の判定が一致：{same}/{len(merged)}")
    lines.append("")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    parser.add_argument("--exp016", type=Path)
    parser.add_argument("--save", action="store_true", help="stats.txt を CSV と同じディレクトリに保存する")
    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    lines = [f"# {args.csv.parent.name}/{args.csv.name}", ""]
    lines += detection_table(df)
    lines += mcnemar_table(df)
    if args.exp016:
        lines += reproduction_check(df, args.exp016)
    out = "\n".join(lines)
    print(out)
    if args.save:
        (args.csv.parent / "stats.txt").write_text(out, encoding="utf-8")


if __name__ == "__main__":
    main()
