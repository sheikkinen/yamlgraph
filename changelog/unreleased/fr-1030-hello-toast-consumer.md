---
type: feat
scope: hello
req: REQ-YG-672
---
- **FR-1030 Hello demo announces its greeting**: `examples/demos/hello/graph.yaml` — the repository's quickstart graph — now ends with a `tool_call` node that submits the greeting it just generated as a desktop notification, using the shared `send_toast` tool declared by manifest (`../../shared/send_toast.tool.yaml`). The smallest demo therefore also demonstrates manifest-backed tool calls with zero Python in the demo directory. The node declares `on_error: skip`, so a host with no notifier still reaches `END` with a visible FR-778 failure envelope in `state.notified` rather than a swallowed error, and its verification question is `"Will contain submitted"` — the literal appears only in a real success envelope, unlike the vacuous `"Will return non-empty"`, which the non-empty failure envelope would also satisfy. The graph description and the demo README both disclose the side effect. (REQ-YG-672)
