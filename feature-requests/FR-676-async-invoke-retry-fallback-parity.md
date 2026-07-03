# Feature Request: Async invoke parity — retry and structured-output fallback

**Priority:** MEDIUM
**Type:** Bug
**Status:** Enforced
**Effort:** 1 day
**Requested:** 2026-07-03

## Summary

`utils/llm_factory_async.py::invoke_async` has no retry loop, no backoff,
and no FR-464 structured-output fallback — while the sync path
(`executor.py::_invoke_with_retry`) has all three. Async resilience diverges
by transport: an async graph fails on the first transient error the sync CLI
silently survives. Add retry-with-backoff and the structured-output fallback
to the async path, matching sync semantics. Successor to rejected FR-672,
reframed per the Judgement: this is a parity gap, not duplication.

## Value Statement

A2A server, native streaming, and FastAPI callers get the same resilience
against transient provider errors (429/529/timeouts) as the sync CLI,
instead of failing where sync would recover.

## Problem

Verified (2026-07-03 session):

- `yamlgraph/utils/llm_factory_async.py:73-94` — `invoke_async` calls
  `with_structured_output` and nothing else: no retry, no `is_retryable`,
  no backoff, no JSON-extraction fallback
- `yamlgraph/executor.py::_invoke_with_retry` — retries up to `MAX_RETRIES`
  with exponential backoff on `is_retryable()` errors, and degrades to
  JSON extraction when a provider rejects `response_format` (FR-464)

The codebase convention is sync-first with async wrappers — a promise of
equivalent behavior through a different transport. Today the resilience
characteristics differ by transport, and the gap lands on exactly the
surfaces where retries matter most: long-running streaming runs and remote
A2A calls. Invisible until a production incident under provider load —
a Commandment 9 operational-truth gap.

FR-672's Judgement named this: "That may be a future async parity problem."
The gap exists now; only its symptom is deferred.

## Proposed Solution

In `llm_factory_async.py::invoke_async`:

1. Retry loop mirroring sync: `MAX_RETRIES`, `is_retryable()` (already
   shared in `executor_base.py`), exponential backoff via
   `asyncio.sleep` (never `time.sleep`).
2. FR-464 fallback mirroring sync: on `response_format` rejection, append
   the schema hint, plain-invoke, `extract_json`, validate — in the
   FR-669-corrected form (raise extraction failure with snippet,
   `from struct_err`).
3. Move/share pure decision helpers from their current homes: `is_retryable`
  already lives in `executor_base.py`, while `_build_schema_hint` currently
  lives privately in `executor.py` and should be moved to `executor_base.py`
  (or another shared non-layer-violating module) before async uses it. Only
  transport (thread-pool invoke / async sleep) should differ.

Sequencing: after FR-669 lands, so the fallback is copied in its corrected
form rather than porting the bare-`raise` defect to a second location.

Out of scope (Purge): retry-policy configurability, per-provider retry
tuning, circuit breakers.

## Acceptance Criteria

- [ ] Failing test first (RED): async invoke against a mock LLM that raises
      a retryable error once then succeeds → currently raises, must return
      the success; sibling sync test already passes
- [ ] Failing test (RED): async structured output where provider rejects
      `response_format` and plain response contains JSON → parsed model
      returned (parity with FR-464)
- [ ] No-JSON fallback case raises extraction error with snippet
      (parity with FR-669)
- [ ] Backoff uses `asyncio.sleep`; no event-loop blocking (no `time.sleep`)
- [ ] Retry counts/backoff schedule identical to sync for the same inputs
- [ ] `_build_schema_hint` or its replacement lives in shared code; async does
  not import private helpers from `executor.py`
- [ ] All unit tests green
- [ ] Changelog fragment in `changelog/unreleased/`

## Alternatives Considered

- **Extract a shared retry engine first (FR-672 approach)** — rejected by
  Judgement: there is no duplicated logic to extract yet. Implement parity
  first; if the two implementations later drift, extraction becomes a
  proven need instead of speculation.
- **Wrap sync `_invoke_with_retry` via `run_in_executor`** — rejected:
  blocks the thread pool per LLM call; native async invocation is the
  point of the async path.
- **Accept divergence, document it** — rejected: documentation does not
  survive a 3 a.m. incident; the convention promises parity.

## Related

- FR-672 (rejected predecessor — Judgement identified this parity gap)
- FR-669 (sequencing dependency: corrected fallback form)
- docs/diary/diary-2026-07-03-the-subagents-confident-inventory.md
- yamlgraph/utils/llm_factory_async.py:73-94
- yamlgraph/executor.py (`_invoke_with_retry`), yamlgraph/executor_base.py

## Judgement

**APPROVED WITH AMENDMENTS.** FR-672 was correctly rejected as a false
duplication claim, and this FR reframes the real issue: async invocation has
weaker behavior than sync invocation. The code facts check out:
`invoke_async` calls `with_structured_output(...).invoke(...)` or
`llm.invoke(...)` once inside a thread-pool wrapper; it has no retry loop, no
`is_retryable`, no backoff, and no FR-464 JSON fallback. The sync executor has
all of those.

**Amendments:**
1. Do not import `_build_schema_hint` from `executor.py` in async code. Move it
  to shared code (`executor_base.py` is the natural home) as part of the RED /
  GREEN change, then update sync and async callers.
2. Be precise about transport: the current async path is not native provider
  async; it wraps sync calls in `run_in_executor`. The fix should preserve
  that architecture and use `asyncio.sleep` between attempts outside the
  thread-pool call.
3. Sequence after FR-669 or include FR-669's corrected fallback behavior in
  the same enforcement branch. Do not port the current bare-`raise` defect
  into async.
4. Keep policy configurability out of scope. Match the existing sync constants
  and retryability predicate first.
