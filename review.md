# Reviewer A (Methodology Expert)

## Strengths
- The paper’s core framing is clear and methodologically interesting: `PerformanceCheck` is positioned as a post-hoc confirmation step rather than a discovery method, and that distinction is stated consistently in the abstract, introduction, and conclusion.
- The intervention design is much better motivated than in many similar drafts; the admissibility discussion in [draft.md](C:/Users/tsukasa/Documents/rl-shift-auto-detection/draft.md:53) and the class-consistent Waterbirds intervention in [draft.md](C:/Users/tsukasa/Documents/rl-shift-auto-detection/draft.md:57) help clarify what the method is and is not claiming.

## Weaknesses
- There is a concrete claim/evidence inconsistency in the main GridWorld summary. The abstract and conclusion report `top-2 = 101/120 (84%)` in [draft.md](C:/Users/tsukasa/Documents/rl-shift-auto-detection/draft.md:5) and [draft.md](C:/Users/tsukasa/Documents/rl-shift-auto-detection/draft.md:226), but the Results table reports `106/120 (88%)` in [draft.md](C:/Users/tsukasa/Documents/rl-shift-auto-detection/draft.md:109). This is a high-priority fix because it undermines trust in all repeated summary numbers.
- The introduction overstates the Waterbirds story. It says `PerformanceCheck と SHAP の双方が一致して背景スプリアス依存を検出` in [draft.md](C:/Users/tsukasa/Documents/rl-shift-auto-detection/draft.md:17), but the main result later emphasizes disagreement in success rates (`SHAP 30/30` vs `PerformanceCheck 18/30`) in [draft.md](C:/Users/tsukasa/Documents/rl-shift-auto-detection/draft.md:226). As written, the high-level claim is too coarse for the evidence actually shown.
- Topic drift remains around LunarLander. Even though the paper says it is only an applicability-boundary case, it still appears in the abstract, introduction, results tail, limitations, and conclusion: [draft.md](C:/Users/tsukasa/Documents/rl-shift-auto-detection/draft.md:5), [draft.md](C:/Users/tsukasa/Documents/rl-shift-auto-detection/draft.md:36), [draft.md](C:/Users/tsukasa/Documents/rl-shift-auto-detection/draft.md:177), [draft.md](C:/Users/tsukasa/Documents/rl-shift-auto-detection/draft.md:226). For a conference paper with tight space, this reads as off-topic relative to the main contribution.

## Actionable Revisions
- Resolve all duplicated headline metrics from a single authoritative table, then propagate the corrected numbers to abstract, introduction, and conclusion.
- Rewrite the Waterbirds summary claim as “partial agreement / complementary signals” rather than “both methods agree.”
- Cut LunarLander from the abstract and conclusion, and reduce main-text mentions to one sentence that points readers to the appendix.

---

# Reviewer B (Domain Expert)

## Strengths
- The paper stays mostly aligned with the target problem of detecting spurious reliance via intervention-based performance sensitivity, especially in the way it separates candidate discovery from candidate confirmation.
- The benchmark mix is sensible: synthetic control (`GridWorld`), stylized vision benchmark (`ColoredMNIST`), and a real spurious-correlation benchmark (`Waterbirds`).

## Weaknesses
- The manuscript is substantially under-length for the stated NeurIPS-style completeness bar. A local word count gives about `2,424` words for [draft.md], far below the `5,000–6,500` target in the review prompt. This shows in the thin treatment of experimental protocol, benchmark rationale, and failure analysis.
- The Experiments/Results section is light on benchmark-specific citations. The prompt explicitly asks for citation distribution beyond Intro/Related Work, but [draft.md](C:/Users/tsukasa/Documents/rl-shift-auto-detection/draft.md:85) through [draft.md](C:/Users/tsukasa/Documents/rl-shift-auto-detection/draft.md:177) is mostly citation-free despite making dataset- and protocol-specific claims.
- The paper has enough figures (7), so it avoids the “zero figures” problem, but some of the space is spent on narrow diagnostic snapshots (`n=5` tables) rather than deeper domain interpretation.

## Actionable Revisions
- Either expand the paper to full conference depth or narrow the framing to a shorter-format paper. Right now the ambition and body length are mismatched.
- Add benchmark/protocol citations directly in Experiments/Results for ColoredMNIST setup, Waterbirds split/evaluation conventions, and any benchmark-specific intervention choices.
- Replace at least one of the `n=5` snapshot tables with a fuller domain-facing analysis of when Waterbirds disagreement matters for practical remediation.

---

# Reviewer C (Statistics/Rigor Expert)

## Strengths
- The draft does several rigor things right: multiple seeds (`n=30`), Wilson confidence intervals in the main tables, and a paired sign test for the Waterbirds `Δ_bg - Δ_fg` gap in [draft.md](C:/Users/tsukasa/Documents/rl-shift-auto-detection/draft.md:140).
- Reproducibility is improved by the appendix tables for hyperparameters and compute resources.

## Weaknesses
- The main “Δ beats SHAP” claims are still not paired-tested where they most need to be. The Results tables show CIs, but the manuscript does not report explicit paired significance tests for the seed-matched Δ-vs-SHAP comparisons in GridWorld and ColoredMNIST; see [draft.md](C:/Users/tsukasa/Documents/rl-shift-auto-detection/draft.md:103) and [draft.md](C:/Users/tsukasa/Documents/rl-shift-auto-detection/draft.md:127). Because the same seeds/oracles are compared, a paired test such as McNemar should be shown, not just separate CIs.
- Two visually prominent diagnostic tables are only `n=5` snapshots: [draft.md](C:/Users/tsukasa/Documents/rl-shift-auto-detection/draft.md:119) and [draft.md](C:/Users/tsukasa/Documents/rl-shift-auto-detection/draft.md:167). These are fine as illustrations, but they are easy to over-read next to the paper’s 30-seed claims.
- Reproducibility is improved but still incomplete. [draft.md](C:/Users/tsukasa/Documents/rl-shift-auto-detection/draft.md:290) states that seeds are fixed, but it does not list the actual seeds or enough exact protocol detail for some interventions.

## Actionable Revisions
- Report paired significance tests for all headline Δ-vs-SHAP comparisons in the paper body or appendix, and cite them explicitly where superiority is claimed.
- Relabel the `n=5` tables as illustrative examples and keep the inferential weight on the 30-seed aggregates.
- Add the exact seed list and any intervention-sampling details needed to reproduce the paired comparisons exactly.
