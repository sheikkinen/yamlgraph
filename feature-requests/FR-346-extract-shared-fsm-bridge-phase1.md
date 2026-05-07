# Feature Request: FR-346 Extract shared FSM bridge module (Phase 1)

**Priority:** HIGH
**Type:** Feature
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-05-07

## Summary

Extract the canonical fire-and-forget FSM-to-YAMLGraph bridge from `examples/fsm-router/actions/yamlgraph_async_action.py` into a shared framework module at `yamlgraph/utils/fsm/`, then make the fsm-router example consume that shared implementation.

## Value Statement

FSM integrators get one maintained bridge contract (instead of example-local copies), reducing drift and duplicate bug fixes.

## Problem

Bridge logic currently lives in example-local code instead of framework code:

1. `examples/fsm-router/actions/yamlgraph_async_action.py` contains the canonical async guard + event dispatch behavior.
2. The example action has already drifted before (FR-204 context), showing this pattern is not stable when duplicated.
3. There is no shared `yamlgraph.utils.fsm` package to host the contract.

## Research: Existing Patterns and Prior Art

1. **Canonical behavior is already defined in fsm-router action + tests.**
   - Guard key contract (`_graph_running_*`)
   - Async fire-and-forget execution (`asyncio.create_task`)
   - AF_UNIX DGRAM event dispatch
   - Event resolution cascade (interrupt `continue/done` -> `event_map` -> `_route/route` -> `success`)
   - Source: `examples/fsm-router/actions/yamlgraph_async_action.py`, `examples/fsm-router/tests/test_yamlgraph_async_action.py`, `reference/patterns/fsm-as-conductor.md`

2. **A second action exists but is architecturally different and must stay out of scope.**
   - `.chaplain/actions/yamlgraph_async_action.py` is subprocess-based and synchronous from FSM perspective.
   - It is not the same contract and should not be merged into this phase.

3. **Dependency and architecture constraints are already known.**
   - Optional dependency already exists: `pyproject.toml` includes `[project.optional-dependencies].fsm = ["statemachine-engine>=1.0.70"]`
   - Import-linter enforces layers; `yamlgraph.utils` (Layer 3) must avoid static imports from `yamlgraph.executor_async` (Layer 2).

4. **Topic-source discrepancy in this worktree.**
   - Requested source file `.chaplain/processing/gh-346.md` is not present on this branch.
   - Canonical planning source used: GitHub issue #346.

## Objectives

1. Establish `yamlgraph.utils.fsm` as the shared home for bridge logic used by FSM integrations.
2. Keep fsm-router runtime behavior unchanged while replacing local implementation with shared import/wrapper.
3. Preserve explicit phase boundary: do not migrate Chaplain or voicebot implementations in this FR.

## Constraints

1. **Single responsibility:** extraction + example adoption only.
2. **No behavior regressions:** preserve existing guard, dispatch, payload, and routing semantics.
3. **Layer safety:** no module-level Layer-3 -> Layer-2 imports.
4. **Optional dependency safety:** helper utilities must remain importable without `yamlgraph[fsm]`; action class should provide a clear install error if `[fsm]` extra is missing.
5. **No new dependency additions:** reuse existing `[fsm]` optional extra.

## Proposed Solution

### In Scope

1. Add shared package `yamlgraph/utils/fsm/` with:
   - `__init__.py` (public API exports)
   - `helpers.py` (`json_safe`, `extract_event`, `resolve_context_ref`)
   - `event_sender.py` (AF_UNIX DGRAM sender utility)
   - `graph_runner.py` (graph-input build + event resolution cascade helpers)
   - `action.py` (`YamlgraphAsyncAction` based on current fsm-router behavior)
2. Replace `examples/fsm-router/actions/yamlgraph_async_action.py` with thin wrapper/import from `yamlgraph.utils.fsm`.
3. Port/add unit tests to framework-level test paths for shared helpers and event-resolution behavior.
4. Update `reference/patterns/fsm-as-conductor.md` to point to `yamlgraph.utils.fsm` as canonical location.
5. Add changelog fragment in `changelog/unreleased/` for FR-346.

