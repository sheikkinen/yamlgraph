# Reflection: FR-375 `graph run --json` stdout mode + TypeScript Node.js demo

**Date:** 2026-05-13
**FR:** FR-375
**Branch:** feat/watcher2-gh-375

## Cognitive Process

The task decomposed cleanly into two concerns: adding `--json` to the CLI and producing a TypeScript subprocess demo. The serializer reuse constraint (`_serialize_state()`) kept the implementation surface small.

## Traps Encountered

**stdout purity trap.** The hardest constraint was AC-03: stdout must contain *only* valid JSON in `--json` mode. The existing `cmd_graph_run()` writes progress lines, RESULT headers, timing summaries, and token counts to stdout. A naïve flag addition would have produced polluted JSON. The correct fix was to extract a `graph_run_helpers.py` module and route every non-payload line through `sys.stderr` in JSON mode — normalizing at the output boundary, not patching individual print calls.

**Interrupt interaction.** The `--json` mode must be non-interactive. The existing interrupt handler calls `input()` to ask the user for a command. Letting that happen in JSON mode would hang a subprocess consumer. The guard had to be explicit: detect `__interrupt__` in state *before* any interactive loop and exit non-zero.

**Demo gate alignment.** The `demo-output.log` requirement (demo-gate) is easy to miss when the demo runs against a live LLM. The file had to be committed alongside `demo.sh` with representative output.

## Heuristic

> **Stdout is a typed channel.** When adding a machine-readable mode to a CLI, treat stdout as a contract boundary — normalize at the entry point of every write, not at each individual call site.

This is the same law as "normalize at the boundary where external data enters" applied to *output* direction.

## Seed

When `--json` mode and `--stream` mode are both desired (streaming JSON events), what is the right envelope format — newline-delimited JSON (ndjson) vs SSE vs JSON array? And should the interrupt payload be emittable as a structured event rather than a non-zero exit?
