# Feature Request: FR-514 - DM v2 Delta-Close Ledger with Carry-Forward Floor

**Priority:** HIGH
**Type:** Enhancement
**Status:** Enforced (2026-06-17) — scope frozen, code + tests green
**Effort:** ~0.5 day
**Requested:** 2026-06-17
**Plan:** [docs/plan-ledger-memory.md](../docs/plan-ledger-memory.md) §4.1, §6 (item 1)

## Summary

Change the chapter-close world_state contract from **regenerate** (the LLM
re-emits the entire ledger every chapter) to **update-delta** (the LLM emits
operations against the inherited ledger, which deterministic code applies). The
inherited active set becomes a **floor**: a close that emits zero operations
leaves prior state intact rather than emptying it.

## Value Statement

A forgetful chapter close can no longer silently reset continuity state — the
ledger accumulates like a real memory instead of being regenerated from scratch.

## Problem

Run 10020-BC, Chapter 5 closed with **zero relationships**, breaking the
carry-chain: Chapter 6 re-derived the entire relationship web from scratch (and
changed several types). The grounding gate (FR-513) is correctly strict, but
regenerate semantics let a single off-chapter zero the store.

Every surveyed memory system (Generative Agents, MemGPT, A-MEM, Zep) uses
update-delta semantics; none re-emits the whole store each step. The ledger is the
outlier, and the Ch5 dropout is the direct symptom.

## Proposed Solution

### 1. Close emits operations, not a full ledger

`chapter_close.yaml` asks the LLM to emit a list of operations against the
inherited ledger:

```yaml
operations:
  - op: add         # newly established this chapter (bond, fact, object, character)
  - op: reaffirm    # still true this chapter (resets the decay clock; FR-517)
  - op: update      # a field changed (status, type, tensions, location, inventory)
  - op: invalidate  # conclusively ended (death, rupture, alliance broke)
```

Each op carries the same `recap_citations` grounding contract FR-513 introduced,
now enforced **per operation**.

### 2. Deterministic apply in world_state.py

A pure `apply_ledger_delta(inherited: dict, operations: list) -> dict`:

- starts from the inherited ledger (the floor),
- applies grounded `add` / `update` / `invalidate` / `reaffirm` ops,
- drops ungrounded ops (no `recap_citations`, or relationship with <2 parties),
- returns the new typed ledger.

`close_chapter` ([chapter_ops.py](../examples/dungeon_master/api/chapter_ops.py))
calls `apply_ledger_delta(inherited_world_state(...), closed["operations"])`
instead of `parse_world_state(closed["world_state"])`.

### 3. The floor

`operations == []` → result equals the inherited ledger. Empty/invalid op payload
normalizes to "carry forward unchanged," never to an empty store.

## Judgement (frozen contracts — binding on enforcement)

These four contracts are shared across FR-514/515/517/518 and are resolved **here**,
at the FR that introduces the apply path. The follow-ups inherit them verbatim.

- **J1 — Edge identity key.** A relationship edge is identified by
  `tuple(sorted(between))` (the participant set, case-normalized, type-independent).
  Type-independence is required so `enmity → romantic_bond` reconciles onto the
  *same* edge (FR-515). **Invariant:** at most **one current** edge per pair (an
  `update` op acts on that pair's current edge). Expressing two concurrent
  relationship dimensions for one pair (the Ch8 Hilde&Arnulf `hierarchy`+`alliance`
  case) is **deferred to FR-518**; until then a pair has one current edge and a
  second dimension lives in `type`/`tensions`.
- **J2 — Chapter stamp is an integer ordinal, not a string.** Every edge gains
  `valid_from: int` (the 0-based chapter ordinal at which this edge opened), set on
  `add`. The plan's `"Ch1"` / FR-515's `"1"` are illustrative only; the stored and
  compared value is the integer ordinal. This makes FR-515 `valid_to` and FR-517
  decay arithmetic, not string parsing.
- **J3 — Apply signature carries the ordinal.** The pure function is
  `apply_ledger_delta(inherited: dict, operations: list, current_index: int) -> dict`.
  `close_chapter` passes the closing chapter's ordinal; apply stays pure (it never
  resolves ordinals itself).
