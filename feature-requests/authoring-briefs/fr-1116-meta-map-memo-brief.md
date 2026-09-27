# Authoring brief: FR-1116 meta_map — map memo consumer

Governing FR: feature-requests/FR-1116-map-memo-file-corpus.md (item 7)

## Task

Modify `examples/demos/meta_map/graph.yaml` and add one data file
`examples/demos/meta_map/memo.yaml`. No prompt changes, no subgraph
changes. `tools.py` is already migrated by the FR's enforcement (it reads
records, failures and the verdict from `state.merged.result`).

1. New data file `examples/demos/meta_map/memo.yaml`, exactly:

   ```yaml
   store: outputs/meta_map/memo.sqlite
   signature_files:
     - examples/demos/meta_map/graph.yaml
     - examples/demos/meta_map/subgraphs/summarize_one.yaml
     - examples/demos/meta_map/prompts/describe_graph.yaml
     - examples/demos/meta_map/tools.py
   ```

2. `data_files:` gains `memo_config: memo.yaml` (keep `poison: poison.yaml`).
3. `state:` gains `memo_config: dict`, `memo: dict`, `merged: dict`.
4. `tools:` gains two FR-768 manifest entries:
   `map_memo_split: {manifest: ../../shared/map_memo_split.tool.yaml}` and
   `map_memo_merge: {manifest: ../../shared/map_memo_merge.tool.yaml}`.
5. New node `memo_split` between `poison_the_source` and `summarize`:
   `type: tool_call`, `tool: map_memo_split`, `on_error: fail`,
   `state_key: memo`, args:
   - `items: "{state.paths}"`
   - `signature_files: "{state.memo_config.signature_files}"`
   - `store: "{state.memo_config.store}"`
6. `summarize` map: `over: "{state.memo.result.todo}"` and
   `min_success: 0`. Every other key (`as`, `max_items: 100`,
   `on_overflow: error`, `timeout: 120`, `failures: summary_failures`,
   `collect: summaries`, the subgraph `node:` block) stays byte-identical.
7. New node `memo_merge` between `summarize` and `prepare_reduce`:
   `type: tool_call`, `tool: map_memo_merge`, `on_error: fail`,
   `state_key: merged`, args:
   - `plan: "{state.memo.result}"`
   - `results: "{state.summaries}"`
   - `failures: "{state.summary_failures}"`
   - `map_name: summarize`
   - `map_dispatch: "{state._map_verdict.summarize.dispatch}"`
   - `min_success: 0.9`
8. Edges: `poison_the_source → memo_split → summarize → memo_merge →
   prepare_reduce`; the rest unchanged. Node order in the file:
   discover, poison_the_source, memo_split, summarize, memo_merge,
   prepare_reduce, reduce, render.
9. Add a short YAML comment above `summarize` saying the real 0.9
   threshold is judged by `memo_merge` over the whole population, which is
   why the map itself declares `min_success: 0`.

Directly related documentation artifact (edit it too):
`examples/demos/meta_map/README.md` — add `memo_split` / `memo_merge` to
the pipeline diagram and node table; change the `summarize` row to
`min_success: 0` (threshold moved to `memo_merge`); add a "Memo" section:
reruns only call the LLM for files whose bytes changed, a change to any
signature file re-runs everything, failures are stored and reused too,
provider/model overrides from the CLI are NOT part of the signature, and
`rm outputs/meta_map/memo.sqlite` forces a full run. Keep the recorded
FR-1113 run section as is (it predates the memo).

## Validation

- `yamlgraph graph lint examples/demos/meta_map/graph.yaml`
- `yamlgraph graph validate examples/demos/meta_map/graph.yaml`
- `pytest tests/unit/test_fr1113_meta_map.py tests/unit/test_fr1116_map_memo.py -q --no-cov`
  (the FR's enforcement updates these tests; record the result, do not
  edit tests).
- Smoke (real provider, from the repo root): `rm -f outputs/meta_map/memo.sqlite`,
  then run `yamlgraph graph run examples/demos/meta_map/graph.yaml --full`
  twice. Exit 3 is expected each time (poison fails untolerated). Record
  from `outputs/meta_map/report.md` the `Coverage:` and `Memo:` lines of
  both runs: the second run must show 0 executed and all items reused.
  Record the exact outcome or blocker; do not widen the change to make
  the smoke pass.

**Prior art:** FR-1116-map-memo-file-corpus.md (governing FR — this brief
executes item 7); FR-1113 created the demo; FR-1076 superseded by FR-1116;
book-summary is the precedent for `tool_call` over FR-768 manifests.
