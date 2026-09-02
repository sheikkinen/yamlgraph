# Judgement: FR-955 Map Branch Input Projection — `Send` carries only what the branch reads

**Verdict:** APPROVED WITH REVISIONS — the projection boundary and full-state fallback are sound, but authority activates only after R-1 through R-7 are folded into the FR and this advisory draft is human-reviewed.

**Reviewed against:** `feature-requests/FR-955-map-branch-input-projection.md`; `feature-requests/FR-955.research.md`; `feature-requests/FR-936-map-node-hardening.md`; `feature-requests/FR-936-map-node-hardening.judgement.md`; `feature-requests/FR-939-map-overflow-policy.md`; `feature-requests/052-map-output-flattening.md`; `feature-requests/FR-467-conditional-edge-to-map-node.md`; `feature-requests/030-map-concurrency-control.md`; `yamlgraph/compile/map_compiler.py`; `yamlgraph/compile/graph_loader.py`; `yamlgraph/models/node_schema.py`; `yamlgraph/models/graph_schema.py`; `yamlgraph/models/state_builder.py`; `yamlgraph/models/state_codegen.py`; `yamlgraph/utils/expressions.py`; `yamlgraph/executor_base.py`; `yamlgraph/error_handlers.py`; `yamlgraph/utils/guard_runtime.py`; `yamlgraph/verification.py`; `yamlgraph/node_factory/llm_nodes.py`; `yamlgraph/node_factory/tool_nodes.py`; `yamlgraph/node_factory/subgraph_nodes.py`; `yamlgraph/tools/python_tool.py`; `yamlgraph/linter/checks_prompts.py`; `yamlgraph/linter/patterns/map.py`; `capabilities/CAP-11-subgraph-map.yaml`; `ARCHITECTURE.md`; `pyproject.toml`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The defect and boundary are real. Current fan-out sends `{**state, item_var: item, "_map_index": i}` to every branch (`yamlgraph/compile/map_compiler.py:363-366`), while the generated graph state includes infrastructure, common-input, custom, data-file, and node-derived fields (`yamlgraph/models/state_builder.py:185-207`). Reducing the actual `Send.arg` therefore attacks the persisted branch-input shape at its source rather than hiding the cost downstream.

The safe-default rule is correct: a key may be dropped only when all reads are statically established; otherwise the branch retains full state unless the author supplies an explicit contract (`feature-requests/FR-955-map-branch-input-projection.md:130-142`). This honors the parent judgement's D-1 fence (`feature-requests/FR-936-map-node-hardening.judgement.md:27-37,149-151,183-184`) and preserves the existing empty-`variables` behavior, which passes every non-internal, non-`None` state value to LLM/router prompts (`yamlgraph/utils/expressions.py:241-269`).

The research record is substantive rather than shape-only: it compares six mechanisms, preserves the mandatory-declaration dissent, dispositions the existing subgraph mapping and projection-node alternatives, and answers `is_this_a_graph` at the fan-out boundary (`feature-requests/FR-955.research.md:28-60`). Prior map concerns are also separated correctly: output flattening changes branch results, conditional-to-map changes routing, FR-939 owns overflow, and FR-030 concerns concurrency rather than payload contents.

| Rubric criterion | Finding |
|---|---|
| Scope | One concern is isolated: map branch input contents. Overflow, timeout, retry, durability, scheduling, caching, and result shaping are fenced out (`feature-requests/FR-955-map-branch-input-projection.md:193-196`). |
| Consistency | The safe fallback is consistent, but validation against only the explicit `state:` section contradicts the repository's generated-state contract, and the unresolved lint-level question contradicts the parent judgement's required warning posture. Revisions are required. |
| Measurability | Exact `Send.arg` assertions and paired behavior tests are mechanical. The proposed completed-checkpoint `pending_writes` read does not guarantee that a non-empty branch write is being measured; the witness must be tightened. |
| Feasibility | Pydantic, Jinja2 ASTs, map lint patterns, and `Send` are already present. The static analysis is feasible, but it must cover actual execution readers and be extracted from the already-large compiler rather than added as a second linter implementation. |
| Architecture alignment | Compile-time projection at the existing fan-out boundary follows CAP-11 and the repository's boundary-normalization law. A shared pure projection module is required to keep compiler and linter decisions identical. |
| Single responsibility | The proposal has one operational contract and one warning that exposes fallback under that same contract. No split is warranted. |
| Strategic classification | **Framework primitive**: current SQLite-checkpointed map users and the fi-catalog consumer provide 3+ use cases, and no existing abstraction projects the actual `Send` branch input. This corrects the existing map primitive rather than adding a second node type. |
| Testability | RED tests can assert exact payloads, static/dynamic classification, unchanged execution, schema rejection, lint output, and serialized branch-write size once the witness and consumer matrix are revised. |

