# Judgement: FR-1161 `cached_map` Node: Warm-First Map Dispatch for Prompt Caching

**Verdict:** REJECTED — Return to planning: warm-first dispatch addresses a measured problem, but the standalone core primitive lacks the required use-case justification and its release router can change the dispatched population after warming.

**Prior art:** FR-1155 (origin and meters), FR-1158 (rejected memo, distinguished), FR-1159 (rejected contrib memo), FR-1073, FR-984, FR-1055, FR-111 as dispositioned in the FR.

**Reviewed against:** Committed inputs at `a38051858158808da302b3b419b77db52b59d13b`:

- `feature-requests/FR-1161-cached-map-warm-first.md`, entire file.
- `feature-requests/FR-1155.research.md`, entire file.
- `feature-requests/FR-1155-prompt-cache-tokens-in-token-usage.md`, sections returned for Research, Problem, Proposed Solution, Alternatives Considered, Follow-up, Acceptance Criteria, Judgement fold and Implementation status.
- `feature-requests/FR-1158-cached-map-node.judgement.md`, entire file.
- `feature-requests/FR-1159-map-memo-contrib.md`, lines 1-220.
- `feature-requests/FR-1073-map-result-contract.md`, lines 1-220.
- `feature-requests/FR-984-map-fan-out-max-concurrency.md`, lines 1-200.
- `feature-requests/FR-1055-anthropic-prompt-cache-blocks-never-reach-api.md`, lines 1-150.
- `feature-requests/FR-111-compiled-graph-cache.md`, lines 1-140.
- `yamlgraph/compile/map_compiler.py` and `yamlgraph/compile/map_contract.py`, entire files.
- `examples/demos/prompt-caching/graph.yaml`, entire file.
- `.github/skills/judge-fr/doctrine.md` and `.github/skills/judge-fr/judgement.template.md`, entire files.
- Repository instructions supplied from `.github/copilot-instructions.md` and `CLAUDE.md`.

The consumed files match HEAD. No author transcript, working notes, external consumer checkout, or uncommitted adapter modification informed this verdict. The game-engine workload is evaluated as a claim in the committed FR, not as independently inspected code. This is a draft only; it does not change the FR's status.

## What is sound

The strongest case for approval is substantial: the spike records eight writes versus one for an identical 12-item population, and warm-first retains most parallelism (`FR-1155.research.md:78-97`). This is not persistent result reuse. Dispositioning FR-1158's rejected memo and keeping every real worker invocation is correct (`FR-1161:25-47`).

Waiting for a complete warm-stage outcome avoids making an unsupported first-token cache-availability assumption. Separate supersteps avoid branches holding concurrency slots while waiting for another branch. One token, all-index accounting and commit-before-enforce are sound invariants to preserve (`FR-1161:179-191`; `map_contract.py:177-219`). The example, real graph witness and graph-authoring route are appropriate deliverables, not unrelated scope.

| Rubric criterion | Assessment |
|---|---|
| 1. Scope | One scheduling concern, but a second public core node is not yet justified over the smaller map option. Deferral is a product preference, not evidence that the option cannot fit (`FR-1161:98-109,285-286`). |
| 2. Consistency | Unchanged population/results conflict with re-resolving `over` after item 0 has committed. Literal failure/verdict equality also conflicts with fresh dispatch identities (`FR-1161:161-185,229-234`; `map_contract.py:127`). |
| 3. Measurability | Ordering and concurrency are directly measurable. Live thresholds are both already specified and promised to be fixed after seeing the witness; the ordinary-map race is not deterministic (`FR-1161:243-250,267-269`). |
| 4. Feasibility | The worker factory and account/join factories are reusable. The dispatch record currently stores a token and count, not the population; unchanged factories alone do not provide a stable release population (`map_contract.py:119-175`). |
| 5. Architecture alignment | Compiler-owned Send wiring and shared worker construction align. Full map semantics require preserving branch input context as well as result classification; a new release boundary must not feed item 0's accumulated outputs into later worker inputs (`FR-1161:167-185`; `map_contract.py:163-170`). |
| 6. Single responsibility | One cohesive concern: warm-first dispatch. Registration, example and witnesses support it; no SPLIT is warranted. |
| 7. Strategic classification | **Contrib/example on current demand evidence**, with a core scheduling gap, not an approved framework primitive. Character/place maps provide at most two concrete workload classes; an imagined demo map and a future automatic trigger are not additional independently evidenced consumers (`FR-1161:100-109`; judge doctrine:51-55). This classification does not authorize inventing a plugin. |
| 8. Testability | Main order/width tests can fail for missing behavior without new imports. Population identity, worker-input parity, timeout semantics and normalized result comparison need explicit contracts before their tests can be derived (`FR-1161:222-250`). |

