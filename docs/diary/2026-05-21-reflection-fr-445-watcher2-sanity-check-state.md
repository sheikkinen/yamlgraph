# Reflection: FR-445 Watcher2 Sanity-Check

**Date:** 2026-05-21
**FR:** FR-445 — Python Tool Path Root Confinement
**Reviewer:** watcher2 (post-validate sanity)

## Trap

`downstream_fix` — the old code silently resolved tool paths relative to CWD, meaning errors surfaced only at execution time in unpredictable directories. The correct cure was to normalize at the entry boundary (`load_python_function`) rather than guarding downstream node execution.

## What Happened

`yamlgraph/tools/python_tool.py` resolved `config.path` with `Path(config.path).resolve()` — CWD-relative, unconfined. The fix extracted path resolution into `_resolve_python_tool_path()`, applying `graph_root`-relative resolution and `resolved.relative_to(root)` rejection, mirroring the existing `schema_loader_tool.py` boundary pattern exactly. Requirement text in `ARCHITECTURE.md`, `CAP-75-portable-chaplain.yaml`, and `reference/module-map.md` updated to reflect graph-root semantics. Changelog fragment added. 11 tests pass: 5 new RED acceptance tests (AC-01–05 via `load_and_compile`) plus 6 existing `test_python_nodes` regression tests.

## Root Cause

`graph_root` was already threaded through every call site (`graph_loader`, `node_compiler`, `map_compiler`, `tools/agent`) but was ignored for path boundary validation inside `load_python_function`. The fix was purely local to `python_tool.py` — no call-site changes required.

## What Worked

- Mirroring the `schema_loader_tool._resolve_schema_path()` pattern — same `relative_to()` guard, same error message structure — removed any design uncertainty.
- Acceptance tests using `load_and_compile()` confirmed compile-time enforcement (AC-06) rather than just unit-testing the helper function in isolation.
- `graph_root=None` fallback to CWD is retained for call sites that genuinely lack graph context, preserving compatibility without a silent security hole — confinement only applies when `graph_root` is explicitly provided.
- Pipeline log confirms clean FSM progression: `enforce_session --enforce_done--> micro_changelog --changelog_done--> micro_title --title_done--> sanity_check` with enforce exit code 0 after ~630 s.

## Seed:

If every file-referencing tool type (`python`, `schema_loader`, future `data_loader`) independently implements boundary enforcement, the pattern will drift across files. Should boundary normalization be elevated to a shared `resolve_within_root(path, graph_root)` utility in `yamlgraph/utils/`, tested once, and imported by all tool loaders — so the boundary contract has a single source of truth rather than three copies?
