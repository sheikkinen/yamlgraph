# Feature Request: Map result contract — failures apart from results, completeness checked after the branches

**Priority:** HIGH
**Type:** Bug
**Status:** Judged — APPROVED WITH REVISIONS ([judgement](FR-1073-map-result-contract.judgement.md)); R-1–R-6 folded 2026-09-25 (see [Revision fold](#revision-fold)). **Authority active (2026-09-25):** operator accepted H-1–H-4 in [Migration census](#migration-census) and the fold as written, satisfying judgement C-1 and C-5. **Operator ruling (2026-09-25): "no splits or bloat".** One PR. Cut: `key` and the duplicate-key check (AC-03 and the `key` half of AC-01; no consumer until FR-1065), and the H-4 live rerun. All graph edits go through one authoring brief. **Implemented 2026-09-25** — see [Implementation](#implementation-2026-09-25).
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
- Raw record, `examples/demos/fi_domain_crawl/demo-output.log` line 60:
  all 10 `crawl_results` rows are `_error` rows; nine read
  `'_error': 'None'`. `crawl_page` returns `"error": None` on success
  (`nodes/crawl_page.py#L96`) and the wrapper tests key presence, so nine
  successful crawls were replaced by the string `None` and rendered into
  the `summarise` prompt; one real 403 was indistinguishable from them.
- Two consumers turn a failed branch into a plausible verdict:
  `ramp_incidents/nodes/incident_tools.py#L189` writes
  `verdict: not_an_incident`, and
  `salvage_classify/nodes/salvage_tools.py#L231` writes
  `verdict: obsolete` with the error text as the rationale.
- A map-level `on_error` is accepted by `NodeConfig` and read by nothing
  (`map_compiler.py` never reads it); eight maps declare one (census rows
  2, 5–7, 10, 50, 53, 59). A python sub-node's `on_error` is also unread:
  `load_python_function` returns the bare function, so the wrapper's catch
  is the only handler.

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
  min_success: 0.98                 # optional; int count or float fraction in [0, 1]; absent = 1.0
```

1. **Dispatch node (R-1).** The edge function cannot write state, so the
   map's own node `<name>` becomes a dispatch node. It resolves `over`,
   applies `max_items`, resolves every key, raises on a duplicate key
   (naming map, key and both indices) and writes
   `_map_open.<name> = {dispatch, dispatched, keys}`, where `dispatch` is a
   fresh `uuid4().hex`. The conditional edge after it reads only that
   record and emits one `Send` per item carrying `_map_name`,
   `_map_dispatch`, `_map_index` and `_map_key`; with zero items it routes
   to the join. The join reads the exact token from `_map_open.<name>`;
   nothing selects a "latest" token. A branch that mutates what `over` reads
   cannot change the dispatched set.
   *Deviation from the filed item 1 (payload only):* the judgement requires
   the join to receive the exact token, and only a node can write it to
   state. The `Send` payload still carries it so each accounting row is
   attributed.
2. **Overlap (R-1).** `_map_open` merges per map name. Its reducer raises
   `MapAccountingError`, naming the map and both tokens, when a token
   arrives while the same map's record is still open; the join closes the
   record by writing `None`. This catches overlap within one superstep and
   across supersteps, before either join publishes a verdict. Different map
   names never conflict. A sequential loop opens a new token only after the
   previous join closed; old accounting rows carry the old token and are
   never selected.
3. **Branch outcome (R-3).** One helper in the wrapper classifies every
   branch:
   - *failure*: the sub-node raised or timed out, or its update has a truthy
     `errors` or a truthy `error`. Today the check is key presence; this
     fixes the `fi_domain_crawl` `error: None` case and `errors: []`.
   - *tolerated failure*: the update has `_skipped: True`. That covers an
     LLM sub-node with `on_error: skip` after its final attempt
     (`llm_execution.py#L136-L145`) and guard skips (`llm_nodes.py#L209`,
     `copilot_node.py#L309`). A timeout caught by the wrapper is never
     tolerated, because the sub-node's `on_error` never saw it.
   - *success*: otherwise.

   Every branch appends one `MapAccounting` row. A success appends its
   content to `collect`, keeping today's `_map_index`. A failure appends
   one `MapFailure` to `failures`. A non-tolerated failure also appends
   exactly one `PipelineError` with `node=_map_<name>_sub` to
   `state.errors`. A tolerated failure appends none, and the sub-node's own
   `errors` entry is dropped.
4. **Typed records (R-3).**
   - `MapFailure {map, dispatch, _map_index, key, error_type, message, node, tolerated}`
   - `MapAccounting {map, dispatch, dispatched, _map_index, key, outcome}`, with `outcome` one of `succeeded | tolerated | failed`
   - `MapVerdict {dispatch, dispatched, succeeded, tolerated, failed, accepted, min_success, met}`
   - `MapCompletenessError` and `MapAccountingError`

   `state.errors` stays `list[PipelineError]`.
5. **State and reducers (R-3).**
   - `collect` and `failures` are append lists. A shared channel keeps the
     map and dispatch attribution on every record.
   - `_map_accounting` is an append list of typed rows.
   - `_map_open` and `_map_verdict` are dicts keyed by map name and merged
     per key, not `last_value`. `_map_verdict.<name>` is written only by
     that map's join.
   - `failures` must be a non-empty state key that differs from `collect`
     and from the reserved keys (`errors`, `current_step`, `_loop_counts`,
     `_map_*`). It defaults to `<collect>_failures`.
   - Schema and state code generation produce all four channels.
6. **Join (R-2, R-4).** `_map_<name>_join` does the following in order:
   - reads `_map_open.<name>`;
   - selects the accounting rows carrying that exact token;
   - checks that the indices are exactly `0..dispatched-1` with no repeats
     and that the keys match, and raises `MapAccountingError` otherwise;
   - writes `_map_verdict.<name>` and closes `_map_open.<name>`;
   - raises `MapCompletenessError` if `met` is false.

   The checkpoint keeps the finished branches.
7. **Policy (R-2).**
   - *Type:* `min_success: int | float | None`. Booleans, strings,
     non-finite floats, negative integers and floats outside `[0.0, 1.0]`
     fail at load, with a message naming the map, the field and the value.
     YAML `1` means one accepted item; `1.0` means all of them. An integer
     larger than `dispatched` is valid but unmet.
   - *Terms:* `succeeded` counts real `collect` entries, `tolerated` counts
     `_skipped` failures and `failed` counts every other failure.
     `accepted = succeeded + tolerated` and
     `dispatched = succeeded + tolerated + failed`.
   - *Arithmetic:* for an integer, `met = accepted >= min_success`. For a
     fraction, `met = accepted / dispatched >= min_success`. An absent
     value means fraction `1.0`.
   - *Zero items:* every count is 0, `min_success` is as declared (or
     `1.0`) and `met` is `true`, with no division.
   - *Ownership:* `min_success` is the only map-result policy; the nested
     `node.on_error` owns branch disposition. A map-level `on_error` stays
     unread, as today, and gets no meaning here. Rejecting it at load is
     refused in this FR: D-1 names `key`, `failures` and `min_success`
     only, so the judgement did not authorize that schema change.
8. **Topology (R-4).**
   - Each map compiles three nodes: `<name>` (dispatch),
     `_map_<name>_sub` and `_map_<name>_join`. A collision with any other
     node name fails compilation, naming the map and the conflicting node.
   - Incoming edges keep targeting `<name>`. Its conditional edge sends to
     the sub-node, or straight to the join when there are zero items.
   - The sub-node's only outgoing edge goes to the join. Every edge that
     used to leave the sub-node now leaves the join.
   - Map-to-map runs upstream sub → upstream join → FR-944 barrier
     `_map_join_<from>_<to>` → downstream dispatch → downstream sub, and
     the downstream map fans out once.
   - START → map, node → map, map → END, map → node and loop-back → map
     keep their destinations; the only change is the inserted nodes.
   - The compiler's map metadata carries all three names. Today it carries
     `(map_edge_fn, sub_node_name)` (`edge_compiler.py#L221-L249`).
9. **Migration (R-5).** The [Migration census](#migration-census) below.

Out of scope: retry ownership (separate FR from FR-1064 R-1), resume
(FR-1065), overflow (FR-939), input projection (FR-955), timeout threads
(FR-956), CLI exit codes (refiled FR-1066), map-level `on_error` rejection
(item 7).

## Migration census

**Method.**
- Every `examples/**/*.yaml` was parsed with `yaml.safe_load` and every
  node with `type: map` was listed: 67 in total.
- `yamlgraph/`, `graphs/`, `.github/`, `scripts/` and `projects/` contain
  no map nodes.
- `yamlgraph_gen/snippets/nodes/map-basic.yaml` is a placeholder template
  that does not parse. It follows row 66.
- `_error` consumers were found by grepping for `"_error"` in
  `examples/**/*.py` and `yamlgraph/**/*.py`: 22 sites in 16 files. No
  prompt reads `_error`. The only producer is `map_compiler.py#L148-L196`.
- `SkipReport.from_state` has one caller (row 59).
- Tests under `tests/` that assert `_error` rows are rewritten under D-4 and
  are not listed here.

**Disposition key.**
- **strict**: no `min_success`; any non-tolerated failure raises at the
  join.
- **skip → tolerated**: the LLM sub-node's `on_error: skip` makes its
  failures tolerated, so strict still passes when they happen, as the
  author declared.
- **consumer check removed**: under strict the consumer's `_error` branch
  can never run, so it is deleted.
- **consumer reads `failures`**: the consumer keeps its failed-row output
  by reading the failures channel.
- **consumer raises on non-empty `failures`**: the sub-node says skip but
  the consumer raises on `_error` today. The consumer keeps that raise by
  reading `failures`, so behavior is unchanged.

| # | Graph (under `examples/`) | Map | Sub-node type, `on_error` | Map-level `on_error` (unread today) | `_error` consumer today | Disposition |
|---|---|---|---|---|---|---|
| 1 | `abstraction_span/graph.yaml` | score | llm, — | — | `nodes/tools.py#L81` raises | strict; consumer check removed |
| 2 | `batch_image_prompts/graph.yaml` | enrich | llm, — | skip | none; rows flow on | strict; move `on_error: skip` into sub-node (**H-2**) |
| 3 | `book_reviewer/graph.yaml` | chapter_review | llm, — | — | `nodes/tools.py#L441` drops silently | strict; consumer check removed |
| 4 | `book_reviewer/graph.yaml` | continuity | llm, — | — | `nodes/tools.py#L446` drops silently | strict; consumer check removed |
| 5 | `book_translator/graph.yaml` | extract_glossary | llm, — | skip | none; rows flow on | strict; move `on_error: skip` into sub-node (**H-2**) |
| 6 | `book_translator/graph.yaml` | translate_all | llm, — | retry | none; rows flow on | strict; move `on_error: retry` into sub-node (**H-2**) |
| 7 | `book_translator/graph.yaml` | proofread_all | llm, — | skip | none; rows flow on | strict; move `on_error: skip` into sub-node (**H-2**) |
| 8 | `codegen/impl-agent.yaml` | execute_discovery | tool_call, — | — | none; rows flow on | strict |
| 9 | `cwe-classifier/graph.yaml` | classify_clusters | llm, — | — | none; rows flow on | strict |
| 10 | `daily_digest/graph.yaml` | analyze_all | llm, — | skip | none; rows flow on | strict; move `on_error: skip` into sub-node (**H-2**) |
| 11 | `demos/book-summary/graph.yaml` | render_pages | tool_call, retry | — | `tools.py#L156` raises | strict; consumer check removed |
| 12 | `demos/book-summary/graph.yaml` | transcribe_pages | python, retry | — | `tools.py#L202` raises | strict; consumer check removed |
| 13 | `demos/book-summary/graph.yaml` | summarize_pages | llm, retry | — | `tools.py#L60` raises | strict; consumer check removed |
| 14 | `demos/cap_journey_census/graph.yaml` | extract_items | python, fail | — | none; rows flow on | strict |
| 15 | `demos/cap_journey_census/graph.yaml` | judge_items | llm, skip | — | `tools.py#L316` failed ledger row | strict; skip → tolerated; consumer reads `failures` |
| 16 | `demos/chatterbox/graph.yaml` | generate | llm, — | — | none; rows flow on | strict |
| 17 | `demos/chinese-horoscope/graph.yaml` | generate | llm, — | — | none; rows flow on | strict |
| 18 | `demos/corpus_census/graph.yaml` | extract_items | python, fail | — | none; rows flow on | strict |
| 19 | `demos/corpus_census/graph.yaml` | judge_items | llm, skip | — | `tools.py#L243` failed ledger row | strict; skip → tolerated; consumer reads `failures` |
| 20 | `demos/diary_index/graph.yaml` | extract_all | llm, skip | — | none; rows flow on | strict; skip → tolerated |
| 21 | `demos/fi_domain_crawl/graph.yaml` | crawl | python, — | — | none; rows flow on | strict |
| 22 | `demos/file-hook/graph.yaml` | process | tool_call, — | — | none; rows flow on | strict |
| 23 | `demos/fr-atlas/graph.yaml` | theme_chunks | llm, — | — | none; rows flow on | strict |
| 24 | `demos/horoscope/graph.yaml` | generate | llm, — | — | none; rows flow on | strict |
| 25 | `demos/innovation_matrix/pipeline.yaml` | expand_all | llm, — | — | none; rows flow on | strict |
| 26 | `demos/map/graph.yaml` | expand | llm, — | — | none; rows flow on | strict |
| 27 | `demos/map-timeout/graph.yaml` | process | python, — | — | none; rows flow on | `min_success: 2` (**H-1**) |
| 28 | `demos/pattern_model_census/graph.yaml` | extract_items | python, fail | — | `tools.py#L97` raises | strict; consumer check removed |
| 29 | `demos/pattern_model_census/graph.yaml` | judge_pattern | llm, skip | — | `tools.py#L116` raises | strict; skip → tolerated; consumer raises on non-empty `failures` |
| 30 | `demos/pattern_model_census/graph.yaml` | judge_model | llm, skip | — | `tools.py#L116` raises | strict; skip → tolerated; consumer raises on non-empty `failures` |
| 31 | `demos/person_profile_census/gh-profiler.yaml` | extract_items | python, fail | — | none; rows flow on | strict |
| 32 | `demos/person_profile_census/gh-profiler.yaml` | judge_items | llm, skip | — | `tools.py#L418` failed ledger row | strict; skip → tolerated; consumer reads `failures` |
| 33 | `demos/person_profile_census/graph.yaml` | extract_items | python, fail | — | none; rows flow on | strict |
| 34 | `demos/person_profile_census/graph.yaml` | judge_items | llm, skip | — | `tools.py#L418` failed ledger row | strict; skip → tolerated; consumer reads `failures` |
| 35 | `demos/persona_scenarios/graph.yaml` | generate_personas | llm, — | — | none; rows flow on | strict |
| 36 | `demos/persona_scenarios/graph.yaml` | generate_scenarios | llm, — | — | none; rows flow on | strict |
| 37 | `demos/philosopher_book/editorial_graph.yaml` | edit_chapters | llm, — | — | `tools.py#L498` raises | strict; consumer check removed |
| 38 | `demos/prompt_theme_analyzer/graph.yaml` | classify_themes | llm, skip | — | none; rows flow on | strict; skip → tolerated |
| 39 | `demos/python-map/graph.yaml` | analyze | python, — | — | none; rows flow on | strict |
| 40 | `demos/ramp_doctrine/graph.yaml` | judge_entries | llm, — | — | `nodes/doctrine_tools.py#L250` carries, `#L277` raises | strict; consumer check removed |
| 41 | `demos/ramp_incidents/graph.yaml` | classify_documents | llm, — | — | `nodes/incident_tools.py#L189` **rewrites as verdict `not_an_incident`** | strict; consumer check removed |
| 42 | `demos/ramp_rtm/graph.yaml` | derive | llm, — | — | none; rows flow on | strict |
| 43 | `demos/repo_census/graph.yaml` | extract_items | python, fail | — | none; rows flow on | strict |
| 44 | `demos/repo_census/graph.yaml` | judge_items | llm, skip | — | `tools.py#L112` raises | strict; skip → tolerated; consumer raises on non-empty `failures` |
| 45 | `demos/req_witness_audit/graph.yaml` | audit_batches | llm, retry | — | `tools.py#L79` raises | strict; consumer check removed |
| 46 | `demos/safety-guards/graph.yaml` | expand | llm, — | — | none; rows flow on | strict |
| 47 | `demos/salvage_classify/graph.yaml` | classify_assets | llm, — | — | `nodes/salvage_tools.py#L231` **rewrites as verdict `obsolete`, error text as rationale** | strict; consumer check removed |
| 48 | `demos/session-shapes/graph.yaml` | classify | llm, — | — | `nodes/session_shape_tools.py#L183` raises | strict; consumer check removed |
| 49 | `demos/tavily_rag/graph-deep.yaml` | retrieve | python, — | — | none; rows flow on | strict |
| 50 | `diary_digest/graph.yaml` | analyze_all | llm, — | skip | none; rows flow on | strict; move `on_error: skip` into sub-node (**H-2**) |
| 51 | `dungeon_master/turn.yaml` | intents | llm, — | — | none; rows flow on | strict |
| 52 | `icpc-2-rfe/graph.yaml` | classify_clusters | llm, — | — | none; rows flow on | strict |
| 53 | `image_pipeline/graph.yaml` | generate_prompts | subgraph, — | skip | none; rows flow on | strict; map-level `on_error: skip` stays unread (**H-2**) |
| 54 | `memory-curation/graph.yaml` | judge_notes | llm, — | — | none; rows flow on | strict |
| 55 | `novel_fandom/draft.yaml` | draft_chapters | llm, — | — | none; rows flow on | strict |
| 56 | `npc/encounter-multi.yaml` | perceive_all | llm, — | — | none; rows flow on | strict |
| 57 | `npc/encounter-multi.yaml` | decide_all | llm, — | — | none; rows flow on | strict |
| 58 | `npc/encounter-multi.yaml` | narrate_all | llm, — | — | none; rows flow on | strict |
| 59 | `ocr_cleanup/graph.yaml` | cleanup_pages | llm, — | skip | `tools/merger.py#L160` `SkipReport` reads skips from `state.errors` | strict; move `on_error: skip` into sub-node (**H-2**); consumer reads `failures` |
| 60 | `plot_modeller/graphs/perspective_l5.yaml` | per_agent | subgraph, — | — | none; rows flow on | strict |
| 61 | `plot_modeller/graphs/roundtrip_skeleton.yaml` | draft_chapter | llm, — | — | none; rows flow on | strict |
| 62 | `storyboard/animated-character-graph.yaml` | animate_panels | llm, — | — | none; rows flow on | strict |
| 63 | `style_convert/graph.yaml` | convert_styles | llm, — | — | `nodes/validate_conversions.py#L39` raises | strict; consumer check removed |
| 64 | `surplus/diary-discourse-analysis/graph.yaml` | read_chunks | llm, — | — | `nodes/tools.py#L407` raises | strict; consumer check removed |
| 65 | `surplus/diary-discourse-analysis/graph.yaml` | distill_batches | llm, — | — | `nodes/tools.py#L442` raises | strict; consumer check removed |
| 66 | `yamlgraph_gen/snippets/patterns/generate-then-map.yaml` | process_items | llm, — | — | none; rows flow on | strict (template) |
| 67 | `yamlgraph_gen/snippets/patterns/map-then-summarize.yaml` | process_items | llm, — | — | none; rows flow on | strict (template) |

**What the table shows.**
- 23 of 67 maps have a consumer that examines `_error`; 44 pass error rows
  unexamined into the next node or prompt.
- Rows 41 and 47 are the plausible-wrong-answer class. Strict removes it.
- Rows 29, 30 and 44 carry contradictory declarations: skip in the
  sub-node, raise in the consumer. Today's behavior is kept; this FR does
  not resolve the contradiction.
- After the change, row 59's `SkipReport` would see no skips in
  `state.errors` (R-3), so `merger.py` reads `failures` instead.

**Human decisions.** All four accepted by the operator on 2026-09-25, as
proposed below ("open questions had suggested or implied solutions. all
accepted"). H-4: the `innovation_matrix` rerun spend is authorized (C-9),
run after deterministic acceptance and non-gating.
- **H-1 (R-5):** approve the table, in which every map is strict except
  row 27 (`map-timeout`, `min_success: 2`).
  - Row 27 evidence: the demo exists to show a timeout. `tasks.yaml` gives
    `slow-task` a 5.0 s delay against the map's `timeout: 1.0`, and
    `demo-output.log` line 11 shows two completed tasks and one
    `TimeoutError`. Strict would make the demo raise.
  - No other map gets a threshold. FR-985's 57–92% census coverage came
    from `judge_items` skip failures, which are tolerated under item 7 and
    pass strict. `fi_domain_crawl`'s one real 403 in ten items is a single
    run, not a threshold (judgement R-5).
- **H-2 (R-5):** approve moving the unread map-level `on_error` into the
  LLM sub-node for rows 2, 5, 6, 7, 10, 50 and 59.
  - With the move, the declared skip or retry takes effect. Without it,
    these maps go strict with no tolerance.
  - Row 53 (`image_pipeline`) stays strict, because its sub-node is a
    subgraph and emits no `_skipped`.
  - Each moved graph goes through `scripts/author.sh` with a committed
    brief under `feature-requests/authoring-briefs/`.
- **H-3 (R-5):** extend D-5 to the 17 consumer files in the table (16
  `_error` readers plus `ocr_cleanup/tools/merger.py`). The
  frozen D-5 names only `corpus_census/tools.py`, but AC-17 requires every
  `_error` consumer to be migrated.
- **H-4 (R-6, optional, non-gating):** authorize the provider spend for
  one `innovation_matrix` rerun after deterministic acceptance, or decline
  it.

## Acceptance Criteria

The judgement's revised AC-01 to AC-23 are adopted. Additions are marked
**(+)**.

- [ ] AC-01: RED first: map schema accepts optional `key` and `failures`, defaults `failures` to `<collect>_failures`, and validates `min_success` per item 7; booleans, strings, non-finite floats, negative integers, and out-of-range floats fail at load with the map name and offending field/value.
- [ ] AC-02: `failures` equal to `collect`, empty, or colliding with a reserved key fails at load; two maps may share a non-reserved collect/failure channel.
- [ ] AC-03: the dispatch node resolves every key before any `Send`; duplicate keys fail before any branch executes and name the map, duplicate key, and both indices.
- [ ] AC-04: the timeout path, general exception path, and error-bearing update path emit the identical `MapFailure` shape; each non-tolerated path emits exactly one `PipelineError` with `node=_map_<name>_sub`; no path writes to `collect`.
- [ ] AC-05: a successful update containing `errors: []` is collected as success. **(+)** So is an update containing `error: None` (the `fi_domain_crawl` case).
- [ ] AC-06: with a memory checkpointer, three items and one non-tolerated Python sub-node failure under absent `min_success` produce two collect entries, one failure, complete accounting, and `MapCompletenessError` at the join; checkpoint inspection after the raise sees the two finished results.
- [ ] AC-07: 100 items, one non-tolerated failure, `min_success: 0.98` → `succeeded=99 tolerated=0 failed=1 accepted=99 met=true`; the downstream node runs with 99 entries and no error-shaped content.
- [ ] AC-08: `min_success: 1` accepts one accepted item, `1.0` requires all, an integer above dispatch is unmet, and every invalid boundary from item 7 is covered.
- [ ] AC-09: nested `on_error: skip` failure → one `MapFailure(tolerated=true)`, no `PipelineError`, increments `tolerated` and `accepted` only. **(+)** A wrapper timeout under a skip sub-node is `failed`, not tolerated.
- [ ] AC-10: zero items routes the dispatch node to the join and yields the zero verdict with `met=true`; the sub-node never runs.
- [ ] AC-11: a branch that mutates state read by `over` cannot change the dispatch count, keys, or index set; missing or repeated accounting indices raise `MapAccountingError`.
- [ ] AC-12: two maps sharing collect/failure channels account only their own map and dispatch. Two sequential loop invocations of one map use distinct tokens and leave only the second verdict current.
- [ ] AC-13: two overlapping invocations of the same map fail closed with both tokens named; no verdict is published.
- [ ] AC-14: compiled topology witnesses cover START → map → END, node → map → node, zero items, loop-back, and map-to-map; every outgoing path starts at `_map_<name>_join`; name collisions fail naming the conflicting node.
- [ ] AC-15: the FR-944 N=3 fixture still yields downstream indices `[0, 1, 2]` once; the N×M fixture still fans out exactly M times; no downstream router bypasses the upstream join.
- [ ] AC-16: state generation gives collect, failures, `_map_accounting`, `_map_open`, and `_map_verdict` their declared reducers; concurrent different-map verdicts are both kept; `state.errors` stays `list[PipelineError]`.
- [ ] AC-17: no repository map consumer reads `_error` from `collect`. The 17 consumer files in the census are migrated per their disposition, with fixtures proving the kept behavior. **(+)** Rows 41 and 47 no longer produce a verdict for a failed item.
- [ ] AC-18: every graph edit (H-2 rows, row 27) has a committed authoring brief, a governed authoring report, passing lint, and an attempted narrow smoke with its exact outcome; no threshold other than those approved under H-1 exists.
- [ ] AC-19: deterministic downstream-content tests: strict failure prevents consumer execution; declared partial success passes only real results; failures and verdict readable separately; no `_error` or exception repr in content.
- [ ] AC-20: `reference/graph-yaml.md` documents field types and defaults, integer-versus-fraction semantics, tolerated arithmetic, zero items, the typed records, same-map overlap rejection, and the strict default; new REQ ID on every new test; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-21: RED and GREEN are separate commits; RED fails on behavior assertions, not missing imports, fixtures, credentials, or services.
- [ ] AC-22: the focused FR-1073 suite and affected map/schema/state/FR-944 regressions pass. A paid provider run is not required (H-4).
- [ ] AC-23: this FR records final status, migration decisions and deviations; one fix changelog fragment and one diary entry with `Seed:` are committed.

## Revision fold

| Revision | Folded into |
|---|---|
| R-1 exact dispatch token, overlap fails closed | Items 1, 2; AC-12, AC-13 |
| R-2 threshold types, terms, zero items, policy ownership | Item 7 (map-level `on_error` alias removed); AC-01, AC-08–AC-10 |
| R-3 typed records and reducers apart from `state.errors` | Items 3–5; AC-04, AC-16 |
| R-4 join topology on every path | Item 8; AC-14, AC-15 |
| R-5 migration census, authoring route | [Migration census](#migration-census), H-1–H-3; AC-17, AC-18 |
| R-6 live rerun optional | H-4; AC-19, AC-22 |

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

### Judge's answer on the strict default

The strict default goes ahead now; it does not wait for FR-1065. Resume
makes a failed run cheaper but does not make undeclared partial output
correct ([judgement](FR-1073-map-result-contract.judgement.md), "What is
sound"). The operator's preference (2026-09-25) was the same.

## Implementation (2026-09-25)

Branch `feat/fr-1073-map-result-contract`. RED `b38aff20`; GREEN is the
next commit on the branch. One PR, per the operator ruling.

**Code.**
- `yamlgraph/models/map_results.py`: `MapFailure`, `MapAccounting`,
  `MapVerdict`, `MapCompletenessError`, `MapAccountingError`, the reducers,
  and `compute_verdict` (item 7 arithmetic).
- `yamlgraph/compile/map_contract.py`: branch classification, the dispatch
  node and router, the account node and the join.
- `map_compiler.py` compiles `<name>` (dispatch), `_map_<name>_sub`,
  `_map_<name>_account` and `_map_<name>_join`. `edge_compiler.py` starts
  every outgoing edge at the
  join. `validators.py` checks `min_success` and `failures` at load.
  `state_builder.py`/`state_codegen.py` declare the reducers.

**AC status.** AC-01, AC-02, AC-04 to AC-23 met: witnesses in
`tests/unit/test_fr1073_map_result_contract.py`, the migrated map test
files, and the consumer witnesses below. AC-03 cut by the operator ruling.
AC-23: status, decisions, changelog fragment and the diary entry
(`docs/diary/2026-09-25-reflection-fr-1073.md`) are in this PR.

**Consumer migration (H-3, AC-17).**
- 11 files drop their `_error` branch: a failed item can no longer reach
  `collect`. Rows 41 and 47 lose the rewrite into `not_an_incident` /
  `obsolete`. A strict map now raises at the join before these consumers
  run (AC-06, AC-19 witnesses), so no per-consumer fixture exists: the
  consumers no longer have a failed-item path.
- `corpus_census`, `person_profile_census`, `cap_journey_census` turn
  `findings_failures` records into the same failed ledger row as before.
  Witness: `test_failures_channel_becomes_failed_row`.
- `repo_census` and `pattern_model_census` raise on any
  `*_findings_failures` record, tolerated or not. Witnesses:
  `test_tolerated_failure_still_rejected` (both suites).
- `ocr_cleanup/tools/merger.py` builds its `SkipReport` from
  `map_results_failures`. Witness: `tests/unit/test_fr1073_ocr_skip_report.py`.
- Four tests that fed hand-built `_error` envelopes to removed branches
  were deleted (`test_style_convert`, `test_fr776_vision_fallback` ×2,
  `test_abstraction_span_separation`).

**Graph edits (H-1, H-2, AC-18).** Brief
`feature-requests/authoring-briefs/fr-1073-map-migration.md`, run through
`scripts/author.sh`. Rows 2, 5, 6, 7, 10, 50, 59 move `on_error` (and
`max_retries`) into the sub-node. Row 27 adds `min_success: 2`. A second
brief, `feature-requests/authoring-briefs/fr-1073-book-translator-state.md`,
also run through `scripts/author.sh`, declares `reviewed_chunks: dict` in
`book_translator`'s state. That clears its E303
(`human_review.resume_key`), which was on main before this change (review
P3). The governed reports are written to `tmp/draft-authoring-report.md`
per run and are not committed; their results:

| Graph | `yamlgraph graph lint` | Smoke |
|---|---|---|
| `batch_image_prompts` | exit 0 | compile check; no live run (H-4) |
| `book_translator` | exit 0 (0 errors, 4 warnings) | `graph info` exit 0; no live run (H-4) |
| `daily_digest` | exit 0 | compile check; no live run (H-4) |
| `diary_digest` | exit 0 | compile check; no live run (H-4) |
| `ocr_cleanup` | exit 0 | compile check; no live run (H-4) |
| `demos/map-timeout` | exit 0 | run from its own graph, `examples/demos/map-timeout/demo-output.log`: two results, one non-tolerated `TimeoutError` in `results_failures`, verdict met, no raise, `current_step: _map_process_join` |

**Deviations from the plan.**
- `MapFailure.index`, not `_map_index`.
- `key` cut (operator ruling); the dispatch token is a UUID per dispatch.
- Item 8 names three nodes; the map compiles four. Item 6 requires the
  verdict and the closed dispatch to be written before
  `MapCompletenessError`, and LangGraph discards every write of a node
  that raises. So `_map_<name>_account` does item 6's first four steps and
  `_map_<name>_join` raises in the next step. The join still owns every
  outgoing edge (AC-14). Found by review of PR #702 (P1); the checkpoint
  witness now asserts the failed verdict and `_map_open.<name> is None`.
- `MapFailure.dispatch` and `MapAccounting.dispatch` are required strings;
  a branch without `_map_dispatch` raises `MapAccountingError` (review P2).
- The FR-944 barrier node is dropped: the join is the barrier.
- The map `Send` branch in `routing.py` is deleted; the dispatch router
  owns fan-out. It re-resolves `over` and checks the count against the
  dispatch record (AC-11).
- The `Send` payload carries `_map_dispatch` so each branch reports its
  token.
- `tests/fixtures/interrupt_loop_end.yaml` had a `passthrough` sub-node
  inside a map, which never worked: it failed on every item with an
  `rsplit` error that the old contract hid as an `_error` result. The
  fixture now uses a python tool (`tests/fixtures/interrupt_loop_tools.py`).
  This is the FR's thesis, witnessed by the repository's own fixture.
- `yamlgraph/schemas/graph-v1.json` unchanged: it does not list
  `timeout` or `flatten_output` either and admits extra node keys.

**Gate bypass (operator decision, 2026-09-25).** The GREEN commit ran with
`SKIP=demo-proof-check`. The gate asks for a fresh `demo-output.log` for
12 LLM demos whose tool code changed: book-summary, cap_journey_census,
corpus_census, pattern_model_census, person_profile_census,
philosopher_book, ramp_doctrine, ramp_incidents, repo_census,
req_witness_audit, salvage_classify, session-shapes. The gate is right
that their behaviour changed. The operator chose unit witnesses over 12
live runs (cost, gh/azure credentials): each changed branch has a unit
test, and the full unit suite passed. Their committed logs predate
FR-1073. `map-timeout` is the one demo with a fresh log, produced by its
own graph.

**Post-judgement operator rulings (2026-09-26).** These change frozen
judgement clauses; they are recorded here as amendments, not deviations.
Review round 2 of PR #702 raised each one.
- **A-1 (review P1): `key` cut.** The judgement froze `key` in the failure
  and accounting identity and a duplicate-key check before any `Send`
  (AC-01 `key` half, AC-03). The operator's 2026-09-25 ruling cuts both.
  First consumer is FR-1065, which will carry `key` when it needs it.
- **A-2 (review P4): `book_translator` state edit approved after the
  fact.** Judgement C-7 excludes unrelated demo repair; C-6 requires every
  edited graph to lint. `book_translator` failed lint (E303) on `main`
  before this change, so C-6 and C-7 conflict for that graph. The operator
  approves the `reviewed_chunks: dict` edit and its brief.
- **A-3 (review P2): demo proofs postponed.** The 12 demo logs above are
  replaced with a one-line `✅ Live run postponed until map proven to
  work` notice. They are not run logs; the previous live runs remain in
  git history. The live runs happen after this map contract has been
  proven in use.
- **A-4 (review P3): FR-944 barrier node dropped.** Judgement R-4 and
  item 206 name upstream sub → upstream join → FR-944 barrier →
  downstream fan-out. The implementation wires the upstream join straight
  to the downstream dispatch: the join already runs only after every
  upstream branch has reported, so a separate barrier would wait on the
  same event twice. The operator accepts this topology (2026-09-26);
  `test_fr944_map_to_map_index.py` witnesses the end state.

## Related

- Research brief: [research-briefs/map-result-contract-brief.md](research-briefs/map-result-contract-brief.md)
- Plan: [docs/issues-2026-09-24.md](../docs/issues-2026-09-24.md) §7 A
- Consumed by: [FR-1065](FR-1065-resumable-map-investigation.md) (item key, failures), a refiled FR-1066 (exit code), a refiled FR-1070 (innovation_matrix)