The research gate is satisfied for investigating this mechanism: the committed spike, alternatives table and `is_this_a_graph` answer are substantive (`FR-1161:19-24,281-292`). This is scheduling, not new measurement tooling; the measurement-tooling pre-authority raw-sample gate does not apply. The semaphore spike remains evidence of the phenomenon, not proof of the proposed graph topology (`FR-1155.research.md:85-86`).

## Required revisions

These are return-to-plan requirements, not conditional implementation authority.

### R-1: Supply the core-primitive justification without counting hypothetical consumers

Replace the use-case paragraph with a committed table naming each concrete workload, its shared-prefix contract and the existing abstraction's actual gap. Do not count redo variants as independent demand merely because their node names differ; do not count a newly proposed demonstration or automatic-mode implementation as another consumer.

The doctrine requires three or more use cases for a framework primitive (`judge-fr/doctrine.md:51-55`), and FR-1158's judgement already rejected counting demonstrations as independent demand. Either supply that evidence for the standalone node or return with a smaller, separately judged extension of the existing map abstraction. Do not silently substitute contrib packaging, add a plugin system, or change ordinary map here.

Keep the operator's standalone-first request visible. Surface the product decision explicitly: **Should a standalone public node remain required if the committed evidence does not meet the framework-primitive threshold?** A judge cannot waive doctrine or invent consumers to reconcile that decision. The `cached_map` spelling is not itself a blocker; retain it if the public node is subsequently authorized, and state that it provides ordering, not result memoization.

### R-2: Freeze the population and common branch inputs before warming

Replace the promise that both routers re-resolve `over` against their current state (`FR-1161:182-185`) with a dispatch-time snapshot contract. Both waves must use the same capped items, indices, dispatch token and common pre-worker input context. Keep execution bookkeeping separate from that common worker input snapshot.

The current router copies the dispatch state into every Send (`map_contract.py:151-170`). The wrapper appends results into `collect` (`map_compiler.py:211-214`). A map whose `over` reads its collect channel therefore illustrates the defect: item 0 appends a result before the release router resolves `over`, so the count changes and the release raises despite a valid original population. A count check alone also cannot detect a same-length item substitution. Independently, later worker variables must not begin seeing the warm result merely because it committed one superstep earlier.

Specify the snapshot's ownership, lifetime and typed transport in the FR, including how it remains usable across the warm/release boundary without a process-global event or mutable compiler closure. Permit only the shared-factory changes necessary for this contract; preserve ordinary map behavior.

Add a compiled-graph witness where `over` and `collect` use the same append-reduced channel, and another where a worker reads a common state variable affected by collection. Assert exactly the original N item identities execute once, later workers receive the original common input value, and accounting uses one token with indices exactly `0..N-1`. Include sequential re-entry so a prior dispatch snapshot cannot leak into the next.

### R-3: Distinguish logical completion from timeout-thread termination

Qualify the absolute whole-worker guarantee in `FR-1161:186-190,225-226`. The existing timeout wrapper returns after `Future.result(timeout=...)` and shuts down with `wait=False`; a running thread can continue (`map_compiler.py:103-125`). Reusing it cannot guarantee that a timed-out worker or its provider request has physically stopped before release.

Define release as occurring after item 0's wrapped outcome has settled and committed: success, classified failure, tolerated skip or timeout. State that successful workers and subgraphs finish before release, but existing timed-out background work may overlap it. Preserve existing timeout behavior; cancellation and timeout-thread redesign are not authorized.

