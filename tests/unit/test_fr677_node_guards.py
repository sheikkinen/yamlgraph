"""FR-677 Move 1: guards honored on all side-effect node types (or rejected).

Guards were previously wired only into llm/router/copilot nodes. This module
proves the guard contract now extends to shell tool, python, and agent nodes,
and that declaring guards on a node type that cannot honor them is a
compile-time error rather than a silent no-op.
"""

import types
from unittest.mock import MagicMock, patch

import pytest
from langgraph.graph import StateGraph

from yamlgraph.compile.node_compiler import (
    GUARD_SUPPORTED_TYPES,
    GraphConfigError,
    compile_node,
)
from yamlgraph.tools.agent import create_agent_node
from yamlgraph.tools.nodes import create_tool_node
from yamlgraph.tools.python_tool import PythonToolConfig, create_python_node
from yamlgraph.tools.shell import ShellToolConfig
from yamlgraph.utils.guard_runtime import GuardHaltError


# --- module-level python tool functions (loaded by create_python_node) -------
def _return_scalar(state):
    return state.get("seed", 5)


def _return_dict_value(state):
    return {"value": state.get("seed", 5)}


def _fake_config():
    """Minimal stand-in for GraphConfig sufficient for compile_node's prologue."""
    return types.SimpleNamespace(
        loop_limits={},
        prompts_relative=False,
        prompts_dir=None,
        defaults={},
    )


# --- Move 1a: compile-time guard matrix --------------------------------------
class TestGuardCompileMatrix:
    """Guards may only be declared on supported node types."""

    @pytest.mark.req("REQ-YG-511")
    @pytest.mark.parametrize(
        "node_type",
        ["map", "race", "subgraph", "tool_call", "passthrough", "interrupt"],
    )
    def test_guards_on_unsupported_type_rejected(self, node_type):
        """Declaring guards on an unsupported type fails loud at compile."""
        graph = StateGraph(dict)
        node_config = {
            "type": node_type,
            "guards": {"post": [{"check": "output", "on_fail": "halt"}]},
        }
        with pytest.raises(GraphConfigError, match="guards"):
            compile_node("n", node_config, graph, _fake_config(), {}, {}, {})

    @pytest.mark.req("REQ-YG-511")
    def test_supported_types_include_side_effect_nodes(self):
        """The matrix admits tool, python, and agent (plus llm/router/copilot)."""
        for expected in ("tool", "python", "agent", "llm", "router", "copilot"):
            assert expected in GUARD_SUPPORTED_TYPES


# --- Move 1b: shell tool node guards -----------------------------------------
class TestToolNodeGuards:
    @pytest.mark.req("REQ-YG-511")
    def test_post_halt_raises(self):
        tools = {"echo": ShellToolConfig(command="echo hello")}
        node_config = {
            "tool": "echo",
            "guards": {
                "post": [
                    {
                        "check": "output | length > 100",
                        "on_fail": "halt",
                        "message": "output too short",
                    }
                ]
            },
        }
        node_fn = create_tool_node("n", node_config, tools)
        with pytest.raises(GuardHaltError, match="output too short"):
            node_fn({})

    @pytest.mark.req("REQ-YG-511")
    def test_post_pass_returns_output_unchanged(self):
        tools = {"echo": ShellToolConfig(command="echo hello")}
        node_config = {
            "tool": "echo",
            "guards": {"post": [{"check": "output | length < 100", "on_fail": "halt"}]},
        }
        node_fn = create_tool_node("n", node_config, tools)
        result = node_fn({})
        assert result["n"].strip() == "hello"

    @pytest.mark.req("REQ-YG-511")
    def test_pre_halt_raises_before_execution(self):
        tools = {"echo": ShellToolConfig(command="echo hello")}
        node_config = {
            "tool": "echo",
            "guards": {"pre": [{"check": "state.ready == 1", "on_fail": "halt"}]},
        }
        node_fn = create_tool_node("n", node_config, tools)
        with pytest.raises(GuardHaltError):
            node_fn({"ready": 0})

    @pytest.mark.req("REQ-YG-511")
    def test_pre_skip_returns_skip_state(self):
        tools = {"echo": ShellToolConfig(command="echo hello")}
        node_config = {
            "tool": "echo",
            "state_key": "out",
            "guards": {"pre": [{"check": "state.ready == 1", "on_fail": "skip"}]},
        }
        node_fn = create_tool_node("n", node_config, tools)
        result = node_fn({"ready": 0})
        assert result["out"] is None
        assert result["current_step"] == "n"


