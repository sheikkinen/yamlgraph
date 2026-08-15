# Judgement: FR-800 Correct Memory-Demo Mock Target to the FR-660 Shell-Tool Seam

**Verdict:** APPROVED WITH REVISIONS - the seam correction is minimal and directionally correct, but authority activates only after the FR requires a permanent mock-call assertion and removes or resolves non-committed/missing evidence references.

**Prior art:** dispositioned in the parent FR's Prior art line (FR-798 owns the Class B trace and disposition; FR-660 owns the seam move; FR-006 has no committed artifact — governing contract is REQ-YG-025/026) and re-verified against the cited artifacts in the Reviewed-against record below — no undispositioned overlap found.

**Reviewed against:** `feature-requests/FR-800-memory-demo-mock-seam-correction.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `docs/investigations/fr798-full-suite-failures.md`; `feature-requests/FR-798-full-suite-failure-classification-investigation.md`; `feature-requests/FR-798-full-suite-failure-classification-investigation.judgement.md`; `feature-requests/FR-660-agent-tool-execution-unification.md`; `tests/integration/test_memory_demo.py`; `yamlgraph/tools/agent.py`; `yamlgraph/tools/tool_builders.py`; `yamlgraph/tools/shell.py`. The cited `logs/fr798-classB-seam.log` and `logs/fr798-py312-classB.log` are not accepted as evidentiary inputs because they are not tracked committed artifacts in this repository; FR-006 is cited but no `feature-requests/*006*` artifact is present.

## What is sound

The problem is real and already traced by committed evidence. FR-800 names the current deterministic failure as `AttributeError: <module 'yamlgraph.tools.agent'> does not have the attribute 'execute_shell_tool'` (`feature-requests/FR-800-memory-demo-mock-seam-correction.md:8`), and the committed FR-798 investigation records the same Class B symptom and causal chain (`docs/investigations/fr798-full-suite-failures.md:81-100`).

The proposed owning seam matches the current code. `agent.py` imports `build_langchain_tool` and does not import `execute_shell_tool` (`yamlgraph/tools/agent.py:18-22`), while `tool_builders.py` imports `execute_shell_tool` from `yamlgraph.tools.shell` and calls that imported name inside the shell StructuredTool wrapper (`yamlgraph/tools/tool_builders.py:17-20`, `yamlgraph/tools/tool_builders.py:44-47`). `shell.py` owns the function definition (`yamlgraph/tools/shell.py:91-95`). Patching `yamlgraph.tools.tool_builders.execute_shell_tool` is therefore the module where the name is looked up at call time, not the defining module and not the stale agent module.

The scope is appropriately narrow. FR-660 explicitly moved execution to a unified `tool.invoke(tool_args)` path and removed duplicate `execute_shell_tool` imports from `agent.py` (`feature-requests/FR-660-agent-tool-execution-unification.md:29-63`, `feature-requests/FR-660-agent-tool-execution-unification.md:65-70`). FR-800 correctly rejects restoring a dead re-export and production edits (`feature-requests/FR-800-memory-demo-mock-seam-correction.md:50-53`, `feature-requests/FR-800-memory-demo-mock-seam-correction.md:64-71`), aligning with the repo rule against shims and false-idol entropy (`.github/copilot-instructions.md:220-222`).

Strategic classification: **Contrib/example test correction**. This is not a framework primitive; it repairs one integration witness for the memory-demo/tool-results contract using existing abstractions.

## Required revisions

### R-1: Make the test prove the patched seam was exercised

Amend the Proposed Solution and AC-01 so the permanent test asserts the mock was called, not merely that `_tool_results` exists. FR-800's Ideal Result says a future seam move should fail clearly rather than silently orphaning the contract (`feature-requests/FR-800-memory-demo-mock-seam-correction.md:36-40`), but the current proposed one-line patch (`feature-requests/FR-800-memory-demo-mock-seam-correction.md:42-48`) is insufficient by itself: the existing test only asserts `_tool_results` presence, length, and tool name (`tests/integration/test_memory_demo.py:284-286`). If the shell seam moves again while the command still succeeds, those assertions can pass without proving the mock intercepted execution.

Fold this exact requirement into the FR: after `result = node_fn({"input": "Show commits"})`, assert `mock_exec.assert_called_once_with(tool_config, {"count": "5"})`, and assert the stored tool result includes the mocked output and `success is True`. This may make the implementation more than one line, but remains a test-only seam correction.

### R-2: Resolve input-closure evidence and prior-art references

Remove `logs/fr798-classB-seam.log` and `logs/fr798-py312-classB.log` from the FR's evidentiary Related block, or commit them before relying on them. They are cited as evidence (`feature-requests/FR-800-memory-demo-mock-seam-correction.md:31-34`, `feature-requests/FR-800-memory-demo-mock-seam-correction.md:73-76`) but are not tracked committed artifacts, while judge doctrine permits only committed artifacts as input (`.github/skills/judge-fr/doctrine.md:16-24`). The committed replacement citation is `docs/investigations/fr798-full-suite-failures.md:81-113`.

Also resolve the FR-006 citation in the Prior art line (`feature-requests/FR-800-memory-demo-mock-seam-correction.md:10`): either cite the exact committed artifact path if it exists under another name, or state that no committed FR-006 artifact is available and that the governing contract for this correction is the current test's `REQ-YG-025` / `REQ-YG-026` markers (`tests/integration/test_memory_demo.py:241-242`). Do not leave an unresolvable prior-art reference in the authority record.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-800-memory-demo-mock-seam-correction.md` revised with R-1 and R-2 |
| D-2 | `tests/integration/test_memory_demo.py` test-only correction to patch `yamlgraph.tools.tool_builders.execute_shell_tool` and assert the mock seam was exercised |

Not authorized: production changes under `yamlgraph/**`; restoring or adding `execute_shell_tool` in `yamlgraph.tools.agent`; `create=True` patches; graph or prompt artifact edits; skip/xfail/deselect/retry changes; changes outside `tests/integration/test_memory_demo.py` except folding the required revisions into FR-800.

## Revised acceptance criteria

- [ ] AC-01: `test_tool_results_stored_in_state` patches `yamlgraph.tools.tool_builders.execute_shell_tool`.
- [ ] AC-02: The test asserts `mock_exec.assert_called_once_with(tool_config, {"count": "5"})`, proving the call resolved through the patched seam.
- [ ] AC-03: The test asserts `_tool_results[0]` includes `tool == "git_log"`, the mocked output, and `success is True`.
- [ ] AC-04: The full `tests/integration/test_memory_demo.py` module passes.
- [ ] AC-05: No production files change, and no re-export/shim is added to `yamlgraph.tools.agent`.
- [ ] AC-06: FR-800 cites only committed evidence or explicitly marks unavailable prior art as unavailable.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement until R-1 and R-2 are folded into `feature-requests/FR-800-memory-demo-mock-seam-correction.md`. | GATE |
| C-2 | The only code surface authorized is `tests/integration/test_memory_demo.py`; production shell, agent, and tool-builder modules are read-only for this FR. | GATE |
| C-3 | The patch target must be `yamlgraph.tools.tool_builders.execute_shell_tool`; `yamlgraph.tools.agent.execute_shell_tool`, `yamlgraph.tools.shell.execute_shell_tool`, and `create=True` are forbidden. | GATE |
| C-4 | Enforcement must run the named test and the full `tests/integration/test_memory_demo.py` module; a pass without the explicit mock-call assertion does not satisfy this judgement. | GATE |

Authority granted: after the required revisions are folded, enforcement may make the test-only correction that retargets the memory-demo shell mock to the FR-660 tool-builder seam and proves `_tool_results` is populated from that mocked execution.
