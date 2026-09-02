# Problem brief: every map branch receives a copy of the whole parent state

**Prior art:** FR-936
(`feature-requests/FR-936-map-node-hardening.md`) bundled this concern
with three others and was SPLIT by its judgement
(`feature-requests/FR-936-map-node-hardening.judgement.md`, R-3, C-2,
AC-03/AC-04); this brief is that judgement's deliverable D-1 and
inherits its scope fence: overflow disposition (D-2, FR-939), timeout
lifecycle (D-3), and native retry (D-4) are adjacent but out of bounds.
`capabilities/CAP-11-subgraph-map.yaml` is the governing capability.
FR-052 (`feature-requests/052-map-output-flattening.md`) shapes what a
branch *returns*, not what it *receives* — no overlap. FR-467
(`feature-requests/FR-467-conditional-edge-to-map-node.md`) routes into
a map node; it does not touch the `Send` payload. FR-030
(`feature-requests/030-map-concurrency-control.md`, Won't Fix) is about
how many branches run at once, not what each carries. A REJECTED-FR
sweep found no prior proposal governing `Send` payload contents.

## Problem statement

`map_edge` dispatches one `Send` per item with
`{**state, item_var: item, "_map_index": i}`
(`yamlgraph/compile/map_compiler.py:363-366`): a shallow copy of the
complete parent state mapping travels into every branch, regardless of
what the sub-node reads. LangGraph persists each parallel branch's input
and output as pending writes, so with a checkpointer attached every
branch write carries the whole parent state. At the first named
consumer's scale (a ~500k-item fan-out, `docs/plan-web-toolkit.md`
component D) the run becomes memory- and IO-bound on state copies
rather than on LLM work, and the in-run crash durability that pending
writes already provide is undermined by the size of each write.

The root cause is that the compiler does not know which state keys a
sub-node needs, so it passes everything. That set is not derivable from
prompt text alone. Today:

- an `llm` sub-node with empty `variables` receives *every*
  non-underscore, non-None state value as prompt variables
  (`yamlgraph/utils/expressions.py:262-265`);
- Jinja templates receive the state object directly as `state`
  (`yamlgraph/executor_base.py:115-117`), so `{{ state.anything }}`
  is legal without declaration;
- `requires:` and `skip_if_exists` read state keys at execution time
  (`yamlgraph/error_handlers.py:183-199`; `NodeConfig.skip_if_exists`,
  `yamlgraph/models/node_schema.py:155-157`);
- guards evaluate expressions against state
  (`yamlgraph/utils/guard_runtime.py:87,162,180`);
- `python` sub-nodes receive the full effective state object
  (`yamlgraph/tools/python_tool.py:299-311`);
- `tool_call` sub-nodes resolve tool name and args from arbitrary
  `{state.…}` expressions (`yamlgraph/node_factory/tool_nodes.py:99-127`);
- `subgraph` sub-nodes declare their inputs via `input_mapping`, which
  may be `"*"` or `"auto"` (`yamlgraph/node_factory/subgraph_nodes.py:35-42`);
- `agent` sub-nodes read state dynamically through their tools.

The only existing static extractor recognises a narrow
`{{ state.key }}` shape (`yamlgraph/linter/checks_prompts.py:48-50`).

The problem: there is no contract for what a map branch's input
payload contains. The payload is "everything", by accident of
implementation, and neither the graph author nor the compiler can say
otherwise.

## Classification

enforcement/latency-critical

## Constraints

- The FR-936 judgement scope fence applies (C-1, C-6): this concern
  ships alone — no overflow, timeout, retry, durability, caching,
  Store, chunked-scheduling or checkpoint-format changes ride along.
- Correctness before size (FR-936 judgement C-2, rejudgement C-3): a
  state key may be omitted from a branch payload only when every
  execution-time consumer of that branch is proven not to need it —
  prompt-text matching alone is insufficient evidence. Consumers that
  must be covered, per sub-node type: `variables`, empty-`variables`
  pass-through, direct Jinja `state` access, `requires`, guards
  (pre/post), verification, routing (`router` sub-nodes), `skip_if_exists`,
  and the framework's internal fields (`_map_index`, `_loop_counts`,
  `errors`).
- Sub-node types whose reads cannot be derived statically (`python`,
  `agent`, `tool_call` with state-resolved args, `subgraph` with
  `input_mapping: "*"` or `"auto"`) must retain a safe default; any
  reduced payload for them must be an explicit author declaration, and
  the retained-everything case must be visible to the author (the
  linter is the established surface for "visible but allowed").
- Any author-facing declaration must be typed on `NodeConfig`
  (Pydantic, Commandment 5) and validated at graph load (Commandment 3).
- `as`-variable injection (`map_compiler.py:264-268`) and `_map_index`
  ordering (`sorted_add` reducer) must be preserved byte-for-byte in
  behaviour: same results, same order, same error shapes.
- Witnesses must measure what the consumer pays: the exact key set of
  each `Send` payload AND the serialized size of a checkpointer
  pending-write or checkpoint for a branch, with an unrelated large
  state value present. A test asserting only Python object size of a
  shallow copy proves nothing (`{**state}` copies references).
- Existing map demos and examples (`examples/demos/map`,
  `examples/demos/python-map`, `examples/book_reviewer`,
  `examples/icpc-2-rfe`, `examples/cwe-classifier`) must run unchanged
  with no declaration added — reduction must be safe-by-default or
  opt-in, never silently lossy.
- `is_this_a_graph`: must be answered — this is a compile-time payload
  contract inside the framework's fan-out boundary, but the research
  must confirm no graph-shaped alternative (e.g. a projection node
  authored in YAML ahead of the map) is being missed.

## Witnessed incidents

- 2026-08-31 FR-936 audit: `Send(sub_node_name, {**state, item_var: item,
  "_map_index": i})` confirmed at `yamlgraph/compile/map_compiler.py:363-366`;
  judgement recorded that the shallow copy is prepared for every
  surviving item after the cap check.
- FR-936 judgement R-3 (2026-08-31): rejected a prompt-text-only
  derivation because empty `variables` means "pass every non-internal
  state value" (`yamlgraph/utils/expressions.py:262-265`) and Jinja
  receives the state object directly (`yamlgraph/executor_base.py:115-117`);
  required Python sub-nodes to be classified as dynamic readers.
- FR-936 rejudgement (2026-09-02) R-3 / AC-05 / C-3: the fence above,
  plus the requirement that witnesses assert exact keys and reduced
  serialized pending-write size.
- `docs/plan-web-toolkit.md` "Existing map node audit" item 1 and the
  "Free lunch already banked" note: with the SQLite checkpointer
  attached, pending writes already give partial in-run crash durability
  today — "currently undermined by deviation 1 making every write
  huge". Component D (resumable map) is sequenced behind this fix.
- `docs/2026-09-02-brainstorm-business-use-cases.md` §5.2: every
  census-scale use case ranked 1–14 is map-reduce; D-1 is named as the
  blocker for checkpointing at scale.
