---
type: feat
scope: novel_fandom
req: REQ-YG-517
---
- **FR-684 Semantic Dedup Graph-Tool**: Added `semantic_dedup.yaml` graph-tool with LLM prompt including false-positive negative examples. Wired threshold router in worldgen: deterministic dedup → semantic dedup subgraph → apply_merge_map → create_skeletons. Registered `dedup_check` for `deepen_events` agent. Removed `_LLM_DEDUP_THRESHOLD` and TODO stub from `dedup_entities.py`. (REQ-YG-517)
