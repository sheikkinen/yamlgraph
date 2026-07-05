---
type: feat
scope: novel-fandom
---
- **FR-689 Integrated Dedup Gate**: Dedup pre-check integrated into all 6 create_* graph-tool pipelines as mechanical gate. Standalone dedup_check removed from agent tools. Added update_refs tool for dangling ref repair. Final gate now scans filesystem directly for cross-type ID collisions. (REQ-YG-517)
- **Graph Variables Injection Fix**: Graph-level `variables:` from child YAML now correctly injected into graph-tool state via `make_graph_tool_fn()` and CLI initial state via `_build_run_config()`. Root cause of create_* "unknown entity_type" error.
