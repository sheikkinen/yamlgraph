# Reflection: FR-346 Extract Shared FSM Bridge Module (Phase 1)

**Date:** 2026-05-07
**FR:** FR-346 — Extract shared FSM bridge module into `yamlgraph.utils.fsm`
**Reviewer:** watcher2 (validate remediation)

## What Happened

FR-346 extracted the fire-and-forget FSM-to-YAMLGraph bridge that had lived in
`examples/fsm-router/actions/yamlgraph_async_action.py` into a proper shared
framework module at `yamlgraph/utils/fsm/`. The package exposes four modules:
`helpers.py` (json_safe, extract_event, resolve_context_ref), `event_sender.py`
(AF_UNIX DGRAM dispatch), `graph_runner.py` (input build + event resolution
cascade), and `action.py` (`YamlgraphAsyncAction`). The fsm-router example was
reduced to a thin wrapper that re-exports from the shared package. A new
requirement `REQ-YG-319` and capability `CAP-141` were registered. Framework-level
tests replaced the example-local test suite.

## Traps Encountered

### `working_system_inertia`

The example-local action had already drifted once (documented in FR-204 context).
Yet the temptation remained to leave it in place and "just document it better."
The decisive argument was not the maintenance burden per se but that tests
couldn't guard the example code from the framework's perspective — only moving
the implementation into `yamlgraph/utils/` brought it under the unit-test gate.

### `architecture_as_diagram`

The import-linter rule forbidding Layer-3 → Layer-2 static imports is specified
in `.importlinter` but easy to violate in a hurry. `graph_runner.py` uses
deferred imports (`from yamlgraph.executor_async import ...` inside the function
body) exactly because a module-level import would violate the boundary
silently until `lint-imports` ran. The explicit injection-point pattern
(`load_fn=None, run_fn=None`) makes the deferral testable in isolation.

### `framework_costume`

Early drafts tried to unify the Chaplain subprocess action with the async
task-based action under the same class hierarchy. These two actions share a
name but not a contract: one is synchronous from FSM's perspective (fork +
wait), the other is fire-and-forget (asyncio task + guard key). Recognising
this as `false_duplicate` kept Phase 1 cleanly scoped and avoided a confusing
base class that would have served neither consumer well.

## What Worked

- RED tests written in `test_fr346_fsm_bridge_shared_module_red.py` before
  implementation provided exact acceptance signals. The four structural checks
  (package path, importable API, fsm-router delegation, doc reference) were
  each independently verifiable, reducing debugging surface.
- Separating `helpers.py` from `graph_runner.py` from `action.py` by
  dependency level meant each could be tested without `statemachine_engine`
  installed — optional-dependency safety was structurally enforced, not
  just documented.
- The `[fsm]` optional extra already existed in `pyproject.toml`, so no
  dependency policy change was required. Zero new dependencies is a strong
  constraint that kept scope narrow.

## Seed

`graph_runner.py` currently hardcodes the event resolution priority order
(interrupt → event_map → _route/route → success). Could this cascade be
declared as a YAML configuration on the FSM action itself — allowing
integrators to insert project-specific resolution steps (e.g., a
`context_map` key consulted before `event_map`) without patching framework
code? This would make the bridge extensible at the graph level rather than
requiring a new FR for each new resolution strategy.