- **J4 — Lane scope: delta is relationships-only; the floor is all lanes.** Only
  the `relationships` lane switches to operations (it is the lane with the defect,
  the grounding contract, and the need for history). `characters`/`objects`/`facts`
  keep their full-ledger emission but gain the **floor**: a missing/empty lane in
  the close payload carries the inherited lane forward unchanged rather than
  emptying it. `chapter_close.yaml` therefore emits a dual payload —
  `world_state` (the three non-relationship lanes) **and** `operations` (the
  relationship deltas). Extending delta semantics to the other lanes (free-string
  `facts` have no natural key) is explicitly out of scope.

**Verdict:** Approved. Path is explicit and minimal under J1–J4. Highest-leverage
item; enforce first.

## Acceptance Criteria

- [x] **A1 - Delta application.** `apply_ledger_delta(inherited, operations,
  current_index)` applies add/update/invalidate/reaffirm against an inherited
  ledger and returns the typed shape; `add` stamps `valid_from = current_index`.
  Test: `test_apply_delta_adds_grounded_relationship_and_stamps_ordinal`.
- [x] **A2 - Carry-forward floor.** A close emitting zero operations yields the
  inherited active set unchanged. Test: `test_empty_delta_preserves_inherited_ledger`.
- [x] **A3 - Grounding preserved per-op.** An ungrounded operation is dropped; a
  grounded one is applied. Test: `test_ungrounded_operation_dropped`.
- [x] **A4 - invalidate removes from active set.** An `invalidate` op marks the edge
  resolved so it leaves turn context. Test: `test_invalidate_removes_from_active`.
- [x] **A5 - Close wiring.** `close_chapter` derives world_state via the delta path
  (`apply_lane_floor` + `apply_ledger_delta`); existing close/world_state tests
  (`test_chapters.py`, 189 DM tests) still pass.
- [ ] **A6 - Regression run.** Re-generate the 10020 premise; verify no chapter
  zeroes its relationships (the Ch5 dropout does not recur). *Deferred to live
  validation (real LLM run), as FR-513 A7 was; the floor makes the dropout
  impossible by construction — `test_empty_delta_preserves_inherited_ledger`.*
- [x] **A7 - One current edge per pair.** Two `add` ops for the same
  `sorted(between)` collapse onto a single current edge. Test:
  `test_single_current_edge_per_pair`.
- [x] **A8 - Non-relationship lane floor.** A close whose payload omits/empties
  `characters` (or `objects`/`facts`) carries the inherited lane forward unchanged.
  Test: `test_missing_lane_carries_forward`.

## Implementation

- `world_state.py`: `Relationship` gains `valid_from`/`valid_to`/`last_reaffirmed`
  (int ordinals); new `apply_ledger_delta`, `apply_lane_floor`, edge helpers
  (`_rel_key`, `_new_edge`, `_update_edge_fields`, `_op_grounded`).
- `chapter_ops.close_chapter`: derives `world_state` via
  `apply_lane_floor(emitted, inherited)` + `apply_ledger_delta(inherited,
  operations, ordinal)`; reads `operations` from inside the emitted `world_state`.
- `prompts/chapter_close.yaml`: relationships lane replaced by a grounded
  `operations` delta contract (add/reaffirm/update/invalidate).

## Alternatives Considered

1. **Keep regenerate; add a "don't shrink" post-check.** Rejected: a heuristic patch
   downstream of the symptom; cannot distinguish a legitimate removal from a
   forgetful one. Delta makes intent explicit at the boundary.
2. **Carry forward verbatim and only let the LLM append.** Rejected: relationships
   legitimately change (enmity→romantic_bond); append-only cannot express updates.

## Related

- [docs/plan-ledger-memory.md](../docs/plan-ledger-memory.md) — north-star (§4.1).
- [FR-513](FR-513-dm-v2-emotional-state-in-world-ledger.md) — the grounding gate this preserves.
- [FR-515](FR-515-dm-v2-bitemporal-ledger-reconciliation.md) — builds invalidation into temporal markers.
- [world_state.py](../examples/dungeon_master/api/world_state.py), [chapter_close.yaml](../examples/dungeon_master/prompts/chapter_close.yaml).