Parameterize the warm-failure witness over exception, tolerated skip and wrapper timeout. Assert release and all-index accounting for each, and distinguish tolerated from failed counts and `min_success` outcomes. Use bounded synchronization and clean up the test worker so the timeout witness cannot leak work.

### R-4: Define semantic parity rather than literal record equality

Replace AC-04's unqualified equality with comparison of deterministic content ordered by `_map_index`, failure index/type/message/tolerance and verdict counts/policy/met. Normalize per-run dispatch identifiers consistently; each dispatch deliberately gets a fresh UUID (`map_contract.py:127`). Do not normalize away missing, duplicate or incorrectly attributed indices.

Specify diagnostic node naming separately. Existing wrappers, failure factories, account and join factories produce `_map_<name>_*` diagnostic names even if registered under `_cmap_<name>_*` (`map_compiler.py:157`; `map_contract.py:51,203,217`). Choose and document whether those semantic diagnostic identifiers remain shared or are parameterized to match the new topology; require the matching assertion rather than literal equality between structurally different graphs.

Keep the unsupported inference out of the documentation: ordering does not guarantee identical stochastic LLM responses or side-effect timing. Parity is the map result/accounting contract for equivalent deterministic worker outcomes.

### R-5: Make the live witness bounded and its gate independent of a provider race

Fold a reproducible witness protocol into the FR before implementation:

- Fix the Haiku model identifier, output-token limit, N = 4, explicit graph/invoke concurrency of 4, one eligible byte-identical shared prefix per variant, and a distinct nonce for each variant.
- Define positive P from the warm call's actual cache-write fields, using FR-1155's existing `max(cache_creation, ephemeral_5m + ephemeral_1h)` rule. Reject missing/zero evidence rather than deriving a vacuous threshold.
- Gate the warm-first graph on a cold first-call write with no cache read, total writes in `[P, 1.5 P]`, and total reads at least `2.5 P`. Capture all four cached-map raw records and the ordinary-map control's records/totals; read and explain the raw fields before computing the aggregate result.
- Keep ordinary-map `writes > 1.5 P` as a contextual observation, not a blocking assertion. Native concurrency bounds width; it does not guarantee overlapping cache misses at a remote provider. Do not weaken the warm-first gate to accommodate a failed run.
- Remove the contradictory promise to choose thresholds after observing the acceptance run (`FR-1161:249-250,267-269`). If observations invalidate the planned gate, amend and rejudge instead of tuning until green.

The human spend question must be explicit: **What call/token or monetary ceiling is authorized for the eight-call witness, the four-call demo and any retries?** The FR names paid runs without a ceiling (`FR-1161:211-215,243-250`). FR-1155's authorization concerned its own spike and two-call witness, not unlimited future runs. Missing credentials, an exhausted cap or a skipped integration test leave the live AC unmet.

Qualify Summary, Value Statement and Ideal Result (`FR-1161:51-65,93-96`): one write plus N-1 reads is an observed cold-run target for identical eligible prefixes, not a guarantee for every worker/provider/cache state. An already warm cache can produce zero writes; varying prefixes or expiration can produce more. Label the quoted 0.199/0.154 ratios as the measured N = 12 case rather than a general N = 9 result.

### R-6: Complete the acceptance surface for the advertised map contract

Extend the focused tests beyond happy-path lint/topology. Assert schema/load validation, inferred state and generated-state handling, failure channels, cap precedence and overflow before any warm worker starts, and outgoing routing through the join. Include map-to-cached-map and cached-map-to-map composition, plus the re-entry case from R-2. Every recognized map surface must remain consistent; include the published graph schema if it enumerates node types.

Specify exact existing-suite commands rather than FR numbers alone, and include FR-1153's timeout/context-propagation witnesses alongside the named FR-1073/984/1113 suites (`FR-1161:278-279`). All new tests need the allocated REQ marker. Add relevant Ruff/format and import-boundary checks, strict requirement coverage, the FR implementation/decision record, and the required diary entry with a `Seed:`. No unrelated cleanup or tooling changes are requested.

## Scope is frozen

No implementation scope is granted by this rejected draft.

