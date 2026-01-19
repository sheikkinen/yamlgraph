# Checkpointers

Checkpointers enable state persistence across graph executions. They're required for interrupt nodes and enable session resumption.

## Quick Start

```yaml
# graphs/my-graph.yaml
version: "1.0"
name: my-graph

checkpointer:
  type: memory  # In-memory (dev/testing)
  # type: sqlite
  # path: "./sessions.db"
  # type: redis
  # url: "${REDIS_URL}"
```

## Checkpointer Types

### Memory (Default)

In-memory storage. Data lost on restart. Good for development.

```yaml
checkpointer:
  type: memory
```

### SQLite

File-based persistence. Good for single-server deployments.

```yaml
checkpointer:
  type: sqlite
  path: "./sessions.db"  # Or ":memory:" for in-memory
```

### Redis

Distributed persistence. Required for multi-server deployments.

```yaml
checkpointer:
  type: redis
  url: "${REDIS_URL}"  # Environment variable expansion
  ttl: 60              # TTL in minutes (default: 60)
```

**Installation:**
```bash
pip install yamlgraph[redis]
```

## Environment Variables

Use `${VAR}` syntax for secrets:

```yaml
checkpointer:
  type: redis
  url: "${REDIS_URL}"  # Expands to redis://user:pass@host:6379
```

## Python API

### Sync Usage

```python
from yamlgraph.graph_loader import load_graph_config, compile_graph, get_checkpointer_for_graph

config = load_graph_config("graphs/my-graph.yaml")
graph = compile_graph(config)
checkpointer = get_checkpointer_for_graph(config)

app = graph.compile(checkpointer=checkpointer)

# Use with thread_id
result = app.invoke(
    {"input": "hello"},
    {"configurable": {"thread_id": "session-123"}}
)
```

### Async Usage

```python
from yamlgraph.executor_async import load_and_compile_async, run_graph_async

# Automatically uses async-compatible checkpointer
app = await load_and_compile_async("graphs/my-graph.yaml")

result = await run_graph_async(
    app,
    {"input": "hello"},
    {"configurable": {"thread_id": "session-123"}}
)
```

### Direct Factory Usage

```python
from yamlgraph.storage import get_checkpointer

# Sync checkpointer
checkpointer = get_checkpointer({
    "type": "redis",
    "url": "redis://localhost:6379",
    "ttl": 120,
})

# Async checkpointer (for FastAPI, etc.)
async_checkpointer = get_checkpointer(
    {"type": "redis", "url": "redis://localhost:6379"},
    async_mode=True,
)
```

## Async Mode

When using async graph execution, the factory automatically selects async-compatible checkpointers:

| Type | Sync | Async |
|------|------|-------|
| memory | `MemorySaver` | `MemorySaver` (supports both) |
| sqlite | `SqliteSaver` | `MemorySaver` (fallback) |
| redis | `RedisSaver` | `AsyncRedisSaver` |

> **Note**: SQLite async requires `aiosqlite` package. If not installed, falls back to `MemorySaver`.

## Thread ID

Every checkpointed session requires a unique `thread_id`:

```python
config = {"configurable": {"thread_id": "user-123-session-456"}}
result = app.invoke(state, config)
```

Common patterns:
- `f"user-{user_id}"` — One session per user
- `f"user-{user_id}-{uuid4()}"` — New session each time
- `f"conversation-{conversation_id}"` — Shared conversation

## Session Lifecycle

```
1. First invoke: Creates checkpoint
2. Interrupt: Saves state, returns __interrupt__
3. Resume: Loads checkpoint, continues from interrupt
4. Complete: Final state saved
```

To start fresh, use a new `thread_id`.

## See Also

- [Interrupt Nodes](interrupt-nodes.md) - Human-in-the-loop patterns
- [Async Usage](async-usage.md) - Async graph execution
- [FastAPI Example](../examples/fastapi_interview.py) - Web server integration
