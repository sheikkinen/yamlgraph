# Feature Request: FR-421 ActionConfig Mapping Hardening

**Priority:** HIGH
**Type:** Bug
**Status:** Approved with Amendments
**Effort:** 0.5 day
**Requested:** 2026-05-19

## Summary

Harden ActionConfig mapping in the shared FSM bridge by rejecting invalid `event_map` types and applying annotation-key stripping consistently for nested `params` payloads.

## Value Statement

FSM pipeline operators get deterministic, fail-fast config validation so routing errors are caught at load/execute boundary instead of surfacing as silent misroutes at runtime.

## Problem

FR-419 moved action config parsing to `ActionConfig`, but two logic gaps remain in mapping flow:

1. `event_map` type coercion is too permissive.
- Current validator returns `{}` when `event_map` is not a dict.
- This suppresses validation errors and can silently alter routing behavior (falls through to success/route cascade).

2. Strip-before-validate is inconsistent between top-level and nested `params` style.
- Top-level config strips annotation/envelope keys before `ActionConfig.model_validate()`.
- If payload source switches to `config["params"]`, nested annotation keys (for example `description`) are not stripped.
- Result: false `extra_forbidden` failure in valid authoring patterns that include descriptions.

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
- If value is not `dict`, raise `ValueError("event_map must be a mapping")`.
- If value is `dict`, preserve current lowercase/strip normalization of keys.

### 2) Normalize payload source before validation

Add a small helper in `yamlgraph/utils/fsm/action.py` that:
- Selects payload source (top-level action fields or nested `params`).
- Applies `_STRIP_BEFORE_VALIDATE` to the selected payload.
- Returns sanitized payload for `ActionConfig.model_validate()`.

This unifies mapping semantics for both config styles and prevents repeated edge-case drift.

### 3) Extend tests for condemned bug classes

Add/extend unit tests in `tests/unit/test_fr419_action_config_schema_boundary.py`:
- `event_map` string/list/non-dict raises `ValidationError`.
- `event_map: null` still resolves to `{}`.
- Nested `params` payload with `description` validates after strip.
- Nested `params` payload still rejects true typos (for example `evnt_key`).

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
- `yamlgraph/utils/fsm/action.py`
- `tests/unit/test_fr419_action_config_schema_boundary.py`

## Judgement

**Verdict:** APPROVE WITH AMENDMENTS — scope frozen, authority granted after applying the constraints below.

This FR identifies real boundary defects and proposes minimal, local fixes aligned with FR-419 intent (`ActionConfig` as strict schema boundary).

Required amendments before enforce:

1. Clarify validator contract for `event_map` nullability.
- `event_map: null` must normalize to `{}`.
- Any non-null, non-dict value must raise `ValidationError`.
- Keep key normalization semantics (strip + lowercase) unchanged for dict input.

2. Specify one canonical payload-normalization path.
- The same strip-before-validate logic must be applied regardless of payload source (top-level fields vs nested `params`).
- `description` remains an annotation key only and must not be added to `ActionConfig` fields.
- Unknown execution keys must still fail via `extra="forbid"`.

3. Add explicit regression tests for both condemned bugs.
- Non-dict `event_map` is rejected (string/list).
- `event_map: null` is accepted and normalizes to `{}`.
- Nested `params` payload containing `description` validates after stripping.
- Nested `params` payload with a typo (for example `evnt_key`) still fails.

4. Narrow verification commands to deterministic unit scope.
- Required verify command:
  - `python -m pytest tests/unit/test_fr419_action_config_schema_boundary.py tests/unit/test_fr420_extract_event_dict_support.py -q --no-cov`

Scope freeze:

- In scope:
  - `yamlgraph/utils/fsm/action.py`
  - `tests/unit/test_fr419_action_config_schema_boundary.py`
- Out of scope:
  - legacy runner behavior in `run_legacy_yamlgraph_async`
  - broader FSM routing cascade changes
  - new config surface area beyond this bug fix
