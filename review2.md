# Peer Review 4: PerformanceCheck - Detecting Spurious Features

## Overall Verdict: Weak Accept / Accept

The manuscript has reached a high level of technical maturity. The introduction of the "PerformanceCheck" branding, the systematic inclusion of Wilson Confidence Intervals, and the sophisticated analysis of discordant pairs significantly elevate the work. The paper now moves beyond a simple empirical report to a structured diagnostic framework.

---

## Reviewer D: Methodology Expert
**Score: 7/10 (Weak Accept)**

**Strengths:**
- The **PerformanceCheck** branding provides a clear identity and aligns well with the "functional necessity" logic.
- The formalization of Admissibility (Conditions a and b) is excellent and addresses previous concerns about OOD artifacts.

**Weaknesses:**
- **Mathematical Coupling:** While the admissibility conditions are defined, the transition from "ideal I=0" to "practical class-consistent replacement" could be more explicit in the Method section.
- **Robustness Evidence:** The claim of stability against mask perturbation (exp020) is currently limited to a single seed. (Note: exp022 is expected to address this).

**Actionable Revisions:**
- [ ] **Bridge the Gap:** Add a sentence in Method explicitly linking the `class-consistent` replacement in exp021 to the satisfaction of the "Peripheral Distribution Preservation" (Condition b).
- [ ] **Finalize Robustness:** Once exp022 results are in, replace the single-seed claim with the 30-seed aggregate stability score.

---

## Reviewer E: Domain Expert
**Score: 8/10 (Accept)**

**Strengths:**
- The **Discordant Pairs analysis** (12 seeds in Waterbirds) is the "gold mine" of this paper. It provides clear evidence that PerformanceCheck can identify cases where a model has achieved functional invariance despite the presence of spurious signals in the representation space.
- The **Human-in-the-loop Remediation workflow** provides the "So What?" that was missing. It frames the tool as a practical guide for engineers.

**Weaknesses:**
- **Boldness of Claims:** The paper could be even bolder in framing these discordant pairs. Instead of saying "Delta is more conservative," say "PerformanceCheck identifies functional robustness that attribution methods hallucinate as vulnerabilities."

**Actionable Revisions:**
- [ ] **Refine the "Hallucination" Logic:** In the Discussion, use the term "attribution hallucination" to describe cases where SHAP/SpecScore flag dependencies that don't actually harm performance.
- [ ] **Remediation Detail:** Briefly specify which augmentation (e.g., Mixup, CutMix) would be prioritized for a high-PerformanceCheck-score feature.

---

## Reviewer F: Statistics & Rigor Expert
**Score: 7/10 (Weak Accept)**

**Strengths:**
- Statistical reporting (Wilson CI, McNemar) is now exemplary and follows the highest standards.
- Positioning figures near relevant text has dramatically improved the narrative flow.

**Weaknesses:**
- **Anti-Repetition Rule:** There are still instances where the exact values from Table 1 are repeated in the prose of the Results section.
- **Caption Self-Containment:** Captions (especially Figure 7) should explicitly state the takeaway: "Note that PerformanceCheck scores remain low for seeds 15-17, correctly identifying background invariance."

**Actionable Revisions:**
- [ ] **Audit Exact Numbers:** Replace redundant inline numbers with qualitative descriptions (e.g., "approximately two-thirds" instead of "0.667").
- [ ] **Analytical Captions:** Expand all captions to include a "Key Takeaway" sentence.
