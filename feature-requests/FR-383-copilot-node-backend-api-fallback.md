# Feature Request: FR-383 Copilot node `backend: api` fallback

**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-05-14

## Summary

Add `backend: api` for `type: copilot` nodes so reasoning-only copilot steps can run through `execute_prompt()` (provider API path) instead of always spawning the Copilot CLI subprocess.

## Value Statement

Pipeline authors get a one-line, per-node fallback from Copilot CLI execution to direct provider API execution without rewriting graph logic or prompt files.

## Problem

`type: copilot` currently documents a `backend` field but behaves as CLI-only in practice:

1. `yamlgraph/models/graph_schema.py` already has `NodeConfig.backend` (currently described as `cli` or `sampling`).
2. `yamlgraph/node_factory/copilot_node.py` ignores `config["backend"]` and always executes `_execute_cli(...)`.
3. `yamlgraph/linter/patterns/copilot.py` checks session-flag shape only; it does not validate backend-specific constraints.
4. `reference/graph-yaml.md` documents `backend: cli|sampling`, but runtime does not branch on backend.

Result: there is no working non-CLI fallback path for copilot nodes despite schema/docs signaling backend configurability.

## Research

### Prior art in codebase

- **Standard API execution path exists:** `yamlgraph/executor.py::execute_prompt()` already handles prompt loading, variable rendering, provider/model selection, and structured output parsing.
- **Copilot result envelope exists:** `yamlgraph/models/schemas.py::CopilotResult` already includes `backend`, `model`, and `session_id`.
- **Copilot CLI path is isolated:** `yamlgraph/node_factory/copilot_node.py::_execute_cli()` is a clear boundary for preserving CLI behavior unchanged.
- **Chaplain usage split is clear:** `.chaplain/graphs/...` uses copilot for both reasoning nodes (judge/validate/sanity) and an agentic enforce node. The enforce node relies on tool access and must remain CLI.

### Alternatives considered

1. **Keep CLI-only and rely on model changes (`cli_flags.model`)**
   Rejected: does not provide an execution-backend fallback; still depends on Copilot CLI runtime path.

2. **Replace copilot node entirely with `type: llm` nodes**
   Rejected: larger migration and loses copilot-specific metadata/session behavior; out of scope for this FR.

3. **Implement documented `sampling` backend first**
   Rejected for this scope: requires MCP loopback infrastructure and is orthogonal to immediate API fallback need.

## Objectives

1. Add `backend: api` execution branch for `type: copilot`.
2. Preserve existing CLI behavior as the default and regression-safe path.
3. Add lint guardrails to prevent API backend misconfiguration that assumes CLI tool/session features.

## Non-Goals

- No changes to existing CLI subprocess behavior.
- No attempt to provide Copilot CLI tool access (`--allow-all-tools`, `--allow-all-paths`) in API mode.
- No batching/cost-profile/routing redesign (covered by separate FRs).

## Proposed Solution

### YAML contract

```yaml
nodes:
  judge:
    type: copilot
    prompt: judge
    backend: api
    provider: anthropic
    model: claude-sonnet-4.6
    variables:
      fr_path: "{state.fr_path}"
    state_key: judge_result
```

- `backend` values for this FR: `cli` (default) and `api`.
- Missing `backend` keeps current behavior (`cli` path).

### Runtime behavior

1. Resolve backend at node creation (`cli` default).
2. If backend is `cli`, execute existing `_execute_cli(...)` path unchanged.
3. If backend is `api`, call `execute_prompt(...)` with existing prompt/variable resolution inputs.
4. Wrap API output in `CopilotResult(backend="api", output=..., model=..., exit_code=0, session_id=None)`.

### Linter behavior

Extend `yamlgraph/linter/patterns/copilot.py` with backend-aware checks:

- **Warning** when `backend: api` has no explicit model signal (`node.model` and no graph default model).
- **Error** when `backend: api` is combined with CLI-only session/tooling flags in `cli_flags` (`allow_all_tools`, `allow_all_paths`, `resume`, `continue_session`).

## Acceptance Criteria

- [x] AC-01: `type: copilot` with `backend: api` executes through `execute_prompt()` and does not call `subprocess.run()`.
- [x] AC-02: `backend` omitted or `backend: cli` preserves existing behavior and existing copilot tests continue to pass.
- [x] AC-03: API path returns `CopilotResult` with `backend="api"` and `session_id is None`.
- [x] AC-04: API path supports prompt schema/structured output through the existing `execute_prompt()` mechanism.
- [x] AC-05: Linter warns on `backend: api` without model signal.
- [x] AC-06: Linter errors on `backend: api` with CLI-only `cli_flags`.
- [x] AC-07: `reference/graph-yaml.md` documents `backend: api` semantics and API-vs-CLI constraints.

## Failing Acceptance Tests (RED first)

1. `tests/unit/test_copilot_node_backend_api.py::test_backend_api_uses_execute_prompt_not_subprocess`
   **Expected RED now:** current implementation always calls `_execute_cli`/`subprocess.run`.

2. `tests/unit/test_copilot_node_backend_api.py::test_backend_api_returns_copilot_result_with_api_backend`
   **Expected RED now:** current implementation always returns `backend="cli"`.

3. `tests/unit/test_copilot_node_backend_api.py::test_backend_omitted_remains_cli_path`
   **Safety test:** proves no behavior drift while adding API branch.

4. `tests/unit/test_linter_patterns_copilot.py::test_warning_backend_api_without_model_signal`
   **Expected RED now:** no backend-model warning rule exists.

5. `tests/unit/test_linter_patterns_copilot.py::test_error_backend_api_with_cli_flags`
   **Expected RED now:** no backend/cli_flags incompatibility rule exists.

## Architecture and Traceability Alignment

- Extend **CAP-30 (Copilot Node)** with new requirement(s):
  - `REQ-YG-356`: Copilot node supports explicit `backend: api` execution via `execute_prompt`.
  - `REQ-YG-357`: Copilot backend lint rules prevent CLI-only flag misuse in API mode.
- Update `ARCHITECTURE.md` requirement table and capability mapping accordingly.
- Mark new tests with `@pytest.mark.req("REQ-YG-356")` / `@pytest.mark.req("REQ-YG-357")`.

## Implementation Surface (for Enforce phase)

| File | Change |
|------|--------|
| `yamlgraph/node_factory/copilot_node.py` | Add backend branch (`cli`/`api`) and API result wrapping |
| `yamlgraph/linter/patterns/copilot.py` | Add backend-aware lint checks |
| `yamlgraph/models/schemas.py` | Update `CopilotResult.backend` description to include `api` |
| `reference/graph-yaml.md` | Document `backend: api` behavior and constraints |
| `tests/unit/test_copilot_node_backend_api.py` | New RED/GREEN tests for runtime backend behavior |
| `tests/unit/test_linter_patterns_copilot.py` | Add RED/GREEN tests for backend lint rules |
| `capabilities/CAP-30-copilot-node.yaml` | Add new REQ entries |
| `ARCHITECTURE.md` | Add REQ rows and capability references |

## Related

- `yamlgraph/node_factory/copilot_node.py`
- `yamlgraph/linter/patterns/copilot.py`
- `reference/graph-yaml.md#type-copilot---copilot-cli-delegation`
- `capabilities/CAP-30-copilot-node.yaml`
