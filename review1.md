# Peer Review: Explainability Evaluation Framework for Reinforcement Learning Policies Based on Structural Constraint Bottlenecks

**対象**: draft_en.md（英語版・全文）  
**実施日**: 2026-04-20

---

## Reviewer A (Methodology Expert)

### Strengths

1. The decoupling design (Oracle fixed, Surrogate evaluated post-hoc) is clean and well-motivated. It correctly identifies that maximizing AA alone is insufficient for evaluating explanation quality.

2. The two-stage evaluation (fidelity then invariance) is a logically sound diagnostic framework. The experimental demonstration that high AA can coexist with complete performance collapse (Experiment 2, p=0.0 reversed_c: AA=0.942 yet J=-1.000) is the strongest empirical result.

3. Statistical methodology is above-average for the field: 10 seeds, Welch's t-tests with Holm-Bonferroni correction, explicit reporting of non-significant results (e.g., Experiment 3 gravity conditions). The paper does not cherry-pick.

4. The contrastive experimental design (Experiment 2 vs Experiment 3) is effective pedagogy and methodologically appropriate.

### Weaknesses

1. **MAJOR: The framework detects a problem but does not evaluate explanations.** The title says "Explainability Evaluation Framework" but the framework actually detects spurious dependency replication. There is no evaluation of explanation quality in any human-meaningful sense (no user studies, no ground-truth explanation comparison, no evaluation of whether the Surrogate's structure actually helps a practitioner understand the policy). The gap between "detecting that a Surrogate copied a spurious feature" and "evaluating explainability" is substantial. The Discussion acknowledges this partly (`"Detection of spurious dependencies becomes practically meaningful only when combined with subsequent remedial actions"`) but the title and abstract still overclaim.

2. **MAJOR: Circularity in Experiment 2.** The Spurious GridWorld is explicitly designed so that p=0.0 makes c a perfect predictor of the goal. Any reasonable learner will use c. Then the paper demonstrates that a Surrogate that copies this dependency fails when c is reversed. This is tautological by construction: the experiment demonstrates what the environment was designed to produce. The paper should acknowledge this more directly and explain why this demonstration is still useful (e.g., as a controlled validation that the diagnostic criteria work).

3. **MAJOR: Arbitrary threshold problem is underaddressed.** The thresholds theta_AA=0.9 and alpha=0.8 are acknowledged as empirical guidelines, but the paper does not provide sensitivity analysis results in the main text (only references Tables 6 and 7 which appear to be in appendices not shown). For a framework paper, the robustness of the diagnostic criteria to threshold choice is central, not supplementary.

4. **MINOR: Distribution shift selection is acknowledged as arbitrary but no heuristics are provided.** The paper says "what to shift" is a practical challenge and defers to future work. For a framework paper, at minimum a taxonomy of shift types (feature manipulation vs. physical parameter change vs. domain shift) with guidance on when each is appropriate would strengthen the contribution.

### Actionable Revisions

- Revise the title to reflect what the framework actually does: detection of spurious dependency replication, not evaluation of explainability in general. Consider: "Detecting Spurious Dependencies in Surrogate Explanations of RL Policies via Invariance Testing."
- Add explicit acknowledgment that Experiment 2's result is by construction, then argue why this controlled validation matters.
- Move threshold sensitivity analysis into the main text or at minimum summarize the key finding (qualitative conclusions unchanged).

---

## Reviewer B (Domain Expert -- XRL / Interpretable RL)

### Strengths

1. The positioning relative to prior work is comprehensive and honest. The paper correctly identifies that policy distillation work (Bastani et al., 2018; Vasic et al., 2019) treats AA maximization as the goal, and that SHAP/LIME reveal feature dependencies without evaluating their validity under shift.

2. The MoET tree visualization (Section 6.2) showing the root split on the spurious feature c is a compelling structural demonstration. The claim that this was reproduced across all 10 seeds is strong.

3. The paper avoids the common trap of claiming to solve the explainability problem. The Discussion explicitly states the framework is a diagnostic tool, not an explanation method.

4. The Comprehensiveness faithfulness comparison (Experiment 9) adds genuine value by concretely showing what the proposed invariance axis captures that within-distribution metrics miss.

### Weaknesses

1. **MAJOR: Scalability evidence is weak despite claims.** The paper's Contribution 3 claims the framework works "across multiple RL environments" but the main experiments use CartPole (4D state, 2 actions) and a custom 5x5 GridWorld (3D state, 4 actions). These are among the simplest RL benchmarks. LunarLander and Hopper are relegated to appendices with the caveat "full validation in continuous control remains future work." The claim of generality is not supported by the main-body evidence.

2. **MAJOR: The Hopper experiment (Experiment 8) does not support the framework's claims.** RegTree achieves R^2=0.922 on train but drops to R^2=-0.001 under gravity_hi and R^2=-0.124 under gravity_lo. These are not interpretable as "high fidelity" in any meaningful sense. The epsilon-agreement values on train (AA=0.703 at d=12) are also below the 0.9 threshold, meaning Stage 1 fidelity verification fails. When Stage 1 fails, Stage 2 invariance testing is not meaningful. The paper should be more explicit that the framework's applicability to continuous control is unvalidated rather than partially validated.

3. **MINOR: MoET is the primary Surrogate model but is not widely used.** The paper acknowledges that the framework is agnostic to model structure, but the experiments rely heavily on MoET. The model comparison experiments (4-5) show MoET and Tree produce nearly identical AA in GridWorld, raising the question of whether the MoET gating mechanism adds value over a simpler tree in these small environments.

4. **MINOR: No comparison with IRM or concept bottleneck baselines.** The related work extensively discusses IRM and concept bottleneck models, but there is no experimental comparison. Even a simple baseline (retrain the oracle with IRM penalty, then distill) would contextualize the framework's practical value.

### Actionable Revisions

- Downscope Contribution 3. Replace "tendency for the evaluation axes to function consistently across multiple RL environments" with a more honest claim about the two toy environments in the main text.
- Be explicit in Section 5.5 that the Hopper experiment fails Stage 1 fidelity for all Surrogate models tested (best R^2=0.922, best epsilon-agreement=0.703), making Stage 2 invariance diagnosis inapplicable under the paper's own criteria.
- Add at minimum a qualitative discussion of how the framework would need to be adapted for high-dimensional observations (images, point clouds).

---

## Reviewer C (Statistics / Rigor Expert)

### Strengths

1. The statistical reporting is methodologically sound. All main comparisons use Welch's t-test (appropriate given potential variance heterogeneity across conditions) with Holm-Bonferroni correction for multiple comparisons. Effect sizes (Cohen's d) are reported alongside p-values.

