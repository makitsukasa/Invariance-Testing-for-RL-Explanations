# Peer Review Report — 構造制約ボトルネックに基づく強化学習方策の説明可能性評価枠組み

---

## Reviewer A: Methodology Expert

### Strengths

1. **Clean experimental design for the core claim.** The decoupling of Oracle and Surrogate, followed by two-stage evaluation (reproducibility then invariance), is methodologically sound. Experiment 2 (spurious GridWorld) and Experiment 3 (non-spurious CartPole) form a proper contrastive pair that directly addresses the central claim.

2. **Appropriate use of multiple seeds.** 10 seeds across main experiments with reported mean and standard deviation is adequate for the environment scale. The choice to use independent seeds for distillation and evaluation data is good practice that prevents memorization artifacts.

3. **Sensitivity analysis of thresholds.** Tables 6 and 7 for AA threshold and alpha sensitivity are a methodological strength. The large separation between spurious and non-spurious conditions makes the results robust to threshold choice.

4. **SHAP comparison in Experiment 2.** Demonstrating that SHAP importance values for the spurious feature remain unchanged between train and reversed_c conditions while the framework detects the problem is an effective methodological comparison.

### Weaknesses

**[MAJOR] W-A1: Numerical discrepancies between stored experiment data and paper claims.**

The paper reports for Experiment 1: `N=0, K=4, d=5: AA=0.915±0.028` (Section 6.1). The actual experiment summary file shows `AA=0.910±0.016`. Similarly, `N=16, K=4, d=5` is reported as `AA=0.819±0.033` but the file shows `AA=0.809±0.010`. The discrepancy arises from using different seed sets in different sub-experiments. A paper must report numbers from a single, consistent experimental run.

> **Fix:** Re-run Experiment 1 with consistent seeds and report a single set of numbers. If `0.915` comes from a separate sub-experiment, label it clearly, or use only the canonical 10-seed run for all claims.

**[MAJOR] W-A2: Hopper R² metric is not traceable in stored results.**

The paper claims `RegTree d=12: train R²=0.920±0.009` (Appendix 5, Section 5.5). However, the experiment summary files for exp011 and exp012 only report AA values — no R² column. These R² values appear to have been computed post-hoc and are not stored in canonical output, creating a reproducibility gap.

> **Fix:** Either (a) re-run experiments to output R² as a first-class metric in CSV/summary files, or (b) provide a documented post-processing script that computes R² from stored action difference files and produces the reported numbers.

**[MAJOR] W-A3: Experiment 7 (LunarLander) uses only 5 seeds while the paper states 10 as standard.**

Section 5.1 states "各条件は乱数シード10本で実行し". The LunarLander experiment (exp009) evidence contains only seeds 42, 123, 456, 789, 1011. This is a direct contradiction.

> **Fix:** Run 5 additional seeds to reach 10, or explicitly state that LunarLander and Hopper use 5 seeds and justify why.

**[MINOR] W-A4: Experiment 12 summary shows `±nan` for standard deviations.** While the CSV may have 10 seeds of data, the summary aggregation appears broken. This is a reproducibility concern.

**[MINOR] W-A5: The decision tree visualization in Section 6.2 is from a single seed (seed=42), single condition.** The claim that "all 4 experts learned the same structure" is not verified across all 10 seeds.

---

## Reviewer B: Domain Expert (XRL / Explainable RL)

### Strengths

1. **Clear positioning relative to prior work.** The distinction between this framework as a post-hoc evaluation tool versus IRM/CBM as training strategies is well articulated. The paper correctly identifies the gap: existing distillation work (Bastani et al., 2018; Vasic et al., 2019) optimizes AA but does not check for spurious dependency replication.

2. **Model-agnostic design.** The framework genuinely does not depend on the internal structure of the Surrogate model, as demonstrated by testing across decision trees, MoET, linear models, and GBT. This is a real strength for practical adoption.

3. **Honest limitations section.** The limitations are concrete and specific (small environments, 10 seeds, oracle presupposition, shift selection arbitrariness). This is better than most papers.

### Weaknesses

**[MAJOR] W-B1: The contribution is primarily diagnostic, not prescriptive, which limits practical impact.**

The paper repeatedly acknowledges that detection without remediation has limited utility: 「スプリアス依存の検出は、その後の対処法と組み合わせてはじめて実用的な意義を持つ」. A reviewer will ask: once you detect spurious dependency, what do you do? The paper offers no guidance beyond "debug and improve."

> **Fix:** Add a paragraph in Discussion (Section 7) outlining 2–3 concrete remediation strategies following a positive detection (e.g., re-training oracle with IRM, feature selection for distillation, regularized distillation), with references.

**[MAJOR] W-B2: The Hopper results actively undermine the contribution rather than supporting it.**

For Hopper (exp011), RegTree d=12 achieves R²=0.920 on train but J_S is only 5–10% of oracle performance (~150–200 vs ~3500). The invariance evaluation is therefore inapplicable: you cannot meaningfully evaluate distribution shift behavior when the surrogate does not function as a policy even in-distribution. Including these results makes the framework look weaker.

> **Fix:** Either (a) relegate Hopper entirely to an appendix as a negative/preliminary result, with clear framing, or (b) find a surrogate architecture that achieves functional J_S on Hopper before applying invariance evaluation.

**[MINOR] W-B3: The GridWorld environment is custom-designed to demonstrate the phenomenon.** The spurious feature c is engineered to perfectly correlate with the goal during training. Real-world spurious correlations are rarely this clean.

> **Fix:** Strengthen the p=0.2 and p=0.5 results as the partial-correlation cases, and explicitly frame them as addressing this concern.

