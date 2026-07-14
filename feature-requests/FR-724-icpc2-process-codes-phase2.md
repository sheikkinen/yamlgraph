# Feature Request: FR-724 ICPC-2 Process Codes (Phase 2)

**Priority:** HIGH
**Type:** Feature
**Status:** In Progress
**Effort:** 1-2 days
**Requested:** 2026-07-14
**Judged:** 2026-07-14 — scope frozen with 5 findings
**Parent:** FR-722 (phase 1, Completed) — see `examples/icpc-2-rfe/PLAN.md`

## Problem

Phase 1 covers components 1 (symptoms) and 7 (diseases) only. Field
fixture HP-36 (Finnish prescription-renewal call) proved the gap: the
canonical RFE for a renewal/administrative call is a **process code**
(components 2–6, the shared `-30…-69` rubrics), so phase 1 can only
answer `low_confidence` with the disease context (K86) as best partial.
Renewal, exam, test-result, administrative, and referral calls are the
dominant traffic in the ninchat voice deployment — they deserve
first-class codes.

The builder already parses all 40 process rubrics from ICPC-2e-v7.0
(inclusion/exclusion/criteria present since v5.0) and currently
excludes them (`chapter == "-"`, FR-722 phase-1 purge list).

## Proposed Solution

- Builder: include process rubrics as chapter-independent rows
  (`cluster_id: PROC-C<n>` per component 2–6; ~5 clusters, fan-out
  grows 33 → ~38, still under max_items 40).
- ICPC-2 semantics note: process codes combine with a chapter in real
  coding (e.g. `-50` in chapter K → K50 medication renewal). Phase 2
  scope: emit the process verdict + the chapter context separately
  (`primary: {code: "-50", ..., chapter_context: "K86"}`); composing
  the combined rubric (K50) is a formatting concern for the reducer,
  judged at enforce.
- Prompt: unchanged contract; process clusters flow through the same
  `reason_cluster` prompt with their own briefs.
- Reducer: no policy change; coverage meta components becomes
  `[1, 2, 3, 4, 5, 6, 7]`.

## Acceptance Criteria

- [ ] AC-01 HP-36 fixture: primary is the medication-renewal process
      code with hypertension as chapter/disease context; not
      low_confidence.
- [ ] AC-02 Symptom regression: cough transcript still yields R05
      match (phase-1 witnesses stay green untouched).
- [ ] AC-03 Coverage honesty: meta declares the expanded components;
      builder/loader/reducer witnesses extended for PROC clusters.
- [ ] AC-04 Fragment + diary + REQ under CAP-203 (id verified free at
      enforce).

## Constraints

1. FR-722 contracts frozen: span alignment, verdict discipline,
   deterministic reducer, catalog-generation posture (A1) all unchanged.
2. No new prompt; no new dependencies.

## Evidence

- `examples/icpc-2-rfe/data/HP-36-acting-on-behalf-of-adult.md` +
  archived runs in `logs/icpc2-rfe/` (K86 top partial, low_confidence).
- FR-722 Implementation, field runs 7–8.

## Judgement (2026-07-14)

**Verdict: APPROVED — with 5 findings, two of them re-pins.** Cluster
arithmetic verified against the Tier-1 ClaML: process components
distribute C2:20, C3:10, C4:2, C5:1, C6:7 — exactly 5 clusters,
fan-out 33 → 38, under the graph's max_items 40.

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | `chapter_context` cannot come from the LLM — a process cluster's prompt sees only process rubrics and has no basis to judge chapter; asking it would break the one-judgement contract | `chapter_context` is REDUCER-derived: the best-ranked non-process candidate (match or partial), attached mechanically when the primary is a process code. Code, not prompt |
| F2 | **Live contradiction found:** the phase-1 prompt's verdict-discipline example (`reason_cluster.yaml` L10) says a renewal call MATCHES the hypertension rubric — phase 2 makes that example wrong (the renewal PROCESS code is the match; the disease rubric is context) | Flip the example in the same commit that adds process clusters; phase-1 witnesses must stay green (they assert R05/cough, not the example's semantics) |
| F3 | AC-01 as written wants "K86 as disease-context secondary", but under F2's flip K86 becomes partial_match and `secondary` holds matches only | AC-01 re-pinned: HP-36 primary = medication-renewal process code, not low_confidence; K86 appears as reducer-attached `chapter_context` AND in best_partial. It does NOT need to be in `secondary` |
| F4 | Tie risk: if both a process code and a chapter code claim match, rank falls to confidence then code string — "-" sorts before letters, so process codes would win ties by ASCII accident | Pin the semantics explicitly in the reducer: a process-code match outranks a chapter-code match for RFE primacy (ICPC RFE semantics: the stated reason IS the process), with the chapter code demoted to context. Deliberate rule, witnessed — never asciibetical luck |
| F5 | Combined-code composition (K50 = chapter + process) tempts scope creep | OUT of scope, confirmed: emit `-50` + `chapter_context: K86`. Composing combined rubrics requires chapter-binding rules from the book — provenance work with its own FR |

Additional pins:
- `cluster_id: PROC-C<n>` (not `--C<n>` which the current f-string would
  produce from chapter `"-"`) — builder handles the process chapter
  explicitly; loader/briefs unchanged.
- Coverage meta becomes `components: [1,2,3,4,5,6,7]`; the FR-725 label
  for HP-36 flips in the same commit if 725 lands first (whichever
  lands second reconciles).
- Traceability: new REQ under CAP-203, id verified free at enforce;
  fragment (feat) + diary.

**Out of scope (purge list):** combined-code composition (F5), any
reducer policy change beyond F1/F4, prompt changes beyond the F2
example flip, calibration, phase 3/4 concerns.
