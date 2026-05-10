# Feature Request: FR-363 Per-node OTel scoping in copilot_node.py

**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-05-10

## Summary

Add optional `YAMLGRAPH_OTEL_DIR` support to `yamlgraph/node_factory/copilot_node.py::_execute_cli` so each copilot node subprocess gets a node-scoped exporter path:

`COPILOT_OTEL_FILE_EXPORTER_PATH=<YAMLGRAPH_OTEL_DIR>/<node_name>.otel.jsonl`

When unset, behavior stays exactly as today.

## Value Statement

Maintainers can analyze watcher and multi-node copilot executions without interleaved spans, making OTel traces usable for process mining and failure forensics.

## Problem

Copilot CLI emits OTel spans when `COPILOT_OTEL_FILE_EXPORTER_PATH` is present in the subprocess environment. Today `_execute_cli` calls `subprocess.run(...)` without an `env=` override, so all copilot nodes inherit the same ambient exporter path (if one is set), causing mixed spans in a single file.

This blocks the next process-mining steps because per-node boundaries are not observable from trace files alone.

## Research: Existing Patterns, Prior Art, and Gaps

1. **Current runtime path has no per-node env override.**
   - `yamlgraph/node_factory/copilot_node.py` calls `subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)` with no `env` parameter.
2. **Per-phase OTel scoping is already proven outside runtime.**
   - `scripts/copilot_instrument.sh` sets `COPILOT_OTEL_FILE_EXPORTER_PATH` per phase (`plan`, `implement`) before each copilot call.
3. **Watcher pipeline is multi-step and needs segmentation.**
   - `.chaplain/config/watcher-pipeline-v2.yaml` orchestrates separate plan/judge/enforce/validate/sanity phases; process-mining requires node-level separation.
4. **Roadmap dependency is explicit.**
   - `docs/plan-process-mining.md` defines FR-363 as prerequisite for semantic classification and mining pipeline FRs.
5. **Gap remains unsolved in framework runtime.**
   - Repo search shows no `YAMLGRAPH_OTEL_DIR` support in YAMLGraph runtime code.

## Objectives

1. Allow node-scoped OTel exporter paths for copilot subprocess execution.
2. Preserve current behavior when `YAMLGRAPH_OTEL_DIR` is unset.
3. Keep implementation minimal (single callsite change in `_execute_cli`).

## Constraints

1. **Single responsibility:** only copilot subprocess env scoping in `_execute_cli`.
2. **No behavior change when unset:** do not alter command/flags/output/error semantics if `YAMLGRAPH_OTEL_DIR` is absent.
3. **No new dependencies:** stdlib only (`os`, existing `Path` usage).
4. **No architecture drift:** keep state model (`CopilotResult`) and session/share extraction unchanged.
5. **Boundary contract:** this FR sets exporter path only; directory lifecycle is caller responsibility.

## Proposed Solution

In `_execute_cli`, construct optional subprocess environment:

```python
otel_dir = os.environ.get("YAMLGRAPH_OTEL_DIR")
node_env = None
if otel_dir:
    node_otel_path = Path(otel_dir) / f"{node_name}.otel.jsonl"
    node_env = {
        **os.environ,
        "COPILOT_OTEL_FILE_EXPORTER_PATH": str(node_otel_path),
    }

result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    timeout=timeout,
    env=node_env,
)
```

### In Scope

1. `_execute_cli` env construction and subprocess wiring.
2. Unit/integration coverage for set/unset behavior and per-node path derivation.
3. FR documentation updates only for this capability.

### Out of Scope

1. Event classification/mining logic (FR-364/FR-365).
2. Framework-wide OTel spans for non-copilot nodes (FR-366 scope).
3. New config keys in graph YAML.
4. Automatic OTel directory creation/permissions management.

## Acceptance Criteria

