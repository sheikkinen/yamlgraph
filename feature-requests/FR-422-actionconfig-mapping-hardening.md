# Feature Request: FR-422 ActionConfig Mapping Hardening

**Priority:** MEDIUM
**Type:** Bug (defensive hardening)
**Status:** APPROVE — plan amended, authority granted
**Effort:** 0.25 day
**Requested:** 2026-05-19

## Summary

Harden ActionConfig mapping in the shared FSM bridge by rejecting invalid `event_map` types and applying annotation-key stripping consistently for nested `params` payloads.

## Value Statement

FSM pipeline operators get deterministic, fail-fast config validation so routing errors are caught at load/execute boundary instead of surfacing as silent misroutes at runtime.

## Problem

FR-419 moved action config parsing to `ActionConfig`, but two logic gaps remain in mapping flow. **Both are defensive: neither is a current live failure** (confirmed by grep — real pipeline config uses only proper dict `event_map` and flat top-level syntax). The fix prevents the same regression class if either authoring style is introduced in future.

1. `event_map` type coercion is too permissive.
- Current validator returns `{}` when `event_map` is not a dict.
- This suppresses validation errors and can silently alter routing behavior (falls through to success/route cascade).
- Not observed in watcher-pipeline-v2.yaml; both `event_map` blocks are proper YAML dicts.

2. Strip-before-validate is inconsistent between top-level and nested `params` style.
- Top-level config strips annotation/envelope keys before `ActionConfig.model_validate()`.
- If payload source switches to `config["params"]`, nested annotation keys (for example `description`) are not stripped.
- Result: false `extra_forbidden` failure in valid authoring patterns that include descriptions.
- Nested `params` style is not used in the current watcher-pipeline-v2.yaml; gap is latent.

3. `_NORMALIZE_EMPTY_ON_UNRESOLVED` is dead in the new execution path.
- The constant and its normalization logic (`""` for unresolved single-expression placeholders) exist only in `run_legacy_yamlgraph_async`.
- `YamlgraphAsyncAction.execute()` calls `ActionConfig.model_validate()` directly on the engine-resolved dict. If a context key is absent when the engine resolves `"{validate_gate_output}"`, the literal string `{validate_gate_output}` passes through `_coerce_variable_values` unchanged (it is a string, so no coercion applies) and is forwarded to the graph as the actual variable value.
- The receiving graph gets a template placeholder string instead of an empty string or a real value. Effect depends on how the graph uses the variable — silent wrong input rather than a clean empty default.
- This is **out of scope for this FR** (legacy runner behavior is explicitly excluded). Documented here for traceability; a follow-up FR should decide the canonical contract for unresolved placeholders in the new path.

Observed reproductions:
- `ActionConfig.model_validate({"graph": "g.yaml", "event_map": "APPROVE"})` returns empty map instead of raising.
- `yamlgraph_async` config using `params: { ..., description: ... }` fails validation.
- `_NORMALIZE_EMPTY_ON_UNRESOLVED` is referenced only in `run_legacy_yamlgraph_async`; new path has no equivalent guard (confirmed by grep).

## Proposed Solution

### 1) Enforce strict `event_map` typing

Update `ActionConfig._normalize_event_map`:
- If value is `None`, keep `{}` behavior.
- If value is not a `dict`, raise `ValueError(f"event_map must be a mapping, got {type(v).__name__}")`.
- If value is `dict`, preserve current lowercase/strip normalization of keys (unchanged).

### 2) Fix nested params strip — inline, no helper

In `YamlgraphAsyncAction.execute()`, apply `_STRIP_BEFORE_VALIDATE` to the params branch with the same inline dict comprehension already used for the top-level branch:

```python
# Before (strip gap):
raw_payload = dict(self.config["params"])

# After (consistent strip):
raw_payload = {
    k: v for k, v in self.config["params"].items()
    if k not in _STRIP_BEFORE_VALIDATE
}
```

No new function. No new abstraction.

### 3) Condemning tests first, then verify

