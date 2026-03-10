---
type: feat
scope: async
---
- **Async checkpointer factory** - New `get_checkpointer_async()` function
  - Properly initializes async checkpointers with `await saver.asetup()`
  - Deprecated `async_mode=True` parameter on `get_checkpointer()`
  - Added `shutdown_checkpointers()` for graceful cleanup
