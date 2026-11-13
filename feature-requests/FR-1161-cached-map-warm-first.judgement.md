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
