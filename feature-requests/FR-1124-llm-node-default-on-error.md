# Feature Request: An LLM node without `on_error` gets a named, documented default

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 2 days (framework 1 day; migration census and graph edits 1 day)
**Requested:** 2026-09-27
**First consumer / first event:** any embedding application that calls
`compiled.invoke` on a graph whose `llm` node fails, at the moment the
next node reads the failed node's `state_key`. The witnessed instance
is `sheikkinen/yamlgraph-daily-digest` on 2026-09-19: the ranker failed,
the graph continued, the formatting node read an absent value as a quiet
day, nine unattended runs reported success. Second consumer: the 224
`llm` nodes in 134 repository graphs that declare no `on_error` and today
run a strategy the reference does not name.
**Research:** [FR-1124.research.md](FR-1124.research.md)
**Prior art:** [FR-1083](FR-1083-exit-code-reflects-errors.md) enumerated
this path as row P1 and counted its readers (none); it changed the CLI's
exit status, not the path. [FR-1066](FR-1066-exit-code-reflects-errors.judgement.md)
(REJECTED) was FR-1083's first filing; its rejection was about research
and reachable exit paths and did not rule on the default handler, so this
FR re-enters no rejected territory. [FR-1097](FR-1097-graph-run-completed-errors-exit-3.md)
and [FR-1098](FR-1098-stream-error-event-exit-status.md) make the CLI
exit 3 on recorded errors; this FR is the same truthfulness one layer
down, at the node and at the Python caller, and keeps their tally
working. [FR-778](FR-778-tool-call-on-error-fail.md) gave `tool_call`
nodes an `on_error: fail` because deterministic pipelines need a failed
prerequisite to stop the run; this FR applies that argument to `llm`
nodes and, unlike FR-778, changes the default rather than adding a
value. [FR-1121](FR-1121-daily-digest-ranker-schema-loud-failure.md)
is the application-side fix for the incident and names this question as
unowned; [FR-1123](FR-1123-untyped-subschema-constrained-decoding-gate.md)
is the schema half of the same incident's core cause.
[FR-1073](FR-1073-map-result-contract.md) H-2 moved unread map-level
`on_error` keys; map sub-node defaults are its territory and are not
changed here.

## Summary

The reference documents four `on_error` values and no default for `llm`
nodes. In code, an `llm` node with no `on_error` falls through every
enum branch to `handle_default`, which records a `PipelineError`, leaves
the node's `state_key` unset, and lets the graph continue. That is a
fifth strategy: not `skip` (no `_skipped`, not tolerated), not `fail`
(no raise), unnamed, undocumented, unwitnessed by any test, and the
behaviour of 224 of the repository's 236 `llm` nodes. This FR makes the
default `fail`, the value `python`, `tool` and `copilot` nodes already
document, gives graphs an explicit `defaults.on_error` to opt out, and
migrates the repository's graphs by census.

## Value Statement

A graph author who writes an `llm` node and nothing else gets the
behaviour the reference describes for every other node type: a failure
raises, the run stops, and no downstream node ever mistakes a failed
prerequisite for an empty one.

## Problem

| Node type | Documented default | Code default |
|---|---|---|
| `python` | `fail` | `fail` |
| `tool` (shell) | `fail` | `fail` |
| `copilot` | `fail` | `fail` |
| `tool_call` | `skip` with failure envelope (FR-778) | `skip` |
| `llm` | none stated | record-and-continue (`handle_default`) |

The record-and-continue path sets `errors: [PipelineError]` and nothing
else. The next node sees an absent `state_key`. The only reader of
`errors` in the framework is the CLI's exit tally (FR-1097); a Python
caller of `compiled.invoke` or `invoke_graph` gets a normal return.
FR-1083's census found no repository graph or tool reading `errors`.

Census on 2026-09-27 over `examples/`, `graphs/` and `.github/`:

| Measure | Count |
|---|---|
| Graph files with nodes | 208 |
| `llm` nodes | 236 |
| with `on_error` | 12 |
| without `on_error` | 224 |
| graphs with at least one uncovered `llm` node | 134 |

