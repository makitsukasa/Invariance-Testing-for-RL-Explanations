## Reviewer A (methodology expert)

### Strengths
- The paper is well aligned with the stated topic: it focuses on detecting spurious features via intervention-based performance sensitivity, and the central object `Δ_i = P(f,D) - P(f,T_i(D))` is clearly defined.
- The main methodological contribution is appropriately scoped. The draft is careful that PerformanceCheck is a confirmation step for already-proposed candidates rather than a full candidate discovery system.
- The paper compares the proposed confirmation signal against a meaningful baseline family (SHAP) across synthetic and semi-real settings, and the qualitative distinctions between “candidate existence” and “functional necessity” are potentially interesting.
- The manuscript includes substantially more than the minimum figure count; the results section is visually supported.

### Weaknesses
- The biggest methodological problem is incomplete claim-evidence alignment for the title/abstract/conclusion. The title promises “detecting spurious features,” but much of the evidence is actually about ranking a known candidate above alternatives after hand-designed interventions. That is weaker than general “detection.”
- Several strong claims in the abstract and conclusion are only partially supported by the presented evidence:
  - “PerformanceCheck … quantifies dependence … from local interventions and performance change only”: this is supported mechanistically by the method section, but not validated beyond a narrow set of intervention designs.
  - “Useful diagnostic information distinct from attribution methods”: supported for GridWorld and partly for ColoredMNIST, but Waterbirds shows SHAP at 30/30 vs PerformanceCheck at 18/30, so the paper must state more clearly that the advantage is task-dependent and tied to the authors’ notion of functional necessity.
  - “Candidate discovery and confirmation are connectable”: supported only by separate proxy experiments, not by a unified end-to-end pipeline.
- Topic drift appears in two places:
  - The LunarLander appendix is acceptable as a negative result, but the environment/training collapse discussion risks reading like an RL troubleshooting report rather than evidence about spurious-feature confirmation.
  - Some Waterbirds discussion expands into system-building language (“semi-automatic flow,” “three-stage workflow”) that is not fully demonstrated experimentally.
- The intervention validity story remains too informal. The paper acknowledges that good interventions should destroy the target feature while preserving others, but this is not operationalized with quantitative fidelity checks.
- Completeness is a major issue for venue fit: the body is only about 2,252 words, far below the stated NeurIPS-style target of 5,000-6,500 words.

### Actionable revisions
- Narrow the core claim everywhere from “detecting spurious features” to “confirming whether a proposed candidate is functionally necessary for performance under targeted intervention,” unless you add true candidate-discovery evaluation.
- Add an explicit threat-to-validity subsection for interventions with quantitative checks of intervention faithfulness and off-target damage.
- Reframe Waterbirds more carefully: SHAP is better at consistently flagging the background candidate, while PerformanceCheck is more conservative about functional dependence under the chosen interventions.
- Either remove most of the workflow/system language or add an actual end-to-end experiment from candidate proposal to confirmation.
- Expand the paper substantially; at present it reads like an extended workshop paper, not a full conference submission.

## Reviewer B (domain expert)

### Strengths
- The paper addresses an important and timely robustness question: distinguishing suspicious correlates from features whose removal actually harms performance.
- The dataset choices are sensible for the paper’s narrative: GridWorld for controlled analysis, ColoredMNIST for canonical spurious-correlation structure, and Waterbirds for a realistic vision benchmark.
- The ColoredMNIST section’s critique of the chosen SHAP aggregation rule is interesting and, if tightened, could be a useful cautionary note for the community.
- The discussion recognizes an important distinction between attribution-style explanations and intervention-based validation.

### Weaknesses
- Claim-evidence alignment is uneven in the front matter. The abstract foregrounds strong numerical takeaways, but does not foreground the central caveat that the proposed method underperforms SHAP on the coarse Waterbirds candidate-identification task as currently defined.
- The paper’s notion of “success” changes across domains:
  - GridWorld/ColoredMNIST use known-feature ranking over small candidate sets.
  - Waterbirds collapses to a background-vs-foreground comparison.
  This makes cross-domain comparisons feel less unified than the prose suggests.
