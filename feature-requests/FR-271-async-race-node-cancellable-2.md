# Feature Request: Async race node with cancellable HTTP clients

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 3–5 days
**Requested:** 2026-04-22

## Summary

Rewrite the race node to use `asyncio` with cancellable async LLM clients so losers are actually aborted on the wire when a winner emerges — not merely abandoned in a background thread. Supersedes the mitigations in FR-267 (double-wrap), FR-270 (non-blocking shutdown), and the proposed daemon-thread workaround in #169.

## Value Statement

Race nodes become truthful: total wall-clock equals the winner's latency, resources are released immediately, interpreter exit is clean, and LangSmith traces show one span per race, not `N-1` orphans. Enables race nodes for any use case where observability and resource hygiene matter (production voice, long-lived workers, evaluation suites).

## Problem

Current race node (post-FR-270) uses `ThreadPoolExecutor` with synchronous LLM clients:

- Winner is selected and returned correctly.
- Losers' HTTP calls continue running in the pool until they finish on their own — `Future.cancel()` is a no-op once running, and there is no portable way to kill a CPython thread. The only safe controls are:
  1. Wait for the call to finish (what we used to do — FR-270 root cause)
  2. Mark the thread daemon and rely on interpreter exit to reap it (#169 — cheap but only helps short-lived processes)
  3. Cancel cooperatively at an await point — requires asyncio
- Consequence: for a long-lived server (voice coordinator, FastAPI worker), loser threads pile up while the winner is already serving the next turn. Each race spawns `N-1` orphan HTTP connections that run to completion against the provider, costing tokens, quota, and LangSmith spans.

Symptom witnesses:
- NV-240 integration suite: 108 s of tests + ~60 s of post-exit pause waiting for vertex HTTP to drain (now worked around via daemon threads in #169)
- Production: every race emits a vertex inference we never read, billed anyway
- LangSmith: orphan spans with no parent correlation

## Proposed Solution

Rewrite `race_node.py` to an async-native race core with execution-mode-safe adapters:

```python
async def _invoke_candidate_async(
  candidate: dict,
  messages: list,
  output_model: type | None,
  parse_json: bool,
) -> tuple[dict, Any]:
  llm = await create_llm_async(
    provider=candidate["provider"],
    model=candidate["model"],
  )
  # Native async providers use llm.ainvoke directly.
  # Non-native providers may degrade to thread fallback (explicitly flagged).
  response = await llm.ainvoke(messages)
  content = normalize_content(response.content)
  parsed = extract_json(content) if parse_json else content
  return candidate, parsed


async def _race_async(
  candidates: list[dict],
  messages: list,
  output_model: type | None,
  parse_json: bool,
  timeout: float | None,
) -> tuple[dict, Any]:
  """Return first successful candidate result; cancel remaining tasks."""
  tasks: dict[asyncio.Task, dict] = {
    asyncio.create_task(
      _invoke_candidate_async(c, messages, output_model, parse_json),
      name=f"race-{c.get('provider', '?')}-{c.get('model', '?')}",
    ): c
    for c in candidates
  }
  errors: list[tuple[dict, Exception]] = []
  deadline = None if timeout is None else (asyncio.get_running_loop().time() + timeout)

  try:
    while tasks:
      remaining = None if deadline is None else max(0.0, deadline - asyncio.get_running_loop().time())
      done, _pending = await asyncio.wait(
        tasks.keys(),
        timeout=remaining,
        return_when=asyncio.FIRST_COMPLETED,
      )
      if not done:
        raise TimeoutError(f"race timed out after {timeout}s")

      for task in done:
        candidate = tasks.pop(task)
        try:
          winner_candidate, winner_result = task.result()
        except Exception as exc:
          errors.append((candidate, exc))
          continue

        for loser in tasks:
          loser.cancel()
        await asyncio.gather(*tasks.keys(), return_exceptions=True)
        return winner_candidate, winner_result

    raise AllCandidatesFailedError(errors)
  finally:
    # Defensive cleanup for timeout/error exits.
    for task in tasks:
      task.cancel()
    if tasks:
      await asyncio.gather(*tasks.keys(), return_exceptions=True)


def _run_coro_sync_safe(coro):
  """Run coroutine from sync node without event-loop conflicts."""
  try:
    asyncio.get_running_loop()
  except RuntimeError:
    return asyncio.run(coro)

  # Already inside an event loop (for example app.ainvoke path):
  # run coroutine in a dedicated thread with its own loop.
  with ThreadPoolExecutor(max_workers=1) as ex:
    return ex.submit(lambda: asyncio.run(coro)).result()


def node_fn(state: dict) -> dict:
  winner, result = _run_coro_sync_safe(_race_async(...))
  return {
    state_key: result,
    "_race_winner": {
      "provider": winner.get("provider"),
      "model": winner.get("model"),
    },
    ...
  }
```

Key properties:
1. **First-success correctness.** Race continues past early failures and only stops on first successful candidate.
2. **Deterministic cancellation point.** Remaining candidates are cancelled only after a winner is produced or terminal timeout/all-failed condition is reached.
3. **Execution-mode safety.** No direct `asyncio.run()` call inside node body; sync invocation uses a loop-safe bridge compatible with both `invoke` and `ainvoke` execution paths.
4. **Bounded timeout semantics.** Timeout applies to the full race window, not a single completion event.
5. **Trace hygiene.** Cancelled siblings resolve with explicit cancellation rather than abandoned background work.

### LLM factory impact

Reuse existing async utilities instead of introducing duplicate API names:

- Keep `yamlgraph.utils.llm_factory.create_llm()` unchanged for sync paths.
- Reuse `yamlgraph.utils.llm_factory_async.create_llm_async()` for async candidate creation.
- Add provider-capability signaling (native async vs degraded fallback) and one-time warning logs when a candidate cannot offer on-wire cancellation.

### Provider capability contract

- **Native async providers:** cancellation expectation is cooperative transport cancellation (`CancelledError` propagation at await points).
- **Fallback providers (`run_in_executor`):** cancellation is best-effort task cancellation only; on-wire abort is not guaranteed and is surfaced via warning/metadata.

### Migration

- Graph YAML schema unchanged (`type: race`, `candidates`, `timeout`, `parse_json`).
- Existing graphs continue to run without configuration changes.
- Non-race nodes remain sync-first and continue using existing factory/executor paths.

## Acceptance Criteria

- [ ] `ThreadPoolExecutor` removed from `race_node.py`; replaced with asyncio.
- [ ] Loser candidates' HTTP connections are closed within 500 ms of the winner's resolution (verify with `httpx` transport hook or connection-pool introspection).
- [ ] Condemning unit test: fast fake async LLM (50 ms) + slow fake async LLM (30 s sleep at an await point). Assert:
  - `node_fn` returns within 1 s with fast result
  - Slow task is cancelled (track via `CancelledError` in the fake's `finally:`)
  - Interpreter exits within 1 s after `node_fn` returns
- [ ] NV-240 integration suite in `sheikkinen/ninchat-voice`:
  - Still 6/6 green
  - Post-exit pause < 2 s (today: ~60 s without #169, ~0 s with #169 daemon workaround)
- [ ] LangSmith / OTel: no orphan spans from cancelled losers; cancelled tasks close their span with status `cancelled`.
- [ ] Backward compatibility for providers without native async: fall back to `loop.run_in_executor` with a warning logged once per provider.

## Out of Scope

- Rewriting non-race nodes to async (tracked separately in FR-XXX async pipeline).
- Async YAMLGraph CLI (`yamlgraph graph run` remains sync; it just blocks on the async race internally).
- Changing LangGraph state merge semantics.

## Superseded / Related

- **Supersedes (once shipped):**
  - #169 (daemon-thread mitigation) — becomes unnecessary
  - Parts of #161 proposed fix (the asyncio alternative section)
- **Builds on:**
  - FR-267 / #155 (timeout double-wrap removed)
  - FR-270 / #168 (non-blocking shutdown)
- **Downstream:**
  - `sheikkinen/ninchat-voice` NV-240 suite — acceptance oracle

## Risk

- Provider async surface varies. Vertex, anthropic, openai have stable `.ainvoke`. Older/legacy integrations may need the `run_in_executor` fallback, which leaks the same loser-thread hazard — but only for those specific providers, and visibly via a deprecation warning.
- LangGraph state merge timing with async nodes is well-defined; no additional risk.

## Judgement (v2 — re-judged 2026-04-22)

**Verdict: AUTHORITY GRANTED.**

Previous judgement (v1) required four amendments. On re-examination, the proposal is stronger than initially credited. Two amendments were wrong or already addressed; two are downgraded to implementation notes. The core design is sound and may be enforced.

### Design correctness

1. **First-success semantics.** `_race_async` pops completed tasks from the `tasks` dict, catches exceptions into `errors`, and continues the `while tasks:` loop past failures. Siblings are cancelled only after a successful `task.result()`. Correct.

2. **Native `ainvoke()` is already specified.** The proposed `_invoke_candidate_async` calls `await llm.ainvoke(messages)` directly — this IS the native LangChain async path, not the yamlgraph `invoke_async()` `run_in_executor` wrapper. `create_llm_async()` is used only for LLM object construction (non-blocking). V1 amendment 1 was wrong; the proposal already does the right thing. **Implementation note**: since `create_llm()` is pure object construction with no I/O, prefer calling it synchronously to avoid the executor round-trip. Replace `llm = await create_llm_async(...)` with `llm = create_llm(...)`.

3. **Sync-async bridge.** `_run_coro_sync_safe` detects an existing event loop (ainvoke path) and falls back to a dedicated-thread bridge; otherwise calls `asyncio.run()`. This is the same pattern used by the A2A client (`yamlgraph/contrib/a2a_client.py`). V1 amendment 2 proposed a dual-path factory (`create_race_node_async`), but this adds a second code path to maintain and requires changes to `node_compiler.py` / `compile_graph_async` — scope creep for zero correctness gain. The sync bridge is sufficient. **Implementation note**: if a native async compile path is later added (FR-XXX async pipeline), a `create_race_node_async` can be extracted then. Not required now.

4. **Timeout semantics.** Deadline is computed once; `asyncio.wait(timeout=remaining)` re-checks against it each iteration. If `done` is empty after wait, `TimeoutError` is raised. Correct.

5. **Cleanup.** `finally` block cancels all remaining tasks and `gather`s them with `return_exceptions=True`. No task leaks.

### Acceptance criteria amendments (non-blocking)

The following tightenings should be applied during enforcement, not as a gate:

- **"Interpreter exits within 1 s"** — replace with: "No race-owned `asyncio.Task` is pending after the race coroutine returns. Verify via `CancelledError` observation in the slow fake's `finally:` block."
- **Add**: "`on_error: skip` preserved — all candidates fail → `{state_key: None, errors: [...]}`, no raise."
- **Add**: "Timeout fires when no candidate completes within deadline — assert `AllCandidatesFailedError` or `on_error: skip` returns `None`."
- **Keep as-is**: fast fake (50 ms) + slow fake (30 s await-sleep) condemning test; NV-240 6/6 green; LangSmith trace hygiene.

### Provider contract

The "Provider capability contract" section already distinguishes native async from `run_in_executor` fallback. Sufficient. **Implementation note**: log a one-time `WARNING` per non-native provider at race creation time (not per invocation) so operators can identify candidates that won't benefit from true on-wire cancellation.

### Scope freeze

- `race_node.py` async rewrite: **in scope.**
- `llm_factory_async.py`: **out of scope** (leave unchanged for non-race consumers).
- Non-race node factories: **out of scope.**
- `node_compiler.py`: **minimal change only** — `_compile_race_node` continues to call `create_race_node()` which now returns a sync-bridged async node. No dual-path registration needed.
- CLI: **out of scope.**
- New YAML config keys: **none.**
- Deprecation of #169 daemon-thread workaround: **in scope** (remove after NV-240 confirms clean exit).

### Risk

- **Low**: LangChain `ainvoke()` is stable across anthropic, openai, vertex.
- **Low**: `_run_coro_sync_safe` bridge is proven in A2A client.
- **Medium**: Vertex `ainvoke()` cancellation at transport layer is unverified. Mitigated by condemning test with fake providers + NV-240 integration as acceptance oracle.

### Authority

**Granted.** Enforcement may begin. Commit RED (failing tests, `SKIP=pytest`) and GREEN (implementation) separately per the rite. Update this FR with implementation decisions as they arise.
