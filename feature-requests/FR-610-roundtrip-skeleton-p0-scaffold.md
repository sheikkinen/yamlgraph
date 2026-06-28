# Feature Request: Round-trip skeleton P0 — scaffold the dry loop

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-06-28

## Summary

Stand up `examples/plot_modeller/graphs/roundtrip_skeleton.yaml` as a lintable, end-to-end
graph with **placeholder nodes**, so the wiring (premise → cast → briefs → draft map →
assemble → gate) is proven before any node is made smart. This is Phase 0 of the walking
skeleton specified in
[plan-roundtrip-phased.md](../examples/plot_modeller/docs/plan-roundtrip-phased.md).

## Value Statement

Graph authors get a frozen, lint-green topology to build into incrementally — every later
phase fills a node rather than re-wiring, so the structural risk is paid down once, up front.

## Problem

The L1–L7 effort was bottom-up: each layer perfected in isolation, and L7 stalled AMBER-RED
*because it was graded alone*. The walking skeleton inverts this — but only if the thin loop
exists first. Without the scaffold, every subsequent phase re-litigates topology.

## Proposed Solution

One graph file, all flow declared in YAML (no Python runner; leaf tools only):

```yaml
# graphs/roundtrip_skeleton.yaml
state: {premise, genre, cast, briefs, drafts, book, coherence}
nodes:
  derive_cast:           # stub: returns a 1-line constant
  outline_chapter_briefs: # stub: returns one brief
  draft_chapter:          # map over briefs (stub prose)
  assemble_book:          # python leaf: ordered concat
  coherence_gate:         # stub: returns {}
edges: linear + map fan-out/fan-in
```

Reuse the Loom synopsis fixture already used by `interiority_ab` (one genre, one seed).

Run shape (no runner):
`PROVIDER=anthropic ANTHROPIC_MODEL=claude-haiku-4-5 .venv/bin/yamlgraph graph run examples/plot_modeller/graphs/roundtrip_skeleton.yaml --var premise=... --full`

## Acceptance Criteria

- [ ] `yamlgraph graph lint examples/plot_modeller/graphs/roundtrip_skeleton.yaml` passes.
- [ ] `graph run ... --full` executes top-to-bottom and reaches END, printing a (stub) book.
- [ ] No `spike_*.py` runner sequences the loop; only leaf tools are Python.
- [ ] Topology frozen — node names and edges match the phased plan.

## Alternatives Considered

Build bottom-up (perfect each node before wiring) — rejected: that is the exact failure mode
the skeleton method exists to avoid.

## Related

- [plan-roundtrip-phased.md](../examples/plot_modeller/docs/plan-roundtrip-phased.md) (P0)
- [plan-roundtrip-skeleton.md](../examples/plot_modeller/docs/plan-roundtrip-skeleton.md) (build spec)
- Successor: FR-611 (P1 cast + briefs)
