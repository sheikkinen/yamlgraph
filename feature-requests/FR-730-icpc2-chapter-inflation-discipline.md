# Feature Request: FR-730 ICPC-2 Chapter-Code Inflation Discipline

**Priority:** MEDIUM
**Type:** Fix
**Status:** Judged
**Effort:** 1 day
**Requested:** 2026-07-14
**Judged:** 2026-07-14 — scope frozen; proposal's cap list and direction (c) both overturned by rubric-level verification
**Parent:** FR-727 (phase 3b) — see `examples/icpc-2-rfe/PLAN.md`
**Evidence:** FR-727 definitive baseline `logs/fr727-final.json`
(22/30; all 8 residual failures quantified below)

## Problem

The meta-process cap (FR-727) killed process-side verdict inflation;
the same defect class survives in the **chapter-code population**.
Rubrics that describe the situation's periphery rather than the
patient's stated reason claim `match`/high `partial_match` and pollute
two output surfaces:

1. **Secondary leaks** (4/30 baseline failures): Z10 "Health care
   system problem" and A13 "Concern about/fear of medical treatment"
   ride into `secondary` on hp36 (3×); P76 "Depressive disorder" — a
   *diagnosis* the transcript does not establish, claimed over the
   stated feelings-complaint P03 — leaks on tired-mood (1×).
2. **Corrupted composition** (the sharpest artifact): the `chapter_context`
   slot takes the best-ranked non-process candidate, so inflated Z10
   outranked K86 on an HP-36 run and the composed combined code came
   out **Z50** (renewal in the *social problems* chapter) instead of
   **K50** (cardiovascular). The composition mechanics are correct;
   the context input is polluted.

Unlike the process family, chapter codes cannot be capped by a small
static list — Z10/A13 are "true-of-everything" style, but P76-over-P03
is a *specificity* error (diagnosis claimed where only a symptom is
stated), and the right answer varies by transcript.

## Proposed Solution (directions for the Judge — pick, don't stack)

(a) **Z/A-meta static cap** (smallest): extend the FR-727 mechanism
    with a curated chapter-side list (Z10, A13, A23, A29-class
    "concern/risk/other" rubrics) — same demote-not-drop semantics.
    Handles the leak class; does NOT handle P76-over-P03.
(b) **Symptom-over-diagnosis context preference**: for the
    `chapter_context` slot only, prefer component-1 (symptom) and
    disease codes with `match` verdicts over Z-chapter codes; make Z
    codes ineligible as composition context (a renewal is never
    "social-chapter" business unless nothing else surfaced).
(c) **Evidence-gated diagnosis verdicts**: a component-7 (disease)
    code may claim `match` only when its evidence spans include the
    condition's name or an explicit prior-diagnosis statement —
    checkable in code against the catalog title/inclusion terms
    (P76 fails, K86 with "verenpainelääke" passes via inclusion cues).

Recommendation: (a) for the leak class + (b) for composition, as two
small witnessed reducer rules; (c) only if the harness shows
diagnosis-inflation beyond P76.

## Acceptance Criteria

- [ ] AC-01 Harness rerun (N=5): hp36 must_not_include failures (A13/
      Z10) go to zero; tired-mood P76 leak gone; total ≥ 26/30. The
      criterion that gates: **zero failures in the chapter-inflation
      class**; the aggregate is context (FR-727 diary:
      threshold_encodes_forecast).
- [ ] AC-02 Composition integrity: HP-36 composed code is K50 (or A50
      when no clinical context genuinely surfaces) across N=5 — never
      a Z-chapter composition for a clinical-context call.
- [ ] AC-03 No regression on passing fixtures (backpain/cough stay
      5/5); genuine Z-chapter RFEs still classifiable (a transcript
      actually about a social problem keeps its Z primary — witness
      with a synthetic fixture).
- [ ] AC-04 Fragment, diary, REQ under CAP-203 (id verified free at
      enforce); labels untouched (they already encode the truth).

