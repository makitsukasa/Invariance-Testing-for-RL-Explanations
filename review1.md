# Peer Review — Explainability Evaluation Framework for RL Policies Based on Structural Constraint Bottlenecks

**対象**: draft_en.md（英語版）  
**実施日**: 2026-04-19

> **注**: 本レビューは要約版のドラフトに基づいて実施されたため、一部の指摘（Critical A1: placeholder sections、Critical A2: zero figures、Major A3: threshold sensitivity not shown、Major B1: SHAP without evidence）は実際の draft_en.md には該当しない（本文はフル記述済み、Figure 1〜5 存在、Table 6/7 存在、Figure 4 = SHAP 比較）。これらはメモへの転記対象外とする。

---

## Reviewer A (Methodology Expert)

### Strengths

1. **Sound decoupling architecture.** The two-stage framework (fidelity → invariance) is methodologically clean. Separating Oracle from Surrogate avoids the performance-interpretability trade-off. The insight that high AA is necessary but not sufficient is well-motivated.

2. **Verified numerical claims.** All key numbers independently verified against raw data (exp002 summary, exp003 metrics.csv, exp004 summary, exp009 metrics.csv, exp011 r2_summary.csv, exp014 metrics.csv). All match: Exp 2 train AA=0.988±0.011, reversed_c AA=0.942±0.056, J_S=−1.000; Exp 3 pole_long p_adj=0.0004; LunarLander GBT J_S=236.8; Hopper DAgger J_S=2239 with gravity_lo reversal at 127%.

3. **Contrastive experimental design.** Experiment 2 (spurious → collapse) paired with Experiment 3 (non-spurious → no collapse) is a strong design for the core claim.

### Weaknesses

**[MINOR] W-A4: The "agnostic to internal structure" claim is underspecified.**

Contribution 1 claims the framework works for "arbitrary interpretable models" but experiments test only three model families (linear, tree, MoET) plus GBT. There is no formal statement of what properties a Surrogate model must have for the framework to apply (e.g., deterministic action output, finite action space, etc.).

> **Fix:** State explicitly what properties are required or note this as a limitation.

---

## Reviewer B (Domain Expert — XAI/RL)

### Strengths

1. **Addresses a real gap.** Bastani (2018) and Vasic (2019) optimize AA without checking for spurious dependency replication. The paper correctly identifies this blind spot.

2. **Good positioning relative to IRM and OOD robustness.** Section 2.3 carefully distinguishes post-hoc diagnosis from IRM's training objective.

3. **Extension to continuous control.** The BC vs DAgger contrast (AA_ε=0.703 + J_S=4.5% vs AA_ε=0.420 + J_S=63%) is a genuinely interesting result showing the two metrics capture different aspects.

### Weaknesses

**[MAJOR] W-B2: Hopper fidelity criterion ambiguity in continuous action spaces.**

Section 3.3 defines Stage 1 as "AA > 0.9 or R² > 0.9." For Hopper (continuous), RegTree d=12 achieves R²=0.922 (passes) but AA_ε=0.703 (fails). It is not clear from the text which metric governs in continuous action spaces. A reader could reasonably interpret the surrogate as failing Stage 1 fidelity.

> **Fix:** Clarify explicitly in Section 3.3 that for continuous action spaces, R² (or ε-agreement) replaces AA as the Stage 1 criterion, not as an addition to it.

**[MAJOR] W-B3: The framework lacks a formal decision procedure.**

The paper proposes two-stage evaluation but provides no algorithm or flowchart that a practitioner could follow: when exactly does a surrogate pass/fail Stage 1? What if AA passes but invariance is borderline? The framework is conceptual rather than operational.

> **Fix:** Add Algorithm 1 (or a decision flowchart) specifying inputs, thresholds, and output (pass/investigate/reject).

**[MINOR] W-B4: Mindlin et al. (2025) connection remains hand-waved.**