No test names `handle_default`.

## Ideal Result

`on_error` on an `llm` node has a default that is one of the four
documented values, printed in the common node property table, and
proven by a test that fails an `llm` node without `on_error` and asserts
the documented outcome. The default is `fail`, so `llm`, `python`,
`tool` and `copilot` agree, and a graph that wants continuation says so
once in `defaults.on_error` or per node. No graph in the repository
changes behaviour by accident: every graph that relied on continuation
is found by census and given the declaration it was implicitly using.

## Proposed Solution

### S-1: Default `fail`, resolved at load

`yamlgraph/models/node_schema.py`: `on_error` for `llm` nodes resolves
node value → `defaults.on_error` → `"fail"`. `create_llm_node` receives
a value that is always one of the four enum members;
`handle_error`'s fall-through to `handle_default` becomes unreachable
for `llm` nodes and is deleted from that dispatch (Purge). `handle_default`
stays for the callers FR-1083 rows P2, P3 and P5 still route through it
(retry exhausted, fallback failed, `requires:` missing); those rows are
not changed here.

### S-2: `defaults.on_error`

The graph-level `defaults:` block accepts `on_error` with the same four
values, validated at load like `defaults.on_overflow` (FR-939). It
applies to `llm` nodes only; `python`, `tool`, `tool_call` and map
sub-node defaults are untouched. A node value overrides it.

```yaml
defaults:
  on_error: skip        # this graph tolerates LLM failures everywhere
nodes:
  rank:
    type: llm
    prompt: rank
    on_error: fail      # except here
```

### S-3: Reference

The common node property table gains an `on_error` row: type `string`,
default `"fail"`, the four values, and the sentence "a node that fails
under `fail` raises; there is no record-and-continue mode". The
`on_error` value table gains a `Default` note. The `defaults:` table
gains `on_error`.

### S-4: Witnesses

- RED: `tests/unit/test_fr1124_llm_default_on_error.py` compiles a
  two-node graph whose first `llm` node raises through a stub provider
  and declares no `on_error`; asserts the invoke raises with the node
  named. Fails today (returns normally with `errors` populated).
- `defaults.on_error: skip` on the same graph → no raise, second node
  runs, `errors` carries one `tolerated: true` entry (FR-1097 tally
  unchanged).
- Node `on_error: fail` under `defaults.on_error: skip` → raises.
- Invalid `defaults.on_error` fails at load naming the value.
- `handle_error` with `on_error=None` for an `llm` node is no longer
  reachable: a test asserts the resolved config never carries `None`.
- FR-1097's tally tests pass unchanged.

### S-5: Migration by census

The 134 graphs are a corpus; sequential review is the
`impossibly_large_sequential_task` signal. Discovery is a Python walk
over graph YAML (the FR-1083 method, no LLM): it lists the 224 nodes.
Classification is the census graph (FR-1120's `cap_journey_census`
shape: extract each node with its downstream readers, judge, reduce to
a ledger), because deciding whether continuation is load-bearing means
reading the graph after the node. Each node lands in one class:

- **A: nothing depends on continuation** — the failed node's
  `state_key` is read only by nodes that would fail without it, or the
  node is last before END. Default `fail` is the correct behaviour;
  no edit.
- **B: continuation is load-bearing** — a downstream node, condition
  or map consumes the absent value deliberately (an `{% if %}` guard,
  a `requires:` gate, a tolerated verdict). These get `on_error: skip`
  on the node, or `defaults.on_error: skip` if every `llm` node in the
  graph is class B.

Class B edits are graph authoring and go through `scripts/author.sh`
with one committed brief per example directory. The census output is
committed as `docs/issues-<date>-fr1124-census.md` with one row per
node, so the judge and the migration author read the same list. The
FR's implementation record states the A/B counts.

### S-6: Sequencing

1. RED witness; S-1, S-2, S-3; GREEN. Unit suite green except graphs
   whose tests rely on continuation, which are class B by definition
   and are listed.
