# Feature Request: Map Branch Input Projection — `Send` carries only what the branch reads

**Priority:** HIGH
**Type:** Enhancement
**Status:** Judged — APPROVED WITH REVISIONS
([FR-955-map-branch-input-projection.judgement.md](FR-955-map-branch-input-projection.judgement.md),
2026-09-02, sole route). **R-1–R-7 folded 2026-09-02** into the body
below; the judgement's revised acceptance criteria AC-01–AC-18 and
gates C-1–C-8 are the frozen contract. Authority activates on human
review of the judgement (C-8).
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
and the per-type execution keys) instead of a copy of the whole parent
state. Sub-nodes whose reads cannot be decided statically keep full
state, and the linter says so with one warning per map node.

## Value Statement

Every checkpointed map graph writes branch inputs proportional to what
the branch uses, not to the size of the parent state; the census-scale
consumer becomes buildable on the map node rather than around it.

## Problem

`map_edge` dispatches `Send(sub_node_name, {**state, item_var: item,
"_map_index": i})` (`yamlgraph/compile/map_compiler.py:363-366`). With a
checkpointer attached, LangGraph persists each branch's input as a
pending write, so every branch write carries the entire parent state —
and the generated state includes infrastructure, common-input, custom,
data-file and node-derived fields (`yamlgraph/models/state_builder.py:185-207`).
The compiler passes everything because it does not know what the
sub-node needs, and that set is not derivable from prompt text alone:
empty `variables` passes every non-`_`, non-None key
(`yamlgraph/utils/expressions.py:262-265`); Jinja receives the `state`
object directly (`yamlgraph/executor_base.py:115-117`); `requires`,
`skip_if_exists`, guards, model/provider references, verification
placeholders, `tool_call`'s `task`, and subgraph relay fields all read
parent state at execution time (matrix in §3).

The judgement's rule (C-1): drop a key only when the shared analyzer
proves every runtime read, or the author explicitly assumes the contract
with `pass_keys`. Anything else is a correctness regression disguised as
an optimisation.

## Ideal Result

A map branch receives exactly the keys it can read — derived where the
sub-node's configuration makes that decidable, declared by the author
where it does not — and a graph author can see, before running, which
map nodes still fall back to full state and why. Results, order, and
error shapes are byte-identical to today; only the payload shrinks.

## Proposed Solution

Delivery surface is the judgement's D-1–D-6 table (§Scope). The
production seams are `yamlgraph/models/node_schema.py` (typed field),
the established graph-level validation surface (effective-state check),
a new pure leaf module `yamlgraph/compile/map_projection.py`
(analysis), `yamlgraph/compile/map_compiler.py` (`Send.arg` projection),
and `yamlgraph/linter/patterns/map.py` (the warning). No other
production file changes.

### 1. `pass_keys` on the outer map node, validated against the effective state (R-1)

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

`NodeConfig.pass_keys: list[str] | None`, map nodes only. Validation
runs **after graph expansion and schema validation** against the
**effective generated state field set** used by `build_state_class`:
base/infrastructure fields, common inputs, the explicit `state:`
section, `data_files` keys, top-level node `state_key`/`parsed_key`
fields, map `collect` keys, and generated node-type fields
(`yamlgraph/models/state_builder.py:185-207,220-268`). An unknown key
fails load with the map node name, every unknown key, and the sorted
effective field set. Witnesses cover an explicit state key, a prior
node's `state_key`, a `data_files` key, a built-in field, and an
unknown key.

### 2. One pure analyzer, consumed by compiler and linter (R-4)

`yamlgraph/compile/map_projection.py` (leaf module, no compiler or
linter imports) exposes:

```python
@dataclass(frozen=True)
class BranchKeys:
    keys: frozenset[str]          # top-level parent-state roots
    decidable: bool
    reasons: tuple[ReasonCode, ...]  # deterministic, sorted

def derive_branch_keys(
    sub_node_config: dict, sub_node_type: str,
    prompt_segments: Sequence[str], pass_keys: list[str] | None,
) -> BranchKeys: ...
```