Section 2.4 suggests the framework could serve as a "preliminary evaluation" before human interaction, but no concrete integration path is given.

---

## Reviewer C (Statistics/Rigor Expert)

### Strengths

1. **Appropriate statistical methodology.** Welch's t-test with Holm-Bonferroni correction and Cohen's d is better than most papers. 10 seeds is adequate.

2. **Transparent seed filtering.** Reporting both all-10 and converged-8 statistics for Experiment 3 is methodologically transparent.

3. **Verified p-values.** All statistical claims confirmed against pvalue_summary.csv.

### Weaknesses

**[MAJOR] W-C1: Experiment 3 non-significant results may be presented without sufficient context.**

The paper states "other shifts not significant (p_adj>0.18)." However, the gravity_hi raw p-value (before Holm correction) may have been ≈0.03–0.09. Readers should know whether gravity_hi crossed raw significance before correction, as this affects the interpretation of "invariance."

> **Fix:** Report raw and adjusted p-values for all Experiment 3 contrasts, or add a sentence noting which conditions were nominally significant before correction.

**[MAJOR] W-C2: Hopper gravity_lo reversal claim is not robust to CI.**

The paper highlights "J_S=493 > J_oracle=389 (127% reversal)" under gravity_lo for the DAgger surrogate. However, J_S standard deviation is 483, meaning the 95% CI for J_S almost certainly includes values below J_oracle. The headline "reversal" is not statistically supported.

> **Fix:** Either report a CI for the J_S/J_oracle ratio and note the reversal is not significant, or soften the framing to "a tendency toward reversal, consistent with CartPole pole_long."

**[MINOR] W-C3: Converged-seed exclusion criterion (J ≥ 450) is post-hoc.**

The criterion is reasonable, but it was not pre-registered. Clarify whether statistical tests used 8 or 10 seeds, and note the post-hoc nature of the filter.

**[MINOR] W-C4: Experiment 4 multiple comparisons family not globally controlled.**

Holm-Bonferroni is applied within each noise level (3 comparisons per N), but not across all N levels jointly. The family-wise error rate across all 12 Experiment 4 comparisons is not controlled.

---

## Cross-Reviewer Summary

| Issue | ID | Severity |
|-------|-----|----------|
| "Arbitrary" models claim needs formal conditions | W-A4 | Minor |
| Hopper fidelity criterion (R² vs AA) ambiguous for continuous | W-B2 | Major |
| No formal decision procedure / Algorithm 1 | W-B3 | Major |
| Mindlin connection still hand-waved | W-B4 | Minor (re-flag) |
| Exp 3: raw vs adjusted p-values not reported | W-C1 | Major |
| Hopper gravity_lo reversal CI not robust | W-C2 | Major |
| Converged-seed filter is post-hoc, stat test seed set unclear | W-C3 | Minor |
| Exp 4 family-wise error rate not globally controlled | W-C4 | Minor |
| Citations sparse in Section 4 (Methods) and Section 5 (Experiments) | Cross | Minor |

### What Is Good

- Core idea is sound, addresses a genuine gap.
- All experimental data verified and reproducible (10 seeds, scripts present).
- Statistical methodology mostly appropriate.
- Contrastive experimental design (Exp 2 vs Exp 3) is effective.
- Related work positioning is careful and accurate.
- English writing quality is natural and technical.

### Verdict

The experimental evidence and core idea are solid. The paper is completable as-is from a content standpoint. The remaining issues are mostly about presentation clarity (algorithm, continuous-action criterion, CI reporting) rather than fundamental problems with the experimental design or conclusions.

**Suggested priority for revision:**
1. Clarify continuous-action Stage 1 criterion (W-B2)
2. Add Algorithm 1 or decision flowchart (W-B3)
3. Report raw+adjusted p-values for Exp 3 (W-C1)
4. Qualify Hopper gravity_lo reversal with CI (W-C2)
5. Address "arbitrary" models scope (W-A4)
