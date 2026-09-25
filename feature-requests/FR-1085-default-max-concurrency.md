# Feature Request: One resolved `max_concurrency` for every run entry point

**Priority:** MEDIUM
**Type:** Bug
**Status:** Judged — APPROVED WITH REVISIONS ([judgement](FR-1085-default-max-concurrency.judgement.md)); authority gated on folding the required revisions. No implementation authority yet.
**Human decision (2026-09-25, operator):** suggested default accepted — one fixed built-in width of 8 for every provider and entry point, re-confirming the FR-1068 / PR #691 answer.
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
- R-2 (human default-risk decision): not decided here. See
  "Human decision needed". FR-1068's header records an operator answer of
  width 8 (commit `d2564be2`, PR #691). This FR asks the operator to confirm
  it against two facts found after that answer (Problem, points 3 and 4).
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

Resolve `max_concurrency` once, in one place, for every way a graph runs:
the CLI (sync, `--async`, `--stream`), `run_graph_async`,
`run_graph_streaming_native` and `invoke_graph`. The order is: explicit run
value, then the graph's `config.max_concurrency`, then an environment
variable, then a built-in default. The value of the built-in default is a
human decision.

## Value Statement

A graph author can say how many provider requests a run opens at once
without knowing the host's CPU count or which entry point the caller used.

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
   ([graph_loader.py#L417](../yamlgraph/compile/graph_loader.py#L417)).
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
   `os.cpu_count`. Python 3.13 reads `os.process_cpu_count` (checked on
   3.13.5). The test must patch the function the running Python reads.
6. **Almost no graph sets the value.** 1 of 202 graphs sets
   `max_concurrency` (plan §2 D6).

## Ideal Result

For any graph and any entry point, the number of branches in flight at once
is a declared value: the caller's, the graph's, the deployment's, or a
documented default. Never the host's CPU count, never "unbounded".

## Proposed Solution

1. **One resolver.** A single function returns the width for a run, in this
   order:
   1. an explicit value in the caller's run config (`config["max_concurrency"]`),
      or `--max-concurrency` on the CLI;
   2. the graph's `config.max_concurrency`
      ([graph_loader.py#L91-L93](../yamlgraph/compile/graph_loader.py#L91-L93));
   3. `YAMLGRAPH_MAX_CONCURRENCY` from the environment;
   4. the built-in default (value: human decision below).
2. **Every entry point calls it.** The CLI (`_build_run_config`),
   `run_graph_async`, `run_graph_streaming_native` and `invoke_graph`. For
   `run_graph_async`, the compiled app carries the graph's value the same
   way it already carries `_yamlgraph_graph_name`
   ([executor_async.py#L253](../yamlgraph/executor_async.py#L253)).
3. **Errors at the boundary.** Every level must be a positive integer.
   The CLI already rejects `0` and negatives at parse time
   ([cli/__init__.py#L125-L134](../yamlgraph/cli/__init__.py#L125-L134)).
   The YAML value already fails at load
   ([validators.py#L209-L221](../yamlgraph/utils/validators.py#L209-L221)).
   New: a caller config value that is not a positive integer raises
   `ValueError` before the graph runs. `YAMLGRAPH_MAX_CONCURRENCY` that is
   empty-but-set, non-integer, `0`, negative or a boolean word raises at
   first resolve, naming the variable and the value. This follows the
   `LLM_REQUEST_TIMEOUT` pattern
   ([llm_bounds.py#L34-L53](../yamlgraph/utils/llm_bounds.py#L34-L53)).
4. **Documentation.** `reference/graph-yaml.md` (the `max_concurrency` row)
   states the order and that the cap applies to every entry point.
   `reference/development-operations.md` (Key Environment Variables) lists
   `YAMLGRAPH_MAX_CONCURRENCY` and the default.

### Human decision needed

**Question for the operator:** may the runtime apply one fixed width to
every provider and every API caller when nothing else sets it? If yes, what
value?

**Suggested default: 8**, the value FR-1068's header already records as an
operator answer (PR #691, accepted risk: a quota below 8 yields 429s until
overridden). The suggestion rests on this evidence:

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

**What changed since the recorded answer:** the async path is not bounded
by the CPU count (Problem 3), and a default of 8 raises width on hosts with
fewer than 4 CPUs (Problem 4). The operator confirms 8, picks another value,
or answers "no global default". If the answer is "no global default", this FR
keeps steps 1–3 without level 4. The resolver then leaves the width unset,
as today, and the docs say so.

## Acceptance Criteria

- [ ] AC-01 (RED): a fixture graph maps over 40 items. Each branch is a
  python node that records how many branches are in flight at once. With no
  width set and the CPU function Python reads patched to 64 (`os.process_cpu_count`
  on 3.13), the recorded peak on current code is above the default, for the
  CLI sync path, CLI `--async`, `run_graph_async` and `invoke_graph`. The
  test records each path's measured peak, including the async one.
- [ ] AC-02 (GREEN): the same fixture peaks at exactly the default on every
  path in AC-01 and on `run_graph_streaming_native`, at patched CPU counts of
  2 and 64.
- [ ] AC-03: precedence. Four cases, each asserting the measured peak: caller
  value beats graph value beats env value beats default. The CLI flag counts
  as the caller value.
- [ ] AC-04: a graph with `config.max_concurrency: 3` peaks at 3 through
  `run_graph_async` and `invoke_graph` with a caller config that has no
  width. On current code this fails (Problem 1).
- [ ] AC-05: `YAMLGRAPH_MAX_CONCURRENCY` set to `""`, `abc`, `0`, `-1`, `2.5`
  or `true` raises `ValueError` naming the variable and the value. A caller
  config value of `0` or `"4"` raises `ValueError` before any node runs.
- [ ] AC-06: the human decision is recorded in this FR's header with the
  chosen value (or "no global default") and the accepted quota risk, before
  GREEN.
- [ ] AC-07: `reference/graph-yaml.md` and
  `reference/development-operations.md` state the order, the default and
  the entry points covered.
- [ ] AC-08: new REQ in a capability file, tests tagged,
  `python scripts/req_coverage.py --strict` passes, changelog fragment, FR
  implementation record, diary entry.

## Alternatives Considered

Solution classes (chosen: 1):

1. **One run-level resolver with a fixed default, applied at every entry
   point.** Chosen. It uses the key LangGraph already honours, so yamlgraph
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
([FR-1079](FR-1079-retry-ownership.md), FR-708). Changing any graph's own
`max_concurrency` value, including the census graph's `4` → `2` noted in
FR-984; that is a graph edit through `scripts/author.sh`.

## Related

- Replaces: [FR-1068](FR-1068-default-max-concurrency.md)
- Extends: [FR-984](FR-984-map-fan-out-max-concurrency.md)
- Evidence: [FR-985](FR-985-census-coverage-floor-and-population-header.md)
- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §2 D6, §7 D
- Composes with: [FR-1079](FR-1079-retry-ownership.md)
