"""FR-713 Part A witnesses: persistent bridge loop (LLM-free).

The bridge substrate is promoted from per-invocation daemon-thread +
asyncio.run() to ONE long-lived event loop thread (yamlgraph-bridge-loop)
owned by the graph runtime. These witnesses pin the judged contract:

- AC-01: exactly one bridge loop thread across N sequential invocations
- AC-06: importing yamlgraph does not start the loop; fork resets it
- AC-08: post-verdict drain is scoped to the invocation's own tasks (F1)
- AC-09: budget-breach abandonment cancels the coroutine — the FR-708
  leak-lifetime bound survives the shared loop (F2)
- AC-10: client construction happens off-loop, on the caller thread (F6)
- AC-11: a dead loop thread is restarted lazily with a WARNING (F8)
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
import sys
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from yamlgraph.utils import bridge


@pytest.fixture(autouse=True)
def _propagate_yamlgraph_logs():
    """yamlgraph logger has propagate=False; caplog needs propagation."""
    parent = logging.getLogger("yamlgraph")
    original = parent.propagate
    parent.propagate = True
    yield
    parent.propagate = original


def BRIDGE_THREADS() -> list[threading.Thread]:
    return [t for t in threading.enumerate() if t.name == bridge.BRIDGE_THREAD_NAME]


def _fast_llm(content: str = "ok"):
    mock = MagicMock()

    async def ainvoke(messages, config=None):
        result = MagicMock()
        result.content = content
        return result

    mock.ainvoke = ainvoke
    mock.with_structured_output = MagicMock(return_value=mock)
    return mock


class TestSinglePersistentLoop:
    """AC-01: one loop thread, not one per invocation."""

    @pytest.mark.req("REQ-YG-541")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_one_loop_thread_across_sequential_races(
        self, mock_prepare, mock_create_llm
    ):
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)
        mock_create_llm.side_effect = [_fast_llm(f"r{i}") for i in range(3)]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "timeout": 5,
            "parse_json": True,
            "candidates": [{"provider": "anthropic"}],
        }
        node_fn = create_race_node("race_ac01", node_config, {})

        loops_seen: set[int] = set()
        for i in range(3):
            result = node_fn({"_loop_counts": {}, "errors": []})
            assert result["response"] == f"r{i}"
            threads = BRIDGE_THREADS()
            assert len(threads) == 1, (
                f"invocation {i + 1}: expected exactly one "
                f"{bridge.BRIDGE_THREAD_NAME} thread, got "
                f"{[t.name for t in threading.enumerate()]}"
            )
            loops_seen.add(id(threads[0]))

        assert len(loops_seen) == 1, "loop thread must be reused, not respawned"
        assert not any(
            t.name == "race-bridge" for t in threading.enumerate()
        ), "per-invocation race-bridge threads must no longer exist"


class TestImportAndForkSafety:
    """AC-06: lazy start; fork resets the loop handle (F3)."""

    @pytest.mark.req("REQ-YG-541")
    def test_import_does_not_start_loop(self):
        code = (
            "import yamlgraph, yamlgraph.utils.bridge, threading; "
            "names = [t.name for t in threading.enumerate()]; "
            "assert 'yamlgraph-bridge-loop' not in names, names"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True
        )
        assert proc.returncode == 0, proc.stderr

    @pytest.mark.req("REQ-YG-541")
    def test_import_without_register_at_fork_capability(self):
        """FR-950 AC-01/AC-02: runtimes lacking os.register_at_fork (Windows)
        must still import, and must still not start the loop thread. The
        deletion is subprocess-local setup — it installs no fake API and
        cannot reach the parent process."""
        code = (
            "import os, threading\n"
            "if hasattr(os, 'register_at_fork'):\n"
            "    del os.register_at_fork\n"
            "import yamlgraph, yamlgraph.utils.bridge\n"
            "names = [t.name for t in threading.enumerate()]\n"
            "assert 'yamlgraph-bridge-loop' not in names, names\n"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True
        )
        assert proc.returncode == 0, proc.stderr

    @pytest.mark.req("REQ-YG-541")
    @pytest.mark.skipif(sys.platform == "win32", reason="fork is POSIX-only")
    def test_fork_after_warmup_gets_fresh_lazy_loop(self):
        code = """
import asyncio, os, sys
from yamlgraph.utils import bridge

async def probe():
    return "alive"

assert bridge.run_coro_sync_safe(probe(), verdict_budget=5.0) == "alive"
pid = os.fork()
if pid == 0:  # child: loop thread did not survive fork — must lazily restart
    ok = bridge.run_coro_sync_safe(probe(), verdict_budget=5.0) == "alive"
    os._exit(0 if ok else 1)
