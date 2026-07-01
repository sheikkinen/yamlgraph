# FR-639: novel_fandom Phase 3 — Prose + Close Loop

**Priority:** MEDIUM
**Type:** Feature (example)
**Status:** Proposed
**Effort:** 2–3 days
**Requested:** 2026-07-01

## Summary

The play loop's write half (subsystems S7 + S8). An approved plot path (FR-638) is
drafted into chapter prose (a `map` over beats, grounded in retrieved canon), the
prose is gated for leaked entities, an LLM extracts what *happened* as **edge-level
delta-ops**, and a deterministic `apply_deltas` tool writes them back to the dynamic
canon — appending events and reconciling relationship valence with bi-temporal
validity, never regenerating the store.

## Value Statement

Closes the loop: stories change the world in a controlled, append-only way, so canon
compounds across chapters instead of rotting or being overwritten — the difference
between a wiki that grows and one that drifts.

## Problem

FR-638 produces a gated plot path but writes nothing. To make canon *accumulate*, the
consequences of each chapter must land back in the dynamic lane under strict
discipline (per [plan-ledger-memory.md](../docs/plan-ledger-memory.md) and the
judgement's committed decisions): **edge-level ops** (C3), **carry-forward floor**
(zero ops ⇒ no change), and **invalidate-not-delete** bi-temporal reconciliation.
Prose must also be gated: a chapter may not name an entity absent from canon.

## Proposed Solution

### Draft graph (`graphs/draft.yaml`, S7)

```yaml
nodes:
  draft_chapters:
    type: map                   # fan out over plot_path.beats
    prompt: draft_chapter       # grounded in retrieved canon context
    state_key: chapters
  gate_prose:
    type: python
    tool: prose_ref_gate        # no leaked entities in prose (reused gate, prose-scan)
    state_key: prose_gate
```

### Close graph (`graphs/close.yaml`, S8)

```yaml
nodes:
  extract_deltas:
    type: llm
    prompt: extract_consequences   # → edge-level ops (new event, valence shift)
    state_key: deltas
  apply_deltas:
    type: python
    tool: apply_deltas             # write ops to canon/ (lane: dynamic only)
    state_key: _written
```

### `apply_deltas` tool (deterministic, the persistence half)

- **Edge-level ops only:** `add_event`, `add_edge`, `update_valence`,
  `invalidate_edge` — matching the ledger granularity ([FR-513–518](./FR-513-dm-v2-emotional-state-in-world-ledger.md)).
- **Carry-forward floor:** zero ops ⇒ dynamic canon byte-unchanged; it cannot
  spontaneously empty.
- **Bi-temporal reconcile:** a contradicting fact sets `valid_to` on the old edge
  (invalidate), never deletes it ([FR-515](./FR-515-dm-v2-bitemporal-ledger-reconciliation.md)).
- **Lane guard:** rejects any op targeting a `lane: static` page.
- **Single-writer:** `propose → gate → commit` assumes no concurrent writer (M3).

### Dynamic page shape

```yaml
# canon/events/ashfall_reckoning.yaml  (lane: dynamic)
type: event
id: ashfall_reckoning
lane: dynamic
window: age_of_cinders
participants: [kaelen, voss]
consequences: ["Kaelen breaks with the Ashguard"]
valid_from: "2026-07-01"
valid_to: null
references: [kaelen, voss, ashguard]
```

## Acceptance Criteria

- [ ] `graphs/draft.yaml` maps beats → chapters grounded in retrieved canon; lints + runs.
- [ ] `prose_ref_gate` rejects a chapter naming a non-canon entity (RED test first).
- [ ] `apply_deltas` supports `add_event`, `add_edge`, `update_valence`,
      `invalidate_edge`; each unit-tested (RED first).
- [ ] **Carry-forward floor:** a zero-op close leaves dynamic canon byte-identical. (Test.)
- [ ] **Invalidate-not-delete:** a contradicting fact sets `valid_to`, old edge retained. (Test.)
- [ ] **Lane guard:** an op targeting a `lane: static` page is rejected. (Test.)
- [ ] End-to-end: pathfind (FR-638) → draft → close grows the dynamic canon by exactly
      the extracted ops, and a re-run over the next window builds on them.
- [ ] Tests tagged `@pytest.mark.req("REQ-YG-XXX")`; capability entry added.
- [ ] `demo-output.log` present showing a full window iteration.

## Alternatives Considered

- **Page-level `update_page(delta)` as the primitive** — rejected per C3: edge-level
  ops are the primitive; `update_page` is a convenience wrapper over them.
- **Delete-on-contradiction** — rejected: loses history; bi-temporal invalidate keeps
  the audit trail (Graphiti discipline).
- **Regenerate the dynamic store each close** — rejected: the regenerate-whole-store
  failure mode the ledger work exists to prevent.

## Related

- [plan-fandom-architecture-2.md](../docs/plan-fandom-architecture-2.md) §2 (S7+S8), §3 (dynamic schema).
- [plan-fandom-judgement.md](../docs/plan-fandom-judgement.md) — C3 (edge-level), M3 (single-writer).
- [plan-ledger-memory.md](../docs/plan-ledger-memory.md) — delta-ledger discipline.
- [FR-638](./FR-638-novel-fandom-plot-pathfinder.md) — produces the plot path this drafts.
- [FR-515](./FR-515-dm-v2-bitemporal-ledger-reconciliation.md) / [FR-513–518](./FR-513-dm-v2-emotional-state-in-world-ledger.md) — bi-temporal + delta model.
- [FR-632](./FR-632-pydantic-tojson-boundary.md) — Pydantic-in-template fix this draft step relies on.
