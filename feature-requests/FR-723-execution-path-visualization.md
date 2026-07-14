# Feature Request: FR-723 Execution Path Visualization — Route Hook + Mermaid Export + Overlay

**Priority:** MEDIUM
**Type:** Feature
**Status:** Completed (enforced 2026-07-14)
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
  `{"event":"route","node":<source>,"value":<matched condition|loop_exit>,"target":<target>,"thread_id":<or null>}`
- **thread_id mechanism (R-1):** router fns receive `state` only — the
  thread id lives in `config["configurable"]`, unreachable from the seam.
  Mechanism: a **contextvar** set by the executor/run entrypoints around
  graph invocation (zero signature churn; serves any future seam).
  Fallback consideration: LangGraph's `(state, config)` conditional-edge
  signature if the pinned version supports it. Absent both, the field is
  emitted as **`null` — never fabricated**.
- **Map fan-out targets (R-2):** when the decision returns `Send` objects,
  the line carries the **map-node name + fan-out count**
  (`{"target":"process_items","fan_out":4}`) — never `repr(Send)`, whose
  payloads carry state content (the privacy rule made structural).
- **Opt-in** by env (`YAMLGRAPH_ROUTE_LOG=1`) or graph-YAML flag
  (`observability.route_log: true`) — zero overhead when off (guard
  before serialization).
- Values are the matched condition string / target names — framework
  metadata, never state content (privacy bounded by construction).
- Emission never raises (forensic-channel discipline: a log line must
  not break the run).
- The `yamlgraph.route` logger namespace is **public API** — documented as
  the attach point for downstream handlers/filters.

### 2. `yamlgraph graph export --mermaid <graph.yaml>`

- Renders the **authored** YAML: nodes (type-annotated: llm/race/
  tool/map), edges with condition labels by reference, loop limits,
  interrupt nodes marked, **and the loop-exit edge rendered explicitly**
  (`loop_exit → <target>`) — the hole this FR closes deserves visibility
  on the authored map, not only in route lines. Conditions-as-authored,
  not the compiled LangGraph view (`draw_mermaid()` renders Send fan-outs
  and internal names — documented as the rejected alternative).
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

### Migration note (ninchat_voice, separate NC — R-3: filed BEFORE this FR merges)

Once this lands, ninchat's five `emit_route` calls become a shim over
framework events and MUST be deleted (no-shims commandment); its
overlay parser consumes the framework grammar; its project-local
pieces (facts channel for topics/extracted/delivery, death markers,
schema sidecar, utterance inventory) remain project-local — they are
domain, not graph semantics.
**Grammar compatibility fact for the NC:** ninchat's parser keys on
`call_sid` in `📋 FACTS:`-prefixed lines; the framework emits
`event:route` JSON on `yamlgraph.route` with `thread_id`. ninchat already
invokes with `thread_id=call_sid`, so the shim is a prefix/field rename —
small by design. The NC is filed (not enforced) as an AC-06 deliverable;
without it the shim lingers and no-shims is violated by omission.

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

- [x] AC-01 RED — unit: with route log enabled, a fixture graph run
      emits one line per conditional decision INCLUDING a loop-limit
      exit, a **simple-router decision** (`make_router_fn`), and a **map
      fan-out** (name + count, no state content — R-2's privacy
      assertion testable); route lines carry the invoking `thread_id`
      (or `null`, never fabricated — R-1); disabled ⇒ zero lines and no
      serialization cost (mock assert — **load-bearing: this hook rides
      every conditional edge of every graph; enforce this first**).
      → `tests/unit/test_route_log.py` (zero-overhead test leads the file);
      RED commit ef938d80.
- [x] AC-02 Export: `graph export --mermaid` on 3 representative
      example graphs (one loopy, one map fan-out, one router node)
      produces syntactically valid Mermaid containing every authored
      node and condition label exactly once, loop-exit edges rendered.
      → reflexion / map / router demos in `tests/unit/test_mermaid_export.py`.
- [x] AC-03 Overlay: fixture run's route.jsonl renders taken edges +
      ordinals; ordered route reconstructible from the render alone
      (condemning test: counts-only render fails).
      → `test_overlay_route_reconstructible_from_render`.
- [x] AC-04 Diff: occurrence-aligned; same-input temp-0 rerun ⇒ empty
      diff; altered fixture ⇒ diff names seam and Nth firing.
      → `diff_routes` keyed per `(node, occurrence)`; CLI exits 1 on divergence.
- [x] AC-05 Demo: one example (`examples/demos/` or dungeon_master
      chapter) run + export + overlay committed as demo-output.log
      (demo gate). → `examples/demos/reflexion/demo-output.log`: live run
      routed refine→refine→END at score 0.85, thread_id `fr723-demo`
      carried, self-diff "routes identical".
- [x] AC-06 New REQ under CAP-06 (hook) and CAP-10 (export); changelog
      fragment; docs in reference/graph-yaml.md (observability flag)
      and CLI reference incl. the `yamlgraph.route` public logger
      namespace; **ninchat migration NC filed before merge (R-3)**.
      → REQ-YG-552 (CAP-06), REQ-YG-553 (CAP-10) — renumbered from the
      FR's draft 551/552: CAP-203 (FR-724, landed first) owns 551 per the
      allocation-race rule; ninchat NC-374 filed.

## Implementation Record (2026-07-14)

- **Seam:** `yamlgraph/utils/route_log.py` (emitter, contextvar, opt-in
  guards, file sink) + emission wired into `routing.py` at all decision
  points: simple-router match/default, expression match, map fan-out
  (Send count taken before return — R-2), loop-limit exit, no-match
  fallthrough. `make_router_fn` gained a required `source_node` arg for
  attribution (callsite: edge_compiler).
- **R-1 delivered as ruled:** contextvar set by
  `route_thread_id_from_config()` at three entrypoints — CLI
  `_invoke_graph`, `run_graph_async`, `run_graph_streaming_native`.
- **Env extension (decision):** `YAMLGRAPH_ROUTE_LOG=<path>` attaches a
  raw-JSONL file handler in addition to the logger — the smallest
  mechanism giving the CLI an end-to-end route.jsonl story without a new
  flag; `=1` remains logger-only as pinned.
- **Export:** `yamlgraph/mermaid_export.py` (pure stdlib+yaml, registered
  in the `.importlinter` Layer-2 contract) + `yamlgraph/cli/export_commands.py`.
  Authored view only; `draw_mermaid()` remains the rejected alternative.
- **Deviations:** none of substance; module-map line budget bumped
  265→270 (three judged new modules, precedent FR-677/716/719) and the
  FR-716 pin on executor_async honoured by trimming a stale docstring
  example rather than relaxing the gate.

## Alternatives Considered

- Per-project emission (ninchat prototype) — proven fragile twice
  (missing fifth seam day one; loop-exit seam invisible by
  construction).
- LangGraph `get_graph().draw_mermaid()` — compiled view, loses
  authored conditions; documented cross-check only.
- LangSmith callbacks — post-hoc, polluted, absent for dead runs.
- Always-on route log — violates zero-overhead default; opt-in flag.
