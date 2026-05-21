# Diary: FR-444 Watcher2 Sanity-Check Reflection

**Date:** 2026-05-21
**FR:** FR-444 — Graph Loader Strict Mode for Python Tool Load Failures
**Reviewer:** watcher2 (post-validate)

## Trap

`downstream_fix` — the original warn-and-continue pattern in `_parse_all_tools()` let broken Python tool imports surface as opaque "Unknown tool" runtime errors instead of compile-time failures. The fix (strict by default) correctly normalises at the boundary where the tool enters the registry, not at the `tool_call` node where the symptom appeared.

## What Happened

FR-444 introduced `config.tool_load_mode: strict | warn` in `GraphConfig`, defaulting to strict. The diff is tightly scoped: 26 lines changed in `graph_loader.py`, accumulating all load failures before raising one actionable `ValueError`. The RED/GREEN test file covers AC-01 through AC-04 with behavioural assertions (raises, message content, runtime `success=False`, `caplog`-style `mock.warning`). All 4 tests pass in 0.22 s.

## Root Cause

The original behaviour prioritised graph-compilation resilience over fail-fast feedback. There was no compile-time contract for tool-load failures, so graph authors had no mechanism to detect broken Python tool wiring before runtime.

## What Worked

- Accumulating failures before raising gives graph authors a single, complete compile error listing every broken tool — no need to fix-one-then-retry.
- Invalid `tool_load_mode` values are validated eagerly in `GraphConfig.__init__`, so typos are caught before any tools are loaded.
- REQ-YG-420/421 traceability, changelog fragment, CAP-157 capability file, and `ARCHITECTURE.md` updates are all present; the pipeline audit chain is satisfied.

## Pipeline Log Evidence

The referenced pipeline log (`fsm-pipeline-inquisitor-wip-main-gate-20260520-083933.log`) is from a prior run (a different PR that hit a CI timing issue). It is not directly related to this branch; no FSM log specific to this worktree was found.

## Verdict

**PASS** — proportionality, test quality, and FR/code alignment are all acceptable.

## Seed:

If a graph declares `tool_load_mode: strict` but ships with optional Python tools that are only needed in certain deployment environments, can the YAML schema support a `required: false` field on individual tools to exempt them from strict-mode failures — and what would that contract look like in the context of the existing `_parse_all_tools()` accumulation loop?