Add to `tests/unit/test_fr419_action_config_schema_boundary.py`:
- `event_map` string value raises `ValidationError` (condemns bug before fix)
- `event_map` list value raises `ValidationError`
- `event_map: None` normalizes to `{}` (null contract locked)
- nested `params` with `description` validates after strip (condemns bug before fix)
- nested `params` with typo (`evnt_key`) still fails (regression guard)

## Acceptance Criteria

- [ ] `ActionConfig` rejects non-dict `event_map` values with a validation error.
- [ ] `event_map: null` remains accepted and normalizes to `{}`.
- [ ] `yamlgraph_async` top-level payload and `params` payload pass through the same strip-before-validate path.
- [ ] `description` is ignored consistently for both payload styles before validation.
- [ ] Unknown execution keys are still rejected (`extra="forbid"` behavior preserved).
- [ ] Tests added for both bugs and all tests pass:
  - `tests/unit/test_fr419_action_config_schema_boundary.py`
  - `tests/unit/test_fr420_extract_event_dict_support.py`

## Alternatives Considered

1. Keep permissive coercion (`event_map` non-dict -> `{}`)
- Rejected: hides config defects and creates silent routing changes.

2. Add `description` field to `ActionConfig`
- Rejected: mixes author annotation into runtime execution contract.

3. Patch only one branch (`top-level` or `params`)
- Rejected: keeps split semantics and allows the same class of regressions to recur.

## Related

- `feature-requests/FR-419-kill-translate-legacy-config.md`
- `feature-requests/FR-420-extract-event-dict-support.md`
- `feature-requests/FR-421-built-in-questionnaire-gap-utilities.md`
- `yamlgraph/utils/fsm/action.py`
- `tests/unit/test_fr419_action_config_schema_boundary.py`

## Judgement

**Verdict: AMEND — revise plan, then re-submit.**

FR correctly identifies two real bugs confirmed by reproduction. However the plan contains one unnecessary abstraction and one classification error that must be corrected before enforce.

### AMEND-01 — Bug classification error: both issues are defensive, not live

Neither bug is causing a current pipeline failure:
- `event_map` non-dict: not used in watcher-pipeline-v2.yaml (both usages are proper YAML dicts; confirmed by grep).
- Nested `params` strip gap: the `params:` nested style is not used in watcher-pipeline-v2.yaml. The fallback path in `execute()` was added for an older config style that is not present in the current pipeline.

This must be documented in the Problem section. "Observed reproductions" are synthetic. The value of the fix is defensive: prevents the same class of regression from recurring if either YAML authoring style is introduced. This is still worth doing, but the severity is MEDIUM (not HIGH), and effort is 0.25 day.

### AMEND-02 — Over-engineered fix for Issue 2

The proposed "small helper function" adds indirection for a one-line change. The fix is:

```python
# In execute(), replace:
raw_payload = dict(self.config["params"])
# With:
raw_payload = {k: v for k, v in self.config["params"].items() if k not in _STRIP_BEFORE_VALIDATE}
```

No new function. No new abstraction. One inline dict comprehension, identical in structure to the top-level strip already on the line above.

### Approved constraints

1. Fix `_normalize_event_map`: `None` → `{}` (kept); non-null non-dict → `ValueError("event_map must be a mapping, got {type}")`. Dict input unchanged.
2. Fix nested params strip: inline dict comprehension in `execute()`, no helper function.
3. Tests required (condemning first):
   - `event_map` string value raises `ValidationError`
   - `event_map` list value raises `ValidationError`
   - `event_map: None` normalizes to `{}`
   - nested `params` with `description` validates after strip
   - nested `params` with typo (`evnt_key`) still fails
4. Verify: `python -m pytest tests/unit/test_fr419_action_config_schema_boundary.py tests/unit/test_fr420_extract_event_dict_support.py -q --no-cov`

### Scope freeze (unchanged)

- In scope: `yamlgraph/utils/fsm/action.py`, `tests/unit/test_fr419_action_config_schema_boundary.py`
- Out of scope: `run_legacy_yamlgraph_async`, Problem 3 (`_NORMALIZE_EMPTY_ON_UNRESOLVED`), routing cascade changes