### Architecture Notes (implementation constraints)

1. `graph_runner.py` must use deferred import and explicit injection points for graph execution callables to preserve import-linter boundaries and testability, e.g.:

```python
async def run_and_dispatch(
    ...,
    load_fn=None,
    run_fn=None,
) -> None:
    if load_fn is None or run_fn is None:
        from yamlgraph.executor_async import load_and_compile_async, run_graph_async
```

2. `action.py` is the only module that may import `statemachine_engine` symbols; package import behavior should keep non-action helpers usable without `[fsm]`.

### Out of Scope

1. `.chaplain/actions/yamlgraph_async_action.py` migration.
2. Voicebot migration (separate follow-up phase).
3. New behavior not present in current contract (provider-specific telemetry, UI activity emitters, or lifecycle refactors).

## Acceptance Criteria

- [x] New requirement `REQ-YG-319` added to ARCHITECTURE.md Capabilities table as: "FSM bridge shared module: `yamlgraph.utils.fsm` package with `YamlgraphAsyncAction`, `extract_event`, `json_safe`, `resolve_context_ref` exported from `yamlgraph.utils.fsm`; fire-and-forget guard semantics; AF_UNIX DGRAM event dispatch; interrupt/event_map/route/success resolution cascade | `utils/fsm`".
- [x] `REQ-YG-319` added to the capability registry consumed by `scripts/req_coverage.py` (`CAP-141`).
- [x] All RED test functions updated to use `@pytest.mark.req("REQ-YG-319")` (not REQ-YG-049).
- [x] `yamlgraph/utils/fsm/` exists with `__init__.py`, `helpers.py`, `event_sender.py`, `graph_runner.py`, and `action.py`.
- [x] Shared action preserves fire-and-forget guard semantics and completion guard cleanup.
- [x] Shared event resolution follows documented order: interrupt (`continue`/`done`) -> `event_map` -> `_route/route` -> `success`.
- [x] fsm-router action file is reduced to a thin wrapper/import over shared module.
- [x] Shared helper symbols are importable independently of the `[fsm]` extra.
- [x] Framework-level tests cover helper behavior and event-resolution cascade contracts.
- [x] `reference/patterns/fsm-as-conductor.md` explicitly references `yamlgraph.utils.fsm`.
- [x] Chaplain action file remains unchanged.

## Failing Acceptance Tests (RED)

RED test artifact in this planning branch:

- `tests/unit/test_fr346_fsm_bridge_shared_module_red.py`

Planned RED assertions:

1. Shared package path exists at `yamlgraph/utils/fsm/`.
2. Shared public bridge API is importable from `yamlgraph.utils.fsm`.
3. fsm-router action delegates to shared module import.
4. Pattern documentation references `yamlgraph.utils.fsm`.

Amendment resolved: RED acceptance tests now use `@pytest.mark.req("REQ-YG-319")`.

RED command (expected to fail before implementation):

```bash
pytest tests/unit/test_fr346_fsm_bridge_shared_module_red.py -q --no-cov
```

## Alternatives Considered

1. **Keep bridge logic in example code only**
   - Rejected: preserves drift and duplicated maintenance.
2. **Migrate Chaplain in same FR**
   - Rejected: different subprocess architecture; mixing concerns increases risk.
3. **Skip extraction and just document pattern**
   - Rejected: documentation alone does not remove duplicated implementation risk.

## Related

- Issue: <https://github.com/sheikkinen/yamlgraph/issues/346>
- `examples/fsm-router/actions/yamlgraph_async_action.py`
- `examples/fsm-router/tests/test_yamlgraph_async_action.py`
- `reference/patterns/fsm-as-conductor.md`
- `.chaplain/actions/yamlgraph_async_action.py`
- `pyproject.toml` (`[project.optional-dependencies].fsm`)
- `.importlinter`