_, status = os.waitpid(pid, 0)
sys.exit(os.waitstatus_to_exitcode(status))
"""
        proc = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True
        )
        assert proc.returncode == 0, proc.stderr


class TestScopedDrain:
    """AC-08 (F1): drain waits on and WARNs about ONLY its own tasks."""

    @pytest.mark.req("REQ-YG-541")
    def test_drain_ignores_concurrent_invocation_tasks(self, caplog):
        async def straggler_race():
            async def straggler():
                try:
                    await asyncio.sleep(30.0)
                except asyncio.CancelledError:
                    # cancellation-ignoring, but bounded: outlives the 0.5s
                    # drain grace (gets abandoned + WARNed), then finishes so
                    # it cannot pollute later tests at interpreter exit.
                    await asyncio.sleep(2.0)
                    raise

            task = asyncio.get_running_loop().create_task(
                straggler(), name="inv1-straggler"
            )
            await asyncio.sleep(0)  # let the straggler enter its try block
            task.cancel()
            return "inv1-verdict"

        async def clean_race():
            task = asyncio.get_running_loop().create_task(
                asyncio.sleep(0.01), name="inv2-clean"
            )
            await task
            return "inv2-verdict"

        results: dict = {}

        def run_inv1():
            results["inv1"] = bridge.run_coro_sync_safe(
                straggler_race(), verdict_budget=5.0, cleanup_grace=0.5
            )

        with caplog.at_level(logging.WARNING):
            t1 = threading.Thread(target=run_inv1)
            t1.start()
            time.sleep(0.1)  # inv1 verdict delivered; its drain in progress
            start = time.monotonic()
            results["inv2"] = bridge.run_coro_sync_safe(
                clean_race(), verdict_budget=5.0, cleanup_grace=0.5
            )
            inv2_duration = time.monotonic() - start
            t1.join(timeout=5.0)

            deadline = time.monotonic() + 3.0
            while time.monotonic() < deadline and "inv1-straggler" not in caplog.text:
                time.sleep(0.05)

        assert results["inv1"] == "inv1-verdict"
        assert results["inv2"] == "inv2-verdict"
        # inv2 must not be held hostage by inv1's drain
        assert inv2_duration < 1.0, f"clean race delayed {inv2_duration:.2f}s"
        assert "inv1-straggler" in caplog.text, "drain WARNING must name its own task"
        warnings = [
            r.getMessage() for r in caplog.records if "abandoned" in r.getMessage()
        ]
        assert warnings, "expected an abandonment WARNING from inv1's drain"
        assert not any(
            "inv2-clean" in w for w in warnings
        ), f"drain must not report another invocation's tasks: {warnings}"


class TestAbandonmentCancels:
    """AC-09 (F2): budget breach cancels the coroutine on the shared loop."""

    @pytest.mark.req("REQ-YG-541")
    def test_abandoned_coroutine_is_cancelled(self):
        fate: dict = {}

        async def outlives_budget():
            try:
                await asyncio.sleep(0.6)
                fate["survived"] = True
                return "never delivered"
            except asyncio.CancelledError:
                fate["cancelled"] = True
                raise

        with pytest.raises(RuntimeError, match="abandoned"):
            bridge.run_coro_sync_safe(outlives_budget(), verdict_budget=0.1)

        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline and not fate:
            time.sleep(0.05)

        assert fate.get(
            "cancelled"
        ), f"abandoned coroutine must be cancelled, not left running: {fate}"
        assert not fate.get("survived"), (
            "abandoned coroutine outlived its budget on the shared loop — "
            "FR-708 leak-lifetime bound regressed"
        )


class TestOffLoopConstruction:
    """AC-10 (F6): create_llm never runs on the bridge loop thread."""

    @pytest.mark.req("REQ-YG-541")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_construction_happens_on_caller_thread(self, mock_prepare, mock_create_llm):
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)
        construction_threads: list[str] = []

        def recording_create_llm(**kwargs):
            construction_threads.append(threading.current_thread().name)
            return _fast_llm()

        mock_create_llm.side_effect = recording_create_llm

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "timeout": 5,
            "parse_json": True,
            "candidates": [{"provider": "anthropic"}, {"provider": "azure"}],
        }
        node_fn = create_race_node("race_ac10", node_config, {})
        result = node_fn({"_loop_counts": {}, "errors": []})

        assert result["response"] == "ok"
        assert len(construction_threads) == 2
        assert all(
            name != bridge.BRIDGE_THREAD_NAME for name in construction_threads
        ), (
            f"client construction ran on the shared bridge loop — "
            f"head-of-line blocking hazard (F6): {construction_threads}"
        )


class TestLoopDeathRecovery:
    """AC-11 (F8): a dead loop thread is restarted lazily with a WARNING."""

    @pytest.mark.req("REQ-YG-541")
    def test_dead_loop_restarts_lazily(self, caplog):
        async def probe():
            return "alive"

        assert bridge.run_coro_sync_safe(probe(), verdict_budget=5.0) == "alive"
        (thread_before,) = BRIDGE_THREADS()

        # Kill the loop the way an unhandled internal fatality would.
        bridge._loop.call_soon_threadsafe(bridge._loop.stop)  # noqa: SLF001
        thread_before.join(timeout=5.0)
        assert not thread_before.is_alive(), "loop thread should have exited"

        with caplog.at_level(logging.WARNING):
            assert bridge.run_coro_sync_safe(probe(), verdict_budget=5.0) == "alive"

        (thread_after,) = BRIDGE_THREADS()
        assert thread_after is not thread_before
        assert (
            "restart" in caplog.text.lower()
        ), "loop restart must be witnessed by a WARNING"
