# Feature Request: FR-209 Extend A2A Demo with Streaming Response

**Priority:** LOW
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-03-29

## Summary

Extend the A2A server demo (`examples/demos/a2a_server/demo.sh`) with a Part 3 that uses `message/stream` to show the complete task lifecycle — including the actual LLM-generated greeting — via Server-Sent Events.

## Value Statement

Demo users see the full A2A task lifecycle (working → artifact → completed) instead of an opaque `"state": "working"` response, making the protocol's streaming capability tangible.

## Problem

The current demo (FR-208) sends a task via `message/send` and shows:

```json
{
  "result": {
    "status": { "state": "working" }
  }
}
```

The user never sees the actual graph output. The Agent Card advertises `"streaming": true` but the demo never exercises it. This leaves the most compelling A2A capability — real-time event streaming — undemonstrated.

## Proposed Solution

Add a **Part 3** to `demo.sh` that calls `message/stream` and captures the SSE event stream. The A2A SDK's `DefaultRequestHandler.on_message_send_stream()` already wires `message/stream` to the same `YAMLGraphAgentExecutor.execute()` method, which emits `TaskStatusUpdateEvent` and `TaskArtifactUpdateEvent` via `EventQueue`. No production code changes are required.

### Demo script addition

```bash
# --- Part 3: Stream response via SSE ---
echo "🌊 Part 3: Stream response via message/stream (SSE)"
echo "  Method: message/stream → Server-Sent Events"
echo "---"

curl -sN -X POST "http://localhost:$PORT/" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "message/stream",
    "params": {
      "message": {
        "role": "user",
        "messageId": "demo-msg-2",
        "parts": [{"kind": "text", "text": "name=World style=casual"}]
      }
    }
  }' | timeout 30 cat
```

### Expected SSE output

The stream should include three event types in sequence:

1. **`TaskStatusUpdateEvent`** — `state: working` (graph execution started)
2. **`TaskArtifactUpdateEvent`** — contains the LLM-generated greeting text
3. **`TaskStatusUpdateEvent`** — `state: completed` (graph execution finished)

## Acceptance Criteria

- [ ] `demo.sh` has a Part 3 that sends `message/stream` and captures SSE events
- [ ] The streamed output includes at least: working status, artifact with greeting text, completed status
- [ ] `demo-output.log` is regenerated and includes the Part 3 SSE output
- [ ] Demo runs end-to-end without manual intervention (`demo.sh` exits 0)
- [ ] No production code changes — demo-only scope

## Constraints

- Reuse the existing server instance started in Part 2 (no second server)
- Use `timeout` or equivalent to prevent curl from hanging if the stream doesn't close
- Keep the demo self-contained — no additional dependencies or API keys beyond what Part 2 already requires

## Alternatives Considered

1. **Polling `tasks/get` after `message/send`**: Would show the completed task but not the real-time event stream. Misses the point of demonstrating SSE.
2. **Token-level streaming (REQ-YG-211)**: `task/sendSubscribe` with `run_graph_streaming_native()` is future work. The current `message/stream` already provides event-level streaming which is sufficient for the demo.
3. **Separate streaming demo**: Would duplicate server setup. Extending the existing demo is simpler and keeps all A2A capabilities in one place.

## Implementation Notes

- The A2A SDK's `on_message_send_stream()` yields events as an `AsyncGenerator[Event]`, which `A2AStarletteApplication` serializes as `text/event-stream` SSE.
- The `execute()` method in `a2a_server.py` already closes the `EventQueue` on completion, which signals end-of-stream to the SSE consumer.
- The `demo-gate` CI check (FR-206) requires `demo-output.log` in the diff for changes under `examples/demos/a2a_server/`.

## Related

- **FR-208**: A2A Protocol Server (parent feature, CAP-81)
- **REQ-YG-208**: Agent Card with `streaming=True`
- **REQ-YG-211**: `task/sendSubscribe` SSE streaming (future — not required for this FR)
- `examples/demos/a2a_server/demo.sh`: File to modify
- `yamlgraph/a2a_server.py`: `YAMLGraphAgentExecutor.execute()` (no changes needed)
