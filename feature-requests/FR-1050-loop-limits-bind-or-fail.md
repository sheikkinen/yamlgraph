# FR-1050: `loop_limits` must bind or fail compilation

**Priority:** HIGH
**Type:** Bug
**Status:** **Judged APPROVED WITH REVISIONS 2026-09-18** —
[FR-1050-loop-limits-bind-or-fail.judgement.md](FR-1050-loop-limits-bind-or-fail.judgement.md).
R-1 through R-4 are folded in below (Proposed Solution, Deferred, Acceptance
Criteria, Migration); authority is active for the frozen scope, enforcement not
yet started.
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
| `interactive_tool`, `pipeline` | expansion-only macros, erased before compilation | no — the authored node no longer exists when limits are validated |

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

### Move 1 — standalone `race` enforces (R-2)

`race` is an LLM node with N candidates. Its limit semantics are the `llm`
semantics, already settled at `llm_nodes.py:306`: check before firing, return
`{"_loop_limit_reached": True, "current_step": node_name}` without executing,
leave the counter untouched. Add that check to `race_node.py`, ahead of the
existing increment.

**`router_race_node.py` gets no production change (judgement R-2).** A router
with `candidates` already runs the `llm`/`router` check before incrementing and
before dispatching to `_execute_router_race` (`llm_nodes.py:303-309,337-342`);
`_execute_router_race` receives an already incremented counter and never
increments itself (`router_race_node.py:33-40,102-105,129-132`). A second check
there would read the incremented value and could suppress the Nth permitted
execution. A regression test still proves candidates do not fire after
exhaustion on that path.

### Move 2 — compile-time support matrix, validated before expansion (R-1)

Mirroring FR-677's `GUARD_SUPPORTED_TYPES`:

```python
LOOP_LIMIT_SUPPORTED_TYPES: frozenset[str] = frozenset(
    {NodeType.LLM, NodeType.ROUTER, NodeType.PYTHON, NodeType.TOOL,
     NodeType.PASSTHROUGH, NodeType.RACE}
)
```

Validation iterates **every graph-level `loop_limits` entry against the raw
authored node map, before `interactive_tool` and `pipeline` expansion** — not
node-by-node inside `compile_node`, which iterates nodes rather than entries
(`node_compiler.py:299-330`) and therefore cannot see dangling keys, and which
runs after both transforms have deleted the authored macro node
(`graph_loader.py:160-171`; `interactive_tool.py:38-55,83-107`;
`pipeline_template.py:90-107,126-130`). The boundary check rejects:

- a key naming no authored node (the compile-time hole today covered only by
  advisory linter E008, `checks_semantic.py:67-72`);
- an authored node whose type is outside the supported set;
- the expansion-only `interactive_tool` and `pipeline` types.

`interactive_tool.max_iterations` and the `loop_limit` it generates internally
are untouched; this FR governs graph-level `loop_limits` only.

An entry naming a node whose type is outside the set raises `GraphConfigError`
at compilation, naming the node, its type, and the supported set — the error
shape FR-677 already established.

```
GraphConfigError: Node 'ask_recap' of type 'interrupt' has a 'loop_limits'
entry but loop limits are only enforced on node types ['llm', 'passthrough',
'python', 'race', 'router', 'tool']. Remove the entry or change the node type.
```

### Move 3 — the classification cannot drift (R-3)

Deriving the supported set by compiling one node per type is circular:
compilation with `loop_limits` is itself gated by that set, so it cannot
independently discover support.

Instead, two explicit, disjoint classifications —
`LOOP_LIMIT_SUPPORTED_TYPES` and `LOOP_LIMIT_UNSUPPORTED_TYPES` — whose union
equals the complete `NodeType` enum (`yamlgraph/constants.py:10-27`). A new
enum value left unclassified fails the test. Compile rejection is parameterised
over the unsupported set (including the expansion-only types); execution at
exhaustion is parameterised over every supported runtime type, each asserting
`_loop_limit_reached`, an unchanged `_loop_counts`, and zero underlying
work/candidate calls. Either drift direction fails, without pretending a
maintained classification was inferred. This is the part FR-027 lacked, and the
reason it decayed.

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

