---
type: fix
scope: map
req: REQ-YG-692
---
- **FR-1163 A failed strict map keeps its evidence and its cost**: when a `map` or `cached_map` join misses `min_success`, `MapCompletenessError` now carries the collect key, a snapshot of the collected rows and the failing dispatch's `MapFailure` records. `graph run` prints each failure (`#<index> <type>: <message>`), the collected count, the rows with `--full`, and the token and timing summaries before exiting 1; `--json` emits one `{"status": "failed", ...}` object. Any execution failure (including timeout and streaming error events) now prints enabled usage summaries once. Success output is unchanged. (REQ-YG-692)