**[MINOR] W-B4: Citation [^2] (Mindlin et al., 2025) appears only in the introduction with no further discussion.** Either integrate the interactive-explanation perspective into the Discussion or remove this citation.

**[MINOR] W-B5: No comparison against existing XRL evaluation frameworks.** The claim that AA alone is insufficient is asserted rather than demonstrated against a baseline evaluator that would have given misleading conclusions.

---

## Reviewer C: Statistics / Rigor Expert

### Strengths

1. **10 seeds with mean and standard deviation** is adequate for the toy environments used. Threshold sensitivity analysis (Tables 6, 7) demonstrates that conclusions are not an artifact of a single threshold choice.

2. **Clear separation between conditions.** In exp002, reversed_c produces J=−1.000 (complete failure) versus train J≈0.97 — a massive effect size that does not require sophisticated testing to interpret.

### Weaknesses

**[CRITICAL] W-C1: No formal statistical tests are reported for the main claims.**

The central claims — that the framework distinguishes spurious from non-spurious environments — are supported only by point estimates and standard deviations. While effect sizes are large, the paper should report at minimum: a formal test (e.g., paired t-test or Wilcoxon) comparing J_S between train and shifted conditions, effect sizes (Cohen's d), and confidence intervals.

The large standard deviations in exp003 (J_oracle=428.1±148.5 for train) suggest that some seeds produce very different behavior, making the absence of formal testing more concerning.

> **Fix:** Add a statistical comparison table for key contrasts: exp002 train vs reversed_c (AA and J), exp003 across shift conditions. Report 95% confidence intervals. For n=10, use a nonparametric test if normality cannot be assumed.

**[MAJOR] W-C2: Oracle convergence failures contaminate the exp003 statistics.**

`J_oracle=428.1±148.5` for the train condition (CV ≈ 35%) is attributed to "DQN stochastic convergence (approximately 2 of 10 seeds fail to converge)." Including non-converged oracle seeds in the aggregate statistics inflates variance and contaminates the AA/J_S means.

> **Fix:** Either (a) filter seeds where oracle fails to reach threshold (J ≥ 450) and report statistics on remaining seeds (with clear disclosure), or (b) re-train oracles until all 10 seeds converge. Report both filtered and unfiltered results if desired.

**[MAJOR] W-C3: LunarLander (Experiment 7) has only 5 seeds.**

With n=5, the 95% CI for GBT train AA=0.876±0.026 is approximately [0.844, 0.908]. This is acceptable for a supplementary result, but the paper does not flag the reduced statistical power, and the stated methodology implies n=10 for all experiments.

**[MINOR] W-C4: The α sensitivity analysis (Table 7) is trivially uninformative for the spurious case.** When J_S/J_train is −1.03 or 0.06, any reasonable α detects it. The analysis would be more meaningful if borderline cases existed where α choice matters.

**[MINOR] W-C5: The multiple comparison correction method is not explicitly named.** The paper mentions "Holm–Bonferroni 補正" once (exp004) but does not consistently specify the correction family across experiments.

---

## Cross-Reviewer Consensus Issues

### [CRITICAL]

**CR-1: Word count is insufficient for a full conference submission.**

The main body (Sections 1–9, excluding appendices) contains approximately 2,900–3,100 words. This is well below the NeurIPS/ICML target of 5,000–6,500 words. Experiments 4–8 are summarized in a single subsection (Section 5.5) with one paragraph each, deferring all details to appendices. The paper reads as an extended abstract or workshop paper. The Results section (Section 6) covers only Experiments 1–3; Experiments 4–8 appear only as appendices, making the main body thin.

**CR-2: No reference list.**

The paper uses footnote-style citations (`[^1]`, `[^2]`, etc.) but does not include a rendered bibliography section. This is a formatting defect.

### [MAJOR]

**CR-3: Bullet-point lists in Section 1 (contributions) and Section 5.1 (experiment objectives).** Numbered lists in the contribution paragraph are common in ML papers but should be transformed into prose for a polished submission.

**CR-4: Decision tree visualization in Section 6.2 is inline text, not a figure.** The paper has 4 image figures (Figures 1–4), which meets the minimum, but the ASCII tree should be rendered as a proper figure for camera-ready.

**CR-5: Submission venue is ambiguous.** The paper is written entirely in Japanese. If targeting a Japanese venue, the NeurIPS word count criterion is irrelevant. If targeting an English-language venue, the paper must be translated. The title length check and formatting requirements differ by venue.

**CR-6: Compute resources not reported.** GPU/CPU type, total compute time, and memory requirements are absent.

---

## Summary Table

| Criterion | Status |
|-----------|--------|
| Topic alignment | PASS — paper stays on stated topic throughout |
| Claim-evidence alignment | PARTIAL FAIL — Hopper R² not traceable; exp001 numbers inconsistent with stored data |
| Statistical validity | FAIL — no formal tests for main claims; oracle failure contamination unaddressed |
| Completeness | FAIL — ~3,000 words (target 5,000–6,500); no reference list |
| Reproducibility | PARTIAL FAIL — hyperparameters specified but R² computation untraceable; seed count inconsistency |
| Writing quality | PASS (with issues) — flowing prose in most sections; some numbered lists |
| Figures | PASS — 4 figures present |
| Citation distribution | PASS (marginal) — present in Method and Discussion, though sparse |

**Overall verdict: Major Revision required.**

The core experimental design and central claim are sound. The contrastive pair (exp002 spurious vs exp003 non-spurious) is the clearest and most convincing result. However, the paper is too short for a full-venue submission, lacks formal statistical tests for the main claims, has numerical traceability issues (exp001 discrepancy, Hopper R² provenance), and is missing a reference list. The Hopper results in Appendix 5 should be reconsidered — as currently framed, they weaken rather than strengthen the contribution.
