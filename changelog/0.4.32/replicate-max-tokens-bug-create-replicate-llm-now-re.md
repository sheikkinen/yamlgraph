---
type: fix
scope: replicate
req: REQ-YG-060
---
- **Replicate `max_tokens` bug**: `_create_replicate_llm()` now receives and forwards `max_tokens` via `**kwargs`. Previously silently dropped. (REQ-YG-060)
