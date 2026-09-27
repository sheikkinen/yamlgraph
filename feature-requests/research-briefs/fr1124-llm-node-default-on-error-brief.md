# Problem brief: an LLM node with no `on_error` runs a fifth strategy the reference does not name

**Prior art:** FR-1083
(`feature-requests/FR-1083-exit-code-reflects-errors.md`, Split
2026-09-26) enumerated every path that appends to `state.errors` and
lets a run complete; its row P1 is exactly this path — "LLM node, no
`on_error`, call fails → `handle_default`" — and its census D4 found
that none of 202 graphs and not the CLI read `state.errors`. It did not
propose changing the path, only making the CLI's exit status reflect
it. FR-1066 (REJECTED) was the first filing of that exit-status goal;
its rejection concerned research and reachable paths, not the default
handler. FR-1097 (Implemented 2026-09-26) makes `graph run` exit 3 when
a completed run recorded untolerated errors; FR-1098 does the same for
streaming. Neither reaches a Python caller of `compiled.invoke` or
`invoke_graph`. FR-778 (`feature-requests/FR-778-tool-call-on-error-fail.md`)
added `on_error: fail` to `tool_call` nodes whose default is `skip`
with a failure envelope, and its rationale — deterministic pipelines
need a failed prerequisite to stop the run — is the same argument at a
different node type. FR-1121 (Proposed, sibling in this PR) fixes the
one production consumer this path silenced and names the framework
question as unowned. FR-1073 H-2 moved unread map-level `on_error`
declarations into sub-nodes; it did not touch the default. No REJECTED
FR was found that proposes a default for LLM nodes.

## Problem statement

`reference/graph-yaml.md` documents four `on_error` values for a node:
`skip` (log, continue without output), `retry`, `fail` (raise, halt)
and `fallback`. The common node property table lists no `on_error` row
and no default. The `python`, `tool` (shell) and `copilot` sections
document a default of `fail`, and the code agrees for python and shell
(`python_tool.py`, `tools/nodes.py`). The `tool_call` section documents
a default of `skip` with a failure envelope (FR-778).

For an `llm` node the code does something the reference never names.
`create_llm_node` reads `on_error` with no default; `handle_error`
compares it against the four enum members, matches none, and falls
through to `handle_default`, which logs at ERROR, wraps the exception
in a `PipelineError`, and returns `NodeResult(success=False)`. The
state update appends the error to `errors`, leaves the node's
`state_key` unset, and the graph continues to the next edge. That is
not `skip` (which marks the update `_skipped` and `tolerated: true`),
not `fail` (which raises), and not documented anywhere.

Two consequences follow. First, every downstream node sees an absent
value and no signal that a node ahead of it failed; the digest's
formatting node read the absence as "quiet day" for nine unattended
runs. Second, the only surface that reports the recorded error is the
CLI's exit code (FR-1097). A Python caller of `compiled.invoke`, the
form the digest's runner and every embedding application use, receives
a normal return with `errors` populated and nothing raised; no
repository graph or tool reads that list (FR-1083 D4).

The path is unwitnessed: no test under `tests/` names
`handle_default`. It is also the repository's dominant configuration.
A census on 2026-09-27 of the 208 graph files under `examples/`,
`graphs/` and `.github/` finds 236 `llm` nodes, of which 224 declare no
`on_error`, across 134 graphs. Whatever the default becomes, it is the
behaviour of nearly every LLM node in the repository.

The open question is what an `llm` node without `on_error` should do,
whether the answer is one of the four documented values or a fifth that
must then be named and documented, how a change of that size is
migrated across 134 graphs, and whether a Python caller should learn of
recorded errors by a return value, a raise, or not at all.

## Classification

enforcement/latency-critical

## Constraints

- No fifth behaviour survives undocumented. Whatever the default is, it
  appears in the common node property table with a `Default` cell and
  in the `on_error` value table, and a test names it.
- No silent fallback (Scripture, Commandment 6). A node that failed must
  not be indistinguishable, to the next node, from a node that never
  ran; the FR-1121 incident is the witness.
- Any change to the default is a change to 224 nodes in 134 graphs.
  The research must cost the migration honestly: which graphs rely on
  continuation today, how they are found (FR-1083's census method is
  the precedent), and whether the change ships behind a graph-level
  `defaults.on_error` first or all at once.
- `python` and `tool` nodes default to `fail`; `tool_call` defaults to
  `skip` with an envelope, by a judged FR-778 decision. A proposal that
  makes `llm` differ from both must say why the third answer is
  right.
- FR-1097's exit-3 tally is a consumer of `state.errors` and must keep
  working; a default of `fail` moves these runs from exit 3 to exit 1
  and loses the partial output FR-1066 R-3 insisted on keeping. That
  trade must be stated.
- Graph and prompt edits, if a migration needs them, go through
  `scripts/author.sh` with committed briefs (FR-767); a repo-wide
  migration of 134 graphs is a corpus task and the census graph is the
  precedent (`impossibly_large_sequential_task`).
- Framework code only: `yamlgraph/node_factory/llm_execution.py`,
  `llm_nodes.py`, `error_handlers.py`, `models/node_schema.py`, the
  reference, and tests. No change to map, race or router defaults rides
  along; FR-1083's other rows stay theirs.
- `is_this_a_graph`: the default itself is not; the migration census
  of 134 graphs may be, and the research must say which.

## Witnessed incidents

- 2026-09-19 through 2026-09-27, `sheikkinen/yamlgraph-daily-digest`:
  `[ERROR] yamlgraph.error_handlers: Node rank_stories failed: ...` on
  nine consecutive runs; the graph continued, the formatting node
  reported `no_articles`, the runner exited 0, GitHub Actions showed
  success. The node declares no `on_error`.
- `yamlgraph/node_factory/llm_execution.py` on main, `handle_error`:
  four `if cfg.on_error == ErrorHandler.X` branches, then
  `nr = handle_default(node_name, error)` and
  `nr.to_state_update(...)`; `yamlgraph/error_handlers.py`
  `handle_default` returns `NodeResult(success=False, error=...)`;
  `to_state_update` sets `errors: [error]` and never sets `state_key`
  on failure.
- `yamlgraph/node_factory/llm_nodes.py` line 164:
  `on_error=node_config.get("on_error")` — no default.
  `yamlgraph/tools/python_tool.py`: `node_config.get("on_error",
  "fail")`. `yamlgraph/node_factory/tool_nodes.py` line 106:
  `node_config.get("on_error", "skip")`.
- `yamlgraph/constants.py` `ErrorHandler`: four members `skip`,
  `retry`, `fail`, `fallback`; no member for "record and continue".
- `reference/graph-yaml.md`: common node table has no `on_error` row;
  the `on_error` value table lists four values and no default; the
  `python`, `tool` and `copilot` tables state default `fail`; the
  `tool_call` table states default `skip` (FR-778).
- 2026-09-27 census over `examples/`, `graphs/`, `.github/`: 208
  graphs, 236 `llm` nodes, 12 with `on_error`, 224 without, 134 graphs
  containing at least one uncovered `llm` node.
- `grep -rln handle_default tests/` on 2026-09-27: no file.
- FR-1083 §Reachable paths, row P1, and its witnessed run: the
  `innovation_matrix` pipeline lost four of 25 map branches through
  this path inside a map, printed success output and exited 0
  (2026-09-24). FR-1097 changed that exit to 3; the state shape is
  unchanged.
- `yamlgraph/cli/graph_commands.py` line 270:
  `compute_tally(result.get("errors"), baseline)` is the only reader
  of `errors` in the CLI or executor modules.
