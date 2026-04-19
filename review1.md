# Peer Review: Detecting Spurious Dependencies in Surrogate Explanations of RL Policies via Invariance Testing

**対象**: draft_en.md（英語版・全文）  
**実施日**: 2026-04-20

---

## Reviewer A (Methodology Expert)

### Strengths

1. The decoupling design (Oracle fixed, Surrogate evaluated post-hoc) is clean and well-motivated. It correctly avoids the performance-explainability trade-off that plagues single-model approaches. The framework is genuinely model-agnostic.

2. The two-stage evaluation is logically sound. Requiring fidelity as a necessary condition before invariance testing is a proper gatekeeping structure. The diagnostic criteria (AA > θ_AA AND J_S collapse) are clearly defined and testable.

3. Experiment 2 now explicitly acknowledges the by-construction nature and frames its value correctly: "The value of this experiment lies not in demonstrating this consequence but in confirming that the proposed framework's diagnostic criteria function correctly in a controlled setting with a known ground truth." This is a mature framing.

4. Threshold sensitivity analysis (Tables 6 and 7) is now in the main text, and qualitative conclusions are shown to be robust across θ_AA ∈ {0.85, 0.90, 0.95} and α ∈ {0.7, 0.8, 0.9}.

### Weaknesses

1. **MAJOR: The framework is a necessary-condition detector, not a sufficient-condition evaluator.** The paper correctly notes that "high invariance does not guarantee the causal validity of the dependencies." However, the abstract says "identify states where AA is high but the explanation is wrong" without noting the converse does not hold (no detection ≠ explanation is correct). This asymmetry should be explicit in the abstract and conclusion.

2. **MAJOR: Distribution shift selection remains entirely manual and unguided.** Without knowing what to shift, the framework cannot be applied. The suggestion to use SHAP importance to prioritize shift candidates (Section 8) is a two-sentence aside in Limitations, not a methodological contribution. For a framework paper, this is the most critical user decision; it should be elevated to the main framework description (Section 3.3 or 4).

3. **MINOR: The paper conflates two different uses of "invariance."** In the IRM sense, invariance means a representation stable across environments. In this paper, it means AA and J_S are maintained after shift. Section 2.3 distinguishes them, but the term is used loosely thereafter.

4. **MINOR: The detection-remediation gap is not bridged.** Section 7 lists possible remedial actions but none are demonstrated.

### Actionable Revisions

- Add a sentence to the abstract: the framework detects spurious dependencies but cannot confirm their absence.
- Elevate the SHAP-guided shift selection heuristic from Limitations to Section 3.3 or 4.
- Add a brief terminological note in Section 3.3 distinguishing "invariance" as used here from IRM's concept.

---

## Reviewer B (Domain Expert -- XRL / Interpretable RL)

### Strengths

1. The related work section is comprehensive. The distinction from IRM (training-time vs. post-hoc) and from SHAP/LIME (revealing vs. evaluating dependencies) is clearly drawn.

2. Experiment 9 (Comprehensiveness comparison) adds substantial value. comp_c correctly reflects c-dependence on training distribution (p=0.0: 0.484) but cannot predict J_S collapse under reversed_c. This is a concrete, quantitative illustration of what the invariance axis adds.

3. The paper honestly reports negative/weak results: Hopper BC achieves only 4.5% of oracle performance, gravity conditions in Experiment 3 are not significant after correction, most model comparisons in Experiment 5 lack significance.

4. The title "Detecting Spurious Dependencies in Surrogate Explanations of RL Policies via Invariance Testing" is precisely scoped ("detecting," not "evaluating" or "eliminating").

### Weaknesses

1. **MAJOR: Scalability evidence remains insufficient.** The main experiments use CartPole (4D, 2 actions) and 5×5 GridWorld (3D, 4 actions). Contribution 3 claims "a tendency for the evaluation axes to function consistently across multiple RL environments." LunarLander (Experiment 7) is in an appendix and only GBT produces functional policies. Hopper (Experiment 8) fails Stage 1 fidelity for all BC surrogates (best AA_ε = 0.703, below 0.9); DAgger reaches J_S = 63% but AA_ε = 0.420 also fails Stage 1. The paper correctly notes "preliminary," but Contribution 3 in the Introduction does not sufficiently hedge.

2. **MAJOR: Hopper experiment's Stage 1 failure undermines claims about continuous spaces.** RegTree d=12 achieves R²=0.922 on training, but BC policy performance is 4.5% of oracle. DAgger's AA_ε = 0.420 on oracle states is not "high fidelity." The paper should be explicit: no interpretable surrogate achieves both high fidelity and functional policy performance in Hopper under the framework's criteria.

3. **MINOR: MoET selection rationale is circular for Experiment 2.** Section 7 states MoET was selected because Tree's reversed_c AA=0.887 falls below θ_AA=0.9. This means the primary model was chosen because it produces the result needed to demonstrate the framework. Transparent, but raises whether the diagnostic criteria are too narrowly tuned to MoET's behavior.

4. **MINOR: No real-world environment tested.** In real-world RL, spurious features are unknown a priori and distribution shifts are not cleanly controllable. A discussion of how the framework operates under these constraints would strengthen practical motivation.

### Actionable Revisions

