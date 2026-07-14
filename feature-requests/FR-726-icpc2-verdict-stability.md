# Feature Request: FR-726 ICPC-2 Verdict Stability (Phase 4)

**Priority:** LOW (blocked)
**Type:** Feature
**Status:** Proposed
**Effort:** 1-2 days
**Requested:** 2026-07-14
**Parent:** FR-722 — see `examples/icpc-2-rfe/PLAN.md`
**Blocked by:** FR-725 — this FR may not be judged until the crosscheck
harness has produced baseline agreement numbers (AC-04 there).

## Problem

Per-cluster LLM verdicts are nondeterministic even at temperature 0.1;
the deterministic reducer cannot repair variance in its inputs. Verdict
discipline (prompt) reduced but cannot eliminate flapping between
adjacent verdicts (match ↔ partial_match) on genuinely borderline
rubrics — observed as primary churn on HP-36 before discipline, and as
residual best-partial reordering after.

## Proposed Solution (to be judged against FR-725 baseline)

Per-cluster self-consistency voting: sample each cluster N times
(default N=3), aggregate per code — majority verdict, median
confidence, union of aligned evidence spans. Cost is N× LLM calls;
the judgement must weigh measured agreement gain against measured cost
(seed question from diary 2026-07-14: is 3× worth it, and should the
map node express repeat-sampling natively rather than the example
hand-rolling it?).

Alternatives the Judge must consider:
1. Reducer-side hysteresis over the run archive (no extra calls).
2. Native map-node `samples: N` + `aggregate:` primitive (framework
   feature — separate FR if chosen).
3. Do nothing: if FR-725 baseline shows ≥90% primary agreement after
   verdict discipline, close as not-worth-it.

## Acceptance Criteria

- [ ] AC-01 FR-725 harness shows a statistically meaningful agreement
      improvement at the judged N (before/after on the same fixtures).
- [ ] AC-02 Cost accounting: calls and wall-clock per transcript,
      before/after, in the FR.
- [ ] AC-03 Deterministic reducer contract unchanged; all phase-1/2
      witnesses green.
- [ ] AC-04 Explicit kill criterion honored: if baseline agreement is
      already ≥90%, this FR closes CONDEMNED with the numbers cited.

## Constraints

1. No calibration claims — voting changes verdict stability, not
   confidence meaning.
2. Fan-out × N must respect max_map_items or batch within the subnode.
