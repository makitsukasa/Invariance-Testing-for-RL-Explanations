# Peer Review: Detecting Spurious Features via Intervention-Based Performance Sensitivity

## Overall Verdict: Borderline Major Revision

This draft is now substantially stronger than the earlier versions. The core idea is clear, the intervention-based perspective is consistent, the figures are embedded in the manuscript body, and the Waterbirds section now includes both a worst-group analysis and a specialized baseline comparison. The paper no longer feels like a collection of experiments; it has an identifiable argument.

The remaining issues are no longer about whether the paper has evidence at all. They are about how precisely the paper distinguishes candidate spuriousness from intervention-based necessity, how uniformly the statistics are presented, and how cleanly the specialized-baseline comparison is framed.

## Reviewer A: Methodology Expert

### Strengths
1. The method is now conceptually coherent. Delta is defined as an intervention-based performance drop, and the paper clearly separates this from post-hoc attribution.
2. The intervention story is much better motivated than before. The manuscript now repeatedly emphasizes that the operator should destroy the target feature while preserving the rest of the input as much as possible.
3. The paper has a stronger empirical spine. GridWorld, ColoredMNIST, Waterbirds, and the LunarLander boundary case together make the scope of the method easier to understand.

### Weaknesses
1. The admissibility conditions for interventions are still only partly formalized. The paper states the intuition well, but it would benefit from a sharper operational contract for when an intervention is considered valid and when its quality becomes a limiting factor.
2. The manuscript still mixes several related but not identical notions: candidate spuriousness, intervention-based necessity, and rank-based detection. These are all related, but the distinction should be stated more explicitly in one place.
3. The specialized baseline section is useful, but the paper should be careful not to overstate what the proxy scores mean. The baseline is a candidate-confirmation signal, not a direct measure of functional dependence.

### Actionable Revisions
1. Add a short formal subsection that states the admissibility conditions for the intervention family in one place.
2. Use one consistent phrasing for the detection rule: either rank-based success or top-k inclusion, but not both as if they were interchangeable.
3. In the Waterbirds specialized-baseline discussion, explicitly separate "candidate spuriousness" from "functional necessity" so the roles of Spec/PCA and Delta are unmistakable.

## Reviewer B: Domain Expert

### Strengths
1. The benchmark choice is now compelling. The paper no longer relies on a single toy setting; it spans synthetic, semi-synthetic, and real-image benchmarks.
2. Waterbirds is now doing real work in the paper. The worst-group analysis, the specialized baseline, and the intervention sensitivity result all reinforce the same story from different angles.
3. The negative-result framing around LunarLander is sensible. It is now clearly a boundary case rather than a distraction.

### Weaknesses
1. The specialized-baseline comparison is still slightly under-explained in domain terms. A reader who knows spurious-feature detection will understand that Spec/PCA are proxy scores, but the paper should state more clearly what kind of "spuriousness" they estimate and why that is the right comparator for Delta.
2. The Waterbirds discussion is strong, but the key disagreement cases deserve one more sentence of interpretation in the main text. Right now the reader can infer the meaning, but the paper would benefit from stating it directly.
3. The scope of the contribution is still a little broad in the conclusion. The paper should keep the claim focused on the tested benchmarks and on intervention-based diagnosis, rather than implying a general solution to spurious-feature detection.

### Actionable Revisions
1. Add one short paragraph in the Waterbirds results section explaining why the specialized baseline is a proxy for candidate spuriousness rather than a competing measure of the same quantity.
2. Add a sentence that interprets the discordant pairs in exp021 as evidence of a difference in measurement target, not just a mismatch in accuracy.
3. Keep the conclusion grounded in the tested benchmarks and avoid broad generalization beyond the evidence.

## Reviewer C: Statistics / Rigor Expert

### Strengths
1. The statistical reporting is much better than in the first draft. Multiple seeds are used, the manuscript now includes confidence intervals, and the Waterbirds comparison has a paired significance test.
2. The paper now has figures in the main body, which makes the results far easier to audit.
3. The manuscript is more reproducible. Hyperparameters, compute resources, and dataset details are all documented.

### Weaknesses
1. The statistical style is not yet fully uniform. Some parts of the paper emphasize counts, some emphasize percentages, and some explicitly show Wilson confidence intervals. That is better than before, but the presentation could be more consistent.
2. The exp021 specialized-baseline comparison is currently strong, but the figure caption and the discussion should match the same statistical language as the rest of the paper. The reader should not have to infer whether a proxy score is a detection rate, a ranking criterion, or an auxiliary statistic.
3. The paper still relies on prose in a few places where a compact table would improve clarity, especially for the representative disagreement cases in Waterbirds.

### Actionable Revisions
1. Keep the confidence-interval style consistent in the main results tables and captions.
2. Add one compact disagreement table for exp021 with a few representative seeds, and define the columns clearly.
3. Make the caption language match the body language: Delta is an intervention-based necessity diagnostic, while Spec/PCA are proxy scores for candidate spuriousness.

## Summary

The paper is now much closer to a convincing submission than it was in the first round. The method is clearer, the evidence is broader, and the Waterbirds section finally connects specialized baseline detection, intervention-based diagnosis, and worst-group performance in one coherent narrative.

What still prevents this from feeling fully polished is not a missing experiment, but a small amount of conceptual and statistical cleanup:

1. Make the intervention admissibility conditions explicit.
2. Standardize the detection language and statistical presentation.
3. State the role of the specialized baseline more crisply, especially in the disagreement cases.

If those are tightened, the paper would read as a well-motivated intervention-based diagnosis paper rather than as a collection of benchmark-specific observations.
