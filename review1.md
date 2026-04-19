# Peer Review — Explainability Evaluation Framework for RL Policies Based on Structural Constraint Bottlenecks

**対象**: draft_en.md（英語版・全文）  
**実施日**: 2026-04-19（再実施）

---

## Reviewer A (Methodology Expert)

### Strengths

1. **Clear decoupling design.** The separation of Oracle and Surrogate training avoids the explainability-performance trade-off cleanly, and the two-stage evaluation (fidelity then invariance) is logically well-structured.

2. **Systematic experimental design.** The paper includes a deliberate progression from baseline (Exp 1) to direct evidence (Exp 2) to contrastive evidence (Exp 3), with supplementary experiments addressing alternative explanations (data volume, model type). The claim-to-experiment mapping in Section 5.1 is commendable.

3. **Honest statistical reporting.** Holm-Bonferroni correction is applied, non-significant results are reported as such, and the paper repeatedly notes when differences fail to reach significance.

4. **Sensitivity analyses (Tables 6 and 7).** Testing the robustness of threshold parameters is valuable for a framework paper.

### Weaknesses

**[MAJOR] W-A1: Data discrepancy in Experiment 1.**

Section 6.1 reports `N=0, K=4, d=5: AA=0.915±0.028`. The raw data in `exp001_cartpole_noise/summary.txt` shows `AA=0.910±0.016` for that configuration. The 0.915±0.028 value comes from `exp004_cartpole_comparison/summary.txt`, which is labeled Experiment 4. The standard deviations differ substantially (0.016 vs 0.028), indicating results from different experiment runs are being conflated.

> **Fix:** Explicitly document that `exp004` is the canonical source for both Experiment 1 and Experiment 4, and explain why (e.g., unified seed set). The current EXPERIMENT_MAP.md notes this but the paper text does not.

**[MAJOR] W-A2: P-value misreporting in Experiment 3.**

Section 7 states: "Other shift conditions (gravity_lo, gravity_hi, pole_short) were not significant after Holm–Bonferroni correction (p_adj>0.18)." The actual values in `pvalue_summary.csv` are: gravity_hi p_adj=0.087, gravity_lo p_adj=0.186, pole_short p_adj=0.186. The claim "p_adj>0.18" is false for gravity_hi (0.087 < 0.18).

> **Fix:** Correct to "p_adj>0.08" or report the exact values.

**[MINOR] W-A3: "Decoupling" framing overstates novelty.**

Training a surrogate from a fixed policy and evaluating it is standard practice in policy distillation (Bastani et al., 2018; Vasic et al., 2019). The actual novelty is the invariance evaluation axis, not decoupling per se. Foregrounding "decoupling" as Contribution 1 dilutes the message.

> **Fix:** Reframe Contribution 1 to emphasize the invariance evaluation methodology as the primary contribution.

---

## Reviewer B (Domain Expert — XAI/RL)

### Strengths

1. **Central insight is sound.** The observation that high AA is necessary but not sufficient, and that invariance under distribution shift provides a complementary axis, addresses a genuine gap in XRL evaluation.

2. **SHAP comparison (Section 6.2, Figure 4).** Demonstrating that SHAP feature importance is nearly identical between train and reversed_c while the policy collapses is an effective illustration of the framework's added value.

3. **MoET tree visualization.** Showing the actual tree structure with the root split on the spurious feature is compelling qualitative evidence.

4. **Good positioning vs. IRM.** The distinction between invariant learning (training-time) and invariance evaluation (post-hoc diagnosis) is handled correctly.

### Weaknesses

**[MAJOR] W-B1: The Spurious GridWorld is trivially engineered.**

When p=0.0, the spurious feature c deterministically indicates the goal. Any distribution shift that reverses it will cause failure. This is not subtle. The claim that the framework provides novel diagnostic capability is harder to justify in this setting. The p=0.2 and p=0.5 conditions are more realistic but receive less analytical attention.

> **Fix:** Move p=0.2/0.5 analysis to the main body as the primary demonstration, treating p=0.0 as a limiting case illustration.

**[MAJOR] W-B2: No comparison with existing XAI evaluation methods.**

The paper positions itself as an "evaluation framework" but only compares against SHAP (an explanation method, not an evaluation method). There is no comparison with faithfulness metrics (Alvarez-Melis & Jaakkola, 2018) or any other evaluation methodology.

> **Fix:** Apply at least one existing evaluation method to the same experiments and show what it would or would not detect.

**[MAJOR] W-B3: Experiment 8 logical gap — DAgger fails Stage 1, yet Stage 2 is applied.**

The framework's Stage 1 criterion is AA > 0.9 (or R² > 0.9). The DAgger surrogate achieves AA_ε=0.420, which is well below 0.9. The paper does not address whether a surrogate that fails Stage 1 should be used for Stage 2 invariance evaluation. This is a logical inconsistency in the framework.

