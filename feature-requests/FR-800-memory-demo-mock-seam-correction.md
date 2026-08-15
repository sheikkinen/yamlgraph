# Feature Request: Correct Memory-Demo Mock Target to the FR-660 Shell-Tool Seam

**Priority:** MEDIUM
**Type:** Bug
**Status:** Judged — APPROVED WITH REVISIONS (revisions folded below; see `FR-800-memory-demo-mock-seam-correction.judgement.md`)
**Effort:** 0.5 hours
**Requested:** 2026-08-15
**First consumer / first event:** the next enforcer running `tests/integration/test_memory_demo.py` — the first event is the current deterministic `AttributeError: <module 'yamlgraph.tools.agent'> does not have the attribute 'execute_shell_tool'` in `test_tool_results_stored_in_state`, red on every run since FR-660 (2026-07-03).

**Prior art:** FR-798 (Class B investigation — owns the trace and this disposition: "patch-target correction"; explicitly forbids restoring a dead re-export), FR-660 (`085f3aad` — moved shell execution out of `agent.py` into the unified bind/execute path). FR-006 (memory demo) has no committed FR artifact under that ID (judgement R-2); the governing contract for this correction is the test's existing `REQ-YG-025` / `REQ-YG-026` requirement markers.

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
body green with the full agent loop executing, on both Python 3.14.6 and
3.12.11 (committed evidence: `docs/investigations/fr798-full-suite-failures.md`,
Class B section — judgement R-2: uncommitted session logs removed from the
evidentiary record).

## Ideal Result

The test exercises the real agent loop against the seam where the name is
looked up at call time; a future seam move fails the test with a clear
mock-ownership error rather than silently orphaning the contract.

## Proposed Solution

One-line change in `tests/integration/test_memory_demo.py:267`:

```python
patch("yamlgraph.tools.tool_builders.execute_shell_tool") as mock_exec,
```

**Seam-proof assertions (judgement R-1, binding):** after
`result = node_fn({"input": "Show commits"})`, the test must assert
`mock_exec.assert_called_once_with(tool_config, {"count": "5"})`, and assert
the stored tool result includes the mocked output and `success is True` —
proving the call resolved through the patched seam, so a future seam move
fails loudly instead of silently orphaning the contract.

The current red run is the RED evidence (Scripture 7: the bug is already
condemned by the failing test — the fix makes it witness the contract
again). No re-export in `yamlgraph.tools.agent` (FR-798 disposition;
Commandment 8 — no compat shims). No production files change.

## Acceptance Criteria

(Revised per judgement — supersedes the proposed set.)

- [ ] AC-01: `test_tool_results_stored_in_state` patches
  `yamlgraph.tools.tool_builders.execute_shell_tool`.
- [ ] AC-02: The test asserts `mock_exec.assert_called_once_with(tool_config,
  {"count": "5"})`, proving the call resolved through the patched seam.
- [ ] AC-03: The test asserts `_tool_results[0]` includes `tool == "git_log"`,
  the mocked output, and `success is True`.
- [ ] AC-04: The full `tests/integration/test_memory_demo.py` module passes.
- [ ] AC-05: No production files change, and no re-export/shim is added to
  `yamlgraph.tools.agent`.
- [ ] AC-06: FR-800 cites only committed evidence or explicitly marks
  unavailable prior art as unavailable.

## Alternatives Considered

- **Restore `execute_shell_tool` import in `agent.py`:** dead re-export to
  satisfy a stale patch path — forbidden by FR-798's disposition and
  Commandment 8.
- **Rewrite the test against `shell.execute_shell_tool`:** patching the
  defining module doesn't intercept `tool_builders`' from-import binding;
  wrong seam.

## Related

- `docs/investigations/fr798-full-suite-failures.md` (Class B — committed
  evidentiary record; seam experiment and py312 confirmation documented there)
