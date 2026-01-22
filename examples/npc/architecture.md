# NPC Example Architecture

This document describes the layered architecture of the NPC Encounter example, demonstrating how to build production-ready web applications with YAMLGraph.

---

## Overview

The NPC example implements a D&D-style encounter system where multiple NPCs react to player actions in real-time. It showcases:

- **YAML-defined graphs** for game logic
- **Human-in-the-loop** via interrupt nodes
- **Parallel processing** via map nodes
- **Web API** for browser-based UX
- **Session persistence** via checkpointing

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                         UX Layer                                 │
│  HTMX + Jinja2 Templates                                        │
│  - index.html (encounter setup form)                            │
│  - components/turn_result.html (reactive updates)               │
│  - SSR fragments, no frontend framework                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP POST (hx-post)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer                                │
│  FastAPI + async routes                                         │
│  - api/app.py: FastAPI app, static mounts, lifespan             │
│  - api/routes/encounter.py: /start, /turn endpoints             │
│  Returns HTML fragments for HTMX consumption                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │ EncounterSession wrapper
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Session Adapter Layer                        │
│  api/session.py: EncounterSession class                         │
│  - Wraps compiled LangGraph application                         │
│  - Maps session_id → thread_id for checkpointing                │
│  - Handles GraphInterrupt for human-in-loop                     │
│  - Parses graph results into TurnResult dataclass               │
└───────────────────────────┬─────────────────────────────────────┘
                            │ ainvoke / Command(resume=...)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Graph Layer (YAMLGraph)                      │
