# Feature Request: FR-723 Execution Path Visualization — Route Hook + Mermaid Export + Overlay

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 2 days
**Requested:** 2026-07-14
**Prototype:** ninchat_voice NC-372 (generated map, drift-gated) + NC-373 (route facts, overlay, occurrence-aligned diff) — enforced 2026-07-14; this FR ports the proven design to the framework boundary
**Related:** CAP-06 (routing), CAP-09 (CLI), CAP-10 (export), CAP-13 (tracing — explicitly NOT the mechanism)

## Summary

Three pieces making every graph's executed path visible: (1) an opt-in
**route decision hook** emitting one structured log line per routing
decision at the single seam where all decisions happen
(`routing.py`); (2) `yamlgraph graph export --mermaid` rendering the
**authored** graph (nodes, conditions, loop limits, interrupts); (3)
`--overlay <route.jsonl>` rendering an executed route on that map with
occurrence ordinals. Every graph in `examples/` becomes path-visible
with zero per-project code.

## Value Statement

Every example, demo, and downstream project (35 example dirs today;
dungeon_master chapter loops, plot_modeller validator-retry loops,
icpc-2-rfe) gets "how did this run route?" as one command instead of a
per-project logging retrofit — and misroute debugging becomes a diff.

## Problem — the per-project approach is proven fragile

ninchat_voice built this project-locally (NC-357/372/373). The enforce
log is the condemning evidence for doing it at the framework boundary
instead:

1. **The missing fifth seam** (ninchat 99edb4e): project-side emission
   requires manually enumerating deciding seams; NC-373 missed one on
   day one. Every future conditional edge silently lacks route facts
   until someone remembers.
2. **The missing sixth seam, found writing this FR:** `expr_router_fn`
   L79–80 loop-limit exit is a routing decision (`loop_exit` →
   target/END) that ninchat's per-seam emission never captured — loop
   exhaustion routes are invisible in its overlays.
3. Both defects vanish when emission lives where every decision is
   evaluated: `routing.py` (103 lines, two router fns +
   `evaluate_condition`). Normalize at the boundary where the decision
   enters existence.

LangSmith is not the mechanism (NC-373 ruling stands): spans are
post-hoc, race/zombie-polluted (FR-713/NC-367), and unavailable for
exactly the dead runs where the route matters most.

## Proposed Solution

### 1. Route decision hook (`routing.py`, opt-in)

- Both router fns + the loop-exit path emit via a dedicated logger
  (`yamlgraph.route`), one JSON line per decision:
  `{"event":"route","node":<source>,"value":<matched condition|loop_exit>,"target":<target>,"thread_id":<from config>}`
- **Opt-in** by env (`YAMLGRAPH_ROUTE_LOG=1`) or graph-YAML flag
  (`observability.route_log: true`) — zero overhead when off (guard
  before serialization).
- Values are the matched condition string / target names — framework
  metadata, never state content (privacy bounded by construction).
- Emission never raises (forensic-channel discipline: a log line must
  not break the run).

### 2. `yamlgraph graph export --mermaid <graph.yaml>`

- Renders the **authored** YAML: nodes (type-annotated: llm/race/
  tool/map), edges with condition labels by reference, loop limits,
  interrupt nodes marked. Conditions-as-authored, not the compiled
  LangGraph view (`draw_mermaid()` renders Send fan-outs and internal
  names — documented as the rejected alternative).
- Pure function of the YAML: stdlib + yaml, no LLM, no API keys — safe
  for pre-commit use by downstream projects.

### 3. `--overlay <route.jsonl>` + `--diff a.route b.route`

- Overlay: taken edges highlighted (`classDef taken`), **decision
  ordinals preserved** — a reader must be able to reconstruct the
  ordered route from the render (ninchat's projection-at-the-last-mile
  lesson: counts alone violate `assert_path_not_destination` in the
  tool that exists to serve it; condemning test required).
- Diff: occurrence-aligned per `(node, occurrence_index)` (NC-373 R-3
  — naive positional diff misaligns after the first divergence in a
  loopy route). Empty diff = the cheap determinism witness.

### Migration note (ninchat_voice, separate NC)

Once this lands, ninchat's five `emit_route` calls become a shim over
framework events and MUST be deleted (no-shims commandment); its
overlay parser consumes the framework grammar; its project-local
pieces (facts channel for topics/extracted/delivery, death markers,
schema sidecar, utterance inventory) remain project-local — they are
domain, not graph semantics.

### Out of scope (purge list)

- HTML/interactive viewers, animation.
- LangSmith-derived routes (rejected above).
- Emitting state content in route lines.
- Auto-rendering inside `graph run` (presentation stays out of the
  execution path; the CLI export is the consumer).

## Raw Output Read

- **Samples read:** ninchat_voice `logs/coordinator.log` route-fact
  lines from the NC-373 enforce (scripted fixture runs); its rendered
  overlays in `logs/persona-tests/`; `routing.py` L36–44, L74–93.
- **What I saw:** the loop-exit branch (L79) returns a route with NO
  emission possible in the project-local design — ninchat's overlays
  show probe loops that "vanish" at exhaustion rather than routing to
  recap; the framework hook closes a hole the prototype could not see
  from outside. A generated dump would not contain this asymmetry.

## Acceptance Criteria

- [ ] AC-01 RED — unit: with route log enabled, a fixture graph run
      emits one line per conditional decision INCLUDING a loop-limit
      exit; disabled ⇒ zero lines and no serialization cost (mock
      assert).
- [ ] AC-02 Export: `graph export --mermaid` on 3 representative
      example graphs (one loopy, one map fan-out, one router node)
      produces syntactically valid Mermaid containing every authored
      node and condition label exactly once.
- [ ] AC-03 Overlay: fixture run's route.jsonl renders taken edges +
      ordinals; ordered route reconstructible from the render alone
      (condemning test: counts-only render fails).
- [ ] AC-04 Diff: occurrence-aligned; same-input temp-0 rerun ⇒ empty
      diff; altered fixture ⇒ diff names seam and Nth firing.
- [ ] AC-05 Demo: one example (`examples/demos/` or dungeon_master
      chapter) run + export + overlay committed as demo-output.log
      (demo gate).
- [ ] AC-06 New REQ under CAP-06 (hook) and CAP-10 (export); changelog
      fragment; docs in reference/graph-yaml.md (observability flag)
      and CLI reference.

## Alternatives Considered

- Per-project emission (ninchat prototype) — proven fragile twice
  (missing fifth seam day one; loop-exit seam invisible by
  construction).
- LangGraph `get_graph().draw_mermaid()` — compiled view, loses
  authored conditions; documented cross-check only.
- LangSmith callbacks — post-hoc, polluted, absent for dead runs.
- Always-on route log — violates zero-overhead default; opt-in flag.
