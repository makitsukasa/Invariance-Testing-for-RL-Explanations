# Peer Review Simulation 7: PerformanceCheck - Detecting Spurious Features

## Reviewer D (Methodology Expert)
**Overall Assessment:** The paper presents a highly mature framework. The formalization of "PerformanceCheck" and its framing within do-calculus provides a solid foundation for post-hoc auditing.

**Strengths:**
- Clear formulation of PerformanceCheck.
- Sound use of do-calculus for operationalizing feature dependency.

**Weaknesses:**
- **Faithfulness Metrics:** There is limited discussion on how to measure the "faithfulness" of the interventions themselves. How can an auditor be sure a mask-based replacement isn't introducing its own artifacts?
- **Feature Interactions:** The current methodology focuses on individual feature interventions. The potential for multi-feature interaction analysis is not addressed.

**Actionable Revisions:**
1. **Faithfulness Discussion:** Add a paragraph in Method or Limitations discussing how one might validate intervention quality (e.g., via visual inspection or secondary proxies).
2. **Interaction Note:** Briefly mention the extension to multi-feature sensitivity in Future Work.

---

## Reviewer E (Domain Expert)
**Overall Assessment:** The paper's insight into SHAP artifacts in ColoredMNIST is a significant contribution to the domain. The pipeline evaluation using CLIP/SSL discovery makes the work highly relevant to current computer vision practices.

**Strengths:**
- Excellent analysis of structural artifacts in attribution methods.
- Realistic pipeline evaluation using modern CLIP/SSL discovery proxies.

**Weaknesses:**
- **Replacement Trade-offs:** The trade-offs of class-consistent background replacement are not fully detailed. Does this strategy risk masking certain types of spurious dependencies that are class-agnostic?
- **Mask Visualization:** While mask sensitivity is quantified, visual examples of "tight" vs "loose" masks would help ground the results for practitioners.

**Actionable Revisions:**
1. **Replacement Strategy:** Clarify the rationale for class-consistent replacement and discuss potential class-agnostic bias cases.
2. **Visual Examples:** Add a figure showing example mask perturbations (-3px vs +3px) in the Appendix.

---

## Reviewer F (Statistics/Rigor Expert)
**Overall Assessment:** The paper is exemplary in its use of 30 seeds, Wilson CIs, and McNemar tests. The reproducibility appendix is highly detailed. However, a critical numerical discrepancy exists.

**Strengths:**
- Exceptional statistical reporting and uncertainty quantification.
- Detailed reproducibility documentation.

**Weaknesses:**
- **Numerical Discrepancy:** The Results section claims a detection rate of 106/120 (88%) for GridWorld top-2, but the provided 95% CI [0.77, 0.90] matches the actual count of 101/120 (84%) from the experiment logs. This typo undermines the precision of the paper.

**Actionable Revisions:**
1. **Numerical Audit:** Re-verify and synchronize every single count and percentage in the Tables and Prose against the raw `stats.txt` outputs.
2. **Standard Deviations:** Add standard deviations where appropriate for point estimates in the Discovery Results.
