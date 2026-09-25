# Judgement: FR-1073 Map result contract

**Prior art:** `FR-1073-map-result-contract.md` is the FR this judgement governs. FR-1064 (SPLIT parent), FR-957, FR-985 (Shelved), FR-408 (Rejected), FR-677, FR-944, FR-983 and FR-936 are dispositioned in the FR and reviewed above.

**Verdict:** APPROVED WITH REVISIONS — the separate success/failure channels, post-branch completeness join, and strict undeclared-partial-success default are the right framework correction; authority activates only after R-1 through R-6 are folded into the FR, every non-strict migration threshold is explicitly human-approved, and this advisory draft is human-reviewed.

**Reviewed against:** `feature-requests/FR-1073-map-result-contract.md`; `feature-requests/FR-1073.research.md`; `docs/issues-2026-09-24.md`; `feature-requests/FR-1064-map-branch-contract.md`; `feature-requests/FR-1064-map-branch-contract.judgement.md`; `feature-requests/FR-957-map-branch-native-retry-policy.md`; `feature-requests/FR-985-census-coverage-floor-and-population-header.md`; `feature-requests/FR-985-census-coverage-floor-and-population-header.judgement.md`; `feature-requests/FR-408-runtime-repair-metadata.md`; `feature-requests/FR-677-verification-first-class-dsl.md`; `feature-requests/FR-944-map-to-map-index-attribution.md`; `feature-requests/FR-983-map-concurrency-and-census-coverage-gate.judgement.md`; `feature-requests/FR-936-map-node-hardening.judgement.md`; `yamlgraph/compile/map_compiler.py`; `yamlgraph/compile/edge_compiler.py`; `yamlgraph/models/node_schema.py`; `yamlgraph/models/state_builder.py`; `yamlgraph/models/schemas.py`; `.github/copilot-instructions.md`; `.github/skills/graph-authoring/doctrine.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

| Criterion | Finding |
|---|---|
| Scope | The parent SPLIT required map-result semantics to be separated from provider/executor retry ownership (`FR-1064-map-branch-contract.judgement.md:15-29`). FR-1073 does that: retry, resume, overflow, projection, and timeout lifecycle are explicitly excluded (`FR-1073-map-result-contract.md:132-134`). The remaining migration is directly coupled to changing the default map contract, although its exact graph surface must be enumerated by R-5. |
| Consistency | The value statement and strict default agree: incomplete successes do not reach an undeclared consumer (`FR-1073-map-result-contract.md:47-57,74-78,119-125`). This satisfies the parent gate that forbids unacknowledged partial output (`FR-1064-map-branch-contract.judgement.md:19-25,50-54`). The unresolved meanings of “latest dispatch,” tolerated counts, and count-versus-fraction thresholds are contract defects, not reasons to reject the direction; R-1 through R-3 make them exact. |
| Measurability | RED 1 through RED 6 name discriminating state and exception outcomes, including the `errors: []` false positive, mutated `over`, shared collect channels, and loop reuse (`FR-1073-map-result-contract.md:138-147`). The current wrapper confirms these tests can begin RED on behavior rather than imports: it catches timeout/general exceptions into `collect` and treats mere `errors` key presence as failure (`map_compiler.py:139-202`). R-4 and the revised criteria add the missing topology, reducer, and concurrency assertions. |
| Feasibility | The implementation seams exist. Fan-out payloads are constructed in one edge function (`map_compiler.py:334-366`), map branches are wrapped at one boundary (`map_compiler.py:116-225`), and outgoing map edges currently attach directly to the synthetic sub-node (`edge_compiler.py:246-249`). FR-944 already proved a generated barrier join after map fan-in (`edge_compiler.py:221-236`). Zero-item routing and a result join require changing the map metadata and edge destinations, but no LangGraph modification or retry redesign. |
| Architecture alignment | The proposal normalizes the defect at map fan-in instead of requiring 26 consumers to filter error-shaped data (`FR-1073-map-result-contract.md:61-70,158-165`; `docs/issues-2026-09-24.md:113-128`). Separate channels and an identity-completeness verdict also match the incident’s evidenced target pattern (`docs/issues-2026-09-24.md:206-221`). Typed schema fields and state reducers are the existing extension points (`node_schema.py:96-106,370-378`; `state_builder.py:259-262`). |
| Single responsibility | Item identity, failure separation, accounting, and the threshold verdict are inseparable parts of one map-result contract: the join cannot decide policy without branch outcomes and original dispatch identity. The provider-wide retry half remains outside this FR as ordered by the parent judgement. No further split is warranted. |
| Strategic classification | **Framework primitive.** The incident census found 67 map nodes and 26 in-graph consumers, including 13 prompt consumers (`docs/issues-2026-09-24.md:109-128`), well above the rubric’s three-use-case threshold. Existing graph-level `verify:` and downstream census filters are opt-in or consumer-local and therefore do not fit this boundary (`FR-1073-map-result-contract.md:163-165`). |
| Testability | Core acceptance is LLM-free: Python sub-nodes can produce success, exception, skip, duplicate-key, loop, shared-channel, zero-item, and concurrent-dispatch fixtures. A memory checkpointer can witness committed branch results after the join raises. The live `innovation_matrix` run is useful operational evidence but is not deterministic acceptance and may spend provider funds; R-6 removes it from the gate unless explicitly authorized. |

The research gate is substantive. The promoted record contains five independent personas and preserves the subtractionist disagreement (`FR-1073.research.md:3-21`); the FR dispositions add graph verification, lint enforcement, and documentation-only classes, preserve dissent, distinguish the rejected FR-408 repair territory, and answer `is_this_a_graph` (`FR-1073-map-result-contract.md:152-170`). The witnessed defect is also concrete: four failures entered the result list, the synthesis consumed 21 results plus four error reprs, and the process exited 0 (`docs/issues-2026-09-24.md:75-107`).

The strict default should not wait for FR-1065. Resume can reduce the cost of a failed run, but it does not make undeclared partial output correct. The operator’s stated preference (`FR-1073-map-result-contract.md:172-181`), the parent judgement’s fail-closed gate, and the witnessed plausible wrong answer support activating strictness together with a complete, human-approved migration census.

## Required revisions

### R-1: Replace “latest dispatch” inference with an exact dispatch-generation contract

Fold a precise dispatch lifecycle into Proposed Solution item 1 and the join contract:

1. Every invocation of one map edge creates one opaque dispatch token and one immutable dispatched count after `max_items` has been applied.
2. Every branch accounting row carries that exact token, map name, dispatched count, index, key, and outcome.
3. The join receives or derives the exact token for the invocation that scheduled it. It must never select the “latest” token from `_map_accounting`; an opaque fresh identifier has no ordering, and accumulated loop rows make that selection nondeterministic (`FR-1073-map-result-contract.md:94-118`).
4. A sequential loop invocation replaces `_map_verdict.<name>` with the new completed dispatch while old accounting rows cannot be selected by the new join.
5. Two overlapping invocations of the same map name are not represented by the single-value `_map_verdict.<name>` contract. Reject that overlap with a typed accounting error naming the map and both dispatch tokens before either invocation can publish a verdict; never let last-write-wins choose one. Different map names may complete concurrently.

Add RED witnesses for two sequential invocations of one map and two overlapping invocations of one map. The sequential witness must produce two distinct dispatch tokens and leave the second verdict current. The overlapping witness must fail closed rather than producing a nondeterministic verdict. This folds the concurrent-invocation requirement from the parent judgement (`FR-1064-map-branch-contract.judgement.md:23-25`) instead of substituting only a loop test.

### R-2: Freeze threshold types, arithmetic, zero-item behavior, and error-policy ownership

Define `min_success` as a strict `int | float | None`; reject booleans, strings, non-finite floats, negative integers, and floats outside inclusive `[0.0, 1.0]`. YAML integer `1` means one accepted item; YAML float `1.0` means 100 percent. An integer larger than `dispatched` is valid but unmet.

Freeze these verdict terms:

- `succeeded`: branches that wrote a real entry to `collect`.
- `tolerated`: branches that wrote a failure record because the nested sub-node explicitly returned `_skipped: true`.
- `failed`: all other failure records.
- `accepted`: `succeeded + tolerated`.
- `dispatched`: `succeeded + tolerated + failed`, after identity validation.
- Integer policy: `met = accepted >= min_success`.
- Fraction policy: `met = accepted / dispatched >= min_success`.
- Absent policy: equivalent to fraction `1.0`.
- Zero items: `{dispatched: 0, succeeded: 0, tolerated: 0, failed: 0, accepted: 0, min_success: <declared-or-1.0>, met: true}` without division.

`MapCompletenessError` is raised only after accounting is complete and `met` is false. A nested sub-node’s `on_error: skip` classifies its failure as tolerated; other failures are not tolerated. Remove the sentence making map-level `on_error: fail` an alias for `min_success: 1.0` (`FR-1073-map-result-contract.md:123-125`): `min_success` owns map-result policy in this FR, while nested `node.on_error` owns branch disposition. Do not silently create a second map-level policy surface.

### R-3: Define typed public records and reducers separately from `state.errors`

Replace the claim that one record is written unchanged to both `failures` and `state.errors` (`FR-1073-map-result-contract.md:104-109`) with two typed outputs:

- `MapFailure`: `{map, dispatch, _map_index, key, error_type, message, node, tolerated}`. Every configured failure channel contains only serialized `MapFailure` values. `map` and `dispatch` are required because two maps may intentionally share a collect/failure channel.
- `PipelineError`: the existing framework model remains the element type of `state.errors` (`schemas.py:31-83`; `state_builder.py:68-70`). Non-tolerated failures append one `PipelineError` whose `node` is the real synthetic sub-node name; tolerated failures append none.
- `MapAccounting`: a private typed record containing the fields frozen by R-1 and an outcome from the closed set `succeeded | tolerated | failed`.
- `MapVerdict`: `{dispatch, dispatched, succeeded, tolerated, failed, accepted, min_success, met}`.

Specify state generation and reducer behavior. A map’s `collect` and `failures` channels are list reducers; shared channels retain stable attribution and order. `_map_accounting` accumulates typed rows. `_map_verdict` merges different map names and replaces the same map name only for a completed later sequential invocation; it must not use the current unconstrained `last_value` behavior (`state_builder.py:20-34`). Validate that `failures` is a non-empty state-key name, differs from `collect` and reserved infrastructure keys, and defaults to `<collect>_failures`. Add schema/code-generation witnesses so the feature is not accepted merely because runtime dicts happen to flow.

### R-4: Specify the join topology for every authorized path

Fold the compiler shape into the FR rather than leaving “the edge routes straight to the join” implicit (`FR-1073-map-result-contract.md:110-127`):

- Each compiled map owns `_map_<name>_sub` and `_map_<name>_join`; generated-name collisions fail compilation and name the map and conflicting synthetic node.
- Every non-empty fan-out sends only to the sub-node; every sub-node completion converges on the result join; every outgoing edge formerly sourced from the sub-node is sourced from the result join.
- Empty input schedules the result join directly with the dispatch token and `dispatched=0`; it must not depend on a sub-node that never runs.
- For map-to-map, the order is upstream sub-node → upstream result join → FR-944 barrier join → downstream fan-out, and the downstream fan-out fires once.
- Direct-to-END, ordinary node-to-map, START-to-map, map-to-map, and loop-back-to-map paths retain their existing destination semantics apart from insertion of the result join.

Update compiler metadata so edge compilation knows both synthetic node names. Add structural tests asserting the compiled path, not only final state, plus the FR-944 N=3 and independent N×M fixtures. The existing FR-944 barrier proves the join pattern, but its current metadata exposes only `(map_edge_fn, sub_node_name)` and its outgoing path is still sub-node-based (`edge_compiler.py:221-249`).

### R-5: Commit the migration census and route graph edits through graph authoring

Before authority activates, add an exact table to FR-1073 listing every repository map affected by the strict default: graph path, map name, current branch disposition, whether it stays strict or receives explicit `min_success`, the exact proposed value, and the committed evidence for that value. Also list the exact `_error` consumers being migrated. “Every map ... whose graph expects partial success” is not an enumerable delivery surface (`FR-1073-map-result-contract.md:128-130`).

Do not infer non-strict thresholds from historical survival alone. FR-985 was shelved because three demo-specific runs at 57–92 percent still produced useful briefs (`FR-985-census-coverage-floor-and-population-header.md:1-7`), but that does not select a threshold for another graph. **Human decision required:** does the operator approve every exact non-strict threshold in the folded migration table? Until an affirmative decision is recorded against the table, only strict `1.0` behavior is authorized for that map.

Any material `graph.yaml` edit must have a committed FR-bound task brief under `feature-requests/authoring-briefs/`, run through the sole graph-authoring route, and produce the required report, lint, and narrow smoke evidence (`.github/skills/graph-authoring/doctrine.md:9-30,53-90`). The migration may not use direct manual graph edits. The `corpus_census/tools.py` consumer migration remains authorized because it is the named existing downstream workaround (`docs/issues-2026-09-24.md:170-178`).

### R-6: Make the live innovation-matrix rerun optional operational evidence

Replace the current paid, nondeterministic acceptance item (`FR-1073-map-result-contract.md:149`) with deterministic compiled-graph witnesses:

- Under the absent/strict policy, one branch failure prevents the downstream consumer from running.
- Under a declared met partial policy, the downstream consumer receives only successful `collect` entries and can separately read typed failures and the verdict.
- In both cases no `_error` or exception repr enters the consumer’s content input.

Retain the `innovation_matrix` rerun only as a non-gating operational observation. **Human decision required:** does the operator authorize the provider spend for that rerun after deterministic acceptance passes? If authorized, record provider/model, exact command, dispatch/success/failure verdict, quoted raw `synthesize` input or the fact that strict failure prevented synthesis, and terminal result. If not authorized or if credentials are unavailable, record that it was not run and make no live-demo claim. The uncommitted raw files from the original incident are evidence summarized in the committed incident record, not acceptance artifacts (`docs/issues-2026-09-24.md:49-58`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 — map configuration | `yamlgraph/models/node_schema.py`; generated graph schema if required: map-only `key`, `failures`, and strict `min_success` validation |
| D-2 — typed records and state | `yamlgraph/models/schemas.py` or one focused map-result model/exception module; `yamlgraph/models/state_builder.py`; `yamlgraph/models/state_codegen.py`: `MapFailure`, `MapAccounting`, `MapVerdict`, `MapCompletenessError`, channel registration, and reducers |
| D-3 — compilation | `yamlgraph/compile/map_compiler.py`; `yamlgraph/compile/edge_compiler.py`: dispatch payload, one branch-result helper, result join, zero-item route, and FR-944 composition |
| D-4 — deterministic witnesses | One focused FR-1073 unit/compiled-graph test module plus directly affected existing map, state-builder, schema, and FR-944 regression suites |
| D-5 — consumer migration | `examples/demos/corpus_census/tools.py`; only the exact graph files listed in the folded migration census and approved under R-5; committed graph-authoring brief(s) and `tmp/draft-authoring-report.md` evidence |
| D-6 — contract and traceability | `reference/graph-yaml.md`; CAP-11 or the existing map capability with new REQ IDs; regenerated `ARCHITECTURE.md`; one fix changelog fragment; FR-1073 implementation record; one diary reflection with `Seed:` |
| D-7 — optional observation | One human-authorized `innovation_matrix` run record after deterministic acceptance; no production or graph change to `innovation_matrix` under this deliverable |

Not authorized: SDK/provider retry changes; executor-loop or node-retry ownership; FR-957 implementation or status changes; resume/reuse implementation; checkpoint format changes; map overflow, input projection, timeout-thread ownership, concurrency limits, caching, scheduling, or progress logging; CLI exit-code policy; changes to `state.errors` outside adding correctly attributed existing `PipelineError` values; prompt changes; unrelated `innovation_matrix` repair; thresholds not explicitly listed and human-approved; graph files outside the folded migration census; or any FR-936/FR-939/FR-955/FR-956 surface.

## Revised acceptance criteria

- [ ] AC-01: RED first: map schema accepts optional `key` and `failures`, defaults `failures` to `<collect>_failures`, and validates `min_success` as the strict integer/fraction contract from R-2; booleans, strings, non-finite floats, negative integers, and out-of-range floats fail at load with the map name and offending field/value.
- [ ] AC-02: `failures` equal to `collect`, empty, or colliding with a reserved infrastructure field fails at load; two maps may intentionally share a non-reserved collect/failure channel because every failure record carries map and dispatch attribution.
- [ ] AC-03: fan-out resolves every item key before returning any `Send`; duplicate keys fail before any branch executes and name the map, duplicate key, and both indices.
- [ ] AC-04: the timeout exception path, general exception path, and error-bearing update path emit the identical typed `MapFailure` shape; each non-tolerated path emits exactly one correctly attributed `PipelineError`; no path writes to `collect`.
- [ ] AC-05: a successful update containing `errors: []` is collected as success and emits no failure/accounting error.
- [ ] AC-06: with a memory checkpointer, three items and one non-tolerated Python sub-node failure under absent `min_success` produce two successful collect entries, one failure, complete accounting, and `MapCompletenessError` at the join; checkpoint inspection after the raise sees the two finished results.
- [ ] AC-07: 100 items with one non-tolerated failure and `min_success: 0.98` produce `succeeded=99`, `tolerated=0`, `failed=1`, `accepted=99`, `met=true`; the downstream node runs with 99 success entries and no error-shaped content.
- [ ] AC-08: integer and fraction semantics are distinguished: `min_success: 1` accepts one accepted item, `min_success: 1.0` requires all dispatched items accepted, an integer above dispatch is unmet, and every invalid boundary from R-2 is covered.
- [ ] AC-09: an explicit nested `on_error: skip` failure produces one `MapFailure(tolerated=true)`, no `PipelineError`, increments `tolerated` and `accepted` but not `succeeded` or `failed`, and participates in threshold arithmetic exactly as R-2 defines.
- [ ] AC-10: zero items schedules the result join and yields the exact zero verdict from R-2 with `met=true`; the graph reaches its ordinary target without executing the sub-node.
- [ ] AC-11: a branch that mutates state read by `over` cannot change the dispatch count, keys, or expected index set captured at fan-out; missing or repeated accounting indices raise a typed framework accounting error.
- [ ] AC-12: two maps sharing collect/failure channels account only their own map and dispatch; records remain attributable and stable. Two sequential loop invocations of one map use distinct tokens and leave only the second verdict current without selecting old accounting rows.
- [ ] AC-13: two overlapping invocations of the same map name fail closed with both dispatch tokens named and publish no nondeterministically selected verdict.
- [ ] AC-14: compiled topology witnesses cover START → map → END, ordinary node → map → node, zero-item routing, loop-back, and map-to-map; all outgoing paths originate after `_map_<name>_join`, and synthetic-name collisions fail with the conflicting name.
- [ ] AC-15: the FR-944 N=3 fixture still yields downstream indices `[0, 1, 2]` once, and its independent N×M fixture still fans out exactly M times; no downstream map router attaches directly to the upstream sub-node or bypasses the upstream result join.
- [ ] AC-16: state-generation tests prove collect, failures, `_map_accounting`, and `_map_verdict` have their declared reducers; concurrent different-map verdict updates preserve both entries; `state.errors` remains an accumulated list of `PipelineError`.
- [ ] AC-17: no repository map consumer reads `_error` from `collect`; `corpus_census/tools.py` reads the declared failures channel, and focused fixtures prove its previous successful and failed-row behavior through the new contract.
- [ ] AC-18: the folded migration table enumerates every affected map and `_error` consumer; every non-strict value has explicit human approval and cited evidence; every graph edit has a committed authoring brief, governed authoring report, passing lint, and attempted narrow smoke with exact outcome.
- [ ] AC-19: deterministic downstream-content tests prove strict failure prevents consumer execution and declared partial success passes only real results, while failures and verdict remain separately readable; no `_error` or exception repr appears in content.
- [ ] AC-20: `reference/graph-yaml.md` documents field types/defaults, integer-versus-fraction semantics, tolerated arithmetic, zero items, typed failure/verdict shapes, same-map overlap rejection, and strict default behavior; traceability artifacts and every new test carry the new map-result REQ ID, and `python scripts/req_coverage.py --strict` passes.
- [ ] AC-21: RED and GREEN are separate commits; RED fails on schema, channel, accounting, topology, threshold, or downstream-content assertions rather than missing imports, fixtures, credentials, or services.
- [ ] AC-22: the focused FR-1073 suite and directly affected map/schema/state/FR-944 regressions pass. A paid provider run is not required; if human-authorized, its sanitized result is appended as a non-gating operational observation.
- [ ] AC-23: FR-1073 records final implementation status, exact migration decisions and deviations; one fix changelog fragment and one diary reflection containing `Seed:` are committed.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-6 are folded into FR-1073 and this advisory draft is human-reviewed before implementation authority activates. | GATE |
| C-2 | Core behavior remains strict by default: no downstream node receives undeclared partial `collect` output after a non-tolerated failure. | GATE |
| C-3 | Dispatch identity is passed exactly to its join; no join infers “latest” from accumulated opaque tokens, and overlapping same-map invocations fail closed. | GATE |
| C-4 | `failures` contains typed `MapFailure`; `state.errors` contains existing typed `PipelineError`; tolerated failures never enter `state.errors`; reducers preserve concurrent different-map updates. | GATE |
| C-5 | No non-strict migration threshold is implemented until the exact value and graph path are recorded in the FR and explicitly approved by the human operator. | GATE |
| C-6 | Every material graph edit uses a committed FR-bound authoring brief and the sole graph-authoring route, with lint, smoke attempt, and report evidence. | GATE |
| C-7 | Retry ownership, resume, overflow, projection, timeout lifecycle, CLI exit behavior, and unrelated demo repair remain outside the diff. | GATE |
| C-8 | RED precedes GREEN and directly condemns missing FR-1073 behavior; import, fixture, credential, or service failures do not count as RED. | GATE |
| C-9 | The live `innovation_matrix` rerun occurs only after explicit human spend authorization and remains non-gating. | GATE |

Authority granted: after C-1 and C-5 are satisfied, implement only the frozen typed map-result contract, result join/accounting topology, strict declared-partial-success policy, enumerated consumer migration, direct documentation/traceability, and deterministic witnesses.
