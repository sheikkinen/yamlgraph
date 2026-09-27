---
type: feat
scope: error
req: REQ-YG-715
---
- **FR-1124 Graph-level `defaults.on_error`**: `defaults.on_error` (`skip|retry|fail|fallback`) sets the error policy for top-level `llm` nodes; a node's own `on_error` wins. Invalid values fail graph load, and `defaults.on_error: fallback` is refused when an inheriting node has no `fallback.provider`. Router, race and map sub-nodes are unaffected. (REQ-YG-715)
