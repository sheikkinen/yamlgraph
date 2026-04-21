# Feature Request: Activate FR-266 Acceptance Tests — Copilot Node Model Selection

**Priority:** HIGH
**Type:** Fix
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-04-21
**FR:** FR-266 (follow-up)

## Summary

FR-266 implementation is complete (code changes in `graph_schema.py`, `node_compiler.py`,
`copilot_node.py`), but all 12 acceptance tests in
`tests/unit/test_copilot_node_model_selection.py` are still decorated with
`@pytest.mark.skip(reason="FR-266 RED: awaiting implementation")`.

The RED phase is over. The skips must be removed and all tests verified GREEN to close
the TDD cycle. Until they run, REQ-YG-265 has zero coverage in CI.

## Value Statement

Graph authors using `defaults.model` on mixed copilot+LLM graphs get the guarantee they
expect, and CI blocks any future regression — neither is true while tests are skipped.

## Problem

`test_copilot_node_model_selection.py` was written as RED-phase proof (TDD Commandment 7):
red test first, then implementation. The implementation was applied correctly. The skip
decorators were never removed. As a result:

- `pytest` reports 12 skipped, 0 failed — CI passes vacuously.
- `req_coverage.py` shows REQ-YG-265 uncovered (no test markers reach CI).
- A regression in the model-resolution chain would pass CI undetected.

## Evidence of Implementation (all three changes present)

| File | Evidence |
|---|---|
| `yamlgraph/models/graph_schema.py` | `model: str \| None = Field(default=None, …)` at line 102 |
| `yamlgraph/node_compiler.py` | `_compile_copilot_node` passes `defaults=ctx.effective_defaults` |
| `yamlgraph/node_factory/copilot_node.py` | Lines 173–178 resolve `cli_flags.model > config.model > defaults.model` |

## Proposed Solution

Remove `@pytest.mark.skip(reason="FR-266 RED: awaiting implementation")` from all 9 test
classes (12 test methods) in `tests/unit/test_copilot_node_model_selection.py`. Verify
every test passes GREEN with no code changes required.

```python
# Remove this decorator from each test class:
@pytest.mark.skip(reason="FR-266 RED: awaiting implementation")

# Keep the existing marker on each class:
@pytest.mark.req("REQ-YG-265")
```

The tests use `subprocess.run` patching — no API keys required.

## Acceptance Criteria

- [ ] All `@pytest.mark.skip` decorators removed from `test_copilot_node_model_selection.py`
- [ ] `pytest tests/unit/test_copilot_node_model_selection.py -q --no-cov` reports 12 passed, 0 skipped
- [ ] `python scripts/req_coverage.py` shows REQ-YG-265 covered
- [ ] Full unit suite passes: `pytest tests/unit/ -q --no-cov`
- [ ] FR-266 status updated to note test activation complete

## Alternatives Considered

### Keep skips and add a separate integration test

Would perpetuate vacuous CI coverage for REQ-YG-265. The existing unit tests
use mocked subprocess — they are fast, isolated, and require no API keys. No reason
to defer.

### Delete the skipped tests and rewrite

The test file is complete and correct. Deletion would waste the RED-phase work and
force a rewrite that might miss edge cases already captured.

## Related

- `feature-requests/FR-266-copilot-node-model-selection.md` — canonical FR (status: Implemented, tests not yet activated)
- `tests/unit/test_copilot_node_model_selection.py` — 9 test classes, 12 methods, all skipped
- `capabilities/CAP-118-copilot-node-model-selection.yaml` — REQ-YG-265 registered here
- `ARCHITECTURE.md` line 1553 — REQ-YG-265 requirement row
- `tests/unit/test_copilot_node.py::test_cli_flags_passed` — existing passing test (REQ-YG-087, must not regress)
