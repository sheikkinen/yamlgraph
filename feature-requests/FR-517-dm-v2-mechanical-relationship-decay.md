# Feature Request: FR-517 - DM v2 Mechanical Relationship Decay

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Enforced (2026-06-17) — code + tests green (depends on FR-514)
**Effort:** ~0.25 day
**Requested:** 2026-06-17
**Plan:** [docs/plan-ledger-memory.md](../docs/plan-ledger-memory.md) §4.3, §6 (item 4)
**Depends on:** FR-514 (the `reaffirm` operation; contracts J2–J3)

## Judgement

- `last_reaffirmed` is an **integer ordinal** (J2); decay is
  `current_index - last_reaffirmed > decay_after`, using the `current_index`
  parameter FR-514 adds to `apply_ledger_delta` (J3). No string math.
- **Why `last_reaffirmed` is distinct from FR-515 `valid_from`:** `valid_from`
  records when this edge *version opened* (and must not move, or FR-515 history
  breaks); `last_reaffirmed` records when it was last *confirmed still true* and
  moves on every `reaffirm`. They are different clocks; reusing `valid_from` for
  decay would corrupt the temporal record. Both are justified.
- Decay sets `status = dormant`; it does **not** set `valid_to` (a dormant edge is
  still current, just paused). Retrieval (FR-513/516) already excludes dormant.

**Verdict:** Approved, MEDIUM. Enforce after FR-514; independent of FR-515/516.

## Summary

Make `dormant` a deterministic code outcome, not only an LLM judgement. An edge not
`reaffirm`-ed for N chapters is demoted `active → dormant` automatically; the close
LLM may still `reaffirm` a dormant edge back to active when the recaps revive it.

## Value Statement

Stale relationships fade on a predictable schedule instead of lingering as `active`
until the model happens to notice they should not be — recency becomes arithmetic,
not the model's recollection.

## Problem

Today `status` is whatever the close LLM emits. The model has no reliable sense of
"how many chapters since this mattered," so a bond that stopped being relevant can
stay `active` indefinitely, bloating turn context (until FR-516) and misdirecting
play with tensions no longer in motion. Generative Agents (arXiv:2304.03442) models
recency as an explicit, decaying score precisely because the LLM cannot be trusted
to track elapsed time.

## Proposed Solution

### Track last-reaffirmed chapter

Each edge carries a `last_reaffirmed` chapter id (set on `add` and on each
`reaffirm` op from FR-514).

### Deterministic decay in apply

After applying the close delta, `apply_ledger_delta` demotes any `active` edge
whose `last_reaffirmed` is more than `decay_after` chapters behind the current
chapter:

```python
if current_index - edge_last_reaffirmed_index > decay_after and edge["status"] == "active":
    edge["status"] = "dormant"
```

### LLM revival, code decay (the boundary split)

- **Code** demotes active→dormant on the schedule.
- **LLM** may `reaffirm` (dormant→active) or `invalidate` (→archived/closed) when
  the recaps justify it.

`decay_after` lives in graph defaults (e.g. 2 chapters, matching the FR-513
"dormant = paused 2+ chapters" guidance).

## Acceptance Criteria

- [x] **A1 - last_reaffirmed tracked.** `add` and `reaffirm` set the edge's
  `last_reaffirmed` to the current chapter. Test: `test_reaffirm_updates_clock`.
- [x] **A2 - Mechanical demotion.** An active edge unrefreshed beyond `decay_after`
  is demoted to dormant by code, with no LLM op. Test:
  `test_stale_edge_decays_to_dormant`.
- [x] **A3 - Reaffirm rescues.** A `reaffirm` op within the window keeps the edge
  active. Test: `test_reaffirm_prevents_decay`.
- [x] **A4 - Dormant excluded from turn context.** Decayed edges leave active turn
  context. Test: `test_decayed_edge_not_in_turn_context`.

## Implementation

The decay pass runs at the end of `apply_ledger_delta`: an edge with
`valid_to is None`, `status == active`, and `current_index - last_reaffirmed >
decay_after` is set to `dormant`. `add`/`reaffirm` set `last_reaffirmed =
current_index`. `DECAY_AFTER = 2` is the module default (overridable per call).

## Alternatives Considered

1. **Continuous recency score (Generative Agents exponential decay).** Deferred:
   a discrete chapter-count threshold matches the chapter-granular ledger and is
   simpler to test; revisit if finer decay is needed.
2. **Leave decay to the LLM.** Rejected: that is the status quo, and it is exactly
   the unreliable elapsed-time tracking this FR removes.

## Related

- [docs/plan-ledger-memory.md](../docs/plan-ledger-memory.md) — north-star (§4.3).
- [FR-514](FR-514-dm-v2-delta-close-carry-forward-floor.md) — provides the `reaffirm` op.
- [FR-516](FR-516-dm-v2-ranked-topk-ledger-retrieval.md) — consumes the resulting status.
- Generative Agents, arXiv:2304.03442 — recency scoring.
