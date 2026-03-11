---
type: feat
scope: npc
---
- **NPC Encounter Web API** - HTMX-powered web UI for running NPC encounters
  - FastAPI backend with session persistence (`examples/npc/api/`)
  - Session adapter pattern for stateless servers with checkpointer state
  - MemorySaver default, RedisSaver via `REDIS_URL` env var
  - Interrupt detection and resume with `Command(resume=input)`
  - Map node output parsing (`{'_map_index': N, 'value': '...'}`)
  - HTML templates with HTMX fragments
  - Integration tests (20 passing)
