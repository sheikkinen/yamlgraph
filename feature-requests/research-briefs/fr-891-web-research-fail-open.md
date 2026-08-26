# Problem brief: demo graph reports success while its only grounding tool failed every call

**Prior art:** dispositioned in FR-891 (closed-input brief per FR-890 R-2;
fr-888-problem-brief.md is the sibling precedent, different problem class).

## Problem statement

A shipped demo graph (`examples/demos/web-research`) completed with exit
code 0 and produced a fluent, plausible research summary although its only
grounding tool failed on every invocation. The tool converts all failure
modes (missing dependency, network error, empty results) into English
error strings returned as normal tool output. The agent node consumed six
such error strings as if they were research results and logged
"✓ Agent completed". The downstream summarize node synthesized a
market-map narrative from no data. The final artifact contained zero
external citations yet was shape-indistinguishable from a successful run;
only a human reading the raw output caught it (the model itself confessed
mid-text that search had failed, but nothing mechanical acted on the
confession). The same tool is shared by other graphs; any consumer without
its own output-verification boundary inherits the same fail-open behavior.

## Classification

enforcement/latency-critical

## Constraints

- Commandment 6 (Scripture): no silent fallbacks; when a tool yields
  nothing, the fault must be exposed, never substituted with fluent output.
- Three-layer architecture: the tool is a Layer 3 side-effect module; the
  agent loop is framework code; the demo graph is YAML logic. The fix must
  respect layer boundaries (import-linter enforced).
- Agent tools return strings to the LLM by LangChain convention; any change
  to failure signaling must state where the string convention ends and
  hard failure begins.
- `PipelineError` and per-node `on_error: skip|retry|fail|fallback`
  already exist as the framework's error primitives.
- Demos are enforced by demo-gate (demo-output.log proves execution); a
  fix must not make the committed demo log a lie.
- The dependency involved is an optional extra; environments legitimately
  exist without it.

## Witnessed incidents

- 2026-08-26, `research/mercury-census/runs/run-grounded-FAILED-OPEN.log`:
  6/6 tool calls returned "Error: ddgs package not installed"; agent
  completed "successfully" after 5 iterations; summary emitted with zero
  URL-bearing citations; exit code 0. Verified: all 7 `http` matches in
  the artifact are API log lines, none are citations.
- Contrast (same tool, same day): FR-890's research-route librarian wraps
  the identical tool but its LLM-free reducer and wrapper fail closed on
  error strings and missing URLs (R-4) — the graph-level boundary caught
  what the demo graph lets through.
