# Judgement: FR-936 Map Node Hardening — Scale-Correct Send Fan-out

**Verdict:** SPLIT — payload minimization, overflow semantics, timeout resource control, and native retry are orthogonal contracts with independent failure modes; no implementation authority exists until each replacement FR is researched, judged, and approved.

**Prior art:** FR-774/FR-775 (book-summary scale hardening/loop redesign) and FR-776 (vision fallback) are application-layer map *consumers*, not map-node contract changes — no overlap with these deliverables. FR-807 hardens route evidence records, unrelated to Send fan-out. The genuine precedents for this scope are FR-027 (truncate-and-warn overflow contract, explicitly superseded by D-2) and FR-069 (timeout wrapper limitation, inherited by D-3), both dispositioned in the body below.

**Reviewed against:** `feature-requests/FR-936-map-node-hardening.md`; `docs/plan-web-toolkit.md`; `yamlgraph/compile/map_compiler.py`; `yamlgraph/models/node_schema.py`; `yamlgraph/node_factory/llm_nodes.py`; `yamlgraph/node_factory/llm_execution.py`; `yamlgraph/executor_base.py`; `yamlgraph/utils/expressions.py`; `yamlgraph/linter/checks_prompts.py`; `capabilities/CAP-11-subgraph-map.yaml`; `feature-requests/027-execution-safety-guards.md`; `feature-requests/069-map-node-timeout.md`; `feature-requests/052-map-output-flattening.md`; `feature-requests/FR-467-conditional-edge-to-map-node.md`; `tests/unit/test_compile_graph_map.py`; `tests/unit/test_fr027_execution_safety.py`; `tests/unit/test_map_node_timeout.py`; `pyproject.toml`; installed LangGraph 1.2 `StateGraph.add_node` and `RetryPolicy` signatures declared by `pyproject.toml:30`; LangGraph Graph API and Python reference cited by the FR; `.github/copilot-instructions.md`; `CLAUDE.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The core defects are real. `map_edge` currently warns, slices, and returns success when the input exceeds the cap (`yamlgraph/compile/map_compiler.py:350-365`), and every `Send` receives a shallow copy of the complete state mapping (`yamlgraph/compile/map_compiler.py:363-365`). The checkpoint-serialization concern is credible even though `{**state}` does not deep-copy values. The existing timeout wrapper also abandons running work after `Future.result` times out (`yamlgraph/compile/map_compiler.py:93-113`), matching the limitation already recorded by FR-069 (`feature-requests/069-map-node-timeout.md:135-137`).

The proposal correctly keeps durability, chunked scheduling, `CachePolicy`, Store-backed results, and progress logging outside this change (`feature-requests/FR-936-map-node-hardening.md:25-26,67-69`). That boundary aligns with the cited research, which identifies unbounded one-superstep scheduling and result placement as the remaining durable-map gaps (`docs/plan-web-toolkit.md:155-171`). It also conforms to the existing CAP-11 `Send`/reducer architecture rather than inventing a second node type (`capabilities/CAP-11-subgraph-map.yaml:1-16`).

Several criteria are directly testable: overflow can be asserted before branch execution, exact `Send` payload keys can be inspected, and retry attempt counts can be observed. Existing witnesses already isolate overflow and timeout behavior (`tests/unit/test_fr027_execution_safety.py:33-38`; `tests/unit/test_map_node_timeout.py:90-96`). Strategically, however, this is not one new framework primitive: it is four changes to an existing primitive, driven by the fi-catalog case and current map users (`feature-requests/FR-936-map-node-hardening.md:8-12,30-32`).

## Required revisions

### R-1: Split the four contracts

Replace FR-936 with four independently researched FRs: (1) map branch input projection, (2) overflow policy, (3) timeout cancellation/resource ownership, and (4) native retry integration. Each changes a different public or operational contract and can ship, fail, and be reverted independently. The current grouping violates the single-responsibility gate (`.github/skills/judge-fr/doctrine.md:49-50`), despite sharing `map_compiler.py`.

### R-2: Supply substantive research for each replacement FR

The cited audit enumerates the same four intended changes (`docs/plan-web-toolkit.md:173-190`) but does not compare 4–6 genuine solution classes for each concern, preserve disagreement, or answer `is_this_a_graph` per replacement scope. The alternatives table distributes one alternative across each of four different problems (`feature-requests/FR-936-map-node-hardening.md:152-159`); it is not solution-class research for any one problem. Each replacement FR must carry a committed research record satisfying the prospective FR-890 gate before receiving authority.

### R-3: Define input projection from execution contracts, not prompt text alone

Specify `pass_keys` as a union with statically derived keys; remove the ambiguous “overrides/extends” wording (`feature-requests/FR-936-map-node-hardening.md:89-90`). Enumerate required keys for every supported sub-node type and for node machinery, including `variables`, `requires`, direct Jinja `state` access, guards, verification, routing, `skip_if_exists`, and internal execution fields. Empty `variables` currently means “pass every non-internal state value as prompt variables” (`yamlgraph/utils/expressions.py:241-264`), and Jinja receives the state object directly (`yamlgraph/executor_base.py:83-116`), so prompt-reference scanning alone cannot preserve present semantics.

Python sub-nodes must be classified as dynamically state-reading alongside agent/subgraph cases; the current fallback list omits them. Define safe behavior for every uncomputable case: explicit declared inputs or full-state pass-through with a lint warning. Use Jinja parsing or an existing template-variable extractor rather than adding another partial regex; the current linter helper only recognizes a narrow `{{ state.key }}` shape (`yamlgraph/linter/checks_prompts.py:48-50`).

The payload witness must measure exact payload keys and serialized checkpoint/pending-write size. It must not claim that `{**state}` deep-copies a 1 MB value.

### R-4: Isolate and specify the overflow policy migration

The overflow FR must explicitly supersede FR-027’s deliberate truncate-and-warn contract (`feature-requests/027-execution-safety-guards.md:41-43`) and define both node-level and graph-default behavior. Add a typed `Literal["error", "truncate"]` schema field with `error` as the default, reject invalid values during graph validation, prove the exception occurs before any sub-node call, and preserve truncation only when explicitly selected. Error text must include node name, observed count, and configured cap.

### R-5: Replace the shared-pool timeout design

Do not authorize the bounded shared executor described at `feature-requests/FR-936-map-node-hardening.md:117-124`. A blocking timed-out callable continues occupying its worker; after `pool_size` permanent hangs, later work queues forever. This bounds thread count by converting resource leakage into deterministic starvation and does not satisfy the Ideal Result.

Open the timeout replacement as an investigation-first FR. It must prove the lifecycle from submission through timeout, cancellation/return, executor disposal, and subsequent healthy branch execution. The accepted mechanism must either terminate work at the provider/client boundary or isolate it in a genuinely terminable execution unit. Merely recording the already-observable timeout error is not cancellation.

### R-6: Reconcile native retry with swallowed exceptions

Use LangGraph’s actual `add_node(..., retry_policy=RetryPolicy(...))` keyword, not the FR’s `retry=` spelling (`feature-requests/FR-936-map-node-hardening.md:62-63`). More importantly, define how exceptions reach LangGraph: `wrap_for_reducer` currently catches both timeout and every other exception and converts them to successful state updates (`yamlgraph/compile/map_compiler.py:139-173`), while LLM execution also dispatches errors internally according to `on_error` (`yamlgraph/node_factory/llm_execution.py:82-116`). A `RetryPolicy` attached to that wrapped node cannot observe those failures as proposed.

The retry FR must define one owner for retries, the exact ordering between native retries and final `on_error` disposition, and behavior for each sub-node type. Represent retry configuration with a typed Pydantic model matching supported LangGraph fields. Do not permit arbitrary import strings or callables for `retry_on`; use the native default or a closed declarative allowlist. Tests must cover retryable success, exhausted retry, non-retryable failure, and final `on_error` handling—not only a flaky mock that succeeds on attempt two.

### R-7: Give each split its own traceability and delivery record

Each replacement FR must allocate the minimum new CAP-11 requirement IDs needed for its contract, tag its RED witnesses, update only the relevant map reference section, add its own changelog fragment, and record its own diary reflection. Existing broad “map tests green” and “examples rerun” language (`feature-requests/FR-936-map-node-hardening.md:144-150`) is regression context, not a substitute for concern-specific assertions.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Replacement FR: map branch input projection and `pass_keys` contract |
| D-2 | Replacement FR: `max_items` overflow policy and typed `on_overflow` contract |
| D-3 | Investigation FR: map branch timeout cancellation and resource lifecycle |
| D-4 | Replacement FR: LangGraph `RetryPolicy` integration and exception ownership |
| D-5 | FR-936 updated to record the SPLIT disposition and links to D-1 through D-4 |

No production code, schema, reference documentation, capability requirement, changelog fragment, demo artifact, or test rewrite is authorized by FR-936. Not authorized: durable/resumable map behavior, chunked scheduling, concurrency controls, `CachePolicy`, Store-backed results, checkpoint format changes, progress JSONL, provider-wide timeout refactors without their own judged scope, or changes to non-map retry semantics.

## Revised acceptance criteria

- [ ] AC-01: FR-936 records the SPLIT disposition and identifies four replacement FRs with no overlapping implementation deliverables.
- [ ] AC-02: Each replacement FR has committed, substantive research with 4–6 solution classes, precedent disposition, preserved disagreement, and an explicit `is_this_a_graph` answer.
- [ ] AC-03: The input-projection FR defines exact required-key derivation for every supported sub-node type and every node-level state consumer; uncomputable access uses explicit declaration or full-state pass-through with a lint warning.
- [ ] AC-04: Input-projection RED tests assert exact `Send` payload keys, absence of an unrelated 1 MB state value, successful prompt/guard/verification execution, and reduced serialized checkpoint or pending-write size.
- [ ] AC-05: The overflow FR validates `on_overflow` as `error | truncate`, defaults to `error`, raises before the first sub-node call with node/count/cap in the message, and truncates with a warning only when explicitly configured.
- [ ] AC-06: Overflow tests cover node-level `max_items`, graph-level `max_map_items`, within-cap input, invalid policy values, and the explicit truncate path.
- [ ] AC-07: The timeout investigation reproduces more hangs than the proposed concurrency bound and proves that a later healthy branch still executes within a fixed deadline.
- [ ] AC-08: The timeout solution proves running timed-out work terminates or is isolated and reclaimed; bounded thread count alone does not satisfy this criterion.
- [ ] AC-09: The retry FR maps typed YAML configuration to `add_node(..., retry_policy=...)` and proves that retryable exceptions reach LangGraph.
- [ ] AC-10: Retry tests assert attempt counts for retryable success, exhausted retry, and non-retryable failure, then assert the configured final `on_error` disposition occurs exactly once.
- [ ] AC-11: Each replacement FR adds concern-specific CAP-11 requirement coverage, focused documentation, a changelog fragment, and a diary entry; existing map tests remain green.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement any FR-936 production change before all affected work is assigned to a separately judged replacement FR. | GATE |
| C-2 | Do not drop state keys based solely on prompt-text matching; every execution-time state consumer must be covered or the branch must retain full-state input. | GATE |
| C-3 | Do not accept a timeout mechanism that leaves hung work occupying all capacity or that passes only a thread-count assertion without a post-timeout liveness witness. | GATE |
| C-4 | Do not attach `RetryPolicy` to a wrapper that converts the target exception into a state update before LangGraph can observe it. | GATE |
| C-5 | Do not expose arbitrary Python exception imports/callables through YAML retry configuration. | GATE |
| C-6 | Do not pull durable-map features or non-map timeout/retry refactors into any replacement FR without separate evidence and judgement. | GATE |

Authority granted: none; only the four replacement FRs and the FR-936 split record may be authored, after which each replacement must re-enter judgement independently.


---

## Rejudgement (2026-09-02) — split record update

Rendered by the sole judge route (`scripts/judge.sh` → `yamlgraph graph run .github/skills/judge-fr/adapters/graph.yaml`, copilot CLI backend, model `gpt-5.6-sol`, run_id `01a06295-0578-783f-90ff-a0609feba198`) against the FR-936 split record as updated 2026-09-02. **Advisory until human-reviewed** (NC-412 C-6). Appended rather than prepended so that line references into the original 2026-08-31 judgement (cited by `FR-939-map-overflow-policy.judgement.md`) remain valid.


**Verdict:** SPLIT — the updated record correctly separates four independent map-node contracts, but FR-936 grants no implementation authority and remains incomplete until the three unallocated children are authored and every child independently passes research and judgement.

**Reviewed against:** `feature-requests/FR-936-map-node-hardening.md`; `feature-requests/FR-936-map-node-hardening.judgement.md`; `feature-requests/FR-939-map-overflow-policy.md`; `feature-requests/FR-939-map-overflow-policy.judgement.md`; `feature-requests/069-map-node-timeout.md`; `docs/plan-web-toolkit.md`; `docs/2026-09-02-brainstorm-business-use-cases.md`; `yamlgraph/compile/map_compiler.py`; `yamlgraph/schemas/graph-v1.json`; `reference/patterns.md`; `capabilities/CAP-11-subgraph-map.yaml`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The revised parent record now states the correct disposition up front and withholds implementation authority (`feature-requests/FR-936-map-node-hardening.md:5`). Its four-way partition is real rather than cosmetic: D-1 owns `Send` payload contents, D-2 owns overflow disposition, D-3 owns timeout lifecycle, and D-4 owns retry registration and exception ordering (`feature-requests/FR-936-map-node-hardening.md:32-39`). Those contracts can be implemented, tested, reverted, and fail independently, so the single-responsibility rubric requires SPLIT.

The defects themselves remain evidenced. Current fan-out still slices above the cap and copies the complete state into every `Send` (`yamlgraph/compile/map_compiler.py:351-365`); timeout cleanup still returns without waiting for running work (`yamlgraph/compile/map_compiler.py:112`), matching FR-069's explicit admission that the submitted thread is not cancelled (`feature-requests/069-map-node-timeout.md:135-137`); and the wrapper catches general exceptions before LangGraph can observe them as node failures (`yamlgraph/compile/map_compiler.py:161`). The first consumer is also concrete: the cited plan identifies the 500k-item fan-out and checkpoint-state pressure (`docs/plan-web-toolkit.md:184-204`) and records the same four hardening gaps (`docs/plan-web-toolkit.md:206-228`).

| Rubric criterion | Finding |
|---|---|
| Scope | The parent is minimal only as a split record; each implementation surface is separately fenced, while durability, chunking, caching, Store use, checkpoint format, and progress logging are excluded (`feature-requests/FR-936-map-node-hardening.md:37-42`). |
| Consistency | Status, child table, non-overlap contract, and ordering note consistently deny parent authority (`feature-requests/FR-936-map-node-hardening.md:5,20-49`). The unmodified original proposal is historical evidence, not an active implementation plan (`feature-requests/FR-936-map-node-hardening.md:65-68`). |
| Measurability | Overflow is already expressed as a pre-`Send` assertion, and the timeout child requires a post-timeout healthy-branch liveness witness (`feature-requests/FR-936-map-node-hardening.md:33-35`). D-1 and D-4 still need child-level exact witnesses rather than relying on the original broad criteria (`feature-requests/FR-936-map-node-hardening.md:184-202`). |
| Feasibility | D-1, D-2, and D-4 extend the existing CAP-11 map compiler surface (`capabilities/CAP-11-subgraph-map.yaml:1-16`); D-3 is correctly constrained to investigation because the rejected shared-pool design cannot terminate running work (`feature-requests/FR-936-map-node-hardening.md:25-28,34`). |
| Architecture alignment | The split preserves the existing `Send`/reducer primitive instead of creating a second map node type, consistent with the native-coverage analysis (`docs/plan-web-toolkit.md:184-204`) and CAP-11 (`capabilities/CAP-11-subgraph-map.yaml:1-16`). |
| Single responsibility | Four independent contracts are bundled in the historical proposal (`feature-requests/FR-936-map-node-hardening.md:136-182`); SPLIT is mandatory. |
| Strategic classification | These are framework-primitive corrections to an existing abstraction, not one new primitive: current code and the plan evidence show multiple existing and census-scale map consumers (`yamlgraph/compile/map_compiler.py:332-365`; `docs/plan-web-toolkit.md:206-228`). |
| Testability | Direct witnesses exist for payload keys, pre-dispatch overflow, post-timeout liveness, and retry attempt/error ordering, but they belong in four independently researched child FRs; the parent correctly leaves three of those children unallocated (`feature-requests/FR-936-map-node-hardening.md:32-35`). |

The adjacent invalid Pattern 12 example is also correctly parked rather than smuggled into implementation scope: the example uses `source`, `prompt`, and `state_key` (`reference/patterns.md:1127-1145`), while the generated schema exposes the map-node `max_items` surface and no such map shorthand (`yamlgraph/schemas/graph-v1.json:200-236`). Recording that drift creates no FR-936 authority (`feature-requests/FR-936-map-node-hardening.md:53-63`).

## Required revisions

### R-1: Allocate and author the three missing child requests

Create separate FRs for D-1 input projection, D-3 timeout lifecycle investigation, and D-4 native retry. Update the FR-936 child table with each committed path and status. Keep FR-939 as D-2; do not reopen its overflow surface in another child. FR-936 is complete as a split record only when all four rows identify concrete replacement FRs.

### R-2: Give every child substantive, scope-specific research

Each child must point to its own committed research record satisfying the prospective FR-890 gate: four to six genuine solution classes for that child's single problem, relevant precedent disposition including rejected precedent, preserved disagreement, and an explicit `is_this_a_graph` answer. The parent's alternatives table distributes one alternative across each of four concerns (`feature-requests/FR-936-map-node-hardening.md:204-211`) and therefore cannot substitute for child research. Do not treat the uncaptured external LangGraph documentation claim as committed evidence; each child must preserve the exact source evidence it relies on.

### R-3: Preserve the D-1 execution-contract fence

The input-projection child must derive the payload from every execution-time state consumer, not prompt text alone. It must cover `variables`, `requires`, direct Jinja state access, guards, verification, routing, `skip_if_exists`, and every supported sub-node type. Python, agent, and subgraph consumers with dynamic access must require declared inputs or retain full-state pass-through with a lint warning, exactly as fenced at `feature-requests/FR-936-map-node-hardening.md:32`. Its RED witnesses must assert exact keys and a reduced serialized pending-write/checkpoint payload, not merely shallow-copy object size.

### R-4: Preserve the D-3 termination-and-liveness fence

The timeout child must remain investigation-first. It must reproduce more permanent hangs than the available execution capacity, trace submission through timeout, cancellation or return, disposal, and reclamation, and prove a later healthy branch completes within a fixed deadline. A bounded executor, thread-count ceiling, or recorded timeout error does not establish termination (`feature-requests/069-map-node-timeout.md:135-137`).

### R-5: Preserve the D-4 retry-ownership fence

The retry child must define one retry owner, typed Pydantic configuration, a closed declarative `retry_on` allowlist, and exact ordering between LangGraph retry and final `on_error`. Its witnesses must prove retryable success, exhausted retry, non-retryable failure, and one final disposition. It must not attach `RetryPolicy` outside a wrapper that still catches the target exception and returns a successful state update (`yamlgraph/compile/map_compiler.py:161`).

### R-6: Replace parent completion ambiguity with split-record criteria

Keep the original proposal explicitly historical, but make the revised acceptance criteria below the authoritative completion contract for FR-936. The original implementation criteria (`feature-requests/FR-936-map-node-hardening.md:184-202`) must not be read as authority to modify production code under the parent.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | One committed child FR and research record for map branch input projection |
| D-2 | Existing FR-939 overflow child, governed only by its own judgement |
| D-3 | One committed investigation FR and research record for timeout cancellation and resource lifecycle |
| D-4 | One committed child FR and research record for native `RetryPolicy` and exception ownership |
| D-5 | `feature-requests/FR-936-map-node-hardening.md` updated only as the parent split registry |

Not authorized by FR-936: production code, schemas, tests, capability requirements, reference documentation, changelog fragments, demos, or prompts. Also not authorized: durable or resumable map behavior, batching or chunked scheduling, concurrency controls, `CachePolicy`, Store-backed results, checkpoint-format changes, progress logging, provider-wide timeout behavior, non-map retry behavior, or repair of the parked Pattern 12 documentation drift.

## Revised acceptance criteria

- [ ] AC-01: FR-936 remains `Status: SPLIT` and explicitly states that it grants no implementation authority.
- [ ] AC-02: The child table identifies four committed replacement FR paths, one each for D-1 through D-4, with no overlapping implementation deliverables.
- [ ] AC-03: D-2 points only to FR-939 and accurately records its human-review and implementation state.
- [ ] AC-04: Each child points to a committed research record containing four to six genuine solution classes, precedent disposition, preserved disagreement, and an explicit `is_this_a_graph` answer.
- [ ] AC-05: D-1 freezes exact state-consumer coverage and dynamic-access behavior; its child criteria require exact payload-key and serialized-size witnesses.
- [ ] AC-06: D-3 is an investigation FR whose criteria require termination or isolation, capacity reclamation, and a fixed-deadline healthy-branch liveness witness after excess hangs.
- [ ] AC-07: D-4 freezes typed retry configuration, a closed retryable-error vocabulary, one retry owner, exception visibility to LangGraph, and final `on_error` ordering.
- [ ] AC-08: Every child allocates only its necessary CAP-11 requirement IDs and requires `@pytest.mark.req` on each new test, consistent with `.github/copilot-instructions.md:166`.
- [ ] AC-09: The parent non-overlap contract excludes durability, scheduling, concurrency, caching, Store, checkpoint-format, progress, provider-wide, and non-map changes.
- [ ] AC-10: The original proposal and acceptance criteria are labeled historical and cannot be cited as parent implementation authority.
- [ ] AC-11: The parked Pattern 12 documentation drift remains outside all four children unless a separate judged scope explicitly adopts it.
- [ ] AC-12: No FR-936 production implementation diff exists.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not implement production changes under FR-936; only independently judged child FRs may grant implementation authority. | GATE |
| C-2 | Do not begin a child judgement until its committed research record satisfies the FR-890 substance gate. | GATE |
| C-3 | Do not drop state keys from `Send` payloads unless every execution-time consumer is covered or the dynamic branch retains full-state input. | GATE |
| C-4 | Do not accept timeout handling that leaves hung work occupying all capacity or lacks the post-timeout liveness witness. | GATE |
| C-5 | Do not attach native retry where the target exception is converted to a state update before LangGraph observes it. | GATE |
| C-6 | Do not expose arbitrary Python imports or callables through retry YAML. | GATE |
| C-7 | Do not cross child fences or absorb durability, scheduling, caching, checkpoint, progress, provider-wide, non-map, or parked documentation work. | GATE |
| C-8 | Treat this draft as advisory until human-reviewed. | GATE |

Authority granted: only to finish the FR-936 split registry and author the three missing child FRs with their committed research records; no production implementation is authorized by FR-936.
