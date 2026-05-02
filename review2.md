# Peer Review Simulation 6: PerformanceCheck - Detecting Spurious Features

## Reviewer D (Methodology Expert)
**Overall Assessment:** The paper presents a well-motivated framework, "PerformanceCheck," which distinguishes between the discovery of spurious feature candidates and the confirmation of their functional necessity. The formalization is solid, but the connection between the "Discovery" phase and the main "PerformanceCheck" results remains numerically thin in the manuscript body.

**Strengths:**
- Clear formalization of PerformanceCheck as a post-hoc intervention.
- Rigorous distinction between discovery and confirmation phases.

**Weaknesses:**
- **Numerical Connectivity Gap:** While the draft mentions the potential for pipeline integration, the specific numerical results from the discovery-phase experiments (exp024/exp025) are not present in the Results section.
- **Vague Alignment Data:** The text claims success in connecting discovery to confirmation but doesn't report the specific 80% to 30% alignment drop observed in the logs.

**Actionable Revisions:**
1. **Discovery Statistics:** Integrate the exact probe performance (e.g., 80-100% vs 20-40% in exp024) into a new Results subsection.
2. **Alignment Numbers:** Explicitly state the 80% to 30% alignment success rates across mask radii from exp025.

---

## Reviewer E (Domain Expert)
**Overall Assessment:** High relevance to AI safety and shortcut learning. The use of real-world-style Waterbirds and the inclusion of CLIP/SSL based discovery significantly modernize the work.

**Strengths:**
- Excellent use of real-world-style Waterbirds benchmark.
- Modernized approach using CLIP/SSL discovery.

**Weaknesses:**
- **Superficial Interpretation:** The difference between CLIP (100% alignment for background) and SSL (0% alignment) is noted but not deeply explained. This is a crucial insight for the "Discovery" domain.
- **Mask-Dependency Caveats:** The limitation of mask-based interventions for non-spatial features needs more prominent discussion.

**Actionable Revisions:**
1. **Semantic Analysis:** Expand the Discussion on *why* CLIP's semantic text-image alignment makes it more suitable for background-spurious discovery compared to DINOv2.
2. **Localization Discussion:** Address the hurdles of applying this framework to non-localized features (e.g., in medical or tabular domains).

---

## Reviewer F (Statistics/Rigor Expert)
**Overall Assessment:** Statistical reporting is generally strong, particularly the use of Wilson CIs and McNemar tests. However, some connectivity claims lack the same level of statistical grounding as the core Δ results.

**Strengths:**
- Strong reporting with n=30 seeds and 95% CIs.
- Appropriate use of McNemar tests for paired comparisons.

**Weaknesses:**
- **Claim-Evidence Mismatch:** The manuscript claims high connectivity success but hasn't updated the primary tables or prose to include the discovery-confirmation alignment stats.
- **Metric Inconsistency:** Some point estimates lack associated standard deviations or range indicators in the new discovery results.

**Actionable Revisions:**
1. **Connectivity Table:** Add a small table or prose section summarizing the alignment percentages between discovery proxies and PerformanceCheck across the 30 seeds.
2. **Statistical Consistency:** Ensure all new discovery numbers (top-1 recall, alignment %) include CI or standard deviations.
