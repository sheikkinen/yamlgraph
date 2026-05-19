# Feature Request: FR-413 Migrate Chaplain `yamlgraph_async_action` to shared FSM bridge

**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-05-19

## Summary

Replace `.chaplain/actions/yamlgraph_async_action.py` with a thin adapter over `yamlgraph.utils.fsm.YamlgraphAsyncAction` while preserving the current watcher pipeline action contract.

## Value Statement

Watcher maintainers get one canonical `yamlgraph_async` execution path, so bridge fixes land once and apply to Chaplain immediately instead of drifting behind.

## Problem

Chaplain is the remaining outlier for `yamlgraph_async` execution:

1. `.chaplain/actions/yamlgraph_async_action.py` still runs `yamlgraph graph run` directly via subprocess.
2. Shared bridge behavior already exists in `yamlgraph/utils/fsm/{action.py,graph_runner.py,snapshot.py}` and is already consumed by `examples/fsm-router/actions/yamlgraph_async_action.py`.

This duplicates event-resolution and payload behavior that are already standardized by architecture requirements `REQ-YG-319` (shared FSM bridge) and `REQ-YG-347` (snapshot hooks).

## Proposed Solution

Implement Chaplain as a shared-bridge adapter and keep all legacy watcher config compatibility at the adapter boundary.

```yaml
# Existing watcher config must remain valid (no params: rewrite required)
judge:
  - type: yamlgraph_async
    graph: .chaplain/graphs/watcher-plan/step-judge-v2.yaml
    vars:
      topic_file: "{topic_file}"
      fr_path: "{fr_path}"
    event_map:
      APPROVE: approve
      AMEND: revise
      REJECT: reject
      SPLIT: revise
    success: error
    error: error
```

1. Replace `.chaplain/actions/yamlgraph_async_action.py` with a thin subclass of `yamlgraph.utils.fsm.YamlgraphAsyncAction`.
2. Translate legacy top-level config keys (`graph`, `vars`, `success`, `error`, `event_map`) into shared `params` shape.
3. Preserve Chaplain-specific behavior in adapter logic only:
   - runtime variable interpolation from context
   - unresolved placeholder normalization for `precommit_output` and `validate_gate_output` to `""`
   - event-map token normalization needed by shared cascade (`continue`, `done`, verdict tokens)
   - dynamic graph path resolution using `context["main_dir"]` (legacy parity)
4. Keep `.chaplain/config/watcher-pipeline-v2.yaml` unchanged.

## Acceptance Criteria

- [x] **AC-01 Thin wrapper:** `.chaplain/actions/yamlgraph_async_action.py` subclasses shared `yamlgraph.utils.fsm.YamlgraphAsyncAction`.
- [x] **AC-02 Remove subprocess path:** Chaplain action contains no `create_subprocess_exec`, no `create_subprocess_shell`, and no direct `yamlgraph graph run` argv construction.
- [x] **AC-03 Legacy contract translation:** top-level watcher keys are translated into shared `params` (`graph`, `variables`, `success`, `failure`, `event_map`) without changing watcher YAML.
- [x] **AC-04 Shared dispatch path:** `execute()` launches shared `run_and_dispatch` fire-and-forget path and passes translated success/failure/event-map contract.
- [x] **AC-05 Dynamic main_dir parity:** graph path resolution uses `context["main_dir"]` when provided, matching legacy runtime behavior.
- [x] **AC-06 Placeholder normalization parity:** unresolved `{precommit_output}` / `{validate_gate_output}` placeholders become empty strings.
- [x] **AC-07 Event routing parity:** interrupt continuation (`continue`), completion (`done`), and mapped verdict events resolve through shared bridge semantics.
- [x] **AC-08 Watcher compatibility:** existing watcher pipeline tests remain green (`tests/unit/test_fr305_watcher_pipeline_v2.py` and related watcher async-action coverage).

## Failing Acceptance Tests (RED)

RED tests for this FR live in:

- `tests/unit/test_fr413_chaplain_yamlgraph_async_shared_bridge_red.py`

They assert:

1. thin subclass over shared bridge
2. subprocess path removal
3. legacy-to-params translation and event token normalization
4. shared `run_and_dispatch` launch contract
5. `main_dir` path resolution parity
6. unresolved placeholder normalization parity

Expected RED command:

```bash
pytest tests/unit/test_fr413_chaplain_yamlgraph_async_shared_bridge_red.py -q --no-cov
```

## Alternatives Considered

1. **Keep Chaplain implementation as-is.** Rejected: preserves drift and duplicate behavior contracts.
2. **Fork shared bridge behavior into Chaplain again.** Rejected: recreates the same maintenance split.
3. **Force watcher YAML migration to `params:` now.** Rejected: unnecessary config churn; adapter boundary can preserve compatibility.

## Related

- Topic source: GitHub issue `#415` (`.chaplain/processing/gh-415.md` was not present in this worktree during planning)
- Shared bridge: `yamlgraph/utils/fsm/action.py`, `yamlgraph/utils/fsm/graph_runner.py`, `yamlgraph/utils/fsm/snapshot.py`
- Thin-wrapper prior art: `examples/fsm-router/actions/yamlgraph_async_action.py`
- Watcher action contract: `.chaplain/config/watcher-pipeline-v2.yaml`
- Prior extraction context: `.chaplain/done/gh-346.md`, `.chaplain/done/gh-369.md`, `.chaplain/done/gh-393.md`