- Soften Contribution 3: replace "demonstrating a tendency for the evaluation axes to function consistently across multiple RL environments" with "providing initial evidence that the two-axis evaluation logic applies beyond the primary experimental environments."
- Add to Limitations: in Hopper, no interpretable surrogate achieves both high fidelity and functional policy performance simultaneously under BC; DAgger's low AA_ε means Stage 1 is not satisfied in the standard sense.
- Add brief discussion of real-world applicability constraints.

---

## Reviewer C (Statistics / Rigor Expert)

### Strengths

1. Statistical methodology is above average: Welch's t-tests with Holm-Bonferroni correction, Cohen's d reported, 10 independent seeds with separate distillation/evaluation splits, honest reporting of non-significant results.

2. 95% CI is now reported for the key comparison. Experiment 2 reversed_c AA is "0.942 (95% CI: [0.902, 0.982])," directly addressing the relationship to θ_AA = 0.9.

3. Zero-variance J_S result is handled appropriately: "trivially obvious" and does not require statistical testing, with the t-test degeneracy noted.

4. Table 2 reports both all-seed and converged-seed statistics for Experiment 3, preventing cherry-picking concerns.

### Weaknesses

1. **MAJOR: The 95% CI lower bound for reversed_c AA barely exceeds the diagnostic threshold.** CI = [0.902, 0.982], threshold = 0.9. Lower bound exceeds threshold by only 0.002. The paper should explicitly acknowledge this near-boundary nature and discuss robustness. A one-sided or bootstrap CI might provide a more precise bound.

2. **MAJOR: No power analysis for the central comparison.** p_adj = 0.030 with n=10 is acknowledged as marginal, but no power analysis is provided. At n=10 and d=1.14, power for a two-sided t-test at α=0.05 is approximately 0.55--0.65, meaning a 35--45% chance of missing the effect. This should be stated.

3. **MINOR: mean ± SD vs. SE ambiguity.** The key comparison now reports 95% CI, but most results are still mean ± SD. A brief note at first use clarifying ± = SD (not SE) would prevent misinterpretation.

4. **MINOR: Multiple testing across experiments not addressed.** Holm-Bonferroni correction within each experiment, but no correction across experiments 2, 3, 4, 5, 7. Family-wise error rate not discussed. Standard practice but should be acknowledged.

5. **MINOR: Degenerate J_S t-test still referenced.** The paper notes J_S collapse is "trivially obvious," but p_adj < 0.001 for J_S is referenced elsewhere. The p-value should be omitted or explicitly labeled as degenerate where variance is zero.

### Actionable Revisions

- Add a sentence noting the near-boundary CI lower bound (0.902 vs. threshold 0.9) and its implications.
- Report approximate power for Experiment 2 AA comparison (n=10, d=1.14, α=0.05, power ≈ 0.55--0.65).
- Add a brief note clarifying ± represents SD, not SE.
- Omit or explicitly label as degenerate the J_S p-value where variance is zero.

---

## Cross-Reviewer Summary

### Consensus Findings

All three reviewers agree on:
- The paper addresses a real gap and the invariance axis adds genuine diagnostic value
- Experimental methodology is well above average for reproducibility and statistical transparency
- Experiment 2 vs. 3 contrastive design is effective and well-framed
- Comprehensiveness faithfulness comparison (Experiment 9) is a strong addition
- Title is now appropriately scoped
- Scalability evidence remains the weakest aspect

### Critical Issues Requiring Revision

| # | Issue | Severity | Reviewers |
|---|-------|----------|-----------|
| 1 | Framework cannot confirm absence of spurious dependencies; asymmetry not stated in abstract | MAJOR | A |
| 2 | Distribution shift selection unguided; SHAP heuristic buried in Limitations, not in framework | MAJOR | A |
| 3 | Contribution 3 scalability claims still overscoped relative to two toy environments | MAJOR | B |
| 4 | Hopper: no surrogate achieves both high fidelity + functional performance; "preliminary" framing too generous | MAJOR | B |
| 5 | CI lower bound for reversed_c AA barely exceeds θ_AA (0.902 vs 0.9); robustness not addressed | MAJOR | C |
| 6 | No power analysis for the central comparison (n=10, d=1.14, power ≈ 0.55--0.65) | MAJOR | C |

### What Passed This Round

- Title: 13 words, accurately scoped. ✓
- Figures: 5 figures referenced (Figures 1--5). ✓
- Citation distribution: citations appear in all sections. ✓
- Writing quality: flowing prose throughout; Section 5.1 numbered list and Section 4.3 bullet list are functionally appropriate. ✓
- Threshold sensitivity (Tables 6, 7): now in main text. ✓
- Experiment 2 "by construction" acknowledgment: properly framed. ✓
- Statistical methodology: Welch's t-test, Holm-Bonferroni, Cohen's d, n=10, independent splits. ✓

### Verdict

**REVISE.** Substantial improvement from the prior version: title correctly scoped, Experiment 2's by-construction nature acknowledged, threshold sensitivity in main text, 95% CI reported. The core contribution is sound and Experiment 9 concretely demonstrates the invariance axis's value. Six MAJOR issues remain: the framework's asymmetry (cannot confirm absence) is not stated in the abstract; shift selection is unguided; scalability claims still exceed evidence; Hopper framing is generous; CI lower bound barely exceeds the threshold; and no power analysis is provided. All are addressable in a revision cycle.
