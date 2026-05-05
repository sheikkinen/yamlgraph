# Feature Request: FR-331 Static module map for Tier-2 codebase context

**Priority:** MEDIUM
**Type:** Feature
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-05-05

## Summary

Add a deterministic generator (`scripts/generate_module_map.py`) that builds `reference/module-map.md` from `yamlgraph/**/*.py` using stdlib AST analysis, then reference that map from `CLAUDE.md` as always-available structural context.

## Value Statement

Enforcement agents get immediate structural orientation (where modules, exports, dependencies, and related tests are) so sessions spend fewer startup tool calls on repository discovery.

## Problem

Issue #333 reports repeated orientation overhead: enforce sessions begin with multiple exploratory file-system/code-search calls before productive work. The repository ships rich behavioral guidance (`CLAUDE.md`, `.github/copilot-instructions.md`) but no generated structural index for fast codebase navigation.

Without a static Tier-2 map, context loading is slower, token-heavier, and less deterministic across sessions.

## Research: Existing Patterns and Prior Art

1. **No module-map generator exists in current codebase.**
   - No `scripts/generate_module_map.py`.
   - No `reference/module-map.md` (or `.yaml`) artifact.

2. **Stdlib `ast.parse()` is already a trusted pattern in repository tooling.**
   - `scripts/req_coverage.py` parses Python test files with AST.
   - `scripts/hedging_check.py` parses Python source with AST for static analysis.

3. **Current agent context is behavior-heavy, structure-light.**
   - `CLAUDE.md` and `.github/copilot-instructions.md` define process/doctrine and key files, but not a generated module tree with export/dependency/test mapping.

4. **No existing pre-commit hook currently regenerates structural maps.**
   - `.pre-commit-config.yaml` contains many quality hooks, but none for module-map generation.

5. **Topic context and rationale are documented.**
   - `docs/diary/2026-05-05-research-context-building.md` defines Tier 1/2/3 model and proposes static module map as minimal intervention.
   - `docs/diary/2026-05-05-reflection-philosopher-agent-sdk-context-building.md` explains why this is the smallest high-value step before dynamic context selection.

6. **Topic source is explicitly available and aligned with the issue.**
   - Source file read: `/Users/sheikki/Documents/src/yamlgraph/.chaplain/processing/gh-333.md`
   - GitHub issue #333 body matches the same scope and acceptance intent.

## Objectives

1. Produce a deterministic, human-readable structural map for `yamlgraph/` modules.
2. Include key orientation data: exports/signatures, imports/dependencies, and module→test mapping.
3. Make the artifact discoverable from core agent instructions (`CLAUDE.md`) with minimal ongoing maintenance burden.

## Constraints

1. **Single-responsibility scope:** static Tier-2 module map only (no runtime context planner graph).
2. **Parser constraint:** stdlib-only (`ast`), no tree-sitter or new third-party parser dependency.
3. **Architecture constraint:** no changes to graph execution/runtime behavior (`graph_loader`, node factories, executor flow).
4. **Determinism constraint:** stable ordering and reproducible output for identical code state.
5. **Performance constraint:** generation target `< 2s` on repository-scale input.

## Proposed Solution

### In scope

1. Add `scripts/generate_module_map.py` that scans `yamlgraph/**/*.py` and emits `reference/module-map.md`.
2. Extract per-module metadata:
   - relative module path
   - line count
   - exported functions/classes (with signatures where statically available)
   - import dependencies (local/module-level)
3. Add `test_map` section mapping source modules to likely test files under `tests/` (deterministic heuristic documented in script output header).
4. Add explicit reference in `CLAUDE.md` to `reference/module-map.md` (import/reference wording acceptable if consistent with existing docs style).
5. Add focused unit tests for generator/output contracts.

### Out of scope

1. LLM-based relevance classifier (Medium/Full context planner variants).
2. Dynamic per-task context selection orchestration in watcher/enforce graphs.
3. Cross-language indexing beyond Python source under `yamlgraph/`.
4. Mandatory CI/pre-commit auto-regeneration gate (can be follow-up once base artifact quality is validated).

## Acceptance Criteria

- [x] **AC-01:** `scripts/generate_module_map.py` exists and parses `yamlgraph/**/*.py` via stdlib `ast.parse()`.
- [x] **AC-02:** Running the script writes `reference/module-map.md` with deterministic top-level sections: metadata, module index/tree, and `test_map`.
- [x] **AC-03:** Map entries include module path, line count, exported functions/classes, and import dependencies.
- [x] **AC-04:** `test_map` section links modules to corresponding test files using a documented deterministic mapping rule.
- [x] **AC-05:** `CLAUDE.md` includes an explicit reference to `reference/module-map.md`.
- [x] **AC-06:** Script runs with no new third-party dependencies and completes under the `<2s` target in normal local execution.
- [x] **AC-07:** Focused tests are added for script behavior and artifact structure.

## Failing Acceptance Tests (RED)

Create:

- `tests/unit/test_fr331_static_module_map_tier2_context.py`

Planned RED tests:

1. `test_ac01_generator_script_exists_and_uses_ast_parse`
2. `test_ac02_generator_writes_reference_module_map_markdown`
3. `test_ac03_module_entries_include_exports_and_import_dependencies`
4. `test_ac04_output_contains_test_map_section_with_deterministic_mapping`
5. `test_ac05_claude_references_module_map_artifact`
6. `test_ac06_generator_has_no_external_parser_dependencies`

RED command:

```bash
pytest tests/unit/test_fr331_static_module_map_tier2_context.py -q --no-cov
```

Additional RED evidence commands (expected to fail before implementation):

```bash
test -f scripts/generate_module_map.py
test -f reference/module-map.md
rg -n "module-map\\.md" CLAUDE.md
```

## Alternatives Considered

1. **Keep runtime-only discovery (grep/read/list)**
   - Rejected: preserves token/latency overhead and non-deterministic orientation behavior.

2. **Implement full context planner now (module map + LLM relevance classifier)**
   - Rejected for this FR: broader scope; static map is the minimal independently judgeable step.

3. **Use tree-sitter or richer parser stack**
   - Rejected: unnecessary dependency/cost for current Python-only indexing goal; stdlib AST already established in repo tooling.

4. **Manual curated module map documentation**
   - Rejected: drifts quickly and is harder to maintain than generated output.

## Related

- GitHub issue #333: <https://github.com/sheikkinen/yamlgraph/issues/333>
- `docs/diary/2026-05-05-research-context-building.md`
- `docs/diary/2026-05-05-reflection-philosopher-agent-sdk-context-building.md`
- `scripts/req_coverage.py`
- `scripts/hedging_check.py`
- `.pre-commit-config.yaml`
- `CLAUDE.md`
- Topic source: `/Users/sheikki/Documents/src/yamlgraph/.chaplain/processing/gh-333.md`
