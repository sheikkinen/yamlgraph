---
type: feat
scope: map
req: REQ-YG-075
---
- **FR-052 Map Output Flattening**: `flatten_output: true` option for map nodes — merges `_map_xxx_sub` contents into items, converts Pydantic models via `model_dump()`, preserves `_map_index` (REQ-YG-075)
  - `flatten_map_results()` function in `map_compiler.py`
  - `flatten_output` field in `NodeConfig` model
  - Wired through `wrap_for_reducer` in `compile_map_node`
