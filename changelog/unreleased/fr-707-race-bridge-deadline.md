---
type: fix
scope: race
---
- **FR-707 Race Sync Bridge Deadline**: a race node's verdict now reaches the caller at the deadline instead of after every loser finishes. `_run_coro_sync_safe` runs the coroutine in a dedicated daemon thread on both entry paths and hands the result through a Future the moment it exists; loser cleanup drains post-verdict, bounded by `CLEANUP_GRACE` (5 s), logging a WARNING that names abandoned candidates. Previously one cancellation-ignoring provider connection blocked the caller's event loop for the losers' full lifetime (NC-361: 320–340 s production stall for a 10 s timeout; FR-706 witness: 5.01 s block for 0.5 s). `timeout: null` races keep an unbounded bridge; a bridge budget breach raises `RuntimeError` (invariant), never an anonymous `TimeoutError`. (REQ-YG-269)
