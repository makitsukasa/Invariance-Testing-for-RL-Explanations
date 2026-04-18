"""
compute_pvalues.py — 主要主張に対する Welch t 検定 + Holm-Bonferroni 補正

使い方:
    .venv/Scripts/python.exe experiments/scripts/compute_pvalues.py

出力:
    experiments/results/pvalue_summary.csv  — 全比較のテーブル
    stdout に各テストの結果を出力

対象:
    [A] 実験2 (exp002): train vs reversed_c の AA および J_S（スプリアス検出の有意性）
    [B] 実験3 (exp003): train vs 各シフト条件の AA（非スプリアス環境の不変性）
    [C] 実験4 (exp004): N=0 での MoET vs Tree vs Linear の AA（モデル比較）
    [D] 実験7 (exp009): LunarLander GBT train vs gravity_lo の J_S

計算:
    - Welch t 検定（scipy.stats.ttest_ind, equal_var=False）
    - Cohen's d = (mean1 - mean2) / pooled_std
    - Holm-Bonferroni 補正（statsmodels.stats.multitest.multipletests）
    - 同一グループ内の全比較をまとめて補正
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

RESULTS_DIR = Path("experiments/results")


def cohen_d(a, b):
    n1, n2 = len(a), len(b)
    s1, s2 = np.std(a, ddof=1), np.std(b, ddof=1)
    pooled = np.sqrt(((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 2))
    return (np.mean(a) - np.mean(b)) / pooled if pooled > 0 else float("nan")


def welch_test(a, b):
    t, p = stats.ttest_ind(a, b, equal_var=False)
    d = cohen_d(a, b)
    return {"t": t, "p_raw": p, "cohen_d": d, "n1": len(a), "n2": len(b),
            "mean1": np.mean(a), "mean2": np.mean(b),
            "std1": np.std(a, ddof=1), "std2": np.std(b, ddof=1)}


def apply_holm(rows: list[dict]) -> list[dict]:
    pvals = [r["p_raw"] for r in rows]
    reject, p_adj, _, _ = multipletests(pvals, method="holm")
    for r, pa, rej in zip(rows, p_adj, reject):
        r["p_adj"] = pa
        r["reject_H0"] = rej
    return rows


# ──────────────────────────────────────────────
# [A] 実験2: exp002 spurious GridWorld (p=0.0, K=4, d=5)
# ──────────────────────────────────────────────
def test_exp002():
    df = pd.read_csv(RESULTS_DIR / "exp002_spurious_gridworld/metrics.csv")
    df = df[(df["spurious_p"] == 0.0) & (df["n_experts"] == 4) & (df["max_depth"] == 5)]

    train = df[df["eval_condition"] == "train"]
    rev_c = df[df["eval_condition"] == "reversed_c"]

    rows = []
    for metric in ["action_agreement", "j_reasoned"]:
        r = welch_test(train[metric].values, rev_c[metric].values)
        r.update({"group": "exp002", "comparison": f"train vs reversed_c ({metric})",
                  "metric": metric})
        rows.append(r)
    return rows


# ──────────────────────────────────────────────
# [B] 実験3: exp003 CartPole gravity shift
# ──────────────────────────────────────────────
def test_exp003():
    df = pd.read_csv(RESULTS_DIR / "exp003_cartpole_gravity/metrics.csv")
    df = df[(df["n_experts"] == 4) & (df["max_depth"] == 5)]

    train = df[df["condition"] == "train"]["action_agreement"].values
    conditions = [c for c in df["condition"].unique() if c != "train"]

    rows = []
    for cond in sorted(conditions):
        cond_data = df[df["condition"] == cond]["action_agreement"].values
        r = welch_test(train, cond_data)
        r.update({"group": "exp003", "comparison": f"train vs {cond} (AA)",
                  "metric": "action_agreement"})
        rows.append(r)
    return rows


# ──────────────────────────────────────────────
# [C] 実験4: exp004 CartPole model comparison at N=0
# ──────────────────────────────────────────────
def test_exp004():
    df = pd.read_csv(RESULTS_DIR / "exp004_cartpole_comparison/metrics.csv")

    rows = []
    for noise_dim in [0, 4, 8, 16]:
        sub = df[df["noise_dim"] == noise_dim]
        models = sorted(sub["model_type"].unique())
        pairs = [(m1, m2) for i, m1 in enumerate(models) for m2 in models[i+1:]]
        for m1, m2 in pairs:
            a = sub[sub["model_type"] == m1]["action_agreement"].values
            b = sub[sub["model_type"] == m2]["action_agreement"].values
            r = welch_test(a, b)
            r.update({"group": "exp004", "comparison": f"N={noise_dim}: {m1} vs {m2} (AA)",
                      "metric": "action_agreement"})
            rows.append(r)
    return rows


# ──────────────────────────────────────────────
# [D] 実験7: exp009 LunarLander GBT train vs gravity_lo
# ──────────────────────────────────────────────
def test_exp009():
    df = pd.read_csv(RESULTS_DIR / "exp009_gbt_continuous/metrics.csv")
    df = df[(df["env"] == "lunarlander") & (df["model_type"] == "gbt")]

    rows = []
    train = df[df["eval_condition"] == "train"]
    for cond in ["gravity_hi", "gravity_lo"]:
        cond_data = df[df["eval_condition"] == cond]
        for metric in ["action_agreement", "j_reasoned"]:
            if metric not in df.columns:
                continue
            r = welch_test(train[metric].values, cond_data[metric].values)
            r.update({"group": "exp009", "comparison": f"GBT train vs {cond} ({metric})",
                      "metric": metric})
            rows.append(r)
    return rows


def main():
    all_rows = []

    for test_fn, label in [
        (test_exp002, "exp002 GridWorld"),
        (test_exp003, "exp003 CartPole shift"),
        (test_exp004, "exp004 model comparison"),
        (test_exp009, "exp009 LunarLander"),
    ]:
        try:
            rows = test_fn()
            rows = apply_holm(rows)
            all_rows.extend(rows)
            print(f"\n=== {label} ({len(rows)} comparisons) ===")
            for r in rows:
                sig = "**" if r["reject_H0"] else "  "
                print(f"  {sig} {r['comparison']}")
                print(f"       mean1={r['mean1']:.3f}+/-{r['std1']:.3f}  "
                      f"mean2={r['mean2']:.3f}+/-{r['std2']:.3f}  "
                      f"p_raw={r['p_raw']:.4f}  p_adj={r['p_adj']:.4f}  d={r['cohen_d']:.2f}")
        except Exception as e:
            warnings.warn(f"[SKIP] {label}: {e}")

    if all_rows:
        out_path = RESULTS_DIR / "pvalue_summary.csv"
        df_out = pd.DataFrame(all_rows)
        cols = ["group", "comparison", "metric", "n1", "n2",
                "mean1", "std1", "mean2", "std2", "t", "p_raw", "p_adj", "cohen_d", "reject_H0"]
        df_out = df_out[[c for c in cols if c in df_out.columns]]
        df_out.to_csv(out_path, index=False, float_format="%.6f")
        print(f"\nFull table saved to: {out_path}")


if __name__ == "__main__":
    main()
