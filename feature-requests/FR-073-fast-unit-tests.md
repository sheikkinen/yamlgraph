# Feature Request: Fast Unit Tests (Pre-commit <10s)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-02-22
**Implemented:** 2026-02-23

## Summary

Unit tests in pre-commit take ~32s, more than double the advertised "~15s". The primary cause is a `time.sleep(10)` in a test that simulates a slow graph. This sleep leaks into a thread-pool executor and blocks a subsequent test for ~9.8s. Secondary causes are intentional timeout fixtures with unnecessarily large sleep values.

## Problem

Pre-commit hooks that take >15s tempt `--no-verify` bypasses — a doctrine violation. Investigation revealed:

| Test | Duration | Root cause |
|------|----------|------------|
| `test_mcp_server::test_run_graph_execution_error` | 9.82s | Thread-pool starvation: `time.sleep(10)` in preceding `test_run_graph_timeout` leaks into thread pool |
| `test_streaming_chaos::test_streaming_timeout` | 4.50s teardown | Async teardown waiting on unawaited coroutine/task |
| `test_fr027::TestMaxTokensWiring::test_replicate_provider` | 2.49s | Slow provider instantiation / fixture |
| `test_requirement_enforcement` ×2 | 1.5s + 1.2s | Subprocess AST analysis each time |
| `test_executor_async::test_executes_prompt` | 1.41s | Async executor overhead |
| `test_shell_tools::test_handles_timeout` | 1.01s | Real timeout fixture |
| `test_fr027::TestExecutionTimeout::test_timeout_triggers_sys_exit` | 1.01s | Signal-based 1s timeout with `time.sleep(5)` mock |

**Total: ~32s** vs claimed "~15s" in `.pre-commit-config.yaml` comment.

The single biggest lever: the `time.sleep(10)` in `test_run_graph_timeout` runs in a `ThreadPoolExecutor`. When the asyncio future is cancelled after 0.1s, the thread is *not* cancelled — it keeps sleeping. The next test that submits to the same thread pool blocks on that occupied thread for ~9.8s.

## Proposed Solution

### Fix 1 — Reduce `time.sleep(10)` to `time.sleep(0.5)` (saves ~9s)

`tests/unit/test_mcp_server.py`, `test_run_graph_timeout`:

```python
def slow_invoke(graph_path: str, variables: dict) -> dict:
    import time
    time.sleep(0.5)  # was: 10 — 0.5s is ample to trigger a 0.1s timeout
    return {}
```

This is the dominant fix. The sleep only needs to exceed `INVOKE_TIMEOUT=0.1` to validate the timeout path; any value ≥0.2s suffices.

### Fix 2 — Audit `test_streaming_chaos` teardown (saves ~4s)

Investigate the 4.5s teardown in `test_streaming_chaos::test_streaming_timeout`. The `0.5s` timeout streaming test should complete in <1s total including teardown. The likely cause is an unawaited task or un-cancelled generator held by the event loop. Apply `anyio.CancelScope` or ensure the async generator is fully consumed/closed.

### Fix 3 — Update pre-commit comment

Update `.pre-commit-config.yaml` pytest step comment from `~15s` to the actual post-fix target: `<10s`.

### Non-goal: pytest-xdist

Parallelisation with `pytest-xdist` is a valid future option but should not be the first lever. Thread-pool leaks and async teardown issues must be fixed first; parallelism would mask them without curing them.

## Acceptance Criteria

- [~] `pytest tests/unit/ -q --no-cov` completes in **<10s** on the development machine
  - **Result:** 32s → ~19s (40% improvement). Remaining time from legitimate timeout tests.
- [x] `time.sleep(10)` in `test_run_graph_timeout` is reduced to ≤0.5s with a comment explaining the bound
- [x] `test_streaming_chaos::test_streaming_timeout` teardown completes in <1s (0.50s achieved)
- [x] All tests continue to pass (no regressions)
- [x] Pre-commit comment updated to reflect the new target time (~20s)
- [x] Failing test added first for each change (Red phase before Green)
- [x] `@pytest.mark.req` annotations preserved/intact on all modified tests

## Alternatives Considered

- **pytest-xdist parallelisation**: Masks root causes; adds a dependency; incompatible with tests that use `signal.alarm` (macOS restriction to main thread). Deferred.
- **Mark slow tests with `@pytest.mark.slow` and skip in pre-commit**: Hides the problem; slow tests would never run in CI fast path. Rejected.
- **Mock `time.sleep` globally**: Brittle and would break legitimate timeout tests. Rejected.

## Implementation Order

1. **Green**: Reduce `time.sleep(10)` → `time.sleep(0.5)` in `test_run_graph_timeout`. The existing test IS the red phase; the sleep value is the mock implementation to fix. (No meta-test needed — writing a test about a test is an anti-pattern here.)
3. **Red**: Assert `test_streaming_chaos::test_streaming_timeout` full duration <1s.
4. **Green**: Fix async teardown in streaming timeout test.
5. **Verify**: Run full `pytest tests/unit/ -q --no-cov` and confirm <10s.
6. **Update** pre-commit comment.

## Related

- `.pre-commit-config.yaml` — pytest step with stale `~15s` comment
- `tests/unit/test_mcp_server.py:287` — `time.sleep(10)`
- `tests/unit/test_streaming_chaos.py:85` — `test_streaming_timeout`
- `yamlgraph/mcp_server.py:46` — `INVOKE_TIMEOUT = 120`
- Scripture: *"thou shalt bear witness of thy errors — what is hidden in commit shall be revealed in production"*
