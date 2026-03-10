---
type: fix
scope: node-level
req: REQ-YG-050
---
- **Node-level `model` override (REQ-YG-050)** — The `model` field in graph YAML node config and `defaults` was silently ignored. Only `temperature` and `provider` were extracted. Now `model` flows through the full call chain: `create_node_function()` → `execute_prompt()` → `prepare_messages()` → `create_llm()`. Priority: node config > defaults > prompt YAML > provider default. 8 new tests.
