---
type: feat
scope: chainmap
---
- **ChainMap serialization** in `SimpleRedisCheckpointer`
  - Fixes `TypeError: Cannot serialize <class 'collections.ChainMap'>` when graphs contain ChainMap in state
  - ChainMap serialized as `{"__type__": "chainmap", "value": {...}}`
  - Deserialized back to `ChainMap` instance
  - 2 new unit tests for ChainMap serialization
