# Feature Request: Map Branch Input Projection — `Send` carries only what the branch reads

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
**Effort:** 2 days
**Requested:** 2026-09-02
**First consumer / first event:** the fi-catalog pilot (component D,
`docs/plan-web-toolkit.md`) — the first map run large enough that
checkpoint pending-writes, not LLM calls, dominate wall-clock and disk.
Nearer-term: every map graph running today with the SQLite checkpointer
(`examples/book_translator`, `examples/daily_digest`, `examples/npc`)
pays the full-state-payload tax on every branch write.
**Research:** [FR-955.research.md](FR-955.research.md) — FR-890 sole
route, run 2026-09-02, five personas; six solution classes dispositioned.
**Prior art:** [FR-936-map-node-hardening.md](FR-936-map-node-hardening.md)
— SPLIT parent; this is deliverable **D-1**, fenced by its judgement
(R-3, C-2, AC-03/AC-04) and the 2026-09-02 rejudgement (R-3, AC-05, C-3).
[FR-939-map-overflow-policy.md](FR-939-map-overflow-policy.md) — sibling
D-2, owns the item-count check; this FR does not touch it.
[052-map-output-flattening.md](052-map-output-flattening.md) — shapes what
a branch returns, not what it receives. [FR-467-conditional-edge-to-map-node.md](FR-467-conditional-edge-to-map-node.md)
— routes into a map; payload untouched. [030-map-concurrency-control.md](030-map-concurrency-control.md)
(Won't Fix) — how many branches run, not what each carries. Retrieval
hits FR-533/557/560/567/568 are Dungeon Master narrative "projection"
FRs sharing only the noun; dismissed. No REJECTED FR governs `Send`
payload contents.

## Summary

Compute, at compile time, the set of state keys a map sub-node can
read; fan out with that set (plus an author-declared `pass_keys` union
and the framework's internal keys) instead of a copy of the whole
parent state. Sub-nodes whose reads cannot be decided statically keep
full state, and the linter says so.

## Value Statement

Every checkpointed map graph writes branch inputs proportional to what
the branch uses, not to the size of the parent state; the census-scale
consumer becomes buildable on the map node rather than around it.

## Problem

`map_edge` dispatches `Send(sub_node_name, {**state, item_var: item,
"_map_index": i})` (`yamlgraph/compile/map_compiler.py:363-366`). With a
checkpointer attached, LangGraph persists each branch's input as a
pending write, so every branch write carries the entire parent state.
The compiler passes everything because it does not know what the
sub-node needs, and that set is not derivable from prompt text alone:

| Consumer | Where it reads state | Statically decidable? |
|---|---|---|
| `variables: {x: "{state.X}"}` | `yamlgraph/utils/expressions.py:255-260` | yes — `X` |
| empty `variables` on `llm`/`router` | `expressions.py:262-265` passes every non-`_`, non-None key | **no** — pass-everything semantics |
| Jinja `{{ state.X }}` in prompt text | `yamlgraph/executor_base.py:115-117` exposes `state` | yes for attribute access; **no** for `state[expr]`, loops over `state`, filters |
| `requires: [a, b]` | `yamlgraph/error_handlers.py:183-199` | yes |
| `skip_if_exists` | reads the node's own `state_key` | yes |
| guards pre/post | `yamlgraph/utils/guard_runtime.py:87,162,180` evaluate expressions over state | yes when expression vocabulary is `{state.X}`; otherwise no |
| verification | reads the node result, not parent state | n/a |
| `python` sub-node | `yamlgraph/tools/python_tool.py:299-311` receives the effective state object | **no** |
| `tool_call` sub-node | `yamlgraph/node_factory/tool_nodes.py:99-127` resolves tool/args from `{state.…}` | yes when args are literal templates; **no** when `args: "{state.task.args}"` |
| `agent` sub-node | tools read state dynamically | **no** |
| `subgraph` sub-node | `input_mapping` dict → yes; `"*"`/`"auto"` → **no** (`subgraph_nodes.py:35-42`) |
| framework internals | `_map_index` (`map_compiler.py:147,184`), `_loop_counts` (`llm_nodes.py:303`) | always required |

The judgement's rule (C-2): drop a key only when every consumer is
proven not to need it. Anything else is a correctness regression
disguised as an optimisation.

## Ideal Result

A map branch receives exactly the keys it can read — derived where the
sub-node's configuration makes that decidable, declared by the author
where it does not — and a graph author can see, before running, which
map nodes still fall back to full state and why. Results, order, and
error shapes are byte-identical to today; only the payload shrinks.

## Proposed Solution

All changes inside `yamlgraph/compile/map_compiler.py`,
`yamlgraph/models/node_schema.py`, and one linter check.

### 1. `pass_keys` on `NodeConfig`

```yaml
nodes:
  classify:
    type: map
    over: "{state.domains}"
    as: domain
    pass_keys: [locale, taxonomy]   # optional; union with derived keys
    node:
      type: llm
      prompt: classify_domain
      variables:
        domain: "{state.domain}"
        rules: "{state.rules}"
      state_key: label
    collect: labels
```

`pass_keys: list[str] | None`, validated at graph load: every entry must
name a key declared in the graph's `state:` section (else load fails
naming node, key, and the declared keys).

### 2. Static derivation per sub-node type

`derive_branch_keys(sub_node_config, sub_node_type, prompt_text) ->
BranchKeys(keys: frozenset[str], decidable: bool, reasons: list[str])`:

- Always: `as` variable, `_map_index`, `_loop_counts`, the sub-node's
  `state_key` (for `skip_if_exists`), every `requires` entry.
- `variables` templates: keys from `{state.X…}` via the existing
  expression parser; `decidable=False` if `variables` is empty on an
  `llm`/`router` sub-node (pass-everything semantics must be preserved).
- Prompt templates: parse with Jinja2 (`jinja2.Environment.parse` +
  AST walk for `Getattr(Name("state"), X)`); any other use of the
  `state` name (`Getitem`, iteration, filter argument) sets
  `decidable=False`. The regex at `checks_prompts.py:48-50` is not reused
  (judgement R-3: no second partial regex).
- Guards: keys from `{state.X}` in each guard expression; non-conforming
  expression → `decidable=False`.
- `tool_call`: literal-template args → derived; state-resolved
  `tool`/`args` → `decidable=False`.
- `subgraph`: `input_mapping` dict → its parent keys; `"*"`/`"auto"` →
  `decidable=False`.
- `python`, `agent`: `decidable=False` unless `pass_keys` is declared.

### 3. Payload rule in `map_edge`

```
if decidable or pass_keys is not None:
    payload = {k: state[k] for k in (derived ∪ pass_keys) if k in state}
else:
    payload = {**state}            # today's behaviour, unchanged
payload |= {item_var: item, "_map_index": i}
```

When `pass_keys` is declared on a non-decidable sub-node, the declaration
is the author's contract: payload = declared ∪ always-keys. This is the
explicit-declaration path the judgement requires for dynamic readers.

### 4. Lint

New warning (`W0xx`, id allocated at enforcement) on every map node
whose branch payload is not projectable and has no `pass_keys`,
naming the reason(s) from `BranchKeys.reasons` and the fix:
"declare `pass_keys` or make the reads static". Existing demos will
emit this warning where they use `python`/`agent` sub-nodes; that is
the visibility the judgement asks for, not a failure.

## Acceptance Criteria

- [ ] AC-01 RED: `map_edge` payload for an `llm` sub-node with explicit
      `variables` contains exactly `{as, _map_index, _loop_counts?,
      state_key, requires…, derived keys}` and nothing else; an unrelated
      1 MB state value is absent from every `Send.arg`.
- [ ] AC-02 RED: serialized size witness — compile a two-branch map with
      `MemorySaver` (and `SqliteSaver` when `aiosqlite`/sqlite available),
      run with a 1 MB unrelated state value, read the checkpoint tuple's
      pending writes via the checkpointer API, assert serialized bytes
      for each branch write are < 10 % of the full-state baseline.
- [ ] AC-03: with the projected payload, `requires`, `skip_if_exists`,
      pre/post guards, and verification on the sub-node behave
      identically to the full-state run (paired assertions).
- [ ] AC-04: empty `variables` on an `llm` sub-node → full-state
      payload (byte-identical prompt variables to today) and one lint
      warning; `python`, `agent`, `subgraph "*"` sub-nodes → same.
- [ ] AC-05: `pass_keys` on a `python` sub-node → payload = declared ∪
      always-keys; the function receives no other parent keys.
- [ ] AC-06: `pass_keys` naming an undeclared state key fails
      `load_graph_config` with node name, key, and declared keys.
- [ ] AC-07: Jinja prompt using `state[...]`, `{% for k in state %}` or
      a filter over `state` → `decidable=False`, full state, lint warning.
- [ ] AC-08: allowlist witness — a test enumerates every
      `state.get("_…")`/`state["_…"]` read under `yamlgraph/node_factory`,
      `yamlgraph/error_handlers.py`, `yamlgraph/utils/guard_runtime.py`
      and fails if a key is read that is not in the always-keys set.
- [ ] AC-09: order and `_map_index` attribution unchanged; FR-944 chained
      maps still receive zero-based indices; `flatten_output` unchanged.
- [ ] AC-10: `examples/demos/map`, `examples/demos/python-map`,
      `examples/book_reviewer`, `examples/icpc-2-rfe`, `examples/cwe-classifier`
      compile and their existing tests pass with no YAML change.
- [ ] AC-11: one new CAP-11 requirement (branch payload contract);
      every new test tagged `@pytest.mark.req`; `python scripts/req_coverage.py --strict` green.
- [ ] AC-12: RED and GREEN separate commits; RED fails on payload
      contents, not on import or fixture.
- [ ] AC-13: `reference/map-nodes.md` documents `pass_keys`, the
      derivation table above, the safe default, and the lint warning;
      one changelog fragment; one diary reflection.
- [ ] AC-14: diff contains none of: overflow/`max_items` changes
      (FR-939), timeout/executor changes (FR-956), retry changes
      (FR-957), durability/Store/cache/chunking.

## Alternatives Considered

Dispositioned in [FR-955.research.md](FR-955.research.md): mandatory
`input_mapping` with empty default (rejected — breaks every existing
map graph; subtractionist dissent preserved as the lint posture),
Step-Functions-style edge path filters as a second surface (rejected —
duplicates the fact the sub-node config already states), a YAML
projection node ahead of the map (rejected — cannot change what `Send`
spreads), `add_node(input_schema=…)` (rejected — narrows the view, not
the persisted write), deferring to durable map D (rejected — inputs, not
results; cost is paid today).

## Related

- `yamlgraph/compile/map_compiler.py:255-268,335-366`
- `yamlgraph/utils/expressions.py:241-265`, `yamlgraph/executor_base.py:86-117`
- `yamlgraph/error_handlers.py:183-199`, `yamlgraph/utils/guard_runtime.py`
- `capabilities/CAP-11-subgraph-map.yaml`
- `docs/plan-web-toolkit.md` — audit item 1, component D sequencing
- `docs/2026-09-02-brainstorm-business-use-cases.md` §5.2

### Questions for the human (as options, or 'none')

1. Lint level for non-projectable map nodes without `pass_keys`:
   **warning** (recommended — demos keep passing) vs error under
   `graph run --gate`. Evidence: judgement R-3 asks for "full-state
   pass-through with a lint warning".
