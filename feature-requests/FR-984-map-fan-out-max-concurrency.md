# Feature Request: expose LangGraph `max_concurrency` for map fan-out from `graph.yaml` and the CLI

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-09-04
**Classification:** Contrib/example (FR-983 judgement R-2 — one named
consumer; a configuration gap in an existing abstraction, not a new
primitive)
**First consumer / first event:** the person-profile census
(`examples/demos/person_profile_census/graph.yaml`, `judge_items` map)
on its next corp run — the 2026-09-04 run fanned out at the LangGraph
default pool width against an Azure per-minute quota and lost 100 of
259 rows to 429s.
**Research:** [research-briefs/fr983-map-concurrency-coverage-gate-brief.md](research-briefs/fr983-map-concurrency-coverage-gate-brief.md)
(committed `9a490c8c`, preflight exit 0) and the apportioned in-body
alternatives table below — the FR-890 R-6 record inherited from
[FR-983](FR-983-map-concurrency-and-census-coverage-gate.md), whose
judgement split this deliverable out. The sole research route was down
(ddgs egress) when the parent was filed; the brief is committed for
re-running.
**Prior art:** [FR-983-map-concurrency-and-census-coverage-gate.md](FR-983-map-concurrency-and-census-coverage-gate.md)
[Judged — SPLIT] — the parent incident record; this FR is its
Successor A and inherits its frozen scope verbatim. FR-027
(`yamlgraph/compile/graph_loader.py:83-88`, `config:` execution-safety
block) — owns `recursion_limit`, `max_map_items`, `timeout`; this FR
adds one sibling key and nothing else. `recursion_limit` plumbing
(`graph_run_helpers.py:140-143`, `cli/__init__.py:98-104`) — the exact
precedent for YAML value + CLI override → `RunnableConfig`.
[FR-939-map-overflow-policy.md](FR-939-map-overflow-policy.md) —
`max_items` bounds population size, not fan-out width; untouched.
[FR-069](069-map-node-timeout.md) — map per-item `timeout` and its
one-shot `ThreadPoolExecutor(max_workers=1)` wrapper in
`map_compiler.py:100-108`; unrelated to fan-out width, untouched.
[FR-985-census-coverage-floor-and-population-header.md](FR-985-census-coverage-floor-and-population-header.md)
— Successor B; independent, no shared implementation, may land in
either order. No REJECTED FR touches map concurrency.

## Summary

LangGraph v1.2.9 throttles parallel `Send` tasks with a semaphore when
`RunnableConfig["max_concurrency"]` is set (`langgraph/pregel/_executor.py:135`,
sync and async). yamlgraph never passes it: `grep -rn max_concurrency
yamlgraph/` is empty, `graph.yaml` has no field, the CLI has no flag.
Add the key to the FR-027 `config:` block, a `--max-concurrency`
override, and plumb it into the invoke config exactly as
`recursion_limit` is plumbed. Absent → unchanged behaviour.

## Value Statement

Any graph author whose map node hits a provider quota can state the
width the provider bears in one line, instead of watching FR-943
containment quietly drop the rows the rate limiter rejected.

## Problem

From the parent's evidence run (`logs/tt-profile.log`, 2026-09-04
09:16–09:18): 259 rows, 1249 HTTP 429s, 100 rows dropped after three
yamlgraph retries each. Probe of the platform primitive, 40 `Send`
tasks × 50 ms:

| `config` | peak parallel workers | results |
|---|---|---|
| `{}` | 12 | 40/40 |
| `{"max_concurrency": 4}` | 4 | 40/40 |

The width is a `RunnableConfig` key the runtime already honours; the
defect is that no yamlgraph surface can set it.

## Ideal Result

A graph author writes `config: {max_concurrency: 4}` beside
`recursion_limit`, an operator overrides it with `--max-concurrency 2`
for a tighter quota, and LangGraph does the rest. Graphs that say
nothing behave exactly as today.

## Proposed Solution

- `yamlgraph/compile/graph_loader.py:84` — `self.max_concurrency =
  graph_level_config.get("max_concurrency")`; validate `None` or a
  positive `int` (booleans, floats, strings, `0`, negatives rejected at
  load with `max_concurrency` in the message).
- `yamlgraph/cli/__init__.py:98` — `--max-concurrency`, `type=` a
  positive-int parser that rejects `0` and negatives before invocation,
  naming `--max-concurrency` in the diagnostic; default `None`.
- `yamlgraph/cli/graph_run_helpers.py:140` — CLI value if given, else
  `graph_config.max_concurrency`; if not `None`,
  `config["max_concurrency"] = value`. No key when absent.
- `reference/graph-yaml.md` — one entry beside `recursion_limit`:
  scope (whole invoke, all parallel branches), positive-int contract,
  YAML/CLI precedence, absence semantics.
- `examples/demos/person_profile_census/graph.yaml` — `config:
  max_concurrency: 4`; README shows the `--max-concurrency` override.
  This is a material `graph.yaml` edit and goes through the
  graph-authoring route (`scripts/author.sh`, report artifact).

No yamlgraph-owned semaphore, sleep, pool, or retry change (C-6).

