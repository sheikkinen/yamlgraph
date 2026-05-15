"""Acceptance tests for FR-391 phase-aware completion event resolution."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from yamlgraph.utils.fsm.graph_runner import run_and_dispatch


@pytest.mark.req("REQ-YG-319")
class TestFR391PhaseAwareEventResolution:
    """Shared FSM runner resolves completion events with phase-aware precedence."""

    @pytest.mark.asyncio
    async def test_ac01_completed_state_phase_is_checked_before_done_fallback(
        self,
    ) -> None:
        app = MagicMock()
        app.aget_state = AsyncMock(
            side_effect=[
                SimpleNamespace(next=()),
                SimpleNamespace(next=(), values={"phase": "crisis"}),
            ]
        )
        load_fn = AsyncMock(return_value=app)
        run_fn = AsyncMock(return_value={"intent": "unknown"})
        sent: list[tuple[str, str, dict | None]] = []

        await run_and_dispatch(
            graph_path="/tmp/test.yaml",
            initial_state={"user_input": "help"},
            input_key="user_input",
            output_key="result",
            event_key="intent",
            event_map={"crisis": "crisis_detected", "done": "completed"},
            success_event="success",
            failure_event="failed",
            machine_name="router",
            thread_id="thread-1",
            load_fn=load_fn,
            run_fn=run_fn,
            send_fn=lambda machine, event, payload: sent.append(
                (machine, event, payload)
            ),
        )

        assert sent == [("router", "crisis_detected", None)]

    @pytest.mark.asyncio
    async def test_ac02_phase_crisis_maps_to_crisis_event(self) -> None:
        app = MagicMock()
        app.aget_state = AsyncMock(
            side_effect=[
                SimpleNamespace(next=()),
                SimpleNamespace(next=(), values={"phase": "crisis"}),
            ]
        )
        load_fn = AsyncMock(return_value=app)
        run_fn = AsyncMock(return_value={"result": "ok"})
        sent: list[tuple[str, str, dict | None]] = []

        await run_and_dispatch(
            graph_path="/tmp/test.yaml",
            initial_state={"user_input": "help"},
            input_key="user_input",
            output_key="result",
            event_key="intent",
            event_map={"crisis": "crisis_detected", "done": "completed"},
            success_event="success",
            failure_event="failed",
            machine_name="router",
            thread_id="thread-1",
            load_fn=load_fn,
            run_fn=run_fn,
            send_fn=lambda machine, event, payload: sent.append(
                (machine, event, payload)
            ),
        )

        assert sent == [("router", "crisis_detected", {"result": "ok"})]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("completion_phase", "expected"),
        [("done", "completed"), (None, "completed"), ("unknown", "completed")],
    )
    async def test_ac03_missing_or_unknown_phase_falls_back_to_done(
        self, completion_phase: str | None, expected: str
    ) -> None:
        values = {"phase": completion_phase} if completion_phase is not None else {}
        app = MagicMock()
        app.aget_state = AsyncMock(
            side_effect=[
                SimpleNamespace(next=()),
                SimpleNamespace(next=(), values=values),
            ]
        )
        load_fn = AsyncMock(return_value=app)
        run_fn = AsyncMock(return_value={"intent": "unknown"})
        sent: list[tuple[str, str, dict | None]] = []

        await run_and_dispatch(
            graph_path="/tmp/test.yaml",
            initial_state={"user_input": "done"},
            input_key="user_input",
            output_key="result",
            event_key="intent",
            event_map={"done": "completed", "crisis": "crisis_detected"},
            success_event="success",
            failure_event="failed",
            machine_name="router",
            thread_id="thread-1",
            load_fn=load_fn,
            run_fn=run_fn,
            send_fn=lambda machine, event, payload: sent.append(
                (machine, event, payload)
            ),
        )

        assert sent == [("router", expected, None)]

    @pytest.mark.asyncio
    async def test_ac04_interrupt_continue_semantics_unchanged(self) -> None:
        app = MagicMock()
        app.aget_state = AsyncMock(
            side_effect=[
                SimpleNamespace(next=("awaiting_input",)),
                SimpleNamespace(next=("awaiting_input",), values={"phase": "crisis"}),
            ]
        )
        load_fn = AsyncMock(return_value=app)
        run_fn = AsyncMock(return_value={"intent": "done"})
        sent: list[tuple[str, str, dict | None]] = []

        await run_and_dispatch(
            graph_path="/tmp/test.yaml",
            initial_state={"user_input": "continue"},
            input_key="user_input",
            output_key="result",
            event_key="intent",
            event_map={
                "continue": "on_continue",
                "crisis": "crisis_detected",
                "done": "completed",
            },
            success_event="success",
            failure_event="failed",
            machine_name="router",
            thread_id="thread-1",
            load_fn=load_fn,
            run_fn=run_fn,
            send_fn=lambda machine, event, payload: sent.append(
                (machine, event, payload)
            ),
        )

        assert sent == [("router", "on_continue", None)]
