# Feature Request: expose LangGraph `max_concurrency` for map fan-out from `graph.yaml` and the CLI

**Priority:** HIGH
**Type:** Bug
**Status:** Judged — APPROVED WITH REVISIONS (2026-09-04, [judgement](FR-984-map-fan-out-max-concurrency.judgement.md)); R-1..R-5 folded below, human-reviewed; authority active for the frozen scope.
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
either order. [FR-030](030-map-concurrency-control.md) [**Won't Fix**,
2026-02-14] — the rejected precedent (judgement R-1): proposed a
per-map `max_concurrency` field and was closed as "wrong layer" on the
stated belief that `Send()` has no native concurrency control, so the
only implementations were a yamlgraph semaphore, batched `Send()`, or a
sequential loop (`030-map-concurrency-control.md:31-55`). The evidence
has changed: LangGraph v1.2.9 honours `RunnableConfig["max_concurrency"]`
with its own semaphore (`_executor.py:135`; 40-task probe, peak 12 → 4).
This FR exposes that whole-invoke key and adds **no** scheduling
implementation — the very thing FR-030 was rejected for proposing.
FR-030's redirect to retry policy (FR-031) is kept as the documented
operator workaround, not the fix: a longer retry ladder makes a dropped
row a slow row without changing how many rows fire at once. The
parent's claim that no rejected FR touches map concurrency was false;
the sweep grepped `FR-*.md` and missed the `0NN-*.md` naming of early
FRs. Authoring brief for the census edit (judgement R-3):
[authoring-briefs/fr-984-census-max-concurrency-brief.md](authoring-briefs/fr-984-census-max-concurrency-brief.md).

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
- `yamlgraph/schemas/graph-v1.json` (judgement R-2) — add
  `max_concurrency` to the `config` properties as `integer`,
  `minimum: 1`, beside `recursion_limit`/`max_map_items`/`max_tokens`/
  `timeout` (`graph-v1.json:289-312`). Schema publication does not
  replace load-boundary validation; both must agree.
- `examples/demos/person_profile_census/graph.yaml` — `config:
  max_concurrency: 4`; README shows the `--max-concurrency 2` override.
  This is a material `graph.yaml` edit and goes through the
  graph-authoring route (`scripts/author.sh`) driven by the committed
  brief
  [authoring-briefs/fr-984-census-max-concurrency-brief.md](authoring-briefs/fr-984-census-max-concurrency-brief.md)
  (judgement R-3), producing `tmp/draft-authoring-report.md`, lint, and
  a smoke attempt whose exact outcome is recorded.

No yamlgraph-owned semaphore, sleep, pool, or retry change (C-6).

## Acceptance Criteria

Revised list from the FR-984 judgement (supersedes the parent's
Successor A list). The former AC-A11 is no longer a criterion — see
"Non-gating observation" below (judgement R-4).

- [ ] AC-01: RED first: loading a graph with absent
  `config.max_concurrency` yields `GraphConfig.max_concurrency is None`,
  and a positive integer is retained; YAML boolean, string, fractional,
  zero, and negative values fail during load with `max_concurrency` in
  the diagnostic.
- [ ] AC-02: the run-config builder omits `max_concurrency` when neither
  CLI nor YAML supplies it, uses the YAML value when CLI is absent, and
  uses the CLI value when both are present.
- [ ] AC-03: `--max-concurrency` accepts a positive integer; zero and
  negative values fail argument parsing before graph invocation and the
  diagnostic names `--max-concurrency`.
- [ ] AC-04: `yamlgraph/schemas/graph-v1.json` publishes
  `config.max_concurrency` as an integer with minimum `1`, and a focused
  test asserts that contract.
- [ ] AC-05: one compiled YAMLGraph map over at least 40 Python-tool
  items is parameterized over sync `invoke` and async `ainvoke`; with
  `N = 2`, a thread-safe counter records peak `<= 2`, the unconfigured
  control records peak `> 2`, and both paths return every expected
  result without an LLM.
- [ ] AC-06: `reference/graph-yaml.md` documents that the key applies to
  the whole invocation and all parallel branches, accepts only positive
  integers, is overridden by the CLI value, and is omitted entirely when
  absent.
- [ ] AC-07: the person-profile census graph sets
  `config.max_concurrency: 4`, and its documented invocation shows
  `--max-concurrency 2` as override syntax without changing census
  policy.
- [ ] AC-08: FR-984 cites a committed graph-authoring task brief
  ([authoring-briefs/fr-984-census-max-concurrency-brief.md](authoring-briefs/fr-984-census-max-concurrency-brief.md));
  the graph edit is produced through the governed route; the report
  names the graph and README artifacts; graph lint passes; the narrow
  smoke is attempted and its exact outcome or blocker is recorded.
- [ ] AC-09: `CAP-262-map-fan-out-concurrency.yaml` and `REQ-YG-645`,
  re-verified against `origin/main` at push, cover every changed
  production branch; every new test carries the REQ marker; regenerated
  `ARCHITECTURE.md` and `python scripts/req_coverage.py --strict` pass.
