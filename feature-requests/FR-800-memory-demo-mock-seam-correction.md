# Feature Request: Correct Memory-Demo Mock Target to the FR-660 Shell-Tool Seam

**Priority:** MEDIUM
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 hours
**Requested:** 2026-08-15
**First consumer / first event:** the next enforcer running `tests/integration/test_memory_demo.py` — the first event is the current deterministic `AttributeError: <module 'yamlgraph.tools.agent'> does not have the attribute 'execute_shell_tool'` in `test_tool_results_stored_in_state`, red on every run since FR-660 (2026-07-03).

**Prior art:** FR-798 (Class B investigation — owns the trace and this disposition: "patch-target correction"; explicitly forbids restoring a dead re-export), FR-660 (`085f3aad` — moved shell execution out of `agent.py` into the unified bind/execute path), FR-006 (the memory-demo feature the test covers).

## Summary

`test_tool_results_stored_in_state` patches
`yamlgraph.tools.agent.execute_shell_tool`, a symbol FR-660 removed. The
production call chain is now `create_agent_node()` →
`build_langchain_tool()` (`yamlgraph/tools/tool_builders.py:46`) →
`execute_shell_tool()` (`yamlgraph/tools/shell.py:91`). Change the patch
target to the owning module.

## Value Statement

The only deterministic red in the integration lane disappears, and the
`_tool_results` state contract regains a working witness after six weeks
without one.

## Problem

The test raises before exercising any behavior — the `_tool_results`
storage contract (REQ-YG-025/026) has been unwitnessed since `085f3aad`.
FR-798 proved the corrected seam works: patching
`yamlgraph.tools.tool_builders.execute_shell_tool` runs the identical test
body green with the full agent loop executing
(`logs/fr798-classB-seam.log`), on both Python 3.14.6 and 3.12.11.

## Ideal Result

The test exercises the real agent loop against the seam where the name is
looked up at call time; a future seam move fails the test with a clear
mock-ownership error rather than silently orphaning the contract.

## Proposed Solution

One-line change in `tests/integration/test_memory_demo.py:267`:

```python
patch("yamlgraph.tools.tool_builders.execute_shell_tool") as mock_exec,
```

The current red run is the RED evidence (Scripture 7: the bug is already
condemned by the failing test — the fix makes it witness the contract
again). No re-export in `yamlgraph.tools.agent` (FR-798 disposition;
Commandment 8 — no compat shims). No production files change.

## Acceptance Criteria

- [ ] AC-01: `test_tool_results_stored_in_state` passes; the mock is called
  and `_tool_results` assertions execute (not skipped by an earlier raise).
- [ ] AC-02: The patch target is the module that resolves the name at call
  time (`yamlgraph.tools.tool_builders`), not a restored re-export.
- [ ] AC-03: Full `tests/integration/test_memory_demo.py` module green.
- [ ] AC-04: No production files change.

## Alternatives Considered

- **Restore `execute_shell_tool` import in `agent.py`:** dead re-export to
  satisfy a stale patch path — forbidden by FR-798's disposition and
  Commandment 8.
- **Rewrite the test against `shell.execute_shell_tool`:** patching the
  defining module doesn't intercept `tool_builders`' from-import binding;
  wrong seam.

## Related

- `docs/investigations/fr798-full-suite-failures.md` (Class B)
- `logs/fr798-classB-seam.log`, `logs/fr798-py312-classB.log`
