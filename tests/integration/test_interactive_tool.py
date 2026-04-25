"""Integration tests for FR-049: interactive_tool node type.

Tests the full YAML → load → expand → compile → invoke → resume pipeline
with deterministic stub tools (no LLM, no external deps).

Covers:
- T1: Basic 3-turn conversation (MemorySaver, sync)
- T2a: Natural exit at 5 turns (MemorySaver, sync)
- T2b: Loop limit exit (MemorySaver, sync, patched max_iterations=2)
- T3: No-end variant (MemorySaver, sync)
- T4: Async multi-turn (MemorySaver, async)
- T5: SQLite in-memory checkpointer (sync)
- T6: Stream mode 'values' (MemorySaver, sync)
- T7: Stream mode 'updates' (MemorySaver, sync)
- T8: Stream mode 'messages' (MemorySaver, async)
- T9: Redis checkpointer (async, skip if unavailable)
"""

from __future__ import annotations

from pathlib import Path

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from tests.integration.stubs.chatbot_tool import reset_sessions
from yamlgraph.graph_loader import compile_graph, load_graph_config

FIXTURES = Path(__file__).parent / "fixtures" / "interactive_tool"
CHATBOT_YAML = FIXTURES / "chatbot.yaml"
CHATBOT_NO_END_YAML = FIXTURES / "chatbot_no_end.yaml"


@pytest.fixture(autouse=True)
def _clean_sessions():
    """Reset stub session store before and after each test."""
    reset_sessions()
    yield
    reset_sessions()


def _compile_sync(yaml_path: Path, checkpointer=None):
    """Load, expand, compile a graph with given checkpointer."""
    config = load_graph_config(yaml_path)
    state_graph = compile_graph(config)
    return state_graph.compile(checkpointer=checkpointer or MemorySaver())


def _make_config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


# ── T1: Basic 3-Turn Conversation ────────────────────────────────


@pytest.mark.req("REQ-YG-075")
class TestBasic3Turn:
    """T1: start → ask → step loop, end tool, condition routing."""

    def test_basic_3_turn_conversation(self):
        graph = _compile_sync(CHATBOT_YAML)
        config = _make_config("t1-basic")

        # Turn 0: invoke → start runs, then interrupt (greeting)
        result = graph.invoke({}, config)
        assert "__interrupt__" in result
        assert (
            result.get("bot_response") == "Hello! I'm a stub chatbot. How can I help?"
        )

        # Turn 1: resume with "hello"
        result = graph.invoke(Command(resume="hello"), config)
        assert "__interrupt__" in result
        assert "You said 'hello'" in result.get("bot_response", "")

        # Turn 2: resume with "bye" → session closes, end tool runs
        result = graph.invoke(Command(resume="bye"), config)
        assert "__interrupt__" not in result
        assert result.get("session_done") is True
        assert "session_summary" in result
        assert "2 turns" in result["session_summary"]


# ── T2a: Natural Exit at 5 Turns ─────────────────────────────────


@pytest.mark.req("REQ-YG-075")
class TestNaturalExit:
    """T2a: stub sets session_done=True at turn 5 via condition routing."""

    def test_natural_exit_5_turns(self):
        graph = _compile_sync(CHATBOT_YAML)
        config = _make_config("t2a-natural")

        # Turn 0: greeting
        result = graph.invoke({}, config)
        assert "__interrupt__" in result

        # Turns 1-5: keep chatting (no "bye"); stub exits at turn >= 5
        for i in range(1, 6):
            result = graph.invoke(Command(resume=f"message {i}"), config)
            if "__interrupt__" not in result:
                # Stub hit turn >= 5, session_done=True, routed to end
                break

        # Should have completed (end tool ran)
        assert result.get("session_done") is True
        assert "session_summary" in result


# ── T2b: Loop Limit Exit ─────────────────────────────────────────


