# Peer Review Simulation 5: PerformanceCheck - Detecting Spurious Features

## Reviewer D (Methodology Expert)
**Overall Assessment:** The paper presents a well-motivated framework, "PerformanceCheck," which distinguishes between the discovery of spurious feature candidates and the confirmation of their functional necessity. The formalization using intervention-based performance sensitivity ($\Delta$) is a solid step toward operationalizing model auditing.

**Strengths:**
- **Clear Pipeline:** Effectively separates the "discovery" (existing methods) from "confirmation" (proposed method), addressing a common ambiguity in XAI literature.
- **Interventionist Logic:** Grounding the method in do-calculus concepts rather than just gradient-based attribution is a significant methodological strength.
- **Cross-Domain Evaluation:** Testing across RL (GridWorld), synthetic CV (ColoredMNIST), and real-world CV (Waterbirds) demonstrates the framework's versatility.

**Weaknesses:**
- **Manual Intervention Design:** The methodology relies heavily on manually designed intervention operators (e.g., GrabCut for Waterbirds, per-dimension sampling for GridWorld). The lack of a generalized approach for complex, non-localized features is a significant limitation.
- **Claim-Evidence Inconsistency:** There is a jarring discrepancy in the Waterbirds section. The text claims a functional necessity in "all 30 seeds" with a p-value of $1.86 \times 10^{-9}$, while the results table and prompt evidence show a detection rate of 18/30 (60%).

**Actionable Revisions:**
1. **Consistency Audit:** Harmonize the Waterbirds claims. Either explain why the sign test uses all 30 seeds while the detection rate is 18/30, or correct the text to reflect the 18/30 (60%) reality.
2. **Generalized Intervention:** Add a discussion or a small pilot on how one might automate the intervention design using generative models or automated segmentation to reduce the reliance on domain-specific heuristics.
3. **Pipeline Integration:** Provide more detail on how a specific discovery method (e.g., Domino or SpRAy) would pass its output to PerformanceCheck in a unified workflow.

---

## Reviewer E (Domain Expert)
**Overall Assessment:** The paper addresses the critical issue of shortcut learning in deep learning. The choice of benchmarks is appropriate, and the analysis of the "structural artifact" in ColoredMNIST is particularly insightful for the domain.

**Strengths:**
- **Benchmark Relevance:** Waterbirds and ColoredMNIST are standard in the spurious correlation community, making the results easy to contextualize.
- **Negative Case Analysis:** Including the LunarLander failure/boundary case is excellent for demonstrating the limitations of the "functional necessity" assumption.
- **Practical Workflow:** The discussion on ranking top-$k$ candidates for human auditing is highly relevant to real-world model deployment scenarios.

**Weaknesses:**
- **Writing Style:** The paper relies heavily on bullet-pointed lists (specifically in the Introduction, Method, Results, and Limitations). This disrupts the flow of the argument and feels more like a technical report than a formal research paper.
- **Real-World Complexity:** While Waterbirds is "real-world-ish," the intervention relies on pixel-perfect masks. In many domains (e.g., healthcare), features aren't spatially localized, which is a major hurdle for this method.

**Actionable Revisions:**
1. **Prose Refinement:** Convert the bulleted contributions and limitations into flowing paragraphs. A senior-level paper should demonstrate more narrative cohesion.
2. **Robustness Discussion:** Elaborate on the "Mask Sensitivity" section. If GrabCut fails partially, how does that affect the auditor's conclusion in a non-toy setting?
3. **Aesthetics:** The figure captions are overly long and descriptive (e.g., "This figure shows that..."). Move the interpretation to the main text and keep captions for identifying the content.

---

## Reviewer F (Statistics/Rigor Expert)
**Overall Assessment:** The paper follows good practices by using multiple seeds (n=30) and reporting confidence intervals. However, the statistical reporting in the Waterbirds section contains errors that undermine the paper's rigor.

**Strengths:**
- **Sample Size:** $n=30$ is a standard and robust choice for these types of benchmarks.
- **Uncertainty Quantification:** The inclusion of Wilson CIs for detection rates is a significant positive for reproducibility and comparison.
- **Significance Testing:** Use of McNemar tests for paired comparisons between $\Delta$ and SHAP is appropriate.

**Weaknesses:**
- **Hallucinated Statistics:** The Waterbirds sign test p-value ($1.86 \times 10^{-9}$) is mathematically impossible for an 18/30 detection rate. This p-value corresponds to 30/30 successes. The text explicitly claims "all 30 seeds were positive," which directly contradicts the 18/30 data in the table.
- **Inaccurate Discordant Pairs Table:** The table listing seeds 15, 16, and 17 as "NG" (PerformanceCheck) for the specialized baseline comparison is factually incorrect based on the provided results.csv, where those seeds are labeled as "True" (OK).
- **Reproducibility Detail:** While hyperparameters are listed, the specific compute resource details (CPU model) are helpful, but the lack of a "random seed" range (e.g., 0-29 or specific values) makes exact reproduction slightly harder.

**Actionable Revisions:**
1. **Critical Data Audit:** Recalculate the Waterbirds p-value based on the actual 18/30 count and remove the "all 30 seeds" claim.
2. **Fix Discordant Table:** Update the table in the Results section to use the actual discordant seeds (e.g., Seed 1, 3, 5) where PerformanceCheck failed but the baseline succeeded.
3. **Hyperparameter Check:** Ensure all numbers in the tables match the values in the figures and summary logs exactly. Currently, there are rounding discrepancies (e.g., 0.100 vs 0.103125).

---

### Verification Summary against Checklist:
1. **TOPIC ALIGNMENT:** PASS. The paper stays focused on intervention-based detection.
2. **CLAIM-EVIDENCE ALIGNMENT:** **FAIL**. Major contradiction in Waterbirds (all 30 vs 18/30) and discordant seed table.
3. **STATISTICAL VALIDITY:** PASS (Methodologically), but **FAIL** (Implementation/Reporting accuracy).
4. **COMPLETENESS:** PASS. All sections are present and deep.
5. **REPRODUCIBILITY:** PASS. Detailed hyperparameters and resources provided.
6. **WRITING QUALITY:** **FLAGGED**. Excessive bullet points in main sections (Intro, Method, Results, Limitations).
7. **FIGURES:** PASS. 7 figures mentioned.
8. **CITATION DISTRIBUTION:** PASS. Consistent across sections.
