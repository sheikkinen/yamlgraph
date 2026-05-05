# Feature Request: FR-335 Compress static module map output

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-05-05

## Summary

Compress `reference/module-map.md` generation so the artifact stays agent-readable (<=250 lines) by filtering dependency noise to internal `yamlgraph.*` imports, collapsing trivial `__init__.py` modules, and switching verbose multi-line lists to compact one-line fields.

## Value Statement

Enforcement agents get a concise Tier-2 orientation artifact they can actually read at session start, reducing startup search/tool churn.

## Problem

FR-331 introduced a deterministic module-map generator, but the generated output is currently 1511 lines, far above the intended ~100-200 line budget. At this size, the map is often skipped by agents, which defeats the purpose of adding it.

Current bloat sources:

1. dependency lists include stdlib/third-party imports (`logging`, `pathlib`, `typing`, etc.) instead of internal dependency signal
2. trivial `__init__.py` modules still emit full multi-line blocks
3. exports/dependencies are rendered as nested bullets instead of compact single-line lists

## Research: Existing Patterns and Prior Art

1. **Current implementation is verbose by design.**
   - `scripts/generate_module_map.py` renders per-module `###` sections with nested bullets for exports and dependencies.
   - `_extract_dependencies()` currently returns all import roots (including stdlib and third-party), which inflates output.

2. **The size problem is reproducible in this branch.**
   - `reference/module-map.md` currently has 1511 lines (`wc -l`).

3. **Compression is not already solved elsewhere in the codebase.**
   - No alternative module-map generator exists.
   - No post-processing/compression step exists for `reference/module-map.md`.

4. **Constraint-compatible parser approach already exists.**
   - `scripts/generate_module_map.py`, `scripts/req_coverage.py`, and `scripts/hedging_check.py` use stdlib `ast.parse()`.
   - This supports a no-new-dependencies compression pass.

5. **Feature lineage is clear.**
   - Parent FR: `feature-requests/FR-331-static-module-map-tier2-context.md`
   - Reflection context: `docs/diary/2026-05-05-reflection-fr-331-static-module-map.md`
   - Topic source read: `/Users/sheikki/Documents/src/yamlgraph/.chaplain/processing/gh-335.md`
   - GitHub issue: #335

6. **RED acceptance surface already exists and currently fails where expected.**
   - `tests/unit/test_fr335_module_map_compression.py` is present.
   - Running `pytest tests/unit/test_fr335_module_map_compression.py -q --no-cov` currently fails AC-01/02/03 and passes AC-04/05.

## Objectives

1. Bring generated `reference/module-map.md` to <=250 lines.
2. Keep dependency lists focused to internal module graph signal (`yamlgraph.*` only).
3. Preserve module coverage while reducing noise (collapse trivial module sections).
4. Define a deterministic compact rendering contract for trivial modules and one-line dependency/export fields.
5. Preserve FR-331 contract behavior and stdlib-only implementation.

## Constraints

1. **Single responsibility:** output compression for static module-map generator only.
2. **No runtime behavior changes:** no watcher/graph execution pipeline changes.
3. **No dependency additions:** `scripts/generate_module_map.py` remains stdlib-only.
4. **Determinism preserved:** output ordering and shape remain reproducible.
5. **Compatibility guard:** existing FR-331 acceptance tests must continue to pass.

## Proposed Solution

### In scope

1. Update `scripts/generate_module_map.py` to filter dependency output to internal imports rooted at `yamlgraph` (canonicalized to `yamlgraph.*`).
2. Detect trivial modules (`__init__.py` with `<10` lines and `<=1` public export) and render them as compact one-line entries (e.g. `- yamlgraph/path/__init__.py - 4 lines; exports: _none_`) instead of `###` module sections.
3. Render exports and dependencies in compact single-line form (e.g. `- exports: func1(), class Foo` and `- import dependencies: yamlgraph.mod1, yamlgraph.mod2`), replacing nested bullet lists.
4. Regenerate `reference/module-map.md` with the compressed format.
5. Add focused RED acceptance tests for compression and non-regression constraints.

### Out of scope

1. Dynamic/task-adaptive context planning.
2. Non-Python module indexing.
3. Replacing AST parsing with external parser stacks.
4. New CI/pre-commit policy changes beyond this output contract.

## Acceptance Criteria

- [x] **AC-01:** Running `python scripts/generate_module_map.py` regenerates `reference/module-map.md` at <=250 lines.
- [x] **AC-02:** Dependency lists in the generated map contain only internal `yamlgraph` dependencies.
- [x] **AC-03:** Trivial modules (`__init__.py`, `<10` lines, `<=1` public export) are rendered as single-line entries and are not rendered as full `###` multi-line module sections.
- [x] **AC-04:** Existing FR-331 acceptance tests continue to pass unchanged.
- [x] **AC-05:** `scripts/generate_module_map.py` remains stdlib-only (no new third-party imports/dependencies).

## Failing Acceptance Tests (RED)

Existing RED suite:

- `tests/unit/test_fr335_module_map_compression.py`

Planned RED tests:

1. `test_ac01_regenerated_module_map_stays_within_line_budget`
2. `test_ac02_dependency_lists_contain_only_yamlgraph_imports`
3. `test_ac03_trivial_init_modules_are_not_rendered_as_verbose_sections`
4. `test_ac04_existing_fr331_acceptance_tests_still_pass`
5. `test_ac05_generator_script_remains_stdlib_only`

RED command:

```bash
pytest tests/unit/test_fr335_module_map_compression.py -q --no-cov
```

## Alternatives Considered

1. **Keep FR-331 output as-is**
   - Rejected: map remains too large to serve its intended orientation role.

2. **Drop dependency lists entirely**
   - Rejected: removes useful architecture signal that the map was meant to provide.

3. **Split output into multiple files**
   - Rejected for this FR: adds indirection without fixing core verbosity in the primary artifact.

4. **Adopt richer external parser tooling**
   - Rejected: unnecessary dependency/cost for this compression-only pass.

## Related

- Topic source: `/Users/sheikki/Documents/src/yamlgraph/.chaplain/processing/gh-335.md`
- GitHub issue #335: <https://github.com/sheikkinen/yamlgraph/issues/335>
- Parent: `feature-requests/FR-331-static-module-map-tier2-context.md`
- Generator: `scripts/generate_module_map.py`
- Artifact: `reference/module-map.md`
- Existing tests: `tests/unit/test_fr331_static_module_map_tier2_context.py`
- Reflection: `docs/diary/2026-05-05-reflection-fr-331-static-module-map.md`
