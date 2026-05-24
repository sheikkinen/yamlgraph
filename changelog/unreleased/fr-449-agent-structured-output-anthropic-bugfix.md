---
type: fix
scope: agent
req: REQ-YG-422
---
- **FR-449 Agent Structured Output Anthropic Bugfix**: Fixed agent nodes returning prose strings instead of validated dicts with Anthropic provider. Normalized content blocks, appended HumanMessage before fallback invoke, added debug logging for silent parse failures. (REQ-YG-422)
