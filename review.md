# Reviewer A (Methodology Expert)

## Strengths
- The paper now has a clear core idea: PerformanceCheck measures intervention-based performance sensitivity rather than output-distribution attribution.
- The distinction between candidate spuriousness proxies (e.g., SHAP / PCA-style baselines) and intervention-based necessity is conceptually strong and easy to motivate.
- The experimental design is broad enough to show the method under several regimes: a synthetic setting (GridWorld), a coded benchmark (ColoredMNIST), and a real-world benchmark (Waterbirds).
- The inclusion of exp021 makes the disagreement between proxy-style methods and PerformanceCheck concrete instead of merely philosophical.

## Weaknesses
- The admissibility conditions for interventions are still not fully pinned down. The paper says the intervention should destroy the target feature while preserving other features as much as possible, but it does not yet make the boundary between a valid intervention and an overly destructive OOD corruption fully operational.
- The method still relies on several intervention families with different assumptions (feature replacement, mask perturbation, background swap, foreground noise). This is reasonable, but the paper should explain more clearly when these families are comparable and when they are not.
- The human-in-the-loop remediation story is promising, but the paper is still stronger at showing confirmation than at showing a fully specified repair protocol.

## Actionable Revisions
1. Add a short admissibility subsection that distinguishes "target-feature corruption" from "generic OOD corruption" and says what counts as an acceptable approximation in practice.
2. Add one explicit negative-control example or short ablation showing that simply breaking the input in a destructive way does not produce the same signal as a targeted intervention.
3. Make the boundary between "PerformanceCheck as a confirmation module" and "PerformanceCheck as a repair-prioritization module" explicit in the Discussion.
4. Keep the title and main framing focused on intervention-based sensitivity; the current title is concise and within the length limit, so no change is needed there.

# Reviewer B (Domain Expert)

## Strengths
- The paper is well aligned with the spurious-feature diagnosis problem in practical ML workflows.
- The narrative now makes a useful distinction between discovering candidate spurious features and confirming whether the model actually depends on them.
- Waterbirds, ColoredMNIST, and GridWorld are complementary enough to show that the method is not tied to a single benchmark style.
- The exp021 specialized-baseline comparison is especially helpful because it makes the proxy-vs-necessity distinction visible in a real benchmark.

## Weaknesses
- The paper is still slightly ambiguous about whether it is primarily a detector, a confirmer, or a repair-prioritization tool. In practice it is the latter two, but the prose should say that more directly.
- The remediation story in Discussion is now present, but it still reads more like a proposal than a concrete practitioner workflow.
- For domain readers, it would help to see one explicit example of how a practitioner would use the top-k output to decide on augmentation, relabeling, or retraining priorities.

## Actionable Revisions
1. Add a concise paragraph in Discussion that says: candidate discovery first, PerformanceCheck confirmation second, remediation prioritization third.
2. Give one concrete example of how a top-k candidate list would change an augmentation or retraining decision.
3. Be careful not to oversell the exp021 disagreement as "the baseline was wrong"; the cleaner interpretation is that the baseline answers a different question than PerformanceCheck.
4. The paper now has enough benchmark coverage to support the domain story, so the main improvement needed is explanation, not more datasets.

# Reviewer C (Statistics / Rigor Expert)

## Strengths
- The use of 30 seeds in the main Waterbirds and GridWorld/ColoredMNIST runs is a major improvement over a single-seed story.
- Wilson confidence intervals and McNemar testing make the statistical claims substantially more credible.
- The paper now has multiple views of the same phenomenon: tables, scatter plots, distribution plots, and baseline-comparison figures.

## Weaknesses
- The writing still mixes exact counts, percentages, and qualitative statements in a way that is not fully standardized across sections.
- There are still places where the text repeats the same number in prose and in a table, which makes the Results read heavier than necessary.
- Some sections in Method / Results / Discussion still lean on list-like formatting. The workflow list in Discussion is helpful, but it reads more like notes than polished prose.
- A few figure insertions appear duplicated or stacked in a way that feels like leftover editing rather than a final camera-ready layout.

## Actionable Revisions
1. Standardize the reporting format in the main text to something like `k/n (%, 95% CI)` and keep repeated exact numbers mostly in tables.
2. Remove any duplicate figure insertions and ensure each figure appears once, immediately after the paragraph that discusses it.
3. Convert list-like paragraphs in Discussion into prose where possible, or move them to an appendix if they are meant to be procedural notes.
4. Keep the statistical story consistent: counts, percentages, confidence intervals, and exact p-values should appear in a fixed pattern across all main results.

## Overall Assessment
This is a solid and increasingly coherent paper. The methodological core is good, the benchmark coverage is broad enough, and the statistics are now much more serious than in the earlier draft. The main remaining work is not adding more benchmarks, but tightening the paper's logical boundaries: what counts as a valid intervention, how the remediation workflow should be read, and how the numerical results are presented so the reader can follow the story without tripping over formatting noise.
