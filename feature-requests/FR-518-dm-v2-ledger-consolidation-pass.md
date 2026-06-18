# Feature Request: FR-518 - DM v2 Ledger Consolidation Pass

**Priority:** LOW
**Type:** Enhancement
**Status:** Partially enforced (2026-06-17) — deterministic `apply_merges` shipped + tested; LLM merge-proposal prompt + cadence wiring deferred (no live defect: FR-514 J1 + FR-515 already neutralize the Ch8 same-pair duplicate)
**Effort:** ~0.5 day
**Requested:** 2026-06-17
**Plan:** [docs/plan-ledger-memory.md](../docs/plan-ledger-memory.md) §4.5, §6 (item 5)
**Depends on:** FR-514, FR-515 (delta + temporal edges to consolidate over)

## Judgement

- This FR **owns the multi-edge-per-pair case** that FR-514 J1 deferred: the only
  way a pair holds two concurrent dimensions (Ch8 `hierarchy`+`alliance`) is for
  this consolidation pass to either merge them or explicitly sanction them. Until
  FR-518 lands, J1's "one current edge per pair" holds and the second dimension
  lives in `type`/`tensions`.
- Merges close the merged-out edges with `valid_to` (FR-515 J2 ordinal), never
  delete — preserving history and the FR-513 grounding citations.

**Verdict:** Approved, LOW. Enforce last; it is cleanup, not a continuity fix.

## Summary

Add a periodic **consolidation** (reflection) pass that merges redundant ledger
edges and may synthesize higher-order facts. This is the cleanup/evolution step of
A-MEM (arXiv:2502.12110) — second-order, sequenced last in the memory roadmap.

## Value Statement

The ledger stays legible as a story grows: duplicate and near-duplicate edges are
merged, and recurring patterns become single higher-order facts rather than a pile
of low-level ones.

## Problem

Run 10020-BC, Chapter 8 carried Hilde & Arnulf as **two** edges simultaneously —
`hierarchy` *and* `alliance`. Nothing merges semantically overlapping edges, so the
ledger accumulates redundancy. A-MEM's "memory evolution" addresses exactly this:
integrating a new memory updates and consolidates existing ones.

This is a **correctness-adjacent cleanup**, not a continuity bug on its own —
hence LOW priority and last in sequence. It should not block the delta/reconcile/
retrieval/decay FRs.

## Proposed Solution

### A bounded consolidation step at chapter close (or every M chapters)

A dedicated prompt receives the current edge set for a participant pair / cluster
and proposes merges:

```yaml
# consolidate.yaml — proposes merges, grounded in the existing edges
merges:
  - merge: [<edge_id_a>, <edge_id_b>]
    into: {between: [...], type: ..., tensions: [...]}
    rationale: "hierarchy subsumed by the broader alliance once Arnulf yielded"
```

Deterministic code applies only **grounded** merges (the merged edge must cite the
sources it subsumes), preserving the FR-513 grounding invariant and the FR-515
temporal history (merged-out edges are closed, not deleted).

### Higher-order synthesis (optional, same pass)

The pass may emit a synthesized fact ("the Aschenwulf line now defers to Reinmar's
route authority") as a new grounded `fact` edge, mirroring Generative Agents'
reflection.

## Acceptance Criteria

- [x] **A1 - Duplicate merge.** Two semantically overlapping edges for the same pair
  collapse into one; sources are closed with temporal markers (FR-515), not deleted.
  Test: `test_overlapping_edges_merged`.
- [x] **A2 - Grounded merges only.** A merge whose result lacks citation to its
  sources is rejected. Test: `test_ungrounded_merge_rejected`.
- [x] **A3 - No-op safety.** A ledger with no redundancy is unchanged by the pass.
  Test: `test_consolidation_noop_on_clean_ledger`.
- [ ] **A4 - Cadence.** The pass runs on the configured cadence (close, or every M
  chapters) without altering unrelated edges. *Deferred: the deterministic
  `apply_merges` primitive is shipped and tested, but the LLM merge-proposal
  prompt and the close/cadence wiring that would call it are not yet built. This
  is the lowest-value item and FR-514 J1 + FR-515 already prevent the Ch8
  same-pair duplicate by construction, so there is no live defect forcing it.*

## Implementation

`world_state.apply_merges(ledger, merges, current_index)` (pure): applies grounded
merges — sources closed with `valid_to`, consolidated edge opened with FR-513
grounding enforced; a merge over missing/closed sources is skipped (no-op on a
clean ledger). Not yet wired into `close_chapter`; the LLM proposal prompt is
future work.

## Alternatives Considered

1. **Consolidate inside the regular close prompt.** Rejected: overloads the close
   LLM's job (extract + reconcile + merge) and makes failures harder to localize; a
   dedicated pass is testable in isolation.
2. **Skip consolidation entirely.** Acceptable short-term — this is the lowest-value
   item; the delta/reconcile/retrieval/decay FRs deliver the continuity wins. Listed
   for completeness of the memory model.

## Related

- [docs/plan-ledger-memory.md](../docs/plan-ledger-memory.md) — north-star (§4.5).
- [FR-514](FR-514-dm-v2-delta-close-carry-forward-floor.md), [FR-515](FR-515-dm-v2-bitemporal-ledger-reconciliation.md) — prerequisites.
- A-MEM (arXiv:2502.12110) — memory evolution; Generative Agents (arXiv:2304.03442) — reflection.
