"""exp030 の補足分析（記録済みの CSV だけを使う。新しい学習・評価はしない）。

1. p = 0.3 で Δ（サロゲート）がランダムと区別できなかった原因の切り分け
2. 論文A の判定の AA を、状態の変換による aa からロールアウトの状態による aa_roll に替えた場合の診断手順全体
   （感度の確認。事前登録した主な結果は aa のまま変えない）

Usage:
    python experiments/analyze_exp030_supplement.py [--save]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "experiments"))

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, spearmanr

import compute_stats_shift_target as st

RES29 = ROOT / "experiments/results/exp029_shap_delta_same_model/results.csv"
RES30 = ROOT / "experiments/results/exp030_shift_target_validation/results.csv"
NOISE = [f"noise_{i}" for i in range(7)]
C = "c (spurious)"


def delta_breakdown(d29: pd.DataFrame, d30: pd.DataFrame) -> list[str]:
    lines = ["## 1. p ごとの Δ の内訳（exp029）と、環境側の c のシフトによる低下（exp030 の gt）", "",
             "noise の置換（U(0,1) を U(0,1) で置き換える）は分布を変えないので、noise の Δ の真の値は 0 であり、",
             "観測された noise の Δ は推定のばらつき（特徴ごとに別のエピソード seed、200 エピソード）である。", ""]
    m = d29.merge(d30, on=["seed", "spurious_p"], suffixes=("", "_30"))
    hdr = (f"{'p':>4} {'モデル':<6} {'Δ(c) 平均±SD':>14} {'noise の Δ の SD':>16} {'noise の Δ の最大（run 平均）':>26} "
           f"{'c が top-1':>9} {'c 反転の低下':>11} {'c ランダム化の低下':>16}")
    lines.append(hdr)
    for p, g in m.groupby("spurious_p"):
        for s, js in (("sur", "js"), ("ora", "jo")):
            c = g[f"delta_{s}_{C}"]
            nz = g[[f"delta_{s}_{n}" for n in NOISE]]
            others = g[[f"delta_{s}_{n}" for n in ["agent_x", "agent_y"] + NOISE]]
            top_c = int((c > others.max(axis=1)).sum())
            drop_rev = (g[f"gt__none__{js}"] - g[f"gt__c__reversed__{js}"]).mean()
            drop_rnd = (g[f"gt__none__{js}"] - g[f"gt__c__random__{js}"]).mean()
            lines.append(f"{p:>4.1f} {s:<6} {c.mean():>+7.3f}±{c.std():.3f} {nz.values.std():>16.3f} "
                         f"{nz.max(axis=1).mean():>26.3f} {top_c:>6}/{len(g)} {drop_rev:>+11.3f} {drop_rnd:>+16.3f}")
    g = m[np.isclose(m.spurious_p, 0.3)]
    others = g[[f"delta_sur_{n}" for n in ["agent_x", "agent_y"] + NOISE]]
    hit = g[f"delta_sur_{C}"] > others.max(axis=1)
    lines += ["", "p = 0.3 で、Δ（サロゲート）の top-1 が c だった run と、そうでなかった run の AA(train)：",
              f"  c だった run：n = {hit.sum()}、平均 {g.aa_train[hit].mean():.3f}",
              f"  c でなかった run：n = {(~hit).sum()}、平均 {g.aa_train[~hit].mean():.3f}",
              f"  Mann–Whitney U（両側）p = {mannwhitneyu(g.aa_train[hit], g.aa_train[~hit]).pvalue:.3f}",
              f"  Spearman（AA(train) と Δ_sur(c)）ρ = {spearmanr(g.aa_train, g[f'delta_sur_{C}'])[0]:+.2f}"
              f"（p = {spearmanr(g.aa_train, g[f'delta_sur_{C}'])[1]:.3f}）",
              f"  Spearman（Δ_sur(c) と Δ_ora(c)）ρ = {spearmanr(g[f'delta_sur_{C}'], g[f'delta_ora_{C}'])[0]:+.2f}", ""]
    return lines


def aa_roll_pipeline(d29: pd.DataFrame, d30: pd.DataFrame) -> list[str]:
    d = d30.copy()
    for col in [c for c in d.columns if c.endswith("__aa_roll")]:
        d[col[: -len("_roll")]] = d[col]
    runs = st.build_table(d, d29)
    lines = ["## 2. 感度の確認：判定の AA を aa_roll に替えた場合（段階1あり、正解 = H_inv）", "",
             "事前登録した主な結果ではない。表の見方は stats.txt の「診断手順全体」と同じ。", ""]
    return lines + st.pipeline_section(runs, gated=True, crit="feat_inv")[2:]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", action="store_true")
    args = ap.parse_args()
    d29, d30 = pd.read_csv(RES29), pd.read_csv(RES30)
    lines = ["=" * 70, "  exp030 補足分析（記録済みの CSV のみ）", "=" * 70, ""]
    lines += delta_breakdown(d29, d30)
    lines += aa_roll_pipeline(d29, d30)
    text = "\n".join(lines)
    print(text)
    if args.save:
        (RES30.parent / "supplement.txt").write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
