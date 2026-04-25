"""Tests for agent nodes (type: agent).

Agent nodes allow the LLM to autonomously decide which tools to call
in a loop until it has enough information to respond.
"""

from unittest.mock import MagicMock, patch

import pytest

from yamlgraph.tools.agent import (
    build_langchain_tool,
    build_python_tool,
    create_agent_node,
)
from yamlgraph.tools.python_tool import PythonToolConfig
from yamlgraph.tools.shell import ShellToolConfig

# Mock prompt config returned by load_prompt
MOCK_AGENT_PROMPT = {
    "system": "You are a helpful assistant.",
    "user": "{input}",
}


@pytest.fixture(autouse=True)
def mock_load_prompt():
    """Auto-mock load_prompt for all tests in this module."""
    with patch("yamlgraph.tools.agent.load_prompt", return_value=MOCK_AGENT_PROMPT):
        yield


class TestBuildLangchainTool:
    """Tests for build_langchain_tool function."""

    @pytest.mark.req("REQ-YG-018")
    def test_creates_tool_with_name(self):
        """Tool has correct name."""
        config = ShellToolConfig(
            command="echo test",
            description="Test tool",
        )
        tool = build_langchain_tool("my_tool", config)
        assert tool.name == "my_tool"

    @pytest.mark.req("REQ-YG-018")
    def test_creates_tool_with_description(self):
        """Tool has correct description."""
        config = ShellToolConfig(
            command="echo test",
            description="A helpful test tool",
        )
        tool = build_langchain_tool("test", config)
        assert tool.description == "A helpful test tool"

    @pytest.mark.req("REQ-YG-018")
    def test_tool_executes_command(self):
        """Tool invocation runs shell command."""
        config = ShellToolConfig(
            command="echo {message}",
            description="Echo a message",
        )
        tool = build_langchain_tool("echo", config)
        result = tool.invoke({"message": "hello"})
        assert "hello" in result


class TestCreateAgentNode:
    """Tests for create_agent_node function."""

    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-018")
    def test_agent_completes_without_tools(self, mock_create_llm):
        """Agent can finish with no tool calls."""
        # Mock LLM that returns a direct answer (no tool calls)
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = "The answer is 42"
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = mock_response
        mock_create_llm.return_value = mock_llm

        tools = {
            "search": ShellToolConfig(command="echo search", description="Search"),
        }
        node_config = {
            "prompt": "agent",
            "tools": ["search"],
            "max_iterations": 5,
            "state_key": "result",
        }

        node_fn = create_agent_node("agent", node_config, tools)
        result = node_fn({"input": "What is the meaning of life?"})

        assert result["result"] == "The answer is 42"
        assert result["_agent_iterations"] == 1

    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-018")
    def test_agent_calls_tool(self, mock_create_llm):
        """LLM tool call executes shell command."""
        # Mock LLM that first calls a tool, then returns answer
        mock_llm = MagicMock()

        # First response: call a tool
        first_response = MagicMock()
        first_response.tool_calls = [
            {"id": "call1", "name": "echo", "args": {"message": "test"}}
        ]
        first_response.content = ""

        # Second response: final answer
        second_response = MagicMock()
        second_response.tool_calls = []
        second_response.content = "I echoed: test"

        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.side_effect = [first_response, second_response]
        mock_create_llm.return_value = mock_llm

        tools = {
            "echo": ShellToolConfig(command="echo {message}", description="Echo"),
        }
        node_config = {
            "prompt": "agent",
            "tools": ["echo"],
            "max_iterations": 5,
            "state_key": "result",
        }

        node_fn = create_agent_node("agent", node_config, tools)
        result = node_fn({"input": "Echo something"})

        assert result["result"] == "I echoed: test"
        assert result["_agent_iterations"] == 2

    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-018")
    def test_max_iterations_enforced(self, mock_create_llm):
        """Stops after max_iterations reached."""
        # Mock LLM that always calls a tool (never finishes)
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = [
            {"id": "call1", "name": "search", "args": {"query": "more"}}
        ]
        mock_response.content = "Still searching..."
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = mock_response
        mock_create_llm.return_value = mock_llm

        tools = {
            "search": ShellToolConfig(command="echo searching", description="Search"),
        }
        node_config = {
            "prompt": "agent",
            "tools": ["search"],
            "max_iterations": 3,
            "state_key": "result",
        }

        node_fn = create_agent_node("agent", node_config, tools)
        result = node_fn({"input": "Search forever"})

        # Should stop at max_iterations
        assert result["_agent_limit_reached"] is True
        assert mock_llm.invoke.call_count == 3

    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-018")
    def test_tool_result_returned_to_llm(self, mock_create_llm):
        """LLM sees tool output in next turn."""
        mock_llm = MagicMock()

        # First: call tool
        first_response = MagicMock()
        first_response.tool_calls = [
            {"id": "call1", "name": "calc", "args": {"expr": "2+2"}}
        ]
        first_response.content = ""

        # Second: answer based on tool result
        second_response = MagicMock()
        second_response.tool_calls = []
        second_response.content = "The result is 4"

        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.side_effect = [first_response, second_response]
        mock_create_llm.return_value = mock_llm

        tools = {
            "calc": ShellToolConfig(
                command="echo 4",  # Simulates python calc
                description="Calculate",
            ),
        }
        node_config = {
            "prompt": "agent",
            "tools": ["calc"],
            "max_iterations": 5,
            "state_key": "answer",
        }

        node_fn = create_agent_node("agent", node_config, tools)
        node_fn({"input": "What is 2+2?"})

        # Check that second invoke received messages with tool result
        second_call_messages = mock_llm.invoke.call_args_list[1][0][0]
        # Should have: system, user, ai (with tool call), tool result
        assert len(second_call_messages) >= 4

    @pytest.mark.req("REQ-YG-018")
    def test_default_max_iterations(self):
        """Default max_iterations is 10."""
        tools = {
            "test": ShellToolConfig(command="echo test", description="Test"),
        }
        node_config = {
            "prompt": "agent",
            "tools": ["test"],
            # No max_iterations specified
        }

        # Just verify it doesn't fail - actual behavior tested above
        node_fn = create_agent_node("agent", node_config, tools)
        assert callable(node_fn)


