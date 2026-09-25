# Judgement: FR-1085 One resolved `max_concurrency` for every run entry point

**Prior art:** `FR-1085-default-max-concurrency.md` is the FR judged here; FR-1068 (Rejected) is its predecessor, dispositioned in the FR.

**Verdict:** APPROVED WITH REVISIONS — the shared run-level resolver is a feasible correction to an existing LangGraph primitive, but authority activates only after the FR narrows its “every entry point” claim, folds the recorded default of 8 consistently, and tests cap semantics across supported Python versions.

**Reviewed against:** `feature-requests/FR-1085-default-max-concurrency.md`; `feature-requests/FR-1068-default-max-concurrency.md`; `feature-requests/FR-1068-default-max-concurrency.judgement.md`; `feature-requests/FR-984-map-fan-out-max-concurrency.md`; `feature-requests/FR-985-census-coverage-floor-and-population-header.md`; `feature-requests/030-map-concurrency-control.md`; `docs/issues-2026-09-24.md`; `README.md`; `ARCHITECTURE.md`; `pyproject.toml`; `feature-requests/TEMPLATE.md`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `yamlgraph/__init__.py`; `yamlgraph/cli/__init__.py`; `yamlgraph/cli/graph_commands.py`; `yamlgraph/cli/graph_run_helpers.py`; `yamlgraph/compile/graph_loader.py`; `yamlgraph/executor_async.py`; `yamlgraph/observability/otel.py`; `yamlgraph/utils/llm_bounds.py`; `yamlgraph/utils/validators.py`; `reference/graph-yaml.md`; `reference/development-operations.md`; `examples/demos/person_profile_census/graph.yaml`; `tests/unit/test_fr984_map_max_concurrency.py`; `tests/unit/test_invoke_graph.py`; `tests/unit/test_async_executor.py`.

## What is sound

The problem is real and bounded. The CLI currently copies only its flag or the graph value into `RunnableConfig` (`yamlgraph/cli/graph_run_helpers.py:145-150`), while `invoke_graph`, `run_graph_async`, and native streaming pass caller config without resolving the graph setting (`yamlgraph/compile/graph_loader.py:395-417`; `yamlgraph/observability/otel.py:267-319`; `yamlgraph/executor_async.py:287-323`). The witnessed unset sync width was 16 on the 12-CPU host, and only 1 of 202 graphs declares a width (`docs/issues-2026-09-24.md:75-83,135-137`). FR-984 already proved that LangGraph's run-level primitive caps both sync and async map execution, so reusing it adds no yamlgraph scheduler (`feature-requests/FR-984-map-fan-out-max-concurrency.md`, Problem and Alternatives Considered; `tests/unit/test_fr984_map_max_concurrency.py:164-239`).

The FR resolves the two binding defects from the rejected predecessor. Its in-body research record compares five genuine solution classes, preserves provider-boundary admission as dissent, and answers `is_this_a_graph` (`FR-1085:193-231`), satisfying the equivalent committed-record route allowed by `feature-requests/TEMPLATE.md:11-20`. The operator has also selected one fixed default of 8 (`FR-1085:6`), with the quota evidence and uncertainty stated rather than disguised (`FR-1085:138-158`). Rejected FR-1068 and the older wrong-layer FR-030 are both distinguished (`FR-1085:17-43,213-221`).

The solution is architecturally aligned: one resolver extends the established CLI-over-YAML `RunnableConfig` path, validates external values at the run boundary, and applies the result through existing LangGraph execution (`FR-1085:101-130`; `.github/copilot-instructions.md:182-203`). It is one responsibility: resolve and propagate one whole-run cap. Strategic classification is **contrib/existing-primitive correction**: two witnessed consumers expose a gap in an abstraction LangGraph already supplies, so this is not authority for a new framework scheduler. Tests can be derived directly once the cap-vs-occupancy and public-surface ambiguities below are removed.

## Required revisions

