# meta_map — map over the repository's own map graphs (FR-1113)

A single demo that exercises the map node in full on a real corpus: this
repository's own map graphs. Each graph is read by a subgraph; an LLM says what
the graph does; Python checks that claim against a real YAML parse. Three
deliberately wrong inputs ("poison") are added to prove that bad inputs fail
visibly instead of passing quietly.

```bash
yamlgraph graph run examples/demos/meta_map/graph.yaml --full
# exit 3 is the expected outcome: the three poison branches fail untolerated
# (yamlgraph/cli/graph_run_helpers.py report_tally). The report is still written.
cat outputs/meta_map/report.md
```

Provider: `inception/mercury-2.5` (about 56 LLM calls per run).

## Pipeline

```
discover → poison_the_source → summarize (map → subgraph) → prepare_reduce → reduce → render
                                   └─ summarize_one: read_source → describe (LLM) → reconcile
```

| Node | Kind | What it shows |
|------|------|---------------|
| `discover` | python | Walks `examples/` and `graphs/`; a malformed YAML raises and names the path |
| `poison_the_source` | python | Appends `poison.yaml` paths (loaded via `data_files`) |
| `summarize` | map | `max_items: 100` + `on_overflow: error`, `timeout: 120`, `min_success: 0.9`, `failures: summary_failures`, `config.max_concurrency: 8`, subgraph sub-node with `input_mapping` / `output_mapping` |
| `reconcile` | python | Compares the LLM's `map_nodes` claim against `parse_map_nodes`; a mismatch raises `ClaimMismatchError` |
| `prepare_reduce` | python | Computes counts from `_map_verdict` and the records; the LLM only writes prose |
| `render` | python | Writes `outputs/meta_map/report.md`; every map index must appear exactly once |

## Poison

| Path | Why it must fail |
|------|------------------|
| `examples/demos/hello/graph.yaml` | A valid graph with no map node |
| `feature-requests/FR-1113-meta-map-demo.md` | Markdown with an embedded YAML map example |
| `yamlgraph/compile/map_compiler.py` | Python that implements the map node |

The source text gives the model no hint about which inputs are poison. Only
the parse decides.

## Recorded run (`proofs/poisoned-run/run-evidence.txt`)

`demo-output.log` holds the output of `yamlgraph graph validate` for this
graph (same approach as `map-timeout`). The demo-proof gate treats any
`[ERROR]` line as fatal, and a poisoned run is designed to produce three of
them. The full log of the real run is in `proofs/poisoned-run/run-evidence.txt`.

55 dispatched · 52 succeeded · 0 tolerated · 3 failed. The threshold is
`ceil(0.9 × 55) = 50`, so the run meets it. All three failures are the poison
paths, each with `ClaimMismatchError`. The model's raw claims were:

- hello: claimed `[]`. The model told the truth; the source has no map nodes, so it still fails.
- FR-1113: claimed `['summarize']`. The model was fooled by the Markdown's embedded YAML.
- map_compiler.py: claimed `[]`.

"Version" is a label for the YAML keys a graph declares, checked in this
order: `overflow` > `result-contract` > `timeout` > `capped` > `core`. At
runtime, the FR-1073 result contract applies to every map.

## Not shown here

- `tolerated` failures: each branch either succeeds or fails.
- `on_overflow: truncate`: the demo uses `error`, which the overflow test covers.
- Chaining one map into another, and `flatten_output`.

Tests: `tests/unit/test_fr1113_meta_map.py` (stubbed LLM, no network).
