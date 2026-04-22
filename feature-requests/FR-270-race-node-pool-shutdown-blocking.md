# Feature Request: FR-270 Race node blocks on slow losers due to `with` pool shutdown

**Priority:** HIGH
**Type:** Bug
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-04-22
**FR:** FR-270
**Judged:** 2026-04-22

## Summary

Race nodes block until the slowest candidate finishes, not the fastest. `node_fn` wall-clock is
`max(candidates)` instead of `min(candidates)`. Returning inside a `with ThreadPoolExecutor(...)` block
triggers `pool.shutdown(wait=True)` in `__exit__`, stalling state delivery to LangGraph until every
in-flight HTTP call completes. Combined with FR-267's timeout bug, this is the root cause of the silent
state-drop described in issue #152.

## Value Statement

Graph authors using race nodes get true race-to-first semantics: the winner's state reaches LangGraph
in `fast_candidate_time + ε`, never in `max(candidates)` time — regardless of how slow the losers are.

## Problem

`race_node.py` races candidates inside a `with ThreadPoolExecutor(max_workers=len(llms)) as pool:` block:

```python
with ThreadPoolExecutor(max_workers=len(llms)) as pool:
    futures = {pool.submit(_invoke_candidate, ...): cand for ...}
    try:
        for future in as_completed(futures, timeout=timeout):
            result = future.result()
            for f in futures:
                f.cancel()    # ← no-op for already-running futures (CPython docs)
            ...
            return ret        # ← triggers pool.__exit__ → shutdown(wait=True)
```

Two concrete misbehaviours:

1. **`Future.cancel()` is a no-op** for futures already executing (CPython contract). Loser HTTP calls
   are never interrupted.
2. **`return` inside `with` triggers `pool.shutdown(wait=True)`** in `__exit__`. The race node cannot
   deliver the winner's state to LangGraph until every loser finishes — even if the winner returned
   seconds ago.

Measured in the `medical_triage` graph with a fast Anthropic winner and a slow Vertex loser:

```
t=0.0   race starts; anthropic + vertex fired concurrently
t=1.8   anthropic returns; race logs "winner"; return ret
t=1.8→  with __exit__ → shutdown(wait=True) — blocked on vertex
t=8–10  vertex's HTTP call completes; pool exits
t=8–10  LangGraph finally receives the winner state dict
```

When FR-267's outer-timeout bug is also present, the outer `_maybe_wrap_timeout` fires at `timeout=10s`
while the inner `shutdown(wait=True)` is still blocking, causing the outer wrapper to return
`{state_key: None, errors: [TIMEOUT_ERROR]}` and overwrite the winner result entirely.

This FR targets the `shutdown(wait=True)` root cause in `race_node.py`, independent of the
outer-wrapper fix in FR-267.

## Proposed Solution

Replace the `with` context manager with explicit pool lifecycle management. Call
`pool.shutdown(wait=False, cancel_futures=True)` in a `finally` block so that the winner is returned
immediately and loser threads are abandoned to complete (and discard) their results naturally.

```python
pool = ThreadPoolExecutor(max_workers=len(llms))
try:
    futures = {
        pool.submit(_invoke_candidate, llm, messages, output_model, parse_json): candidate
        for llm, candidate in zip(llms, candidates, strict=True)
    }
    try:
        for future in as_completed(futures, timeout=timeout):
            candidate = futures[future]
            try:
                result = future.result()
                logger.info(
                    "Race node %s: winner %s/%s",
                    node_name,
                    candidate.get("provider", "?"),
                    candidate.get("model", "?"),
                )
                return {
                    state_key: result,
                    "_race_winner": {
                        "provider": candidate.get("provider"),
                        "model": candidate.get("model"),
                    },
                    "current_step": node_name,
                    "_loop_counts": loop_counts,
                }
            except Exception as e:
                logger.warning(
                    "Race candidate %s/%s failed: %s",
                    candidate.get("provider", "?"),
                    candidate.get("model", "?"),
                    e,
                )
                errors.append((candidate, e))
    except TimeoutError:
        timeout_exc = TimeoutError(f"Race {node_name} timed out after {timeout}s")
        if on_error == ErrorHandler.SKIP:
            return {
                state_key: None,
                "current_step": node_name,
                "_loop_counts": loop_counts,
                "errors": [
                    PipelineError.from_exception(
                        timeout_exc,
                        node=node_name,
                        error_type=ErrorType.TIMEOUT_ERROR,
                    )
                ],
            }
        raise AllCandidatesFailedError(errors + [({}, timeout_exc)]) from timeout_exc
finally:
    # Race-to-first: abandon any still-running losers without waiting.
    # Loser threads die naturally when their HTTP calls return; their results are discarded.
    pool.shutdown(wait=False, cancel_futures=True)
```

Note: the `TimeoutError` handling in the `try/except` block above is the same fix proposed in FR-267
(Change 2). This FR and FR-267 address orthogonal bugs that can be fixed independently, but both must
land for the full correctness guarantee: FR-267 removes the outer wrapper, this FR ensures the inner
pool doesn't block on losers.

## Acceptance Criteria

