"""FR-449: Agent structured output fails with Anthropic content format.

Anthropic returns response.content as list[dict] (content blocks),
not str. This causes _try_structured_output to crash silently,
returning prose text instead of a structured dict.

These tests condemn the bug by using Anthropic-format content blocks.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from yamlgraph.node_factory.base import get_output_model_for_node
from yamlgraph.tools.agent import _try_structured_output, create_agent_node
from yamlgraph.tools.shell import ShellToolConfig

MOCK_PROMPT = {
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


PROMPT_YAML_WITH_SCHEMA = """\
schema:
  name: SimpleVerdict
  fields:
    verdict:
      type: str
      description: "APPROVE or REJECT"
    reasoning:
      type: str
      description: "Why"
system: You are a judge.
user: "Judge: {input}"
"""


@pytest.fixture
def prompt_with_schema(tmp_path):
    """Create a minimal prompt YAML with inline schema."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    prompt_file = prompts_dir / "judge.yaml"
    prompt_file.write_text(PROMPT_YAML_WITH_SCHEMA)
    return tmp_path


class TestAnthropicContentBlocks:
    """FR-449 Bug 1: Anthropic returns content as list of blocks."""

    @pytest.mark.req("REQ-YG-422")
    def test_try_structured_output_with_list_content(self):
        """_try_structured_output handles Anthropic list content blocks."""
        # Build a real output model from inline schema YAML
        import tempfile

        from yamlgraph.schema_loader import load_schema_from_yaml

        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
            f.write(PROMPT_YAML_WITH_SCHEMA)
            f.flush()
            output_model = load_schema_from_yaml(Path(f.name))

        # Anthropic format: list of content block dicts
        content = [
            {"type": "text", "text": '{"verdict": "APPROVE", "reasoning": "Solid"}'}
        ]
        result = _try_structured_output(
            content, msgs=[], output_model=output_model, llm_base=MagicMock()
        )
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        assert result["verdict"] == "APPROVE"
        assert result["reasoning"] == "Solid"

    @pytest.mark.req("REQ-YG-422")
    @patch("yamlgraph.tools.agent.load_prompt", return_value=MOCK_PROMPT)
    @patch("yamlgraph.tools.agent.create_llm")
    def test_agent_node_with_anthropic_content_returns_dict(
        self, mock_create_llm, _mock_prompt, tools, base_node_config
    ):
        """Full agent node returns dict when LLM gives Anthropic list content."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        # Anthropic format — the bug: this is list, not str
        mock_response.content = [
            {
                "type": "text",
                "text": '{"verdict": "AMEND", "reasoning": "Needs work"}',
            }
        ]
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = mock_response
        mock_create_llm.return_value = mock_llm

        import tempfile

        from yamlgraph.schema_loader import load_schema_from_yaml

        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
            f.write(PROMPT_YAML_WITH_SCHEMA)
            f.flush()
            output_model = load_schema_from_yaml(Path(f.name))

        node_fn = create_agent_node(
            "agent", base_node_config, tools, output_model=output_model
        )
        result = node_fn({"input": "Judge this"})

        assert isinstance(
            result["result"], dict
        ), f"Expected dict, got {type(result['result'])}: {str(result['result'])[:100]}"
        assert result["result"]["verdict"] == "AMEND"


class TestAnthropicFallbackPath:
    """FR-449 Bug 2: Fallback path fails when messages end with AIMessage."""

    @pytest.mark.req("REQ-YG-422")
    def test_try_structured_output_fallback_with_ai_message_last(self):
        """Fallback works when conversation ends with AIMessage (Anthropic constraint)."""
        import tempfile

        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        from yamlgraph.schema_loader import load_schema_from_yaml

        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
            f.write(PROMPT_YAML_WITH_SCHEMA)
            f.flush()
            output_model = load_schema_from_yaml(Path(f.name))

        # Content is prose, not JSON — forces fallback to structured LLM re-invoke
        content = "I have completed my analysis and the FR looks good."

        msgs = [
            SystemMessage(content="You are a judge."),
            HumanMessage(content="Judge this FR."),
            AIMessage(content="I have completed my analysis and the FR looks good."),
        ]

        mock_llm_base = MagicMock()
        mock_structured = MagicMock()
        mock_structured_result = output_model(verdict="APPROVE", reasoning="Solid")
        mock_structured.invoke.return_value = mock_structured_result
        mock_llm_base.with_structured_output.return_value = mock_structured

        result = _try_structured_output(
            content, msgs=msgs, output_model=output_model, llm_base=mock_llm_base
        )

        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        assert result["verdict"] == "APPROVE"

        # Verify fallback was called with messages ending in HumanMessage
        call_args = mock_structured.invoke.call_args[0][0]
        assert (
            call_args[-1].type == "human"
        ), f"Last message should be HumanMessage, got {call_args[-1].type}"


class TestPipelineSchemaResolution:
    """FR-449: Full pipeline from prompt YAML schema → agent node → dict output.

    Exercises the same call chain as node_compiler.py:
    get_output_model_for_node() → create_agent_node(output_model=...) → invoke
    """

    @pytest.mark.req("REQ-YG-422")
    @patch("yamlgraph.tools.agent.load_prompt", return_value=MOCK_PROMPT)
    @patch("yamlgraph.tools.agent.create_llm")
    def test_pipeline_with_anthropic_list_content(
        self, mock_create_llm, _mock_prompt, tools, prompt_with_schema
    ):
        """Schema resolved from prompt YAML + Anthropic content → dict output."""
        # Step 1: Resolve output model the same way node_compiler.py does
        node_config = {
            "prompt": "judge",
            "tools": ["search"],
            "max_iterations": 5,
            "state_key": "verdict",
        }
        output_model = get_output_model_for_node(
            node_config,
            prompts_dir=prompt_with_schema / "prompts",
        )
        assert output_model is not None, "Schema not resolved from prompt YAML"

        # Step 2: Mock LLM returning Anthropic-format content blocks
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = [
            {
                "type": "text",
                "text": '{"verdict": "APPROVE", "reasoning": "Looks good"}',
            }
        ]
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = mock_response
        mock_create_llm.return_value = mock_llm

        # Step 3: Create agent node with resolved output model
        node_fn = create_agent_node(
            "judge", node_config, tools, output_model=output_model
        )
        result = node_fn({"input": "Evaluate this"})

        # Step 4: Assert structured dict output
        assert isinstance(
            result["verdict"], dict
        ), f"Expected dict, got {type(result['verdict'])}: {str(result['verdict'])[:200]}"
        assert result["verdict"]["verdict"] == "APPROVE"
        assert result["verdict"]["reasoning"] == "Looks good"

    @pytest.mark.req("REQ-YG-422")
    @patch("yamlgraph.tools.agent.load_prompt", return_value=MOCK_PROMPT)
    @patch("yamlgraph.tools.agent.create_llm")
    def test_pipeline_with_prose_content_falls_back(
        self, mock_create_llm, _mock_prompt, tools, prompt_with_schema
    ):
        """Prose content (no JSON) triggers fallback structured LLM re-invoke."""
        node_config = {
            "prompt": "judge",
            "tools": ["search"],
            "max_iterations": 5,
            "state_key": "verdict",
        }
        output_model = get_output_model_for_node(
            node_config,
            prompts_dir=prompt_with_schema / "prompts",
        )

        # Mock LLM returning prose (no JSON) — forces fallback
        mock_llm_base = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = "The FR is well-structured and should be approved."
        mock_llm_bound = MagicMock()
        mock_llm_bound.invoke.return_value = mock_response
        mock_llm_base.bind_tools.return_value = mock_llm_bound

        # Mock the structured output fallback
        mock_structured = MagicMock()
        mock_structured_result = output_model(verdict="APPROVE", reasoning="Good")
        mock_structured.invoke.return_value = mock_structured_result
        mock_llm_base.with_structured_output.return_value = mock_structured
        mock_create_llm.return_value = mock_llm_base

        node_fn = create_agent_node(
            "judge", node_config, tools, output_model=output_model
        )
        result = node_fn({"input": "Evaluate this"})

        assert isinstance(
            result["verdict"], dict
        ), f"Expected dict, got {type(result['verdict'])}: {str(result['verdict'])[:200]}"
        assert result["verdict"]["verdict"] == "APPROVE"

        # Verify fallback was invoked with HumanMessage last (Bug 2 fix)
        fallback_msgs = mock_structured.invoke.call_args[0][0]
        assert (
            fallback_msgs[-1].type == "human"
        ), f"Fallback msgs should end with HumanMessage, got {fallback_msgs[-1].type}"
