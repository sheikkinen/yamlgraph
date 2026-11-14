---
type: fix
scope: config
req: REQ-YG-060
---
- **FR-1165 Graph-level `config.max_tokens` is refused at load**: the key was documented and parsed but never applied to any LLM call, so every call ran at the provider default. Loading a graph that sets it now raises `ValueError` naming `defaults.max_tokens`, the graph-wide setting that is applied (node `max_tokens` still overrides it). The key is removed from `graph-v1.json` and `reference/graph-yaml.md`. (REQ-YG-060)
