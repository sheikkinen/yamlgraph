---
type: fix
scope: promptsrelative
---
- **prompts_relative bug** - Complete fix for graph-relative prompt resolution
  - `node_factory.create_node_function()` now passes path params to executor
  - `create_interrupt_node()` now accepts and forwards path params
  - `graph_loader._compile_node()` extracts prompts config from defaults
  - Integration test verifies path params forwarded to `execute_prompt()`
