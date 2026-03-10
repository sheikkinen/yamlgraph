---
type: feat
scope: tuple
---
- **Tuple dict key serialization** in `SimpleRedisCheckpointer`
  - Tuple keys serialized as `"__tuple__:[json_array]"` strings for orjson compatibility
  - LangGraph checkpoints use tuple keys in `channel_versions` and `versions_seen`
  - New `_stringify_keys()` / `_unstringify_keys()` for recursive key conversion
  - 4 new unit tests for tuple key serialization
