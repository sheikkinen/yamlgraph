# FR-1050: `loop_limits` must bind or fail compilation

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-09-18
**First consumer / first event:** the csap flex-navigator graph
(`~/src/customer-service-agent-platform/graphs/flex_navigator/graph.yaml`),
at the moment `yamlgraph graph validate` is next run against it — 50 of its
`loop_limits` entries bind nothing today, and compilation will name all 16
that remain unsupported after this FR.
**Research:** in-body dispositioned alternatives table (FR-889 style), see
[Alternatives Considered](#alternatives-considered) — the investigation was a
source read of the five enforcing call sites and the eight factories that have
none, recorded in [Problem](#problem).
**Prior art:**
- [027-execution-safety-guards.md](027-execution-safety-guards.md) — this FR
  finishes its P0 item 3, which stated the invariant ("enforced on ALL node
  types") but named three factories and shipped exactly those three.
- [FR-677-verification-first-class-dsl.md](FR-677-verification-first-class-dsl.md)
  — the precedent move, applied here to a second feature: a compile-time
  support matrix that refuses a declaration a node type cannot honour. FR-677
  deferred `race` and `interrupt` for *guards*; this FR resolves `race` for
  *loop_limits* only, and defers `interrupt` for the reason in
  [Deferred](#deferred-not-in-this-fr).
- [FR-172-loop-exit-target.md](FR-172-loop-exit-target.md) /
  [FR-630-loop-exits-end-bug.md](FR-630-loop-exits-end-bug.md) — the
  `loop_exits` seam that consumes `_loop_limit_reached`. Unchanged here; this
  FR only makes the flag reachable from more node types.
- [FR-706-race-timeout-loop-liveness.md](FR-706-race-timeout-loop-liveness.md)
  — rewrote the race node's timeout path and left its loop counter untouched;
  the counter has incremented without ever being read since.
- [REJECTED-fix-philosopher-copilot-nodes.md](REJECTED-fix-philosopher-copilot-nodes.md)
  — dismissed: rejected as a duplicate of FR-185, copilot node migration, no
  shared territory with loop bounds.

## Summary

`loop_limits` is honoured by 5 of the 13 node types. On the other 8 the entry
is silently inert: the graph declares a bound, the linter confirms the cycle is
guarded, and nothing bounds it. This FR makes an unsupported entry a compile
error, and adds enforcement to `race`, where the semantics are already settled.

## Value Statement

A graph author who writes a loop bound either gets one or gets told they
cannot have one — never a bound that reads as live and is not.

## Problem

`loop_limit` is injected into every node's config
(`yamlgraph/compile/node_compiler.py:329`), and then read by five factories:

| node type | factory | enforces |
|---|---|---|
| `llm`, `router` | `yamlgraph/node_factory/llm_nodes.py:306` | yes |
| `python` | `yamlgraph/tools/python_tool.py:278` | yes |
| `tool` | `yamlgraph/tools/nodes.py:101` | yes |
| `passthrough` | `yamlgraph/node_factory/control_nodes.py:142` | yes |
| `race` | `yamlgraph/node_factory/race_node.py:366` | **no — increments `_loop_counts`, never checks it** |
| `interrupt` | `yamlgraph/node_factory/control_nodes.py:17` | **no — never reads `loop_limit`** |
| `agent` | `yamlgraph/tools/agent.py` | no |
| `tool_call` | `yamlgraph/node_factory/tool_nodes.py` | no |
| `copilot` | `yamlgraph/node_factory/copilot_node.py` | no |
| `verify` | `yamlgraph/utils/guard_runtime.py` | no |
| `map`, `subgraph` | compiled without a counter | no |

`race` is the sharpest case: it maintains the counter and never reads it, so
the state a graph author would inspect to debug the loop is populated and
meaningless.

**The linter converts this into a clean bill of health.** W012
(`yamlgraph/linter/checks_semantic.py:302`) warns when a node in a cycle has no
`loop_limits` entry. It never asks whether the entry can be enforced. A cycle
bounded entirely by inert entries passes the check written to catch unbounded
cycles. That is worse than no W012: it is a reason to stop looking.

### Count of inert entries today

Scan of every `loop_limits` entry whose node's type is not in the enforcing
set, across both repositories:

| repo | `race` | `interrupt` | `map` | `tool_call` | total | graphs |
|---|---|---|---|---|---|---|
| yamlgraph (`graphs`, `examples`, `projects`) | 0 | 1 | 3 | 1 | **5** | 2 |
| csap (`graphs`) | 34 | 16 | 0 | 0 | **50** | 7 |

55 declared bounds, in 9 graphs, that bound nothing.

## Ideal Result

A `loop_limits` entry means one thing everywhere: this node will not execute
more than N times in a thread. Where a node type cannot make that promise, the
graph does not compile, so no author can hold a bound they do not have. The
enforcing set is discovered from the code rather than maintained by hand, so
the next node type cannot repeat FR-027's decay.

## Proposed Solution

### Move 1 — `race` and `router_race` enforce

`race` is an LLM node with N candidates. Its limit semantics are the `llm`
semantics, already settled at `llm_nodes.py:306`: check before firing, return
`{"_loop_limit_reached": True, "current_step": node_name}` without executing,
leave the counter untouched. Add the same check to `race_node.py` and
`router_race_node.py`, ahead of the existing increment.

### Move 2 — compile-time support matrix

Mirroring FR-677's `GUARD_SUPPORTED_TYPES`:

```python
LOOP_LIMIT_SUPPORTED_TYPES: frozenset[str] = frozenset(
    {NodeType.LLM, NodeType.ROUTER, NodeType.PYTHON, NodeType.TOOL,
     NodeType.PASSTHROUGH, NodeType.RACE}
)
```

A `loop_limits` entry naming a node whose type is outside the set raises
`GraphConfigError` at compilation, naming the node, its type, and the supported
set — the error shape FR-677 already established.

```
GraphConfigError: Node 'ask_recap' of type 'interrupt' has a 'loop_limits'
entry but loop limits are only enforced on node types ['llm', 'passthrough',
'python', 'race', 'router', 'tool']. Remove the entry or change the node type.
```

### Move 3 — the set cannot drift

A test asserts `LOOP_LIMIT_SUPPORTED_TYPES` equals the set of types whose
compiled node function returns `_loop_limit_reached` when its limit is
exceeded, derived by compiling a one-node graph per registered type. A new node
type that does not enforce fails this test until it is either wired or listed
as unsupported. This is the part FR-027 lacked, and the reason it decayed.

## Deferred (not in this FR)

**`interrupt` enforcement.** Bounding the ask is not the same move as bounding
a computation, and it has unresolved semantics: `_loop_limit_reached` is read
only by the conditional-edge router (`yamlgraph/routing.py:82`), so a suppressed
interrupt still lets every direct-edge node between it and the next router run —
including a `race` classifier that would then classify a stale `user_message`
the caller never sent. Compile-time rejection is honest until that is judged;
FR-677 took the same position on the same node type.

**The direct-edge traversal itself** — that a limited node's flag is not
observed until the next conditional router — is the deeper defect behind the
above. It changes traversal semantics for every existing graph and needs its own
FR and blast radius.

**This FR does not unblock csap NC-522** (bounding the summary read-back at two
rounds). Even with `race` enforcing, a visit count cannot express that policy,
because one node emits both the answer and the reconfirmation question. NC-522's
typed Python boundary stands either way. The value here is that the graph stops
claiming bounds it does not have.

## Acceptance Criteria

- [ ] AC-01 RED first: a test compiles a graph with a `loop_limits` entry on a
  `race` node, drives it past the limit, and asserts the node stops executing —
  failing on main because the limit is never read.
- [ ] AC-02 `race` and `router_race` call `check_loop_limit` before incrementing
  `_loop_counts`, and return `{"_loop_limit_reached": True, "current_step":
  <node>}` without firing any candidate.
- [ ] AC-03 A `loop_limits` entry on a node of an unsupported type raises
  `GraphConfigError` at compilation, naming the node, its type, and the sorted
  supported set. Asserted for `interrupt`, `map`, `tool_call`, `agent`,
  `copilot`, `verify` and `subgraph`.
- [ ] AC-04 A `loop_limits` entry naming each supported type compiles and
  enforces; asserted per type, not as an aggregate.
- [ ] AC-05 The drift test of Move 3 passes, and fails when a type is removed
  from its factory's check or added to the frozenset without enforcement.
- [ ] AC-06 `loop_exits` behaviour is unchanged: an exhausted `race` node
  reaches its declared exit target through the existing router seam, asserted on
  a compiled walk.
- [ ] AC-07 The two in-repo graphs are migrated — `examples/demos/multi-turn`
  (1 `interrupt`) and `examples/demos/book-summary` (3 `map`, 1 `tool_call`) —
  by deleting the unsupported entries, with a line in each graph saying the
  bound was never live.
- [ ] AC-08 W012's false reassurance is closed: a cycle whose only
  `loop_limits` entries were unsupported now fails compilation before W012 can
  report it clean. Asserted on a fixture.
- [ ] AC-09 `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` and
  `ruff check yamlgraph/` pass; `yamlgraph graph validate` passes on every graph
  under `graphs/`, `examples/` and `projects/`.
- [ ] AC-10 The FR records implementation status, decisions and deviations, and
  CHANGELOG.md is updated.

## Migration

Breaking for any graph carrying an entry on a now-rejected type: 5 entries in
this repo (AC-07), 16 in csap. The fix is deletion — the entry never did
anything, so removing it changes no behaviour.

csap's 34 `race` entries are the opposite case: they become live bounds at the
values their authors already chose. That **is** a runtime behaviour change —
`classify_recap: 6`, `generate_recap: 4`, `answer_recap_question: 2` and the
probe and extraction limits begin to fire. It realises the declared intent, but
it is not a no-op, and csap must land it behind its own FR with a witness rather
than inherit it from a version bump.

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A1 | Linter error instead of compile error | **Rejected.** Graphs are run by the chaplain, MCP server and A2A server, not only by a linted commit — FR-677's own rationale for choosing the execution boundary over the commit boundary. A lint is also advisory where this must not be. |
| A2 | Widen W012 to check enforceability, and stop there | **Rejected.** It fixes the false reassurance but leaves the inert entry compiling. The author still writes a bound and still does not get one. |
| A3 | Enforce in all 8 non-enforcing types at once | **Rejected.** `interrupt`, `map` and `subgraph` each need judged semantics (see Deferred); `race` does not, because its semantics are `llm`'s. Bundling them buys one release and spends three judgements. |
| A4 | Silently ignore, document the supported set in the schema reference | **Rejected.** This is the status quo plus a paragraph. The 55 entries were written by authors who had the docs. |
| A5 | Make the limit a runtime warning rather than a hard stop | **Rejected.** Out of territory: FR-027 chose the hard stop deliberately to cap runaway cost, and nothing here reopens that. |

## Related

- `yamlgraph/compile/node_compiler.py:329` — limit injection
- `yamlgraph/routing.py:82` — the only reader of `_loop_limit_reached`
- `yamlgraph/linter/checks_semantic.py:302` — W012
- csap NC-522 — the investigation that surfaced this; explicitly not unblocked
