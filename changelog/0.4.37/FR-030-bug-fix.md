---
type: fix
scope: bug
---
- **FR-030 Bug Fix: Dict token crash**: Router nodes emit dict content (classification result) which caused callers to crash with `TypeError`. Added `isinstance(chunk.content, str)` guard to filter non-string tokens.
