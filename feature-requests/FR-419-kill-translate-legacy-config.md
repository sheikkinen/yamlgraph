# Feature Request: FR-419 Kill `_translate_legacy_config` — Validate Action Config at the Schema Boundary

**Priority:** HIGH
**Type:** Bug / Refactor
**Status:** Enforced
**Effort:** 2 days
**Requested:** 2026-05-19
**Judged:** 2026-05-19

## Summary

Replace `_translate_legacy_config()` and the raw `params: dict` bridge contract
with a Pydantic `ActionConfig` model that validates every key at load time. An
unknown or misspelled key raises `ValidationError` when the pipeline starts — not
a silent routing failure hours into a run.

## Value Statement

A typo in a YAML action config (`event_ky:` instead of `event_key:`) raises an
error when the pipeline starts, not after Copilot CLI has spent 30 minutes on a
plan that will be silently discarded.

## Problem

`YamlgraphAsyncAction._translate_legacy_config()` is a named compatibility shim
(Commandment 8: *"No shims, no adapters, no 'compat' flags"*). It was introduced
in FR-413 to translate the chaplain's flat YAML action syntax into the shared
bridge's internal `params: dict`. The shim is an implicit allowlist: only keys
explicitly coded in the function survive translation. All others are silently
dropped at the config boundary.

This was proven by the FR-416 regression: `event_key: judge_result` was present
in `watcher-pipeline-v2.yaml`. The pipeline ran. The judge step consumed 30
seconds of Copilot CLI. The result was silently discarded because `event_key`
was not in the shim's allowlist. The pipeline routed to `error`. No exception.
No warning. The only symptom was a wrong FSM state.

Current translation table (after FR-416 patch):

| Flat YAML key  | Forwarded? | Maps to in params  |
|----------------|------------|--------------------|
| `graph`        | ✓          | `graph`            |
| `vars`         | ✓          | `variables`        |
| `success`      | ✓          | `success`          |
| `error`        | ✓          | `failure`          |
| `event_map`    | ✓          | `event_map`        |
| `event_key`    | ✓ (patch)  | `event_key`        |
| `input_key`    | **✗**      | `input_key`        |
| `input_value`  | **✗**      | `input_value`      |
| `output_key`   | **✗**      | `output_key`       |
| `thread_id`    | **✗**      | `thread_id`        |
| `phase`        | **✗**      | `phase`            |
| `payload_keys` | **✗**      | `payload_keys`     |
| `timeout`      | **✗**      | `timeout`          |

Seven keys silently dropped. Each is a latent FR-416-class bug.

The root issue is not that the allowlist is incomplete. The root issue is that
**an allowlist is the wrong mechanism**. A complete allowlist is still a silent
drop for any key added to `snapshot_params()` in the future. The shim must be
maintained in parallel with the bridge contract forever. That is the class of bug.
Patching the shim one key at a time does not fix the class.

## Proposed Solution — Pydantic `ActionConfig`

Replace the raw `params: dict[str, Any]` contract with a validated model. The
bridge parses its input config through `ActionConfig` at `execute()` time. The
shim is deleted. The schema is the contract.

### Step 1 — Define `ActionConfig` in `yamlgraph/utils/fsm/action.py`

```python
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

class ActionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    # Required
    graph: str

    # Input/output wiring
    input_key: str = "input"
    input_value: str | None = None
    output_key: str = "yamlgraph_result"
    event_key: str | None = None          # defaults to output_key at runtime
    payload_keys: list[str] | None = None

    # Routing
    event_map: dict[str, str] = Field(default_factory=dict)
    success: str = "completed"
    failure: str = Field(
        "failed",
        validation_alias=AliasChoices("failure", "error"),
    )

    # Graph execution context
    variables: dict[str, str] = Field(
        default_factory=dict,
        validation_alias=AliasChoices("variables", "vars"),
    )
    thread_id: str | None = None
    phase: str = "graph"
    timeout: int = 300
```

`extra="forbid"` means any key not declared above — including typos — raises
`ValidationError` at parse time. The `AliasChoices` fields preserve the existing
flat YAML syntax (`vars:`, `error:`) without any translation code.

### Step 2 — Parse config in the bridge `execute()`

```python
async def execute(self, context: dict[str, Any]) -> str | None:
    raw = self.config.get("params") or self.config
    try:
        action_config = ActionConfig.model_validate(raw)
    except ValidationError as exc:
        logger.error("yamlgraph_async: invalid action config: %s", exc)
        return self.config.get("failure") or self.config.get("error", "error")

    snapshot = snapshot_params_from(action_config, context,
                                    project_root=self.GRAPH_BASE_DIR)
    ...
```

### Step 3 — Update `snapshot_params()` to accept `ActionConfig`

Replace the `params: dict[str, Any]` signature with `ActionConfig`. All
`params.get("key", default)` calls become direct attribute access. Defaults live
in the model, not scattered across `snapshot_params()` bodies.

```python
def snapshot_params_from(
    config: ActionConfig,
    context: dict[str, Any],
    *,
    project_root: str | Path | None = None,
) -> SnapshotParams:
    event_key = config.event_key or config.output_key
    input_value = resolve_context_ref(
        config.input_value or context.get(config.input_key, ""), context, missing=""
    )
    initial_state = {config.input_key: input_value}
    for key, value in config.variables.items():
        initial_state[key] = resolve_context_ref(value, context)
    ...
```

### Step 4 — Delete the shim

After Steps 1–3, delete from `.chaplain/actions/yamlgraph_async_action.py`:
- `_translate_legacy_config()` — replaced by `ActionConfig` aliases
- `_normalize_event_map()` — move into `ActionConfig` validator if needed
- The `__init__` override that called `_translate_legacy_config`