## Required revisions

### R-1: Validate `pass_keys` against the effective generated state contract

Replace “declared in the graph's `state:` section” at `feature-requests/FR-955-map-branch-input-projection.md:103-105` with the effective graph-state field set used by `build_state_class`: base fields, common inputs, explicit `state:`, `data_files`, top-level node `state_key`/`parsed_key`, map `collect`, and generated node-type fields (`yamlgraph/models/state_builder.py:185-207,220-268`). Keep `pass_keys` on the outer map node. Perform this node/graph cross-field validation after graph expansion and schema validation, and make the error name the map node, each unknown key, and the sorted effective field set. Add witnesses for an explicit state key, a prior node's `state_key`, a `data_files` key, a built-in field, and an unknown key.

### R-2: Replace the partial reader table with an executable consumer contract

Fold a per-sub-node matrix into the FR that names every state-reading configuration path and classifies it as statically derivable or dynamic. At minimum, correct these omissions:

- LLM/router `model`, `provider`, and fallback provider may be full-string state references (`yamlgraph/node_factory/llm_nodes.py:331-356`); verification questions interpolate parent-state placeholders (`yamlgraph/verification.py:94-101`); all rendered `user`, scalar/list `system`, and `system_segments[*].content` templates receive `state` (`yamlgraph/executor_base.py:203-270`).
- `tool_call` reads `task` even when `tool` and `args` are otherwise static, and that value changes the returned envelope's `task_id` (`yamlgraph/node_factory/tool_nodes.py:14-26,99-127`). Either derive `task` unconditionally for this type or prove a narrower behavior-preserving rule.
- `subgraph` is statically projectable only for invoke mode with an explicit mapping and no dynamic relay read. Direct mode shares state, `"auto"`/`"*"` copy or expose all state, and relay execution reads generated resume/payload fields (`yamlgraph/node_factory/subgraph_nodes.py:30-43,249-294`); those cases are dynamic unless their complete contract is explicitly declared.
- Error/skip machinery and each supported sub-node implementation must be included even when the key is not underscore-prefixed. Do not retain AC-08's source regex as proof of completeness: it misses indirect reads and known keys such as `task`.

Define derived keys as top-level state roots. Nested reads such as `{state.task.args}` derive `task`. For every unsupported syntax or unresolved prompt, classify the whole branch as undecidable; never return a partial “decidable” set.

### R-3: Make Jinja and expression classification precise

State that all executable prompt segments are parsed with one shared Jinja2 AST classifier. A chain rooted at a static attribute such as `state.customer.locale` derives the top-level key `customer`, including when that value is passed through a filter. Direct use of the root `state`, computed subscripts/attributes, iteration over `state`, aliasing the whole mapping, or any AST form whose top-level root cannot be proven sets `decidable=False`. Revise AC-07 so “a filter over `state`” means the whole mapping, not a filter applied to a statically rooted attribute.

For `{state...}` expressions, cover every syntax accepted by `resolve_template`/`resolve_state_expression`, including embedded references and both operands of supported arithmetic/list/dict forms (`yamlgraph/utils/expressions.py:55-236`). The static extractor must either return every top-level root or mark the expression undecidable; an extractor that understands only the simple full-string form is forbidden.

### R-4: Single-source projection analysis outside `map_compiler.py`