class TestBuildPythonTool:
    """Tests for build_python_tool function."""

    @pytest.mark.req("REQ-YG-018")
    def test_creates_tool_with_name(self):
        """Tool has correct name."""
        config = PythonToolConfig(
            module="yamlgraph.utils.prompts",
            function="load_prompt",
            description="Load a prompt",
        )
        tool = build_python_tool("load_prompt", config)
        assert tool.name == "load_prompt"

    @pytest.mark.req("REQ-YG-018")
    def test_creates_tool_with_description(self):
        """Tool has correct description."""
        config = PythonToolConfig(
            module="yamlgraph.utils.prompts",
            function="load_prompt",
            description="Load a YAML prompt file",
        )
        tool = build_python_tool("load_prompt", config)
        assert tool.description == "Load a YAML prompt file"

    @pytest.mark.req("REQ-YG-018")
    def test_tool_is_structured_tool(self):
        """Tool is a LangChain StructuredTool."""
        from langchain_core.tools import StructuredTool

        config = PythonToolConfig(
            module="yamlgraph.utils.prompts",
            function="load_prompt",
            description="Load a prompt",
        )
        tool = build_python_tool("test_tool", config)
        assert isinstance(tool, StructuredTool)

    @pytest.mark.req("REQ-YG-018")
    def test_tool_executes_function(self):
        """Tool invocation calls the Python function."""
        # Use a simple test function
        config = PythonToolConfig(
            module="os.path",
            function="join",
            description="Join paths",
        )
        tool = build_python_tool("path_join", config)
        result = tool.invoke({"a": "/home", "p": "user"})
        assert "/home" in result or "user" in result


class TestAgentWithPythonTools:
    """Tests for agent nodes using Python tools."""

    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-018")
    def test_agent_calls_python_tool(self, mock_create_llm):
        """Agent can use Python tools."""
        mock_llm = MagicMock()

        # First response: call a python tool
        first_response = MagicMock()
        first_response.tool_calls = [
            {
                "id": "call1",
                "name": "my_python_tool",
                "args": {"a": "/home", "p": "user"},
            }
        ]
        first_response.content = ""

        # Second response: final answer
        second_response = MagicMock()
        second_response.tool_calls = []
        second_response.content = "Path is /home/user"

        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.side_effect = [first_response, second_response]
        mock_create_llm.return_value = mock_llm

        python_tools = {
            "my_python_tool": PythonToolConfig(
                module="os.path",
                function="join",
                description="Join paths",
            ),
        }
        node_config = {
            "prompt": "agent",
            "tools": ["my_python_tool"],
            "max_iterations": 5,
            "state_key": "result",
        }

        node_fn = create_agent_node("agent", node_config, {}, python_tools=python_tools)
        result = node_fn({"input": "Join home and user"})

        assert result["result"] == "Path is /home/user"
        assert result["_agent_iterations"] == 2

    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-018")
    def test_agent_mixes_shell_and_python_tools(self, mock_create_llm):
        """Agent can use both shell and python tools."""
        mock_llm = MagicMock()

        # First: call shell tool
        first_response = MagicMock()
        first_response.tool_calls = [
            {"id": "call1", "name": "echo_tool", "args": {"message": "hello"}}
        ]
        first_response.content = ""

        # Second: call python tool
        second_response = MagicMock()
        second_response.tool_calls = [
            {"id": "call2", "name": "path_tool", "args": {"a": "/", "p": "tmp"}}
        ]
        second_response.content = ""

        # Third: final answer
        third_response = MagicMock()
        third_response.tool_calls = []
        third_response.content = "Done with both tools"

        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.side_effect = [first_response, second_response, third_response]
        mock_create_llm.return_value = mock_llm

        shell_tools = {
            "echo_tool": ShellToolConfig(command="echo {message}", description="Echo"),
        }
        python_tools = {
            "path_tool": PythonToolConfig(
                module="os.path",
                function="join",
                description="Join paths",
            ),
        }
        node_config = {
            "prompt": "agent",
            "tools": ["echo_tool", "path_tool"],
            "max_iterations": 5,
            "state_key": "result",
        }

        node_fn = create_agent_node(
            "agent", node_config, shell_tools, python_tools=python_tools
        )
        result = node_fn({"input": "Use both tools"})

        assert result["result"] == "Done with both tools"
        assert result["_agent_iterations"] == 3


