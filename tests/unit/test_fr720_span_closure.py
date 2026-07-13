"""FR-720 RED witness: close LangSmith spans on race-loser cancellation.

NC-367 census: 38/38 deployed vertex loser spans pending-forever — race
losers are cancelled at an await point and their trace runs never close.
The fix (judged, F1 re-pin): the candidate wrapper pre-generates a run_id
per ainvoke attempt, passes it as ``config={"run_id": ...}``, and on
CancelledError enqueues ``client.update_run(...)`` with a terminal error
and race_outcome metadata before re-raising.

LLM-free per Judgement F4: a recording callback handler cannot witness
this (cancellation is exactly what kills callbacks); the witness mocks
the langsmith client and asserts the update_run payload.
"""

import asyncio
import time
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from yamlgraph.node_factory import race_node
from yamlgraph.node_factory.race_node import AllCandidatesFailedError, _race_async

WINNER = {"provider": "azure", "model": "gpt-4o"}
LOSER = {"provider": "vertex", "model": "gemini-2.0-flash"}


class _Response:
    content = "winner content"


class _FastLLM:
    async def ainvoke(self, messages, config=None):
        return _Response()


class _HangingLLM:
    """Never completes — must be cancelled. Records the config it got."""

    def __init__(self, seen_configs: list):
        self._seen = seen_configs

    async def ainvoke(self, messages, config=None):
        self._seen.append(config)
        await asyncio.Event().wait()


@pytest.fixture
def ls_client(monkeypatch):
    """Tracing enabled + mocked langsmith client factory."""
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")
    client = MagicMock()
    monkeypatch.setattr(
        race_node, "_get_langsmith_client", lambda: client, raising=False
    )
    return client


def _wait_for_calls(client: MagicMock, count: int, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if client.update_run.call_count >= count:
            return
        time.sleep(0.01)


class TestSpanClosureOnLoserCancel:
    """AC-01/AC-02: winner-found cancel site closes the loser's span."""

    @pytest.mark.req("REQ-YG-547")
    def test_winner_path_closes_loser_span(self, ls_client):
        seen: list = []
        armed = [(WINNER, _FastLLM()), (LOSER, _HangingLLM(seen))]

        winner, result = asyncio.run(
            _race_async(armed, ["msg"], None, False, timeout=10)
        )

        assert winner == WINNER
        _wait_for_calls(ls_client, 1)
        assert ls_client.update_run.call_count == 1
        kwargs = ls_client.update_run.call_args.kwargs
        assert isinstance(kwargs["run_id"], UUID)
        assert kwargs["end_time"] is not None
        assert kwargs["error"] == "cancelled: lost race to azure/gpt-4o"
        meta = kwargs["extra"]["metadata"]
        assert meta["race_outcome"] == "lost"
        assert meta["race_winner"] == "azure/gpt-4o"

    @pytest.mark.req("REQ-YG-547")
    def test_run_id_is_the_handle(self, ls_client):
        """F1: the run_id passed to ainvoke config IS the id closed."""
        seen: list = []
        armed = [(WINNER, _FastLLM()), (LOSER, _HangingLLM(seen))]

        asyncio.run(_race_async(armed, ["msg"], None, False, timeout=10))

        _wait_for_calls(ls_client, 1)
        assert len(seen) == 1
        assert seen[0] is not None, "ainvoke received no config — no handle"
        invoked_id = seen[0]["run_id"]
        closed_id = ls_client.update_run.call_args.kwargs["run_id"]
        assert invoked_id == closed_id

    @pytest.mark.req("REQ-YG-547")
    def test_drain_path_marks_timeout(self, ls_client):
        """F7: timeout losers (FR-707 cancel-only drain) close too."""
        armed = [(WINNER, _HangingLLM([])), (LOSER, _HangingLLM([]))]

        with pytest.raises(AllCandidatesFailedError):
            asyncio.run(_race_async(armed, ["msg"], None, False, timeout=0.2))

        _wait_for_calls(ls_client, 2)
        assert ls_client.update_run.call_count == 2
        for call in ls_client.update_run.call_args_list:
            assert call.kwargs["error"] == "cancelled: race timed out"
            assert call.kwargs["end_time"] is not None
            assert call.kwargs["extra"]["metadata"]["race_outcome"] == "lost"

    @pytest.mark.req("REQ-YG-547")
    def test_verdict_not_delayed(self, ls_client):
        """AC-03/AC-04: closure is enqueue-only; the verdict path never
        waits for losers (FR-707 discipline unchanged)."""
        armed = [(WINNER, _FastLLM()), (LOSER, _HangingLLM([]))]

        start = time.monotonic()
        winner, _ = asyncio.run(_race_async(armed, ["msg"], None, False, timeout=30))
        elapsed = time.monotonic() - start

        assert winner == WINNER
        assert elapsed < 2.0, f"verdict delayed {elapsed:.2f}s by span closure"

    @pytest.mark.req("REQ-YG-547")
    def test_tracing_disabled_skips_cleanly(self, monkeypatch):
        """AC-05: no LangSmith env — closure skipped, no client touched."""
        monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)
        monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
        factory = MagicMock()
        monkeypatch.setattr(race_node, "_get_langsmith_client", factory, raising=False)
        armed = [(WINNER, _FastLLM()), (LOSER, _HangingLLM([]))]

        winner, _ = asyncio.run(_race_async(armed, ["msg"], None, False, timeout=10))

        assert winner == WINNER
        factory.assert_not_called()
