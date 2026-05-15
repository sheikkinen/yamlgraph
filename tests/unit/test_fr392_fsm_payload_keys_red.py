"""Acceptance tests for FR-392 payload_keys forwarding in shared FSM runner."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from yamlgraph.utils.fsm.graph_runner import run_and_dispatch
from yamlgraph.utils.fsm.snapshot import SnapshotParams


def _snapshot(payload_keys: list[str] | None) -> SnapshotParams:
    return SnapshotParams(
        graph_path="/tmp/test.yaml",
        initial_state={"user_input": "hello"},
        input_key="user_input",
        output_key="result",
        event_key="intent",
        event_map={"done": "completed"},
        success_event="completed",
        failure_event="failed",
        thread_id="thread-1",
        phase="graph",
        payload_keys=payload_keys,
    )


@pytest.mark.req("REQ-YG-319")
class TestFR392PayloadKeysForwarding:
    @pytest.mark.asyncio
    async def test_ac01_payload_keys_are_forwarded_from_checkpoint_state_values(
        self,
    ) -> None:
        app = MagicMock()
        app.aget_state = AsyncMock(
            side_effect=[
                SimpleNamespace(next=()),
                SimpleNamespace(next=(), values={"session_id": "s-1"}),
            ]
        )
        load_fn = AsyncMock(return_value=app)
        run_fn = AsyncMock(return_value={"result": "ok"})
        sent: list[tuple[str, str, dict | None]] = []

        await run_and_dispatch(
            graph_path="/tmp/test.yaml",
            initial_state={"user_input": "hello"},
            input_key="user_input",
            output_key="result",
            event_key="intent",
            event_map={"done": "completed"},
            success_event="completed",
            failure_event="failed",
            machine_name="router",
            thread_id="thread-1",
            load_fn=load_fn,
            run_fn=run_fn,
            snapshot=_snapshot(["session_id"]),
            send_fn=lambda machine, event, payload: sent.append(
                (machine, event, payload)
            ),
        )

        assert sent == [("router", "completed", {"result": "ok", "session_id": "s-1"})]

    @pytest.mark.asyncio
    async def test_ac02_missing_payload_keys_are_skipped_without_error(self) -> None:
        app = MagicMock()
        app.aget_state = AsyncMock(
            side_effect=[
                SimpleNamespace(next=()),
                SimpleNamespace(next=(), values={"phase": "done"}),
            ]
        )
        load_fn = AsyncMock(return_value=app)
        run_fn = AsyncMock(return_value={"result": "ok"})
        sent: list[tuple[str, str, dict | None]] = []

        await run_and_dispatch(
            graph_path="/tmp/test.yaml",
            initial_state={"user_input": "hello"},
            input_key="user_input",
            output_key="result",
            event_key="intent",
            event_map={"done": "completed"},
            success_event="completed",
            failure_event="failed",
            machine_name="router",
            thread_id="thread-1",
            load_fn=load_fn,
            run_fn=run_fn,
            snapshot=_snapshot(["missing_key"]),
            send_fn=lambda machine, event, payload: sent.append(
                (machine, event, payload)
            ),
        )

        assert sent == [("router", "completed", {"result": "ok"})]

    @pytest.mark.asyncio
    async def test_ac03_none_payload_values_are_not_emitted(self) -> None:
        app = MagicMock()
        app.aget_state = AsyncMock(
            side_effect=[
                SimpleNamespace(next=()),
                SimpleNamespace(next=(), values={"session_id": None}),
            ]
        )
        load_fn = AsyncMock(return_value=app)
        run_fn = AsyncMock(return_value={"result": "ok"})
        sent: list[tuple[str, str, dict | None]] = []

        await run_and_dispatch(
            graph_path="/tmp/test.yaml",
            initial_state={"user_input": "hello"},
            input_key="user_input",
            output_key="result",
            event_key="intent",
            event_map={"done": "completed"},
            success_event="completed",
            failure_event="failed",
            machine_name="router",
            thread_id="thread-1",
            load_fn=load_fn,
            run_fn=run_fn,
            snapshot=_snapshot(["session_id"]),
            send_fn=lambda machine, event, payload: sent.append(
                (machine, event, payload)
            ),
        )

        assert sent == [("router", "completed", {"result": "ok"})]

    @pytest.mark.asyncio
    async def test_ac04_output_key_payload_is_preserved_with_payload_keys(
        self,
    ) -> None:
        app = MagicMock()
        app.aget_state = AsyncMock(
            side_effect=[
                SimpleNamespace(next=()),
                SimpleNamespace(
                    next=(),
                    values={"result": "from-checkpoint", "session_id": "s-1"},
                ),
            ]
        )
        load_fn = AsyncMock(return_value=app)
        run_fn = AsyncMock(return_value={"result": "from-run"})
        sent: list[tuple[str, str, dict | None]] = []

        await run_and_dispatch(
            graph_path="/tmp/test.yaml",
            initial_state={"user_input": "hello"},
            input_key="user_input",
            output_key="result",
            event_key="intent",
            event_map={"done": "completed"},
            success_event="completed",
            failure_event="failed",
            machine_name="router",
            thread_id="thread-1",
            load_fn=load_fn,
            run_fn=run_fn,
            snapshot=_snapshot(["result", "session_id"]),
            send_fn=lambda machine, event, payload: sent.append(
                (machine, event, payload)
            ),
        )

        assert sent == [
            ("router", "completed", {"result": "from-run", "session_id": "s-1"})
        ]

    @pytest.mark.asyncio
    async def test_ac05_legacy_path_without_thread_id_remains_unchanged(self) -> None:
        app = MagicMock()
        app.aget_state = AsyncMock()
        load_fn = AsyncMock(return_value=app)
        run_fn = AsyncMock(return_value={"result": "ok"})
        sent: list[tuple[str, str, dict | None]] = []

        await run_and_dispatch(
            graph_path="/tmp/test.yaml",
            initial_state={"user_input": "hello"},
            input_key="user_input",
            output_key="result",
            event_key="intent",
            event_map={},
            success_event="completed",
            failure_event="failed",
            machine_name="router",
            load_fn=load_fn,
            run_fn=run_fn,
            snapshot=_snapshot(["session_id"]),
            send_fn=lambda machine, event, payload: sent.append(
                (machine, event, payload)
            ),
        )

        assert sent == [("router", "completed", {"result": "ok"})]
        app.aget_state.assert_not_awaited()
