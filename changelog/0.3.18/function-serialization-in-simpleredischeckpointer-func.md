---
type: feat
scope: function
---
- **Function serialization** in `SimpleRedisCheckpointer`
  - Functions/callables serialized as `{"__type__": "function", "value": null}`
  - Allows LangGraph internals that include callables to be checkpointed
  - 3 new unit tests for function serialization
