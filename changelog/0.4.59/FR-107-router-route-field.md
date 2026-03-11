---
type: feat
scope: router
---
- **FR-107 Router `route_field`**: Router nodes now require explicit `route_field` config naming the schema field that holds the route key. Replaces hardcoded `tone`/`intent` extraction in `llm_nodes.py`. Pydantic validator enforces presence for `type: router` nodes. All 10 router nodes across 6 graphs + 2 snippet templates updated. NC-111 (Pydantic object in state) solved by design — extracting the named field yields a string.