Replace the claim that all production logic lives in `map_compiler.py`, `node_schema.py`, and one linter check (`feature-requests/FR-955-map-branch-input-projection.md:81-82`). Add a pure leaf module such as `yamlgraph/compile/map_projection.py` containing the typed `BranchKeys` result and derivation logic. Both `map_compiler.py` and `yamlgraph/linter/patterns/map.py` must consume that result so runtime projection and warning reasons cannot drift. Keep prompt loading/path resolution at the established graph/prompt boundary and pass resolved prompt content into the pure analysis. Do not duplicate the Jinja or expression classifier in the linter.

This structure is required because `map_compiler.py` is already near the repository's 450-line ceiling and the proposal adds a cross-cutting static-analysis concern. The authorized schema surfaces are `node_schema.py` for the typed field and graph-level validation code for the effective-state check; tests, CAP-11, reference documentation, changelog, diary, and FR status are delivery artifacts, not exceptions to the scope table.

### R-5: Define exact key-set and declaration semantics

Freeze the payload equation as:

`({derived roots} union {declared pass_keys} union {per-type execution keys}) intersect present parent-state keys`, followed by unconditional injection/overwrite of the item variable and `_map_index`.

Do not synthesize absent parent keys. Define `pass_keys: []` as an explicit dynamic-reader contract that passes no optional parent keys. Include the sub-node `state_key` only when machinery such as `skip_if_exists` can read it; include `_loop_counts` only for sub-node types that read it. `_map_index` remains unconditional because reducer wrapping and error attribution consume it. Every additional internal key must be justified by a cited runtime read and a behavioral witness, rather than placed in a global allowlist for convenience.

### R-6: Measure a real serialized branch input

Replace AC-02's “run, then read the checkpoint tuple's pending writes” procedure with a deterministic witness that proves the captured record is an actual branch input before comparing sizes. Use an instrumented checkpointer or a deliberately paused/interrupted superstep to capture the relevant write, assert that the capture is non-empty and contains the expected item variable and `_map_index`, then compare the same graph/input under full-state fallback and projected declaration. Run this witness for both `MemorySaver` and `SqliteSaver`; SQLite checkpoint support is a direct dependency (`pyproject.toml:31`), not an optional “when available” branch. Assert exact absence of the 1 MB field and serialized projected bytes below 10% of the full-state baseline for every captured branch.

### R-7: Resolve the lint decision and replace the acceptance contract

Delete the open lint-level question at `feature-requests/FR-955-map-branch-input-projection.md:217-222`. The governing parent already freezes full-state pass-through **with a warning**, so this FR does not authorize a new `graph run --gate` error. Allocate a collision-free warning code before GREEN, require exactly one warning per non-projectable map node, and include stable map-node identity plus all deterministic reason codes in its assertion. Fold the revised acceptance criteria and enforcement conditions below into FR-955 before implementation; record status as judged with authority pending human review.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Typed outer-map `pass_keys` field and effective-state validation in `yamlgraph/models/node_schema.py` plus the established graph-level validation surface |
| D-2 | Pure `BranchKeys` and static consumer analysis in a leaf projection module |
| D-3 | `Send.arg` projection in `yamlgraph/compile/map_compiler.py`, preserving full-state fallback |
| D-4 | One map-pattern warning using the same projection analysis and reason codes |
| D-5 | Focused RED/GREEN unit and checkpointer witnesses for payload, behavior, schema, Jinja/expression classification, and lint |
| D-6 | One CAP-11 requirement, `reference/map-nodes.md`, one changelog fragment, one diary reflection, and FR-955 implementation record |

Not authorized: overflow or `max_items` behavior; timeout/executor lifecycle; retry policy; map concurrency, batching, chunking, durability, Store, caching, checkpoint format, or checkpointer implementation changes; map result/flattening semantics; routing semantics; provider-wide behavior; changes to graph or prompt artifacts; mandatory declarations for existing maps; or promotion of the fallback warning to a gate/error.

## Revised acceptance criteria

