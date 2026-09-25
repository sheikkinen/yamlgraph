# Feature Request: Map result contract — failures apart from results, completeness checked after the branches

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 1.5 days
**Requested:** 2026-09-25
**First consumer / first event:** the next
`examples/demos/innovation_matrix/pipeline.yaml` run: on 2026-09-24 four of
25 branches timed out and `synthesize` ranked "top 5 of 25" from 21 results
plus four stringified `PipelineError` reprs, exit 0. Then
`examples/demos/corpus_census/tools.py`, which filters `_error` rows out of
`collect` by hand.
**Research:** [FR-1073.research.md](FR-1073.research.md) — promoted output of
`scripts/research.sh feature-requests/research-briefs/map-result-contract-brief.md`
(2026-09-25, five personas, 0 failed, 3 classes). Three further classes added
by the FR author are marked as such in the disposition table below. Incident
record: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §1, §2 D1–D3,
§4.1 and appendix.
**Prior art:**
[FR-1064](FR-1064-map-branch-contract.md) (SPLIT) — this FR is its map-result
half (judgement R-1); the retry half is a separate FR and FR-957's status is
not touched here.
[FR-957](FR-957-map-branch-native-retry-policy.md) (judged, not enforced) —
lets branch exceptions reach LangGraph; the §4.1 witness shows finished
branches are lost when one of several concurrent branches raises. Rejected
below as the subtractionist row.
[FR-985](FR-985-census-coverage-floor-and-population-header.md) (Shelved) —
its evidence is that census *briefs* tolerated 57–92% coverage; per FR-1064
judgement R-2 that does not license silent partial output for every consumer.
This FR makes partial success a per-map declaration instead of a default.
[FR-408](FR-408-runtime-repair-metadata.md) (Rejected) — rejected a repair
registry and threshold relaxation; this FR adds no repair actions and never
lowers a declared threshold.
[FR-677](FR-677-verification-first-class-dsl.md) (Done) — graph-level opt-in
`verify:`; dispositioned below as a class.
[FR-944](FR-944-map-to-map-index-attribution.md) — synthetic join-node
precedent (`_map_join_<from>_<to>`, `edge_compiler.py#L222-L236`).
[FR-983](FR-983-map-concurrency-and-census-coverage-gate.md) (Judged, parent
of FR-984/FR-985) — cited by three research rows as the coverage-gate
pattern.
[FR-936](FR-936-map-node-hardening.md) (SPLIT) — FR-939, FR-955, FR-956 stay
outside this FR.

## Summary

A map writes successful results to `collect`, one typed failure record per
failed item to a separate channel, and a verdict after all branches finish.
Unless the map declares how much partial success it accepts, any failure
raises after the branches finish, with the finished results kept in the
checkpoint.

## Value Statement

A prompt or reducer downstream of a map never receives error text as
content, and never receives an incomplete set the graph author did not
declare acceptable.

## Problem

- **D1.** A failed branch becomes `{_map_index, _error}` in `collect`; three
  error paths produce three shapes (one lacks `_error_type`); all record
  `node="map_subnode"`.
- **D2.** `on_error: fail` on a sub-node is caught and returned as data.
- **D3.** 26 in-graph consumers read map output; 13 render it into prompts.
- The error check tests key presence (`"errors" in result`,
  `map_compiler.py#L193`), so a success carrying `errors: []` is a failure.
- No node runs after the branches (`sub_node → target`), and the edge
  function (`map_compiler.py#L335-L366`) cannot write state, so the
  dispatched set is recorded nowhere.

## Ideal Result

After a map, `collect` holds exactly the successful results, `failures` one
record per failed item, and `_map_verdict.<name>` says whether every
dispatched item is accounted for and whether the declared policy was met.
A graph that declared no partial-success policy never continues past a map
with a failed item.

## Proposed Solution

```yaml
judge_items:
  type: map
  over: "{state.items}"
  as: item
  key: "{state.item.id}"            # optional; default _map_index
  node: { type: llm, prompt: judge_item, state_key: judgement }
  collect: judgements               # successes only
  failures: judgement_failures      # optional; default "<collect>_failures"
  min_success: 0.98                 # optional; count or fraction; absent = 1.0
```

1. **Dispatch record in the `Send` payload.** The edge cannot write state,
   so each `Send` carries `_map_name`, `_map_dispatch` (a fresh id per edge
   call), `_map_dispatched` (the count), `_map_index` and `_map_key`. The join
   never re-resolves `over`; a branch that mutates what `over` depends on
   cannot change the dispatched set (FR-1064 judgement R-3). Duplicate keys
   raise in the edge, naming both indices.
2. **Bookkeeping channel.** Every branch, success or failure, appends
   `{map, dispatch, index}` plus `ok` to a private reducer channel
   `_map_accounting`. `collect` keeps only content (plus today's
   `_map_index`), so prompts see no bookkeeping fields.
3. **Failure record.** One helper builds
   `{_map_index, key, error_type, message, node}` with the real sub-node name
   for all three error paths and writes it to `failures` and `state.errors`.
   The presence check becomes "non-empty `errors`". A sub-node update with
   `_skipped: True` (`llm_execution.handle_error`, SKIP branch) is a
   tolerated failure: recorded in `failures`, not in `state.errors`.
4. **Join node** `_map_{name}_join`, wired `sub_node → join → target`
   (FR-944 precedent). For map-to-map edges the FR-944 barrier join moves
   behind it: `sub_node → _map_{name}_join → _map_join_<from>_<to>`. It selects `_map_accounting` rows with its own
   `map` and the latest `dispatch`, and asserts the index set is exactly
   `0..dispatched-1` with no repeats — identity, not count; two maps sharing
   a `collect` channel and a map re-run in a loop are distinguished by
   `map` and `dispatch`. A mismatch raises (framework defect). It writes
   `_map_verdict.<name> = {dispatched, succeeded, failed, tolerated,
   min_success, met}`.
