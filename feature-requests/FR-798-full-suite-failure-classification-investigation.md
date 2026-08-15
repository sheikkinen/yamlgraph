# Feature Request: FR-798 Full-Suite Failure Classification Investigation

**Priority:** HIGH
**Type:** Investigation
**Status:** Proposed
**Effort:** 0.5-1 day
**Requested:** 2026-08-15
**First consumer / first event:** the next enforcer whose otherwise-valid commit
reaches the mandatory pytest hook or full-suite gate - the first event is a red
result that currently cannot be distinguished as product regression, test
isolation defect, provider unavailability, or environment mismatch.

**Prior art:** FR-756 (process-boundary test classification), FR-761
(reproducible Python 3.12 dependency environment), FR-796 (the validation run
that exposed these failures), and FR-797 (the separately judged subgraph
interrupt regression, explicitly excluded here).

## Summary

Investigate and classify the non-subgraph failures exposed while validating
FR-796. Produce deterministic reproductions, causal chains, and separate
follow-up dispositions before changing production code or weakening tests.

The observed classes are:

1. `tests/unit/test_runpod_provider.py::TestRunpodProvider::test_default_model_reads_env_without_fallback`
   intermittently fails under the parallel pre-commit test run because
   `importlib.reload(config)` sees `yamlgraph.config` absent from `sys.modules`;
   the same test passes serially.
2. `tests/integration/test_memory_demo.py::TestMemoryDemoEndToEnd::test_tool_results_stored_in_state`
   patches `yamlgraph.tools.agent.execute_shell_tool`, but that symbol is not
   owned or imported by `yamlgraph.tools.agent`; shell execution now lives in
   `yamlgraph.tools.shell` and `yamlgraph.tools.tool_builders`.
3. Three tests in `tests/integration/test_multi_turn_streaming.py` fail with
   empty response/intent outcomes. Both involved graphs hard-code
   `defaults.provider: openai`, so provider failure may be converted into a
   state-shaped result and misread as checkpoint or guard semantics.
4. `tests/integration/test_providers.py::test_execute_prompt_with_openai_provider`
   runs whenever `OPENAI_API_KEY` exists, but the observed key returned HTTP 429
   `insufficient_quota`; key presence is not provider readiness.

FR-797 owns the three `tests/integration/test_subgraph_interrupt.py` failures.
No subgraph runtime, tests, or acceptance criteria may be changed under FR-798.

## Value Statement

Enforcers get failure evidence that names the responsible boundary before a fix
is proposed, preventing unrelated changes from absorbing flaky tests, exhausted
credentials, and real regressions into one scope.

## Problem

The same full-suite command produced three different kinds of red:

- a serial-green/xdist-red module identity failure;
- a stale mock target that raises before testing behavior;
- live-provider tests where a configured credential is unusable;
- demo-level assertions whose empty state may be a downstream representation
  of that provider failure.

Treating these as one product bug would violate the repository's boundary rule.
Treating all of them as external noise would hide real isolation and error
surfacing defects. The raw failure output is available, but no committed
artifact yet maps each symptom to one causal chain and one owning follow-up.

No recent commit since 2026-08-14 touched the named test or runtime files, so a
single recent regression commit is not established. The Python version also
matters: the observed local environment was Python 3.14.6, while the governed
reproducible CI environment is Python 3.12 (FR-761).

## Ideal Result

A committed investigation report lets a successor reproduce each failure with
one command, states whether it occurs serially, under xdist, under Python 3.12,
and with provider access disabled or healthy, traces the failure to the exact
state/module/provider boundary, and assigns every confirmed defect to a minimal
follow-up FR. No production behavior or test gate changes are made until that
classification exists.

## Proposed Solution

Create `docs/investigations/fr798-full-suite-failures.md` and supporting minimal
test harnesses only where needed to preserve a reproduction. Run this matrix:

### A. RunPod module identity under xdist

- Run the named test serially at least 10 times.
- Run it with the pre-commit xdist configuration at least 20 times.
- Run the containing module beside tests that mutate `sys.modules`, reload
  `yamlgraph.config`, or clear imported YAMLGraph modules.
- Capture worker ID, Python version, `id(config)`,
  `config.__spec__.name`, and whether `sys.modules["yamlgraph.config"] is
  config` immediately before each reload.
- Identify the exact test/fixture or runtime operation that removes or replaces
  the module. Do not serialize the full suite or add retries as the fix.

### B. Memory-demo mock ownership

- Reproduce the current `AttributeError` from the named integration test.
- Trace the production call from `create_agent_node()` to the current shell-tool
  execution owner.
- Determine whether the test is stale, the production seam moved without a
  supported patch boundary, or both.
