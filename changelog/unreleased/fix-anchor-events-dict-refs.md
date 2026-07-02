---
type: fix
scope: novel-fandom
---
- **anchor_events dict reference fix**: Normalize dict-format references (`{"id": "..."}`) to string IDs before set construction. Prevents `unhashable type: dict` crash during worldgen regional scoping.
