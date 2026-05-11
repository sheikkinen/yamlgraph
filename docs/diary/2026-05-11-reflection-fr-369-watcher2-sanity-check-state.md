# Reflection: FR-369 Watcher2 Sanity-Check — FSM Snapshot Hooks Phase 2

**Date:** 2026-05-11
**FR:** FR-369 — FSM snapshot contract and lifecycle hooks for shared bridge subclassing
**Reviewer:** watcher2 post-validate (independent)

## Trap

`working_system_inertia` — the shared FSM bridge (FR-346) worked correctly, so no one added an extension seam. The absence of hooks felt acceptable because the existing tests passed. The result: downstream domains were forced to fork dispatch logic to inject domain behavior, recreating the exact drift the bridge extraction was meant to eliminate.

## What Happened

FR-346 established `yamlgraph.utils.fsm` as the shared bridge but left Phase 2 (snapshot contract + lifecycle hooks) unimplemented. This FR delivers the missing seam:

- `snapshot.py` adds a typed `SnapshotParams` dataclass and `snapshot_params()` factory that raises `ValueError` on missing `graph`, maps `success`/`failure` params, builds `initial_state`, and defaults `phase="graph"` and `payload_keys=None`.
- `action.py` gains four overridable no-op hook methods (`pre_snapshot`, `on_success`, `on_error`, `pre_dispatch`) and wires them into `execute()`.
- `graph_runner.py` accepts bound callbacks (`pre_dispatch_fn`, `on_success_fn`, `on_error_fn`) and invokes them deterministically: `pre_dispatch_fn` before send (suppresses on `False`), `on_success_fn` on success with elapsed ms, `on_error_fn` on exception with elapsed ms.
- `__init__.py` exports `SnapshotParams` and `snapshot_params` to the public API.
- CAP-146 + REQ-YG-347 registered in capabilities YAML and ARCHITECTURE.md.

## Root Cause

No explicit extension contract was specified in FR-346. The bridge collapsed implementation into a single `run_and_dispatch` call with no callback seams. Downstream integrators had to override the entire function signature rather than a single hook point — a symptom of architecture-as-diagram (structure documented, not contracted).

## What Worked

- **Test-first RED file locks all AC boundaries before implementation.** All 9 acceptance tests passed green without modification.
- **Regression suite clean.** `test_fsm_bridge_shared.py` (6 tests) and `test_yamlgraph_async_action.py` (19 tests) all pass; default behavior is unchanged.
- **Proportionality is sound.** 594 inserted lines across 10 files — the bulk is the new `snapshot.py` (76 lines), `graph_runner.py` refactor (109 net), acceptance tests (153 lines), and FR artifact (147 lines). No overreach into domain repositories or transport layer.
- **No pipeline logs present** — execution evidence comes from the test suite, which is deterministic and reproducible. Acceptable for a unit-tested extension seam.
- **Dispatch suppression is explicit and logged.** `pre_dispatch_fn` returning `False` emits an `🛑` log line rather than silently dropping the event.

## Seed

When lifecycle hooks are first exercised in a domain subclass, how should YAMLGraph surface hook call timing (e.g., histogram via OpenTelemetry) without requiring domains to instrument each hook manually — and can the `SnapshotParams` boundary carry enough context for automatic span generation?
