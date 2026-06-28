# Feature Request: Round-trip skeleton P0 — scaffold the dry loop

**Priority:** MEDIUM
**Type:** Feature
**Effort:** 0.5 days
**Requested:** 2026-06-28
**Status:** Judged — Authority GRANTED (2026-06-28)

## Summary

Stand up `examples/plot_modeller/graphs/roundtrip_skeleton.yaml` as a lintable, end-to-end
graph with **placeholder nodes**, so the wiring (premise → cast → briefs → draft map →
assemble → gate) is proven before any node is made smart. This is Phase 0 of the walking
skeleton specified in
[plan-roundtrip-phased.md](../examples/plot_modeller/docs/plan-roundtrip-phased.md).

## Value Statement

Graph authors get a frozen, lint-green topology to build into incrementally — every later
phase fills a node rather than re-wiring, so the structural risk is paid down once, up front.

## Judgement (2026-06-28)

**Verdict: Authority GRANTED.** P0 carries no measurement and is buildable now. This is the
authority gate for Phase 0 of the chain.

**Claims verified.** The reuse assets exist: `graphs/interiority_ab.yaml`,
`prompts/interiority/derive_cast.yaml` + `interiority_sheets.yaml`, and the Loom synopsis fixture
`fixtures/synopses/scifi-hybrid-the-loom.txt` (+ its ground-truth). The skeleton method — freeze
the spine before any node is smart — is the correct inversion of the bottom-up L1–L7 failure that
stalled L7 by grading it in isolation. The structural risk is paid down once, up front; sound.

**Correction 1 (PRIMARY).** "Topology frozen" must mean the P0 **spine**
(premise → cast → briefs → draft-map → assemble → gate) does not re-wire — **not** that no node
may ever be added. P5 ([FR-615](FR-615-roundtrip-skeleton-p5-roundtrip-closure.md)) adds
`reconstruct_synopsis`, `roundtrip_diff`, and a comparison-side `classify_scene_type`. If the
AC's "frozen" forbids additive nodes, P0 contradicts P5. Restate the freeze as **spine
immutability with additive extension permitted off the critical path**.

**Correction 2 (secondary).** The stub `coherence_gate` returns `{}` and the stub draft is prose-
free, so the END-reachable AC is satisfiable while the fan-in is a no-op. The DoD "prints a stub
book" should assert the `assemble_book` leaf actually concatenated the map output (non-empty,
ordered) — otherwise P0 can go green with a broken map fan-in that only surfaces in P2.

**Frozen scope.** Lint-green spine + END reached + `assemble_book` is a real deterministic concat.
No smart nodes. Additive nodes in later phases do not violate the freeze.

## Decision fold (2026-06-28) — brief state carries the authored affect arc (option a)

The chain adopts **option (a)** (closure measured structurally over the authored briefs). Two small
P0 consequences:
- The `briefs` state key must accommodate per-chapter `scene_type` + `eff_affect` (authored affect
  open/close ops) that P1 fills — reserve the shape now so P1 is purely additive.
- "Topology frozen" means **spine immutability** (premise → cast → briefs → draft-map → assemble →
  gate does not re-wire), **with additive nodes permitted off the critical path** (resolving Judge
  Correction 1; P5 adds `reconstruct_synopsis`/`roundtrip_diff` without violating the freeze).

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
