---
type: feat
scope: examples
req: REQ-YG-706
---
- **FR-1116 meta_map uses the map memo**: `examples/demos/meta_map` runs `memo_split` → `summarize` over changed files only → `memo_merge`, which applies `min_success: 0.9` over the whole population. A rerun with no changed file makes zero LLM calls and exits 0, and its report still lists the stored poison failures. Delete `outputs/meta_map/memo.sqlite` to force a full run. (REQ-YG-706)