Prompt loading and path resolution stay at the graph/prompt boundary;
resolved prompt content is passed in. `map_compiler.py` and
`linter/patterns/map.py` both call `derive_branch_keys`; no second
regex or AST classifier and no duplicated reason policy may exist
(C-3). `map_compiler.py` is near the 450-line ceiling, which is why the
analysis lives outside it.

### 3. Consumer contract — executable matrix (R-2)

Derived keys are **top-level state roots**: `{state.task.args}` derives
`task`. For any unsupported syntax or unresolved prompt the **whole
branch** is undecidable — a partial "decidable" set is never returned.

| Sub-node type | State-reading path | Where it reads | Classification |
|---|---|---|---|
| `llm`, `router` | `variables` templates | `expressions.py:55-236` (every accepted syntax) | roots, or undecidable if any syntax is unsupported |
| `llm`, `router` | empty `variables` | `expressions.py:262-265` pass-everything | **undecidable** |
| `llm`, `router` | rendered `user`, scalar/list `system`, `system_segments[*].content` | `executor_base.py:203-270` receive `state` | Jinja AST classifier (§4) |
| `llm`, `router` | `model`, `provider`, fallback provider as full-string state refs | `node_factory/llm_nodes.py:331-356` | roots, or undecidable |
| `llm`, `router` | verification question placeholders | `yamlgraph/verification.py:94-101` | roots |
| all | `requires` | `error_handlers.py:183-199` | roots |
| all with `state_key` | `skip_if_exists` | reads own `state_key` | execution key when machinery can read it |
| all | guards pre/post expressions | `utils/guard_runtime.py:87,162,180` | roots, or undecidable |
| `llm`, `router` | loop protection | `llm_nodes.py:303` reads `_loop_counts` | execution key (these types only) |
| `llm`, `router` | skip/error machinery | `error_handlers.py:249` reads `errors` | execution key (these types only) |
| `router` | routing | reads the node *result*, not parent state | no parent key |
| `tool_call` | `task` | `node_factory/tool_nodes.py:14-26,99-127` — read even when `tool`/`args` are static; changes the envelope's `task_id` | **`task` derived unconditionally** |
| `tool_call` | `tool`, `args` literal templates | `tool_nodes.py:99-127` | roots; state-resolved `tool`/`args` → undecidable |
| `python` | function receives effective state | `tools/python_tool.py:299-311` | **undecidable** unless `pass_keys` |
| `agent` | tools read state dynamically | `tools/agent.py` | **undecidable** unless `pass_keys` |
| `subgraph` | invoke mode, explicit dict `input_mapping`, no dynamic relay read | `subgraph_nodes.py:30-43` | parent roots from the mapping |
| `subgraph` | direct mode (shared state), `"auto"`, `"*"`, relay resume/payload reads | `subgraph_nodes.py:30-43,249-294` | **undecidable** |
| framework | `_map_index` | `map_compiler.py:147,184` reducer wrapping and error attribution | **unconditional** |

Completeness is proven by the table-driven witness (AC-03), not by a
source regex; a regex misses indirect reads and non-underscore keys
such as `task` (judgement R-2).

### 4. Jinja and expression classification (R-3)

One shared Jinja2 AST classifier parses **every** executable prompt
segment. A `Getattr` chain rooted at `Name("state")` — e.g.
`state.customer.locale`, including when passed through a filter —
derives the root `customer`. Direct use of the root `state`, computed
subscripts or attributes, iteration over `state`, aliasing the whole
mapping (`{% set s = state %}`), or any AST form whose top-level root
cannot be proven sets `decidable=False`. "A filter over `state`" means
the whole mapping, not a filter applied to a statically rooted
attribute.

For `{state...}` expressions the extractor covers every syntax accepted
by `resolve_template`/`resolve_state_expression` — embedded references
and both operands of the supported arithmetic, list and dict forms
(`expressions.py:55-236`) — and either returns every top-level root or
marks the branch undecidable. An extractor that understands only the
simple full-string form is forbidden (C-3).

### 5. Payload equation and declaration semantics (R-5)