| Deliverable | Surface |
|---|---|
| Draft judgement | `tmp/draft-judgement-copilot-FR-1161-cached-map-warm-first.md` only |
| Return-to-plan work | Committed FR and cited evidence addressing R-1 through R-6; not performed by this judge |
| Candidate mechanism, not authorized | Warm real item 0, release remaining original items, account once, then enforce once |
| Candidate supporting artifacts, not authorized | Focused offline/live witnesses, governed demo, reference, capability/REQ, generated architecture and changelog |

Not authorized: core `cached_map` registration/compiler implementation; a map option or automatic mode substituted without judgement; result memoization; plugin hooks; migration of game-engine or existing graphs; provider detection; first-token release; new retries/semaphores/cache backends; physical timeout cancellation; token-meter changes; enforcement-infrastructure changes; paid execution without an explicit human limit.

## Revised acceptance criteria

These are the minimum contract for reconsideration, not authorization to implement.

- [ ] AC-01: The committed plan supplies the three-use-case core justification or returns with a separately judged smaller design; hypothetical examples and automatic triggers do not inflate demand. Rejected memo precedent remains explicitly distinguished.
- [ ] AC-02: A provider-free compiled graph proves item 0's wrapped outcome commits before any later worker starts, in both `invoke` and `ainvoke`; successful subgraph warming waits for the entire child graph.
- [ ] AC-03: Remaining workers genuinely overlap; configured width 2 caps the release wave at 2 in flight. Synchronization has bounded waits and cannot deadlock the test process.
- [ ] AC-04: Both waves execute exactly the capped dispatch-time population once, with the original shared worker inputs. Collect-as-over and common-input witnesses pass; re-entry uses a fresh snapshot/token.
- [ ] AC-05: Deterministic results, typed failure semantics and verdict policy/counts/met match ordinary map after only documented identity normalization. All accounting indices and token attribution are asserted, not discarded.
- [ ] AC-06: Warm exception, tolerated skip and wrapper timeout each release remaining items and preserve their distinct accounting semantics. Strict and partial thresholds behave as declared, with the verdict committed before an unmet join raises.
- [ ] AC-07: Empty and singleton populations emit no release Sends, follow existing completeness semantics and reach account/join exactly once; warm and release indices together are exactly `0..N-1`.
- [ ] AC-08: Load/schema/lint, inferred/generated state, cap/overflow handling, join-owned outgoing edges, map-to-map-like composition and diagnostic identities obey the revised contract.
- [ ] AC-09: Under a recorded human spend ceiling, the fixed four-item warm-first live witness satisfies R-5's positive-write/read gate. Raw per-call records, provider/model, command, concurrency, prefix evidence and counts are committed; the ordinary-map control is recorded without requiring a race.
- [ ] AC-10: The governed demo has a substantive authoring report, passes lint and records a real bounded `--token-usage` run. Missing credentials or skipped execution are recorded as unmet evidence, never completion.
- [ ] AC-11: Reference documentation explains ordering-only semantics, cache eligibility and timeout limitations; capability/REQ allocation, marked tests, generated architecture, example index and feature fragment are consistent.
- [ ] AC-12: Exact targeted new/existing map-suite commands, Ruff/format, import boundaries and strict requirement coverage pass on the identified candidate. The FR records status, decisions and deviations; the diary contains the required reflection and `Seed:`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| GATE-1 | No implementation authority. Folding revisions does not turn REJECTED into approval; independently judge the revised committed plan before editing production code or authoring the demo. | GATE |
| GATE-2 | Resolve core classification using actual evidence and the explicit standalone-node product decision; do not fabricate demand or silently substitute another architecture. | GATE |
| GATE-3 | Freeze dispatch-time population/input transport, logical timeout completion and comparison/diagnostic contracts before implementation. | GATE |
| GATE-4 | Record the human paid-call ceiling before any live witness/demo; this judge authorizes no provider spend. | GATE |
| GATE-5 | Any later authorized implementation must preserve ordinary map behavior, use RED/GREEN witnesses and the graph-authoring route, and leave unsuccessful live evidence visibly unmet. | GATE |

Authority granted: none; the measured optimization is worth pursuing, but the present standalone core-node plan must return to planning.

---

