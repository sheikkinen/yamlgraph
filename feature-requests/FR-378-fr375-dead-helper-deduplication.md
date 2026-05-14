# Feature Request: FR-378 FR-375 dead helper deduplication (`_handle_optional_exports`)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-14

## Summary

Remove the dead duplicate `_handle_optional_exports` implementation introduced during FR-375 refactor by keeping a single canonical implementation in `yamlgraph/cli/graph_run_helpers.py` and aliasing it from `yamlgraph/cli/graph_commands.py`.

## Value Statement

CLI maintainers get a cleaner `graph run` helper boundary with one source of truth for optional export behavior, reducing entropy and future regression risk.

## Problem

FR-375 split `graph run` helpers into `graph_run_helpers.py`, but `_handle_optional_exports` now exists in both modules:

1. `yamlgraph/cli/graph_commands.py` defines `_handle_optional_exports` locally and calls it.
2. `yamlgraph/cli/graph_run_helpers.py` also defines `_handle_optional_exports`, but it is not used.

This contradicts the refactor intent ("helpers live in `graph_run_helpers.py` and are re-exported/aliased in `graph_commands.py`"), leaving dead duplicate logic.

## Research: Existing Patterns, Prior Art, and Findings

1. **Topic source discovered outside worktree mirror**
   - Requested file `.chaplain/processing/gh-378.md` is not present in this worktree.
   - Canonical topic file exists at `/Users/sheikki/Documents/src/yamlgraph/.chaplain/processing/gh-378.md`.

2. **Duplication confirmed in production code**
   - `yamlgraph/cli/graph_commands.py:41` defines `_handle_optional_exports`.
   - `yamlgraph/cli/graph_run_helpers.py:250` defines `_handle_optional_exports`.
   - Only `graph_commands.py` calls `_handle_optional_exports` (`graph_commands.py:148`).

3. **Refactor pattern in this module family**
   - `graph_commands.py` already aliases neighboring helpers from `graph_run_helpers` (`_setup_timeout`, `_teardown_timeout`, `_emit_success_output`, etc.).
   - `_handle_optional_exports` is the outlier that remained locally re-implemented.

4. **Dead-code governance precedent**
   - FR-162 and FR-278 establish vulture-first cleanup with explicit false-positive handling and structural cleanup expectations.
   - Existing `vulture_whitelist.py` is the sanctioned suppression mechanism for non-callsite-visible symbols.

5. **Current vulture signal**
   - `python -m vulture yamlgraph vulture_whitelist.py --min-confidence 60` returns clean output in this branch snapshot.
   - Therefore this defect is currently a structural dead-duplication smell that needs targeted acceptance tests, not only vulture gate reliance.

## Objectives

1. Keep exactly one implementation of `_handle_optional_exports` in the CLI run path.
2. Align FR-375 helper ownership: `graph_run_helpers.py` is canonical for run helpers.
3. Preserve existing `cmd_graph_run` behavior for `--export` and `--export-state`.

## Constraints

1. **Single responsibility:** deduplicate `_handle_optional_exports` and tightly-coupled dead-symbol fallout from the same FR-375 refactor surface only.
2. **No behavior drift:** `--export` / `--export-state` runtime behavior and JSON mode quiet semantics must remain unchanged.
3. **Architecture alignment:** keep presentation-layer orchestration thin (`graph_commands.py`) and helper logic centralized (`graph_run_helpers.py`) per ARCHITECTURE three-layer guidance.
4. **No speculative cleanup:** do not bundle unrelated dead-code removals outside the FR-375 helper split scope.

## Proposed Solution

### In Scope

1. Remove local `_handle_optional_exports` function body from `yamlgraph/cli/graph_commands.py`.
2. Add alias binding from `graph_commands.py` to `graph_run_helpers._handle_optional_exports` near other helper aliases.
3. Remove now-unused imports in `graph_commands.py` caused by deleting the local duplicate (if any).
4. Add focused acceptance tests for duplication removal and preserved behavior.
5. Run vulture with existing whitelist to confirm no additional dead symbols are surfaced by this change.

### Out of Scope

1. Any CLI feature changes unrelated to helper deduplication.
2. Changes to `--json`, interrupt, tracing, token, timing, or parser contracts from FR-375.
3. Broad vulture baseline changes or whitelist policy changes.

## Acceptance Criteria

- [x] **AC-01:** `yamlgraph/cli/graph_commands.py` no longer defines a local `_handle_optional_exports` function.
- [x] **AC-02:** `yamlgraph/cli/graph_run_helpers.py` contains the single canonical `_handle_optional_exports` implementation.
- [x] **AC-03:** `graph_commands.py` aliases `_handle_optional_exports` from `graph_run_helpers` consistently with neighboring helper aliases.
- [x] **AC-04:** `cmd_graph_run` still executes optional export paths (`--export`, `--export-state`, JSON quiet behavior) with unchanged outcomes.
- [x] **AC-05:** Vulture run (`python -m vulture yamlgraph vulture_whitelist.py --min-confidence 60`) remains clean after deduplication.
- [x] **AC-06:** If any additional true dead symbols introduced by FR-375 helper split are found during implementation, they are either removed or explicitly justified in `vulture_whitelist.py` (with required confession entry when adding `# noqa`).

## Failing Acceptance Tests (RED plan)

Planned RED test module:

- `tests/unit/test_fr378_fr375_dead_helper_deduplication_red.py`

Planned RED tests (must fail before implementation):

1. `test_ac01_graph_commands_has_no_local_handle_optional_exports_definition`
2. `test_ac02_graph_run_helpers_has_single_handle_optional_exports_definition`
3. `test_ac03_graph_commands_aliases_handle_optional_exports_from_helpers`
4. `test_ac04_cmd_graph_run_optional_exports_behavior_contract_preserved`
5. `test_ac05_vulture_with_whitelist_is_clean_for_cli_refactor_scope`

Planned RED command:

```bash
pytest tests/unit/test_fr378_fr375_dead_helper_deduplication_red.py -q --no-cov
```

Additional RED evidence command (expected to fail before implementation):

```bash
rg -n "def _handle_optional_exports\\(" yamlgraph/cli/graph_commands.py yamlgraph/cli/graph_run_helpers.py
```

Expected current (pre-fix) evidence: two `def _handle_optional_exports` hits.

## Alternatives Considered

1. **Keep local implementation in `graph_commands.py` and delete helper copy**
   - Rejected: conflicts with FR-375 helper extraction direction and leaves one run-helper exception in the module boundary.

2. **Keep both copies (status quo)**
   - Rejected: duplicate logic increases maintenance risk and violates entropy cleanup doctrine.

3. **Move implementation to a third utility module**
   - Rejected: unnecessary indirection for a single helper; no demonstrated reuse beyond current run-helper boundary.

## Related

- Topic: `/Users/sheikki/Documents/src/yamlgraph/.chaplain/processing/gh-378.md`
- FR-375: `feature-requests/FR-375-graph-run-json-stdout-typescript-node-integration.md`
- Watcher2 sanity note: `docs/diary/2026-05-13-reflection-fr-375-watcher2-sanity-check-state.md`
- `yamlgraph/cli/graph_commands.py`
- `yamlgraph/cli/graph_run_helpers.py`
- `tests/unit/test_graph_commands.py`
- `tests/unit/test_fr375_graph_run_json_stdout_red.py`
- `vulture_whitelist.py`
- `.pre-commit-config.yaml` (`vulture-dead-code`)