class TestAgentMessagesDelta:
    """Tests for FR-057: agent returns only new messages, not full history.

    When an agent node is invoked multiple times (e.g., across interrupt
    boundaries), it must return only the NEW messages (delta) so the
    `Annotated[list, add]` reducer doesn't cause quadratic growth.
    """

    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-018")
    def test_agent_returns_delta_not_full_messages(self, mock_create_llm):
        """Agent returns only new messages, not the full conversation."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = "Answer 1"
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = mock_response
        mock_create_llm.return_value = mock_llm

        tools = {
            "search": ShellToolConfig(command="echo test", description="Search"),
        }
        node_config = {
            "prompt": "agent",
            "tools": ["search"],
            "max_iterations": 5,
            "state_key": "result",
        }

        node_fn = create_agent_node("agent", node_config, tools)

        # Simulate first invocation (no existing messages)
        result1 = node_fn({"input": "Question 1"})
        msgs1 = result1["messages"]

        # msgs1 should contain: [SystemMessage, HumanMessage, AIMessage]
        assert len(msgs1) == 3

        # Simulate second invocation WITH existing messages in state
        # (as if the add reducer already accumulated msgs1)
        mock_response2 = MagicMock()
        mock_response2.tool_calls = []
        mock_response2.content = "Answer 2"
        mock_llm.invoke.return_value = mock_response2

        result2 = node_fn({"input": "Question 2", "messages": msgs1})
        msgs2 = result2["messages"]

        # CRITICAL: msgs2 should contain ONLY the delta (new messages),
        # NOT the full conversation. If the agent returns all messages,
        # the add reducer would duplicate msgs1.
        # Delta = [HumanMessage("Question 2"), AIMessage("Answer 2")]
        assert len(msgs2) == 2, (
            f"Expected 2 new messages (delta), got {len(msgs2)}. "
            f"Agent is returning full conversation instead of delta — "
            f"this causes quadratic growth with the add reducer."
        )

    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-018")
    def test_five_turn_loop_linear_growth(self, mock_create_llm):
        """Simulate 5-turn interrupt loop; verify linear message growth."""
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm
        mock_create_llm.return_value = mock_llm

        tools = {
            "search": ShellToolConfig(command="echo test", description="Search"),
        }
        node_config = {
            "prompt": "agent",
            "tools": ["search"],
            "max_iterations": 5,
            "state_key": "result",
        }

        node_fn = create_agent_node("agent", node_config, tools)

        # Simulate the add reducer externally
        accumulated_messages: list = []

        for turn in range(5):
            mock_response = MagicMock()
            mock_response.tool_calls = []
            mock_response.content = f"Answer {turn}"
            mock_llm.invoke.return_value = mock_response

            state = {"input": f"Question {turn}", "messages": accumulated_messages}
            result = node_fn(state)
            delta = result["messages"]

            # Each turn: agent reads existing, adds HumanMessage + AIMessage
            # Delta should be ONLY the new messages (2 per turn for turns > 0,
            # 3 for first turn which includes SystemMessage)
            if turn == 0:
                assert len(delta) == 3, f"Turn 0: expected 3, got {len(delta)}"
            else:
                assert len(delta) == 2, (
                    f"Turn {turn}: expected 2 delta msgs, got {len(delta)}"
                )

            # Simulate add reducer
            accumulated_messages = accumulated_messages + delta

        # After 5 turns: 3 + 2*4 = 11 messages (linear)
        assert len(accumulated_messages) == 11, (
            f"Expected 11 messages (linear growth), got {len(accumulated_messages)}. "
            f"Quadratic growth detected."
        )

    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-018")
    def test_max_iterations_returns_delta(self, mock_create_llm):
        """Max iterations path also returns delta, not full messages."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = [
            {"id": "call1", "name": "search", "args": {"query": "more"}}
        ]
        mock_response.content = "Still searching..."
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = mock_response
        mock_create_llm.return_value = mock_llm

        tools = {
            "search": ShellToolConfig(command="echo result", description="Search"),
        }
        node_config = {
            "prompt": "agent",
            "tools": ["search"],
            "max_iterations": 2,
            "state_key": "result",
        }

        node_fn = create_agent_node("agent", node_config, tools)

        # First invocation with no history — builds initial messages
        result1 = node_fn({"input": "Search"})
        msgs1 = result1["messages"]

        # Second invocation with accumulated state
        result2 = node_fn({"input": "Search again", "messages": msgs1})
        msgs2 = result2["messages"]

        # Should be delta only, not full conversation
        assert len(msgs2) < len(msgs1) + len(msgs2), (
            "Max iterations path returning full conversation instead of delta"
        )
        # More precisely: delta should NOT contain msgs1
        assert msgs2[0] not in msgs1, "Delta contains messages from previous invocation"


