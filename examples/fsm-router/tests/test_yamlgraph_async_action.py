"""Tests for YAMLGraph async FSM action."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add example to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestYamlgraphAsyncAction:
    """Tests for the YamlgraphAsyncAction class."""

    @pytest.fixture
    def action_config(self):
        """Basic action configuration."""
        return {
            "type": "yamlgraph_async",
            "params": {
                "graph": "graphs/classifier.yaml",
                "input_key": "query",
                "output_key": "result",
                "success": "classified",
                "failure": "failed",
            },
        }

    @pytest.fixture
    def context(self):
        """Basic FSM context."""
        return {
            "machine_name": "test_router",
            "current_state": "classifying",
            "query": "Hello, how are you?",
        }

    def test_action_imports_correctly(self):
        """Test that the action can be imported."""
        pytest.importorskip("statemachine_engine")
        from actions.yamlgraph_async_action import YamlgraphAsyncAction

        assert YamlgraphAsyncAction is not None

    def test_action_inherits_base_action(self):
        """Test that action inherits from BaseAction."""
        pytest.importorskip("statemachine_engine")
        from actions.yamlgraph_async_action import YamlgraphAsyncAction
        from statemachine_engine.actions.base import BaseAction

        assert issubclass(YamlgraphAsyncAction, BaseAction)

    @pytest.mark.asyncio
    async def test_action_requires_graph_path(self, context):
        """Test that action fails without graph path."""
        pytest.importorskip("statemachine_engine")
        from actions.yamlgraph_async_action import YamlgraphAsyncAction

        config = {"params": {}}  # No graph path
        action = YamlgraphAsyncAction(config)

        event = await action.execute(context)

        assert event == "failed"

    @pytest.mark.asyncio
    async def test_action_returns_none_on_first_call(self, action_config, context):
        """Test that action returns None (fire-and-forget) on first call."""
        pytest.importorskip("statemachine_engine")
        from actions.yamlgraph_async_action import YamlgraphAsyncAction

        action = YamlgraphAsyncAction(action_config)

        with patch(
            "actions.yamlgraph_async_action._run_and_dispatch", new_callable=AsyncMock
        ):
            event = await action.execute(context)

        assert event is None

    @pytest.mark.asyncio
    async def test_guard_prevents_duplicate_launch(self, action_config, context):
        """Test that guard key prevents duplicate task launch."""
        pytest.importorskip("statemachine_engine")
        from actions.yamlgraph_async_action import YamlgraphAsyncAction

        action = YamlgraphAsyncAction(action_config)

        # Simulate guard already set
        context["_graph_running_classifying"] = True

        event = await action.execute(context)

        assert event is None  # Immediate return, no task launched

    @pytest.mark.asyncio
    async def test_guard_key_set_after_launch(self, action_config, context):
        """Test that guard key is set after task launch."""
        pytest.importorskip("statemachine_engine")
        from actions.yamlgraph_async_action import YamlgraphAsyncAction

        action = YamlgraphAsyncAction(action_config)

        with patch(
            "actions.yamlgraph_async_action._run_and_dispatch", new_callable=AsyncMock
        ):
            await action.execute(context)

        assert context.get("_graph_running_classifying") is True

    @pytest.mark.asyncio
    async def test_stale_guards_cleared(self, action_config, context):
        """Test that stale guards from other states are cleared."""
        pytest.importorskip("statemachine_engine")
        from actions.yamlgraph_async_action import YamlgraphAsyncAction

        action = YamlgraphAsyncAction(action_config)
        context["_graph_running_other_state"] = True

        with patch(
            "actions.yamlgraph_async_action._run_and_dispatch", new_callable=AsyncMock
        ):
            await action.execute(context)

        assert "_graph_running_other_state" not in context
        assert context.get("_graph_running_classifying") is True

    @pytest.mark.asyncio
    async def test_action_passes_variables_to_graph(self, context):
        """Test that action passes variables to initial_state."""
        pytest.importorskip("statemachine_engine")
        from actions.yamlgraph_async_action import YamlgraphAsyncAction

        config = {
            "params": {
                "graph": "graphs/test.yaml",
                "input_key": "query",
                "variables": {
                    "extra_context": "some value",
                    "from_context": "{machine_name}",
                },
                "success": "done",
                "failure": "failed",
            }
        }
        action = YamlgraphAsyncAction(config)

        def capture_create_task(coro):
            coro.close()

        with (
            patch(
                "actions.yamlgraph_async_action.asyncio.create_task",
                side_effect=capture_create_task,
            ),
            patch("actions.yamlgraph_async_action._run_and_dispatch") as mock_dispatch,
        ):
            await action.execute(context)
            call_kwargs = mock_dispatch.call_args

        # _run_and_dispatch is called with initial_state as kwarg
        initial_state = call_kwargs.kwargs.get("initial_state") or call_kwargs[1].get(
            "initial_state"
        )
        if initial_state is None:
            # positional
            initial_state = call_kwargs[0][1]

        assert initial_state["query"] == "Hello, how are you?"
        assert initial_state["extra_context"] == "some value"
        assert initial_state["from_context"] == "test_router"


class TestRunAndDispatch:
    """Tests for the _run_and_dispatch background task."""

    @pytest.mark.asyncio
    async def test_dispatches_route_event(self):
        """Test that route from result is dispatched."""
        pytest.importorskip("statemachine_engine")
        pytest.importorskip("yamlgraph")
        from actions.yamlgraph_async_action import _run_and_dispatch

        mock_result = {"_route": "complex", "category": "technical"}

        with (
            patch(
                "yamlgraph.executor_async.load_and_compile_async",
                new_callable=AsyncMock,
            ) as mock_load,
            patch(
                "yamlgraph.executor_async.run_graph_async", new_callable=AsyncMock
            ) as mock_run,
            patch("actions.yamlgraph_async_action._send_event") as mock_send,
        ):
            mock_load.return_value = MagicMock()
            mock_run.return_value = mock_result

            await _run_and_dispatch(
                graph_path="/tmp/test.yaml",
                initial_state={"query": "test"},
                output_key="result",
                event_key="",
                event_map={},
                success_event="classified",
                failure_event="failed",
                machine_name="test_router",
            )

        mock_send.assert_called_once_with("test_router", "complex", None)

    @pytest.mark.asyncio
    async def test_dispatches_event_map_result(self):
        """Test that event_map maps LLM output to FSM event."""
        pytest.importorskip("statemachine_engine")
        pytest.importorskip("yamlgraph")
        from actions.yamlgraph_async_action import _run_and_dispatch

        mock_result = {"intent": "goodbye"}

        with (
            patch(
                "yamlgraph.executor_async.load_and_compile_async",
                new_callable=AsyncMock,
            ) as mock_load,
            patch(
                "yamlgraph.executor_async.run_graph_async", new_callable=AsyncMock
            ) as mock_run,
            patch("actions.yamlgraph_async_action._send_event") as mock_send,
        ):
            mock_load.return_value = MagicMock()
            mock_run.return_value = mock_result

            await _run_and_dispatch(
                graph_path="/tmp/test.yaml",
                initial_state={"query": "bye"},
                output_key="intent",
                event_key="intent",
                event_map={"goodbye": "on_goodbye", "question": "on_question"},
                success_event="on_question",
                failure_event="failed",
                machine_name="test_router",
            )

        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[0][1] == "on_goodbye"

    @pytest.mark.asyncio
    async def test_dispatches_failure_on_error(self):
        """Test that failure event is dispatched on error."""
        pytest.importorskip("statemachine_engine")
        pytest.importorskip("yamlgraph")
        from actions.yamlgraph_async_action import _run_and_dispatch

        with (
            patch(
                "yamlgraph.executor_async.load_and_compile_async",
                new_callable=AsyncMock,
            ) as mock_load,
            patch("actions.yamlgraph_async_action._send_event") as mock_send,
        ):
            mock_load.side_effect = Exception("Graph compilation failed")

            await _run_and_dispatch(
                graph_path="/tmp/test.yaml",
                initial_state={"query": "test"},
                output_key="result",
                event_key="",
                event_map={},
                success_event="classified",
                failure_event="failed",
                machine_name="test_router",
            )

        mock_send.assert_called_once_with("test_router", "failed")

    @pytest.mark.asyncio
    async def test_guard_cleared_after_completion(self):
        """Test that guard key is cleared when task finishes."""
        pytest.importorskip("statemachine_engine")
        pytest.importorskip("yamlgraph")
        from actions.yamlgraph_async_action import _run_and_dispatch

        context = {"_graph_running_classifying": True}

        with (
            patch(
                "yamlgraph.executor_async.load_and_compile_async",
                new_callable=AsyncMock,
            ) as mock_load,
            patch(
                "yamlgraph.executor_async.run_graph_async", new_callable=AsyncMock
            ) as mock_run,
            patch("actions.yamlgraph_async_action._send_event"),
        ):
            mock_load.return_value = MagicMock()
            mock_run.return_value = {"result": "ok"}

            await _run_and_dispatch(
                graph_path="/tmp/test.yaml",
                initial_state={"query": "test"},
                output_key="result",
                event_key="",
                event_map={},
                success_event="classified",
                failure_event="failed",
                machine_name="test_router",
                context=context,
                guard_key="_graph_running_classifying",
            )

        assert "_graph_running_classifying" not in context


class TestFSMIntegration:
    """Integration tests for FSM + YAMLGraph."""

    def test_fsm_config_is_valid_yaml(self):
        """Test that FSM config is valid YAML."""
        import yaml

        config_path = Path(__file__).parent.parent / "config" / "router.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert config["initial_state"] == "waiting"
        assert "transitions" in config
        assert "actions" in config

    def test_fsm_config_uses_yamlgraph_async(self):
        """Test that all yamlgraph actions use type: yamlgraph_async."""
        import yaml

        config_path = Path(__file__).parent.parent / "config" / "router.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        actions = config.get("actions", {})
        for state, action_list in actions.items():
            for action in action_list:
                action_type = action.get("type", "")
                assert action_type != "yamlgraph", (
                    f"State '{state}' uses blocking type:yamlgraph — "
                    f"must use type:yamlgraph_async"
                )

    def test_yamlgraph_configs_are_valid(self):
        """Test that YAMLGraph configs are valid YAML."""
        import yaml

        graphs_dir = Path(__file__).parent.parent / "graphs"

        for graph_file in graphs_dir.glob("*.yaml"):
            with open(graph_file) as f:
                config = yaml.safe_load(f)

            assert "name" in config
            assert "nodes" in config
