---
type: fix
scope: race
req: REQ-YG-266
---
- **FR-267 Race Node Timeout Fix**: Remove `_maybe_wrap_timeout` from `_compile_race_node` — race nodes own timeout natively via `as_completed(timeout=...)`. The double ThreadPoolExecutor wrap silently discarded return values. Handle `TimeoutError` in race node to produce `PipelineError(TIMEOUT_ERROR)` respecting `on_error` config. (REQ-YG-266)
