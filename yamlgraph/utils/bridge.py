"""Persistent bridge event loop — FR-713 Part A.

ONE long-lived daemon thread runs a single asyncio event loop for all
sync→async bridging (race, router-race, future async node paths). This
replaces the per-invocation daemon-thread + asyncio.run() topology, which
paid thread churn and fresh-loop SDK reconnects per call (FR-711: azure
Δp50 +0.628 s) and made loop-affinity defects reachable (FR-712).

Contract (frozen by FR-713 Judgement):
- The caller waits for the VERDICT, never for cleanup (FR-707). The
  verdict is handed over the moment the coroutine finishes; the bounded
  post-verdict drain runs on the loop, invisible to the caller.
- Budget breach raises RuntimeError — deliberately NOT TimeoutError
  (FR-705: an anonymous bridge TimeoutError would bypass on_error: skip).
- The drain is scoped to the invocation's OWN tasks (F1): concurrent
  invocations share the loop but never each other's drains or WARNINGs.
- Abandonment cancels the submitted work (F2): the FR-708 leak-lifetime
  bound survives the shared loop.
- The loop starts lazily on first use, never at import (AC-06); a fork
  resets the handle so the child gets a fresh lazy loop (F3); a dead loop
  thread is restarted lazily with a WARNING (F8).
- No atexit drain (F7): the thread is a daemon; a hung task can never
  block interpreter exit.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import contextvars
import logging
import os
import threading
from typing import Any

logger = logging.getLogger(__name__)

BRIDGE_THREAD_NAME = "yamlgraph-bridge-loop"
DEFAULT_CLEANUP_GRACE = 5.0

_state_lock = threading.Lock()
_loop: asyncio.AbstractEventLoop | None = None
_thread: threading.Thread | None = None

# F1: tasks created during one bridge invocation are recorded in a
# per-invocation bucket. asyncio.create_task copies the creating task's
# context, so every task spawned inside the invocation's coroutine sees
# the same bucket via this ContextVar — and no other invocation's.
_invocation_tasks: contextvars.ContextVar[set[asyncio.Task] | None] = (
    contextvars.ContextVar("yamlgraph_bridge_invocation_tasks", default=None)
)


def _task_factory(
    loop: asyncio.AbstractEventLoop, coro: Any, **kwargs: Any
) -> asyncio.Task:
    """Record spawned tasks into the current invocation's bucket (F1)."""
    task = asyncio.Task(coro, loop=loop, **kwargs)
    bucket = _invocation_tasks.get()
    if bucket is not None:
        bucket.add(task)
        task.add_done_callback(bucket.discard)
    return task


def _reset_after_fork() -> None:
    """F3: the loop thread does not survive fork — drop the dead handle so
    the child lazily starts a fresh loop. Locks are re-created because a
    forked lock may be held by a thread that no longer exists; cached LLM
    clients are dropped for the same reason (their sessions bind to the
    parent's loop)."""
    global _state_lock, _loop, _thread
    _state_lock = threading.Lock()
    _loop = None
    _thread = None

    from yamlgraph.utils import llm_factory

    llm_factory._cache_lock = threading.Lock()  # noqa: SLF001 — fork hygiene
    llm_factory._llm_cache = {}  # noqa: SLF001 — fork hygiene


# FR-950: fork registration is an optional OS capability — absent on Windows.
_register_at_fork = getattr(os, "register_at_fork", None)
if _register_at_fork is not None:
    _register_at_fork(after_in_child=_reset_after_fork)


def _ensure_loop() -> asyncio.AbstractEventLoop:
    """Return the persistent loop, starting (or restarting, F8) it lazily."""
    global _loop, _thread
    with _state_lock:
        if (
            _loop is not None
            and _thread is not None
            and _thread.is_alive()
            and not _loop.is_closed()
        ):
            return _loop
        if _thread is not None:
            logger.warning("bridge loop thread dead — restarting lazily (FR-713 F8)")
        loop = asyncio.new_event_loop()
        loop.set_task_factory(_task_factory)
        thread = threading.Thread(
            target=loop.run_forever, daemon=True, name=BRIDGE_THREAD_NAME
        )
        thread.start()
        _loop = loop
        _thread = thread
        return loop


def run_coro_sync_safe(
    coro: Any,
    verdict_budget: float | None = None,
    cleanup_grace: float = DEFAULT_CLEANUP_GRACE,
) -> Any:
    """Run a coroutine on the persistent bridge loop from a sync caller.

    The caller waits for the VERDICT, never for cleanup (FR-707): the
    result or exception is delivered through a Future the moment the
    coroutine finishes; the post-verdict drain (bounded by cleanup_grace,
    WARNING names what it abandons) runs on the loop, scoped to this
    invocation's tasks only, invisible to the caller.

    verdict_budget: None → wait indefinitely (a race with `timeout: null`
    has no deadline authority). On budget expiry the submitted work is
    cancelled (F2) and RuntimeError is raised — an invariant breach,
    deliberately NOT TimeoutError (FR-705 removed that handling; an
    anonymous bridge TimeoutError would bypass the on_error: skip
    contract).
    """
    loop = _ensure_loop()
    verdict: concurrent.futures.Future[Any] = concurrent.futures.Future()

    async def _deliver() -> None:
        bucket: set[asyncio.Task] = set()
        _invocation_tasks.set(bucket)
        try:
            verdict.set_result(await coro)
        except BaseException as exc:  # noqa: BLE001 — verdict transport
            if not verdict.done():
                verdict.set_exception(exc)
        # Post-verdict drain: bounded, scoped to THIS invocation (F1),
        # invisible to the caller.
        pending = [t for t in list(bucket) if not t.done()]
        if pending:
            _done, still = await asyncio.wait(pending, timeout=cleanup_grace)
            if still:
                logger.warning(
                    "race cleanup abandoned %d task(s) still pending "
                    "after %.1fs: %s",
                    len(still),
                    cleanup_grace,
                    ", ".join(t.get_name() for t in still),
                )

    delivery = asyncio.run_coroutine_threadsafe(_deliver(), loop)
    try:
        return verdict.result(timeout=verdict_budget)
    except TimeoutError:
        if verdict.done():
            raise  # the TimeoutError IS the verdict — deliver it unrelabeled
        delivery.cancel()  # F2: abandoned work must not outlive the budget
        raise RuntimeError(
            f"race sync bridge abandoned after {verdict_budget:.1f}s — "
            "background loop failed to deliver a verdict within its "
            "guaranteed budget"
        ) from None
