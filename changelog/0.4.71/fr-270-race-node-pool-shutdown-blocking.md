---
type: fix
scope: race
req: REQ-YG-269
---
- **FR-270 Race Node Pool Shutdown**: Replace `with ThreadPoolExecutor` context manager with explicit `pool.shutdown(wait=False, cancel_futures=True)` in `finally`; race node now returns winner state in `fast_candidate_time + ε` regardless of slow losers. (REQ-YG-269)
