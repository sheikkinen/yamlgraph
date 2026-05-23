"""Tests for FR-448: Agent node structured output via prompt schema.

When an agent node's prompt defines a schema: block, the agent should
return a dict (via Pydantic model) instead of raw text.
"""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, Field

from yamlgraph.tools.agent import create_agent_node
from yamlgraph.tools.shell import ShellToolConfig


class JudgeVerdict(BaseModel):
    """Test schema for structured output."""

    verdict: str = Field(description="APPROVE or AMEND")
    reasoning: str = Field(description="Why")


# Prompt config WITHOUT schema
MOCK_PROMPT_NO_SCHEMA = {
    "system": "You are an assistant.",
    "user": "{input}",
}


@pytest.fixture
def tools():
    return {"search": ShellToolConfig(command="echo ok", description="Search")}


@pytest.fixture
def base_node_config():
    return {
        "prompt": "agent",
        "tools": ["search"],
        "max_iterations": 5,
        "state_key": "result",
    }


class TestAgentStructuredOutputNormalExit:
    """Agent returns dict when schema defined — normal exit (no tool calls)."""

    @patch("yamlgraph.tools.agent.load_prompt", return_value=MOCK_PROMPT_NO_SCHEMA)
    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-422")
    def test_returns_dict_when_schema_defined(
        self, mock_create_llm, _mock_prompt, tools, base_node_config
    ):
        """Agent with schema returns dict, not str."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = '{"verdict": "APPROVE", "reasoning": "Looks good"}'
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = mock_response
        mock_create_llm.return_value = mock_llm

        node_fn = create_agent_node(
            "agent", base_node_config, tools, output_model=JudgeVerdict
        )
        result = node_fn({"input": "Judge this"})

        assert isinstance(
            result["result"], dict
        ), f"Expected dict, got {type(result['result'])}"
        assert result["result"]["verdict"] == "APPROVE"
        assert result["result"]["reasoning"] == "Looks good"

    @patch("yamlgraph.tools.agent.load_prompt", return_value=MOCK_PROMPT_NO_SCHEMA)
    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-422")
    def test_validates_against_pydantic_model(
        self, mock_create_llm, _mock_prompt, tools, base_node_config
    ):
        """Returned dict validates against the Pydantic model."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = '{"verdict": "AMEND", "reasoning": "Issues found"}'
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = mock_response
        mock_create_llm.return_value = mock_llm

        node_fn = create_agent_node(
            "agent", base_node_config, tools, output_model=JudgeVerdict
        )
        result = node_fn({"input": "Judge this"})

        # Must be valid JudgeVerdict
        validated = JudgeVerdict.model_validate(result["result"])
        assert validated.verdict == "AMEND"


class TestAgentStructuredOutputMaxIterations:
    """Agent returns dict when schema defined — max iterations exit."""

    @patch("yamlgraph.tools.agent.load_prompt", return_value=MOCK_PROMPT_NO_SCHEMA)
    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-422")
    def test_returns_dict_on_max_iterations(
        self, mock_create_llm, _mock_prompt, tools, base_node_config
    ):
        """Agent hitting max_iterations still returns dict when schema defined."""
        base_node_config["max_iterations"] = 1  # Force max iterations

        mock_llm_base = MagicMock()
        # Always return tool calls — will hit max iterations
        mock_response = MagicMock()
        mock_response.tool_calls = [{"id": "call1", "name": "search", "args": {}}]
        mock_response.content = "Still working on it..."

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_response
        mock_llm_base.bind_tools.return_value = mock_llm

        # Mock structured output fallback path
        mock_structured = MagicMock()
        mock_structured_result = JudgeVerdict(verdict="APPROVE", reasoning="Done")
        mock_structured.invoke.return_value = mock_structured_result
        mock_llm_base.with_structured_output.return_value = mock_structured

        mock_create_llm.return_value = mock_llm_base

        node_fn = create_agent_node(
            "agent", base_node_config, tools, output_model=JudgeVerdict
        )
        result = node_fn({"input": "Judge this"})

        assert isinstance(
            result["result"], dict
        ), f"Expected dict, got {type(result['result'])}"
        assert result["result"]["verdict"] == "APPROVE"
        assert result["_agent_limit_reached"] is True


class TestAgentNoSchemaRegression:
    """Agent without schema continues to return text."""

    @patch("yamlgraph.tools.agent.load_prompt", return_value=MOCK_PROMPT_NO_SCHEMA)
    @patch("yamlgraph.tools.agent.create_llm")
    @pytest.mark.req("REQ-YG-422")
    def test_returns_text_without_schema(
        self, mock_create_llm, _mock_prompt, tools, base_node_config
    ):
        """Agent without schema returns text as before."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = "The answer is 42"
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = mock_response
        mock_create_llm.return_value = mock_llm

        node_fn = create_agent_node("agent", base_node_config, tools)
        result = node_fn({"input": "What?"})

        assert isinstance(result["result"], str)
        assert result["result"] == "The answer is 42"
