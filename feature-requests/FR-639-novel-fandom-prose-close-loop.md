# FR-639: novel_fandom Phase 3 — Prose + Close Loop

**Priority:** MEDIUM
**Type:** Feature (example)
**Status:** Implemented
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

### Draft graph (`examples/novel_fandom/graphs/draft.yaml`, S7)

```yaml
nodes:
  draft_chapters:
    type: map                   # fan out over plot_path.beats
    prompt: draft_chapter       # grounded in retrieved canon context
    state_key: chapters
  extract_mentions:
    type: llm
    prompt: extract_prose_mentions  # extract entity names from prose → structured references list
    state_key: prose_mentions
  gate_prose:
    type: python
    tool: ref_gate              # check extracted mentions resolve to canon (reused gate)
    state_key: prose_gate
```

### Close graph (`examples/novel_fandom/graphs/close.yaml`, S8)

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
- **Target validation:** rejects any op whose target entities don't exist in canon
  (deterministic pre-check — the delta-extraction LLM may hallucinate targets).
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

- [ ] `examples/novel_fandom/graphs/draft.yaml` maps beats → chapters grounded in
      retrieved canon; lints + runs.
- [ ] `extract_prose_mentions` + `ref_gate` rejects a chapter naming a non-canon
      entity (RED test first). Prose entity extraction is a separate LLM step feeding
      structured references into the existing gate.
- [ ] `apply_deltas` supports `add_event`, `add_edge`, `update_valence`,
      `invalidate_edge`; each unit-tested (RED first).
- [ ] **Carry-forward floor:** a zero-op close leaves dynamic canon byte-identical. (Test.)
- [ ] **Invalidate-not-delete:** a contradicting fact sets `valid_to`, old edge retained. (Test.)
- [ ] **Lane guard:** an op targeting a `lane: static` page is rejected. (Test.)
- [ ] **Target validation:** `apply_deltas` rejects an op referencing a non-existent
      canon entity (RED test first).
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

## Judgement

**Verdict: APPROVED with three required corrections.**

This is the highest-risk FR in the trilogy. The close loop is where the delta-ledger
discipline either holds or leaks. The judgement is strict.

### What's right

1. **Edge-level ops as the primitive.** `add_event`, `add_edge`, `update_valence`,
   `invalidate_edge` — exactly the ledger granularity from plan-ledger-memory.md and
   FR-513–518. No page-level overwrites. Correct.
2. **Carry-forward floor.** Zero ops ⇒ no change. The single most important invariant
   (killed the FR-550 Ch5 zero-dropout). Explicitly stated and testable.
3. **Invalidate-not-delete.** Bi-temporal reconciliation (`valid_to` on old edge, new
   edge opens with `valid_from`). History preserved. Correct Graphiti discipline.
4. **Lane guard.** Ops targeting `lane: static` pages rejected. Prevents dynamic close
   from corrupting hand-authored canon.
5. **Two separate graphs (draft + close).** Correct decomposition — the map-over-beats
   step is independent from the delta extraction. They compose sequentially but are
   separately testable.
6. **Single-writer assumption (M3).** Explicitly stated. Correct for Phase 3 — no
   concurrent writes at example-scale.

### Required corrections

1. **Graph locations.** Same as FR-638: `graphs/draft.yaml` and `graphs/close.yaml`
   must live under `examples/novel_fandom/graphs/`, not the framework `graphs/`
   directory. This is an example application (C1).

2. **`prose_ref_gate` is the gate applied to prose text, not structured data.**
   The FR says "reused gate, prose-scan" but the existing `ref_gate` checks
   `references` in a structured dict. Prose is unstructured text — entity mentions
   must be *extracted* before they can be checked against canon. This is a new
   capability: a prose-scan step (regex or LLM-extracted entity list) feeding into
   the existing reference check. The FR must acknowledge this is **not** a pure reuse
   of `ref_gate` but a new adapter that extracts mentions from prose, then delegates
   to the existing reference check. Add a `prose_mention_extractor` step or confirm
   the draft prompt forces entity names into a structured `references` field alongside
   the prose text.

3. **`apply_deltas` must validate op targets exist in canon before writing.**
   The FR describes the ops but doesn't state: what happens when `update_valence`
   references a non-existent edge, or `add_edge` references a non-existent entity?
   The gate catches reference violations in the *plot path*, but the *delta extraction*
   is a separate LLM call that could hallucinate targets. Add: `apply_deltas` rejects
   any op whose target entities don't exist in canon (deterministic pre-check, no LLM).

### Observations (no action required)

- The `extract_consequences` prompt will need careful design. The LLM must emit
  structured ops, not prose summaries. The prompt should use an inline schema or
  Pydantic output model to constrain the shape. This is a prompting concern, not
  a structural one.
- The end-to-end acceptance criterion (pathfind → draft → close → re-run) is ambitious
  for a 2–3 day effort. Consider whether the e2e test can use mock LLM responses
  for the draft/extract steps while keeping `apply_deltas` real. The important
  invariants (carry-forward, invalidate-not-delete, lane guard) are all deterministic
  and testable without LLM.

### Scope freeze

- 1 `draft.yaml` graph (map beats → chapters)
- 1 `close.yaml` graph (extract deltas → apply)
- 1 `draft_chapter` prompt YAML
- 1 `extract_consequences` prompt YAML (with inline schema for ops)
- 1 `prose_ref_gate` or prose-mention-extractor + gate adapter
- 1 `apply_deltas` Python tool (4 ops, carry-forward floor, bi-temporal, lane guard)
- Tests: each op type, carry-forward floor, invalidate-not-delete, lane guard,
  op-target validation, prose leak detection
- demo-output.log

Nothing else.

## Related

- [plan-fandom-architecture-2.md](../docs/plan-fandom-architecture-2.md) §2 (S7+S8), §3 (dynamic schema).
- [plan-fandom-judgement.md](../docs/plan-fandom-judgement.md) — C3 (edge-level), M3 (single-writer).
- [plan-ledger-memory.md](../docs/plan-ledger-memory.md) — delta-ledger discipline.
- [FR-638](./FR-638-novel-fandom-plot-pathfinder.md) — produces the plot path this drafts.
- [FR-515](./FR-515-dm-v2-bitemporal-ledger-reconciliation.md) / [FR-513–518](./FR-513-dm-v2-emotional-state-in-world-ledger.md) — bi-temporal + delta model.
- [FR-632](./FR-632-pydantic-tojson-boundary.md) — Pydantic-in-template fix this draft step relies on.
