---
type: feat
scope: philosopher
req: REQ-YG-194
---
- **FR-194 Philosopher World Context**: Add `load_context` python node that reads `docs/world-context.md` into graph state, enriching the `reflect` prompt with external ecosystem context. Path configurable via `world_context_path` state key. Graceful degradation when file absent. (REQ-YG-194)