@pytest.mark.req("REQ-YG-075")
class TestLoopLimitExit:
    """T2b: max_iterations fires before condition → _loop_limit_reached → END."""

    def test_loop_limit_exit(self):
        # Load config, patch max_iterations to 2 before compile
        config_dict = load_graph_config(CHATBOT_YAML)

        # Patch the expanded step node's loop_limit
        # After expansion, chat__step has loop_limit from max_iterations
        nodes = config_dict.raw_config["nodes"]
        for name, node_cfg in nodes.items():
            if name.endswith("__step"):
                node_cfg["loop_limit"] = 2

        state_graph = compile_graph(config_dict)
        graph = state_graph.compile(checkpointer=MemorySaver())
        run_config = _make_config("t2b-limit")

        # Turn 0: greeting
        result = graph.invoke({}, run_config)
        assert "__interrupt__" in result

        # Loop limit=2 allows 2 successful step executions (counts 0, 1).
        # On the 3rd attempt (count 2 >= limit 2) → _loop_limit_reached=True → END.
        for i in range(1, 5):
            result = graph.invoke(Command(resume=f"msg{i}"), run_config)
            if result.get("_loop_limit_reached") or "__interrupt__" not in result:
                break

        # Graph should have terminated (loop limit bypasses end tool)
        assert result.get("_loop_limit_reached") is True
        # Loop limit bypass means end tool did NOT run
        assert result.get("session_summary") is None


# ── T3: No-End Variant ───────────────────────────────────────────


@pytest.mark.req("REQ-YG-075")
class TestNoEndVariant:
    """T3: step exits directly to END when loop_until fires (no end tool)."""

    def test_no_end_variant(self):
        graph = _compile_sync(CHATBOT_NO_END_YAML)
        config = _make_config("t3-no-end")

        # Turn 0: greeting
        result = graph.invoke({}, config)
        assert "__interrupt__" in result

        # Turn 1: say "bye" → session_done=True → route to END
        result = graph.invoke(Command(resume="bye"), config)
        assert "__interrupt__" not in result
        assert result.get("session_done") is True
        # No end tool → no session_summary
        assert "session_summary" not in result


# ── T4: Async Multi-Turn ─────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.req("REQ-YG-075")
class TestAsyncMultiTurn:
    """T4: async compilation and execution path."""

    async def test_async_multi_turn(self):
        # Compile manually with MemorySaver (async checkpointer)
        config_obj = load_graph_config(CHATBOT_YAML)
        state_graph = compile_graph(config_obj)
        app = state_graph.compile(checkpointer=MemorySaver())
        config = _make_config("t4-async")

        # Turn 0
        result = await app.ainvoke({}, config)
        assert "__interrupt__" in result
        assert "stub chatbot" in result.get("bot_response", "").lower()

        # Turn 1
        result = await app.ainvoke(Command(resume="async hello"), config)
        assert "__interrupt__" in result
        assert "async hello" in result.get("bot_response", "")

        # Turn 2: end
        result = await app.ainvoke(Command(resume="bye"), config)
        assert "__interrupt__" not in result
        assert result.get("session_done") is True


# ── T5: SQLite In-Memory Checkpointer ────────────────────────────


@pytest.mark.req("REQ-YG-075")
class TestSqliteCheckpointer:
    """T5: same flow as T1 but with SqliteSaver(:memory:)."""

    def test_sqlite_checkpointer(self):
        import sqlite3

        from langgraph.checkpoint.sqlite import SqliteSaver

        conn = sqlite3.connect(":memory:", check_same_thread=False)
        checkpointer = SqliteSaver(conn)

        graph = _compile_sync(CHATBOT_YAML, checkpointer=checkpointer)
        config = _make_config("t5-sqlite")

        # Turn 0
        result = graph.invoke({}, config)
        assert "__interrupt__" in result

        # Turn 1
        result = graph.invoke(Command(resume="sqlite hello"), config)
        assert "__interrupt__" in result
        assert "sqlite hello" in result.get("bot_response", "")

        # Turn 2: end
        result = graph.invoke(Command(resume="bye"), config)
        assert "__interrupt__" not in result
        assert result.get("session_done") is True
        assert "session_summary" in result

        conn.close()


# ── T6: Stream Mode — values ─────────────────────────────────────


