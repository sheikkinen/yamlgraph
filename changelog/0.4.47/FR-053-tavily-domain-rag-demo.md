---
type: feat
scope: tavily
req: REQ-YG-076
---
- **FR-053 Tavily Domain RAG Demo** (CAP-25, REQ-YG-076): Domain-scoped RAG with Tavily web search
  - Simple graph: retrieve → answer; Deep graph: plan → map(retrieve) → synthesize
  - Python tool node retrieves context via Tavily API with `TAVILY_TARGET_DOMAIN` scoping
  - 11 unit tests (all mocked, no API key needed)
  - `tavily` optional extra in pyproject.toml
