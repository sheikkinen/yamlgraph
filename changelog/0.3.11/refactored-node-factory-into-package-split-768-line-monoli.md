---
type: feat
scope: refactored
---
- **Refactored node_factory into package** - Split 768-line monolith into focused modules
  - `base.py` (90 lines) - `resolve_class`, `get_output_model_for_node`
  - `llm_nodes.py` (208 lines) - `create_node_function`
  - `streaming.py` (72 lines) - `create_streaming_node`
  - `tool_nodes.py` (90 lines) - `create_tool_call_node`
  - `control_nodes.py` (147 lines) - `create_interrupt_node`, `create_passthrough_node`
  - `subgraph_nodes.py` (220 lines) - `create_subgraph_node`, state mapping helpers
  - All modules under 230 lines (limit: 400)
  - Public API unchanged via `__init__.py` re-exports
