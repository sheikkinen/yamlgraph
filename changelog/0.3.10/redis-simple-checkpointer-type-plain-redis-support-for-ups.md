---
type: feat
scope: redis-simple
---
- **redis-simple checkpointer type** - Plain Redis support for Upstash/Fly.io (FR add-simple-redis-checkpointer)
  - New `SimpleRedisCheckpointer` class using standard Redis commands (GET, SET, SCAN, DEL)
  - No Redis Stack (RediSearch, RedisJSON) requirement
  - Uses `orjson` for secure JSON serialization (no pickle)
  - Supports both sync and async Redis operations
  - Stores only latest checkpoint per thread (no history)
  - New optional dependency: `pip install yamlgraph[redis-simple]`