# Round 2 Judgement: FR-1161 `cached_map` Node: Warm-First Map Dispatch for Prompt Caching

**Verdict:** REJECTED — The revised plan substantially repairs the scheduling contract, but the standalone primitive still fails the doctrine's demand threshold, snapshot serialization changes worker input types, and the tolerated-skip witness contradicts map completeness semantics.

**Reviewed against:** Committed inputs at `c0f94cee65bfb9d8af3b8d2882e6b43d5e601ca9`:

- `feature-requests/FR-1161-cached-map-warm-first.md`, entire file.
- `feature-requests/FR-1161-cached-map-warm-first.judgement.md`, entire file.
- `feature-requests/FR-1155.research.md`, entire file.
- `feature-requests/FR-1155-prompt-cache-tokens-in-token-usage.md`, lines 1-240.
- `feature-requests/FR-1158-cached-map-node.judgement.md`, entire file.
- `feature-requests/FR-1159-map-memo-contrib.md`, lines 1-190.
- `feature-requests/FR-1073-map-result-contract.md`, lines 1-200.
- `feature-requests/FR-984-map-fan-out-max-concurrency.md`, lines 1-145.
- `feature-requests/FR-1055-anthropic-prompt-cache-blocks-never-reach-api.md`, lines 1-115.
- `feature-requests/FR-111-compiled-graph-cache.md`, lines 1-100.
- `yamlgraph/compile/map_compiler.py`, lines 1-330.
- `yamlgraph/compile/map_contract.py`, entire file.
- `yamlgraph/models/map_results.py`, entire file.
- `yamlgraph/models/state_builder.py` and `yamlgraph/models/state_codegen.py`, map-channel search excerpts only.
- `.github/skills/judge-fr/doctrine.md` and `.github/skills/judge-fr/judgement.template.md`, entire files.
- Repository doctrine supplied from `.github/copilot-instructions.md` and `CLAUDE.md`.

The FR, research record and promoted first judgement match HEAD. No author transcript, working notes, external consumer checkout or dirty adapter content was consumed. The game-engine workloads and operator decisions are evaluated as committed FR assertions. This artifact is a draft only; it neither promotes another verdict nor changes the FR's status.

## What is sound

The strongest case **against** shipping is that a new public compiler primitive with broad registration/state obligations serves two prompts in one consumer repository, one of which has no measured eligible cache prefix. A smaller map option remains a deferred alternative, not a disproven one (`FR-1161:112-132,427-434`). The strongest case **for** the mechanism is equally concrete: the measured warm-first variant reduces eight writes to one while retaining most parallelism (`FR-1155.research.md:78-97`). This is a real scheduling optimization, not result memoization.

The revision now specifies dispatch-time population/common-input ownership, snapshot cleanup, sequential re-entry, settled timeout outcomes, diagnostic names and normalized deterministic parity (`FR-1161:207-280`). These address most of the first judgement's technical objections. Separate supersteps avoid waiting branches occupying fan-out slots. The live gate no longer depends on forcing an ordinary-map provider race; a positive warm write, fixed thresholds, distinct nonces and a recorded $1/three-run ceiling are sound (`FR-1161:359-384`). No new paid authorization is inferred by this judge.

| Rubric criterion | Assessment |
|---|---|
| 1. Scope | One scheduling concern, with supporting documentation/demo/tests. The standalone public node remains larger than the deferred map option on the current demand evidence (`FR-1161:103-132,427-434`). |
| 2. Consistency | Not satisfied: recursively dumping arbitrary snapshot values conflicts with unchanged worker inputs; the strict-threshold failure assertion also includes tolerated skips (`FR-1161:238-248,324-328`). |
| 3. Measurability | Ordering, release width, exact indices, re-entry and live cache thresholds are mechanically checkable. Fix the contradictory outcome expectations before they become acceptance assertions (`FR-1161:313-384`). |
| 4. Feasibility | The existing wrapped worker and account/join factories support the topology. `merge_map_open` can carry records with a dispatch key, but the proposed snapshot dump does not preserve the plain map's arbitrary Python input values (`map_results.py:72-84`; `map_contract.py:160-170`). |
| 5. Architecture alignment | Compiler-owned Send wiring and shared worker construction align. Typed transport must validate the envelope without silently converting contained model values into dictionaries (`FR-1161:186-205,238-248`). |
| 6. Single responsibility | One cohesive ordering feature; registration, witnesses and the example support it. No SPLIT is warranted. |
| 7. Strategic classification | **Contrib/example on evidenced demand**, with a compiler integration gap, not a qualifying framework primitive. The FR explicitly admits fewer than three use cases (`FR-1161:112-123`; judge doctrine:51-55). This classification does not authorize a plugin or an unusable contrib implementation. |
| 8. Testability | Most tests are directly derivable. Add a model-valued input parity witness and correct the tolerated-skip truth table; otherwise tests either miss an input-boundary regression or demand a change to existing policy (`FR-1161:324-341`; `map_results.py:97-107`). |

