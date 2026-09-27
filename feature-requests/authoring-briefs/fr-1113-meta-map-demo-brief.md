# Authoring brief: FR-1113 meta-map demo

Governing FR: feature-requests/FR-1113-meta-map-demo.md

## Task

Author exactly these four artifacts in `examples/demos/meta_map/`:

- `graph.yaml` (parent graph)
- `subgraphs/summarize_one.yaml` (per-branch child graph)
- `prompts/describe_graph.yaml`
- `prompts/reduce_summaries.yaml`

The Python tools already exist and are tested:
`examples/demos/meta_map/tools.py` (module `examples.demos.meta_map.tools`).
Do not edit `tools.py`, the tests, or anything under `yamlgraph/`. If a
tool contract seems wrong, stop and record it under Blocked validation.

### Tool contracts (python nodes; each returns a dict update)

| Function | Reads state | Returns |
|----------|-------------|---------|
| `discover_map_graphs` | `scan_roots` (list, default `["examples", "graphs"]`) | `{"paths": list[str]}` |
| `poison_the_source` | `paths`, `poison` (list) | `{"paths": paths + poison}` |
| `read_source` | `path` | `{"source": SourceText}` with fields `path`, `text` |
| `reconcile_claim` | `path`, `source`, `claim` | `{"graph_record": GraphRecord}`; raises `ClaimMismatchError` |
| `reduce_inputs` | `summaries`, `summary_failures`, `_map_verdict` | `{"reduce_input": dict}` with `records` (list) and `counts` (dict) |
| `render_report` | `paths`, `summaries`, `summary_failures`, `_map_verdict`, `overall`, `output_path` | `{"report_path": str}` |

### Parent graph `graph.yaml` (name `meta-map`)

- `defaults`: `provider: inception`, `model: mercury-2.5` (operator
  decision; applies to both prompts), `on_overflow: error`.
- `config`: `max_concurrency: 8`.
- `state`: `scan_roots: list` (default `["examples", "graphs"]`),
  `poison: list` with default, in this order:
  `examples/demos/hello/graph.yaml`,
  `feature-requests/FR-1113-meta-map-demo.md`,
  `yamlgraph/compile/map_compiler.py`;
  `output_path: str` (default `outputs/meta_map/report.md`);
  plus `paths`, `summaries`, `summary_failures`, `reduce_input`,
  `overall`, `report_path`.
- Nodes, in order: `discover` → `poison_the_source` → `summarize` →
  `prepare_reduce` → `reduce` → `render`.
  - `summarize`: `type: map`, `over: "{state.paths}"`, `as: path`,
    `max_items: 100`, `on_overflow: error`, `timeout: 120`,
    `min_success: 0.9`, `failures: summary_failures`,
    `collect: summaries`. Sub-node: `type: subgraph`, `mode: invoke`,
    `graph: subgraphs/summarize_one.yaml`,
    `input_mapping: {path: path}`,
    `output_mapping: {summary: graph_record}`, `state_key: summary`.
    No `on_error` on the map or the sub-node: failures must be
    untolerated.
  - `prepare_reduce`: python, tool `reduce_inputs`, `state_key: reduce_input`.
  - `reduce`: llm, prompt `reduce_summaries`, variables from
    `state.reduce_input.records` and `state.reduce_input.counts`,
    `state_key: overall`. Output: a string summary (a few paragraphs of
    markdown: what the repository's map graphs are for, which map
    versions dominate, what the failures show).
  - `render`: python, tool `render_report`, `state_key: report_path`.

### Child graph `subgraphs/summarize_one.yaml`

- Same `defaults` provider/model.
- `state`: `path: str`, `source`, `claim`, `graph_record`.
- `read_source` (python) → `describe` (llm, prompt `describe_graph`,
  `state_key: claim`, variables `path` and `text` from `state.source`)
  → `reconcile` (python, tool `reconcile_claim`,
  `state_key: graph_record`).
- The prompt directory must resolve to `examples/demos/meta_map/prompts/`
  from the child graph.

### Prompt `describe_graph.yaml`

- Input: a file path and its raw text. Nothing in the prompt says the
  input might be invalid, poisoned, or not a graph, and the schema has
  **no** decline / not-applicable / is_graph field. That is the point
  of the demo (FR-1113 A7): bad data reaches the LLM unfiltered and the
  Python `reconcile` grades the claim afterwards.
- Task: "This is a YAMLGraph graph file that uses map nodes. Name the
  map nodes, state the graph's intent in one sentence, and state the
  map's role in one sentence."
- Inline schema (exactly): `map_nodes: list[str]` (names of top-level
  nodes with `type: map`), `intent: str`, `map_role: str`.

### Prompt `reduce_summaries.yaml`

- Input: the records (path, map nodes, version, declared keys, intent,
  role) and Python-computed counts. The prompt must tell the model to
  use the given counts verbatim and never recount.
- Output: plain text/markdown (no schema).

## Validation

- `yamlgraph graph lint examples/demos/meta_map/graph.yaml` and the
  child graph.
- `pytest tests/unit/test_fr1113_meta_map.py -q --no-cov` must pass
  (the graph-level tests stub the LLM).
- Smoke: `yamlgraph graph run examples/demos/meta_map/graph.yaml --full`
  with `inception/mercury-2.5` (spend authorized, FR-1113 Status). The
  expected outcome is exit 3 (completed with errors) with the three
  poison paths in `summary_failures`, or `MapCompletenessError` if
  more than 10 % of branches fail. Record the exact outcome; do not
  weaken the prompt or add a decline field to make it pass.

**Prior art:** `examples/demos/diary_index/` (discover → map → reduce
with python tools), `examples/image_pipeline/graph.yaml` (map over an
invoke-mode subgraph with input/output mapping),
`examples/demos/map-timeout/` (map `timeout` + `min_success`).