5. **Policy.** `min_success` absent means 1.0: any non-tolerated failure
   raises `MapCompletenessError` at the join, after every branch finished;
   the checkpoint keeps the finished branches. Declared `min_success` met:
   the run continues and downstream nodes can read `failures` and the
   verdict. Sub-node `on_error: skip` failures count as successes for the
   threshold (the author tolerated them). `on_error: fail` on the map is
   `min_success: 1.0`.
6. **Zero items.** The edge routes straight to the join, which writes a
   verdict with `dispatched=0`.
7. **Migration.** `corpus_census/tools.py` reads `failures`. Every map in the
   repository whose graph expects partial success gets an explicit
   `min_success` (census committed with the change).

Out of scope: retry ownership (separate FR from FR-1064 R-1), resume
(FR-1065), overflow (FR-939), input projection (FR-955), timeout threads
(FR-956).

## Acceptance Criteria

- [ ] RED 1 (D2): a Python sub-node raising under `on_error: fail`, three items → no `collect` entry for it, one failure record naming the sub-node, `MapCompletenessError` at the join, the two finished results present in the checkpoint.
- [ ] RED 2: all three error paths produce the identical failure record shape.
- [ ] RED 3: a success whose update contains `errors: []` is collected.
- [ ] RED 4: 100 items, one permanent failure, `min_success: 0.98` → `collect` 99, `failures` 1, verdict `dispatched=100 succeeded=99 failed=1 met=true`, run continues.
- [ ] RED 5: a branch that changes the state `over` reads → the join's dispatched set is unchanged.
- [ ] RED 6: two maps writing one `collect` channel, and one map run twice in a loop → each join accounts only its own dispatch.
- [ ] Zero items → join runs, verdict `dispatched=0`.
- [ ] Map-to-map (FR-944 fixture) still fires the downstream fan-out once.
- [ ] Duplicate keys raise before any branch runs.
- [ ] `on_error: skip` sub-node failure → in `failures`, not in `state.errors`, counted as tolerated.
- [ ] No graph in the repository reads `_error` from a map `collect` (grep witness); the census of maps given an explicit `min_success` is listed in this FR.
- [ ] `innovation_matrix` rerun: `synthesize` input contains no error text (raw output read and quoted).
- [ ] New REQ IDs in `ARCHITECTURE.md`, tests tagged; `reference/graph-yaml.md` documents `key`, `failures`, `min_success` and the verdict.

## Alternatives Considered

Rows 1–5 are the research route's; rows 6–8 are added by the FR author.

| # | Class | Alternative | Disposition |
|---|---|---|---|
| 1 | process-boundary | Wrap each branch so it catches exceptions and writes result and dispatch count to separate channels (os-infra) | **Adopted in part.** The catching wrapper is today's `wrap_for_reducer`; the new part is separate channels (items 2–3). Its claim that the dispatch count can be written by the wrapper is covered by item 1. |
| 2 | schema-data | Record dispatched count and identity before branches run; fail if the count differs (data-process) | **Adopted.** It ignores that the edge cannot write state; item 1 carries the record in the `Send` payload instead. Identity, not count (item 4). |
| 3 | schema-data | `_dispatched_count` in state; each downstream node asserts `len(results) == count` (yamlgraph-native) | **Rejected:** assertion in 26 consumers is `downstream_fix`. Its "optional at first" is the status quo. |
| 4 | process-boundary | Delete the wrapper's catching; let LangGraph's step-level recovery keep finished branches (subtractionist) | **Rejected, contradicted by witness.** §4.1: with ≥2 concurrent branches one raise loses all finished results; this is FR-957's disproved design. Preserved as dissent: it would remove the most code if LangGraph changes. |
| 5 | external-method | AWS Lambda partial batch response: per-item failure list plus summary (librarian, [AWS docs](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html)) | **Adopted as precedent** for `failures` + verdict. Differs: Lambda re-delivers failed items; here re-run is FR-1065's concern. |
| 6 | graph-pipeline (author) | Each graph opts in to FR-677 `verify: check: "state.errors \| length == 0"` | **Rejected:** opt-in; zero census graphs use it; passes partial output until the end of the run. |
| 7 | boundary-enforcement (author) | Keep "record and continue" as default; lint warns when a node reads `collect` without reading `failures` | **Dissent preserved.** Keeps census runs cheap by default, but a lint warning is advisory and the innovation_matrix incident is exactly the unread case. FR-1064 judgement R-2 named it as one of two acceptable forms. |
| 8 | subtraction (author) | Status quo plus documentation that `_error` rows exist | **Rejected:** Commandment 6; the plausible wrong answer is the witnessed failure. |

**is_this_a_graph:** no. This is map compilation semantics in
`yamlgraph/compile/`; graphs express only the policy (`min_success`). Two
research rows answered "yes" meaning "the map is a DAG", not that a graph
should implement the fix.

### Questions for the judge

Operator preference (2026-09-25): strict default now, with the migration
census; the judge decides.

- The strict default changes behavior for every existing map whose graph
  currently tolerates failed branches silently. The migration (item 7) sets
  `min_success` explicitly where partial success is intended. Is that census
  enough, or must the strict default wait for FR-1065 (reuse makes a re-run
  cheap)?

## Related

- Research brief: [research-briefs/map-result-contract-brief.md](research-briefs/map-result-contract-brief.md)
- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §7 A
- Consumed by: [FR-1065](FR-1065-resumable-map-investigation.md) (item key, failures), a refiled FR-1066 (exit code), a refiled FR-1070 (innovation_matrix)