The research gate is satisfied: committed measured evidence, substantive alternatives and the `is_this_a_graph` answer exist (`FR-1161:21-26,423-434`). This is scheduling, not new measurement tooling; the measurement-tooling pre-authority raw-sample gate does not apply. Rejected memo precedent is explicitly distinguished rather than resurrected (`FR-1161:30-39`).

## Required revisions

These are return-to-plan requirements, not conditional implementation authority.

### R-1: Resolve the standalone primitive's unmet classification requirement

Retain the honest two-workload table and the operator's standalone-first decision. The product question from the first judgement has been answered; do not ask it again or manufacture another consumer.

However, a committed product override does not amend the governing judge rubric, which requires three or more use cases for a framework primitive (`judge-fr/doctrine.md:51-55`). The FR itself acknowledges that threshold is unmet (`FR-1161:121-132`). Return with either committed evidence meeting that requirement or a smaller, separately judged extension of the existing map abstraction. Do not silently substitute contrib packaging or invent a plugin.

If the operator intends to change the governance rule rather than the design, that requires a separate explicit doctrine change with human review; it is not authorized by this FR. Recording the override is useful decision provenance, but is not evidence that the present proposal satisfies the current rule.

### R-2: Preserve Python value types across the snapshot boundary

Replace the unconditional `CachedMapSnapshot.model_dump()` transport at `FR-1161:238-248` with a typed snapshot envelope whose contained `items` and `inputs` retain their Python values through dispatch and release. A shallow field mapping of the validated envelope is sufficient; do not recursively serialize the contents as a new scheduling requirement.

Pydantic's recursive dump converts nested model instances into dictionaries even inside `Any` containers. Ordinary map passes those values through unchanged (`map_contract.py:160-170`). Thus an existing Python worker reading `state["item"].name`, or a model-valued common input through attribute access, can succeed under `map` and fail under this design. Applying the same conversion to both waves makes the waves consistent with each other, not with ordinary map.

Add a provider-free compiled comparison using an existing supported Pydantic item type and a Pydantic common input. The worker must access their attributes and assert their concrete types in both warm and release calls. Compare deterministic outputs with ordinary map, normalizing only dispatch identity. Retain the collect-as-over, common-input and re-entry witnesses. Preserve existing checkpoint serialization support; no new general serializer, object-format restriction or deep-copy subsystem is requested.

### R-3: Correct the warm-outcome completeness truth table

Replace unit test 4's blanket assertion that `min_success: 1.0` fails for every parameter (`FR-1161:324-328`). Use N = 4, item 0 as the parameterized outcome, and three successful release workers:

- Exception or wrapper timeout: `succeeded=3`, `tolerated=0`, `failed=1`, `accepted=3`; fraction `1.0` is unmet and fraction `0.5` is met.
- Tolerated skip: `succeeded=3`, `tolerated=1`, `failed=0`, `accepted=4`; both fractions are met.

In every case assert release, indices exactly `0..3`, one token, the committed verdict and snapshot closure. For unmet policy, assert that the later join raises only after accounting commits. Keep bounded timeout cleanup.

This is existing policy, not a new exception: `accepted = succeeded + tolerated` (`FR-1073:183-194`; `map_results.py:97-107`). Do not change `compute_verdict` to make the mistaken witness pass.

## Scope is frozen

