# Reflection: FR-426 watcher2 Sanity Check

**Date:** 2026-05-20
**FR:** FR-426 Declarative `schema_loader` Tool Type
**Author:** watcher2 post-validate reviewer

## Trap

`framework_costume` — repeated project-local Python loader functions wearing the costume of bespoke behavior, when the underlying pattern was identical across 6+ graphs. The duplication went unnoticed because each copy lived in its own module directory, making the repetition invisible to grep-for-function.

## What Happened

Six callback graphs plus flex_navigator all implemented the same `load_schema()` / `load_and_merge()` logic independently. Each copy diverged slightly (merge order, deduplication key, path anchoring). FR-426 introduced a declarative `type: schema_loader` tool primitive that consolidates this pattern in core, removes the project-local boilerplate, and enforces graph-relative path safety at the framework boundary.

## Root Cause

The gap existed because:
1. `data_files` covered static load-time schemas — not state-driven topic lists.
2. `type: python` required project-local code for every graph — no shared primitive.
3. Tool parsing only recognized `python` and shell types — no typed registry path for schema loading.

The combination meant every graph author wrote their own loader rather than reaching for a framework primitive (because none existed).

## What Worked

- **Prior-art reuse:** `data_loader.py`'s graph-relative path safety (`relative_to` traversal check) was adopted verbatim — no new security logic was invented.
- **Boundary normalization:** Config validation (exactly one of `path`/`paths_from_state`, non-empty `state_key`, required `schema_dir` in merge mode) happens at parse time, not at runtime when a missing file would produce a cryptic error.
- **RED-first discipline:** All 7 acceptance tests were written before implementation (confirmed by Judge note: canonical RED state was `ModuleNotFoundError`). GREEN run: 7/7 passed in 0.36s. Full suite: 3922 passed, 0 regressions.
- **Proportionality:** 281-line implementation file, 271-line test file. Eight AC items, seven test functions (AC-03 and AC-04 share one test per Judge observation — cosmetic, internally consistent). The diff is additive with minimal surgery to `graph_loader.py` (16 lines) and `python_tool.py` (36 lines changed).
- **Traceability complete:** REQ-YG-417, REQ-YG-418, CAP-155, changelog fragment, and ARCHITECTURE.md entries all present.

## Seed

Seed: When a new tool type is added to the registry, the tool config validation lives in `parse_*_tools()` at load time — but downstream callers (node_compiler, map_compiler, agent.py) had to be updated to thread `graph_root` context. Is there a way to make `graph_root` available to all tool callables via a single injection point (e.g., a compile-context object passed once to `_parse_all_tools`) so future tool types never require multi-site threading of context parameters?
