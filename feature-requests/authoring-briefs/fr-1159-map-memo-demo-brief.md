# Authoring brief: FR-1159 map_memo demo

Governing FR: feature-requests/FR-1159-map-memo-contrib.md (item 5, AC-06, AC-07)

## Task

Create a new, small demo `examples/demos/map_memo/` that shows the map memo
shipped as `yamlgraph.contrib.map_memo` — used the way an installed user would
use it: tools declared **inline** via `module:`, never via the repo-relative
`examples/shared/*.tool.yaml` manifests.

Files:

1. `notes/alpha.md`, `notes/beta.md`, `notes/gamma.md` — three short
   (2–4 line) plain-text notes on any harmless topic.
2. `tools.py` with two plain functions (stdlib only):
   - `prepare(state) -> dict` returning
     `{"paths": [...], "store": str}`: lists `*.md` files in
     `state["notes_dir"]` (default `examples/demos/map_memo/notes` when the
     key is absent or empty), sorted by name, as `str` paths; `store` is
     `state["store"]` or the default `outputs/map_memo_demo/memo.sqlite`.
   - `read_note(state) -> dict` returning `{"path": ..., "text": ...}` for
     `state["path"]` read as UTF-8.
3. `subgraphs/summarize_one.yaml` — worker: python `read_note`
   (`state_key: note`) → llm node with prompt `summarize_note`
   (`state_key: summary`, variables `path` and `text` from `state.note`).
   **The prompt has no schema** — plain-text output. Provider/model defaults
   as in `examples/demos/meta_map/subgraphs/summarize_one.yaml`.
4. `prompts/summarize_note.yaml` — one-sentence summary of the note; no
   `schema:`.
5. `graph.yaml`, pipeline `prepare → memo_split → summarize → memo_merge → END`:
   - state: `notes_dir: str`, `store: str`, `plan: dict` (prepare output),
     `memo: dict`, `summaries: list`, `summary_failures: list`, `merged: dict`.
   - tools, inline (no manifests):
     ```yaml
     map_memo_split:
       type: python
       module: yamlgraph.contrib.map_memo
       function: map_memo_split
       description: Split items into reused and todo by content signature.
     map_memo_merge:
       type: python
       module: yamlgraph.contrib.map_memo
       function: map_memo_merge
       description: Merge executed map results with reused ones and persist them.
     ```
     plus `prepare` and `read_note` from `examples.demos.map_memo.tools`.
   - `prepare`: python node, `state_key: plan`.
   - `memo_split`: `type: tool_call`, `on_error: fail`, `state_key: memo`,
     args `items: "{state.plan.paths}"`,
     `signature_files:` the literal list
     `[examples/demos/map_memo/graph.yaml, examples/demos/map_memo/subgraphs/summarize_one.yaml, examples/demos/map_memo/prompts/summarize_note.yaml]`,
     `store: "{state.plan.store}"`.
   - `summarize`: `type: map`, `over: "{state.memo.result.todo}"`,
     `as: path`, `max_items: 20`, `on_overflow: error`, `min_success: 0`,
     `failures: summary_failures`, `collect: summaries`, node = subgraph
     `subgraphs/summarize_one.yaml` (`mode: invoke`, input_mapping
     `path: path`, output_mapping `summary: summary`, `state_key: summary`).
     YAML comment: the threshold is judged by `memo_merge` over the whole
     population, so the map declares `min_success: 0`.
   - `memo_merge`: `type: tool_call`, `on_error: fail`, `state_key: merged`,
     args `plan: "{state.memo.result}"`, `results: "{state.summaries}"`,
     `failures: "{state.summary_failures}"`, `map_name: summarize`,
     `map_dispatch: "{state._map_verdict.summarize.dispatch}"`,
     `min_success: 1.0`.
   Follow `examples/demos/meta_map/graph.yaml` as precedent for the
   memo_split / map / memo_merge wiring.
6. `README.md` — what it shows, the inline `module:` declaration, run
   commands (run twice; second run makes zero LLM calls; edit one note →
   one call; `rm outputs/map_memo_demo/memo.sqlite` forces a full run;
   CLI provider/model overrides are not part of the signature).

Contract fixed by the FR's witness test (`tests/unit/test_fr1159_map_memo_contrib.py::test_demo_reuses_unchanged_notes`,
do not edit it): the graph is invoked with
`{"notes_dir": <dir>, "store": <path>}`; only
`yamlgraph.node_factory.llm_nodes.execute_prompt` is patched, it returns the
string `"SUMMARY"` for prompt names containing `summarize` and raises for any
other prompt — so the demo must have exactly one LLM prompt, named with
`summarize`. It reads `out["merged"]["result"]["records"]` and
`out["merged"]["result"]["counts"]`; expected worker calls per run: 3, 0, 1.

## Validation

- `yamlgraph graph lint examples/demos/map_memo/graph.yaml`
- `yamlgraph graph lint examples/demos/map_memo/subgraphs/summarize_one.yaml`
- `pytest tests/unit/test_fr1159_map_memo_contrib.py -q --no-cov -k demo`
- Do NOT run the live smoke; the FR's enforcer runs it under a spend cap.

**Prior art:** FR-1116 meta_map memo consumer (`examples/demos/meta_map`),
FR-1120 census memo graph — same split/map/merge wiring; this demo differs
only in declaring the tools inline by module.
