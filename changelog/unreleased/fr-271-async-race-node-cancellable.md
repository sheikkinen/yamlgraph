---
type: feat
scope: race
req: REQ-YG-270
---
- **FR-271 Async Race Node**: Rewrote `race_node.py` to use asyncio instead of `ThreadPoolExecutor`. Losing candidates are cooperatively cancelled via `asyncio.Task.cancel()` after the winner is found, eliminating orphan HTTP connections and interpreter-exit delays. `_run_coro_sync_safe` bridges sync `node_fn` to the async core without event-loop conflicts under both `invoke` and `ainvoke` execution paths. (REQ-YG-270)