## Scope (frozen by the judgement)

| Deliverable | Surface |
|---|---|
| D-1 | Pre-expansion validation of every graph-level `loop_limits` key and the exhaustive node-type classification, in `yamlgraph/compile/` plus the minimal shared constants that boundary needs |
| D-2 | Standalone `race` pre-execution limit enforcement in `yamlgraph/node_factory/race_node.py` |
| D-3 | RED/GREEN and regression coverage in a dedicated FR-1050 unit-test module: supported, unsupported, dangling, macro-node, router-with-candidates, W012 and `loop_exits` cases |
| D-4 | Removal of the five inert entries from `examples/demos/multi-turn/graph.yaml` and `examples/demos/book-summary/graph.yaml`, with honest comments and refreshed demo evidence |
| D-5 | `reference/graph-yaml.md`, `CAP-17`, generated requirement docs, changelog fragment, FR implementation log, Distill diary entry |

Not authorised: runtime loop-limit semantics for `interrupt`, `map`,
`subgraph`, `tool_call`, `agent`, `copilot`, `verify`, `interactive_tool` or
`pipeline`; direct-edge loop-exit traversal; W012 behaviour;
`interactive_tool.max_iterations`; production changes in `router_race_node.py`;
changes in the csap repository; NC-522.

## Acceptance Criteria

- [ ] AC-01 RED first: a compiled standalone `race` node with a graph-level
  limit is driven past the limit; on current main the candidate is called,
  after the fix it is not.
- [ ] AC-02 Standalone `race` calls `check_loop_limit` before incrementing
  `_loop_counts`; exhaustion returns exactly `{"_loop_limit_reached": True,
  "current_step": <node>}`, leaves the counter unchanged, and fires no
  candidate.
- [ ] AC-03 A router with `candidates` retains its existing outer `llm`/`router`
  behaviour: exhaustion occurs before `_execute_router_race`, leaves the counter
  unchanged, and fires no candidate. `router_race_node.py` has no production
  change.
- [ ] AC-04 Before macro expansion, compilation iterates every graph-level
  `loop_limits` entry. A missing node key raises `GraphConfigError` naming the
  key; an unsupported node raises `GraphConfigError` naming the node, its type,
  and the sorted supported set.
- [ ] AC-05 Unsupported-type rejection is asserted per classification entry,
  including `interrupt`, `map`, `tool_call`, `agent`, `copilot`, `verify`,
  `subgraph`, `interactive_tool` and `pipeline`.
- [ ] AC-06 `LOOP_LIMIT_SUPPORTED_TYPES` and `LOOP_LIMIT_UNSUPPORTED_TYPES` are
  disjoint and their union equals the complete `NodeType` enum; a new node type
  left unclassified fails the test.
- [ ] AC-07 Each supported type (`llm`, `router`, `python`, `tool`,
  `passthrough`, `race`) compiles and is exercised at exhaustion, asserting the
  limit flag, unchanged counter, and zero underlying work calls.
- [ ] AC-08 An exhausted standalone `race` reaches its declared `loop_exits`
  target through the existing routing seam, asserted on a compiled walk.
- [ ] AC-09 A cycle whose only declared bound is unsupported fails compilation;
  W012 is not modified and cannot provide false reassurance for that graph.
- [ ] AC-10 The five inert in-repo entries are removed from
  `examples/demos/multi-turn/graph.yaml` and
  `examples/demos/book-summary/graph.yaml` **through the graph-authoring route**
  (`scripts/author.sh`). Each graph records that the removed bound was never
  live, both demos have refreshed `demo-output.log`, and
  `tmp/draft-authoring-report.md` records lint/smoke outcomes honestly.
- [ ] AC-11 `reference/graph-yaml.md` documents the supported and rejected
  types; `CAP-17` gains a requirement for bind-or-fail loop limits;
  `ARCHITECTURE.md` is regenerated; every new test carries that
  `@pytest.mark.req(...)`; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-12 `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` and
  `ruff check yamlgraph/` pass; `yamlgraph graph validate` passes on every graph
  under `graphs/`, `examples/` and `projects/`.
