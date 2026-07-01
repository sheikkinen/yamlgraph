# FR-638: novel_fandom Phase 2 — Plot Pathfinder

**Priority:** MEDIUM
**Type:** Feature (example)
**Status:** Implemented
**Effort:** 1–2 days
**Requested:** 2026-07-01

## Summary

The fiction-specific generative step (subsystem S6). Given a timeline window and a
character roster, a `retrieve_window` tool reads the open tensions from the typed
canon (FR-637), an LLM proposes a beat sequence that moves those *existing* tensions
toward resolution, and the shipped gate verifies every beat references only canon
entities. Traversal, not invention.

## Value Statement

Turns the static canon graph into stories: the plot is *searched* over fixed
character goals and relationship tensions, so the dramatic arc is derived and
checkable — replacing the refuted self-report metric with a grounded traversal.

## Problem

FR-637 gives a typed canon with goals, valence, and a timeline, but nothing reads
it as a story. The plot pathfinder is the one generative node in the play loop
(per [plan-fandom-generation.md](../docs/plan-fandom-generation.md) §5): it must
propose beats that only reference existing entities and only move tensions that
already exist in canon. Without it, canon is inert.

This is **fiction-domain** logic (tension, resolution, goals, arcs) — no generic
equivalent exists (v2 §2, S6).

## Proposed Solution

### Graph (`examples/novel_fandom/graphs/find_path.yaml`)

```yaml
data_files:
  canon: "canon/**/*.yaml"      # glob load (FR-629)

nodes:
  retrieve_context:
    type: python
    tool: retrieve_window       # filter canon by window + roster; extract open tensions
    state_key: context

  find_path:
    type: llm
    prompt: find_plot_path      # propose beat sequence over the fixed tensions
    state_key: plot_path

  gate_path:
    type: python
    tool: ref_gate              # every beat reference must resolve to canon (reused)
    state_key: gate_result

  fix_path:
    type: llm
    prompt: fix_plot_path       # repair beats that reference non-canon entities
    state_key: plot_path
    loop_limit: 2

edges:
  - {from: START, to: retrieve_context}
  - {from: retrieve_context, to: find_path}
  - {from: find_path, to: gate_path}
  - from: gate_path
    branches:
      - {when: "gate_result.valid == true", to: END}
      - {when: "gate_result.valid == false", to: fix_path}
  - {from: fix_path, to: gate_path}
```

### `retrieve_window` tool (deterministic, no LLM)

Input: `window` (timeline id), `roster` (character ids). Output: a typed `Context`
of the roster pages + their open relationship edges (unresolved valence), unmet
goals, and any event pinned to the window. Bounded read — no full-canon dump beyond
the window/roster (scoped retrieval discipline).

### Output contract (typed)

```yaml
plot_path:
  window: age_of_cinders
  beats:
    - {actors: [kaelen, voss], moves_tension: {edge: kaelen->voss, toward: confrontation},
       references: [kaelen, voss, ashguard]}
```

Every `references` entry and every `actors`/`edge` id must resolve to canon (gated).

## Acceptance Criteria

- [ ] `retrieve_window(window, roster)` returns a typed `Context` of roster pages +
      open tensions; deterministic (no LLM, no mocks needed); unit-tested against
      the FR-637 seed (RED first).
- [ ] `examples/novel_fandom/graphs/find_path.yaml` lints and runs on the seed canon;
      produces a typed `plot_path` whose every reference resolves to canon.
- [ ] A beat referencing a non-canon entity is caught by `gate_path` and repaired by
      `fix_path` within `loop_limit` (RED test injecting a phantom entity).
- [ ] **Traversal-not-invention:** every beat's actors and moved tensions trace to a
      canon page; the pathfinder introduces no new entities. (Test.)
- [ ] `find_plot_path` prompt is a YAML template (no hardcoded prompt); provider
      resolves from `PROVIDER` env, not a graph constant.
- [ ] Tests tagged `@pytest.mark.req("REQ-YG-XXX")`; capability entry added.
- [ ] `demo-output.log` present showing a gated path over the seed.

## Alternatives Considered

- **LLM reads the whole canon per call** — rejected: unbounded context; use scoped
  `retrieve_window`. (Falls back to Phase-4 index only if canon outgrows context.)
- **Let the pathfinder mint new entities and backfill canon** — rejected: that is the
  FR-550 leak. New entities must be authored into canon first (Phase 1 / future S5).

## Judgement

**Verdict: APPROVED with two required corrections.**

### What's right

1. **Traversal-not-invention is the core thesis.** The pathfinder does not create
   entities — it finds dramatic paths over existing canon tensions. This is the
   inversion that killed the FR-550 leak. The constraint is well-stated and testable.
2. **Scoped retrieval.** `retrieve_window` reads a bounded subset (window + roster),
   not the full canon. Correct discipline — avoids unbounded context and keeps the
   graph runnable on seed-scale canon without Phase 4 (index).
3. **Gate reuse.** The same `ref_gate` checks plot path references resolve to canon.
   No new gate logic — only a new input shape adapter.
4. **Typed output contract.** The `plot_path` schema (window, beats with actors,
   moved_tension, references) is concrete enough to be consumed by FR-639's map node.
5. **Loop limit on fix.** `loop_limit: 2` prevents infinite gate-fix cycling.

### Required corrections

1. **Graph location.** The FR places the graph at `graphs/find_path.yaml` — this is
   wrong. This is an example application graph, not a framework graph. It must live
   at `examples/novel_fandom/graphs/find_path.yaml`, consistent with FR-637's scaffold
   and the C1 scope decision (example, not framework).

2. **`retrieve_window` must be a deterministic Python tool, not an LLM node.**
   The FR already says "deterministic, no LLM" in the description, but the graph
   YAML declares it as `type: python` which is correct. Confirm: no prompt, no
   LLM call — pure filtering over the loaded `data_files` canon. The acceptance
   criteria should explicitly state this is unit-testable without mocks.

### Observations (no action required)

- The `condition: gate_result.ok` syntax differs from FR-628's `gate_result.valid == true`.
  This is a YAML-level convention inconsistency. The enforcer should use whichever
  form FR-628's gate actually emits (`valid`, not `ok`) — or map it.
- The `roundtrip_skeleton.yaml` reference in Related is interesting context but the
  pathfinder is the *inverse* (bottom-up from tensions, not top-down from premise).
  Not actionable — noted for diary.

### Scope freeze

- 1 `retrieve_window` Python tool (deterministic, filters canon by window + roster)
- 1 `find_path` graph YAML (draft → gate → fix loop)
- 1 `find_plot_path` prompt YAML (the one LLM call)
- 1 `fix_plot_path` prompt YAML (repair prompt)
- Tests: window retrieval, traversal-not-invention, phantom-entity rejection
- demo-output.log

Nothing else.

## Related

- [plan-fandom-architecture-2.md](../docs/plan-fandom-architecture-2.md) §2 (S6).
- [plan-fandom-generation.md](../docs/plan-fandom-generation.md) §5 (plotting as traversal).
- [FR-637](./FR-637-novel-fandom-canon-schema-seed.md) — the typed canon this reads.
- [FR-630](./FR-630-loop-exits-end-bug.md) / [FR-631](./FR-631-variable-string-interpolation.md) — loop/template fixes this graph relies on.
- [roundtrip_skeleton.yaml](../examples/plot_modeller/graphs/roundtrip_skeleton.yaml) — the top-down shape this inverts.