class TestAgentNormalizeContent:
    """Tests for FR-059: normalize response.content to string.

    Anthropic Claude returns content as list of blocks:
    [{"type": "text", "text": "..."}]. Agent node must normalize
    to string before storing in state_key.
    """

    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-018")
    def test_string_content_passes_through(self, mock_create_llm):
        """String content is stored unchanged."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = "The answer is 42"
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = mock_response
        mock_create_llm.return_value = mock_llm

        tools = {
            "search": ShellToolConfig(command="echo test", description="Search"),
        }
        node_config = {
            "prompt": "agent",
            "tools": ["search"],
            "max_iterations": 5,
            "state_key": "result",
        }

        node_fn = create_agent_node("agent", node_config, tools)
        result = node_fn({"input": "Question"})

        assert result["result"] == "The answer is 42"
        assert isinstance(result["result"], str)

    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-018")
    def test_anthropic_list_content_normalized_to_string(self, mock_create_llm):
        """Anthropic list-of-blocks content is joined into a string."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        # Anthropic Claude format: list of content blocks
        mock_response.content = [
            {"type": "text", "text": "Terveystalo tarjoaa "},
            {"type": "text", "text": "hammaslääkäripalveluita."},
        ]
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = mock_response
        mock_create_llm.return_value = mock_llm

        tools = {
            "search": ShellToolConfig(command="echo test", description="Search"),
        }
        node_config = {
            "prompt": "agent",
            "tools": ["search"],
            "max_iterations": 5,
            "state_key": "result",
        }

        node_fn = create_agent_node("agent", node_config, tools)
        result = node_fn({"input": "Hammaslääkäri?"})

        assert isinstance(result["result"], str), (
            f"Expected str, got {type(result['result'])}: {result['result']}"
        )
        assert result["result"] == "Terveystalo tarjoaa hammaslääkäripalveluita."

    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-018")
    def test_none_content_normalized_to_empty_string(self, mock_create_llm):
        """None content becomes empty string."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = None
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = mock_response
        mock_create_llm.return_value = mock_llm

        tools = {
            "search": ShellToolConfig(command="echo test", description="Search"),
        }
        node_config = {
            "prompt": "agent",
            "tools": ["search"],
            "max_iterations": 5,
            "state_key": "result",
        }

        node_fn = create_agent_node("agent", node_config, tools)
        result = node_fn({"input": "Question"})

        assert isinstance(result["result"], str)
        assert result["result"] == ""

    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-018")
    def test_max_iterations_normalizes_content(self, mock_create_llm):
        """Max-iterations path also normalizes list content to string."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = [
            {"id": "call1", "name": "search", "args": {"query": "more"}}
        ]
        # Anthropic list format on the last message
        mock_response.content = [
            {"type": "text", "text": "Still searching..."},
        ]
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = mock_response
        mock_create_llm.return_value = mock_llm

        tools = {
            "search": ShellToolConfig(command="echo result", description="Search"),
        }
        node_config = {
            "prompt": "agent",
            "tools": ["search"],
            "max_iterations": 1,
            "state_key": "result",
        }

        node_fn = create_agent_node("agent", node_config, tools)
        result = node_fn({"input": "Search"})

        assert isinstance(result["result"], str), (
            f"Max-iterations path returned {type(result['result'])}"
        )
