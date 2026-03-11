---
type: feat
scope: unit
---
- **FR-073 Unit test performance**: Reduced unit test time from 32s → ~19s (40% improvement)
  - `test_mcp_server.py`: `time.sleep(10)` → `time.sleep(0.5)` (thread-pool starvation fix)
  - `test_streaming_chaos.py`: `CHAOS_DELAY=5` → `CHAOS_DELAY=1` (async teardown speed)
