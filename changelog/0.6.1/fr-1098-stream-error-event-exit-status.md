---
type: fix
scope: cli
req: REQ-YG-694
---
- **FR-1098 `graph run --stream` exits 1 on an error event**: the streaming CLI printed a stream error event (LLM timeout, raised node) to stderr and still exited 0. It now exits 1 after printing it; a stream with no error event exits 0. Streaming claims no exit 3 and reads no final state (`reference/streaming.md`). (REQ-YG-694)
