# Feature Request: expose `max_concurrency` for map fan-out and gate the census brief on classification coverage

**Priority:** HIGH
**Type:** Bug
**Status:** Judged — SPLIT (2026-09-04, [judgement](FR-983-map-concurrency-and-census-coverage-gate.judgement.md)); no authority under FR-983. Successors: [FR-984](FR-984-map-fan-out-max-concurrency.md) (concurrency plumbing) — **Enforced** (#586); [FR-985](FR-985-census-coverage-floor-and-population-header.md) (coverage gate) — **Shelved** after three real runs showed the summary-level brief robust to partial coverage. This document is the shared incident record.
**Effort:** 1 day
**First consumer / first event:** the operator re-running the corp
person-profile census (`sheikkinen@<owner>`, 259 private PRs) — the
2026-09-04 09:16 run dropped 100 of 259 rows to Azure 429s and wrote a
brief that reads as a whole-footprint profile. The next run must either
finish with the whole population or refuse to write the brief.
**Requested:** 2026-09-04
**Research:** in-body dispositioned alternatives table below (FR-890 R-6
equivalent record). The sole route could not run: `ddgs` egress is down
on this machine since ~05:22Z today (every engine times out while
`curl`/`httpx` reach the same hosts; FR-982 hit the identical outage
one hour earlier and the operator dispositioned the in-body record
then). The brief is committed at
[research-briefs/fr983-map-concurrency-coverage-gate-brief.md](research-briefs/fr983-map-concurrency-coverage-gate-brief.md)
and passes `scripts/research_preflight.py` (exit 0) for re-running when
egress returns.
**Prior art:** [FR-962-person-profile-census-authored-prs.md](FR-962-person-profile-census-authored-prs.md)
— owns the census; its ideal-result item 5 promised "completeness"
enforced before rendering and item 2 a coverage number; completeness
shipped as index presence, coverage as a printed line. This FR makes
coverage a gate. [FR-943-census-row-failure-containment.md](FR-943-census-row-failure-containment.md)
— per-row `on_error: skip` → `row_failed` marker; the containment is
kept, the aggregate consequence is what this FR adds.
[FR-939-map-overflow-policy.md](FR-939-map-overflow-policy.md) /
FR-027 — `max_items` bounds population size, not fan-out width;
distinct knob, untouched. [FR-069](069-map-node-timeout.md) — map
per-item `timeout`; untouched. [FR-895-census-synthesize-tail.md](FR-895-census-synthesize-tail.md)
— `BRIEF_TOP_N = 30` bounded synthesize input and the fabricated-URL
scan in `render_brief`; the top-N truncation is likewise undisclosed on
the brief but is by design and is *not* absorbed here (named as
successor). `recursion_limit` (`graph_loader.py:84`,
`graph_run_helpers.py:140`, `cli/__init__.py:98`) — the exact plumbing
precedent for a graph-level `RunnableConfig` knob with CLI override.
A REJECTED-FR sweep for `max_concurrency`, `throttle`, `semaphore`,
`rate limit`, `429` returned nothing.

## Summary

The census map node fans out at LangGraph's default thread-pool width
(12 on this machine) with no way to lower it from `graph.yaml` or the
CLI, although LangGraph already honours `RunnableConfig["max_concurrency"]`.
Against an Azure per-minute quota, twelve rows retrying in lockstep
exhausted their retries and 100 of 259 rows were dropped by FR-943
containment. The reducer computed `classification coverage: 56.8%`,
printed it into the ledger, and then let the brief be synthesized and
rendered over the 147 survivors with no disclosure. Two fixes: plumb
`max_concurrency` (graph `config:` block + `--max-concurrency`), and
make the reducer refuse below a coverage floor and stamp the coverage
onto the brief when it passes.

## Value Statement

Operators running any corpus map-reduce against a rate-limited
provider can finish the whole population instead of a random-ish
subset, and a reader of the census brief can never again mistake 57%
of a footprint for 100% of it.

## Problem

From `logs/tt-profile.log` (2026-09-04 09:16:07 → 09:18:51, exit 0):

| observation | value |
|---|---|
| PRs discovered | 259 |
| map rows completed | 159 |
| map rows failed → skipped | **100** |
| rows with a parsed `change_kind` | 147 |
| ledger `classification coverage` | **56.8%** |
| HTTP 429 responses | 1249 |
| `openai._base_client: Retrying request` | 1149 |
| brief lines mentioning coverage / skip / 429 | 0 |

Raw 429 body: `Your requests to gpt-5.4-mini for <deployment> in
swedencentral have exceeded rate limit.`

**Fan-out width.** `judge_items` (`graph.yaml:105-125`) is `type: map`
over 259 items; `max_items: 500` bounds *how many*, nothing bounds *how
many at once*. `grep -rn max_concurrency yamlgraph/` → no hits. Yet
`langgraph/pregel/_executor.py:135` (v1.2.9) wraps `Send` tasks in a
semaphore when `config["max_concurrency"]` is set, sync and async.
Probe, 40 `Send` tasks × 50 ms sleep:

| `config` | peak parallel workers | results |
|---|---|---|
| `{}` | 12 | 40/40 |
| `{"max_concurrency": 4}` | 4 | 40/40 |

Per row, yamlgraph retries 3× (1 s, 2 s, 4 s; `config.py:84-86`,
`executor.py:161-176`), and inside each attempt the OpenAI client
retries twice honouring `Retry-After`. Twelve lockstepped rows burn
nine HTTP attempts in ~7 s; the quota never recovers between waves.

**Coverage.** `_mechanical_rollup` computes
`classification_coverage = judged / total` (`tools.py:344`);
`reduce_pr_ledger` prints it (`tools.py:481`). The reducer's
completeness check (`tools.py:454-457`) asserts every index has *a*
finding — `row_failed` satisfies it. `prepare_brief_input` keeps only
`judged` rows (`tools.py:551-553`); `synthesize` gets `rubric` + `rows`
(`graph.yaml:137-144`); `render_brief` writes the LLM text after a URL
scan. The brief says "Themes", "Surface concentration", "Cadence" over
the survivors; its `docs 76 / feat 35 / fix 23` skew is over 147 rows
chosen by whichever requests the rate limiter admitted. The ledger is
honest; the brief — the artifact a human reads — is not.

## Ideal Result

A graph author states the fan-out width the provider can bear, in the
same `config:` block that already holds `recursion_limit`, and the CLI
can override it per run. A corpus census either classifies the whole
population it discovered or stops before writing a brief; when it
proceeds below 100%, the first line of the brief says so in numbers
the reader cannot miss, written by code.

## Proposed Solution

**D-1 — plumb `max_concurrency` (core, FR-027 execution-safety block).**

```yaml
# graph.yaml
config:
  recursion_limit: 50
  max_concurrency: 4      # new; None → LangGraph default (unchanged)
```

- `yamlgraph/compile/graph_loader.py:84` — `self.max_concurrency =
  graph_level_config.get("max_concurrency")`; validate positive int or
  `None`.
- `yamlgraph/cli/__init__.py:98` — `--max-concurrency` (int, default
  `None`), mirroring `--recursion-limit`.
- `yamlgraph/cli/graph_run_helpers.py:140` — CLI value, else
  `graph_config.max_concurrency`; if not `None`, set
  `config["max_concurrency"]`. Nothing else: LangGraph does the
  throttling.
- `reference/graph-yaml.md` — one entry beside `recursion_limit`.
- `examples/demos/person_profile_census/graph.yaml` — `config:
  max_concurrency: 4` (the census is the first consumer; value is the
  operator's to tune, 4 is the probe value).

**D-2 — coverage gate and stamp (census reducer, LLM-free).**

```python
# tools.py, reduce_pr_ledger, after _canary_gate
coverage = rollup["classification_coverage"]
floor = float(state.get("min_coverage", 1.0))
if coverage < floor:
    raise ValueError(
        f"classification coverage {coverage:.1%} below floor {floor:.0%}: "
        f"{failed} of {total} rows row_failed; raise --var min_coverage "
        f"to accept a partial population, or lower max_concurrency"
    )
```

- `min_coverage` is a graph variable, default `1.0` (Commandment 6:
  the default is "all or raise"; accepting less is an explicit operator
  choice recorded in the invocation).
- `render_brief` prefixes the written brief with a code-generated
  header: `> Population: {judged}/{total} PRs classified
  ({coverage:.1%}); {failed} row_failed. Brief synthesized from top
  {BRIEF_TOP_N} judged rows by delta.` — the FR-895 top-N fact rides
  along because the line is already being written, but no other
  FR-895 behaviour changes.
- The `synthesize` prompt is untouched; the model is never asked to
  report coverage.

## Acceptance Criteria

- [ ] AC-01: `config: {max_concurrency: N}` in `graph.yaml` reaches
  `app.invoke(..., config=...)` as `config["max_concurrency"] == N`;
  absent → key absent from the invoke config (unchanged behaviour).
  Witness: unit test on `GraphConfig` + the config builder in
  `graph_run_helpers`, no LLM.
- [ ] AC-02: `--max-concurrency N` overrides the YAML value; the
  precedence test mirrors the existing `recursion_limit` one.
- [ ] AC-03: `max_concurrency: 0`, negative, or non-int in `graph.yaml`
  is rejected at load with a message naming the field.
- [ ] AC-04: behavioural witness: a compiled yamlgraph `map` over ≥ 40
  python-tool items, each recording peak parallelism with a shared
  counter, shows peak ≤ N when invoked with `max_concurrency: N` and
  peak > N without it (the 40-task probe, expressed through a yamlgraph
  graph rather than raw LangGraph). No LLM.
- [ ] AC-05: `reduce_pr_ledger` raises `ValueError` naming coverage,
  floor, failed and total counts when
  `classification_coverage < min_coverage`; default `min_coverage` is
  `1.0`. Witness: fixture ledger with 3 of 10 rows `row_failed` →
  raises; `min_coverage: 0.7` → passes.
- [ ] AC-06: RED first: the AC-05 fixture with 100 of 259 rows
  `row_failed` passes through today's reducer and produces a
  `brief_input`; after D-2 it raises before `prepare_brief_input` runs.
- [ ] AC-07: `render_brief` output begins with the population header
  line carrying `judged`, `total`, coverage percentage, `row_failed`
  count and `BRIEF_TOP_N`; witness asserts the exact first line for a
  fixture with known counts.
- [ ] AC-08: FR-943 containment unchanged: a single `row_failed` row
  still yields a `row_failed` ledger row, and the map does not abort
  (existing FR-943 witnesses stay green).
- [ ] AC-09: `examples/demos/person_profile_census/graph.yaml` gains
  `config: max_concurrency: 4`; README documents `--var min_coverage=`
  and `--max-concurrency` in the corp invocation; `demo-output.log`
  regenerated via the committed smoke path (public corpus, tracing off
  per FR-982 if landed, `AZURE_MODEL` overridden to a non-corp value).
- [ ] AC-10: live witness recorded in Implementation Status: the corp
  census re-run with `max_concurrency: 4` completes with coverage
  ≥ 0.95 or raises the AC-05 error; either outcome is recorded with
  429 count and coverage from the log. Zero corp identifiers in the
  recorded excerpt.
- [ ] AC-11: registry — `CAP-262-map-fan-out-concurrency.yaml`
  (`REQ-YG-645`, modules `graph_loader.py`, `graph_run_helpers.py`,
  `cli/__init__.py`) and `CAP-263-census-coverage-gate.yaml`
  (`REQ-YG-646`, module `examples/demos/person_profile_census/tools.py`);
  `ARCHITECTURE.md` regenerated; `req_coverage.py --strict` exits 0;
  IDs re-verified against `origin/main` at push time.
- [ ] AC-12: `fix` changelog fragment naming FR-983 and both REQs;
  diary reflection at `docs/diary/diary-<date>-reflection-fr-983-<slug>.md`.

## Alternatives Considered

Research-record column set. Every row carries a detail an executed
probe produced.

| candidate | persona | class | verdict | precedent | is_this_a_graph | effort-risk | rationale |
|---|---|---|---|---|---|---|---|
| Plumb LangGraph `max_concurrency` from `config:` + CLI (D-1) | yamlgraph_native_planner | enforcement/latency-critical | ACCEPT | `recursion_limit` plumbing (FR-027) | no | low / low | Probe: `_executor.py:135` semaphore exists in v1.2.9 for sync and async; 40 `Send` tasks peaked at 12 unthrottled and exactly 4 with `{"max_concurrency": 4}`, 40/40 results both ways. Three files, no new mechanism. |
| Raise `LLM_MAX_RETRIES` / `LLM_RETRY_DELAY` env for the run | os_infra_primitivist | enforcement/latency-critical | REJECT as fix, keep as operator workaround | `config.py:84-86` | no | zero / medium | Probe: knobs exist and would lengthen the ladder to 2→4→8→16→30→30 s. But every row still fires at once; a longer ladder converts a dropped row into a slow row without addressing why the quota is hit. Documented in the README as the no-code fallback, not the fix. |
| yamlgraph-side semaphore or `time.sleep` in the map compiler | data_process_planner | enforcement/latency-critical | REJECT | — | no | medium / medium | Probe shows the platform already implements exactly this (`does_the_platform_already_do_this`); a second implementation is Commandment 8 entropy and would fight LangGraph's own pool sizing. |
| Per-map-node `concurrency:` field instead of graph-level | yamlgraph_native_planner | enforcement/latency-critical | DEFER | FR-069 per-node `timeout` | no | medium / low | LangGraph's knob is per-invoke, not per-node; a per-node field would need yamlgraph to run each map under a sub-config or its own pool — real work for a benefit no consumer has asked for. Graph-level matches the primitive; revisit when a graph has two maps with different quotas. |
| Coverage floor in the reducer, default 1.0 (D-2) | subtractionist | enforcement/latency-critical | ACCEPT | FR-943 containment; Commandment 6 | no | low / low | Probe: `tools.py:344` already computes the number and `:481` prints it; the gate is four lines after `_canary_gate`. Default 1.0 makes partial population an explicit `--var`, recorded in the invocation. |
| Ask the synthesize prompt to state coverage | librarian_research | judgement/analysis/generation | REJECT | FR-895 prompt contract | no | low / high | The model never sees the population (`graph.yaml:137-144` passes rows only); it would be asked to *invent* a number, the exact failure mode the brief already exhibits. Coverage is arithmetic; code writes it. |
| Retry the failed rows in a second map pass | data_process_planner | enforcement/latency-critical | REJECT for this FR | — | yes (a second fan-out) | high / medium | Would be a new node and a new state key, and without D-1 the second pass hits the same wall. D-1 removes the cause; a re-pass is an optimisation to file only if D-1 still leaves gaps at a sane width. |
| Lower `max_items` so the population fits the quota | subtractionist | enforcement/latency-critical | REJECT | FR-939 | no | zero / high | Substitutes the survivors for the whole by construction — the defect this FR exists to make impossible. |

`is_this_a_graph`: the throttle is config plumbing and the gate is
arithmetic; only the rejected re-pass would have been a graph.

## Judgement Fold — 2026-09-04

**Verdict: SPLIT.** Sole route, backend `copilot` (`gpt-5.6-sol`).
The runtime knob ships without the census gate and the census can
refuse partial output under today's concurrency, so single-responsibility
(`judge-fr/doctrine.md:49-50`) forces two FRs.

| # | Finding | Disposition |
|---|---|---|
| R-1 split | D-1 and D-2 are independently deployable | Accepted — FR-984 (D-1), FR-985 (D-2); this FR stays as the incident record and evidence anchor |
| R-2 classify | one consumer ≠ framework primitive | Accepted — both successors are Contrib/example |
| R-3 brief "absent" | claimed uncommitted research brief | **Falsified** — committed at `9a490c8c` on this branch; judge read the main checkout |
| R-4 value contract | parse `min_coverage` once, `[0,1]`, header from reducer-owned counts | Accepted into FR-985 |
| R-5 AC-06 wrong stage | `reduce_pr_ledger` does not produce `brief_input` | Accepted — a real error; FR-985 AC-B04 is the compiled-path witness |
| R-6 CLI validation | `--max-concurrency 0`/negative must fail before invoke | Accepted into FR-984 |
| R-7 paid rerun | human decision, not implicit gate | Operator **authorized** one rerun after both successors are enforced |

Nothing in this FR's Proposed Solution or Acceptance Criteria carries
authority; the successors' AC lists supersede them.

## Related

- Brief: [research-briefs/fr983-map-concurrency-coverage-gate-brief.md](research-briefs/fr983-map-concurrency-coverage-gate-brief.md)
- Evidence run: `logs/tt-profile.log`, `tmp/tt-profile.md` (line 8:
  `classification coverage: 56.8%`), `tmp/tt-profile.brief.md`
  (operator-local; corp content, not committed)
- Fan-out: `examples/demos/person_profile_census/graph.yaml:105-125`;
  `yamlgraph/compile/map_compiler.py:350` (FR-027 cap)
- Platform primitive: `langgraph/pregel/_executor.py:135` (v1.2.9)
- Plumbing precedent: `yamlgraph/compile/graph_loader.py:84`,
  `yamlgraph/cli/graph_run_helpers.py:140-143`, `yamlgraph/cli/__init__.py:98-104`
- Reducer: `examples/demos/person_profile_census/tools.py:302-347`
  (rollup), `:360-382` (canary), `:384-` (reducer), `:544-573`
  (brief input), `:612-` (render)
- Sibling filed today: FR-982 (unit suite runs with tracer live) —
  shares the research-route outage, otherwise independent.