- [x] **AC-01:** When `YAMLGRAPH_OTEL_DIR` is set, `_execute_cli` invokes `subprocess.run` with `env["COPILOT_OTEL_FILE_EXPORTER_PATH"] == "<dir>/<node_name>.otel.jsonl"`.
- [x] **AC-02:** When `YAMLGRAPH_OTEL_DIR` is unset, behavior remains unchanged (existing copilot node tests continue to pass).
- [x] **AC-03:** Multiple copilot nodes in one graph resolve distinct exporter paths by node name (no shared file path).
- [x] **AC-04:** No changes to `CopilotResult` schema or share/session ID extraction flow.

## Failing Acceptance Tests (RED plan)

Planned RED test module:

- `tests/unit/test_fr363_per_node_otel_scoping_red.py`

Planned RED tests (expected to fail before implementation):

1. `test_ac01_execute_cli_sets_node_scoped_otel_export_path_when_yamlgraph_otel_dir_is_set`
   - Patch `subprocess.run`.
   - Set `YAMLGRAPH_OTEL_DIR` to temp directory.
   - Invoke copilot node and assert `env["COPILOT_OTEL_FILE_EXPORTER_PATH"]` equals `<tmp>/<node_name>.otel.jsonl`.
2. `test_ac02_execute_cli_preserves_existing_behavior_when_yamlgraph_otel_dir_unset`
   - Ensure subprocess invocation still succeeds with current command contract and no forced exporter override.
3. `test_ac03_two_copilot_nodes_receive_distinct_export_paths`
   - Compile a two-node copilot graph.
   - Assert subprocess calls for node A and node B receive different node-scoped exporter file paths.
4. `test_ac04_session_id_extraction_contract_unchanged_with_otel_dir_set`
   - With `YAMLGRAPH_OTEL_DIR` set, verify `--share` extraction still populates `CopilotResult.session_id` as before.

RED command:

```bash
pytest tests/unit/test_fr363_per_node_otel_scoping_red.py -q --no-cov
```

## Alternatives Considered

1. **Keep one global exporter file for all nodes**
   - Rejected: interleaved spans remain unusable for node-level mining.
2. **Set exporter path only in watcher scripts**
   - Rejected: solves one pipeline, not YAMLGraph runtime behavior for all copilot-node users.
3. **Add new YAML node config key for OTel path**
   - Rejected for this scope: unnecessary API surface; env-based opt-in is sufficient and minimal.

## Related

- Issue #365: <https://github.com/sheikkinen/yamlgraph/issues/365>
- `feature-requests/FR-362-copilot-instrumentation-process-mining-poc.md`
- `docs/plan-process-mining.md`
- `yamlgraph/node_factory/copilot_node.py`
- `scripts/copilot_instrument.sh`
- `.chaplain/config/watcher-pipeline-v2.yaml`

## Judgement

**Verdict:** APPROVE — scope frozen, authority to implement granted.

### Evaluation

| Dimension | Finding |
|---|---|
| Scope | Minimal — single callsite (`_execute_cli`), single env var, ~7 lines |
| Contradictions | None — `node_name` already in `_execute_cli` signature; `Path` already imported |
| AC measurability | All 4 ACs are patchable/assertable with `subprocess.run` mock |
| Feasibility | Trivial — env spread + `env=` kwarg; `import os` the only missing import |
| Architecture | Aligned — boundary normalization pattern; env-based opt-in; no YAML schema changes |
| Responsibility | Single — copilot subprocess env scoping only |
| Classification | **Framework primitive** — enables per-node OTel for all copilot-node users, prerequisite for FR-364/365/366 |
| RED tests | Not yet written (planned); AC spec is precise enough to write immediately as first commit |

### Implementer Notes

1. Add `import os` to `copilot_node.py` — currently absent from the import block.
2. Add `YAMLGRAPH_OTEL_DIR` to the "Key Environment Variables" table in `CLAUDE.md`.
3. Write the RED test module (`tests/unit/test_fr363_per_node_otel_scoping_red.py`) as the first commit before touching the implementation.

## Topic Source Note

Requested topic source `.chaplain/processing/gh-365.md` is not present in this worktree snapshot; planning source used was GitHub issue #365 plus in-repo artifacts listed above.
