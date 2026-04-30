# Peer Review: Detecting Spurious Features via Intervention-Based Performance Sensitivity

## Overall Verdict: Weak Reject / Borderline Major Revision

This version is materially stronger than the first round. The paper now has a clearer main claim, the Delta operator is better motivated, the GridWorld and ColoredMNIST results are numerically sharper, Waterbirds now has a real worst-group analysis, and the discussion is more careful about the difference between causal intervention and attribution.

That said, the paper is still not ready for a NeurIPS-style submission. The biggest remaining problems are: there are no figures embedded in the manuscript body, the Waterbirds comparison against a specialized spurious-detection baseline is still missing from the paper, and the main claims are still not fully supported with enough visual/statistical evidence in the text.

## Reviewer A: Methodology Expert

### Strengths
1. The paper now has a much clearer method than in the first round. The Delta definition is explicit, the intervention idea is operationalized, and the paper no longer relies on vague "we just measure spuriousness" language.
2. The topic focus is better. The manuscript is centered on intervention-based performance sensitivity rather than drifting into a general explanation of environment quirks.
3. The ablation and negative-result narrative is valuable. LunarLander is now framed more as a boundary case than as a core contribution, which is the right instinct.

### Weaknesses
1. The intervention operator is still underspecified for a methods paper. The paper says interventions can be random resampling, constant replacement, or masking, but it does not yet give a precise operational contract for when each operator is valid, what invariances it preserves, and when the operator itself becomes the bottleneck.
2. The manuscript still mixes top-5 ranking language and binary detection language. The paper needs one clean decision rule and one clean exposition path.
3. The main claim "Delta is an intervention-based proxy for operational necessity" is now defensible, but the paper still needs one more layer of methodological caution. It should be explicit that this is not a causal-identification result; it is a diagnostic score under a chosen intervention family.

### Actionable Revisions
1. Add a short formal subsection that states the admissibility conditions for each intervention family.
2. Make the evaluation rule completely uniform. If top-5 is the standard display, state whether the claim is "rank of the target feature among all features" or "binary success if target is in top-5," and use the same language everywhere.
3. Tighten the limitation sentence around causality. "Do-inspired intervention" is good; "causal dependence" should remain out of the main claim.

## Reviewer B: Domain Expert

### Strengths
1. The benchmark choice is now much more convincing. GridWorld, ColoredMNIST, and Waterbirds together make the paper feel like a cross-domain study rather than a single toy example.
2. Waterbirds now carries real weight. The worst-group result and the SHAP comparison are exactly the kind of real-data evidence the first round was missing.
3. The manuscript does a better job distinguishing post-hoc diagnosis from training-time robustness methods such as IRM and GroupDRO.

### Weaknesses
1. The largest remaining domain-level hole is the missing specialized baseline in the main paper. If the paper wants to argue that Delta is useful for spurious-feature detection, it should be compared against at least one method designed for that task, not only against a general-purpose attribution method like SHAP.
2. LunarLander still feels too much like a side story. The appendix discussion is acceptable, but in the current draft the negative result is still a potential distraction from the core vision.
3. The manuscript is still a little too broad in how it phrases the scope. The results support the method on the tested benchmarks; they do not yet justify broad claims about all spurious-feature detection settings.

### Actionable Revisions
1. Add one specialized baseline in the Waterbirds section, even if it is only one method, and make the comparison table explicit.
2. Compress LunarLander further and keep it in the appendix or a short limitations paragraph.
3. Rewrite the conclusion so it states where Delta works well, where SHAP fails, and what scope of spurious-feature detection the paper actually covers.

## Reviewer C: Statistics / Rigor Expert

### Strengths
1. The statistical reporting is much improved. Multiple seeds are used in the main experiments, Wilson confidence intervals and McNemar tests are already part of the workflow, and the paper no longer looks like a single-run pilot.
2. The results are more reproducible than before. The appendix now includes hyperparameters, compute resources, and dataset details, which is exactly the right direction.
3. The paper has better quantitative discipline now. The concrete counts in GridWorld, ColoredMNIST, and Waterbirds make the argument much easier to assess.

### Weaknesses
1. There are still no figures in the manuscript body. For a NeurIPS-style paper, that is a serious problem. The text alone is not enough to communicate the per-seed distributions, ranking behavior, or the Waterbirds separation.
2. The paper still needs to make sure that every headline claim in the abstract and conclusion points to an explicit result table or figure.
3. The statistical presentation is better, but not yet fully polished. The reader should not have to infer from prose that the method used 30 seeds, Wilson intervals, and paired tests.

### Actionable Revisions
1. Add at least two figures to the body. At minimum, one figure should show the Delta vs SHAP comparison with confidence intervals, and one should show the Waterbirds seed-level scatter or group-wise breakdown.
2. Put confidence intervals or error bars directly in the main results tables, not only in auxiliary files or discussion text.
3. Make the abstract and conclusion cite the exact table or figure where each quantitative claim is supported.

## Summary

The paper is now substantially closer to a real submission than in the first round. The conceptual line is clearer, the experimental coverage is broader, and the manuscript has much better evidence behind the Delta-vs-SHAP claim.

However, I would still not accept it in the current form. The two biggest blockers are:
1. no figures embedded in the main paper body,
2. no specialized spurious-detection baseline in the main Waterbirds comparison.

If those are fixed, along with a slightly tighter methods presentation, the paper would move from "interesting but incomplete" to something much more convincing.