```
payload = ({derived roots} ∪ {declared pass_keys} ∪ {per-type execution keys})
          ∩ {keys present in the parent state}
payload[item_var] = item          # unconditional overwrite
payload["_map_index"] = i         # unconditional overwrite
```

- Absent parent keys are never synthesized.
- `pass_keys: []` is an explicit dynamic-reader contract: the branch
  receives no optional parent keys, only the execution keys and the
  injected values.
- The sub-node `state_key` is included only when `skip_if_exists`
  machinery can read it; `_loop_counts` and `errors` only for the
  sub-node types that read them (§3); `_map_index` always.
- Any further internal key requires a cited runtime read and a
  behavioural witness — there is no convenience allowlist.

### 6. Fallback and warning (R-7)

A branch that is undecidable and has no `pass_keys` receives the
complete parent state, exactly as today, and the map-pattern linter
emits **exactly one warning per such map node** carrying the stable
map-node identity and all deterministic reason codes from
`BranchKeys.reasons`, with the fix "declare `pass_keys` or make the
reads static". The warning code is allocated collision-free before
GREEN. It is a warning, never a `graph run --gate` error, and existing
map YAML is never required to add a declaration (C-6).

### 7. Serialized branch-input witness (R-6)

The size witness must prove the captured record **is** a branch input
before comparing sizes: capture the write with an instrumented
checkpointer or a deliberately paused/interrupted superstep, assert the
capture is non-empty and contains the item variable and `_map_index`,
then compare the same graph and input under full-state fallback and
under a projecting declaration. Run for **both** `MemorySaver` and
`SqliteSaver` — `langgraph-checkpoint-sqlite` is a direct dependency
(`pyproject.toml:31`), not optional. Assert exact absence of the 1 MB
field and projected serialized bytes below 10 % of the full-state
baseline for every captured branch.

## Acceptance Criteria

Frozen by the judgement (R-7); the enforcer satisfies this list.

- [ ] AC-01: RED inspects every `Send.arg` for an explicit-variable LLM map and asserts the exact present-parent key set plus injected item variable and zero-based `_map_index`; an unrelated 1 MB value is absent.
- [ ] AC-02: RED captures a demonstrably real branch input through both `MemorySaver` and `SqliteSaver`, asserts the capture is non-empty and branch-identifiable, and proves every projected serialized branch is below 10% of the same graph/input's full-state-fallback baseline.
- [ ] AC-03: A table-driven test covers every supported map sub-node type and every consumer path frozen by §3, asserting derived top-level roots and `decidable`/reason results.
- [ ] AC-04: Paired projected/full-state executions produce equal result, order, `_map_index`, error shape, `requires`, `skip_if_exists`, pre/post guard, verification, routing, and `flatten_output` behavior.
- [ ] AC-05: Empty variables on LLM/router, Python without `pass_keys`, agent without `pass_keys`, direct/auto/star/dynamic-relay subgraph cases, and every unsupported expression/Jinja form retain the complete parent state and emit exactly one warning.
- [ ] AC-06: `pass_keys` is a union with all statically derived and per-type execution keys; `pass_keys: []` is an explicit contract; absent optional parent keys are not synthesized.
- [ ] AC-07: Effective-state validation accepts explicit state, built-in, data-file, prior-node output, parsed, and map-collect fields, and rejects unknown keys with map name, unknown keys, and sorted effective fields.
- [ ] AC-08: LLM/router model, provider, fallback provider, verification placeholders, and every rendered prompt segment have direct derivation and behavior witnesses.
- [ ] AC-09: Static `tool_call` preserves `task_id` envelope behavior; dynamic tool/args cases fall back unless explicitly declared.
- [ ] AC-10: Invoke subgraphs with explicit input mappings derive parent roots; direct, auto, star, and unresolved relay cases are dynamic and preserve full-state behavior.
- [ ] AC-11: Jinja static attribute chains, filters on static attributes, direct root use, computed subscripts, iteration, aliasing, and malformed/unresolved prompts are classified exactly as §4 requires.
- [ ] AC-12: Every expression form accepted by the runtime resolver either yields all top-level roots or marks the branch undecidable; no partial set is used for projection.
- [ ] AC-13: The compiler and map linter import the same pure derivation function; no second regex/AST classifier or duplicated reason policy exists.
- [ ] AC-14: Existing map examples named by the FR load/compile unchanged, existing focused map tests pass, order remains zero-based, and FR-944 chained-map behavior remains unchanged.
- [ ] AC-15: One new CAP-11 requirement covers branch input projection; every new test has `@pytest.mark.req`, and `python scripts/req_coverage.py --strict` passes.
- [ ] AC-16: RED and GREEN are separate commits; RED fails on payload/classification/serialization assertions rather than imports, unavailable dependencies, empty captures, or fixtures.
- [ ] AC-17: `reference/map-nodes.md` documents `pass_keys`, effective-state validation, the complete consumer matrix, declaration semantics, safe fallback, and warning; one changelog fragment and one diary reflection are present.
- [ ] AC-18: The diff contains no overflow, timeout, retry, concurrency, durability, Store, cache, chunking, checkpoint-format, result-shape, routing, provider-wide, graph-artifact, or prompt-artifact changes.