- Produce a minimal RED witness at the owning symbol; do not restore a dead
  re-export merely to satisfy the old patch path.

### C. Multi-turn/provider separation

- Capture the full returned `errors`, `response`, `intent`, interrupt, and
  checkpoint state for each failing turn instead of asserting only the empty
  destination field.
- Run the multi-turn and guard graphs with OpenAI unavailable, with a controlled
  failing LLM, and with one available provider without editing graph artifacts.
- Determine whether provider exceptions are correctly surfaced, silently
  converted to success-shaped state, or independent from the checkpoint
  behavior.
- Keep graph or prompt edits out of this investigation; any such repair requires
  the graph-authoring route in its own judged FR.

### D. Provider readiness gate

- Demonstrate the distinction between absent key, present-but-exhausted key,
  and a successful provider request.
- Decide whether live integration tests should use a documented readiness
  preflight, a dedicated CI credential lane, or explicit operator selection.
- Do not treat arbitrary provider errors as skips after execution begins, and do
  not weaken the provider integration assertion.

Run the relevant matrix in both the active local environment and the FR-761
Python 3.12 constrained environment. The report must quote exact commands,
counts, outputs, and commit identity.

## Acceptance Criteria

- [ ] AC-01: `docs/investigations/fr798-full-suite-failures.md` records the git
      SHA, Python/dependency environment, exact commands, and raw outcomes for
      all four classes.
- [ ] AC-02: The RunPod test has serial (>=10) and xdist (>=20) reproduction
      counts; the report identifies the operation that breaks module identity
      or states the bounded search that failed to reproduce it.
- [ ] AC-03: A deterministic witness proves or falsifies the hypothesis that a
      foreign test/fixture removes or replaces `yamlgraph.config` in
      `sys.modules`; retries and suite serialization are not accepted as the
      investigation result.
- [ ] AC-04: The memory-demo failure is traced from its stale patch target to
      the current shell-tool owner, with a minimal reproduction and a proposed
      owning test seam.
- [ ] AC-05: Multi-turn failure artifacts include `errors`, response/intent,
      interrupt state, and checkpoint state for every turn, and distinguish LLM
      failure from checkpoint behavior.
- [ ] AC-06: OpenAI absent-key, exhausted-key, and successful-readiness states
      are separately evidenced; the report recommends one explicit integration
      test execution policy without silently skipping runtime failures.
- [ ] AC-07: The relevant matrix is run under the FR-761 Python 3.12 constrained
      environment as well as the active local environment, or the exact setup
      blocker is recorded.
- [ ] AC-08: Each confirmed defect receives one disposition: existing FR,
      proposed follow-up FR with first consumer and boundary, test correction,
      environment/operations action, or no-action with evidence.
- [ ] AC-09: FR-797's subgraph interrupt scope is not modified or duplicated.
- [ ] AC-10: No production files under `yamlgraph/**`, graph/prompt artifacts,
      CI workflows, hooks, or test-gate policy change under this investigation.
- [ ] AC-11: The investigation report ends with a recommended enforcement
      order based on causal dependency, not failure count.

## Constraints

- C-1: Investigation only. Evidence, deterministic harnesses, and disposition
  records are authorized; product fixes are not.
- C-2: Read raw errors and state before adding instrumentation or aggregate
  flake metrics.
- C-3: Do not collapse provider availability, checkpoint semantics, stale mock
  ownership, and xdist isolation into one fix FR.
- C-4: Do not skip, retry, serialize, or deselect failures to produce a green
  suite under this authority.
- C-5: Do not expose API keys, tokens, or provider response secrets in committed
  artifacts.

## Alternatives Considered

1. **One fix FR for all failures** - rejected because the observed failures
   cross module identity, mock ownership, provider operations, and graph state.
2. **Mark the tests flaky and retry** - rejected because retries erase causal
   evidence and the memory/provider failures reproduce deterministically.
3. **Delete live integration tests** - rejected because provider and multi-turn
   contracts are user-facing behavior; execution policy may need repair, not
   removal of the witness.
4. **Fold into FR-797** - rejected because subgraph interrupt propagation has a
   judged runtime fix and distinct acceptance boundary.

## Related

- FR-796 validation record and implementation notes
- FR-797 subgraph interrupt propagation (excluded owner)
- `tests/unit/test_runpod_provider.py`
- `tests/integration/test_memory_demo.py`
- `tests/integration/test_multi_turn_streaming.py`
- `tests/integration/test_providers.py`
- `yamlgraph/tools/agent.py`
- `yamlgraph/tools/tool_builders.py`
- `examples/demos/multi-turn/graph.yaml`
- `examples/demos/multi-turn/guard.yaml`
