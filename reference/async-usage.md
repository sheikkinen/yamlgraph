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

## See Also

- [Streaming](streaming.md) - Token-by-token output
- [Interrupt Nodes](interrupt-nodes.md) - Human-in-the-loop
- [Checkpointers](checkpointers.md) - State persistence
