"""Acceptance tests for FR-392 race winner metadata stripping at FSM boundary."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from yamlgraph.utils.fsm.graph_runner import run_and_dispatch


@pytest.mark.req("REQ-YG-319")
class TestFR392StripRaceWinnerMetadata:
    """Shared FSM runner strips race metadata before dispatch payload assembly."""

    @pytest.mark.asyncio
    async def test_ac01_strips_race_winner_before_payload_build(self) -> None:
        load_fn = AsyncMock(return_value=MagicMock())
        result = {"result": "ok", "_race_winner": {"provider": "openai"}}
        run_fn = AsyncMock(return_value=result)
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

        assert sent == [("router", "completed", {"result": "ok"})]
        assert "_race_winner" not in result

    @pytest.mark.asyncio
    async def test_ac02_payload_excludes_race_winner_even_when_output_key_matches(
        self,
    ) -> None:
        load_fn = AsyncMock(return_value=MagicMock())
        run_fn = AsyncMock(
            return_value={
                "intent": "done",
                "_race_winner": {"provider": "vertex", "model": "gemini-2.5-flash"},
            }
        )
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
    async def test_ac03_logs_race_winner_metadata_at_info(self) -> None:
        load_fn = AsyncMock(return_value=MagicMock())
        run_fn = AsyncMock(
            return_value={
                "result": "ok",
                "_race_winner": {"provider": "vertex", "model": "gemini-2.5-flash"},
            }
        )
        sent: list[tuple[str, str, dict | None]] = []
        with patch("yamlgraph.utils.fsm.graph_runner.logger.info") as mock_info:
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
            "stripping _race_winner metadata" in call.args[0]
            and call.args[1]["provider"] == "vertex"
            for call in mock_info.call_args_list
        )

    @pytest.mark.asyncio
    async def test_ac04_existing_route_and_event_map_resolution_unchanged(self) -> None:
        load_fn = AsyncMock(return_value=MagicMock())
        run_fn = AsyncMock(
            return_value={
                "intent": "unknown",
                "_route": "on_route",
                "result": "ok",
            }
        )
        sent: list[tuple[str, str, dict | None]] = []

        await run_and_dispatch(
            graph_path="/tmp/test.yaml",
            initial_state={"query": "hi"},
            input_key="query",
            output_key="result",
            event_key="intent",
            event_map={"done": "on_done"},
            success_event="completed",
            failure_event="failed",
            machine_name="router",
            load_fn=load_fn,
            run_fn=run_fn,
            send_fn=lambda machine, event, payload: sent.append(
                (machine, event, payload)
            ),
        )

        assert sent == [("router", "on_route", {"result": "ok"})]