│  encounter-multi.yaml                                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Nodes:                                                  │    │
│  │  • await_dm (interrupt) - Wait for DM input              │    │
│  │  • perceive_all (map) - All NPCs perceive in parallel    │    │
│  │  • decide_all (map) - All NPCs decide in parallel        │    │
│  │  • narrate_all (map) - All NPCs narrate in parallel      │    │
│  │  • summarize (llm) - Combine into turn summary           │    │
│  │  • describe_scene (llm) - Generate image prompt          │    │
│  │  • generate_scene_image (python) - Replicate API call    │    │
│  │  • next_turn (passthrough) - Increment turn counter      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  Checkpointer: SQLite (dev) or Redis (prod)                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │ execute_prompt
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Prompt Layer                               │
│  prompts/*.yaml                                                 │
│  - encounter_perceive.yaml: What does NPC notice?               │
│  - encounter_decide.yaml: What action to take?                  │
│  - encounter_narrate.yaml: Describe the action                  │
│  - encounter_summarize.yaml: Combine turn actions               │
│  - scene_describe.yaml: Image generation prompt                 │
│  Jinja2 templates with inline Pydantic schemas                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
examples/npc/
├── api/                          # Web API layer
│   ├── app.py                    # FastAPI application
│   ├── session.py                # Session adapter (graph wrapper)
│   ├── routes/
│   │   └── encounter.py          # HTTP endpoints
│   ├── templates/
│   │   ├── base.html             # Base layout
│   │   ├── index.html            # Encounter setup form
│   │   └── components/
│   │       ├── turn_result.html  # Turn result fragment
│   │       └── error.html        # Error display
│   └── static/                   # CSS, JS assets
│
├── nodes/                        # Custom Python nodes
│   └── image_node.py             # Replicate image generation
│
├── prompts/                      # LLM prompts (Jinja2 + schemas)
│   ├── encounter_perceive.yaml
│   ├── encounter_decide.yaml
│   ├── encounter_narrate.yaml
│   ├── encounter_summarize.yaml
│   ├── npc_identity.yaml
│   ├── npc_personality.yaml
│   └── ...
│
├── encounter-multi.yaml          # Main encounter graph
├── encounter-turn.yaml           # Single-turn graph (simpler)
├── encounter-loop.yaml           # Loop-based variant
├── npc-creation.yaml             # NPC generation graph
│
├── run_encounter.py              # CLI runner
├── demo.py                       # Automated demo script
├── README.md                     # Usage documentation
└── architecture.md               # This file
```

---

## Key Patterns

### 1. Session Adapter Pattern

The `EncounterSession` class wraps the compiled LangGraph with session management:

```python
class EncounterSession:
    def __init__(self, app, session_id: str):
        self._app = app
        self._config = {"configurable": {"thread_id": session_id}}

    async def start(self, npcs: list[dict], location: str) -> TurnResult:
        """Start new encounter."""
        initial_state = {"npcs": npcs, "location": location, ...}
        try:
            result = await self._app.ainvoke(initial_state, self._config)
            return self._parse_result(result)
        except GraphInterrupt:
            # Graph paused at interrupt node
            return TurnResult(turn_number=1, is_complete=False, ...)

    async def turn(self, dm_input: str) -> TurnResult:
        """Resume with DM input."""
        result = await self._app.ainvoke(
            Command(resume=dm_input),
            self._config
        )
        return self._parse_result(result)
```

**Benefits:**
- Session state lives in checkpointer (SQLite/Redis), not Python
- Stateless API servers - horizontally scalable
- Clean separation between HTTP and graph logic

### 2. Human-in-the-Loop Pattern

The graph pauses at `type: interrupt` nodes for human input:

```yaml
nodes:
  await_dm:
    type: interrupt
    message: |
      🎲 Turn {state.turn_number} - What happens next?
    resume_key: dm_input
```

The API resumes with:
```python
await self._app.ainvoke(Command(resume=user_input), config)
```

### 3. Parallel NPC Processing

All NPCs act simultaneously using `type: map` nodes:

```yaml
nodes:
  perceive_all:
    type: map
    over: "{state.npcs}"           # Fan out to all NPCs
    as: npc
    node:
      type: llm
      prompt: encounter_perceive
      variables:
        npc_name: "{state.npc.name}"
        npc_personality: "{state.npc.personality}"
    collect: perceptions           # Fan in results
```

LangGraph's `Send` mechanism enables true parallel execution.

### 4. HTMX Fragment Responses

API returns HTML fragments for dynamic updates:

```python
@router.post("/turn", response_class=HTMLResponse)
async def process_turn(request: Request, session_id: str, dm_input: str):
    session = await _get_session(session_id)
    result = await session.turn(dm_input)

    return templates.TemplateResponse(
        name="components/turn_result.html",
        context={"turn_number": result.turn_number, ...},
        headers={"HX-Trigger": "encounter-updated"},
    )
```

Frontend updates without JavaScript framework complexity.

---

## Data Flow

### Start Encounter

```
Browser                    API                    Session                   Graph
   │                        │                        │                        │
   │──POST /encounter/start─│                        │                        │
   │                        │──EncounterSession()───│                        │
   │                        │                        │──ainvoke(initial)─────│
   │                        │                        │                        │──START
   │                        │                        │                        │──await_dm
   │                        │                        │◀─GraphInterrupt────────│
   │                        │──TurnResult───────────│                        │
   │◀─HTML fragment─────────│                        │                        │
```

### Process Turn

```
Browser                    API                    Session                   Graph
   │                        │                        │                        │
   │──POST /encounter/turn──│                        │                        │
   │  (dm_input)            │                        │                        │
   │                        │──session.turn()───────│                        │
   │                        │                        │──Command(resume=...)──│
   │                        │                        │                        │──perceive_all (map)
   │                        │                        │                        │──decide_all (map)
   │                        │                        │                        │──narrate_all (map)
   │                        │                        │                        │──summarize
   │                        │                        │                        │──generate_image
   │                        │                        │                        │──next_turn
   │                        │                        │                        │──await_dm
   │                        │                        │◀─GraphInterrupt────────│
   │                        │◀─TurnResult───────────│                        │
   │◀─HTML fragment─────────│                        │                        │
```

---

## Checkpointing

Session state is persisted for resume across requests:

```python
def get_checkpointer():
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        # Production: Redis for persistence across restarts
        return RedisSaver.from_conn_string(redis_url)
    else:
        # Development: In-memory (lost on restart)
        return MemorySaver()
```

The graph is compiled with the checkpointer:

```python
graph = compile_graph(config)
app = graph.compile(checkpointer=get_checkpointer())
```

---

## Running the Example

### CLI Mode

```bash
# Single NPC turn
yamlgraph graph run examples/npc/encounter-turn.yaml \
  -v 'npc_name=Thorek' -v 'location=tavern'

# Multi-NPC encounter (interactive)
python examples/npc/run_encounter.py

# Automated demo
python examples/npc/demo.py --npcs 3 --rounds 5
```

### Web UI Mode

```bash
# Start server
uvicorn examples.npc.api.app:app --reload

# Open browser
open http://localhost:8000
```

### With Image Generation

```bash
export REPLICATE_API_TOKEN="your-token"
python examples/npc/demo.py --images
```

---

## Extending This Pattern

This architecture is reusable for any YAMLGraph web application:

1. **Define your graph** in YAML
2. **Create session adapter** wrapping the compiled graph
3. **Build API routes** that call session methods
4. **Return HTML fragments** for HTMX updates

See [reference/web-ui-api.md](../../reference/web-ui-api.md) for the general pattern.
