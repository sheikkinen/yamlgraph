---
type: feat
scope: state-builder
req: REQ-YG-238
---
- **FR-238 Pipeline Accumulated State**: User-configurable reducers in YAML `state:` section via dict-syntax `{type: list, reducer: add}`. `REDUCER_MAP` exposes `add`, `last_value`, `sorted_add`. `generate_typeddict_code()` handles dict-syntax entries. Documented accumulated state pattern for pipelines in `reference/graph-yaml.md`. (REQ-YG-238)
