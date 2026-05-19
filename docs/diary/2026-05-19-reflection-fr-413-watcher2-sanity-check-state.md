# FR-413 Watcher2 Sanity-Check Reflection

**Date:** 2026-05-19
**FR:** FR-413 Migrate Chaplain `yamlgraph_async_action` to shared FSM bridge
**Reviewer:** watcher2 post-validate

## Trap

`downstream_fix` + `working_system_inertia`: the original Chaplain action ran
`yamlgraph graph run` as a subprocess — a complete parallel path to the shared
FSM bridge that had already been extracted into `yamlgraph/utils/fsm/`.
It worked, so nobody touched it. Meanwhile bridge fixes accumulated in the
shared module without ever reaching the Chaplain pipeline.

## What Happened

FR-413 replaces `.chaplain/actions/yamlgraph_async_action.py` with a thin
subclass of `yamlgraph.utils.fsm.YamlgraphAsyncAction`. The constructor now
translates the legacy top-level watcher config keys (`graph`, `vars`, `success`,
`error`, `event_map`) into the shared `params` shape, so the existing
`.chaplain/config/watcher-pipeline-v2.yaml` required no change.

The diff also removes FR-411 (Inquisitor audit-cadence reintegration) wholesale:
`audit_action.py`, `syncing_inbox_action.py`, `CAP-152`, the FR-411 test file
(266 lines), and the FR-411 diary entry were all deleted. This is a large
side-operation — logically coupled because FR-411 was the predecessor attempt
that was superseded, but it makes the surface area of this PR appear larger
than the FR-413 scope alone.

## Root Cause

Chaplain was the last outlier that ran `yamlgraph graph run` directly. Shared
bridge standardization (REQ-YG-319, REQ-YG-347) had already been completed for
`examples/fsm-router/` but the migration of `.chaplain/` was deferred, creating
silent drift.

## What Worked

- **Boundary normalization at `__init__`**: the `_translate_legacy_config` static
  method normalizes the whole config contract once, at construction time. All
  downstream methods see the shared `params` shape; no scattered field remapping.
- **`pre_snapshot` hook** handles runtime-specific concerns (interpolating
  context variables, collapsing unresolved `{precommit_output}` /
  `{validate_gate_output}` placeholders to `""`) without touching the base class.
- **RED tests**: 4 acceptance tests covering all 6 stated criteria. Assertions
  inspect captured `run_and_dispatch` kwargs and exact `initial_state` values,
  not just call presence. The AST-level check for `test_ac01` is particularly
  clean — it proves structure, not runtime behaviour.
- **Compatibility**: 52 watcher pipeline tests and 14 FSM action tests all green
  with no modifications.

## Minor Observations

1. `_NORMALIZE_EMPTY_ON_UNRESOLVED` is defined in both `yamlgraph/utils/fsm/action.py`
   and `.chaplain/actions/yamlgraph_async_action.py` — acceptable given the
   adapter boundary pattern, but worth consolidating if a third site appears.
2. `run_legacy_yamlgraph_async` was added to the shared module as a subprocess
   fallback for callers that lack `current_state` in context. This preserves
   backward compatibility correctly, but the condition `if "current_state" not
   in context` is implicit. A named constant or documented protocol contract
   would make the discriminator explicit.
3. The changelog fragment omits `req: REQ-YG-319` — `req:` is documented as
   optional, so the gate should not block, but adding it would improve
   traceability.

Seed: If an adapter constructor translates a legacy config shape at construction time,
can the shared base class expose a `from_legacy(config)` classmethod that makes
this pattern first-class — so future adapters don't need to duplicate
`_translate_*` boilerplate?
