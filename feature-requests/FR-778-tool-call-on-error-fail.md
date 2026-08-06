# Feature Request: FR-778 — tool_call `on_error: fail`: Prerequisite Failures Fail the Graph

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Enforced 2026-08-06 — AC-01..AC-09 delivered: `on_error` skip/fail in `create_tool_call_node` (fail raises with node+tool+original error, chained), load-boundary rejection via `mode="before"` schema validator (generic field validator otherwise wins for arbitrary values — validator order is contract surface), 13 tests REQ-YG-580 incl. the book1.pdf witnessed regression, docs, changelog, diary. Envelope default byte-identical (pinned by 5 equality tests).
**Effort:** 0.5–1 day
**Requested:** 2026-08-05
**Prior art:** FR-775 (judged, unenforced) adds hand-rolled `gate_probe`/`gate_fetch` python nodes to ONE graph that raise on `success: false` envelopes — the demo-level workaround this FR mechanizes as a framework primitive; FR-778 must not touch FR-775's frozen scope and is not a blocker for it. FR-658 established the tool_call node and its error-text contract for agent loops (AC-9: agent callers must not crash) — that default stays. FR-772 added inline dict args to the same node, untouched here. `on_error: skip|retry|fail|fallback` is the existing per-node contract every other node type honors (CLAUDE.md error handling); tool_call is the outlier.
**First consumer / first event:** the book-summary demo run of 2026-08-05 (tmp/book1.pdf, poppler not installed): `split_document` raised a clear "pdfinfo not found" error, `tool_call` swallowed it into `{success: false, error: ...}`, the graph marched on, and the run died three nodes later with `Map node 'summarize_pages' failed: expression '{state.split_result.result.chunks}' could not be resolved` — a misleading diagnostic pointing at template resolution instead of the missing prerequisite.

## Summary

Add `on_error` support to `tool_call` nodes. Today the node unconditionally
catches every tool exception into a `{success: false, error}` envelope and
lets the graph continue — the only node type that cannot fail the graph.
With `on_error: fail`, a failed tool invocation raises at the node that
caused it, carrying the tool's actual error message.

## Value Statement

Graph authors get "install poppler" as the error instead of a template
resolution failure three nodes downstream; every future tool_call consumer
gets prerequisite-failure hygiene with one line of YAML instead of a
hand-rolled gate node per call site.

## Problem

Witnessed incident (logs/book1-summary.log, 2026-08-05):

1. poppler absent → splitter raises with a precise message.
2. `create_tool_call_node` catches ALL exceptions into the envelope
   (`yamlgraph/node_factory/tool_nodes.py` — `except Exception as e: return
   {state_key: {... "success": False, "error": str(e)}}`).
3. Downstream map resolves `{state.split_result.result.chunks}` → the run
   fails with a template error naming the wrong boundary.

This is the `downstream_fix`/`plausible_wrong_answer` pattern from doctrine:
the fault enters at the tool boundary but manifests at the map boundary.
Commandment 6 forbids silent fallbacks; a success-shaped state update
carrying `success: false` that nothing is forced to check is one.

The envelope default exists for a reason — agent loops must receive error
text rather than crash (FR-658 AC-9) — but deterministic pipelines have the
opposite need, and currently no way to express it. FR-775's judgement
acknowledges this by mandating gate nodes (its R-4) — per-graph boilerplate
for what every other node type gets from `on_error: fail`.

## Ideal Result

A deterministic pipeline writes:

```yaml
nodes:
  split:
    type: tool_call
    tool: split_document
    args: {path: "{state.pdf}", mode: page}
    on_error: fail
    state_key: split_result
```

and a missing prerequisite fails the run AT `split` with the splitter's own
message. Agent-facing and legacy graphs are untouched: the envelope remains
the default.

## Proposed Solution

In `create_tool_call_node` (`yamlgraph/node_factory/tool_nodes.py`):

- Read `on_error = node_config.get("on_error", "skip")` — `skip` names the
  current envelope behavior (continue with `success: false`).
- `on_error: fail`: on unknown tool OR caught exception, raise a
  `ValueError`/`PipelineError` naming the node, the tool, and the original
  error (`raise ... from e`) instead of returning the failure envelope.
  Successful calls return the envelope unchanged — result shape is
  identical on the happy path.
- **Load-time contract (judgement R-1):** for `type: tool_call`, only
  absent, `skip`, and `fail` are valid `on_error` values. `retry`,
  `fallback`, and any arbitrary value fail during **graph load** (not
  merely lint) with an error naming the valid set `skip, fail`. This
  closes the gap where the generic node schema accepts any `ErrorHandler`
  value while only the linter flags unsupported ones.
- Docs: `reference/graph-yaml.md` tool_call properties table gains
  `on_error` with the skip/fail semantics and the agent-vs-pipeline
  guidance.

## Acceptance Criteria (revised per judgement)

- [ ] AC-01: `on_error: fail` on a tool_call node raises at that node when
      the tool callable throws; the raised error contains the node name,
      tool name, and original exception message, preserving exception
      chaining.
- [ ] AC-02: `on_error: fail` raises at that node for an unknown tool name;
      the error contains the node name, requested tool name, and
      "Unknown tool".
- [ ] AC-03: Default (no `on_error`) and explicit `on_error: skip` are
      byte-identical to today's envelope for both callable exceptions and
      unknown tools — existing tests untouched and green.
- [ ] AC-04: Graph load rejects `type: tool_call` with any `on_error`
      outside `skip`/`fail` — including `retry`, `fallback`, and arbitrary
      values — naming the valid set `skip, fail`.
- [ ] AC-05: Unit tests cover AC-01..AC-04, including a regression
      reproducing the witnessed shape: failed envelope + downstream map =
      misleading resolution error; `on_error: fail` = prerequisite named at
      the source.
- [ ] AC-06: A new requirement under
      `capabilities/CAP-05-tool-agent-integration.yaml` owns the behavior
      (judgement R-2 — CAP-05 owns `node_factory/tool_nodes`); all
      new/changed tests carry its `@pytest.mark.req`.
- [ ] AC-07: `reference/graph-yaml.md` documents `tool_call.on_error`;
      changelog fragment added.
- [ ] AC-08: No changes to agent-node tool error handling (FR-658 AC-9),
      FR-658's error-text contract, or FR-775's frozen scope; the
      book-summary graph is NOT migrated here.
- [ ] AC-09: A diary reflection is included (judgement R-3).

## Alternatives Considered

- **Gate nodes per call site (FR-775 R-4)**: correct for FR-775's frozen
  scope, but per-graph boilerplate for a cross-cutting need; this FR is the
  primitive that lets future graphs (and eventually FR-775's successors)
  drop the boilerplate.
- **Make `fail` the default**: rejected — breaks the FR-658 agent contract
  and every existing tool_call consumer; envelope stays default.
- **Splitter-side preflight (check pdfinfo before running)**: fixes one
  tool, not the class; the swallowing happens in tool_call regardless of
  how clearly the tool raises.
- **`verify` block on the demo graph**: detects, but still at a distance
  from the fault boundary; message quality depends on the author.

## Related

- [FR-775-book-summary-loop-redesign.md](FR-775-book-summary-loop-redesign.md) — judged; its gate nodes are the workaround being mechanized
- [FR-658-graph-as-tool.md](FR-658-graph-as-tool.md) — envelope/error-text contract for agent callers (preserved)
- [FR-772-tool-call-inline-dict-args.md](FR-772-tool-call-inline-dict-args.md) — same node, args surface
- yamlgraph/node_factory/tool_nodes.py — the catch-all under change
- logs/book1-summary.log — the witnessed incident