## Acceptance Criteria

Verbatim from the parent judgement (Successor A), R-7 folded into
AC-A11.

- [ ] AC-A01: RED first: a `GraphConfig` test proves absent
  `config.max_concurrency` yields `None`, a positive integer is
  retained, and YAML `0`, negative, boolean, string, and fractional
  values fail at load with `max_concurrency` in the message.
- [ ] AC-A02: the run-config builder omits `max_concurrency` when
  neither CLI nor YAML supplies it, uses the YAML value when CLI is
  absent, and uses the CLI value when both are present.
- [ ] AC-A03: `--max-concurrency` accepts a positive integer; `0` and
  negative values fail parser validation before invocation and name
  the option.
- [ ] AC-A04: a compiled yamlgraph map over at least 40 Python-tool
  items records peak parallelism through a thread-safe counter;
  configured `N` produces peak `<= N`, the unconfigured control
  produces peak `> N`, and both produce all expected results without
  an LLM.
- [ ] AC-A05: sync and async invocation paths are covered if they have
  separate run-config builders; otherwise a test proves they share the
  one tested builder.
- [ ] AC-A06: `reference/graph-yaml.md` documents scope,
  positive-integer validation, YAML/CLI precedence, and absence
  semantics.
- [ ] AC-A07: the person-profile census graph sets
  `config.max_concurrency: 4`, and its documented invocation includes
  `--max-concurrency` override syntax.
- [ ] AC-A08: the graph change has the required graph-authoring
  report, lint, and smoke evidence.
- [ ] AC-A09: one capability and REQ (`CAP-262-map-fan-out-concurrency`,
  `REQ-YG-645`, re-verified against `origin/main` at push) cover the
  production branches; every test carries that REQ marker;
  regenerated `ARCHITECTURE.md` and `python scripts/req_coverage.py
  --strict` pass.
- [ ] AC-A10: FR status/implementation record, one `fix` changelog
  fragment, and diary reflection
  (`docs/diary/diary-<date>-reflection-fr-984-<slug>.md`) are committed.
- [ ] AC-A11: operational witness — **authorized by the operator on
  2026-09-04** to run once after both FR-984 and FR-985 are enforced:
  the corp census with `max_concurrency: 4`, recording sanitized
  configured concurrency, 429 count, discovered/classified/failed
  counts, coverage, and terminal result. Deterministic tests are the
  enforcement gate; this AC records the result, whichever it is, and
  no corp identifier enters the record.

## Alternatives Considered

Apportioned from the parent's research record (rows bearing on
fan-out width). Every row carries a probe-produced detail.

| candidate | persona | class | verdict | precedent | is_this_a_graph | effort-risk | rationale |
|---|---|---|---|---|---|---|---|
| Plumb LangGraph `max_concurrency` from `config:` + CLI | yamlgraph_native_planner | enforcement/latency-critical | ACCEPT | `recursion_limit` (FR-027) | no | low / low | `_executor.py:135` semaphore exists in v1.2.9 for sync and async; 40 `Send` tasks peaked at 12 unthrottled, exactly 4 with `{"max_concurrency": 4}`, 40/40 results both ways. Three files, no new mechanism. |
| Raise `LLM_MAX_RETRIES` / `LLM_RETRY_DELAY` for the run | os_infra_primitivist | enforcement/latency-critical | REJECT as fix; documented operator workaround | `config.py:84-86` | no | zero / medium | Knobs exist (ladder becomes 2→4→8→16→30→30 s) but every row still fires at once; converts a dropped row into a slow row. README names it as the no-code fallback, not the fix. |
| yamlgraph-side semaphore or `time.sleep` in `map_compiler` | data_process_planner | enforcement/latency-critical | REJECT | — | no | medium / medium | Platform already implements exactly this; a second implementation is Commandment 8 entropy and fights LangGraph's pool sizing. Judgement C-6 forbids it. |
| Per-map-node `concurrency:` field | yamlgraph_native_planner | enforcement/latency-critical | DEFER | FR-069 per-node `timeout` | no | medium / low | LangGraph's knob is per-invoke; a per-node field needs a sub-config or private pool per map. No consumer has two maps with different quotas. Named successor, not absorbed. |
| Retry failed rows in a second map pass | data_process_planner | enforcement/latency-critical | REJECT | — | yes | high / medium | New node, new state key; without a width limit the second pass hits the same wall. File only if this FR still leaves gaps at a sane width. |

## Related

- Parent: [FR-983](FR-983-map-concurrency-and-census-coverage-gate.md) and its [judgement](FR-983-map-concurrency-and-census-coverage-gate.judgement.md) (R-1, R-2, R-6, R-7, C-6, Successor A AC list)
- Sibling: [FR-985](FR-985-census-coverage-floor-and-population-header.md)
- Platform: `langgraph/pregel/_executor.py:135` (v1.2.9)
- Plumbing: `yamlgraph/compile/graph_loader.py:84`, `yamlgraph/cli/graph_run_helpers.py:140-143`, `yamlgraph/cli/__init__.py:98-104`
- First consumer: `examples/demos/person_profile_census/graph.yaml:105-125`
