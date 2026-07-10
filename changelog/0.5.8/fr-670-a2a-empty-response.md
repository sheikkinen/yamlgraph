---
type: fix
scope: a2a
---
- **FR-670 A2A empty response raises**: `_extract_text_from_result` raises `ValueError` on empty A2A responses instead of returning silent empty string.