2. The paper explicitly reports non-significant results and does not spin them. For example, Experiment 3 gravity_lo and gravity_hi AA declines are correctly reported as non-significant after correction, and Experiment 4 most N>0 comparisons are non-significant.

3. The use of 10 seeds with independent distillation/evaluation splits is appropriate for the environments tested.

4. Confidence intervals (reported as mean +/- SD) are provided for all key metrics. The paper correctly notes high variance in DQN (2 of 10 seeds failing to converge) and reports both all-seed and converged-seed statistics.

### Weaknesses

1. **MAJOR: The central claim rests on a single significant comparison with marginal p-value.** The core claim (Experiment 2, "high AA but wrong explanation") is supported by p_adj=0.030 for the AA comparison (train vs reversed_c). While statistically significant, this is close to the 0.05 threshold, and with n=10, power is limited. The J_S comparison (p_adj<0.001, d>1000) is overwhelming, but the AA comparison -- which is the one that matters for the "high AA" claim -- has d=1.14, a medium-to-large effect. The paper should report a power analysis or at minimum acknowledge the marginal nature of this result.

2. **MAJOR: Reporting mean +/- SD rather than mean +/- SE or 95% CI is misleading for inference.** The paper reports AA=0.942+/-0.056 for reversed_c, but this is standard deviation, not standard error. For n=10, SE=0.018, so the 95% CI would be approximately [0.902, 0.982]. This is relevant because the diagnostic threshold is 0.9: the lower bound of the CI barely exceeds it, meaning under some reasonable samples, the "high AA" condition would not hold.