- [ ] AC-01: RED inspects every `Send.arg` for an explicit-variable LLM map and asserts the exact present-parent key set plus injected item variable and zero-based `_map_index`; an unrelated 1 MB value is absent.
- [ ] AC-02: RED captures a demonstrably real branch input through both `MemorySaver` and `SqliteSaver`, asserts the capture is non-empty and branch-identifiable, and proves every projected serialized branch is below 10% of the same graph/input's full-state-fallback baseline.
- [ ] AC-03: A table-driven test covers every supported map sub-node type and every consumer path frozen by R-2, asserting derived top-level roots and `decidable`/reason results.
- [ ] AC-04: Paired projected/full-state executions produce equal result, order, `_map_index`, error shape, `requires`, `skip_if_exists`, pre/post guard, verification, routing, and `flatten_output` behavior.
- [ ] AC-05: Empty variables on LLM/router, Python without `pass_keys`, agent without `pass_keys`, direct/auto/star/dynamic-relay subgraph cases, and every unsupported expression/Jinja form retain the complete parent state and emit exactly one warning.
- [ ] AC-06: `pass_keys` is a union with all statically derived and per-type execution keys; `pass_keys: []` is an explicit contract; absent optional parent keys are not synthesized.
- [ ] AC-07: Effective-state validation accepts explicit state, built-in, data-file, prior-node output, parsed, and map-collect fields, and rejects unknown keys with map name, unknown keys, and sorted effective fields.
- [ ] AC-08: LLM/router model, provider, fallback provider, verification placeholders, and every rendered prompt segment have direct derivation and behavior witnesses.
- [ ] AC-09: Static `tool_call` preserves `task_id` envelope behavior; dynamic tool/args cases fall back unless explicitly declared.
- [ ] AC-10: Invoke subgraphs with explicit input mappings derive parent roots; direct, auto, star, and unresolved relay cases are dynamic and preserve full-state behavior.
- [ ] AC-11: Jinja static attribute chains, filters on static attributes, direct root use, computed subscripts, iteration, aliasing, and malformed/unresolved prompts are classified exactly as R-3 requires.
- [ ] AC-12: Every expression form accepted by the runtime resolver either yields all top-level roots or marks the branch undecidable; no partial set is used for projection.
- [ ] AC-13: The compiler and map linter import the same pure derivation function; no second regex/AST classifier or duplicated reason policy exists.
- [ ] AC-14: Existing map examples named by the FR load/compile unchanged, existing focused map tests pass, order remains zero-based, and FR-944 chained-map behavior remains unchanged.
- [ ] AC-15: One new CAP-11 requirement covers branch input projection; every new test has `@pytest.mark.req`, and `python scripts/req_coverage.py --strict` passes.
- [ ] AC-16: RED and GREEN are separate commits; RED fails on payload/classification/serialization assertions rather than imports, unavailable dependencies, empty captures, or fixtures.
- [ ] AC-17: `reference/map-nodes.md` documents `pass_keys`, effective-state validation, the complete consumer matrix, declaration semantics, safe fallback, and warning; one changelog fragment and one diary reflection are present.
- [ ] AC-18: The diff contains no overflow, timeout, retry, concurrency, durability, Store, cache, chunking, checkpoint-format, result-shape, routing, provider-wide, graph-artifact, or prompt-artifact changes.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not drop a parent key unless the shared analyzer proves every runtime read or the author explicitly assumes the contract with `pass_keys`; every undecidable undeclared branch retains full state. | GATE |
| C-2 | Do not validate `pass_keys` against only the explicit `state:` block; use the effective generated graph-state field set. | GATE |
| C-3 | Do not implement separate compiler and linter derivation logic, a partial regex, or an analyzer that returns a projected subset after encountering unsupported syntax. | GATE |
| C-4 | Do not accept a serialized-size witness unless it proves a non-empty captured record is the actual branch input and exercises both direct checkpointer dependencies. | GATE |
| C-5 | Do not omit non-internal reads such as `task`, dynamic model/provider/fallback references, verification placeholders, or subgraph relay/direct behavior from the consumer matrix. | GATE |
| C-6 | Do not promote the fallback warning to an error or require declarations in existing map YAML under this FR. | GATE |
| C-7 | Do not cross the D-1 child fence into overflow, timeout, retry, scheduling, durability, result, routing, provider, or checkpoint implementation work. | GATE |
| C-8 | Treat this draft as advisory; no implementation authority exists until R-1 through R-7 are folded into FR-955 and a human reviews the judgement. | GATE |

Authority granted: after the required revisions are folded and this judgement is human-reviewed, implement only D-1 through D-6 under the exact projection, fallback, warning, and witness contracts above.
