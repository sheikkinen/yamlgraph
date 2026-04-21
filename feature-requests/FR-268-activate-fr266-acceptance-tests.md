# Feature Request: Activate FR-266 Acceptance Tests — Copilot Node Model Selection

**Priority:** HIGH
**Type:** Fix
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-04-21
**FR:** FR-268

## Summary

Remove `@pytest.mark.skip` decorators from all 12 acceptance tests in
`tests/unit/test_copilot_node_model_selection.py`. The FR-266 implementation is
complete; the skip decorators were never removed after the RED phase, leaving
REQ-YG-265 with zero CI coverage and CI passing vacuously.

## Value Statement

Graph authors get the guaranteed model-selection contract for copilot nodes they
expect, and CI blocks any future regression — neither guarantee holds while the
tests are skipped.

## Problem

`tests/unit/test_copilot_node_model_selection.py` was written as the TDD RED-phase
proof for FR-266 (12 test methods across 9 classes, all marked
`@pytest.mark.req("REQ-YG-265")`). The three required code changes were applied
correctly:

| File | Change |
|---|---|
| `yamlgraph/models/graph_schema.py` | `model: str \| None = Field(default=None, …)` added to `NodeConfig` |
| `yamlgraph/node_compiler.py` | `_compile_copilot_node` now passes `defaults=ctx.effective_defaults` |
| `yamlgraph/node_factory/copilot_node.py` | Lines 173–178 resolve `cli_flags.model > config.model > defaults.model` |

The skip decorators were never removed after implementation. Consequences:

- `pytest` reports 12 skipped, 0 failed — CI passes vacuously on the FR-266 scope.
- A regression in the model-resolution chain would go undetected by CI.

> **Note:** `python scripts/req_coverage.py` uses static AST analysis and already reports
> `✅ CAP-118 Copilot Node Model Selection: 1/1 reqs, 12 tests` today — skipped tests are
> counted. The coverage gap is not visible via that script; it is only visible at `pytest`
> runtime (`12 skipped` ≠ `12 passed`).

## Proposed Solution

Remove the `@pytest.mark.skip(reason="FR-266 RED: awaiting implementation")`
decorator from each of the 9 test classes in
`tests/unit/test_copilot_node_model_selection.py`. No production code changes are
required — the implementation is already in place.

```python
# Before (remove this from every test class):
@pytest.mark.skip(reason="FR-266 RED: awaiting implementation")
@pytest.mark.req("REQ-YG-265")
class TestNodeConfigModelField:
    ...

# After:
@pytest.mark.req("REQ-YG-265")
class TestNodeConfigModelField:
    ...
```

The 9 affected classes are:
- `TestNodeConfigModelField` (2 tests)
- `TestCopilotNodeAcceptsDefaults` (1 test)
- `TestCompilerPassesDefaults` (1 test)
- `TestNodeLevelModelPassedToCLI` (1 test)
- `TestDefaultsModelFallback` (1 test)
- `TestCliFlagsModelOverridesNodeLevel` (2 tests)
- `TestNoModelOmitsFlag` (1 test)
- `TestCopilotResultReflectsResolvedModel` (2 tests)
- `TestModelPriorityChain` (1 test)

All tests use `subprocess.run` patching — no API keys required. They are fast,
isolated unit tests.

After activation, update FR-266 status to reflect that the TDD cycle is fully
closed (tests GREEN, REQ-YG-265 covered in CI).

## Acceptance Criteria

- [ ] All `@pytest.mark.skip` decorators removed from `test_copilot_node_model_selection.py`
- [ ] `pytest tests/unit/test_copilot_node_model_selection.py -q --no-cov` reports 12 passed, 0 skipped
- [ ] Full unit suite passes: `pytest tests/unit/ -q --no-cov`
- [ ] FR-266 `Status` field updated to reflect test activation complete
- [ ] Changelog fragment added in `changelog/unreleased/`

## Alternatives Considered

### Keep skips, add a separate integration test

Would perpetuate vacuous CI coverage for REQ-YG-265. The existing unit tests are
fast, isolated, and require no API keys. There is no reason to defer.

### Delete and rewrite

The test file is complete and correct; the RED-phase work is preserved. Deletion
would force a rewrite that might miss edge cases already captured.

## Related

- `feature-requests/FR-266-copilot-node-model-selection.md` — canonical FR (Status: Implemented; tests not yet activated)
- `tests/unit/test_copilot_node_model_selection.py` — 9 test classes, 12 methods, all skipped
- `capabilities/CAP-118-copilot-node-model-selection.yaml` — REQ-YG-265 registered here
- `ARCHITECTURE.md` — REQ-YG-265 requirement row
- `tests/unit/test_copilot_node.py::test_cli_flags_passed` — existing passing test (REQ-YG-087, must not regress)
