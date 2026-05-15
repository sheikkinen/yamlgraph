"""Acceptance tests for FR-392 race winner payload sanitization."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from yamlgraph.utils.fsm import graph_runner
from yamlgraph.utils.fsm.graph_runner import run_and_dispatch


@pytest.mark.req("REQ-YG-319")
class TestFR392RaceWinnerPayloadSanitization:
    """Shared FSM runner strips race metadata before dispatch payload assembly."""

    @pytest.mark.asyncio
    async def test_ac01_run_and_dispatch_strips_race_winner_before_payload_build(
        self,
    ) -> None:
        load_fn = AsyncMock(return_value=MagicMock())
        run_fn = AsyncMock(return_value={"_race_winner": "node_a"})
        sent: list[tuple[str, str, dict | None]] = []

        await run_and_dispatch(
            graph_path="/tmp/test.yaml",
            initial_state={"query": "hi"},
            input_key="query",
            output_key="_race_winner",
            event_key="intent",
            event_map={},
            success_event="completed",
            failure_event="failed",
            machine_name="router",
            load_fn=load_fn,
            run_fn=run_fn,
            send_fn=lambda machine, event, payload: sent.append(
                (machine, event, payload)
            ),
        )

        assert sent == [("router", "completed", None)]

    @pytest.mark.asyncio
    async def test_ac02_stripped_race_winner_is_logged_at_info(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        load_fn = AsyncMock(return_value=MagicMock())
        run_fn = AsyncMock(return_value={"_race_winner": "node_a", "result": "ok"})
        sent: list[tuple[str, str, dict | None]] = []
        info_spy = MagicMock(wraps=graph_runner.logger.info)
        monkeypatch.setattr(graph_runner.logger, "info", info_spy)

        await run_and_dispatch(
            graph_path="/tmp/test.yaml",
            initial_state={"query": "hi"},
            input_key="query",
            output_key="result",
            event_key="intent",
            event_map={},
            success_event="completed",
            failure_event="failed",
            machine_name="router",
            load_fn=load_fn,
            run_fn=run_fn,
            send_fn=lambda machine, event, payload: sent.append(
                (machine, event, payload)
            ),
        )

        assert sent == [("router", "completed", {"result": "ok"})]
        assert any(
            call.args == ("race.winner: %s", "node_a")
            for call in info_spy.call_args_list
        )

    @pytest.mark.asyncio
    async def test_ac03_dispatched_payload_excludes_race_winner_metadata(self) -> None:
        load_fn = AsyncMock(return_value=MagicMock())
        run_fn = AsyncMock(
            return_value={
                "result": {"answer": "ok"},
                "_race_winner": "node_b",
                "other": "value",
            }
        )
        sent: list[tuple[str, str, dict | None]] = []

        await run_and_dispatch(
            graph_path="/tmp/test.yaml",
            initial_state={"query": "hi"},
            input_key="query",
            output_key="result",
            event_key="intent",
            event_map={},
            success_event="completed",
            failure_event="failed",
            machine_name="router",
            load_fn=load_fn,
            run_fn=run_fn,
            send_fn=lambda machine, event, payload: sent.append(
                (machine, event, payload)
            ),
        )

        assert sent == [("router", "completed", {"result": {"answer": "ok"}})]

    @pytest.mark.asyncio
    async def test_ac04_existing_event_cascade_behavior_is_unchanged(self) -> None:
        app = MagicMock()
        app.aget_state = AsyncMock(
            side_effect=[SimpleNamespace(next=()), SimpleNamespace(next=())]
        )
        load_fn = AsyncMock(return_value=app)
        run_fn = AsyncMock(return_value={"intent": "goodbye", "_race_winner": "node_b"})
        sent: list[tuple[str, str, dict | None]] = []

        await run_and_dispatch(
            graph_path="/tmp/test.yaml",
            initial_state={"user_input": "done"},
            input_key="user_input",
            output_key="result",
            event_key="intent",
            event_map={"done": "on_done", "goodbye": "on_goodbye"},
            success_event="completed",
            failure_event="failed",
            machine_name="router",
            thread_id="thread-1",
            load_fn=load_fn,
            run_fn=run_fn,
            send_fn=lambda machine, event, payload: sent.append(
                (machine, event, payload)
            ),
        )

        assert sent == [("router", "on_done", None)]
