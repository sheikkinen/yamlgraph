# Async Usage

YAMLGraph provides async APIs for web frameworks (FastAPI, Starlette) and concurrent pipelines.

## Quick Start

```python
import asyncio
from yamlgraph.executor_async import (
    execute_prompt_async,
    execute_prompt_streaming,
    load_and_compile_async,
    run_graph_async,
)

async def main():
    # Single prompt
    result = await execute_prompt_async("greet", {"name": "World"})

    # Streaming
    async for token in execute_prompt_streaming("greet", {"name": "World"}):
        print(token, end="", flush=True)

    # Full graph
    app = await load_and_compile_async("graphs/my-graph.yaml")
    result = await run_graph_async(app, {"input": "hello"}, config)

asyncio.run(main())
```

## Functions

### execute_prompt_async

Execute a YAML prompt asynchronously.

```python
result = await execute_prompt_async(
    prompt_name="greet",
    variables={"name": "World"},
    output_model=GreetingResponse,  # Optional Pydantic model
    temperature=0.7,
    provider="mistral",
)
```

### execute_prompt_streaming

Stream tokens as they're generated.

```python
async for token in execute_prompt_streaming(
    prompt_name="greet",
    variables={"name": "World"},
    provider="mistral",
):
    print(token, end="", flush=True)
```

> **Note**: Streaming does not support `output_model`. Use `execute_prompt_async` for structured output.

### execute_prompts_concurrent

Execute multiple prompts in parallel.

```python
results = await execute_prompts_concurrent([
    {"prompt_name": "summarize", "variables": {"text": doc1}},
    {"prompt_name": "summarize", "variables": {"text": doc2}},
    {"prompt_name": "summarize", "variables": {"text": doc3}},
])
```

### load_and_compile_async

Load and compile a graph for async execution.

```python
app = await load_and_compile_async("examples/demos/interview/graph.yaml")
```

Automatically uses async-compatible checkpointer and the process-global `GRAPH_CACHE`:
- **First call**: compiles the graph and caches it (logs `INFO Compiling graph: ...`)
- **Subsequent calls**: returns the cached compiled graph (logs `DEBUG Cache hit: ...`)
- **Opt-out**: pass `cache=None` to force recompilation (useful in tests)

```python
# Disable cache for test isolation
app = await load_and_compile_async("graph.yaml", cache=None)
```

### GRAPH_CACHE and clear_cache

The process-global cache lives in `yamlgraph.graph_cache`:

```python
from yamlgraph.graph_cache import GRAPH_CACHE, clear_cache

# Inspect cached graphs
print(list(GRAPH_CACHE.keys()))

# Clear all cached graphs (test teardown, hot-reload)
clear_cache()
```

Compiled graphs are stateless (thread state lives in the checkpointer), so sharing across concurrent invocations is safe.

### run_graph_async

Execute a compiled graph asynchronously.

```python
result = await run_graph_async(
    app,
    initial_state={"input": "hello"},
    config={"configurable": {"thread_id": "t1"}},
)
```

### compile_graph_async

Compile a StateGraph with async checkpointer.

```python
from yamlgraph.graph_loader import load_graph_config, compile_graph
from yamlgraph.executor_async import compile_graph_async

config = load_graph_config("graphs/my-graph.yaml")
state_graph = compile_graph(config)
app = compile_graph_async(state_graph, config)
```

## FastAPI Integration

With `GRAPH_CACHE` (FR-111), no manual global variable is needed — `load_and_compile_async` caches transparently:

```python
from fastapi import FastAPI
from langgraph.types import Command
from yamlgraph.executor_async import load_and_compile_async, run_graph_async

app = FastAPI()

@app.on_event("startup")
async def startup():
    # Warm the cache at startup — subsequent calls are instant
    await load_and_compile_async("graphs/interview.yaml")

@app.post("/chat/{thread_id}")
async def chat(thread_id: str, message: str):
    # Cache hit — no recompilation
    graph_app = await load_and_compile_async("graphs/interview.yaml")
    config = {"configurable": {"thread_id": thread_id}}
    result = await run_graph_async(graph_app, {"input": message}, config)

    if "__interrupt__" in result:
        return {"status": "waiting", "question": result["__interrupt__"][0].value}

    return {"status": "complete", "response": result.get("response")}

@app.post("/chat/{thread_id}/resume")
async def resume(thread_id: str, answer: str):
    graph_app = await load_and_compile_async("graphs/interview.yaml")
    config = {"configurable": {"thread_id": thread_id}}
    result = await run_graph_async(graph_app, Command(resume=answer), config)
    return {"response": result.get("response")}
```

