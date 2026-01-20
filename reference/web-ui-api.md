# Web UI + API Reference

Build HTMX-powered web UIs with FastAPI backends for interactive YAMLGraph pipelines.

---

## Architecture

```
Browser (HTMX) ──▶ FastAPI + Jinja2 ──▶ YAMLGraph Pipeline
     ◀── HTML fragments ◀── Session adapter ◀── Checkpointer
```

**Stack:** FastAPI + HTMX + Jinja2 templates

**Key Insight:** Server is stateless; all session state lives in the checkpointer.

---

## Directory Structure

```
examples/your_app/
├── api/
│   ├── app.py              # FastAPI application
│   ├── session.py          # Session adapter for graph
│   ├── routes/             # API routes
│   └── templates/          # Jinja2 templates + HTMX fragments
├── your-graph.yaml         # YAMLGraph pipeline
└── prompts/                # YAML prompts
```

See [examples/npc/api/](../examples/npc/api/) for a complete working example.

---

## Session Adapter

Wraps LangGraph with checkpointer-based persistence.

### Key Methods

| Method | Purpose |
|--------|---------|
| `start(...)` | Start new graph execution |
| `resume(input)` | Resume after interrupt with user input |
| `_is_resume()` | Check if session exists via checkpointer |
| `_parse_result(result)` | Extract structured data from graph output |

### Key Points

- Module-level checkpointer singleton (persists across requests)
- Use `REDIS_URL` env var for Redis, otherwise falls back to `MemorySaver`
- Detect interrupts via `__interrupt__` key in result dict
- Map node output: extract `value` from `{'_map_index': N, 'value': '...'}`

---

## Routes Pattern

### Form Handling

- Use `Form()` for single values
- Use `form_data.getlist("field")` for multi-value fields
- Return HTML fragments (not JSON)

### Error Responses

Return error template with 400 status (see `examples/npc/api/routes/encounter.py`).

---

## HTMX Templates

### Key Attributes

| Attribute | Purpose |
|-----------|---------|
| `hx-post="/encounter/start"` | POST to endpoint |
| `hx-target="#result"` | Element to replace |
| `hx-swap="innerHTML"` | How to swap content |
| `hx-disabled-elt="#btn"` | Disable during request |

### Fragment Pattern

Main page loads full HTML. HTMX requests return only the fragment to update.

```
templates/
├── base.html               # Full page layout
├── index.html              # Main page (extends base)
└── components/
    ├── turn_result.html    # Turn result fragment
    ├── encounter_state.html # Encounter state fragment
    └── error.html          # Error fragment
```

---

## Interrupt Handling

When graph hits an `interrupt` node:

1. `ainvoke()` returns with `__interrupt__` key
2. Session adapter returns `is_complete=False`
3. Template shows input form
4. User submits → `Command(resume=input)` resumes graph

---

## Checkpointer Options

| Type | Persistence | Config |
|------|-------------|--------|
| `MemorySaver` | In-memory only | Default (no env var) |
| `RedisSaver` | Persistent | Set `REDIS_URL` env var |

**Gotcha:** `--reload` restarts server → loses MemorySaver sessions.

**Production:** Set `REDIS_URL=redis://localhost:6379` for persistence.

---

## Running

```bash
# Development
uvicorn examples.your_app.api.app:app --reload --port 8000

# Production (stable, no reload)
uvicorn examples.your_app.api.app:app --port 8000 --workers 4
```

---

## See Also

- [examples/npc/api/](../examples/npc/api/) - Complete working example
- [graph-yaml.md](graph-yaml.md) - Graph configuration
- [prompt-yaml.md](prompt-yaml.md) - Prompt templates
