# Feature Request: CLI --stream Flag

**Priority:** HIGH
**Type:** Feature
**Status:** Enforced
**Effort:** 1 day
**Requested:** 2026-07-01

## Summary

Add `--stream` flag to `yamlgraph graph run` that uses `run_graph_streaming_native()` for token-by-token output to stdout.

## Value Statement

CLI users get real-time LLM output instead of waiting for full graph completion, making YAMLGraph's #1 expected feature discoverable without writing Python.

## Problem

YAMLGraph has a fully functional streaming API (`run_graph_streaming_native()`) used by the A2A server and OpenAI proxy. But the CLI — the primary user-facing interface — has no streaming support. Users must write Python to access streaming, which contradicts the YAML-first paradigm.

Current CLI path: `app.invoke()` → waits → prints final state.
Needed: `app.astream(stream_mode="messages")` → prints tokens as they arrive → returns final state.

The streaming demo (`demos/streaming/`) bypasses the framework entirely with a raw Python script because there's no CLI path to demonstrate.

## Proposed Solution

Add `--stream` flag to `yamlgraph graph run`:

```bash
# Token-by-token output
yamlgraph graph run examples/demos/hello/graph.yaml --var name="World" --stream

# Combine with existing flags
yamlgraph graph run graphs/showcase.yaml --var topic="AI" --stream --full
```

Implementation in `yamlgraph/cli/graph_run_helpers.py`:

```python
# In _invoke_graph or _run_graph_until_complete:
if stream_mode:
    import asyncio
    from yamlgraph.executor_async import run_graph_streaming_native
    from yamlgraph.models.streaming import StreamEvent

    async def _stream():
        async for item in run_graph_streaming_native(graph_path, initial_state, config=config):
            if isinstance(item, StreamEvent):
                if item.type == "error":
                    print(f"\n❌ {item.error}", file=sys.stderr)
                elif item.type == "interrupt":
                    # Handle interrupt resume same as non-streaming
                    pass
            else:
                print(item, end="", flush=True)
        print()  # Final newline

    asyncio.run(_stream())
```

The `--stream` flag and `--json` are mutually exclusive (streaming outputs raw tokens, not JSON state).

## Acceptance Criteria

- [ ] `yamlgraph graph run <graph> --stream` prints tokens as they arrive
- [ ] Works with `--var` and `--full` flags
- [ ] `--stream` + `--json` produces clear error message
- [ ] Interrupt/resume works in streaming mode (prompts user, resumes)
- [ ] StreamEvent errors print to stderr
- [ ] Tests: mock LLM streaming test, CLI integration test
- [ ] `reference/streaming.md` updated with CLI section

## Alternatives Considered

1. **Per-node `stream: true` in YAML** — Already exists in code but is architecturally broken (creates async generator that `invoke()` can't consume). Graph-level streaming via `astream()` is the correct approach because LangGraph handles it transparently for all LLM nodes.

2. **Separate `yamlgraph graph stream` command** — Unnecessary complexity. A flag on `run` is more discoverable and consistent with how other tools work (`curl --stream`, `docker logs --follow`).

## Related

- `yamlgraph/executor_async.py:324` — `run_graph_streaming_native()`
- `yamlgraph/models/streaming.py` — `StreamEvent`
- `yamlgraph/cli/graph_run_helpers.py:168` — `_invoke_graph()` (needs streaming branch)
- `examples/openai_proxy/` — working streaming consumer
- `yamlgraph/a2a_server.py:150` — working streaming consumer
- FR-634 (streaming demo depends on this)
- FR-635 (dead code cleanup after this proves graph-level streaming)