- [ ] Race node returns within `fast_candidate_time + ε` (< 1s) even when slow candidates take ≫ 1s
- [ ] Condemning test `test_race_returns_on_first_success_not_after_slowest` passes (see below)
- [ ] Winner's `state_key`, `_race_winner`, `current_step`, `_loop_counts` are all present in the returned dict
- [ ] Slow candidates' threads continue (and finish) in the background but do not block the return
- [ ] `race_node.py` no longer uses `with ThreadPoolExecutor(...) as pool:` pattern; `pool.shutdown(wait=False, cancel_futures=True)` is called in `finally`
- [ ] `race_node.py` catches `TimeoutError` from `as_completed(...)` and routes timeout through existing `on_error` behavior (aligned with FR-267 Change 2)
- [ ] Existing race node unit tests pass (`tests/unit/test_race_node.py`)
- [ ] `@pytest.mark.req("REQ-YG-269")` on new condemning test; REQ-YG-269 added to `ARCHITECTURE.md` and `capabilities/CAP-91-race-node-type.yaml`
- [ ] `req_coverage.py --strict` passes

## Condemning Test

```python
@pytest.mark.req("REQ-YG-269")
def test_race_returns_on_first_success_not_after_slowest(monkeypatch):
    """Race must not block on slow losers; returns within fast_candidate_time + ε."""
    import time

    fast_llm = _make_mock_llm('{"ok": true}', delay=0.05)
    slow_llm = _make_mock_llm('{"ok": false}', delay=2.0)

    node_config = {
        "type": "race",
        "state_key": "result",
        "parse_json": True,
        "candidates": [
            {"provider": "fake-fast", "model": "x"},
            {"provider": "fake-slow", "model": "y"},
        ],
    }

    def fake_create_llm(*args, **kwargs):
        return fast_llm if kwargs.get("provider") == "fake-fast" else slow_llm

    with (
        patch("yamlgraph.node_factory.race_node.create_llm", side_effect=fake_create_llm),
        patch("yamlgraph.node_factory.race_node.prepare_messages") as mock_prepare,
    ):
        mock_prepare.return_value = ([MagicMock()], "fake-fast", "x")
        node_fn = create_race_node("test_race", node_config, {}, graph_path=None)

        t0 = time.monotonic()
        result = node_fn({"_loop_counts": {}})
        elapsed = time.monotonic() - t0

    assert elapsed < 1.0, f"race waited for slow loser: {elapsed:.1f}s"
    assert result["result"] == {"ok": True}
    assert result["_race_winner"]["provider"] == "fake-fast"
```

## Requirement

**REQ-YG-269:** Race node must not block on losing candidates after a winner is found. The
`ThreadPoolExecutor` must be shut down with `wait=False, cancel_futures=True` after returning the
winner. The node must not use the `with ThreadPoolExecutor(...) as pool:` pattern, which triggers
`shutdown(wait=True)` and blocks LangGraph state delivery until all losers complete.

**Amends REQ-YG-233 (CAP-91):** Add: "Race node pool is shut down non-blocking (`wait=False, cancel_futures=True`) after the winner is identified. Loser threads terminate naturally; their results
are discarded."

## Alternatives Considered

1. **Set a short `timeout:` to limit loser blocking time** — rejected. Workaround, not a fix. Timeout
   is a total race deadline, not a per-candidate timeout, and it doesn't prevent `shutdown(wait=True)`
   from blocking up to `timeout` seconds regardless.

2. **Use `asyncio` instead of `ThreadPoolExecutor`** — rejected. Race node deliberately chose sync
   threads to avoid event loop conflicts in LangGraph's sync-first model (diary
   `2026-04-18-reflection-fr-232-race-node-type.md`). Switching to asyncio would be a larger
   architectural change with its own failure modes.

3. **Add a `daemon=True` thread flag** — rejected. Python's `ThreadPoolExecutor` does not support
   per-future daemon configuration. `shutdown(wait=False, cancel_futures=True)` is the correct CPython
   idiom for abandoning running futures.

## Related

- **Predecessor:** #152 (silent state drop; race logs winner but LangGraph receives `None`)
- **Companion FR:** FR-267 (removes outer `_maybe_wrap_timeout` double-wrap; orthogonal bug in same code path)
- **Race node FR:** FR-232 (original race node), FR-264 (`parse_json` content normalization)
- **Key file:** `yamlgraph/node_factory/race_node.py:149`
- **Downstream:** `sheikkinen/ninchat-voice` NV-240 integration test

## Judgement

**Verdict:** APPROVE

The bug statement is code-verified: race currently uses `with ThreadPoolExecutor(...) as pool` in `yamlgraph/node_factory/race_node.py`, and that `with` exit path forces `shutdown(wait=True)` semantics that can block winner state delivery.

Two amendments were required for enforceability and are now integrated in this FR:

1. Requirement traceability tightened: REQ-YG-269 must be added to both `ARCHITECTURE.md` and `capabilities/CAP-91-race-node-type.yaml`. `scripts/req_coverage.py` loads requirement IDs from capability YAML and fails strict mode on phantom IDs.
2. Timeout behavior made explicit in acceptance criteria: this FR includes `TimeoutError` handling in race node (`as_completed` boundary) so implementation cannot drift from the proposed snippet.

Scope remains minimal and local: race node pool shutdown behavior plus race-internal timeout handling; no architectural rewrite, no asyncio migration, and no compiler-level timeout redesign in this FR.