- [ ] AC-10: FR status and implementation decisions, one `fix` changelog
  fragment, and `docs/diary/diary-<date>-reflection-fr-984-<slug>.md`
  with a `Seed:` are committed.

### Non-gating observation (judgement R-4, C-8)

The operator authorized (2026-09-04) one combined private-corpus run
after **both** FR-984 and FR-985 are enforced, recording sanitized
configured concurrency, 429 count, discovered/classified/failed counts,
coverage, and terminal result. It does not gate FR-984 completion, must
not run before both successors land, commits no corp identifier, and
makes no claim that FR-984 eliminates provider 429s. Appended to this
record when available.

## Judgement Fold — 2026-09-04

**Verdict: APPROVED WITH REVISIONS** (sole route, `copilot`,
`gpt-5.6-sol`). Authority active after this fold.

| # | Finding | Disposition |
|---|---|---|
| R-1 | Rejected FR-030 (Won't Fix, 2026-02-14) undispositioned; "no rejected FR" claim false | Folded into Prior art with the distinguishing fact: FR-030 believed `Send()` had no native limit and was rejected for proposing a yamlgraph scheduler; LangGraph now has the semaphore and this FR adds none. Sweep defect named: `FR-*.md` glob misses `0NN-*.md` |
| R-2 | `yamlgraph/schemas/graph-v1.json` `config` block lacks the key | Added to Proposed Solution and AC-04; runtime validation still authoritative |
| R-3 | Graph-authoring brief must be committed and cited | Brief committed at `authoring-briefs/fr-984-census-max-concurrency-brief.md`; AC-08 revised |
| R-4 | AC-A11 coupled acceptance to FR-985 | Removed from criteria; kept as non-gating observation with the operator's authorization intact |
| R-5 | AC-A04 left `N` free; AC-A05 proved builder sharing, not behaviour | AC-05 fixes `N = 2` and parameterizes over `invoke`/`ainvoke` |

All five verified against the cited files before folding; none
falsified.

## Alternatives Considered

Apportioned from the parent's research record (rows bearing on
fan-out width). Every row carries a probe-produced detail.

| candidate | persona | class | verdict | precedent | is_this_a_graph | effort-risk | rationale |
|---|---|---|---|---|---|---|---|
| Plumb LangGraph `max_concurrency` from `config:` + CLI | yamlgraph_native_planner | enforcement/latency-critical | ACCEPT | `recursion_limit` (FR-027) | no | low / low | `_executor.py:135` semaphore exists in v1.2.9 for sync and async; 40 `Send` tasks peaked at 12 unthrottled, exactly 4 with `{"max_concurrency": 4}`, 40/40 results both ways. Three files, no new mechanism. |
| Raise `LLM_MAX_RETRIES` / `LLM_RETRY_DELAY` for the run | os_infra_primitivist | enforcement/latency-critical | REJECT as fix; documented operator workaround | `config.py:84-86` | no | zero / medium | Knobs exist (ladder becomes 2→4→8→16→30→30 s) but every row still fires at once; converts a dropped row into a slow row. README names it as the no-code fallback, not the fix. |
| yamlgraph-side semaphore or `time.sleep` in `map_compiler` | data_process_planner | enforcement/latency-critical | REJECT | FR-030 (Won't Fix) proposed exactly this | no | medium / medium | Platform already implements exactly this; a second implementation is Commandment 8 entropy and fights LangGraph's pool sizing. FR-030 was rejected for proposing it when the platform had no primitive; now that it does, the yamlgraph-side variant is doubly wrong. Judgement C-6 forbids it. |
| Per-map-node `concurrency:` field | yamlgraph_native_planner | enforcement/latency-critical | DEFER | FR-069 per-node `timeout` | no | medium / low | LangGraph's knob is per-invoke; a per-node field needs a sub-config or private pool per map. No consumer has two maps with different quotas. Named successor, not absorbed. |
| Retry failed rows in a second map pass | data_process_planner | enforcement/latency-critical | REJECT | — | yes | high / medium | New node, new state key; without a width limit the second pass hits the same wall. File only if this FR still leaves gaps at a sane width. |

## Related

- Parent: [FR-983](FR-983-map-concurrency-and-census-coverage-gate.md) and its [judgement](FR-983-map-concurrency-and-census-coverage-gate.judgement.md) (R-1, R-2, R-6, R-7, C-6, Successor A AC list)
- Sibling: [FR-985](FR-985-census-coverage-floor-and-population-header.md)
- Platform: `langgraph/pregel/_executor.py:135` (v1.2.9)
- Plumbing: `yamlgraph/compile/graph_loader.py:84`, `yamlgraph/cli/graph_run_helpers.py:140-143`, `yamlgraph/cli/__init__.py:98-104`
- First consumer: `examples/demos/person_profile_census/graph.yaml:105-125`
