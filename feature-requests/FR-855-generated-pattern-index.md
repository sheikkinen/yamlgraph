# Feature Request: Generated Pattern Index for Examples (node type / feature → precedent)

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-08-22
**First consumer / first event:** the graph-authoring precedent-search
step (doctrine-mandated before any authoring) and any agent asking "find
examples using X" — first event: the next authoring run or
pattern-lookup subagent launch.

## Summary

A generated index of `examples/` keyed by node type and feature —
sibling to `reference/module-map.md`, regenerated the same way — so
precedent lookups become a file read instead of a subagent launch.

## Value Statement

The single most recurrent subagent class (13 launches) is replaced by a
committed, greppable artifact; authoring precedent search gets a
deterministic source.

## Problem

Census evidence (two reads of the full audit trail): cluster C3
"precedent / pattern search" fired 7× and C4 "capability-status
queries" ~5× through 07-28 (`docs/2026-07-29-research-subagent-promotion.md`),
and the 08-22 delta census confirmed continued firing (differentiator /
footprint / integration-pattern research briefs). 13+ total recurrences
— the highest of any cluster. The deliverable is always a lookup, not a
pipeline: "find map node graph examples", "does `type: agent` work
inside `map`?", "every node_config key used". The CAP registry and
examples already contain the answers; the recurring subagent is a
discoverability gap, not missing machinery.

## Ideal Result

An agent needing precedent greps one committed file — examples indexed
by node type, tool type, and notable features (subgraphs, interrupts,
race, checkpointing) with one-line descriptions and paths — and launches
a subagent only when the index has no row. The index never drifts
because CI or pre-commit regenerates/verifies it like the module map.

## Proposed Solution

A generation script (pattern: `scripts/` sibling of the module-map
generator) that walks `examples/**/graph.yaml`, extracts node types,
tool types, and feature flags from the parsed config, and emits
`reference/pattern-index.md` (table: feature → example paths → one-line
description from graph metadata). Drift-checked the same way
`reference/module-map.md` is.

## Acceptance Criteria

- [ ] `reference/pattern-index.md` generated from parsed graph configs,
      covering all `examples/**/graph.yaml`
- [ ] Index rows for at minimum: every node type in `node_factory/`,
      tool types, subgraph/map/race/interrupt usage
- [ ] Drift gate: regeneration check in pre-commit or CI mirrors the
      module-map mechanism
- [ ] Unit test with `@pytest.mark.req(...)` for the extractor
- [ ] Documentation pointer from the graph-authoring doctrine's
      precedent-search step

## Alternatives Considered

- **Keep launching subagents**: 13 recurrences say no; two-strike rule
  exceeded sixfold.
- **LLM-generated index**: rejected — the facts are mechanical (parsed
  YAML); determinism beats prose.

**Prior art:** `docs/2026-07-29-research-subagent-promotion.md`
recommendation 3 (C3+C4) — this FR files it verbatim after it lay
dormant 24 days; `reference/module-map.md` — generation/drift mechanism
reused; FR-853 `Task shapes:` clauses — complementary, different moment
(FR-853 answers planning-time "should this be a graph?", this index
answers authoring-time "show me precedent"); CAP registry — kept, this
index links to it rather than duplicating it.

## Related

- docs/2026-07-29-research-subagent-promotion.md (census, clusters C3/C4)
- feature-requests/FR-853-agent-instrument-registry.md (companion)
- reference/module-map.md (mechanism precedent)
