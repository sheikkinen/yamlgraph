"""FR-706 witness: race timeout must not block the host event loop.

Seam (F1): sync-bridge-called-on-loop-thread — node_fn(state) invoked
directly inside a coroutine on the host loop, the branch the NC-361
production traceback proves was taken (_run_coro_sync_safe running-loop
path).

Fixture (F2): candidates hang via await asyncio.to_thread(time.sleep, HANG)
— uncancellable (task cancellation cannot stop the thread; mirrors provider
HTTP threads pending at the deadline) but bounded (HANG=5s) so the test
terminates in both verdicts. NOT threading.Event().wait() inside ainvoke:
that would block the background loop before its own timeout fires and hang
the test instead of failing it.

Thresholds (F3): race timeout 0.5s / hang 5s / return < 2.5s / max heartbeat
gap < 2s — order-of-magnitude separation against CI jitter. Blocked behavior
produces ~5s on both axes.
"""

from __future__ import annotations

import asyncio
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

RACE_TIMEOUT = 0.5
HANG = 5.0
RETURN_THRESHOLD = 2.5
GAP_THRESHOLD = 2.0
HEARTBEAT_INTERVAL = 0.1


def _make_hanging_llm():
    """Candidate whose work is uncancellable-but-bounded (F2)."""
    mock = MagicMock()

    async def ainvoke(messages, config=None):
        await asyncio.to_thread(time.sleep, HANG)
        result = MagicMock()
        result.content = "too late"
        return result

    mock.ainvoke = ainvoke
    mock.with_structured_output = MagicMock(return_value=mock)
    return mock


@pytest.mark.req("REQ-YG-269")
@patch("yamlgraph.node_factory.race_node.create_llm")
@patch("yamlgraph.node_factory.race_node.prepare_messages")
def test_race_timeout_does_not_block_host_loop(mock_prepare, mock_create_llm):
    """NC-361 witness: heartbeats must keep ticking through a race timeout."""
    from yamlgraph.node_factory.race_node import (
        AllCandidatesFailedError,
        create_race_node,
    )

    mock_prepare.return_value = ([MagicMock()], "anthropic", None)
    mock_create_llm.side_effect = [
        _make_hanging_llm(),
        _make_hanging_llm(),
        _make_hanging_llm(),
        _make_hanging_llm(),
    ]

    node_config = {
        "type": "race",
        "prompt": "test_prompt",
        "state_key": "response",
        "timeout": RACE_TIMEOUT,
        "parse_json": True,
        "candidates": [
            {"provider": "google", "model": "gemini-2.0-flash"},
            {"provider": "azure", "model": "gpt-4o"},
        ],
    }
    node_fn = create_race_node("race_liveness", node_config, {})
    state = {"_loop_counts": {}, "errors": []}

    # FR-713 re-derivation (FR-709 F1 pattern): the persistent bridge loop
    # and its executor pool are ARCHITECTURE, not leakage — warm them up
    # with one full race, then let the hung executor workers finish their
    # bounded sleep and go idle, so the baseline includes the pool and the
    # measured race reuses (not grows) it.
    with pytest.raises(AllCandidatesFailedError):
        node_fn(dict(state))
    time.sleep(HANG + 1.0)  # workers exit their sleep and return to the pool
    baseline_threads = set(threading.enumerate())
    heartbeats: list[float] = []
    result: dict = {}

    async def heartbeat() -> None:
        while not result.get("done"):
            heartbeats.append(time.monotonic())
            await asyncio.sleep(HEARTBEAT_INTERVAL)

    async def scenario() -> None:
        hb = asyncio.create_task(heartbeat())
        await asyncio.sleep(HEARTBEAT_INTERVAL * 3)  # heartbeat warm-up

        start = time.monotonic()
        # F1: the production seam — sync node_fn called ON the loop thread.
        with pytest.raises(AllCandidatesFailedError):
            node_fn(state)
        result["duration"] = time.monotonic() - start
        result["done"] = True

        await asyncio.sleep(HEARTBEAT_INTERVAL * 3)  # post-timeout ticks
        hb.cancel()
        await asyncio.gather(hb, return_exceptions=True)

    asyncio.run(scenario())

    # Liveness assertions (F3) — gathered so the failure reports BOTH axes.
    gaps = [b - a for a, b in zip(heartbeats, heartbeats[1:], strict=False)]
    max_gap = max(gaps) if gaps else float("inf")
    violations = []
    if result["duration"] >= RETURN_THRESHOLD:
        violations.append(
            f"race node blocked its caller for {result['duration']:.2f}s "
            f"(timeout was {RACE_TIMEOUT}s) — losers awaited synchronously"
        )
    if max_gap >= GAP_THRESHOLD:
        violations.append(
            f"host event loop stalled: max heartbeat gap {max_gap:.2f}s "
            f"(threshold {GAP_THRESHOLD}s) — the NC-361 silent-stall signature"
        )
    assert not violations, "; ".join(violations)

    # F4 (re-derived for FR-713): steady-state reuse — a race on the warm
    # persistent loop must add ZERO threads beyond the pooled baseline
    # (the old "return to baseline" phrasing encoded the fresh-loop
    # teardown; pooled executor workers idle by design and are reused).
    deadline = time.monotonic() + HANG + 2.0
    while time.monotonic() < deadline:
        leaked = set(threading.enumerate()) - baseline_threads
        if not leaked:
            break
        time.sleep(0.1)
    leaked = set(threading.enumerate()) - baseline_threads
    assert not leaked, f"threads grew beyond the warm pool baseline: {leaked}"
