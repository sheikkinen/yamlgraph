---
type: fix
scope: agent
req: REQ-YG-018
---
- **FR-057 Agent messages quadratic growth** (REQ-YG-018): Agent node now returns only new messages (delta) instead of the full conversation. The `add` reducer on `messages` was causing quadratic growth when agent nodes were invoked multiple times across interrupt boundaries. Both return paths (normal completion and max-iterations) now slice `messages[len(existing_messages):]`. Three new tests: delta return, 5-turn linear growth, max-iterations delta.
