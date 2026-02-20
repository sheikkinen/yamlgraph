# Feature Request: Filter non-AI messages from agent node streaming

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-02-20

## Summary

`run_graph_streaming_native` emits **all** message types (SystemMessage, HumanMessage, ToolMessage, AIMessage) from agent nodes. Only AIMessage content should be yielded to clients.

## Problem

When an agent node executes, LangGraph's `stream_mode="messages"` surfaces every message object in the agent's internal conversation loop:

1. **SystemMessage** — the full system prompt (leaks prompt text to client)
2. **HumanMessage** — the user's input (duplicated back to client)
3. **AIMessage with tool_calls** — intermediate "I need to call tool X" responses
4. **ToolMessage** — tool execution results (raw search data)
5. **AIMessage (final)** — the actual answer to stream

The current filter in `executor_async.py` only checks:
```python
if hasattr(chunk, "content") and chunk.content and isinstance(chunk.content, str):
    yield chunk.content
```

This passes through System, Human, and Tool messages because they all have string `.content`. The result is that clients receive the system prompt, echoed user input, and raw tool results interleaved with the actual answer.

**Observed in production:** Terveystalo RAG agent node streams 11K chars of system prompt text before the actual answer. Follow-up turns echo the user message. Tool results leak raw Tavily search data.

## Proposed Solution

Filter by message type in `run_graph_streaming_native`. Only yield content from `AIMessageChunk` (or `AIMessage`):

```python
from langchain_core.messages import AIMessageChunk

async for event in app.astream(
    initial_state, config, stream_mode="messages", subgraphs=subgraphs
):
    if subgraphs:
        _namespace, payload = event
        chunk, metadata = payload
    else:
        chunk, metadata = event

    node_name = metadata.get("langgraph_node")
    if node_filter and node_name != node_filter:
        continue

    # Only yield AI message content (skip System, Human, Tool messages)
    if (
        isinstance(chunk, AIMessageChunk)
        and chunk.content
        and isinstance(chunk.content, str)
        and not chunk.tool_calls  # skip intermediate tool-calling responses
    ):
        yield chunk.content
```

The `not chunk.tool_calls` guard filters out intermediate agent iterations where the LLM decides to call a tool — those responses often have explanatory text ("Let me search for that...") that shouldn't be streamed.

### Alternative: metadata-based filter

LangGraph metadata includes `langgraph_step` and potentially message type info. A metadata-based filter could also work but is less explicit.

## Acceptance Criteria

- [x] Only `AIMessageChunk` content is yielded from `run_graph_streaming_native`
- [x] SystemMessage, HumanMessage, ToolMessage content is suppressed
- [x] AIMessage with `tool_calls` (intermediate agent steps) is suppressed
- [x] AIMessage without `tool_calls` (final answer) is streamed
- [x] Existing LLM node streaming (non-agent) is unaffected
- [x] Router node dict content remains filtered (existing behavior)
- [x] Tests for agent node streaming added
- [x] No regression in subgraph streaming

## Alternatives Considered

1. **Client-side filtering** — SSE proxy strips non-answer content. Fragile, leaks prompt data over the wire.
2. **`node_filter` parameter** — Already exists but cannot distinguish internal agent iterations from final answer within same node.
3. **Separate answer node downstream** — Add a passthrough LLM node after agent that streams. Adds latency and complexity.

## Related

- `yamlgraph/executor_async.py` L350-380 — current streaming filter
- `yamlgraph/tools/agent.py` — agent node implementation
- FR-057 — agent messages quadratic growth (related, already fixed in 0.4.49)
- `questionnaire-api/src/api/routes/streaming.py` — consumer of streaming tokens