- [ ] AC-13 A `changelog/unreleased/` fragment references the new requirement;
  the FR records implementation status, decisions and deviations; a
  `docs/diary/` Distill entry carries a **Seed:**.

## Migration

Breaking for any graph carrying an entry on a now-rejected type — including the
expansion-only `interactive_tool` and `pipeline` macros, and keys naming no
node at all: 5 entries in this repo (AC-10), 16 in csap. The fix is deletion —
the entry never did anything, so removing it changes no behaviour.

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

## Judgement

APPROVED WITH REVISIONS, 2026-09-18 —
[FR-1050-loop-limits-bind-or-fail.judgement.md](FR-1050-loop-limits-bind-or-fail.judgement.md).
R-1 (pre-expansion validation of the whole `loop_limits` map, including dangling
keys and macro nodes), R-2 (no production change in `router_race_node.py`), R-3
(two explicit disjoint classifications instead of the circular drift test) and
R-4 (changelog fragment, CAP-17 requirement, `reference/graph-yaml.md`,
authoring route for the demo migrations, Distill entry) are folded in above.
Gates C-1 to C-6 of the judgement bind enforcement.

## Implementation Status

**ENFORCED 2026-09-18** on `feat/fr-1050-enforce`. REQ-YG-683 (CAP-17).

| Decision | Landed as |
|----------|-----------|
| D-1 | `yamlgraph/compile/loop_limits.py` — `LOOP_LIMIT_SUPPORTED_TYPES` / `LOOP_LIMIT_UNSUPPORTED_TYPES` + `validate_loop_limits()`, called from `load_graph_config` after `apply_loop_node_defaults` and before the `interactive_tool` / `pipeline` expansions (R-1: the expansions erase the authored nodes, so validation must precede them). |
| D-2 | `yamlgraph/node_factory/race_node.py` — `check_loop_limit` consulted before any candidate is fired, matching the llm-node contract. |
| D-3 | `yamlgraph/node_factory/router_race_node.py` unchanged (R-2); a test asserts `check_loop_limit` stays absent from its source. |
| D-4 | `examples/demos/multi-turn/graph.yaml` (`wait_for_user`) and `examples/demos/book-summary/graph.yaml` (`fetch_batch`, `render_pages`, `transcribe_pages`, `summarize_pages`) migrated via `scripts/author.sh`; report at `tmp/draft-authoring-report.md`, blocked validation: none. `tests/fixtures/interrupt_loop_end.yaml` lost its inert `ask` (interrupt) and `plan` (map) entries. |
| D-5 | CAP-17 REQ-YG-683 + `ARCHITECTURE.md` regenerated, `reference/graph-yaml.md` supported/rejected table, `changelog/unreleased/fr-1050-loop-limits-bind-or-fail.md`, refreshed `demo-output.log` for both demos, Distill entry in `docs/diary/`. |

Witness: `tests/unit/test_fr1050_loop_limits_bind_or_fail.py`, 33 tests, all
`@pytest.mark.req("REQ-YG-683")`. RED commit `d82a868e` (17 failed / 16 passed)
precedes the GREEN.

**Deviations:** none from frozen scope. AC-12 was executed as a load-time sweep
over every `*.yaml` under `graphs/` and `examples/` containing a `loop_limits`
block (19 graphs, 0 rejections) — `projects/` does not exist in this checkout.
`tests/unit/test_ramp_installer.py::test_wrapper_delegates` fails identically on
the untouched main checkout (`No module named 'yaml'` inside the `scripts/ramp.sh`
subprocess, an interpreter-selection fault in the local environment); it is
independent of this change and is not repaired here.

## Related

- `yamlgraph/compile/node_compiler.py:329` — limit injection
- `yamlgraph/routing.py:82` — the only reader of `_loop_limit_reached`
- `yamlgraph/linter/checks_semantic.py:302` — W012
- csap NC-522 — the investigation that surfaced this; explicitly not unblocked