- The Waterbirds narrative is still somewhat ambiguous scientifically. If SHAP picks background in 30/30 seeds and PerformanceCheck only in 18/30, readers may reasonably conclude the proposed method is less effective for practical spurious-feature detection unless the task is explicitly redefined as confirming functional necessity rather than identifying suspicious candidates.
- The manuscript does stay broadly on topic, but the appendicial LunarLander material is weakly connected to the main vision-centric story and could distract reviewers.
- Reproducibility is decent but not yet complete enough for a strong empirical paper. Some dataset construction details and selection decisions are present, but the paper still lacks the feel of a fully pinned-down benchmark protocol.

### Actionable revisions
- Rewrite the abstract and conclusion so the Waterbirds result is framed as a tradeoff, not an unqualified success.
- Make the task definition identical across sections: candidate proposal, candidate confirmation, and final decision criterion should be disentangled explicitly.
- Add a concise benchmark table summarizing, for each dataset, what counts as ground truth, what the candidate set is, what metric is used, and what a “correct detection” means.
- Shorten or move LunarLander further out of the main story unless you can connect it directly to the paper’s claimed contribution.
- Add a direct discussion of when practitioners should prefer SHAP-like candidate flagging versus PerformanceCheck-style confirmation.

## Reviewer C (statistics/rigor expert)

### Strengths
- The paper does use multiple seeds (`n=30`) for the main experiments, which is much stronger than a single-run empirical submission.
- Confidence intervals are reported in several result tables, and paired McNemar tests are used for some binary comparison claims, which is directionally appropriate.
- The draft includes useful reproducibility details: seed range, hyperparameters, software stack, and approximate compute cost.

### Weaknesses
- Statistical reporting is inconsistent across the manuscript. Some claims in the abstract and conclusion are given as point estimates only, without uncertainty.
- The confidence-interval presentation is sometimes unclear. For example, the GrabCut sensitivity summary uses asymmetric notation that is hard to parse and appears formatted inconsistently.
- The paper does not fully justify why the chosen inferential procedures are sufficient for all key claims. McNemar is appropriate for paired binary outcomes, but many broader claims are about effect magnitude, robustness across settings, and interpretation of delta gaps.
- There is no explicit multiple-comparisons discussion despite many comparisons across datasets, `p` values, `k` values, radii, and discovery proxies.
- The paper’s completeness remains below bar for a full conference paper. The short length amplifies concerns that statistical and experimental caveats are not fully developed.
- Reproducibility is good but not complete:
  - Code is “to be released,” not released.
  - Compute resources are specified at a coarse level only.
  - Some intervention-design choices remain heuristic rather than fully parameterized and justified.

### Actionable revisions
- Add uncertainty to every headline result in the abstract and conclusion.
- Standardize statistical reporting: one table should list all main estimates, uncertainty intervals, sample sizes, and the exact hypothesis test used.
- Report effect sizes, not only binary win/loss counts and `p` values.
- Add a brief statement on multiplicity or clearly label which tests are confirmatory versus exploratory.
- Clarify CI construction everywhere and fix the ambiguous interval formatting in the sensitivity summaries.
- Release code or, at minimum, provide exact commands/config hashes for all headline experiments before submission.

## Overall assessment
This is a thoughtful and potentially useful paper, especially in its insistence on separating candidate suspicion from intervention-based confirmation. The strongest positive is conceptual: “does the model highlight this feature?” is not the same question as “does breaking this feature actually reduce performance?” The main concerns are overclaiming relative to the evidence, incomplete methodological validation of the interventions, uneven framing of the Waterbirds results, and major under-length/incompleteness for a full NeurIPS-style paper. As written, the work feels closer to a promising workshop paper or a strong ablation note than a fully developed conference submission.
