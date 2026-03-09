# Feature Request: Async Integration Pattern Documentation

**Priority:** LOW
**Type:** Documentation
**Status:** Enforced ✅
**Effort:** 0.5 days
**Requested:** 2026-03-09

## Summary

Add a section to `reference/async-usage.md` documenting the fire-and-forget
integration pattern for event-driven orchestrators (FSMs, actor systems, message
queues). This covers how to use `run_graph_async()` as a background task that
dispatches results via external event channels.

## Value Statement

Developers integrating YAMLGraph into event-driven systems get a canonical
pattern for non-blocking graph execution, reducing the chance of re-inventing
the wheel or blocking event loops.

## Problem

`reference/async-usage.md` documents `await`-style usage (FastAPI, concurrent
prompts) but not the fire-and-forget pattern where:
1. The caller launches a graph as a background task
2. The caller returns immediately (keeping its event loop responsive)
3. The graph dispatches results via an external channel (socket, queue, callback)

This pattern is proven in `projects/ninchat_voice` (voice_speak_action,
voice_listen_action) and needed by any event-driven system where blocking for
2–30s LLM calls kills responsiveness.

## Proposed Solution

Add a "Fire-and-Forget Integration" section to `reference/async-usage.md` with:

### Content outline

1. **When to use** — event-driven orchestrators where `await` blocks the main loop
2. **Pattern** — `asyncio.create_task(run_graph_async(...))` with result callback
3. **Guard keys** — prevent duplicate launches on re-entry/polling
4. **Result dispatch** — examples for socket, queue, and callback channels
5. **Error handling** — exception → failure event dispatch
6. **Event resolution** — mapping graph output to orchestrator events

### Code example (generic, framework-agnostic)

```python
import asyncio
from yamlgraph.executor_async import load_and_compile_async, run_graph_async

async def launch_graph_background(
    graph_path: str,
    initial_state: dict,
    on_success,   # callback(result: dict)
    on_failure,   # callback(error: Exception)
):
    """Fire-and-forget graph execution with result callback."""
    app = await load_and_compile_async(graph_path)

    async def _run():
        try:
            result = await run_graph_async(app, initial_state)
            await on_success(result)
        except Exception as e:
            await on_failure(e)

    asyncio.create_task(_run())
```

### Files changed

| Path | Action |
|------|--------|
| `reference/async-usage.md` | Add fire-and-forget section |

## Acceptance Criteria

- [ ] `reference/async-usage.md` has a "Fire-and-Forget Integration" section
- [ ] Pattern uses only public YAMLGraph API (`load_and_compile_async`,
      `run_graph_async`)
- [ ] Example is framework-agnostic (no FSM/statemachine_engine imports)
- [ ] Guard key pattern is documented generically
- [ ] Error handling pattern included

## Judgment

**Status: APPROVED WITH REVISION**
**Verdict date:** 2026-03-09

Core direction is correct. Three defects found; none critical. Narrow two
items from scope and clarify caller context before implementation.

---

### J-1 — MEDIUM: Caller-context assumption not stated; sync-thread variant absent

**Filed against:** §Code example, AC-2

`asyncio.create_task()` requires the caller to be inside a running asyncio
event loop (FastAPI endpoint, `asyncio.run()`, etc.). The proven
ninchat_voice pattern for sync-thread callers (bridge handlers) is
`asyncio.run_coroutine_threadsafe(coro, loop)` — an entirely different API.

The FR says "framework-agnostic" but the example only covers async-context
callers. A sync-thread reader (e.g. anyone integrating with
`statemachine_engine`, Celery, or a ThreadPoolExecutor) cannot use the
example as written.

**Resolution:** Add a one-sentence scope statement: *"This pattern applies
when the caller is inside an asyncio event loop. For sync-thread callers
(e.g. ThreadPoolExecutor, event-driven engines), use
`asyncio.run_coroutine_threadsafe(coro, loop).result()` — see NC-138 for
concrete usage."* Do not add a full sync-thread example to FR-170; keep it
YAMLGraph-scoped.

---

### J-2 — LOW: Guard key in AC-4 contradicts AC-3 and is out of scope

**Filed against:** AC-4 ("Guard key pattern is documented generically")

Guard keys are a `statemachine_engine` re-dispatch artifact (engine
re-calls `execute()` every 50ms while it returns `None`). They have no
meaning when `asyncio.create_task` is used from an async context — a task
is created exactly once per `await`-ed call. Including them in
`reference/async-usage.md` introduces FSM concepts into YAMLGraph docs.
AC-3 ("framework-agnostic") already excludes them.

**Resolution:** Delete AC-4. Guard key documentation is owned by NC-138.
Reference NC-138 from a brief note: *"This section does not cover re-dispatch
prevention for polling engines — see NC-138."*

---

### J-3 — LOW: Socket dispatch examples are platform-specific

**Filed against:** §Content outline point 4 ("Result dispatch — examples for
socket, queue, and callback channels")

Unix DGRAM socket dispatch is platform-specific (`AF_UNIX`, macOS/Linux
only) and statemachine_engine-specific. It does not belong in YAMLGraph
reference docs.

**Resolution:** Drop socket from the outline. Keep only asyncio.Queue and
callback examples — both are stdlib, portable, and illustrate the concept
without platform coupling.

---

### Revised AC

- [ ] `reference/async-usage.md` has a "Fire-and-Forget Integration" section
- [ ] Scope statement: async-context callers; pointer to NC-138 for sync-thread variant
- [ ] Pattern uses only public YAMLGraph API (`load_and_compile_async`, `run_graph_async`)
- [ ] Example is framework-agnostic (no FSM/socket imports)
- [ ] Result dispatch examples: asyncio.Queue and callback only (no socket)
- [ ] Error handling pattern included

### Authority

Granted after J-1 scope note and J-2/J-3 scope removals are applied.

---

## Judgement Notes (2026-03-09)

**Original FR-170** proposed a `yamlgraph_async` action type as a new file in
`examples/fsm-router/actions/`. On rejudgement, the FR was found to conflate
three concerns:

1. **YAMLGraph API** — no change needed; `run_graph_async` is already a coroutine
2. **FSM action implementation** — guard keys, socket dispatch, event mapping →
   moved to NC-138 under `projects/ninchat_voice/feature-requests/`
3. **Integration documentation** — this FR (narrowed to docs-only)

The concrete implementation (J-1a guards, Unix DGRAM dispatch, `event_map`)
is tracked in NC-138, which references NC-137 (original incident).

## Related

- NC-137 — Fire-and-forget LLM bridge (incident report)
- NC-138 — `yamlgraph_async` FSM action implementation (split from this FR)
- `reference/async-usage.md` — existing async documentation
- `projects/ninchat_voice/actions/real/voice_speak_action.py` — J-1a guard
  pattern reference
