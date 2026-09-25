# Judgement: FR-1064 Map branch contract

**Prior art:** `FR-1064-map-branch-contract.md` is the FR this judgement governs; its own prior-art line dispositions FR-957, FR-936, FR-985, FR-408 (Rejected) and FR-031. FR-836, FR-839 (Rejected), FR-840 and FR-844 match only on "contract"; they govern GitClaw output, ownership, authority and instructions, not map results.

**Verdict:** SPLIT — map result/failure semantics and provider-wide retry ownership are independent contracts; neither is authorized by this combined FR.

**Reviewed against:** `feature-requests/FR-1064-map-branch-contract.md`; `feature-requests/FR-957-map-branch-native-retry-policy.md`; `feature-requests/FR-936-map-node-hardening.judgement.md`; `feature-requests/FR-985-census-coverage-floor-and-population-header.md`; `docs/issues-2026-09-24.md`; `yamlgraph/compile/map_compiler.py`; `yamlgraph/cli/graph_commands.py`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The multi-branch witness disproves FR-957's final `error_handler` disposition (plan section 4.1). The existing wrapper turns exceptions and error-bearing updates into `collect` rows, including a false positive for `errors: []` (`yamlgraph/compile/map_compiler.py:142-202`). Keeping errors out of the result channel and asserting dispatched equals accounted-for are framework-primitive corrections used by existing map consumers (FR-1064:29-50; plan section 2 D1-D3). RED 1-4 name discriminating behavior (FR-1064:138-146).

## Required revisions

### R-1: File separate map-result and retry-ownership FRs

Put item key, typed failure channel, completeness and threshold verdict in one map FR; put SDK `max_retries`, provider mappings, 429 `Retry-After`, timeout classification, executor loop and node-handler changes in a separate retry FR. The SDK change explicitly affects *every* LLM call (FR-1064:105-120), whereas map failure separation can be tested with Python sub-nodes alone. Do not transfer FR-957's supersession status until the new retry FR is judged; its concurrent-handler defect is evidence, not authorization to alter unrelated callers.

### R-2: Make the default safe for downstream consumers

The map FR must define what a downstream consumer sees after any failure when `min_success` is absent. `collect` alone silently represents 21 of 25 as a complete set (plan section 7 A.4; FR-1064:87-99, 167-170). Require a declared acknowledgement of failure/partial coverage at each consumer, or make the join refuse downstream execution until a declared partial-success policy exists; test both default and explicit partial-success paths. FR-985's shelved *census brief floor* does not establish that every map consumer may silently consume incomplete output (FR-985:5-12).

### R-3: Define dispatch accounting and duplicate handling

Specify how the join gets the original dispatched item count when `over` depends on state mutated by branches; re-resolving merged state (FR-1064:91-94) is not necessarily equivalent to the fan-out snapshot. Specify behavior for zero items, duplicate keys, multiple maps collecting into the same channel and concurrent map invocations. Add RED tests with a branch that changes an `over` dependency and with two maps sharing a collect channel. Count equality alone cannot prove identity-completeness (plan section 6.5).

### R-4: Supply independent committed research and witnesses

Each replacement must meet the FR-890 research gate: four to six genuine solution classes for its own problem, cited precedent (including rejected FR-408 and FR-957 where relevant), preserved dissent, and `is_this_a_graph`. FR-1064:154-163 lists rejected tactics across two different concerns without that record. Retry tests must establish attempt counts on actual supported provider exception types before selecting a global mapping (FR-1064:127-145). Keep FR-939, FR-955 and FR-956 outside both replacements (FR-936 judgement R-1).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | New researched map-result/failure-contract FR |
| D-2 | New researched provider/executor retry-ownership FR |
| D-3 | FR-1064 split disposition and FR-957 conflict record |

Not authorized: changes to `yamlgraph/compile/map_compiler.py`, `yamlgraph/executor.py`, provider clients, schemas, map consumers, demos, or FR-957 implementation under FR-1064.

## Revised acceptance criteria

- [ ] AC-01: Two new FRs have independent research, acceptance tests, scopes and judgements.
- [ ] AC-02: Map FR RED fixtures distinguish missing branches, `errors: []`, zero items, state-mutated `over`, duplicate keys and an unacknowledged partial result reaching a consumer.
- [ ] AC-03: Retry FR records per-layer calls on a real supported provider exception shape and asserts timeout and non-map behavior separately.
- [ ] AC-04: FR-957's invalid concurrent-handler design is explicitly dispositioned without silently granting this FR its former authority.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No implementation under FR-1064; judge each successor independently. | GATE |
| C-2 | Do not alter all provider calls to implement a map-only failure channel. | GATE |
| C-3 | Do not feed incomplete successes to an unacknowledging downstream consumer by default. | GATE |

Authority granted: none; only the two separate proposals may re-enter judgement.
