# Feature Request: Extract shared LLM retry/fallback logic to executor_base

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Rejected
**Effort:** 1 day
**Requested:** 2026-07-03

## Summary

The retry/backoff/structured-output-fallback logic in
`executor.py::PromptExecutor._invoke_with_retry` is duplicated in
`executor_async.py`. Copy-paste drift risk: retry counts, backoff timing,
schema-hint construction, and the FR-464 fallback can silently diverge
between sync and async callers. Extract the shared policy into
`executor_base.py`, which already holds shared message preparation.

## Value Statement

Sync and async graph executions get identical resilience behavior, and
future retry-policy fixes (e.g. FR-669) land in exactly one place.

## Problem

Two implementations of the same policy:

- `yamlgraph/executor.py` — `_invoke_with_retry`: retry loop,
  `is_retryable()` check, exponential backoff, structured-output attempt,
  FR-464 JSON-extraction fallback with `_build_schema_hint`
- `yamlgraph/executor_async.py` — parallel async implementation of the same
  sequence

The codebase convention is sync-first with async wrappers, and
`executor_base.py` already exists for exactly this sharing (holds
`is_retryable`, `format_prompt`, `prepare_messages`). The retry policy never
made it there. `executor_async.py` is also at 435 lines — one edit from the
450 ceiling — and shrinks naturally with this extraction.

## Proposed Solution

Add to `executor_base.py` a single policy function parameterized on the
invoke callable, so sync and async each supply their own transport:

```python
def build_invocation_plan(
    output_model: type[BaseModel] | None,
    messages: list,
) -> InvocationPlan:
    """Pure decision logic: structured vs plain, fallback messages,
    schema hint. No I/O — sync and async transports both consume it."""
```

Keep I/O (actual `invoke` / `ainvoke`, `asyncio.sleep` vs `time.sleep`) in
the respective executors; move all *decision* logic (what to try, when to
fall back, what the schema hint is, which errors are retryable, backoff
schedule computation) into `executor_base.py`.

Sequencing: land FR-669 (fallback error fix) first so the extracted logic
carries the corrected behavior, or fold FR-669 into this FR's RED phase.

## Acceptance Criteria

- [ ] Failing test first (RED): parametrized test asserting sync and async
      paths produce identical fallback messages and backoff schedule for the
      same inputs
- [ ] No retry/fallback decision logic remains duplicated between
      `executor.py` and `executor_async.py` (jscpd clean on these files)
- [ ] `executor_async.py` under 400 lines after extraction
- [ ] All unit + integration tests green
- [ ] Changelog fragment in `changelog/unreleased/`

## Alternatives Considered

- **Async wraps sync via `run_in_executor`** — rejected: blocks the event
  loop's thread pool for every LLM call; native async invocation is the
  point of `executor_async.py`.
- **Full `RetryPolicy` class with pluggable strategies** — rejected:
  speculative extensibility (Purge); one policy exists, extract a function.

## Related

- docs/2026-07-03-review-fable.md (Refactoring: sync/async retry duplication)
- FR-669 (fallback error fix — sequencing dependency)
- yamlgraph/executor.py, yamlgraph/executor_async.py, yamlgraph/executor_base.py

## Judgement

**REJECTED.** The core claim — that retry/fallback logic is duplicated
between `executor.py` and `executor_async.py` — is false. Verification
shows `executor_async.py` does NOT have `_invoke_with_retry`; it delegates
to `llm_factory_async.py` for invocation. The async path has inline
streaming exception handling (~lines 400-409) but this is streaming-specific
error handling, not retry/fallback duplication.

`executor_base.py` already holds the shared helpers (`is_retryable`,
`format_prompt`, `prepare_messages`). More importantly, async execution does
not share sync behavior: `utils/llm_factory_async.py::invoke_async` has no
retry loop and no FR-464 JSON fallback. That may be a future parity problem,
but it is not duplicated retry/fallback logic to extract.

The 435-line count for `executor_async.py` is accurate but is addressed by
FR-674 (module splits) if needed.
