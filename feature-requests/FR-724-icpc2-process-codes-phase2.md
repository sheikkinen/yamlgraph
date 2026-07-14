# Feature Request: FR-724 ICPC-2 Process Codes (Phase 2)

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed
**Effort:** 1-2 days
**Requested:** 2026-07-14
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
