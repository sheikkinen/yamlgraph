---
type: fix
scope: caching
req: REQ-YG-289
---
- **FR-1055 Anthropic prompt-cache blocks never reached the API**: `system_segments` (and the list form of `system:`) built correct Anthropic content blocks and then stored them in `SystemMessage.additional_kwargs`, which `langchain_anthropic` never reads. The consequence was not merely that caching was off — the **entire system prompt was dropped** on every Anthropic call using either form, silently and without error. Blocks now go in `SystemMessage.content`, the documented list form, so `cache_control` reaches the wire and the instruction survives. Scalar `system:` was never affected. A new seam test walks the producer into `langchain_anthropic._format_messages` and doubles as a drift detector for the next message-handling change. (REQ-YG-289)
