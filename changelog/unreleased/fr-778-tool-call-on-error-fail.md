---
type: feat
scope: tools
req: REQ-YG-580
---
- **FR-778 tool_call `on_error: fail`**: prerequisite failures fail the graph
  at the tool node with the tool's actual error (exception chained) instead of
  a swallowed `{success: false}` envelope that downstream nodes trip over at a
  distance. Default `skip` keeps the envelope byte-identical for agent loops;
  graph load rejects `retry`/`fallback`/arbitrary values for tool_call naming
  the valid set `skip, fail`. (REQ-YG-580)
