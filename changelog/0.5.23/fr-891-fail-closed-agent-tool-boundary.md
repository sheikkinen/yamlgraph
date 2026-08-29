---
type: fix
scope: agent
---
- **FR-891 Fail-Closed Agent Tool Boundary**: an agent run whose tool calls
  all failed now raises `AllToolCallsFailedError` (with failure census)
  before final synthesis, on both finalization paths, instead of handing
  error strings to the LLM as evidence; `search_web` raises for empty
  query/missing ddgs and propagates transport errors instead of returning
  "Error: ..." strings. (REQ-YG-018)
