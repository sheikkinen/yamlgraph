# Feature Request: One resolved `max_concurrency` at the six managed run boundaries

**Priority:** MEDIUM
**Type:** Bug
**Status:** Implemented (2026-09-26, branch `feat/fr1085-max-concurrency`) — see "Implementation record". Judged — APPROVED WITH REVISIONS ([judgement](FR-1085-default-max-concurrency.judgement.md)); R-1–R-4 folded 2026-09-26. Authority active (2026-09-26): C-1 satisfied (R-1–R-4 folded); human review recorded — operator instruction 'proceed with all fr changes' (2026-09-26).
**Human decision (2026-09-25, operator):** one fixed built-in width of 8 for every provider and managed entry point, re-confirming the FR-1068 / PR #691 answer. Accepted risks: a provider quota below 8 may return 429s until overridden; on a 2-CPU host the sync width rises from 6 to 8. See "Human decisions".
**Effort:** 0.5 days
**Requested:** 2026-09-25
**First consumer / first event:** the next `innovation_matrix` run
(`examples/demos/innovation_matrix/pipeline.yaml`). On 2026-09-24, on a
12-CPU Mac, it opened 16 simultaneous provider requests because no width was
set ([docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §1.2). The
same graph on another host, or through the async API, opens a different
number.
**Research:** FR-890 research route **skipped by operator decision
(2026-09-25): "refile. skip research — document as skipped"**. Substitute:
the in-body "Alternatives Considered" section below (five solution classes,
one chosen, one preserved dissent, `is_this_a_graph` answer), plus
[docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §1.2 and §2 D6, and
the FR-984 / FR-985 width runs.
**Prior art:**
[FR-1068](FR-1068-default-max-concurrency.md) (REJECTED,
[judgement](FR-1068-default-max-concurrency.judgement.md)). This FR replaces
it. Answers to each objection:
- R-1 (research): five solution classes are compared below, including the
  four the judgement names, with precedent, dissent and `is_this_a_graph`.
- R-2 (human default-risk decision): decided. The operator confirmed 8 on
  2026-09-25 with both risks found after the PR #691 answer (Problem,
  points 3 and 4) accepted; see "Human decisions".
- R-2 (entry points, precedence, errors): the Proposed Solution names every
  entry point, the full precedence order, and the error for each bad input.
- AC-03 (measure peak in-flight branches, not the config dict): AC-01..AC-04
  count concurrent branches in a real compiled graph.

[FR-984](FR-984-map-fan-out-max-concurrency.md) (Enforced). It added
`config.max_concurrency` and `--max-concurrency` and left the default unset.
This FR keeps both and adds a default after them.
[FR-985](FR-985-census-coverage-floor-and-population-header.md) (Shelved).
Holds the width 12 / 4 / 2 run table used as evidence below.
[FR-030](030-map-concurrency-control.md) (Won't Fix). It rejected a
per-map concurrency field: "belongs in LLM provider". This FR adds no
per-map field. Class 4 below is the provider-layer option FR-030 pointed to;
it is kept as dissent, not chosen.

## Summary

Resolve `max_concurrency` once, in one place, at six managed run
boundaries: CLI sync, CLI `--async`, CLI `--stream`, `invoke_graph`,
`run_graph_async` and `run_graph_streaming_native`. The order is: explicit
run value, then the graph's `config.max_concurrency`, then
`YAMLGRAPH_MAX_CONCURRENCY`, then the built-in default 8. Callers that use
the public `load_and_compile(...).compile()` pattern and call
`invoke`/`ainvoke` themselves
([yamlgraph/__init__.py#L11](../yamlgraph/__init__.py#L11),
[README.md#L123-L127](../README.md#L123-L127)) are not changed: they must
still pass `max_concurrency` themselves.

## Value Statement

A graph author can say how many provider requests a run opens at once
without knowing the host's CPU count or which of the six managed boundaries
the caller used.

## Problem

1. **Only the CLI reads the graph's setting.** `_build_run_config` copies
   `--max-concurrency` or `config.max_concurrency` into the run config
   ([graph_run_helpers.py#L145-L150](../yamlgraph/cli/graph_run_helpers.py#L145-L150)).
   The API paths pass the caller's config through unchanged:
   `run_graph_async` ([otel.py#L283](../yamlgraph/observability/otel.py#L283),
   [#L319](../yamlgraph/observability/otel.py#L319)),
   `run_graph_streaming_native`
   ([executor_async.py#L318](../yamlgraph/executor_async.py#L318)) and
   `invoke_graph`
   ([graph_loader.py#L416](../yamlgraph/compile/graph_loader.py#L416)).
   A graph that sets `config.max_concurrency: 4`
   ([person_profile_census/graph.yaml#L18](../examples/demos/person_profile_census/graph.yaml#L18))
   is capped from the CLI and not capped from the API. The reference calls
   the setting a "whole-invocation cap"
   ([graph-yaml.md#L245](../reference/graph-yaml.md#L245)).
2. **Unset width on the sync path depends on the host.** LangGraph 1.2.11
   builds its sync pool with `max_workers=config.get("max_concurrency")`
   (`langchain_core/runnables/config.py` L673). With no value, Python 3.13's
   `ThreadPoolExecutor` uses `min(32, (os.process_cpu_count() or 1) + 4)`.
   That is 16 on the 12-CPU witness host and 32 on a 28-CPU host.
3. **Unset width on the async path has no LangGraph gate.**
   `AsyncBackgroundExecutor` creates a semaphore only when
   `max_concurrency` is set (`langgraph/pregel/_executor.py` L135-L140).
   The effective async width is then whatever the node scheduling allows.
   Not measured yet; AC-01 measures it.
4. **A fixed default can raise width on small hosts.** On a 2-CPU container
   the sync pool today is 6. A default of 8 raises it to 8.
5. **The rejected FR's RED test would not move the pool.** It patched
   `os.cpu_count`, which only Python 3.11 and 3.12 read; Python 3.13 reads
   `os.process_cpu_count` (checked on 3.13.5). The project supports all three
   ([pyproject.toml#L10](../pyproject.toml#L10)), so the test must patch the
   function the running interpreter reads.
6. **Almost no graph sets the value.** 1 of 202 graphs sets
   `max_concurrency` (plan §2 D6).

## Ideal Result

For any graph run through one of the six managed boundaries, the number of
branches in flight at once is capped by a declared value: the caller's, the
graph's, the deployment's, or the documented default 8. Never the host's CPU
count, never "unbounded". Raw compiled-app calls stay caller-owned.

## Proposed Solution

1. **One resolver.** A single function returns the width for a run, in this
   order:
   1. an explicit value in the caller's run config (`config["max_concurrency"]`),
      or `--max-concurrency` on the CLI;
   2. the graph's `config.max_concurrency`
      ([graph_loader.py#L91-L93](../yamlgraph/compile/graph_loader.py#L91-L93));
   3. `YAMLGRAPH_MAX_CONCURRENCY` from the environment;
   4. the built-in default `8`.
2. **Each managed boundary calls it.** The CLI (`_build_run_config`, which
   serves sync, `--async` and `--stream`), `invoke_graph`, `run_graph_async`
   and `run_graph_streaming_native`. For `run_graph_async`, the compiled app
   carries the graph's value the same way it already carries
   `_yamlgraph_graph_name`
   ([executor_async.py#L253](../yamlgraph/executor_async.py#L253)). An app
   without that value resolves caller → environment → 8; the cap is never
   silently omitted. The resolver works on a copy: every other
   `RunnableConfig` field (`configurable`, callbacks, tracing metadata)
   survives, and the caller's mapping is not modified.
3. **Errors at the boundary.** Every level must be a positive integer, and a
   bad value raises before any node runs.
   The CLI already rejects `0` and negatives at parse time
   ([cli/__init__.py#L125-L134](../yamlgraph/cli/__init__.py#L125-L134)).
   The YAML value already fails at load
   ([validators.py#L237-L249](../yamlgraph/utils/validators.py#L237-L249)).
   New: a caller config value that is a boolean, string, fraction, `0` or
   negative raises `ValueError`, matching the YAML rule.
   `YAMLGRAPH_MAX_CONCURRENCY` that is empty-but-set, non-integer, `0`,
   negative or a boolean word raises at first resolve, naming the variable
   and the value. This is modelled on `LLM_REQUEST_TIMEOUT`
   ([llm_bounds.py#L34-L53](../yamlgraph/utils/llm_bounds.py#L34-L53)),
   except that an empty value is an error here, not "unset".
4. **Documentation.** `reference/graph-yaml.md` (the `max_concurrency` row,
   [#L245](../reference/graph-yaml.md#L245)) and
   `reference/development-operations.md` (Key Environment Variables) state
   the order, the default 8, the six managed boundaries, the validation rules,
   and that raw compiled `app.invoke`/`ainvoke` is not covered.

## Human decisions

**2026-09-25, operator — built-in default: 8.** One fixed width for every
provider and managed boundary when nothing else sets it, re-confirming the
FR-1068 / PR #691 answer (commit `d2564be2`). Accepted risks:

- a provider quota below 8 may return 429s until the caller, graph or
  environment overrides the width;
- on a 2-CPU host the sync width rises from 6 to 8 (Problem 4).

Evidence behind the value:

| Witness | Width | Result |
|---|---|---|
| Azure `gpt-5.4-mini`, person-profile census (FR-984, FR-985) | 12 | 1249 × 429, 100 of 259 rows lost |
| same | 4 | 727 × 429, 22 rows lost |
| same | 2 | 349 × 429, 2 rows lost |
| Anthropic haiku, `innovation_matrix` (plan §1.2) | 16 | no 429 recorded; 7 of 16 first-wave requests hit the 30 s request timeout |

What the evidence does not show:
- No run at width 8 exists on any provider.
- The width-16 timeouts match the 30 s cap on a non-streaming call with a
  27 s median (plan §1.2, D7). They do not show that width caused them.
- The Azure quota is one deployment's. It bore width 2. A default of 8 fails
  on it, as does today's unset width.

**2026-09-26, operator — advisory judgement reviewed.** Instruction:
"proceed with all fr changes". R-1–R-4 folded the same day.

## Acceptance Criteria

- [x] AC-01 (RED): a generated 40-item map fixture records peak in-flight
  branches. On current code, CLI sync, CLI `--async`, `run_graph_async` and
  `invoke_graph` each exceed 8 when the interpreter's ThreadPoolExecutor CPU
  source is patched to 64; the test records each measured peak. Python
  3.11/3.12 patch `os.cpu_count`; Python 3.13 patches `os.process_cpu_count`.
- [x] AC-02 (GREEN): with no configured width, resolver tests select exactly
  `8`, and the same behavioural fixture records `1 <= peak <= 8` through CLI
  sync, CLI `--async`, CLI `--stream`, `invoke_graph`, `run_graph_async` and
  `run_graph_streaming_native`, at patched CPU counts 2 and 64.
- [x] AC-03: precedence tests populate all four levels with conflicting
  values and assert exact resolution of caller over graph over
  `YAMLGRAPH_MAX_CONCURRENCY` over built-in `8`; the CLI flag is the CLI
  caller value. Behavioural cases record a peak no greater than the selected
  value.
- [x] AC-04: a graph with `config.max_concurrency: 3` resolves to 3 and
  records `peak <= 3` through `run_graph_async` and `invoke_graph` when
  caller width is absent; a caller width of 2 resolves to 2 and records
  `peak <= 2`.
- [x] AC-05: environment values `""`, `abc`, `0`, `-1`, `2.5` and `true`,
  and caller values `True`, `False`, `"4"`, `2.5`, `0` and `-1`, raise
  `ValueError` naming the source and offending value before any node runs.
  Positive integers from caller and environment are accepted.
- [x] AC-06: the FR header records built-in width 8 and accepts both
  documented risks: provider quotas below 8 may 429 until overridden, and a
  2-CPU sync host can rise from width 6 to 8. No undecided-default or
  no-global-default branch remains.
- [x] AC-07: each programmatic boundary preserves unrelated
  `RunnableConfig` fields and does not mutate the caller-owned mapping. A
  `run_graph_async` app lacking graph-width metadata still follows caller →
  environment → built-in 8.
- [x] AC-08: `reference/graph-yaml.md` and
  `reference/development-operations.md` state the exact precedence, fixed
  default 8, six managed boundaries, validation behaviour, and explicit
  exclusion of raw compiled `app.invoke/ainvoke`.
- [x] AC-09: a new requirement in a capability file covers every production
  branch; every test is tagged; `python scripts/req_coverage.py --strict`
  passes.
- [x] AC-10: the changelog fragment, FR implementation record and diary
  entry describe the narrowed managed-boundary contract and cite the
  behavioural peak witnesses.

All fixture graphs are generated under `tmp_path` or built in the test; no
committed example or production graph is edited.

## Scope (frozen by judgement)

| Deliverable | Surface |
|---|---|
| D-1 | One typed shared resolver for caller value → graph value → `YAMLGRAPH_MAX_CONCURRENCY` → built-in `8`, with positive-integer validation |
| D-2 | Resolver integration at CLI sync, CLI `--async`, CLI `--stream`, `invoke_graph`, `run_graph_async` and `run_graph_streaming_native` |
| D-3 | Async compiled-app metadata sufficient for `run_graph_async` to recover the graph-level value when loaded through `load_and_compile_async` |
| D-4 | Behavioural and resolver tests for precedence, caps, invalid values, config preservation and Python 3.11–3.13 CPU seams |
| D-5 | `reference/graph-yaml.md` and `reference/development-operations.md` documentation |
| D-6 | Requirement capability, tagged tests, changelog fragment, FR implementation record and diary entry |

Not authorized: changing any graph's own `max_concurrency`; committed
fixture/example graph edits; changing `load_and_compile` or raw compiled
`app.invoke/ainvoke`; per-map concurrency; provider/model admission
semaphores; rate limiting; retry or timeout changes; benchmark, graph-tool
or subgraph-runner refactors; provider-specific defaults; any yamlgraph
scheduler.

## Conditions for enforcement

Gates C-1 to C-5 in the
[judgement](FR-1085-default-max-concurrency.judgement.md#conditions-for-enforcement)
apply: revisions folded before GREEN (C-1), scheduling only through
LangGraph's `RunnableConfig["max_concurrency"]` (C-2), no change outside
the six managed boundaries (C-3), behavioural occupancy witnesses on every
boundary (C-4), caller config unmutated with unrelated fields kept (C-5).

## Alternatives Considered

Solution classes (chosen: 1):

1. **One run-level resolver with a fixed default, applied at every managed
   boundary.** Chosen. It uses the key LangGraph already honours, so yamlgraph
   adds no scheduler (the FR-984 design, [graph-yaml.md#L245](../reference/graph-yaml.md#L245)).
   It also closes the API gap in Problem 1, which exists with or without a
   default. Precedent: FR-984's CLI-over-YAML order, extended by one level.
2. **Provider-specific default widths.** A table in the provider layer,
   like the timeout floors in `llm_bounds.py` (`_PROVIDER_TIMEOUT_FLOORS`,
   [llm_bounds.py#L23](../yamlgraph/utils/llm_bounds.py#L23)). Rejected:
   the LangGraph knob is per run, and one run can call several providers.
   The only quota evidence is one Azure deployment. A per-provider number
   would be a guess per provider instead of one guess.
3. **Require an explicit per-graph setting.** A lint rule that fails any
   graph with a map or parallel fan-out and no `max_concurrency`. Rejected:
   it forces edits to every graph holding one of the 67 map nodes
   (plan §2) through `scripts/author.sh`. The right width depends on the deployment's quota,
   which the graph author does not know either.
4. **Concurrency admission at the provider boundary.** A per-provider,
   per-model semaphore around every LLM call, inside `create_llm()` or its
   clients. **Preserved dissent:** this is the only class that bounds what
   the provider actually receives. It holds across nested maps, parallel
   edges and several runs in one API process, which a run-level width does
   not. It is also where FR-030 said the control belongs. It loses for now:
   it is a new scheduler inside yamlgraph, with separate sync and async
   implementations. No consumer runs several graphs in one process against
   one quota. It composes with class 1 if one appears.
5. **Requests-per-second limiter on the clients.** LangChain ships
   `InMemoryRateLimiter` (`langchain_core/rate_limiters.py` L67). It matches a
   per-minute quota better than a width does. Rejected: it needs a rate per
   deployment, which yamlgraph cannot know. It spaces requests but does not
   cap how many are in flight, so slow responses still pile up.

Status quo (leave unset, document only) is not a class: it keeps Problems 1–3.

`is_this_a_graph`: no. Resolving a number from four sources is a
deterministic lookup at the run boundary, not a model decision.

## Out of scope

Per-map concurrency fields (FR-030). Provider-level admission (class 4) and
rate limiting (class 5). Retry and timeout behaviour
([FR-1079](FR-1079-retry-ownership.md), FR-708). Raw compiled-app
`invoke`/`ainvoke` and `load_and_compile`; benchmark execution, graph tools
and subgraph invocation. Changing any graph's own `max_concurrency` value,
including the census graph's `4` → `2` noted in FR-984; that is a graph edit
through `scripts/author.sh`.

## Related

- Replaces: [FR-1068](FR-1068-default-max-concurrency.md)
- Extends: [FR-984](FR-984-map-fan-out-max-concurrency.md)
- Evidence: [FR-985](FR-985-census-coverage-floor-and-population-header.md)
- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §2 D6, §7 D
- Composes with: [FR-1079](FR-1079-retry-ownership.md)

## Implementation record

Commits on `feat/fr1085-max-concurrency`: RED `887b354c`, GREEN
`6163d31c`, record (this commit).

- **D-1** `resolve_max_concurrency`, `with_max_concurrency`,
  `graph_width_of` in
  [validators.py](../yamlgraph/utils/validators.py), beside FR-984's
  `validate_max_concurrency`, which now also validates the graph level.
  Placed there, not in a new module, so the FR-335 module-map line budget
  is untouched. An empty-but-set `YAMLGRAPH_MAX_CONCURRENCY` is an error.
- **D-2** `_build_run_config` (CLI sync, `--async`, `--stream`),
  `invoke_graph`, `run_graph_async`, `run_graph_streaming_native`. Each
  passes a copy of the caller's config with `max_concurrency` set; scheduling
  stays with LangGraph (C-2).
- **D-3** `load_and_compile_async` sets `_yamlgraph_max_concurrency` on the
  compiled app; `graph_width_of` reads the instance `__dict__` so an app
  without it (or a mock) resolves caller → environment → 8.
- **D-4** [test_fr1085_default_max_concurrency.py](../tests/unit/test_fr1085_default_max_concurrency.py):
  69 tests. The CPU seam patches `os.process_cpu_count` on 3.13+ and
  `os.cpu_count` on 3.11/3.12.
- **D-5** [graph-yaml.md](../reference/graph-yaml.md) `max_concurrency`
  row and [development-operations.md](../reference/development-operations.md)
  Key Environment Variables.
- **D-6** CAP-281 / REQ-YG-698; changelog
  `changelog/unreleased/fr-1085-default-max-concurrency.md`; diary
  `docs/diary/diary-2026-09-26-the-mock-width.md`.

**Behavioural peaks** (40-item map, 50 ms sync Python worker, no width
set):

| Boundary | RED, 64 CPUs | GREEN, 64 CPUs | GREEN, 2 CPUs |
|---|---|---|---|
| CLI sync | 32 | 8 | 8 |
| CLI `--async` | 32 | 8 | 6 |
| CLI `--stream` | 32 | 8 | 6 |
| `invoke_graph` | 32 | 8 | 8 |
| `run_graph_async` | 32 | 8 | 6 |
| `run_graph_streaming_native` | 32 | 8 | 6 |

AC-01 names four RED boundaries; all six measured 32. The 2-CPU async
peaks of 6 are not the resolver: the fixture's worker is a sync function,
which LangGraph runs on asyncio's default executor, itself sized
`min(32, cpus + 4)`. Width 8 is a cap, not a floor.

**Deviations and test changes.**
- FR-984's `test_absent_everywhere_omits_key` became
  `test_absent_everywhere_resolves_default` (asserts 8; tagged REQ-YG-698).
- 17 existing tests passed a bare `MagicMock` as the graph config. Its
  auto-attribute `max_concurrency` used to flow unchecked into the CLI run
  config; the resolver now rejects it, so those mocks declare
  `max_concurrency=None`. Exact-config assertions in
  `test_invoke_graph.py`, `test_async_executor.py` and
  `test_otel_observability.py` now include `"max_concurrency": 8`.
- The RED helper `_run_cli` turned a nonzero CLI exit into
  `AssertionError`; it now re-raises the `SystemExit`, so AC-05 sees the
  CLI's exit 1 on a bad environment value. No assertion was weakened.
- `invoke_graph` imports the resolver inside the function and its
  docstring was shortened to keep `graph_loader.py` at the 450-line gate.
  The module sits at the cap; the next change there needs a split.