3. **MINOR: The non-parametric nature of the data is not addressed.** AA is bounded in [0,1], and J_S values cluster at -1.000 for the collapse condition (zero variance). Welch's t-test assumes approximate normality. For the J_S comparison where all 10 values are exactly -1.000 (variance=0), the t-test is degenerate (d>1000 is an artifact of zero-variance denominator). A non-parametric test (Mann-Whitney U) would be more appropriate for this specific comparison.

4. **MINOR: Multiple testing correction is applied within each experiment but not across experiments.** The paper tests multiple hypotheses across Experiments 2, 3, 4, 5, and 7. Family-wise error rate control within each experiment is appropriate, but there is no discussion of how the overall false positive rate is managed across the full study.

### Actionable Revisions

- Report 95% confidence intervals for the key comparisons (at minimum Experiment 2 train vs reversed_c AA, and the diagnostic threshold evaluation).
- Add a sentence acknowledging that the AA significance in Experiment 2 is marginal (p=0.030) and interpret accordingly.
- For the J_S comparison where variance is zero, either use a non-parametric test or note that the t-test is degenerate and the result is trivially obvious (all values identical).

---

## Cross-Reviewer Summary

### Consensus Findings

All three reviewers agree on:
- The paper addresses a real gap (AA alone is insufficient for evaluating surrogate explanations)
- The experimental methodology is above average for reproducibility (10 seeds, independent splits, statistical tests)
- The main empirical demonstration (Experiment 2) is convincing in showing the phenomenon exists
- The scalability evidence is insufficient to support generality claims
- The title overclaims relative to what the framework actually delivers

### Critical Issues Requiring Revision

| # | Issue | Severity | Reviewers |
|---|-------|----------|-----------|
| 1 | Title/framing overclaims "explainability evaluation" when the framework detects spurious dependency replication | MAJOR | A, B |
| 2 | Scalability/generality claims unsupported by main-body evidence (toy envs only) | MAJOR | B |
| 3 | Hopper experiment fails the framework's own Stage 1 criteria; should not be cited as validation | MAJOR | B |
| 4 | Central AA significance is marginal (p=0.030, n=10); CI analysis needed | MAJOR | C |
| 5 | Experiment 2 is tautological by design (acknowledged but insufficiently) | MAJOR | A |
| 6 | Threshold sensitivity analysis absent from main text | MAJOR | A |

### Missing Elements

- No user study or human evaluation of explanation quality
- No comparison with IRM or concept bottleneck baselines
- No power analysis
- No guidance on distribution shift selection beyond "it's hard"
- Bullet-point lists appear in Section 4.3 (metric definitions) and Section 5.1 (experimental objectives numbered list). While the Section 5.1 list is functional, the Section 4.3 bullet list should be converted to prose for a NeurIPS submission.
- Word count of the main body appears to be in the 5,000-6,000 range based on section lengths, which is within NeurIPS limits.
- Four figures are referenced and verified to exist (Figures 1-4). This exceeds the minimum of 2.
- Citations are distributed across Intro, Related Work, Method, Experiments, and Discussion. No section is citation-free.

### Verdict

**REVISE.** The core idea is sound and the experiments are competently executed, but the framing significantly overclaims. The paper presents a diagnostic tool for detecting spurious dependency replication in surrogate models and frames it as a general "explainability evaluation framework." Tightening the claims to match the evidence, moving threshold sensitivity into the main text, adding CI-based statistical reporting, and being honest about the Hopper experiment's failure under the framework's own criteria would bring this to an acceptable standard. The experimental infrastructure is solid; the problem is positioning, not execution.
