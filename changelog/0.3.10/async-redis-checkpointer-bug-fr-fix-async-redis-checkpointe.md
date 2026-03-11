---
type: fix
scope: async
---
- **Async Redis checkpointer bug** (FR fix-async-redis-checkpointer)
  - `AsyncRedisSaver.from_conn_string()` returns context manager, not saver instance
  - Sync Redis now uses direct instantiation: `RedisSaver(redis_url=url)`
  - Async Redis uses `get_checkpointer_async()` for proper initialization
  - `compile_graph_async()` is now properly async
