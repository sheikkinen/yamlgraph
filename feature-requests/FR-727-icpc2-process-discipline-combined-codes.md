# Feature Request: FR-727 ICPC-2 Process-Code Discipline & Combined-Code Composition

**Priority:** HIGH (fixes a measured regression)
**Type:** Fix
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-07-14
**Parent:** FR-724 (phase 2) — see `examples/icpc-2-rfe/PLAN.md`
**Evidence:** FR-725 baseline `logs/fr725-baseline.json` (11 pass / 19 fail)

## Problem

Two coupled defects, one root cause: **phase 2 treats process codes as
free-floating competitors to chapter codes, but ICPC-2 process codes
are components that combine with an anatomical chapter letter or a
specific disease code** (`-50` in a cardiovascular context is coded
K50, not bare `-50`).

1. **Measured regression (FR-725 baseline):** meta-process rubrics —
   `-48` "Clarification/discussion of RFE/demand", `-69` "Other reason
   NEC" — are true of essentially every conversation. They claim
   `match`, and FR-724's process-primacy rule (F4) then flips symptom
   transcripts to process primaries: cough-fever agrees **5/5 on `-48`**
   (expected R05), diabetic-glucose the same. Agreement is high and
   wrong: bias, not variance.
2. **Output shape:** a bare `-50` primary is not a deliverable ICPC-2
   code. Real coding composes the process number with the chapter of
   the problem concerned: `chapter_context` K86 + `-50` → **K50**;
   with no clinical context, chapter **A** (general/unspecified) is the
   convention.

## Proposed Solution

1. **Process-request discipline (fixes the regression):** a process
   code may claim `match` only when the patient explicitly ASKS FOR the
   process (renewal, sick note, results, referral, admin document) —
   not when the process merely occurs in the encounter. Mechanism for
   the Judge: (a) prompt rule + demote `-48`/`-69` to a curated
   `meta_process: true` catalog flag that caps their verdict at
   partial_match in the reducer (code-enforced, not prompt-trusted), or
   (b) exclude `-48`/`-69`/`-45`-style encounter-descriptors from map
   candidacy entirely. The reducer cap (a) is preferred: visible,
   witnessed, reversible.
2. **Combined-code composition (mechanical):** when the primary is a
   process code, compose `combined_code = chapter_letter + process_number`
   from the already-derived `chapter_context` (K86 + -50 → K50);
   chapter A when no non-process candidate exists. Emit alongside, not
   replacing, the parts: `primary: {code: "-50", combined_code: "K50",
   chapter_context: {...}}`. Composition is string mechanics on data
   the reducer already holds — F5's provenance concern (looking up
   combined-rubric TITLES from the book) stays purged; we compose the
   CODE only.

## Acceptance Criteria

- [ ] AC-01 FR-725 harness rerun (N=5): cough-fever and
      diabetic-glucose recover their chapter primaries (R05 / T90-or--50
      per label); overall pass rate ≥ 24/30 from baseline 11/30.
- [ ] AC-02 HP-36: primary `-50` with `combined_code: K50` when the
      chapter context is cardiovascular; process-request fixtures keep
      their process primaries (backpain-sicknote `-62` stays legal).
- [ ] AC-03 Meta-process cap is reducer-enforced with witnesses (a
      `-48` match claim demotes to partial); catalog flag provenance:
      the flag is project-curated (tier 4, documented), not Wonca data.
- [ ] AC-04 Composition witnesses: K-context → K50; no context → A50;
      chapter primaries get no combined_code.
- [ ] AC-05 Labels updated where the output shape changes; fragment,
      diary, REQ under CAP-203.

## Constraints

1. FR-722 contracts frozen (span alignment, deterministic reducer).
2. No new dependencies; composition is string mechanics.
3. FR-726 stays gated until this lands and a fresh baseline separates
   residual variance from the (now-removed) bias.
