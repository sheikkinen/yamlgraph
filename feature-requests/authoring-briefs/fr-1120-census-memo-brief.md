# Authoring brief: FR-1120 person-profile census — map memo wiring

Governing FR: feature-requests/FR-1120-census-map-memo.md (judgement:
feature-requests/FR-1120-census-map-memo.judgement.md)

## Task

Modify **exactly one graph file**: `examples/demos/person_profile_census/graph.yaml`.
No prompt changes. The Python functions it calls already exist and are
committed-ready in `examples/demos/person_profile_census/tools.py`
(`memo_prepare`, `pair_executed`, `reduce_pr_ledger` merged branch) and
`examples/shared/map_memo.py` (`map_memo_split(..., versions=...)`,
`map_memo_merge`). Do not edit Python.

### State

- Add: `memo_store: str`, `memo_inputs: dict`, `memo_query: dict`,
  `versions: dict`, `memo: dict`, `paired: list` (`type: list`),
  `merged: dict`, `executed_contents` (`type: list`, `reducer: sorted_add`),
  `executed_findings` (`type: list`, `reducer: sorted_add`).
- Remove: `contents`, `findings`.
- Do NOT declare `_map_verdict` or `executed_findings_failures` (map-owned).
- Every other state entry stays byte-identical.

### Tools

- New slot `versions`: `slot: true`, `contract: {runtimes: [python]}`.
- `map_memo_split: {manifest: ../../shared/map_memo_split.tool.yaml}`
- `map_memo_merge: {manifest: ../../shared/map_memo_merge.tool.yaml}`
  (precedent: `examples/demos/meta_map/graph.yaml`).
- `memo_prepare` and `pair`: `type: python`, `path: tools.py`,
  functions `memo_prepare` and `pair_executed`, one-line descriptions.
- Existing slots/tools stay byte-identical.

### Nodes (in this order; edges form one linear chain)

START → preflight → memo_prepare → discover → versions → memo_split →
extract_items → judge_items → pair → memo_merge → reduce_ledger →
prepare_brief_input → synthesize → render_brief → END

- `memo_prepare`: `type: python`, `tool: memo_prepare`,
  `state_key: memo_prepared`, `on_error: fail`. (It returns
  `memo_inputs`, `memo_query`, `executed_contents: []`; declare
  `memo_prepared: dict` in state if the linter requires the state_key.)
- `versions`: `type: tool_call`, `tool: versions`,
  `args: {state: "{state.memo_query}"}`, `state_key: versions`,
  `on_error: fail`.
- `memo_split`: `type: tool_call`, `tool: map_memo_split`, `on_error: fail`,
  `state_key: memo`, args exactly:
  ```yaml
  items: "{state.items}"
  versions: "{state.versions.result}"
  store: "{state.memo_store}"
  inputs: "{state.memo_inputs}"
  signature_files:
    - examples/demos/person_profile_census/graph.yaml
    - examples/demos/person_profile_census/prompts/classify_pr.yaml
    - examples/demos/person_profile_census/tools.py
    - examples/demos/corpus_census/adapters/corpus_adapters.py
  ```
- `extract_items`: unchanged except `over: "{state.memo.result.todo}"`
  and `collect: executed_contents`.
- `judge_items`: unchanged except `over: "{state.executed_contents}"`
  and `collect: executed_findings`. Keep `on_error: skip`, `max_items: 500`
  and all variables.
- `pair`: `type: python`, `tool: pair`, `state_key: paired`, `on_error: fail`.
- `memo_merge`: `type: tool_call`, `tool: map_memo_merge`, `on_error: fail`,
  `state_key: merged`, args: `plan: "{state.memo.result}"`,
  `results: "{state.paired}"`, `failures: []`, `map_name: judge_items`,
  `map_dispatch: "{state._map_verdict.judge_items.dispatch}"`,
  `min_success: 0`. Comment: judge failures are stored inside `paired`
  as `error` records so a re-run reuses them as row_failed; the
  reducer's coverage floor remains the threshold.
- `reduce_ledger`, `prepare_brief_input`, `synthesize`, `render_brief`
  unchanged.
- Update `description:` with one sentence: the census memoizes extract +
  classify per PR keyed by GitHub `updatedAt`; `memo_store` is required.

Directly related documentation (edit it too, named for the report):
`examples/demos/person_profile_census/README.md` — add a "Memo (FR-1120)"
section: `--var memo_store=<path>` is required; `--tool
versions=examples/demos/corpus_census/adapters/gh-authored-prs-versions.tool.yaml`
must be bound next to discover; unchanged PRs are neither extracted nor
classified on re-run; rubric/labels/model/graph/prompt/tools/adapter
changes re-run all; delete the store to force a full recompute. Update
any existing run command in the README to include both.

## Validation

- `yamlgraph graph lint examples/demos/person_profile_census/graph.yaml`
- `python -m pytest tests/unit/test_fr1120_census_memo_graph.py -q --no-cov`
  (provider-free: stubs for discover/versions/extract, execute_prompt
  patched). Must pass. Record the outcome.
- Live smoke is out of scope (needs Azure + gh); record as blocked.

**Prior art:** FR-1116 (map memo, meta_map precedent), FR-1119 (E007
map-owned fields), FR-962/FR-985 census briefs for this graph.
