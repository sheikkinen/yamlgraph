# Feature Request: FR-798 Full-Suite Failure Classification Investigation

**Priority:** HIGH
**Type:** Investigation
**Status:** Enforced 2026-08-15 - investigation complete; report at docs/investigations/fr798-full-suite-failures.md
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

### Prior-art disposition (R-1)

| Prior art | Binding disposition for FR-798 |
|---|---|
| FR-756 | Supplies the process/core classification precedent; FR-798 may classify failures across test surfaces but must not change the `process` marker, core-test job, or boundary lint. |
| FR-761 | Supplies the Python 3.12 constrained environment and dependency reproducibility command; FR-798 may run that environment and record blockers but must not regenerate constraints or alter dependency governance. |
| FR-796 | Supplies the validation-run source and observed non-retired-path failures; FR-798 owns only classification of the non-subgraph failures exposed there, not reopening FR-796's demo relocation scope. |
| FR-797 | Owns the three subgraph-interrupt failures; FR-798 may cite them only as excluded context and must not modify subgraph runtime, subgraph tests, interrupt demos, or FR-797 acceptance criteria. |

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

### Reproduction-harness collection policy (R-2)

- The primary deliverable is
  `docs/investigations/fr798-full-suite-failures.md`.
- Raw command outputs may be quoted in that report or stored under
  `docs/investigations/fr798/` if too large for the report.
- Any committed pytest witness under `tests/**` must either pass, be explicitly
  `xfail`/`skip` with an FR-798 reason and owning follow-up disposition, and
  carry normal `@pytest.mark.req(...)`, or be returned to planning before
  commit.
- No default test selection, CI workflow, hook, marker policy, or
  retry/serialization mechanism may change to accommodate the investigation.

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
- Produce a minimal witness at the owning symbol under the R-2 collection
  policy; do not restore a dead re-export merely to satisfy the old patch path.

### C. Multi-turn/provider separation

- Capture the full returned `errors`, `response`, `intent`, interrupt, and
  checkpoint state for each failing turn instead of asserting only the empty
  destination field.
- Run the multi-turn and guard graphs with OpenAI unavailable, with a controlled
  failing LLM, and, when an operator-selected healthy credential is already
  available, with that provider without editing graph artifacts.
- Determine whether provider exceptions are correctly surfaced, silently
  converted to success-shaped state, or independent from the checkpoint
  behavior.
- Keep graph or prompt edits out of this investigation; any such repair requires
  the graph-authoring route in its own judged FR.

### D. Provider readiness gate

- Demonstrate the distinction between absent key, present-but-exhausted key,
  and a successful provider request.
- Successful readiness may use only an operator-selected provider credential
  already available in the environment. Do not create, purchase, rotate, or
  paste credentials under this FR. If no healthy credential is available,
  record that exact blocker while still evidencing absent-key and exhausted-key
  behavior.
- Redact provider error bodies, account identifiers, keys, and request IDs in
  committed artifacts while preserving error class, HTTP status, provider name,
  and command.
- Decide whether live integration tests should use a documented readiness
  preflight, a dedicated CI credential lane, or explicit operator selection.
- Do not treat arbitrary provider errors as skips after execution begins, and do
  not weaken the provider integration assertion.

Run the relevant matrix in both the active local environment and the FR-761
Python 3.12 constrained environment. The report must quote exact commands,
counts, outputs, and commit identity.

## Acceptance Criteria

- [x] AC-01: FR-798 is amended with R-1 through R-3 before enforcement authority
  is used.
- [x] AC-02: `docs/investigations/fr798-full-suite-failures.md` records the git
  SHA, Python/dependency environment, exact commands, and raw outcomes for
  all four non-subgraph classes.
- [x] AC-03: The RunPod test has serial (>=10) and xdist (>=20) reproduction
      counts; the report identifies the operation that breaks module identity
      or states the bounded search that failed to reproduce it.
- [x] AC-04: A deterministic witness proves or falsifies the hypothesis that a
      foreign test/fixture removes or replaces `yamlgraph.config` in
      `sys.modules`; retries and suite serialization are not accepted as the
      investigation result.
- [x] AC-05: The memory-demo failure is traced from its stale patch target to
      the current shell-tool owner, with a minimal reproduction and a proposed
      owning test seam.
- [x] AC-06: Any committed reproduction harness follows the R-2 collection
  policy and does not add a new unclassified default-suite failure.
- [x] AC-07: Multi-turn failure artifacts include `errors`, response/intent,
      interrupt state, and checkpoint state for every turn, and distinguish LLM
      failure from checkpoint behavior.
- [x] AC-08: OpenAI absent-key, exhausted-key, and successful-readiness states
  are separately evidenced when a healthy operator-selected credential is
  available; if not available, the report records the exact readiness
  blocker while still evidencing absent-key and exhausted-key behavior.
- [x] AC-09: The relevant matrix is run under the FR-761 Python 3.12 constrained
      environment as well as the active local environment, or the exact setup
      blocker is recorded.
- [x] AC-10: Each confirmed defect receives one disposition: existing FR,
      proposed follow-up FR with first consumer and boundary, test correction,
      environment/operations action, or no-action with evidence.
- [x] AC-11: FR-797's subgraph interrupt scope is not modified, duplicated, or
  used as evidence of FR-798 completion.
- [x] AC-12: No production files under `yamlgraph/**`, graph/prompt artifacts,
  CI workflows, hooks, branch-protection policy, pytest marker policy,
  dependency governance, or test-gate policy change under this
  investigation.
- [x] AC-13: Committed artifacts redact provider secrets and account/request
  identifiers while preserving enough error class/status/provider detail to
  reproduce the classification.
- [x] AC-14: The investigation report ends with a recommended enforcement
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

## Judgement (2026-08-15)

**Verdict:** APPROVED WITH REVISIONS - R-1 through R-3 are folded above;
authority is active for the frozen investigation scope. See
`FR-798-full-suite-failure-classification-investigation.judgement.md`.

| # | Condition | Severity |
|---|---|---|
| C-1 | Treat this as investigation authority only: classify, reproduce, report, and disposition; do not repair product/runtime behavior or weaken tests/gates. | GATE |
| C-2 | Any committed reproduction harness must follow the revised collection policy and must not create a new default-suite red unrelated to the existing classified failures. | GATE |
| C-3 | Provider-success evidence may use only operator-selected existing credentials; absence of a healthy credential is a reportable blocker, not permission to create or expose secrets. | GATE |
| C-4 | If work touches FR-797's subgraph scope, graph/prompt artifacts, CI/hooks, dependency governance, or test-selection policy, stop and return for a separate judged FR. | GATE |

## Completion Record (Enforced 2026-08-15)

Report: `docs/investigations/fr798-full-suite-failures.md` at `fd9cd8fc`.
All four classes classified; zero product defects; no files under
`yamlgraph/**` changed (AC-12). Dispositions: A = test correction
(fr432 fixture re-import), B = test correction (patch target ->
`yamlgraph.tools.tool_builders.execute_shell_tool`), C = folded into D,
D = operations (OpenAI credit) + proposed readiness-preflight follow-up FR.
xdist matrix reproduced Class A in run 20/20 (~5%/run), confirming the
deterministic 2-module witness. No reproduction harness committed under
tests/** (R-2: report-preserved commands suffice).