### R-1: Narrow the public-surface claim to the named managed boundaries

Rename the FR and rewrite Summary, Value Statement, Ideal Result, documentation promise, and Out of scope so they claim consistent resolution only for: CLI sync, CLI `--async`, CLI `--stream`, `invoke_graph`, `run_graph_async`, and `run_graph_streaming_native`. State explicitly that callers using the public `load_and_compile(...).compile().invoke/ainvoke` pattern must still pass `max_concurrency` themselves and are not changed by this FR. That direct pattern is exported and documented (`yamlgraph/__init__.py:11,41`; `README.md:123-127`), so “every way a graph runs” and “any entry point” are false as written (`FR-1085:1,46-53,95-99`). Do not expand this FR to wrap raw compiled LangGraph apps, benchmark execution, graph tools, subgraph invocation, or provider-level admission.

### R-2: Fold the operator decision and delete the stale decision branch

Replace every placeholder or conditional default with the fixed built-in value `8`. Remove “value: human decision below”, rename or remove “Human decision needed”, and delete the “no global default” branch (`FR-1085:52-53,110,132-161`). Extend the header decision to record the accepted risks mechanically: quotas below 8 may emit 429s until overridden, and the default can raise sync width from 6 to 8 on a 2-CPU host (`FR-1085:87-88,138-158`). Revise AC-06 from a future condition into an assertion that this already-recorded decision and risk statement remain in the frozen FR.

### R-3: Test the cap contract, source selection, and supported runtimes separately

Replace “peaks at exactly” in AC-02 through AC-04 with two complementary witnesses:

1. resolver tests assert the exact selected integer for caller, graph, environment, and default, with every lower-priority source populated by a conflicting value; and
2. a 40-branch behavioural fixture records actual in-flight branches and proves the observed peak never exceeds the selected cap on each authorized boundary.

If exact saturation is retained as an additional observation, make the fixture synchronize deterministically and do not make exact occupancy the semantic gate: `max_concurrency` is documented as a cap, and the enforced precedent asserts `peak <= N` (`reference/graph-yaml.md:245`; `tests/unit/test_fr984_map_max_concurrency.py:220-239`). For RED host-width tests, patch the function used by each supported interpreter: `os.cpu_count` on Python 3.11/3.12 and `os.process_cpu_count` on Python 3.13, rather than naming only the 3.13 seam; the project supports all three (`pyproject.toml:10,18-20`). Generate any CLI graph file under `tmp_path` or reuse an in-test graph mapping; no committed example or production graph edit is authorized.

### R-4: Complete boundary-validation and config-preservation criteria

