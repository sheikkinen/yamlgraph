# Feature Request: An LLM node without `on_error` gets a named, documented default

**Priority:** HIGH
**Type:** Bug
**Status:** Approved with revisions ([judgement](FR-1124-llm-node-default-on-error.judgement.md), 2026-09-27); R-1..R-3 folded 2026-09-27 (see [Judgement fold](#judgement-fold-2026-09-27)); authority active, not yet enforced
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

### S-1: Default `fail`, resolved at the top-level `llm` compiler seam (R-1)

`NodeConfig` owns only the node's own `on_error` and defaults it to
`None` (`node_schema.py`); graph defaults are the untyped
`GraphConfigSchema.defaults` dict (`graph_schema.py`). The resolution
therefore lives where both are visible, in the node compiler:

1. `GraphConfigSchema` gains a validator for `defaults.on_error`, the
   twin of `validate_defaults_on_overflow` (FR-939): the value must be
   one of the four `ErrorHandler` members, and the error names
   `defaults.on_error` and the offending value.
2. `_compile_llm_node` (`node_compiler.py`) computes an effective copy of
   the node config for an authored top-level node whose declared type
   is exactly `llm`: explicit node `on_error` → `ctx.effective_defaults["on_error"]`
   → `"fail"`, and passes that copy to `create_node_function`.
3. `_compile_llm_node` is shared with `router` (FR-759 P3); the
   normalisation is conditioned on the declared type being `llm`.
   Routers are unchanged.
4. Map sub-nodes enter `create_node_function` through
   `compile_map_node`, not `_compile_llm_node`, and are unchanged
   (FR-1073 owns them). Top-level status is decided by the compile
   path, never inferred from a generated node-name prefix.
5. Race and every other node type are unchanged.

`handle_error`'s fall-through to `handle_default` stays (R-2): routers
and map `llm` sub-nodes still reach it. After resolution an authored
top-level `llm` node cannot, and a witness proves that (S-4).

### S-2: `defaults.on_error`

The graph-level `defaults:` block accepts `on_error` with the same four
values, validated at load like `defaults.on_overflow` (FR-939, S-1
item 1). It applies to authored top-level `llm` nodes only; `router`,
`race`, `python`, `tool`, `tool_call`, `copilot`, `agent`, `subgraph`,
guard and map sub-node defaults are untouched. A node value overrides
it.

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
  two-node graph whose first authored top-level `llm` node raises
  through a stub provider and declares no `on_error`. On main the
  invoke returns normally with one untolerated error. After GREEN the
  *original* exception propagates unchanged (`handle_fail` re-raises;
  its exception identity is not touched, R-2) and the downstream node
  is never invoked (spy assertion).
- Resolution: explicit node value → `defaults.on_error` → `fail`; the
  resolved `LLMNodeConfig.on_error` is always one of the four
  `ErrorHandler` values.
- `defaults.on_error: skip` on the same graph → no raise, second node
  runs, `errors` carries exactly one `tolerated: true` entry with the
  existing skip markers (`_skipped`, `_skip_reason`); FR-1097's tally
  is unchanged.
- Node `on_error: fail` under `defaults.on_error: skip` → the original
  exception propagates.
- Invalid `defaults.on_error` fails graph load naming
  `defaults.on_error` and the value.
- Exclusions: an undeclared `router`, an undeclared `race` node and an
  undeclared map `llm` sub-node retain their current policies with and
  without `defaults.on_error`.
- Reachability (R-2): a test proves an authored top-level `llm` node
  cannot reach `handle_default` after resolution, and that an excluded
  node kind still can. `handle_default` is not deleted.
- FR-1097 and FR-1098 error-status regressions pass unchanged.

### S-5: Migration by census

The 134 graphs are a corpus; sequential review is the
`impossibly_large_sequential_task` signal. The migration is a
deterministic inventory reconciled against a census ledger (R-3):

1. **Inventory.** A committed discovery script (`scripts/fr1124_inventory.py`
   or the FR-1083 walk, whichever is committed) at the implementation
   SHA lists every eligible node: an authored top-level node whose
   declared or default type is `llm`, under the roots `examples/`,
   `graphs/`, `.github/`, excluding `prompts/` directories and map
   sub-nodes. The FR's implementation record states the command, roots,
   inclusion rule, exclusions, git SHA, discovered total, and the
   reconciliation against the filing baseline of 224.
2. **Ledger.** One row per discovered node, committed as
   `docs/issues-<date>-fr1124-census.md`: graph path, node name,
   `state_key`, downstream reader or terminal edge, A/B class, source
   evidence, resulting policy. A mechanical check asserts the ledger's
   identity set equals the inventory's with no duplicates or omissions;
   empty, duplicate or unknown identities fail the migration.
3. **Classification.** The census graph (FR-1120's `cap_journey_census`
   shape: extract each node with its downstream readers, judge, reduce)
   proposes the A/B class; its claims are reconciled against the
   deterministic inventory before any authoring run.
   - **A: adopts the new `fail` default** — no graph edit.
   - **B: the author intentionally chooses tolerated continuation** —
     the node gets explicit `on_error: skip`, or the graph gets
     `defaults.on_error: skip` only when every eligible `llm` node in it
     is B. B does not preserve record-and-continue: `skip` changes the
     error to tolerated and adds the skip state markers.
4. **Authoring.** Every B edit goes through `scripts/author.sh` with a
   committed brief under `feature-requests/authoring-briefs/`, passing
   lint and the narrowest honest smoke attempt (or an exact
   blocked-validation record). The adapter report stays the route's
   transient artifact at `tmp/draft-authoring-report.md`; the
   implementation record cites its validation outcome per graph. No A
   graph is edited to restate `fail`; no graph outside the B ledger is
   changed.
5. **Drift.** The inventory is re-run after the migration and must
   reconcile again.

### S-6: Sequencing

1. RED witness; S-1, S-2, S-3; GREEN. Framework behaviour lands
   before any migration (C-6).
2. Inventory and ledger committed and reconciled (C-4); class B edits
   authored through the sole route (C-5); inventory re-run; suite
   green.
3. Separate changelog fragments: `removal` for the implicit
   record-and-continue policy, `feat` for `defaults.on_error`; release
   note names the default change as the headline.

### Not in scope

- Router, race, map sub-node, `tool_call`, python, tool, copilot,
  agent, subgraph and guard defaults (FR-1073 and FR-778 own the map
  and `tool_call` ones); a need to change any of them is a separate
  judged FR (C-7).
- The exception identity re-raised by `handle_fail`, and the shared
  `handle_default` fall-through: both stay (C-3).
- CLI tally and exit semantics (FR-1097, FR-1098).
- Making `invoke_graph` or `run_graph_async` raise on recorded
  tolerated errors: with default `fail` the untolerated case already
  raises; tolerated skips remain data in `errors`, as FR-1097 defined.
- A new enum value naming record-and-continue: rejected below.

## Acceptance Criteria

The judgement's revised list is binding; it replaces the original
AC-1..AC-8.

- [ ] AC-01: RED first: a two-node graph whose first authored top-level
  `llm` has no `on_error` and whose stub provider raises returns
  normally with one untolerated error on main; after GREEN the original
  exception propagates and the downstream node is not invoked. RED and
  GREEN are separate commits.
- [ ] AC-02: resolution tests prove explicit node value →
  `defaults.on_error` → `fail` for authored top-level `llm` nodes, and
  the resolved `LLMNodeConfig.on_error` is one of the four
  `ErrorHandler` values.
- [ ] AC-03: `defaults.on_error` accepts exactly `skip`, `retry`, `fail`
  and `fallback`; an invalid value fails graph load naming
  `defaults.on_error` and the value; an explicit node value overrides
  it.
- [ ] AC-04: an undeclared router, race node and map `llm` sub-node
  retain their current policies; `defaults.on_error` does not alter
  them.
- [ ] AC-05: the shared `handle_default` fall-through remains available
  to excluded callers, while a test proves an authored top-level `llm`
  cannot reach it after effective-policy resolution.
- [ ] AC-06: `defaults.on_error: skip` on a top-level `llm` records
  exactly one tolerated error, sets the existing skip markers, and
  permits the downstream node; explicit node `fail` under that default
  propagates the original exception.
- [ ] AC-07: `reference/graph-yaml.md` documents the top-level `llm`
  default and priority in the common-node, `on_error` value and
  `defaults` tables, and does not present record-and-continue as a
  supported authored mode.
- [ ] AC-08: a deterministic inventory at the implementation SHA emits
  every eligible top-level repository `llm` identity; the committed
  census ledger has exactly the same identity set, no duplicates, A/B
  counts, evidence and resulting policy, and reconciles any difference
  from the filing baseline of 224.
- [ ] AC-09: every B row has explicit `on_error: skip`, or belongs to a
  graph using `defaults.on_error: skip` whose every eligible `llm` is
  B. Each edited graph cites a committed authoring brief and has a
  verified adapter report, passing lint, and a narrow smoke attempt or
  an exact blocked-validation record.
- [ ] AC-10: no A graph is edited solely to restate `fail`; no graph
  outside the B ledger is changed by the migration.
- [ ] AC-11: focused FR-1124 tests, FR-1097/FR-1098 error-status
  regressions, the full unit suite, strict requirement coverage, and
  lint over the deterministic graph inventory pass.
- [ ] AC-12: all new tests carry the governing REQ ID; the
  implementation record names the RED/GREEN commits, inventory SHA and
  counts, A/B counts, authoring runs, validation outcomes, and
  deviations.
- [ ] AC-13: separate `removal` and `feat` changelog fragments describe
  the removed implicit policy and `defaults.on_error`; a Distill diary
  entry contains `**Seed:**`.

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

## Judgement fold (2026-09-27)

[Judgement](FR-1124-llm-node-default-on-error.judgement.md): APPROVED
WITH REVISIONS. Folded the same day:

- **R-1** → S-1 rewritten: resolution at `_compile_llm_node` for
  authored top-level `type: llm` only; `GraphConfigSchema` validates
  `defaults.on_error`; router, race and map sub-nodes excluded by
  compile path, never by name prefix. S-2, Not in scope, AC-02..AC-05
  amended.
- **R-2** → S-1 and S-4 corrected: `handle_fail`'s exception identity is
  untouched and the shared `handle_default` fall-through stays; the
  witness asserts propagation of the original exception and downstream
  non-execution; the deletion/vulture AC is replaced by a reachability
  witness. Removed the wrong claim that FR-1083 paths P2, P3 and P5
  call `handle_default` (they build their own `PipelineError`; the
  only caller is `handle_error`'s fall-through).
- **R-3** → S-5 rewritten as inventory plus reconciled ledger; class B
  redefined as "the author chooses tolerated skip", not "preserves
  record-and-continue"; the adapter report stays the route's transient
  artifact and only its outcome is recorded. S-6, AC-08..AC-10 amended.

Scope frozen to the judgement's D-1..D-7; conditions C-1..C-7 are
gates.

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