@pytest.mark.req("REQ-YG-075")
class TestStreamValues:
    """T6: interrupt/resume via sync .stream(stream_mode='values').

    Note: this is the first sync .stream() test in the codebase.
    All prior streaming tests use async astream().
    """

    def test_stream_values(self):
        graph = _compile_sync(CHATBOT_YAML)
        config = _make_config("t6-values")

        # Turn 0: stream initial invocation
        chunks = list(graph.stream({}, config, stream_mode="values"))
        assert len(chunks) > 0
        # Last chunk should contain bot_response from start tool
        last = chunks[-1]
        assert "bot_response" in last

        # Turn 1: stream resume
        chunks = list(
            graph.stream(Command(resume="streamed hello"), config, stream_mode="values")
        )
        assert len(chunks) > 0
        # Find a chunk with updated bot_response
        responses = [c.get("bot_response", "") for c in chunks if "bot_response" in c]
        assert any("streamed hello" in r for r in responses)


# ── T7: Stream Mode — updates ────────────────────────────────────


@pytest.mark.req("REQ-YG-075")
class TestStreamUpdates:
    """T7: per-node update chunks via sync .stream(stream_mode='updates').

    Note: first sync .stream() with updates mode in the codebase.
    """

    def test_stream_updates(self):
        graph = _compile_sync(CHATBOT_YAML)
        config = _make_config("t7-updates")

        # Turn 0: should see chat__start node update
        chunks = list(graph.stream({}, config, stream_mode="updates"))
        assert len(chunks) > 0

        # Chunks are (node_name, update_dict) tuples in updates mode
        # Verify we see the expanded node names
        node_names = set()
        for chunk in chunks:
            if isinstance(chunk, tuple) and len(chunk) == 2:
                node_names.add(chunk[0])
            elif isinstance(chunk, dict):
                node_names.update(chunk.keys())

        # chat__start should appear
        assert any(
            "chat__start" in name for name in node_names
        ), f"Expected chat__start in node names, got: {node_names}"


# ── T8: Stream Mode — messages ───────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.req("REQ-YG-075")
class TestStreamMessages:
    """T8: messages mode doesn't crash; interrupt/resume works.

    Python nodes don't emit LangChain messages, so we only verify
    the graph runs without error through this stream mode.
    """

    async def test_stream_messages_no_crash(self):
        # Compile with MemorySaver for resume support
        config_obj = load_graph_config(CHATBOT_YAML)
        state_graph = compile_graph(config_obj)
        app = state_graph.compile(checkpointer=MemorySaver())
        config = _make_config("t8-messages")

        # Turn 0: initial invocation via astream messages
        chunks = []
        async for chunk in app.astream({}, config, stream_mode="messages"):
            chunks.append(chunk)
        # Should not crash — that's the primary assertion

        # Turn 1: resume via astream messages
        resume_chunks = []
        async for chunk in app.astream(
            Command(resume="msg hello"), config, stream_mode="messages"
        ):
            resume_chunks.append(chunk)
        # Graph should still be running (interrupt again)

        # Turn 2: end
        end_chunks = []
        async for chunk in app.astream(
            Command(resume="bye"), config, stream_mode="messages"
        ):
            end_chunks.append(chunk)
        # Session should complete


# ── T9: Redis Checkpointer (optional) ────────────────────────────


def _redis_available() -> bool:
    """Check if Redis is running on localhost."""
    try:
        import redis

        r = redis.Redis(host="localhost", port=6379, socket_connect_timeout=1)
        r.ping()
        return True
    except Exception:
        return False


@pytest.mark.asyncio
@pytest.mark.req("REQ-YG-075")
@pytest.mark.skipif(not _redis_available(), reason="Redis not available")
class TestRedisCheckpointer:
    """T9: interactive_tool with Redis checkpointer."""

    async def test_redis_checkpointer(self):
        from yamlgraph.storage.simple_redis import SimpleRedisCheckpointer

        checkpointer = SimpleRedisCheckpointer(
            redis_url="redis://localhost:6379",
            key_prefix="test-fr049a:",
            ttl=60,
        )

        config_obj = load_graph_config(CHATBOT_YAML)
        state_graph = compile_graph(config_obj)
        app = state_graph.compile(checkpointer=checkpointer)
        config = _make_config("t9-redis")

        # Turn 0
        result = await app.ainvoke({}, config)
        assert "__interrupt__" in result

        # Turn 1
        result = await app.ainvoke(Command(resume="redis hello"), config)
        assert "__interrupt__" in result

        # Turn 2: end
        result = await app.ainvoke(Command(resume="bye"), config)
        assert result.get("session_done") is True
