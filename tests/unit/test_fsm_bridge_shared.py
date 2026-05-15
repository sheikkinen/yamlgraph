"""Framework-level tests for the shared FSM bridge module."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from langgraph.types import Command
from pydantic import BaseModel

from yamlgraph.utils.fsm.graph_runner import run_and_dispatch
from yamlgraph.utils.fsm.helpers import extract_event, json_safe, resolve_context_ref


class _IntentModel(BaseModel):
    intent: str


@pytest.mark.req("REQ-YG-319")
class TestSharedFSMHelpers:
    """Shared helper functions preserve canonical bridge semantics."""

    def test_extract_event_handles_string_and_model(self) -> None:
        event_map = {"goodbye": "on_goodbye", "question": "on_question"}

        assert extract_event(" GOODBYE ", event_map) == "on_goodbye"
        assert (
            extract_event(_IntentModel(intent="question"), event_map) == "on_question"
        )
        assert extract_event("unknown", event_map) is None

    def test_json_safe_and_context_ref_resolution(self) -> None:
        payload = {
            "plain": 1,
            "structured": _IntentModel(intent="goodbye"),
            "items": {"a", "b"},
        }
        converted = json_safe(payload)
        assert converted["plain"] == 1
        assert converted["structured"] == {"intent": "goodbye"}
        assert sorted(converted["items"]) == ["a", "b"]

        context = {"session_id": "thread-42"}
        assert resolve_context_ref("{session_id}", context) == "thread-42"
        assert (
            resolve_context_ref("{missing}", context, missing="fallback") == "fallback"
        )
        assert resolve_context_ref("literal", context) == "literal"


@pytest.mark.req("REQ-YG-319")
class TestSharedFSMEventCascade:
    """Event resolution follows interrupt → phase/done → event_map → route → success."""

    @pytest.mark.asyncio
    async def test_interrupt_continue_precedes_event_map_and_route(self) -> None:
        app = MagicMock()
        app.aget_state = AsyncMock(
            side_effect=[
                SimpleNamespace(next=("awaiting_input",)),
                SimpleNamespace(next=("awaiting_input",)),
            ]
        )
        load_fn = AsyncMock(return_value=app)
        run_fn = AsyncMock(
            return_value={
                "intent": "goodbye",
                "_route": "legacy",
                "result": "need more",
            }
        )
        sent: list[tuple[str, str, dict | None]] = []

        await run_and_dispatch(
            graph_path="/tmp/test.yaml",
            initial_state={"user_input": "continue"},
            input_key="user_input",
            output_key="result",
            event_key="intent",
            event_map={"continue": "on_continue", "goodbye": "on_goodbye"},
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

        assert isinstance(run_fn.await_args.args[1], Command)
        assert sent == [("router", "on_continue", {"result": "need more"})]

    @pytest.mark.asyncio
    async def test_interrupt_done_precedes_non_interrupt_cascade(self) -> None:
        app = MagicMock()
        app.aget_state = AsyncMock(
            side_effect=[SimpleNamespace(next=()), SimpleNamespace(next=())]
        )
        load_fn = AsyncMock(return_value=app)
        run_fn = AsyncMock(return_value={"intent": "goodbye", "_route": "legacy"})
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

    @pytest.mark.asyncio
    async def test_route_used_when_event_map_has_no_match(self) -> None:
        load_fn = AsyncMock(return_value=MagicMock())
        run_fn = AsyncMock(return_value={"intent": "unknown", "_route": "on_route"})
        sent: list[tuple[str, str, dict | None]] = []

        await run_and_dispatch(
            graph_path="/tmp/test.yaml",
            initial_state={"query": "hi"},
            input_key="query",
            output_key="result",
            event_key="intent",
            event_map={"goodbye": "on_goodbye"},
            success_event="completed",
            failure_event="failed",
            machine_name="router",
            load_fn=load_fn,
            run_fn=run_fn,
            send_fn=lambda machine, event, payload: sent.append(
                (machine, event, payload)
            ),
        )

        assert sent == [("router", "on_route", None)]

    @pytest.mark.asyncio
    async def test_guard_is_cleared_after_completion(self) -> None:
        load_fn = AsyncMock(return_value=MagicMock())
        run_fn = AsyncMock(return_value={"result": "ok"})
        sent: list[tuple[str, str, dict | None]] = []
        context = {"_graph_running_classifying": True}

        await run_and_dispatch(
            graph_path="/tmp/test.yaml",
            initial_state={"query": "hi"},
            input_key="query",
            output_key="result",
            event_key="result",
            event_map={},
            success_event="completed",
            failure_event="failed",
            machine_name="router",
            context=context,
            guard_key="_graph_running_classifying",
            load_fn=load_fn,
            run_fn=run_fn,
            send_fn=lambda machine, event, payload: sent.append(
                (machine, event, payload)
            ),
        )

        assert sent == [("router", "completed", {"result": "ok"})]
        assert "_graph_running_classifying" not in context
