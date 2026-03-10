---
type: feat
scope: adeletethread
---
- **`adelete_thread()` and `delete_thread()`** methods in `SimpleRedisCheckpointer`
  - Delete all checkpoints for a given thread ID
  - Uses SCAN to find all keys matching thread pattern
  - Required for session cleanup in applications using Redis checkpointer
  - 3 new unit tests added
