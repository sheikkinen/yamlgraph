---
type: feat
scope: examples
req: REQ-YG-435
---
- **FR-468 Dungeon Master Web UI — Server & Session**: New `examples/dungeon_master/api/`
  FastAPI app wraps both DM graphs. A stateless `DMSession` adapter preplans a story
  and drives the interrupt turn loop, detecting completion via `aget_state(...).next`
  and overriding the YAML `:memory:` checkpointer with a process-stable singleton
  (MemorySaver, or Redis when `REDIS_URL` is set). HTMX routes `POST /story/preplan`
  and `POST /story/turn` swap a single `#app-body` region. (REQ-YG-435)
