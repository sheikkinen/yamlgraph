---
type: feat
scope: llm
req: REQ-YG-725
---
- **FR-1151 An `effort` setting for Anthropic llm nodes**: `effort: low | medium | high | xhigh | max` on graph `defaults` and on `llm` nodes (and `router` nodes without `candidates`), node over defaults, is sent to the Anthropic API as `output_config.effort`. Omitted, every request is unchanged. On any other resolved provider it raises before a client is built; on a race node or a router with `candidates` it is refused at load. `effort` is part of the LLM cache key. (REQ-YG-725)
