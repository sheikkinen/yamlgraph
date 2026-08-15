# Judgement: FR-798 Full-Suite Failure Classification Investigation

**Verdict:** APPROVED WITH REVISIONS - the investigation is the right next step for a mixed red full-suite result, but authority activates only after the FR dispositions its prior art, defines how any committed repro harnesses avoid polluting the default suite, and gates live-provider readiness work against credential/spend realities.

**Reviewed against:** `feature-requests/FR-798-full-suite-failure-classification-investigation.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`; cited prior art `feature-requests/FR-756-core-test-isolation.md`, `feature-requests/FR-761-reproducible-dependency-governance.md`, `feature-requests/FR-761-reproducible-dependency-governance.judgement.md`, `feature-requests/FR-796-reclassify-watcher2-witness-demos.md`, `feature-requests/FR-796-reclassify-watcher2-witness-demos.judgement.md`, `feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md`, `feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.judgement.md`; cited evidence files `tests/unit/test_runpod_provider.py`, `tests/integration/test_memory_demo.py`, `tests/integration/test_multi_turn_streaming.py`, `tests/integration/test_providers.py`, `yamlgraph/tools/agent.py`, `yamlgraph/tools/tool_builders.py`, `examples/demos/multi-turn/graph.yaml`, `examples/demos/multi-turn/guard.yaml`.

**Prior art:** FR-756 and FR-761 are adopted only as test-boundary and reproducible-environment precedents; FR-796 supplies the observed failure record without reopening its relocation scope; FR-797 owns and excludes all subgraph-interrupt failures. R-1 requires this disposition to be folded into FR-798 as a binding boundary table.

## What is sound

The problem is real and correctly classified as an investigation-before-fix. FR-796's implementation notes record a full-suite run with 6,013 passes and eight stable integration failures, including memory-demo mocking, three multi-turn/checkpointer assertions, three subgraph-interrupt assertions, and OpenAI `insufficient_quota` (`feature-requests/FR-796-reclassify-watcher2-witness-demos.md:223-232`). FR-798 narrows that evidence to the non-subgraph classes and explicitly excludes FR-797's three subgraph failures (`feature-requests/FR-798-full-suite-failure-classification-investigation.md:20-43`), matching the repo cure that bugs requiring substantial causal proof should split into investigation first, fix second (`.github/copilot-instructions.md:109-115`).

The four named failure classes have plausible independent boundaries rather than one product root cause. The RunPod test really reloads `yamlgraph.config` and depends on `sys.modules` identity (`tests/unit/test_runpod_provider.py:25-33`, `:117-133`). The memory-demo test patches `yamlgraph.tools.agent.execute_shell_tool` (`tests/integration/test_memory_demo.py:264-268`), while `agent.py` imports only `build_langchain_tool`/`build_python_tool` (`yamlgraph/tools/agent.py:18-22`) and `execute_shell_tool` is owned by `tool_builders.py` through `yamlgraph.tools.shell` (`yamlgraph/tools/tool_builders.py:17-20`, `:44-47`). The multi-turn graph and guard both hard-code OpenAI defaults (`examples/demos/multi-turn/graph.yaml:23-25`; `examples/demos/multi-turn/guard.yaml:15-18`), and the provider integration test skips on key absence only, not readiness or quota (`tests/integration/test_providers.py:69-81`).

The proposed evidence matrix is mostly measurable: it names exact tests, reproduction counts, state fields, Python-version comparison, and forbidden shortcuts (`feature-requests/FR-798-full-suite-failure-classification-investigation.md:85-131`). Strategic classification: **Pattern documentation / investigation artifact**, not a framework primitive. The deliverable is a causal report and follow-up disposition map; it should not add a runtime abstraction.

## Required revisions

### R-1: Disposition every cited prior-art boundary

Add a "Prior-art disposition" table before the Summary or in the Proposed Solution. The current FR lists FR-756, FR-761, FR-796, and FR-797 as prior art (`feature-requests/FR-798-full-suite-failure-classification-investigation.md:13-16`), but the judge doctrine requires prior art to be dispositioned before authority is granted (`.github/skills/judge-fr/doctrine.md:112-117`). Fold in this exact boundary map:

| Prior art | Binding disposition for FR-798 |
|---|---|
| FR-756 | Supplies the process/core classification precedent; FR-798 may classify failures across test surfaces but must not change the `process` marker, core-test job, or boundary lint. |
| FR-761 | Supplies the Python 3.12 constrained environment and dependency reproducibility command; FR-798 may run that environment and record blockers but must not regenerate constraints or alter dependency governance. |
| FR-796 | Supplies the validation-run source and observed non-retired-path failures; FR-798 owns only classification of the non-subgraph failures exposed there, not reopening FR-796's demo relocation scope. |
| FR-797 | Owns the three subgraph-interrupt failures; FR-798 may cite them only as excluded context and must not modify subgraph runtime, subgraph tests, interrupt demos, or FR-797 acceptance criteria. |

### R-2: Define the reproduction-harness collection policy

Amend the "supporting minimal test harnesses" authorization (`feature-requests/FR-798-full-suite-failure-classification-investigation.md:82-83`) and the memory-demo "minimal RED witness" requirement (`feature-requests/FR-798-full-suite-failure-classification-investigation.md:99-105`) so enforcement cannot accidentally commit a permanently red default suite. The revision must state exact authorized surfaces and collection behavior:

- The primary deliverable is `docs/investigations/fr798-full-suite-failures.md`.
- Raw command outputs may be quoted in that report or stored under `docs/investigations/fr798/` if too large for the report.
- Any committed pytest witness under `tests/**` must either pass, be explicitly `xfail`/`skip` with an FR-798 reason and owning follow-up disposition, and carry normal `@pytest.mark.req(...)`, or be returned to planning before commit.
- No default test selection, CI workflow, hook, marker policy, or retry/serialization mechanism may change to accommodate the investigation.

This preserves C-4's ban on hiding the original failures with retries/serialization (`feature-requests/FR-798-full-suite-failure-classification-investigation.md:172-175`) while preventing investigation scaffolding from becoming a new unclassified failure source.

### R-3: Gate live-provider success evidence on operator-selected readiness

Revise the provider-readiness section so it does not silently require the enforcer to spend quota or expose credentials. FR-798 currently requires a run with "one available provider" (`feature-requests/FR-798-full-suite-failure-classification-investigation.md:112-113`) and AC-06 requires absent-key, exhausted-key, and successful-readiness evidence (`feature-requests/FR-798-full-suite-failure-classification-investigation.md:151-153`). Fold in:

- Successful readiness may use only an operator-selected provider credential already available in the environment; do not create, purchase, rotate, or paste credentials under this FR.
- If no healthy provider credential is available, record that exact blocker and still fully evidence absent-key and exhausted-key behavior.
- Provider error bodies, account identifiers, keys, and request IDs must be redacted in committed artifacts while preserving the error class, HTTP status, provider name, and command.
- Do not convert arbitrary provider errors into skips after execution begins; the policy recommendation belongs in the report.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `docs/investigations/fr798-full-suite-failures.md` |
| D-2 | Optional raw-output appendices under `docs/investigations/fr798/` if the report would otherwise become unreadable |
| D-3 | Optional minimal reproduction harnesses only on the revised, explicitly non-polluting surfaces from R-2 |
| D-4 | Follow-up dispositions recorded inside the investigation report, including first consumer and boundary for each proposed follow-up FR |
| D-5 | FR-798 implementation-status note after the investigation completes |

Not authorized: production changes under `yamlgraph/**`; graph or prompt artifact edits; CI workflow, hook, branch-protection, pytest marker, or test-selection policy changes; dependency or constraints regeneration; provider credential creation or rotation; retries, sleeps, suite serialization, deselection, or skip-after-failure policies; subgraph runtime/tests/demos/acceptance criteria owned by FR-797; fixes to the classified defects except non-polluting reproduction witnesses allowed by R-2.

## Revised acceptance criteria

- [ ] AC-01: FR-798 is amended with R-1 through R-3 before enforcement authority is used.
- [ ] AC-02: `docs/investigations/fr798-full-suite-failures.md` records the git SHA, Python/dependency environment, exact commands, and raw outcomes for all four non-subgraph classes.
- [ ] AC-03: The RunPod test has serial (>=10) and xdist (>=20) reproduction counts; the report identifies the operation that breaks module identity or states the bounded search that failed to reproduce it.
- [ ] AC-04: A deterministic witness proves or falsifies the hypothesis that a foreign test/fixture removes or replaces `yamlgraph.config` in `sys.modules`; retries and suite serialization are not accepted as the investigation result.
- [ ] AC-05: The memory-demo failure is traced from its stale patch target to the current shell-tool owner, with a minimal reproduction and a proposed owning test seam.
- [ ] AC-06: Any committed reproduction harness follows the R-2 collection policy and does not add a new unclassified default-suite failure.
- [ ] AC-07: Multi-turn failure artifacts include `errors`, response/intent, interrupt state, and checkpoint state for every turn, and distinguish LLM failure from checkpoint behavior.
- [ ] AC-08: OpenAI absent-key, exhausted-key, and successful-readiness states are separately evidenced when a healthy operator-selected credential is available; if not available, the report records the exact readiness blocker while still evidencing absent-key and exhausted-key behavior.
- [ ] AC-09: The relevant matrix is run under the FR-761 Python 3.12 constrained environment as well as the active local environment, or the exact setup blocker is recorded.
- [ ] AC-10: Each confirmed defect receives one disposition: existing FR, proposed follow-up FR with first consumer and boundary, test correction, environment/operations action, or no-action with evidence.
- [ ] AC-11: FR-797's subgraph interrupt scope is not modified, duplicated, or used as evidence of FR-798 completion.
- [ ] AC-12: No production files under `yamlgraph/**`, graph/prompt artifacts, CI workflows, hooks, branch-protection policy, pytest marker policy, dependency governance, or test-gate policy change under this investigation.
- [ ] AC-13: Committed artifacts redact provider secrets and account/request identifiers while preserving enough error class/status/provider detail to reproduce the classification.
- [ ] AC-14: The investigation report ends with a recommended enforcement order based on causal dependency, not failure count.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement until R-1 through R-3 are folded into `feature-requests/FR-798-full-suite-failure-classification-investigation.md`. | GATE |
| C-2 | Treat this as investigation authority only: classify, reproduce, report, and disposition; do not repair product/runtime behavior or weaken tests/gates. | GATE |
| C-3 | Any committed reproduction harness must follow the revised collection policy and must not create a new default-suite red unrelated to the existing classified failures. | GATE |
| C-4 | Provider-success evidence may use only operator-selected existing credentials; absence of a healthy credential is a reportable blocker, not permission to create or expose secrets. | GATE |
| C-5 | If work touches FR-797's subgraph scope, graph/prompt artifacts, CI/hooks, dependency governance, or test-selection policy, stop and return for a separate judged FR. | GATE |

Authority granted: after the required revisions are folded, enforcement may produce the FR-798 investigation report and non-polluting reproduction evidence needed to classify the four non-subgraph failure classes and recommend separate follow-up order.
