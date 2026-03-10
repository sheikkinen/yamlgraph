---
type: feat
scope: documentation
---
- **Documentation for error/errors design pattern**
  - `state_builder.py` - Explains `error` (singular, overwrite) vs `errors` (plural, accumulator)
  - `tool_nodes.py` - Clarifies nested tool result `error` is not state-level
  - `llm_nodes.py` - Notes `errors` uses add reducer for accumulation