See [examples/fastapi_interview.py](../examples/fastapi_interview.py) for complete example.

## Interrupt Handling

```python
from langgraph.types import Command

# Initial run
result = await run_graph_async(app, {"input": "start"}, config)

# Loop through interrupts
while "__interrupt__" in result:
    question = result["__interrupt__"][0].value
    answer = await get_user_input(question)  # Your input method
    result = await run_graph_async(app, Command(resume=answer), config)

# Graph complete
print(result)
```

## Concurrent Graph Execution

Run multiple graphs in parallel:

```python
import asyncio

async def process_user(user_id: str, query: str):
    config = {"configurable": {"thread_id": f"user-{user_id}"}}
    return await run_graph_async(app, {"query": query}, config)

# Process 10 users concurrently
results = await asyncio.gather(*[
    process_user(f"user-{i}", f"Query {i}")
    for i in range(10)
])
```

## Fire-and-Forget Integration

For event-driven orchestrators (FSMs, actor systems, message queues) where
`await`-ing a 2–30s LLM call blocks the main loop, use `asyncio.create_task`
to launch graph execution in the background and dispatch results via an
external channel.

### Pattern

```python
import asyncio
import logging
from typing import Any, Awaitable, Callable

from yamlgraph.executor_async import load_and_compile_async, run_graph_async

logger = logging.getLogger(__name__)

# Store references to prevent garbage collection
_background_tasks: set[asyncio.Task] = set()


async def launch_graph_background(
    graph_path: str,
    initial_state: dict[str, Any],
    on_success: Callable[[dict], Awaitable[None]],
    on_failure: Callable[[Exception], Awaitable[None]],
) -> None:
    """Fire-and-forget graph execution with result callback.

    The caller returns immediately. When the graph completes,
    on_success or on_failure is called from the event loop.
    """
    app = await load_and_compile_async(graph_path)

    async def _run() -> None:
        try:
            result = await run_graph_async(app, initial_state)
            await on_success(result)
        except Exception as e:
            logger.error("Background graph failed: %s", e)
            await on_failure(e)

    task = asyncio.create_task(_run())
    # prevent GC — task removes itself when done
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
```

### Guard Keys (Idempotency)

When the caller may re-enter (polling loops, FSM re-dispatch), use a
state-keyed guard to prevent duplicate launches:

```python
async def guarded_launch(
    context: dict[str, Any],
    guard_key: str,
    graph_path: str,
    state: dict[str, Any],
    on_success,
    on_failure,
) -> None:
    """Launch graph only once per guard_key. Idempotent on re-entry."""
    if context.get(guard_key):
        return  # already launched — wait for callback

    context[guard_key] = True
    await launch_graph_background(graph_path, state, on_success, on_failure)
```

Clear stale guards when the caller transitions to a new phase:

```python
# Clear guards from previous phases on re-entry
stale = [k for k in context if k.startswith("_launched_") and k != guard_key]
for k in stale:
    del context[k]
```

### Result Dispatch

The `on_success` callback bridges graph output back to the orchestrator.
The channel depends on your system:

| Channel | Use case | Example |
|---------|----------|---------|
| Callback | In-process orchestrator | `await orchestrator.dispatch(event)` |
| Queue | Cross-process pipeline | `await queue.put(result)` |
| Socket | Separate server process | `sock.sendto(payload, path)` |
| HTTP | Remote service | `await client.post(url, json=result)` |

### Error Handling

Exceptions inside `create_task` are silent unless caught. The pattern above
catches in `_run()` and dispatches to `on_failure`. For unhandled task
exceptions, add a global handler:

```python
loop = asyncio.get_event_loop()
loop.set_exception_handler(lambda loop, ctx: logger.error(
    "Unhandled task error: %s", ctx.get("exception", ctx["message"])
))
```

## See Also

- [Streaming](streaming.md) - Token-by-token output
- [Interrupt Nodes](interrupt-nodes.md) - Human-in-the-loop
- [Checkpointers](checkpointers.md) - State persistence
- [Fire-and-Forget Integration](#fire-and-forget-integration) - Event-driven orchestrators