Expand AC-05 so caller values reject booleans, strings, fractions, zero, and negatives, matching the existing YAML contract (`yamlgraph/utils/validators.py:209-221`); retain the named invalid environment cases and add positive-value witnesses for both sources. Require every managed entry point to raise before a node runs, preserve unrelated `RunnableConfig` fields such as `configurable`, callbacks, and tracing metadata, and leave the caller-owned config mapping unmodified. Add a witness that `run_graph_async` without graph-width metadata still resolves caller → environment → default rather than silently omitting the cap. These checks prevent the resolver from fixing width by replacing or mutating the pass-through config contracts visible in `run_graph_async` and `invoke_graph` (`yamlgraph/observability/otel.py:267-319`; `yamlgraph/compile/graph_loader.py:395-417`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | One typed shared resolver for caller value → graph value → `YAMLGRAPH_MAX_CONCURRENCY` → built-in `8`, with positive-integer validation |
| D-2 | Resolver integration at CLI sync, CLI `--async`, CLI `--stream`, `invoke_graph`, `run_graph_async`, and `run_graph_streaming_native` |
| D-3 | Async compiled-app metadata sufficient for `run_graph_async` to recover the graph-level value when loaded through `load_and_compile_async` |
| D-4 | Behavioural and resolver tests for precedence, caps, invalid values, config preservation, and Python 3.11-3.13 CPU seams |
| D-5 | `reference/graph-yaml.md` and `reference/development-operations.md` documentation |
| D-6 | Requirement capability, tagged tests, changelog fragment, FR implementation record, and diary entry |

Not authorized: changing any graph's own `max_concurrency`; committed fixture/example graph edits; changing `load_and_compile` or raw compiled `app.invoke/ainvoke`; per-map concurrency; provider/model admission semaphores; rate limiting; retry or timeout changes; benchmark, graph-tool, or subgraph-runner refactors; provider-specific defaults; any yamlgraph scheduler.

## Revised acceptance criteria

- [ ] AC-01 (RED): a generated 40-item map fixture records peak in-flight branches. On current code, CLI sync, CLI `--async`, `run_graph_async`, and `invoke_graph` each exceed 8 when the interpreter's ThreadPoolExecutor CPU source is patched to 64; the test records each measured peak. Python 3.11/3.12 patch `os.cpu_count`; Python 3.13 patches `os.process_cpu_count`.
- [ ] AC-02 (GREEN): with no configured width, resolver tests select exactly `8`, and the same behavioural fixture records `1 <= peak <= 8` through CLI sync, CLI `--async`, CLI `--stream`, `invoke_graph`, `run_graph_async`, and `run_graph_streaming_native`, at patched CPU counts 2 and 64.
- [ ] AC-03: precedence tests populate all four levels with conflicting values and assert exact resolution of caller over graph over `YAMLGRAPH_MAX_CONCURRENCY` over built-in `8`; the CLI flag is the CLI caller value. Behavioural cases record a peak no greater than the selected value.
- [ ] AC-04: a graph with `config.max_concurrency: 3` resolves to 3 and records `peak <= 3` through `run_graph_async` and `invoke_graph` when caller width is absent; a caller width of 2 resolves to 2 and records `peak <= 2`.
- [ ] AC-05: environment values `""`, `abc`, `0`, `-1`, `2.5`, and `true`, and caller values `True`, `False`, `"4"`, `2.5`, `0`, and `-1`, raise `ValueError` naming the source and offending value before any node runs. Positive integers from caller and environment are accepted.
- [ ] AC-06: the FR header records built-in width 8 and accepts both documented risks: provider quotas below 8 may 429 until overridden, and a 2-CPU sync host can rise from width 6 to 8. No undecided-default or no-global-default branch remains.
- [ ] AC-07: each programmatic boundary preserves unrelated `RunnableConfig` fields and does not mutate the caller-owned mapping. A `run_graph_async` app lacking graph-width metadata still follows caller → environment → built-in 8.
- [ ] AC-08: `reference/graph-yaml.md` and `reference/development-operations.md` state the exact precedence, fixed default 8, six managed boundaries, validation behavior, and explicit exclusion of raw compiled `app.invoke/ainvoke`.
- [ ] AC-09: a new requirement in a capability file covers every production branch; every test is tagged; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-10: the changelog fragment, FR implementation record, and diary entry describe the narrowed managed-boundary contract and cite the behavioural peak witnesses.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-4 are folded into FR-1085 before GREEN implementation begins. | GATE |
| C-2 | The implementation delegates scheduling solely to LangGraph's `RunnableConfig["max_concurrency"]`; no yamlgraph semaphore, batching loop, or rate limiter is added. | GATE |
| C-3 | No raw compiled-app, provider-admission, retry, timeout, graph-artifact, benchmark, graph-tool, or subgraph-runner change lands under this FR. | GATE |
| C-4 | RED witnesses exercise actual branch occupancy on every authorized boundary; resolver-only assertions do not substitute for behavioural caps. | GATE |
| C-5 | Caller config remains unmutated and all unrelated run-config fields survive resolution. | GATE |

Authority granted: after R-1 through R-4 are folded, implement the fixed-width-8 shared resolver and wire only the six named managed execution boundaries and their directly required tests, documentation, and traceability artifacts.