# --- Move 1c: python node guards ---------------------------------------------
class TestPythonNodeGuards:
    @pytest.mark.req("REQ-YG-511")
    def test_post_halt_raises(self):
        python_tools = {
            "t": PythonToolConfig(
                module="tests.unit.test_fr677_node_guards",
                function="_return_scalar",
            )
        }
        node_config = {
            "tool": "t",
            "state_key": "v",
            "guards": {"post": [{"check": "output > 10", "on_fail": "halt"}]},
        }
        node_fn = create_python_node("n", node_config, python_tools)
        with pytest.raises(GuardHaltError):
            node_fn({"seed": 5})

    @pytest.mark.req("REQ-YG-511")
    def test_post_pass_returns_value(self):
        python_tools = {
            "t": PythonToolConfig(
                module="tests.unit.test_fr677_node_guards",
                function="_return_scalar",
            )
        }
        node_config = {
            "tool": "t",
            "state_key": "v",
            "guards": {"post": [{"check": "output > 3", "on_fail": "halt"}]},
        }
        node_fn = create_python_node("n", node_config, python_tools)
        result = node_fn({"seed": 5})
        assert result["v"] == 5

    @pytest.mark.req("REQ-YG-511")
    def test_post_halt_on_dict_output_path(self):
        python_tools = {
            "t": PythonToolConfig(
                module="tests.unit.test_fr677_node_guards",
                function="_return_dict_value",
            )
        }
        node_config = {
            "tool": "t",
            "guards": {"post": [{"check": "output.value > 10", "on_fail": "halt"}]},
        }
        node_fn = create_python_node("n", node_config, python_tools)
        with pytest.raises(GuardHaltError):
            node_fn({"seed": 5})

    @pytest.mark.req("REQ-YG-511")
    def test_pre_halt_raises(self):
        python_tools = {
            "t": PythonToolConfig(
                module="tests.unit.test_fr677_node_guards",
                function="_return_scalar",
            )
        }
        node_config = {
            "tool": "t",
            "guards": {"pre": [{"check": "state.seed > 10", "on_fail": "halt"}]},
        }
        node_fn = create_python_node("n", node_config, python_tools)
        with pytest.raises(GuardHaltError):
            node_fn({"seed": 5})

    @pytest.mark.req("REQ-YG-511")
    def test_guard_halt_not_swallowed_by_on_error_skip(self):
        """A guard halt must surface even when on_error=skip is configured."""
        python_tools = {
            "t": PythonToolConfig(
                module="tests.unit.test_fr677_node_guards",
                function="_return_scalar",
            )
        }
        node_config = {
            "tool": "t",
            "on_error": "skip",
            "guards": {"post": [{"check": "output > 10", "on_fail": "halt"}]},
        }
        node_fn = create_python_node("n", node_config, python_tools)
        with pytest.raises(GuardHaltError):
            node_fn({"seed": 5})


# --- Move 1d: agent node guards ----------------------------------------------
MOCK_AGENT_PROMPT = {"system": "You are a helpful assistant.", "user": "{input}"}


@pytest.fixture
def _mock_agent_prompt():
    with patch("yamlgraph.tools.agent.load_prompt", return_value=MOCK_AGENT_PROMPT):
        yield


class TestAgentNodeGuards:
    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-511")
    def test_post_halt_raises(self, mock_create_llm, _mock_agent_prompt):
        mock_llm = MagicMock()
        response = MagicMock()
        response.tool_calls = []
        response.content = "short"
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = response
        mock_create_llm.return_value = mock_llm

        node_config = {
            "prompt": "agent",
            "tools": [],
            "state_key": "result",
            "guards": {"post": [{"check": "output | length > 100", "on_fail": "halt"}]},
        }
        node_fn = create_agent_node("agent", node_config, {})
        with pytest.raises(GuardHaltError):
            node_fn({"input": "hi"})

    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-511")
    def test_pre_skip_returns_skip_state_without_invoking_llm(
        self, mock_create_llm, _mock_agent_prompt
    ):
        mock_llm = MagicMock()
        mock_create_llm.return_value = mock_llm

        node_config = {
            "prompt": "agent",
            "tools": [],
            "state_key": "result",
            "guards": {"pre": [{"check": "state.ready == 1", "on_fail": "skip"}]},
        }
        node_fn = create_agent_node("agent", node_config, {})
        result = node_fn({"input": "hi", "ready": 0})
        assert result["result"] is None
        mock_llm.invoke.assert_not_called()

    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-511")
    def test_post_pass_returns_answer(self, mock_create_llm, _mock_agent_prompt):
        mock_llm = MagicMock()
        response = MagicMock()
        response.tool_calls = []
        response.content = "The answer is 42"
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = response
        mock_create_llm.return_value = mock_llm

        node_config = {
            "prompt": "agent",
            "tools": [],
            "state_key": "result",
            "guards": {"post": [{"check": "output | length > 0", "on_fail": "halt"}]},
        }
        node_fn = create_agent_node("agent", node_config, {})
        result = node_fn({"input": "hi"})
        assert result["result"] == "The answer is 42"
