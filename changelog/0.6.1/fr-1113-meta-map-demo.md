---
type: feat
scope: examples
req: REQ-YG-703
---
- **FR-1113 meta_map demo**: `examples/demos/meta_map/` maps over the repository's own map graphs through a subgraph sub-node. It uses `max_items` + `on_overflow: error`, `timeout`, `min_success: 0.9`, `failures:`, `config.max_concurrency`, and `input_mapping`/`output_mapping`. An LLM claims each graph's map nodes; Python reconciles the claim against a real YAML parse and raises `ClaimMismatchError` on disagreement. Three poison paths from `poison.yaml` (a non-map graph, this FR's Markdown, `map_compiler.py`) must fail untolerated. Counts in the report come from `_map_verdict`, not from the LLM. A real mercury-2.5 run dispatched 55 paths: 52 succeeded, 3 poison paths failed, and the 0.9 threshold was met (CLI exit 3 by design). (REQ-YG-703)
