"""Acceptance tests for FR-392 payload key forwarding in shared FSM runner."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel

from yamlgraph.utils.fsm.graph_runner import run_and_dispatch
from yamlgraph.utils.fsm.snapshot import SnapshotParams


class _PayloadModel(BaseModel):
    intent: str


def _snapshot(payload_keys: list[str] | None) -> SnapshotParams:
    return SnapshotParams(
        graph_path="/tmp/test.yaml",
        initial_state={"query": "hello"},
        input_key="query",
        output_key="result",
        event_key="intent",
        event_map={},
        success_event="completed",
        failure_event="failed",
        thread_id="thread-1",
        phase="graph",
        payload_keys=payload_keys,
    )


@pytest.mark.req("REQ-YG-347")
class TestFR392PayloadKeysForwardingRed:
    @pytest.mark.asyncio
    async def test_ac01_forwards_payload_keys_from_after_state(self) -> None:
        app = MagicMock()
        app.aget_state = AsyncMock(
            side_effect=[
                SimpleNamespace(next=()),
                SimpleNamespace(
                    next=(),
                    values={
                        "prior_messages": ["hi"],
                        "original_intent": "clarify",
                    },
                ),
            ]
        )
        load_fn = AsyncMock(return_value=app)
        run_fn = AsyncMock(return_value={"result": "ok"})
        sent: list[tuple[str, str, dict | None]] = []

        await run_and_dispatch(
            graph_path="/tmp/test.yaml",
            initial_state={"query": "hello"},
            input_key="query",
            output_key="result",
            event_key="intent",
            event_map={},
            success_event="completed",
            failure_event="failed",
            machine_name="router",
            thread_id="thread-1",
            snapshot=_snapshot(["prior_messages", "original_intent"]),
            load_fn=load_fn,
            run_fn=run_fn,
            send_fn=lambda machine, event, payload: sent.append(
                (machine, event, payload)
            ),
        )

        assert sent == [
            (
                "router",
                "completed",
                {
                    "result": "ok",
                    "prior_messages": ["hi"],
                    "original_intent": "clarify",
                },
            )
        ]

    @pytest.mark.asyncio
    async def test_ac02_skips_missing_payload_keys_without_error(self) -> None:
        app = MagicMock()
        app.aget_state = AsyncMock(
            side_effect=[
                SimpleNamespace(next=()),
                SimpleNamespace(next=(), values={"present": "yes", "none_value": None}),
            ]
        )
        load_fn = AsyncMock(return_value=app)
        run_fn = AsyncMock(return_value={"result": "ok"})
        sent: list[tuple[str, str, dict | None]] = []

        await run_and_dispatch(
            graph_path="/tmp/test.yaml",
            initial_state={"query": "hello"},
            input_key="query",
            output_key="result",
            event_key="intent",
            event_map={},
            success_event="completed",
            failure_event="failed",
            machine_name="router",
            thread_id="thread-1",
            snapshot=_snapshot(["present", "missing", "none_value"]),
            load_fn=load_fn,
            run_fn=run_fn,
            send_fn=lambda machine, event, payload: sent.append(
                (machine, event, payload)
            ),
        )

        assert sent == [("router", "completed", {"result": "ok", "present": "yes"})]

    @pytest.mark.asyncio
    async def test_ac03_serializes_payload_keys_with_json_safe(self) -> None:
        app = MagicMock()
        app.aget_state = AsyncMock(
            side_effect=[
                SimpleNamespace(next=()),
                SimpleNamespace(
                    next=(), values={"structured": _PayloadModel(intent="go")}
                ),
            ]
        )
        load_fn = AsyncMock(return_value=app)
        run_fn = AsyncMock(return_value={"result": "ok"})
        sent: list[tuple[str, str, dict | None]] = []

        await run_and_dispatch(
            graph_path="/tmp/test.yaml",
            initial_state={"query": "hello"},
            input_key="query",
            output_key="result",
            event_key="intent",
            event_map={},
            success_event="completed",
            failure_event="failed",
            machine_name="router",
            thread_id="thread-1",
            snapshot=_snapshot(["structured"]),
            load_fn=load_fn,
            run_fn=run_fn,
            send_fn=lambda machine, event, payload: sent.append(
                (machine, event, payload)
            ),
        )

        assert sent == [
            (
                "router",
                "completed",
                {"result": "ok", "structured": {"intent": "go"}},
            )
        ]

    @pytest.mark.asyncio
    async def test_ac04_preserves_existing_output_key_payload(self) -> None:
        app = MagicMock()
        app.aget_state = AsyncMock(
            side_effect=[
                SimpleNamespace(next=()),
                SimpleNamespace(
                    next=(), values={"result": "state-value", "extra": "x"}
                ),
            ]
        )
        load_fn = AsyncMock(return_value=app)
        run_fn = AsyncMock(return_value={"result": "runner-value"})
        sent: list[tuple[str, str, dict | None]] = []

        await run_and_dispatch(
            graph_path="/tmp/test.yaml",
            initial_state={"query": "hello"},
            input_key="query",
            output_key="result",
            event_key="intent",
            event_map={},
            success_event="completed",
            failure_event="failed",
            machine_name="router",
            thread_id="thread-1",
            snapshot=_snapshot(["result", "extra"]),
            load_fn=load_fn,
            run_fn=run_fn,
            send_fn=lambda machine, event, payload: sent.append(
                (machine, event, payload)
            ),
        )

        assert sent == [
            (
                "router",
                "completed",
                {"result": "runner-value", "extra": "x"},
            )
        ]

    @pytest.mark.asyncio
    async def test_ac05_legacy_non_checkpoint_path_unchanged(self) -> None:
        app = MagicMock()
        app.aget_state = AsyncMock()
        load_fn = AsyncMock(return_value=app)
        run_fn = AsyncMock(return_value={"result": "ok"})
        sent: list[tuple[str, str, dict | None]] = []

        await run_and_dispatch(
            graph_path="/tmp/test.yaml",
            initial_state={"query": "hello"},
            input_key="query",
            output_key="result",
            event_key="intent",
            event_map={},
            success_event="completed",
            failure_event="failed",
            machine_name="router",
            snapshot=_snapshot(["prior_messages"]),
            load_fn=load_fn,
            run_fn=run_fn,
            send_fn=lambda machine, event, payload: sent.append(
                (machine, event, payload)
            ),
        )

        app.aget_state.assert_not_awaited()
        assert sent == [("router", "completed", {"result": "ok"})]