The chaplain adapter becomes:

```python
class YamlgraphAsyncAction(_SharedYamlgraphAsyncAction):
    GRAPH_BASE_DIR = Path(__file__).resolve().parents[2]
    # execute() override for run_legacy_yamlgraph_async fallback remains
```

### What does NOT change

- `watcher-pipeline-v2.yaml` — flat syntax (`vars:`, `error:`) handled by
  `AliasChoices`; no YAML changes needed
- `run_legacy_yamlgraph_async` fallback path — unchanged; reads raw config
  directly and predates the params contract
- All existing FSM bridge tests — behavior preserved

## Acceptance Criteria

- [ ] `ActionConfig` is defined in `yamlgraph/utils/fsm/action.py` with `extra="forbid"`
- [ ] All 13 keys in the problem table above are explicit fields in `ActionConfig`
- [ ] `AliasChoices("vars", "variables")` makes flat YAML `vars:` parse without shim
- [ ] `AliasChoices("error", "failure")` makes flat YAML `error:` parse without shim
- [ ] A YAML action config with an unknown key (e.g. `event_ky:`) raises `ValidationError`
  at parse time, not a silent routing failure at runtime
- [ ] `snapshot_params_from(ActionConfig, context)` replaces `snapshot_params(dict, context)`
- [ ] `_translate_legacy_config` is deleted from the chaplain adapter
- [ ] `watcher-pipeline-v2.yaml` is unchanged
- [ ] All existing FSM bridge tests pass
- [ ] `vulture` reports no dead code in the adapter after deletion
- [ ] `req_coverage --strict` passes (new tests tagged `REQ-YG-319`)

## Alternatives Considered

**Option A — Migrate `watcher-pipeline-v2.yaml` to `params:` nesting, delete shim.**
This would work. The YAML change is mechanical (add `params:` nesting to every
action), not a logic change, and touching 30 keys is not a valid objection if it
is the better design. Rejected not because of line count but because: it preserves
the raw dict contract in the bridge, leaving `snapshot_params()` as a dict consumer
with fallback defaults scattered across the function — no schema, no `extra="forbid"`,
no load-time validation. A future key added to `snapshot_params()` requires a
manual YAML update to all action configs. Option C closes the class of bug
permanently; Option A merely changes which file hosts the fragile list.

**Option B — Promote normalization to the shared bridge (`_FLAT_TO_PARAMS` dict).**
Rejected. It moves the allowlist from the adapter into the bridge: same class of
bug at a different address. Two accepted input formats (flat and `params:`-nested)
creates contract ambiguity. The `vars → variables` and `error → failure` renames
are chaplain naming conventions that would contaminate the shared bridge.

## Related

- FR-413: introduced `_translate_legacy_config` as part of shared bridge migration
- FR-416: `event_key` silent drop — first confirmed instance of this bug class
- `yamlgraph/utils/fsm/action.py` — shared bridge
- `yamlgraph/utils/fsm/snapshot.py` — `SnapshotParams` dataclass, `snapshot_params()`
- `.chaplain/actions/yamlgraph_async_action.py` — adapter containing the shim
- `.chaplain/config/watcher-pipeline-v2.yaml` — flat config that must survive unchanged

## Judgement

**Verdict:** APPROVE WITH AMENDMENTS - Scope frozen, authority granted after incorporating the constraints below.

The defect class is real: allowlist translation at the adapter boundary silently drops fields and reintroduces the same bug every time the contract grows. Moving to a single validated schema boundary is the correct fix class.

Required amendments before enforce:

1. Define the parse boundary explicitly to avoid metadata false-positives.
`ActionConfig` with `extra="forbid"` is correct, but validating `self.config` directly is unsafe if action metadata keys (for example `type`) are present in runtime config objects. Parse only the action payload shape (flat action fields or `params` payload), not the full engine envelope.

2. Preserve FR-319 variable interpolation semantics.
Current adapter behavior supports placeholder interpolation inside larger strings (`PREFIX:{precommit_output}:SUFFIX`) plus unresolved-placeholder normalization for selected keys. This behavior must remain equivalent after shim removal, either by retaining a pre-validation interpolation step or by moving it into snapshot materialization with tests.

3. Preserve event-map normalization semantics.
Current adapter lowercases and trims `event_map` keys before matching. If `_normalize_event_map()` is removed, equivalent normalization must be implemented in `ActionConfig` validation or downstream snapshot construction.

4. Keep a compatibility wrapper for `snapshot_params()` during migration.
Changing all call sites to `snapshot_params_from(ActionConfig, ...)` in one step increases blast radius. Keep a thin `snapshot_params(dict, ...)` wrapper (or equivalent transitional adapter) until all callers are migrated and tested.

5. Condemn this bug class with RED tests before implementation.
Minimum RED coverage:
- unknown key rejection (`event_ky`) at parse boundary,
- alias acceptance for both `vars`/`variables` and `error`/`failure`,
- metadata envelope does not produce false validation failures,
- FR-319 interpolation behavior remains intact,
- event-map token normalization remains case-insensitive.

Scope freeze:

1. In scope:
`yamlgraph/utils/fsm/action.py`, `yamlgraph/utils/fsm/snapshot.py`, `.chaplain/actions/yamlgraph_async_action.py`, targeted FSM bridge tests.

2. Out of scope:
watcher pipeline YAML rewrites, route cascade redesign, legacy `run_legacy_yamlgraph_async` contract changes.

Acceptance bar for merge:

1. RED -> GREEN evidence for unknown-key failure and no-silent-drop behavior.
2. Existing FR-319 behavior verified by tests after refactor.
3. No event routing regression in shared bridge tests.

**Judge:** GitHub Copilot (GPT-5.3-Codex), 2026-05-19
