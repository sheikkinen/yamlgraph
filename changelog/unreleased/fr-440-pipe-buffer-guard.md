---
type: feat
scope: hooks
---
- **FR-440 Pipe-Buffer Guard**: PreToolUse hook denies `pytest ... | tail` and `pytest ... | head` without intermediate `tee`. Prevents silent output buffering that masks test hangs.
