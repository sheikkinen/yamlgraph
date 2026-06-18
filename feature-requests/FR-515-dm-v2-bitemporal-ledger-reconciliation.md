# Feature Request: FR-515 - DM v2 Bi-Temporal Ledger Reconciliation

**Priority:** HIGH
**Type:** Enhancement
**Status:** Enforced (2026-06-17) — code + tests green (depends on FR-514)
**Effort:** ~0.5 day
**Requested:** 2026-06-17
**Plan:** [docs/plan-ledger-memory.md](../docs/plan-ledger-memory.md) §4.2, §6 (item 2)
**Depends on:** FR-514 (delta-close operations; contracts J1–J4)

## Judgement

- Inherits FR-514 **J1** (edge key = `sorted(between)`) and **J2** (integer
  ordinal). `valid_to` is therefore an **integer ordinal** (the chapter that closed
  the edge), matching `valid_from`. The illustrative `"1"`/`"2"` in this doc means
  the integers `1`/`2`.
- `valid_from` is **already introduced by FR-514** (set on `add`); FR-515 adds only
  `valid_to` and the close-and-open reconciliation in `apply_ledger_delta`.
- Reconciliation acts on the **one current edge per pair** (J1): an `update`
  contradicting the current edge sets its `valid_to = current_index` and opens a
  new edge with `valid_from = current_index, valid_to = None`.

**Verdict:** Approved. Enforce after FR-514. Kills the type-lag by construction.

## Summary

Give ledger edges a lifespan. When an `update`/`invalidate` operation contradicts
an existing fact, deterministic code does not silently overwrite it — it **closes**
the old edge with a `valid_to` marker and **opens** the new one. Turn context reads
only currently-valid edges; history stays queryable.

## Value Statement

A relationship's type/status changes the moment the play turns, not several
chapters later when the LLM happens to overwrite the stale edge.

## Problem

Run 10020-BC: Hilde & Gunnar stayed `enmity` through Ch1–Ch4 even though the Ch2
prose already had them as intimate lovers; the edge only became `romantic_bond` at
Ch6 — a four-chapter lag. With regenerate (and even with FR-514's delta), an edge
persists unchanged until the model explicitly rewrites it. There is no mechanical
**reconciliation**: nothing forces a contradiction to resolve at the boundary where
it occurs.

Zep/Graphiti (arXiv:2501.13956) solves this with bi-temporal edges: a contradicting
fact invalidates the prior edge rather than overwriting it.

## Proposed Solution

### 1. Edges gain `valid_from` / `valid_to`

```python
{"between": ["Hilde", "Gunnar"], "type": "enmity",
 "valid_from": "1", "valid_to": "2"}            # invalidated, kept for history
{"between": ["Hilde", "Gunnar"], "type": "romantic_bond",
 "valid_from": "2", "valid_to": None}            # current
```

`valid_to is None` ⇒ currently valid. Same pattern applies to facts and object
holders, not only relationships.

### 2. Deterministic reconciliation in apply

When a delta op (FR-514) `update`s or `invalidate`s an edge keyed by the same
participants, `apply_ledger_delta`:

- sets the existing current edge's `valid_to` to the closing chapter id,
- appends the new edge with `valid_from` = this chapter, `valid_to = None`.

No edge is deleted; contradiction is resolved by closing-and-opening.

### 3. Retrieval filters to current

`format_world_state(..., relationships="active")` (turn context) and
`inherited_world_state` carry only `valid_to is None` edges. The close LLM and the
book reviewer may read the full history.

## Acceptance Criteria

- [x] **A1 - Temporal fields.** Edges accept `valid_from`/`valid_to`; legacy edges
  without them normalize to current (`valid_to=None`). Test:
  `test_legacy_edge_normalizes_to_current`.
- [x] **A2 - Close-and-open.** An `update` contradicting a current edge closes the
  old (`valid_to` set) and opens the new (`valid_to=None`). Test:
  `test_contradiction_closes_old_opens_new`.
- [x] **A3 - No deletion.** The invalidated edge remains in the stored ledger with a
  bounded `valid_to`. Test: `test_invalidated_edge_retained_for_history`.
- [x] **A4 - Current-only retrieval.** Turn context and inherited carry include only
  `valid_to is None` edges. Test: `test_turn_context_excludes_closed_edges`.
- [x] **A5 - Type-lag regression.** A constructed Ch_n with intimate recaps over a
  prior `enmity` edge yields a current `romantic_bond` and a closed `enmity` in the
  same close. Test: `test_enmity_to_romantic_reconciled_same_chapter`.

## Implementation

Reconciliation lives in `apply_ledger_delta` (FR-514): an `update` op whose `type`
differs from the current edge sets the old edge's `valid_to = current_index` and
appends a new current edge. `format_world_state(..., relationships="active")` now
excludes `valid_to`-set edges from turn context; `"all"` keeps them for history.

## Alternatives Considered

1. **Overwrite in place (no history).** Rejected: loses the audit trail the book
   reviewer and close LLM use; cannot distinguish "never existed" from "ended."
2. **Single mutable status field only.** Rejected: status captures active/dormant/
   archived but not the *transition chapter*; temporal markers are needed to filter
   retrieval and to ground the reviewer's continuity checks.

## Related

- [docs/plan-ledger-memory.md](../docs/plan-ledger-memory.md) — north-star (§4.2).
- [FR-514](FR-514-dm-v2-delta-close-carry-forward-floor.md) — the delta operations this reconciles.
- Zep / Graphiti, arXiv:2501.13956 — bi-temporal agent memory.
- [world_state.py](../examples/dungeon_master/api/world_state.py).