2. Census committed; class B edits authored; suite green.
3. Changelog fragment of type `removal` for the record-and-continue
   behaviour and `feat` for `defaults.on_error`; release note names
   the default change as the headline.

### Not in scope

- Map sub-node, race, router and `tool_call` defaults (FR-1073, FR-778
  own them).
- Making `invoke_graph` or `run_graph_async` raise on recorded
  tolerated errors: with default `fail` the untolerated case already
  raises; tolerated skips remain data in `errors`, as FR-1097 defined.
- A new enum value naming record-and-continue: rejected below.

## Acceptance Criteria

- [ ] AC-1: RED test fails on main (normal return, `errors` populated)
  and passes after S-1 (raise naming the node); RED and GREEN are
  separate commits.
- [ ] AC-2: an `llm` node's resolved `on_error` is never `None`; the
  `handle_default` fall-through is removed from the `llm` dispatch and
  `vulture` reports no new dead code.
- [ ] AC-3: `defaults.on_error` accepts the four values, is overridden
  per node, applies to `llm` nodes only, and rejects any other value at
  load with the value named.
- [ ] AC-4: the common node table, the `on_error` value table and the
  `defaults:` table in `reference/graph-yaml.md` state the default and
  the override; the sentence "record-and-continue" appears nowhere as a
  supported mode.
- [ ] AC-5: the census file lists every one of the 224 nodes with an
  A or B class and the evidence line; every class B node has an
  authored `on_error` or its graph a `defaults.on_error`, each with a
  committed brief and adapter report.
- [ ] AC-6: the full unit suite and `yamlgraph graph lint` over every
  repository graph pass; FR-1097 and FR-1098 tests pass unchanged.
- [ ] AC-7: all new tests carry a REQ ID (the error-handling
  requirement FR-1083 cites, or a new one via the FR-975/FR-980
  route); `python scripts/req_coverage.py --strict` passes.
- [ ] AC-8: changelog fragments (`removal` and `feat`), FR
  implementation record with A/B counts, Distill diary entry with a
  `**Seed:**`.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Keep record-and-continue, name it as a fifth enum value (`record`) and document it | Rejected. It would legitimise the behaviour that produced nine silent days; a node that continues after failing without marking itself skipped has no honest reader. |
| Default `skip` (tolerated, `_skipped`, continue) | Rejected. Continuation stays the default for 224 nodes, and a skip is exactly what the digest's formatting node could not tell from a quiet day. `skip` remains available by declaration. |
| Make `invoke_graph` / `run_graph_async` raise when `errors` is non-empty, leave the node default alone | Rejected as the sole fix. It repairs the caller and leaves every downstream node blind; the digest's formatting node would still route to END before the raise. Kept in spirit: with default `fail` the raise happens at the node. |
| Lint warning for `llm` nodes without `on_error` | Rejected. 224 warnings on day one is noise; lint without a gate is advisory (`detection_without_enforcement`). |
| Change the default only behind `defaults.on_error`, keep continue when absent | Rejected. The absent case is the case that failed; a default that only applies when declared is not a default. |
| Migrate all 134 graphs by reading them one by one | Rejected; discovery by Python walk, classification by the census graph, author.sh only for class B edits. |

`is_this_a_graph`: the default is not. The migration census is: its
discovery adapter is a deterministic YAML walk, but the A/B judgement
per node reads downstream graph structure and is the extract-and-judge
shape the FR-1120 census graph exists for. All five research personas
gave that answer; the brief's author had proposed a script.

## Related

- `yamlgraph/node_factory/llm_execution.py` (`handle_error`),
  `yamlgraph/error_handlers.py` (`handle_default`, `to_state_update`),
  `yamlgraph/node_factory/llm_nodes.py` line 164,
  `yamlgraph/tools/python_tool.py` (default `fail`),
  `yamlgraph/node_factory/tool_nodes.py` (default `skip`),
  `yamlgraph/constants.py` (`ErrorHandler`).
- `reference/graph-yaml.md` common node table and `on_error` value
  table.
- FR-1083 §Reachable paths row P1; FR-1121 (incident), FR-1123
  (schema half).