## Constraints

1. FR-722/724/727 contracts frozen (span alignment, deterministic
   reducer, process primacy, meta-process cap).
2. Reducer-enforced, not prompt-trusted (prompt discipline has failed
   on inflation three times now).
3. Any static list follows the FR-727 pattern: constant in reduce.py,
   rationale comment, never in the generated Tier-1 catalog.

## Related

- FR-727 Implementation (failure taxonomy, Z50-vs-K50 artifact)
- Diary 2026-07-14 fr725 (every taxonomy has junk-drawer codes —
  graduating heuristic, second family)

## Judgement (2026-07-14)

**Verdict: APPROVED — with the proposal substantially re-pinned.**
Rubric-level verification (inclusion terms read for every candidate)
overturned two of the proposal's three directions:

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | **Direction (c) is unimplementable as specced — its own example is false.** K86's inclusion terms are English ("essential hypertension…"); a Finnish span ("verenpainelääke") can never string-match them. Evidence-gating against catalog terms breaks every non-English transcript — and Finnish support is a demonstrated feature | (c) **KILLED**. Recorded as the reason: catalog-term gating is language-bound; the example's multilingual capability comes precisely from NOT string-matching English terms |
| F2 | **Proposed cap list over-reached.** A29's inclusion terms are genuine symptoms (falls, drowsiness, somnolence — "grandma keeps falling" is a real RFE); A23 covers real exposure calls ("contact with infectious disease"); A13 ("fear of treatment consequences") is a genuinely stateable reason whose hp36 appearance is instance-level inflation, not descriptor semantics | Chapter cap = **{Z10} only** (empty inclusion list — a pure system descriptor, the Z-side twin of -48). A13/A23/A29 stay uncapped; their labels remain permanent detectors |
| F3 | **P76-over-P03 needs a mechanism, and ICPC provides one.** Practical rule 3 (our own background doc): use symptom coding while diagnostic uncertainty remains | New rule (d): **same-chapter symptom-over-diagnosis** — a component-7 match demotes to partial when a component-1 match exists in the same chapter (P03 match → P76 demoted; R05 → R74 demoted; K86 untouched on renewal calls — no K-chapter C1 match exists there). Mechanical, language-independent, witnessed both ways |
| F4 | **Composition context needs eligibility + preference, not just exclusion.** On the Z50 run, excluding Z10 alone might promote A13 over K86 into the context slot | Context slot rules: eligible = non-process, non-capped, **non-Z-chapter**; among eligible, **prefer component-7 diseases over component-1 symptoms** (the composition chapter anchors to the clinical problem being managed — the OPPOSITE preference from RFE primacy, deliberately). K86 wins context over A13 by component, not luck |
| F5 | **A13 residual accepted, named, measured.** No mechanical rule caps a genuinely stateable code without blocking its genuine use; prompt fixes are barred (3 failures) | AC-01 re-scoped: the gating classes are **Z10 leaks = 0, P76-class (same-chapter C7-over-C1) = 0, Z-composition for clinical calls = 0**. A13 secondary leaks are an accepted residual, expected ~2–3/30, tracked by the hp36 label as permanent detector; revisit only with harness evidence of growth. Aggregate ≥ 26/30 becomes ≈ 24–26/30 expected, recorded as context (threshold_encodes_forecast) |

Additional pins: AC-03's genuine-Z witness must use a **non-capped**
Z code (e.g. Z05 work problem) — a genuine Z10 system-complaint call
will now land low_confidence with Z10 top partial, which is the
documented trade-off of capping it; REQ under CAP-203 (id verified
free against origin at enforce); fragment (fix) + diary; harness
rerun quoted in the FR at completion.

**Out of scope (purge list):** direction (c) in any form, cap-list
extensions beyond Z10 without harness evidence, translation/multilingual
term matching, label changes, prompt changes, model variance on
ambiguous fixtures (diabetic/parking scatter — FR-726's territory if
anyone's).
