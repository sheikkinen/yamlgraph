"""FR-707: race sync bridge delivers the verdict at the deadline (LLM-free).

The FR-706 witness (xfail strict) is the primary RED->GREEN. These tests pin
the frozen details around it: cleanup-drain WARNING names pending candidates,
`timeout: null` races keep an unbounded bridge (no arithmetic on None), and
bridge abandonment is a RuntimeError invariant breach — never a TimeoutError
(FR-705 deleted that branch; an anonymous bridge TimeoutError would bypass
the on_error: skip contract).
"""

from __future__ import annotations

import asyncio
import logging
import time
from unittest.mock import MagicMock, patch

import pytest

from yamlgraph.node_factory import race_node as race_node_module


@pytest.fixture(autouse=True)
def _propagate_yamlgraph_logs():
    """yamlgraph logger has propagate=False; caplog needs propagation.

    Without this the drain-WARNING assertion only passed when an earlier
    test in the session happened to leave propagation enabled (test
    pollution) — it failed when run in isolation.
    """
    parent = logging.getLogger("yamlgraph")
    original = parent.propagate
    parent.propagate = True
    yield
    parent.propagate = original


def _make_cancel_ignoring_llm(hang: float):
    """The NC-361 shape: a provider call that ignores cancellation.

    A to_thread loser dies as a TASK instantly on cancel (the hung thread is
    invisible to asyncio.all_tasks), so it never reaches the drain WARNING.
    A coroutine that swallows CancelledError keeps the named race task
    pending — exactly what the drain must report.
    """
    mock = MagicMock()

    async def ainvoke(messages, config=None):
        try:
            await asyncio.sleep(hang)
        except asyncio.CancelledError:
            await asyncio.sleep(hang)  # hung TLS read: cancel changes nothing
            raise
        result = MagicMock()
        result.content = "too late"
        return result

    mock.ainvoke = ainvoke
    mock.with_structured_output = MagicMock(return_value=mock)
    return mock


class TestCleanupDrainWarning:
    """Cleanup-drain expiry logs WARNING naming pending candidates (F6)."""

    @pytest.mark.req("REQ-YG-269")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_warning_names_pending_candidates(
        self, mock_prepare, mock_create_llm, monkeypatch, caplog
    ):
        from yamlgraph.node_factory.race_node import (
            AllCandidatesFailedError,
            create_race_node,
        )

        monkeypatch.setattr(race_node_module, "CLEANUP_GRACE", 0.2)
        mock_prepare.return_value = ([MagicMock()], "anthropic", None)
        mock_create_llm.side_effect = [
            _make_cancel_ignoring_llm(2.0),
            _make_cancel_ignoring_llm(2.0),
        ]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "timeout": 0.2,
            "parse_json": True,
            "candidates": [
                {"provider": "google", "model": "gemini-2.0-flash"},
                {"provider": "azure", "model": "gpt-4o"},
            ],
        }
        node_fn = create_race_node("race_drain", node_config, {})

        with caplog.at_level(logging.WARNING):
            with pytest.raises(AllCandidatesFailedError):
                node_fn({"_loop_counts": {}, "errors": []})

            # WARNING is emitted post-verdict from the daemon bridge thread —
            # poll briefly for it.
            deadline = time.monotonic() + 3.0
            while time.monotonic() < deadline:
                text = caplog.text
                if "abandoned" in text:
                    break
                time.sleep(0.05)

        assert "abandoned" in caplog.text
        assert "google" in caplog.text and "gemini-2.0-flash" in caplog.text
        assert "azure" in caplog.text and "gpt-4o" in caplog.text


class TestTimeoutNoneUnbounded:
    """`timeout: null` → no deadline authority → unbounded bridge (F3)."""

    @pytest.mark.req("REQ-YG-269")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_none_timeout_passes_none_budget(self, mock_prepare, mock_create_llm):
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)
        fast = MagicMock()

        async def ainvoke(messages, config=None):
            result = MagicMock()
            result.content = "quick"
            return result

        fast.ainvoke = ainvoke
        fast.with_structured_output = MagicMock(return_value=fast)
        mock_create_llm.side_effect = [fast]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "timeout": None,
            "parse_json": True,
            "candidates": [{"provider": "anthropic"}],
        }
        node_fn = create_race_node("race_unbounded", node_config, {})

        captured: dict = {}
        real_bridge = race_node_module._run_coro_sync_safe

        def spy(coro, verdict_budget=None):
            captured["budget"] = verdict_budget
            return real_bridge(coro, verdict_budget=verdict_budget)

        with patch.object(race_node_module, "_run_coro_sync_safe", side_effect=spy):
            result = node_fn({"_loop_counts": {}, "errors": []})

        assert captured["budget"] is None, "timeout: null must not compute a budget"
        assert result["response"] == "quick"


class TestBridgeAbandon:
    """Bridge abandonment is an invariant breach: RuntimeError, never TimeoutError (F4)."""

    @pytest.mark.req("REQ-YG-269")
    def test_abandon_raises_runtime_error(self):
        from yamlgraph.node_factory.race_node import _run_coro_sync_safe

        async def outlives_budget():
            await asyncio.sleep(2.0)
            return "never delivered"

        start = time.monotonic()
        with pytest.raises(RuntimeError, match="abandoned"):
            _run_coro_sync_safe(outlives_budget(), verdict_budget=0.1)
        assert time.monotonic() - start < 1.0, "abandon must honor the budget"

    @pytest.mark.req("REQ-YG-269")
    def test_verdict_timeout_error_passes_through(self):
        """A TimeoutError that IS the verdict must not be relabeled as abandon."""
        from yamlgraph.node_factory.race_node import _run_coro_sync_safe

        async def verdict_is_timeout():
            raise TimeoutError("this is the coroutine's own verdict")

        with pytest.raises(TimeoutError, match="own verdict"):
            _run_coro_sync_safe(verdict_is_timeout(), verdict_budget=5.0)