No implementation scope is granted by this rejected draft.

| Deliverable | Surface |
|---|---|
| D-1: Draft judgement | `tmp/draft-judgement-copilot-FR-1161-cached-map-warm-first.md` only |
| Candidate scheduling mechanism, not authorized | Dispatch snapshot, warm item 0, release remaining original indices, account once, enforce at join |
| Candidate supporting artifacts, not authorized | Focused offline/live witnesses, governed demo, reference, capability/REQ, generated architecture and changelog |
| Return-to-plan work | Committed design/evidence addressing R-1 through R-3; not performed by this judge |

Not authorized: core `cached_map` implementation; an unjudged map option or automatic mode; plugin infrastructure; result memoization; consumer migrations; provider inspection; first-token release; physical timeout cancellation; token-meter changes; general serialization tooling; enforcement/doctrine edits; changes to ordinary-map outcome arithmetic.

## Revised acceptance criteria

These are the minimum contract for reconsideration, not authorization to implement.

- [ ] AC-01: The committed plan meets the framework-primitive demand requirement or supplies a separately judged smaller design; hypothetical demonstrations and redo variants do not inflate demand.
- [ ] AC-02: Load/schema/lint, inferred/generated state, failure channels and published-schema validation recognize the authorized design consistently.
- [ ] AC-03: In sync and async invocation, successful item 0 commits before any later worker starts; successful subgraph warming waits for the entire child graph.
- [ ] AC-04: Release workers overlap, and invoke-level concurrency 2 caps their peak at 2; synchronization is bounded.
- [ ] AC-05: Both waves use exactly the capped dispatch-time items and common inputs. Collect-as-over, model-valued items/common inputs and common-input isolation pass without type conversion; re-entry uses fresh tokens/snapshots.
- [ ] AC-06: Equivalent deterministic outcomes match ordinary map's ordered results, failure semantics and verdict policy/counts/met after only documented identity normalization. All indices and token attribution remain checked.
- [ ] AC-07: N = 4 warm exception/timeout and tolerated-skip cases satisfy R-3's distinct truth table, release all remaining items, close the snapshot during accounting and commit the verdict before any unmet join raises.
- [ ] AC-08: Empty/singleton populations, subgraph order, topology/diagnostic names, overflow before any worker, and both map/cached-map composition directions obey the declared contract.
- [ ] AC-09: The fixed live witness uses the recorded model, N = 4, width 4, distinct cold nonces and positive P; warm reads are zero, writes total `[P, 1.5 P]` and reads total at least `2.5 P`. Raw records are read and explained before reporting the aggregate verdict; the ordinary-map race is context only.
- [ ] AC-10: All paid attempts, including the demo and retries, stay within $1 and three runs. Missing credentials, an exhausted ceiling or a skip leave the relevant live criteria unmet.
- [ ] AC-11: The demo follows the authoring route, has a substantive report, lints and records real cache-read/write output. Reference documentation includes snapshot/type semantics, timeout overlap, parity limits and cache eligibility; registry/REQ, generated architecture, index and feature fragment are consistent.
- [ ] AC-12: The FR's named focused/new and existing map suites, clean CI-mirror unit run, Ruff/format, import boundaries and strict requirement coverage pass on the identified candidate. The FR records status/decisions/deviations; a diary entry includes a `Seed:`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| GATE-1 | No implementation authority. Folding these revisions does not convert REJECTED into approval. | GATE |
| GATE-2 | Resolve strategic classification under the governing doctrine; a recorded product preference is not an implicit doctrine amendment. | GATE |
| GATE-3 | Freeze type-preserving snapshot transport and the corrected tolerated-skip truth table before implementation. Preserve ordinary-map behavior and verdict arithmetic. | GATE |
| GATE-4 | Respect the recorded combined paid-run ceiling and the graph-authoring route. Failed or unavailable live evidence remains visibly unmet. | GATE |
| GATE-5 | Do not overwrite or promote judgement history here. If promotion produces two verdict lines in the canonical judgement, the FR-1022 round sentinel applies; this draft does not grant another round or an override. | GATE |

Authority granted: none; return to planning with the demand/classification conflict and the two concrete contract defects resolved.
