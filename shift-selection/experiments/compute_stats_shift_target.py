"""exp030 の集計：選定と評価を独立させた、シフト対象の選定の検証。

設計（判定条件の正本）：experiments/plans/exp030_shift_target_validation.md

exp030 の results.csv（全特徴 × 2 シフトの評価）と exp029 の results.csv（Δ・SHAP の値）を
seed・p で突き合わせ、選定法ごとに正解集合への当たりを数える。

Usage:
    python experiments/compute_stats_shift_target.py RESULTS_030.csv --exp029 RESULTS_029.csv [--save]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from experiments.compute_stats import _ci_str, _pval_str, mcnemar_test
from experiments.run_shift_target_validation import shift_conditions

N_NOISE = 7
SHORT = ["agent_x", "agent_y", "c"] + [f"noise_{i}" for i in range(N_NOISE)]
LONG  = ["agent_x", "agent_y", "c (spurious)"] + [f"noise_{i}" for i in range(N_NOISE)]
N_FEAT = len(SHORT)
THETA_AA, ALPHA, STAGE1_AA = 0.9, 0.8, 0.9
SELECTORS = {
    "delta_sur": "Δ（サロゲート）",
    "shap_sur":  "SHAP（サロゲート）",
    "delta_ora": "Δ（オラクル）",
    "shap_ora":  "SHAP（オラクル）",
}
RANDOM_DRAW_SEED = 20261026
CONDS = [c for c in shift_conditions(N_NOISE) if c[1] is not None]   # (名前, 特徴, 種類)
VARIANTS = {k: [c for c in CONDS if c[1] == k] for k in range(N_FEAT)}


# --- 判定 -----------------------------------------------------------------------

def _flags(row: pd.Series, set_name: str) -> dict:
    """条件ごと・特徴ごとの G_J・G_inv。基準値 J_S(train) が 0 以下なら判定しない（eligible=False）。"""
    base = row[f"{set_name}__none__js"]
    eligible = base > 0
    cond_j, cond_inv = {}, {}
    for name, _, _ in CONDS:
        js, aa = row[f"{set_name}__{name}__js"], row[f"{set_name}__{name}__aa"]
        cond_j[name]   = bool(eligible and js < ALPHA * base)
        cond_inv[name] = bool(cond_j[name] and aa > THETA_AA)
    feat_j   = [any(cond_j[c[0]]   for c in VARIANTS[k]) for k in range(N_FEAT)]
    feat_inv = [any(cond_inv[c[0]] for c in VARIANTS[k]) for k in range(N_FEAT)]
    return {"eligible": eligible, "base": base, "cond_j": cond_j, "cond_inv": cond_inv,
            "feat_j": np.array(feat_j), "feat_inv": np.array(feat_inv)}


def _ranking(row: pd.Series, key: str) -> np.ndarray:
    scores = np.array([row[f"{key}_{n}"] for n in LONG], dtype=float)
    return np.argsort(-scores, kind="stable")


def build_table(df30: pd.DataFrame, df29: pd.DataFrame) -> list[dict]:
    df29 = df29.copy()
    df29["_p"] = df29["spurious_p"].round(3)
    df30 = df30.copy()
    df30["_p"] = df30["spurious_p"].round(3)
    m = df30.merge(df29, on=["seed", "_p"], suffixes=("", "_029"))
    if len(m) != len(df30):
        raise ValueError(f"exp029 と突き合わせられない行がある（{len(df30)} 行中 {len(m)} 行）")
    rng = np.random.default_rng(RANDOM_DRAW_SEED)
    runs = []
    for _, row in m.sort_values(["_p", "seed"]).iterrows():
        gt, pl = _flags(row, "gt"), _flags(row, "pl")
        runs.append({
            "seed": int(row["seed"]), "p": float(row["_p"]), "row": row,
            "aa_train": float(row["aa_train"]), "stage1": bool(row["aa_train"] >= STAGE1_AA),
            "gt": gt, "pl": pl,
            "rank": {k: _ranking(row, k) for k in SELECTORS},
            "random_draw": int(rng.integers(N_FEAT)),
        })
    return runs


# --- 検定 -----------------------------------------------------------------------

def poisson_binomial_sf(probs: list[float], k_obs: int) -> float:
    """P(X >= k_obs)、X は成功確率 probs の独立なベルヌーイの和。"""
    dist = np.zeros(len(probs) + 1)
    dist[0] = 1.0
    for q in probs:
        dist[1:] = dist[1:] * (1 - q) + dist[:-1] * q
        dist[0] *= (1 - q)
    return float(dist[k_obs:].sum())


def holm(pvals: list[float]) -> list[float]:
    order = np.argsort(pvals)
    adj = np.empty(len(pvals))
    running = 0.0
    for i, idx in enumerate(order):
        running = max(running, (len(pvals) - i) * pvals[idx])
        adj[idx] = min(1.0, running)
    return adj.tolist()


# --- 選定の評価 -----------------------------------------------------------------

def _groups(runs: list[dict]):
    ps = sorted({r["p"] for r in runs})
    return [(p, [r for r in runs if r["p"] == p]) for p in ps] + [("ALL", runs)]


def _sel(r: dict, key: str) -> int:
    return r["random_draw"] if key == "random_draw" else int(r["rank"][key][0])


def selection_section(runs: list[dict], target: str) -> tuple[list[str], dict]:
    """target は 'feat_j'（G_J）または 'feat_inv'（G_inv）。"""
    label = "G_J（性能の崩壊）" if target == "feat_j" else "G_inv（主張1の判定基準）"
    lines = [f"## 選定の評価：正解 = {label}", ""]
    out = {}
    for p, sub in _groups(runs):
        ev = [r for r in sub if r["gt"]["eligible"] and r["gt"][target].any()]
        n_inel = sum(not r["gt"]["eligible"] for r in sub)
        n_empty = sum(r["gt"]["eligible"] and not r["gt"][target].any() for r in sub)
        n = len(ev)
        lines.append(f"### p = {p}：評価対象 {n} run（J_S(train) ≤ 0 で判定不能 {n_inel}、正解集合が空 {n_empty}）")
        if n == 0:
            lines.append("")
            continue
        exp1 = sum(r["gt"][target].sum() / N_FEAT for r in ev)
        lines.append(f"{'選定法':<22} {'hit@1':>26} {'hit@2':>26} {'検出までの回数（平均）':>12}")
        for key, name in list(SELECTORS.items()) + [("random_draw", "ランダム（固定 seed の 1 回）")]:
            h1 = sum(bool(r["gt"][target][_sel(r, key)]) for r in ev)
            if key == "random_draw":
                lines.append(f"{name:<22} {_ci_str(h1, n):>26}")
                continue
            h2 = sum(bool(r["gt"][target][r["rank"][key][:2]].any()) for r in ev)
            tests = np.mean([int(np.argmax(r["gt"][target][r["rank"][key]])) + 1 for r in ev])
            lines.append(f"{name:<22} {_ci_str(h1, n):>26} {_ci_str(h2, n):>26} {tests:>12.2f}")
            out[(p, key)] = h1
        exp2 = sum(1 - (1 - r["gt"][target].sum() / N_FEAT) * (1 - r["gt"][target].sum() / (N_FEAT - 1))
                   for r in ev)
        exp_tests = np.mean([(N_FEAT + 1) / (r["gt"][target].sum() + 1) for r in ev])
        lines.append(f"{'ランダム（期待値）':<22} {exp1:>18.1f}/{n} ({exp1/n:.0%}) {exp2:>18.1f}/{n} ({exp2/n:.0%}) {exp_tests:>12.2f}")
        sizes = pd.Series([int(r["gt"][target].sum()) for r in ev]).value_counts().sort_index()
        lines.append("正解集合の大きさ |H|： " + ", ".join(f"{k} 個 → {v} run" for k, v in sizes.items()))
        lines.append("")
    return lines, out


def h1_test(runs: list[dict]) -> tuple[float, int, float, int]:
    ev = [r for r in runs if r["gt"]["eligible"] and r["gt"]["feat_j"].any()]
    k = sum(bool(r["gt"]["feat_j"][_sel(r, "delta_sur")]) for r in ev)
    probs = [r["gt"]["feat_j"].sum() / N_FEAT for r in ev]
    return poisson_binomial_sf(probs, k), k, float(sum(probs)), len(ev)


# --- 診断手順全体 -----------------------------------------------------------------

CATS = ["段階1で終了", "段階2で検出", "段階2で誤警告", "段階2で見逃し", "段階2で非検出（正解集合が空）"]


def _category(r: dict, k: int, gated: bool, crit: str = "feat_inv") -> str:
    if gated and not r["stage1"]:
        return CATS[0]
    flagged = bool(r["pl"][crit][k])
    in_h = bool(r["gt"][crit][k])
    if flagged:
        return CATS[1] if in_h else CATS[2]
    return CATS[3] if r["gt"][crit].any() else CATS[4]


def _cat_counts(sub: list[dict], key: str, gated: bool, crit: str = "feat_inv") -> dict[str, float]:
    counts = {c: 0.0 for c in CATS}
    for r in sub:
        if key == "random":
            for k in range(N_FEAT):
                counts[_category(r, k, gated, crit)] += 1 / N_FEAT
        else:
            counts[_category(r, _sel(r, key), gated, crit)] += 1
    return counts


def pipeline_section(runs: list[dict], gated: bool, crit: str = "feat_inv") -> list[str]:
    title = "段階1あり（論文A の手順どおり、主な結果）" if gated else "段階1なし"
    if crit == "feat_j":
        title += "、判定は G_J（AA の条件を外す。2026-10-26 の動作確認の後に追加した補足）"
    h = "H_inv" if crit == "feat_inv" else "H_J"
    lines = [f"## 診断手順全体：{title}", "",
             f"検出 = 手順用の再テスト（200 エピソード）で疑いと判定し、正解（500 エピソード）でも {h} に入る特徴。",
             f"誤警告率の分母は段階1 を通過した全 run（{h} が空の run を含む）。ランダムは期待値。", ""]
    for p, sub in _groups(runs):
        n = len(sub)
        n_pass = sum(r["stage1"] for r in sub) if gated else n
        n_empty_pass = sum((r["stage1"] or not gated) and not r["gt"][crit].any() for r in sub)
        lines.append(f"### p = {p}：{n} run、段階1 通過 {n_pass}、うち {h} が空 {n_empty_pass}")
        lines.append(f"{'選定法':<20} " + " ".join(f"{c:>10}" for c in CATS)
                     + f" {'検出率（全 run）':>26} {'検出率（段階1 通過）':>26} {'誤警告率':>26} {'誤警告率（正解集合が空）':>12}")
        for key, name in list(SELECTORS.items()) + [("random", "ランダム（期待値）")]:
            cc = _cat_counts(sub, key, gated, crit)
            fa_empty = sum(1 for r in sub if (r["stage1"] or not gated) and not r["gt"][crit].any()
                           and key != "random" and _category(r, _sel(r, key), gated, crit) == CATS[2])
            if key == "random":
                fa_empty = sum(np.mean([_category(r, k, gated, crit) == CATS[2] for k in range(N_FEAT)])
                               for r in sub if (r["stage1"] or not gated) and not r["gt"][crit].any())
                det_all = f"{cc[CATS[1]]:.1f}/{n}"
                det_pass = f"{cc[CATS[1]]:.1f}/{n_pass}" if n_pass else "-"
                fa = f"{cc[CATS[2]]:.1f}/{n_pass}" if n_pass else "-"
            else:
                det_all = _ci_str(int(cc[CATS[1]]), n)
                det_pass = _ci_str(int(cc[CATS[1]]), n_pass) if n_pass else "-"
                fa = _ci_str(int(cc[CATS[2]]), n_pass) if n_pass else "-"
            fa_e = f"{fa_empty:.1f}/{n_empty_pass}" if n_empty_pass else "-"
            lines.append(f"{name:<20} " + " ".join(f"{cc[c]:>10.1f}" for c in CATS)
                         + f" {det_all:>26} {det_pass:>26} {fa:>26} {fa_e:>12}")
        lines.append("")
    return lines


def h2_test(runs: list[dict]) -> tuple[float, int, float, int]:
    k = sum(_category(r, _sel(r, "delta_sur"), True) == CATS[1] for r in runs)
    probs = [np.mean([_category(r, j, True) == CATS[1] for j in range(N_FEAT)]) for r in runs]
    return poisson_binomial_sf(probs, k), k, float(sum(probs)), len(runs)


# --- 補足：特徴別・シフト条件別 ---------------------------------------------------

def condition_section(runs: list[dict]) -> list[str]:
    lines = ["## 特徴別・シフト条件別の性能低下（正解の評価、500 エピソード）", "",
             "低下 = J_S(train) − J_S(shift)、比 = J_S(shift)/J_S(train)（J_S(train) ≤ 0 の run は比と判定から除く）。",
             "G_J・G_inv はその条件で判定が成り立った run 数。", ""]
    for p, sub in _groups(runs):
        el = [r for r in sub if r["gt"]["eligible"]]
        lines.append(f"### p = {p}（{len(sub)} run、比の対象 {len(el)} run）")
        lines.append(f"{'条件':<20} {'低下 平均±SD':>16} {'比 平均±SD':>16} {'J_O 平均':>9} {'AA 平均±SD':>14} {'G_J':>5} {'G_inv':>6}")
        for name, _, _ in CONDS:
            drop = np.array([r["row"]["gt__none__js"] - r["row"][f"gt__{name}__js"] for r in sub])
            ratio = np.array([r["row"][f"gt__{name}__js"] / r["gt"]["base"] for r in el]) if el else np.array([np.nan])
            jo = np.array([r["row"][f"gt__{name}__jo"] for r in sub])
            aa = np.array([r["row"][f"gt__{name}__aa"] for r in sub])
            nj = sum(r["gt"]["cond_j"][name] for r in sub)
            ni = sum(r["gt"]["cond_inv"][name] for r in sub)
            lines.append(f"{name:<20} {drop.mean():>+8.3f}±{drop.std():.3f} {np.nanmean(ratio):>+8.2f}±{np.nanstd(ratio):.2f} "
                         f"{jo.mean():>+9.3f} {aa.mean():>8.3f}±{aa.std():.3f} {nj:>5} {ni:>6}")
        lines.append("")
    lines += ["## 正解集合に入った特徴が、どのシフトで判定されたか（全 run）", ""]
    for target, label in (("cond_j", "G_J"), ("cond_inv", "G_inv")):
        lines.append(f"### {label}")
        lines.append(f"{'特徴':<10} {'片方（1 つ目）':>14} {'片方（2 つ目）':>14} {'両方':>6}")
        for k in range(N_FEAT):
            v1, v2 = VARIANTS[k][0][0], VARIANTS[k][1][0]
            a = sum(r["gt"][target][v1] and not r["gt"][target][v2] for r in runs)
            b = sum(r["gt"][target][v2] and not r["gt"][target][v1] for r in runs)
            both = sum(r["gt"][target][v1] and r["gt"][target][v2] for r in runs)
            lines.append(f"{SHORT[k]:<10} {a:>6}（{VARIANTS[k][0][2]}） {b:>6}（{VARIANTS[k][1][2]}） {both:>6}")
        lines.append("")
    return lines


# --- 副次：McNemar、Δ とシフトの比較 --------------------------------------------------

def mcnemar_section(runs: list[dict]) -> list[str]:
    lines = ["## 対応のある McNemar 検定（hit@1、正解 = G_J、Yates 補正あり）", "",
             "b = 左だけ当たり、c = 右だけ当たり。対象は正解集合が空でない run。", ""]
    for a, b_key in (("delta_sur", "shap_sur"), ("delta_ora", "shap_ora"), ("delta_sur", "delta_ora")):
        lines.append(f"### {a} vs {b_key}")
        lines.append(f"{'p':>4} {'n':>4} {'b':>4} {'c':>4} {'McNemar p':>10}")
        for p, sub in _groups(runs):
            ev = [r for r in sub if r["gt"]["eligible"] and r["gt"]["feat_j"].any()]
            x = np.array([bool(r["gt"]["feat_j"][_sel(r, a)]) for r in ev])
            y = np.array([bool(r["gt"]["feat_j"][_sel(r, b_key)]) for r in ev])
            bb, cc = int((x & ~y).sum()), int((~x & y).sum())
            pv = mcnemar_test(bb, cc)[1] if bb + cc > 0 else 1.0
            lines.append(f"{p!s:>4} {len(ev):>4} {bb:>4} {cc:>4} {_pval_str(pv):>10}")
        lines.append("")
    return lines


def delta_vs_shift_section(runs: list[dict]) -> list[str]:
    lines = ["## Δ（置換による低下）とシフトによる低下の比較（サロゲート、正解の評価）", "",
             "シフトによる低下は、その特徴の 2 種類のシフトのうち大きい方。", ""]
    rhos = {p: [] for p in sorted({r["p"] for r in runs})}
    miss = []
    for r in runs:
        row = r["row"]
        delta = np.array([row[f"delta_sur_{n}"] for n in LONG], dtype=float)
        shift = np.array([max(row["gt__none__js"] - row[f"gt__{c[0]}__js"] for c in VARIANTS[k]) for k in range(N_FEAT)])
        rho = spearmanr(delta, shift).statistic
        if np.isfinite(rho):
            rhos[r["p"]].append(rho)
        top = _sel(r, "delta_sur")
        if r["gt"]["eligible"] and not r["gt"]["feat_j"][top]:
            h = [SHORT[k] for k in np.flatnonzero(r["gt"]["feat_j"])]
            miss.append(f"  p={r['p']} seed={r['seed']}: Δ top-1 = {SHORT[top]}（Δ={delta[top]:+.3f}、"
                        f"シフトでの低下={shift[top]:+.3f}）、H_J = {h or '空'}")
    lines.append("run ごとの Spearman 順位相関（10 特徴）：")
    for p, v in rhos.items():
        if v:
            q = np.percentile(v, [25, 50, 75])
            lines.append(f"  p={p}: n={len(v)}、中央値 {q[1]:+.2f}（四分位 {q[0]:+.2f}〜{q[2]:+.2f}）")
    lines += ["", f"Δ（サロゲート）の top-1 が H_J に入らなかった run（{len(miss)} 件）："] + miss + [""]
    return lines


# --- まとめ ---------------------------------------------------------------------

def analyze(df30: pd.DataFrame, df29: pd.DataFrame) -> list[str]:
    runs = build_table(df30, df29)
    lines = ["=" * 70, "  exp030 集計", "=" * 70, ""]
    if "repro_ok" in df30.columns:
        lines.append(f"exp029 との再現の確認：{int(df30['repro_ok'].sum())}/{len(df30)} run で一致")
    n_s1 = sum(r["stage1"] for r in runs)
    lines += [f"段階1（AA(train) ≥ {STAGE1_AA}）を通過した run：{n_s1}/{len(runs)}", ""]

    p1, k1, e1, n1 = h1_test(runs)
    p2, k2, e2, n2 = h2_test(runs)
    a1, a2 = holm([p1, p2])
    lines += ["## 主な仮説（片側、Holm 補正、有意水準 0.05）", "",
              f"H1（選定）：Δ（サロゲート）の hit@1（G_J） = {k1}/{n1}、ランダムの期待値 = {e1:.1f}/{n1}、"
              f"ポアソン二項の正確検定 p = {p1:.3g}、Holm 補正後 p = {a1:.3g} → {'棄却' if a1 < 0.05 else '棄却されない'}",
              f"H2（手順全体）：Δ（サロゲート）での成功 = {k2}/{n2}、ランダムの期待値 = {e2:.1f}/{n2}、"
              f"p = {p2:.3g}、Holm 補正後 p = {a2:.3g} → {'棄却' if a2 < 0.05 else '棄却されない'}", ""]

    sec, _ = selection_section(runs, "feat_j")
    lines += sec
    lines += pipeline_section(runs, gated=True)
    lines += pipeline_section(runs, gated=False)
    lines += pipeline_section(runs, gated=True, crit="feat_j")
    lines += pipeline_section(runs, gated=False, crit="feat_j")
    lines += condition_section(runs)
    lines += mcnemar_section(runs)
    sec, _ = selection_section(runs, "feat_inv")
    lines += sec
    lines += delta_vs_shift_section(runs)
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv")
    parser.add_argument("--exp029", default=str(ROOT / "experiments/results/exp029_shap_delta_same_model/results.csv"))
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()
    df30 = pd.read_csv(args.csv)
    df29 = pd.read_csv(args.exp029)
    text = "\n".join(analyze(df30, df29))
    print(text)
    if args.save:
        out = Path(args.csv).parent / "stats.txt"
        out.write_text(text + "\n", encoding="utf-8")
        print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