## Scope (frozen by the judgement)

| Deliverable | Surface |
|---|---|
| D-1 | Typed outer-map `pass_keys` field and effective-state validation in `yamlgraph/models/node_schema.py` plus the established graph-level validation surface |
| D-2 | Pure `BranchKeys` and static consumer analysis in `yamlgraph/compile/map_projection.py` |
| D-3 | `Send.arg` projection in `yamlgraph/compile/map_compiler.py`, preserving full-state fallback |
| D-4 | One map-pattern warning in `yamlgraph/linter/patterns/map.py` using the same analysis and reason codes |
| D-5 | Focused RED/GREEN unit and checkpointer witnesses for payload, behaviour, schema, Jinja/expression classification, and lint |
| D-6 | One CAP-11 requirement, `reference/map-nodes.md`, one changelog fragment, one diary reflection, and this FR's implementation record |

Not authorized: overflow or `max_items` behaviour (FR-939); timeout/
executor lifecycle (FR-956); retry policy (FR-957); map concurrency,
batching, chunking, durability, Store, caching, checkpoint format, or
checkpointer implementation changes; map result/flattening semantics;
routing semantics; provider-wide behaviour; changes to graph or prompt
artifacts; mandatory declarations for existing maps; promotion of the
fallback warning to a gate/error.

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

- [FR-955-map-branch-input-projection.judgement.md](FR-955-map-branch-input-projection.judgement.md)
- `yamlgraph/compile/map_compiler.py:255-268,335-366`
- `yamlgraph/models/state_builder.py:185-207,220-268`
- `yamlgraph/utils/expressions.py:55-269`, `yamlgraph/executor_base.py:86-117,203-270`
- `yamlgraph/error_handlers.py:183-199,249`, `yamlgraph/utils/guard_runtime.py`, `yamlgraph/verification.py:94-101`
- `yamlgraph/node_factory/llm_nodes.py:303,331-356`, `yamlgraph/node_factory/tool_nodes.py:14-26,99-127`, `yamlgraph/node_factory/subgraph_nodes.py:30-43,249-294`
- `capabilities/CAP-11-subgraph-map.yaml`
- `docs/plan-web-toolkit.md` — audit item 1, component D sequencing
- `docs/2026-09-02-brainstorm-business-use-cases.md` §5.2

## Judgement (2026-09-02)

**Verdict:** APPROVED WITH REVISIONS — see
[FR-955-map-branch-input-projection.judgement.md](FR-955-map-branch-input-projection.judgement.md)
for the full rubric, R-1–R-7, AC-01–AC-18 and C-1–C-8. R-1–R-7 are
folded above (§1 effective-state validation; §3 consumer matrix; §4
classifier; §2 leaf module; §5 payload equation; §7 captured-write
witness; §6 warning-not-gate). Authority activates on human review.

### Questions for the human (as options, or 'none')

None. The lint-level question was resolved by the judgement (R-7):
warning only, never a gate.
