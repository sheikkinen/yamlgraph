---
type: feat
scope: checkpointer
---
- **Checkpointer Factory** with Redis support
  - Configure checkpointers in YAML: `memory`, `sqlite`, `redis`
  - Async variants: `redis_async`, `memory` (for async)
  - Environment variable expansion in connection strings
  - Optional dependency: `pip install yamlgraph[redis]`
  - See [reference/checkpointers.md](reference/checkpointers.md)
