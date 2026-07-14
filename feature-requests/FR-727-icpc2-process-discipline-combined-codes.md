# Feature Request: FR-727 ICPC-2 Process-Code Discipline & Combined-Code Composition

**Priority:** HIGH (fixes a measured regression)
**Type:** Fix
**Status:** Judged
**Effort:** 1 day
**Requested:** 2026-07-14
**Judged:** 2026-07-14 — scope frozen with 5 findings; cap list pinned from the full rubric read
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

## Judgement (2026-07-14)

**Verdict: APPROVED — with 5 findings.** All 40 process-rubric titles
were read before pinning the cap list (read_raw_output_first applied to
the taxonomy itself, not just the model output).

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | "…and `-45`-style" is instance-chasing; the cap list needs an a-priori principle + explicit membership | Principle: cap rubrics that describe the ENCOUNTER's form or a junk drawer, not a patient-requestable process. **Cap list pinned: `-43, -46, -48, -69`** (`-43` other diagnostic procedure NEC — observed wrong primary on tired-mood; `-46` consultation with primary care provider — true of literally every call; `-48` clarification of demand; `-69` other reason NEC). Explicitly NOT capped: `-63/-64/-65` (follow-up / initiated-by) — "the doctor asked me to call" IS a stateable reason; NEC drawers `-38/-49/-59/-68` stay uncapped on watch — the harness quantifies them before any extension |
| F2 | The FR's preferred mechanism (catalog `meta_process` flag) threads project opinion through the generated Tier-1 artifact | REJECTED in favor of a **constant in reduce.py** (`META_PROCESS_CODES`) with rationale comment. The generated catalog stays a pure Tier-1 derivation; the cap is visibly project curation, versioned with the code that enforces it. Cheaper, equally witnessed, revisable |
| F3 | Cap semantics underspecified (drop? reject? demote?) | **Demote match → partial_match at validation time**, before dedup/ranking. Not a drop (evidence preserved in best_partial), not a rejection (the model did nothing invalid). Witness: a `-48` match claim lands in best_partial, never primary/secondary |
| F4 | Composition validity: is `<chapter>+<digits>` always legal? | Yes by construction — WHO/WICC biaxial design: all 7 components exist in all 17 chapters. `combined_code = chapter_context.code[0] + process_code.lstrip("-")`; **chapter A (general/unspecified) when no non-process candidate exists**. Parts stay primary: `code` remains `-50`; labels keep matching on `code` (AC-05 shrinks to: no label changes needed) |
| F5 | AC-01's ≥24/30 target must survive the pinned scope | Recomputed against the baseline: cough-fever 0→5 (R05 recovers), diabetic 0→5, parking 1→~4 (`-69`/`-48` capped; `-62`/A97 both labeled), backpain 5 (unchanged — `-62` is a genuine request), hp36 3 (Z10/A13 chapter-code inflation is OUT of scope, residual), tired-mood 2→~3 (`-43` capped; P76 residual). Expected ≈25/30; **AC-01 stands at ≥24/30**. Residual failures are chapter-code inflation — deliberately left for the fresh baseline to quantify, NOT smuggled into this FR |

Additional pins: `show_result.py` prints `combined_code` when present;
REQ under CAP-203 (id verified free at enforce); fragment (fix) +
diary; harness rerun (`--runs 5`) is the AC-01 evidence and its report
is quoted in the FR at completion.

**Out of scope (purge list):** chapter-code match inflation (Z10/A13/
P76 leaks — own FR if the fresh baseline justifies it), combined-rubric
TITLE lookup (F5 of FR-724 stays purged), cap-list extensions without
harness evidence, prompt changes (the cap is code-enforced precisely
because prompt discipline failed twice).