> **Fix:** Clarify the framework's behavior when Stage 1 is not met for continuous action spaces. Either revise the Stage 1 criterion for continuous spaces (where R² governs, not AA_ε), or explain why Stage 2 is applied despite Stage 1 non-compliance.

**[MINOR] W-B4: Experiment 7 reveals MoET/Tree fail in continuous control.**

MoET achieves J_S=−264 and Tree J_S=−294 in LunarLander despite AA≈0.72. Only GBT (a non-interpretable ensemble) works. This tension between the framework's preferred surrogate models (interpretable ones) and their viability in continuous environments is not adequately addressed.

**[MINOR] W-B5: Mindlin et al. (2025) connection is not developed.**

The "preliminary evaluation" framing in Section 2.4 is hand-waved. No concrete integration scenario is provided.

---

## Reviewer C (Statistics/Rigor Expert)

### Strengths

1. **Proper use of Holm-Bonferroni correction** with Cohen's d effect sizes.
2. **10 seeds with mean and standard deviation** is reasonable for RL.
3. **Independent distillation and evaluation seeds** prevent overfitting artifacts.

### Weaknesses

**[MAJOR] W-C1: Massive variance in key metrics undermines threshold-based claims.**

Several conditions show standard deviations comparable to or exceeding the effect sizes:
- Experiment 2, p=0.2, reversed_c, K=4,d=5: AA=0.922±0.200. This means individual seeds range from near 0.5 to near 1.0. Reporting a mean of 0.922 as "passing" AA > 0.9 is misleading.
- Experiment 2, p=0.5, reversed_c: AA=0.940±0.132.
- Experiment 3, pole_short: AA=0.846±0.115 (all 10 seeds).

When variance is this large, the diagnostic threshold's reliability for individual deployments is unclear.

> **Fix:** Report median and IQR alongside mean and SD for high-variance conditions. Report per-seed detection rates and bootstrap confidence intervals on the detection rate.

**[MAJOR] W-C2: Selective converged-seed reporting.**

Experiment 3 reports both all-10 and converged-8 statistics. However, it is not stated whether all other experiments (2, 7, 8) had full convergence. If any seeds failed in those experiments and were silently excluded, this should be disclosed.

> **Fix:** Explicitly state convergence status for all experiments. If some seeds were excluded from any experiment, report this uniformly.

**[MINOR] W-C3: No statistical testing for BC vs. DAgger comparison.**

Table A7 reports means and standard deviations for BC vs. DAgger but no significance tests. Given the key claim that "AA_ε and J_S measure different aspects," this should be formally tested.

**[MINOR] W-C4: Appendix-reliant primary claims.**

Claims in the abstract, introduction, and conclusion (Contribution 3, Hopper DAgger results) are supported only by appendix material. For NeurIPS format, appendix material should be supplementary, not primary evidence.

---

## Cross-Reviewer Summary

### Major Issues

| # | Issue | Reviewer |
|---|-------|----------|
| M1 | Data discrepancy: Exp 1 reports AA=0.915 from exp004, not exp001 | A |
| M2 | P-value misreporting: "p_adj>0.18" but gravity_hi p_adj=0.087 | A |
| M3 | High variance undermines threshold-based diagnostics (AA=0.922±0.200) | C |
| M4 | No comparison with existing XAI evaluation methods | B |
| M5 | Exp 8 logical gap: DAgger fails Stage 1 (AA=0.42) but Stage 2 applied | B |
| M6 | Primary claims (Contribution 3) rely on appendix-only experiments | C |

### Minor Issues

| # | Issue |
|---|-------|
| m1 | "Surrogate model" overloads an existing ML term |
| m2 | MoET tree visualization in code-block format rather than figure |
| m3 | Bullet-point lists in Sections 4.3 and 5.1 |
| m4 | Excessive hedging in Section 3.3 ("does not provide definitive judgments") |
| m5 | Mindlin connection hand-waved |
| m6 | "Decoupling" framing overstates novelty as Contribution 1 |

### What's Missing

- No ablation on distillation quality's effect on invariance evaluation outcomes.
- No analysis of false positive rate (non-spurious features flagged as spurious).
- No analysis of false negative rate (shift chosen does not break the dependency).
- No engagement with causal inference literature despite repeated causal disclaimers.
- No guidance on how many distribution shifts are needed for reliable diagnosis.

### What's Good

- Core idea addresses a genuine gap and is clearly articulated.
- All reported numerical values verified against raw experiment files and found consistent (with the exception of M1 and M2 above).
- Statistical methodology (Welch's t, Holm-Bonferroni, Cohen's d) is appropriate.
- Contrastive design (Exp 2 vs Exp 3) is the paper's strongest evidence.
- English writing quality is natural and technically precise.

### Recommendation

**Revise and Resubmit.** The core idea and experimental design are solid. Data discrepancy M1 and p-value misreporting M2 are correctable. The logical gap in continuous-space evaluation (M5) and missing comparisons with evaluation baselines (M4) are the most substantive issues requiring new work.
