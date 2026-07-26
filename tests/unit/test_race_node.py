"""Tests for race node type — FR-232, FR-267, FR-271.

Race nodes fire the same prompt to N provider/model candidates concurrently
and return the first successful result.
"""

import asyncio
import inspect
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# =============================================================================
# Pydantic model for structured output test
# =============================================================================
from pydantic import BaseModel, Field

from yamlgraph.constants import NodeType
from yamlgraph.models import PipelineError
from yamlgraph.models.schemas import ErrorType


class RaceTestOutput(BaseModel):
    """Test output model for structured output race test."""

    answer: str = Field(description="The answer")


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_state():
    """Minimal state for race node tests."""
    return {
        "thread_id": "test-race-001",
        "topic": "unit testing",
        "style": "casual",
        "current_step": "init",
        "error": None,
        "errors": [],
        "messages": [],
        "_loop_counts": {},
    }


def _make_mock_llm(response_text: str, delay: float = 0.0, fail: bool = False):
    """Create a mock LLM that returns a fixed response after optional delay."""
    mock = MagicMock()

    def invoke(messages):
        if delay:
            time.sleep(delay)
        if fail:
            raise RuntimeError(f"LLM failed: {response_text}")
        result = MagicMock()
        result.content = response_text
        return result

    async def ainvoke(messages, config=None):
        if delay:
            await asyncio.sleep(delay)
        if fail:
            raise RuntimeError(f"LLM failed: {response_text}")
        result = MagicMock()
        result.content = response_text
        return result

    mock.invoke = invoke
    mock.ainvoke = ainvoke
    mock.with_structured_output = MagicMock(return_value=mock)
    return mock


# =============================================================================
# NodeType enum
# =============================================================================


class TestRaceNodeType:
    """Race node type constant exists in NodeType enum."""

    @pytest.mark.req("REQ-YG-233")
    def test_race_in_node_type_enum(self):
        """RACE should be a valid NodeType."""
        assert NodeType.RACE == "race"

    @pytest.mark.req("REQ-YG-233")
    def test_race_requires_prompt(self):
        """Race nodes require a prompt field."""
        assert NodeType.requires_prompt("race") is True


# =============================================================================
# Schema validation
# =============================================================================


class TestRaceNodeSchema:
    """NodeConfig validates race node candidates."""

    @pytest.mark.req("REQ-YG-233")
    def test_candidates_minimum_two(self):
        """Race node must have at least 2 candidates."""
        from yamlgraph.models.graph_schema import NodeConfig

        with pytest.raises(Exception, match="at least 2"):
            NodeConfig(
                type="race",
                prompt="test_prompt",
                state_key="result",
                candidates=[{"provider": "anthropic"}],
            )

    @pytest.mark.req("REQ-YG-233")
    def test_candidates_each_has_provider_or_model(self):
        """Each candidate must specify at least provider or model."""
        from yamlgraph.models.graph_schema import NodeConfig

        with pytest.raises(Exception, match="provider.*model"):
            NodeConfig(
                type="race",
                prompt="test_prompt",
                state_key="result",
                candidates=[
                    {"provider": "anthropic"},
                    {},  # missing both provider and model
                ],
            )

    @pytest.mark.req("REQ-YG-233")
    def test_valid_race_node_config(self):
        """Valid race node config passes validation."""
        from yamlgraph.models.graph_schema import NodeConfig

        config = NodeConfig(
            type="race",
            prompt="test_prompt",
            state_key="result",
            candidates=[
                {"provider": "anthropic", "model": "claude-3-5-haiku-20241022"},
                {"provider": "openai", "model": "gpt-4o-mini"},
            ],
        )
        assert config.type == "race"
        assert len(config.candidates) == 2

    @pytest.mark.req("REQ-YG-233")
    def test_race_without_prompt_fails(self):
        """Race node must have a prompt."""
        from yamlgraph.models.graph_schema import NodeConfig

        with pytest.raises(Exception, match="requires 'prompt'"):
            NodeConfig(
                type="race",
                state_key="result",
                candidates=[
                    {"provider": "anthropic"},
                    {"provider": "openai"},
                ],
            )

    @pytest.mark.req("REQ-YG-233")
    def test_race_without_candidates_fails(self):
        """Race node must have candidates field."""
        from yamlgraph.models.graph_schema import NodeConfig

        with pytest.raises(Exception, match="candidates"):
            NodeConfig(
                type="race",
                prompt="test_prompt",
                state_key="result",
            )


# =============================================================================
# State builder
# =============================================================================


class TestRaceStateBuilder:
    """State builder handles race node metadata fields."""

    @pytest.mark.req("REQ-YG-233")
    def test_race_node_adds_race_winner_field(self):
        """Race node type adds _race_winner to state."""
        from yamlgraph.models.state_builder import extract_node_fields

        nodes = {
            "fast_response": {
                "type": "race",
                "state_key": "response",
                "candidates": [
                    {"provider": "anthropic"},
                    {"provider": "openai"},
                ],
            }
        }
        fields = extract_node_fields(nodes)
        assert "_race_winner" in fields
        assert "response" in fields


# =============================================================================
# Race node factory
# =============================================================================


class TestRaceNodeFactory:
    """Core race node execution tests."""

    @pytest.mark.req("REQ-YG-233")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_first_success_wins(self, mock_prepare, mock_create_llm, sample_state):
        """Returns first successful result, not necessarily first to complete."""
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = (
            [MagicMock()],  # messages
            "anthropic",  # resolved_provider
            None,  # resolved_model
        )

        # Fast responder
        fast_llm = _make_mock_llm("fast answer", delay=0.0)
        # Slow responder
        slow_llm = _make_mock_llm("slow answer", delay=0.5)

        mock_create_llm.side_effect = [fast_llm, slow_llm]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "candidates": [
                {"provider": "anthropic", "model": "claude-3-5-haiku-20241022"},
                {"provider": "openai", "model": "gpt-4o-mini"},
            ],
        }
        defaults = {}

        node_fn = create_race_node("fast_response", node_config, defaults)
        result = node_fn(sample_state)

        assert result["response"] == "fast answer"
        assert result["_race_winner"]["provider"] == "anthropic"
        assert result["current_step"] == "fast_response"

    @pytest.mark.req("REQ-YG-233")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_skips_failed_returns_next_success(
        self, mock_prepare, mock_create_llm, sample_state
    ):
        """If first-to-complete fails, takes next successful one."""
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = (
            [MagicMock()],
            "anthropic",
            None,
        )

        # First candidate fails fast
        fail_llm = _make_mock_llm("error", delay=0.0, fail=True)
        # Second candidate succeeds (with slight delay)
        success_llm = _make_mock_llm("good answer", delay=0.1)

        mock_create_llm.side_effect = [fail_llm, success_llm]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "candidates": [
                {"provider": "anthropic"},
                {"provider": "openai"},
            ],
        }

        node_fn = create_race_node("race_node", node_config, {})
        result = node_fn(sample_state)

        assert result["response"] == "good answer"
        assert result["_race_winner"]["provider"] == "openai"

    @pytest.mark.req("REQ-YG-233")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_all_fail_raises(self, mock_prepare, mock_create_llm, sample_state):
        """When all candidates fail, raises AllCandidatesFailedError."""
        from yamlgraph.node_factory.race_node import (
            AllCandidatesFailedError,
            create_race_node,
        )

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)

        fail1 = _make_mock_llm("err1", fail=True)
        fail2 = _make_mock_llm("err2", fail=True)

        mock_create_llm.side_effect = [fail1, fail2]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "candidates": [
                {"provider": "anthropic"},
                {"provider": "openai"},
            ],
        }

        node_fn = create_race_node("race_node", node_config, {})
        with pytest.raises(AllCandidatesFailedError):
            node_fn(sample_state)

    @pytest.mark.req("REQ-YG-233")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_all_fail_on_error_skip(self, mock_prepare, mock_create_llm, sample_state):
        """When all fail and on_error=skip, returns skip state."""
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)

        fail1 = _make_mock_llm("err1", fail=True)
        fail2 = _make_mock_llm("err2", fail=True)

        mock_create_llm.side_effect = [fail1, fail2]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "on_error": "skip",
            "candidates": [
                {"provider": "anthropic"},
                {"provider": "openai"},
            ],
        }

        node_fn = create_race_node("race_node", node_config, {})
        result = node_fn(sample_state)

        assert result["response"] is None
        assert result.get("errors")

    @pytest.mark.req("REQ-YG-233")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_race_winner_metadata(self, mock_prepare, mock_create_llm, sample_state):
        """_race_winner contains provider and model of winning candidate."""
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "openai", None)

        llm1 = _make_mock_llm("answer1", delay=0.2)
        llm2 = _make_mock_llm("answer2", delay=0.0)

        mock_create_llm.side_effect = [llm1, llm2]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "candidates": [
                {"provider": "anthropic", "model": "claude-3-5-haiku-20241022"},
                {"provider": "openai", "model": "gpt-4o-mini"},
            ],
        }

        node_fn = create_race_node("race_node", node_config, {})
        result = node_fn(sample_state)

        winner = result["_race_winner"]
        assert "provider" in winner
        assert "model" in winner
        # The faster one (openai) should win
        assert winner["provider"] == "openai"
        assert winner["model"] == "gpt-4o-mini"

    @pytest.mark.req("REQ-YG-233")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_structured_output_works(self, mock_prepare, mock_create_llm, sample_state):
        """Race node passes output_model to LLM for structured output."""
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)

        mock_result = RaceTestOutput(answer="structured answer")
        llm1 = MagicMock()
        structured_llm = MagicMock()
        structured_llm.invoke = MagicMock(return_value=mock_result)
        structured_llm.ainvoke = AsyncMock(return_value=mock_result)
        llm1.with_structured_output = MagicMock(return_value=structured_llm)

        llm2 = _make_mock_llm("fallback", delay=0.5)

        mock_create_llm.side_effect = [llm1, llm2]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "output_model": "tests.unit.test_race_node.RaceTestOutput",
            "candidates": [
                {"provider": "anthropic"},
                {"provider": "openai"},
            ],
        }

        node_fn = create_race_node("race_node", node_config, {})
        result = node_fn(sample_state)

        assert isinstance(result["response"], RaceTestOutput)
        assert result["response"].answer == "structured answer"

    @pytest.mark.req("REQ-YG-233")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_concurrent_execution(self, mock_prepare, mock_create_llm, sample_state):
        """Candidates run concurrently — total time < sum of individual delays."""
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)

        # Both take 0.2s; if concurrent, total should be ~0.2s, not 0.4s
        llm1 = _make_mock_llm("answer1", delay=0.2)
        llm2 = _make_mock_llm("answer2", delay=0.2)

        mock_create_llm.side_effect = [llm1, llm2]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "candidates": [
                {"provider": "anthropic"},
                {"provider": "openai"},
            ],
        }

        node_fn = create_race_node("race_node", node_config, {})

        start = time.monotonic()
        result = node_fn(sample_state)
        elapsed = time.monotonic() - start

        assert result["response"] is not None
        # If sequential, would be ≥0.4s; concurrent should be ~0.2s
        assert elapsed < 0.35, f"Took {elapsed:.2f}s — not concurrent"


# =============================================================================
# Node compiler integration
# =============================================================================


class TestRaceNodeCompiler:
    """Race node wires into the node compiler registry."""

    @pytest.mark.req("REQ-YG-233")
    def test_race_in_node_type_handlers(self):
        """NODE_TYPE_HANDLERS includes 'race'."""
        from yamlgraph.compile.node_compiler import NODE_TYPE_HANDLERS

        assert "race" in NODE_TYPE_HANDLERS


# =============================================================================
# Content normalization and parse_json — FR-264
# =============================================================================


class TestRaceContentNormalization:
    """Race node normalizes provider-specific content formats (FR-264)."""

    @pytest.mark.req("REQ-YG-264")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_list_content_normalized_to_string(
        self, mock_prepare, mock_create_llm, sample_state
    ):
        """Anthropic-style list content blocks are normalized to string."""
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)

        # Simulate Anthropic response: content is a list of blocks
        mock_llm = MagicMock()
        response = MagicMock()
        response.content = [{"type": "text", "text": "hello from claude"}]
        mock_llm.invoke = MagicMock(return_value=response)
        mock_llm.ainvoke = AsyncMock(return_value=response)

        mock_llm2 = _make_mock_llm("fallback", delay=1.0)
        mock_create_llm.side_effect = [mock_llm, mock_llm2]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "candidates": [
                {"provider": "anthropic"},
                {"provider": "openai"},
            ],
        }

        node_fn = create_race_node("race_node", node_config, {})
        result = node_fn(sample_state)

        assert result["response"] == "hello from claude"
        assert isinstance(result["response"], str)

    @pytest.mark.req("REQ-YG-264")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_string_content_unchanged(
        self, mock_prepare, mock_create_llm, sample_state
    ):
        """String content passes through normalization unchanged."""
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "openai", None)

        llm1 = _make_mock_llm("plain string answer")
        llm2 = _make_mock_llm("fallback", delay=1.0)
        mock_create_llm.side_effect = [llm1, llm2]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "candidates": [
                {"provider": "openai"},
                {"provider": "anthropic"},
            ],
        }

        node_fn = create_race_node("race_node", node_config, {})
        result = node_fn(sample_state)

        assert result["response"] == "plain string answer"
        assert isinstance(result["response"], str)


class TestRaceParseJson:
    """Race node supports parse_json: true for JSON extraction (FR-264)."""

    @pytest.mark.req("REQ-YG-264")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_parse_json_extracts_json_object(
        self, mock_prepare, mock_create_llm, sample_state
    ):
        """parse_json: true extracts JSON from LLM response."""
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "openai", None)

        llm1 = _make_mock_llm('{"key": "value", "count": 42}')
        llm2 = _make_mock_llm("fallback", delay=1.0)
        mock_create_llm.side_effect = [llm1, llm2]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "parse_json": True,
            "candidates": [
                {"provider": "openai"},
                {"provider": "anthropic"},
            ],
        }

        node_fn = create_race_node("race_node", node_config, {})
        result = node_fn(sample_state)

        assert isinstance(result["response"], dict)
        assert result["response"]["key"] == "value"
        assert result["response"]["count"] == 42

    @pytest.mark.req("REQ-YG-264")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_parse_json_with_markdown_code_block(
        self, mock_prepare, mock_create_llm, sample_state
    ):
        """parse_json extracts JSON from markdown code blocks."""
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "openai", None)

        llm1 = _make_mock_llm('```json\n{"result": "extracted"}\n```')
        llm2 = _make_mock_llm("fallback", delay=1.0)
        mock_create_llm.side_effect = [llm1, llm2]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "parse_json": True,
            "candidates": [
                {"provider": "openai"},
                {"provider": "anthropic"},
            ],
        }

        node_fn = create_race_node("race_node", node_config, {})
        result = node_fn(sample_state)

        assert isinstance(result["response"], dict)
        assert result["response"]["result"] == "extracted"

    @pytest.mark.req("REQ-YG-264")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_parse_json_with_anthropic_list_content(
        self, mock_prepare, mock_create_llm, sample_state
    ):
        """parse_json works with Anthropic list content containing JSON."""
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)

        # Anthropic returns JSON wrapped in content blocks
        mock_llm = MagicMock()
        response = MagicMock()
        response.content = [{"type": "text", "text": '{"answer": "from claude"}'}]
        mock_llm.invoke = MagicMock(return_value=response)
        mock_llm.ainvoke = AsyncMock(return_value=response)

        llm2 = _make_mock_llm("fallback", delay=1.0)
        mock_create_llm.side_effect = [mock_llm, llm2]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "parse_json": True,
            "candidates": [
                {"provider": "anthropic"},
                {"provider": "openai"},
            ],
        }

        node_fn = create_race_node("race_node", node_config, {})
        result = node_fn(sample_state)

        assert isinstance(result["response"], dict)
        assert result["response"]["answer"] == "from claude"

    @pytest.mark.req("REQ-YG-264")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_parse_json_disabled_by_default(
        self, mock_prepare, mock_create_llm, sample_state
    ):
        """Without parse_json, JSON string comes back as-is."""
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "openai", None)

        llm1 = _make_mock_llm('{"key": "value"}')
        llm2 = _make_mock_llm("fallback", delay=1.0)
        mock_create_llm.side_effect = [llm1, llm2]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "candidates": [
                {"provider": "openai"},
                {"provider": "anthropic"},
            ],
        }

        node_fn = create_race_node("race_node", node_config, {})
        result = node_fn(sample_state)

        # Without parse_json, result should be a string
        assert isinstance(result["response"], str)
        assert result["response"] == '{"key": "value"}'

    @pytest.mark.req("REQ-YG-264")
    @patch("yamlgraph.node_factory.race_node.get_output_model_for_node")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_parse_json_skips_output_model_resolution(
        self, mock_prepare, mock_create_llm, mock_get_output, sample_state
    ):
        """parse_json: true skips output_model resolution at factory time."""
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "openai", None)
        llm1 = _make_mock_llm('{"key": "value"}')
        llm2 = _make_mock_llm("fallback", delay=1.0)
        mock_create_llm.side_effect = [llm1, llm2]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "parse_json": True,
            "candidates": [
                {"provider": "openai"},
                {"provider": "anthropic"},
            ],
        }

        node_fn = create_race_node("race_node", node_config, {})
        result = node_fn(sample_state)

        # get_output_model_for_node should NOT have been called
        mock_get_output.assert_not_called()
        assert isinstance(result["response"], dict)


class TestNormalizeContentShared:
    """Shared normalize_content utility lives in yamlgraph.utils.content."""

    @pytest.mark.req("REQ-YG-264")
    def test_normalize_string_passthrough(self):
        """String content passes through unchanged."""
        from yamlgraph.utils.content import normalize_content

        assert normalize_content("hello") == "hello"

    @pytest.mark.req("REQ-YG-264")
    def test_normalize_list_of_text_blocks(self):
        """Anthropic-style list of text blocks normalized to string."""
        from yamlgraph.utils.content import normalize_content

        content = [
            {"type": "text", "text": "hello "},
            {"type": "text", "text": "world"},
        ]
        assert normalize_content(content) == "hello world"

    @pytest.mark.req("REQ-YG-264")
    def test_normalize_none_returns_empty_string(self):
        """None content returns empty string."""
        from yamlgraph.utils.content import normalize_content

        assert normalize_content(None) == ""

    @pytest.mark.req("REQ-YG-264")
    def test_normalize_other_type_stringified(self):
        """Non-str, non-list content is stringified."""
        from yamlgraph.utils.content import normalize_content

        assert normalize_content(42) == "42"


# =============================================================================
# FR-267: Race node timeout — no double ThreadPoolExecutor wrap
# =============================================================================


class TestRaceTimeoutNoDoubleWrap:
    """FR-267: _compile_race_node must NOT apply _maybe_wrap_timeout.

    Race nodes own timeout natively via as_completed(timeout=...).
    Wrapping with _maybe_wrap_timeout creates nested ThreadPoolExecutors
    that silently drop the return value.
    """

    @pytest.mark.req("REQ-YG-266")
    @patch("yamlgraph.compile.node_compiler._maybe_wrap_otel")
    @patch("yamlgraph.compile.node_compiler._maybe_wrap_timeout")
    @patch("yamlgraph.compile.node_compiler.create_race_node")
    def test_compile_race_node_does_not_wrap_timeout(
        self, mock_create_race, mock_wrap_timeout, mock_wrap_otel
    ):
        """_compile_race_node must NOT call _maybe_wrap_timeout."""
        from yamlgraph.compile.node_compiler import _compile_race_node

        mock_node_fn = MagicMock()
        mock_create_race.return_value = mock_node_fn
        mock_wrap_otel.side_effect = lambda fn, name, node_type: fn

        ctx = MagicMock()
        ctx.node_name = "race_test"
        ctx.node_config = {
            "type": "race",
            "prompt": "test",
            "timeout": 10,
            "candidates": [
                {"provider": "anthropic"},
                {"provider": "openai"},
            ],
        }
        ctx.effective_defaults = {}
        ctx.config.source_path = None
        ctx.cache_policy = None

        _compile_race_node(ctx)

        mock_wrap_timeout.assert_not_called()
        ctx.graph.add_node.assert_called_once_with(
            "race_test", mock_node_fn, cache_policy=None
        )


class TestRaceTimeoutCorrectness:
    """FR-267: Race node with timeout returns correct state."""

    @pytest.mark.req("REQ-YG-266")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_race_with_timeout_returns_full_state(
        self, mock_prepare, mock_create_llm, sample_state
    ):
        """Race with timeout: candidate succeeds → full state dict returned.

        All of state_key, _race_winner, current_step, _loop_counts must
        be present and non-None. This is the condemning test for the
        double-wrap bug: with _maybe_wrap_timeout, the return value is lost.
        """
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)

        fast_llm = _make_mock_llm("fast answer", delay=0.0)
        slow_llm = _make_mock_llm("slow answer", delay=0.3)
        mock_create_llm.side_effect = [fast_llm, slow_llm]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "timeout": 5,
            "candidates": [
                {"provider": "anthropic", "model": "claude-3-5-haiku-20241022"},
                {"provider": "openai", "model": "gpt-4o-mini"},
            ],
        }

        node_fn = create_race_node("fast_response", node_config, {})
        result = node_fn(sample_state)

        assert result["response"] == "fast answer"
        assert result["_race_winner"] is not None
        assert result["_race_winner"]["provider"] == "anthropic"
        assert result["current_step"] == "fast_response"
        assert result["_loop_counts"] is not None
        assert result["_loop_counts"]["fast_response"] == 1

    @pytest.mark.req("REQ-YG-266")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_race_with_timeout_parse_json(
        self, mock_prepare, mock_create_llm, sample_state
    ):
        """Race with timeout + parse_json: true returns parsed dict in state."""
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "openai", None)

        llm1 = _make_mock_llm('{"key": "value", "count": 42}')
        llm2 = _make_mock_llm("fallback", delay=1.0)
        mock_create_llm.side_effect = [llm1, llm2]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "timeout": 5,
            "parse_json": True,
            "candidates": [
                {"provider": "openai"},
                {"provider": "anthropic"},
            ],
        }

        node_fn = create_race_node("race_json", node_config, {})
        result = node_fn(sample_state)

        assert isinstance(result["response"], dict)
        assert result["response"]["key"] == "value"
        assert result["_race_winner"] is not None
        assert result["current_step"] == "race_json"

    @pytest.mark.req("REQ-YG-266")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_race_timeout_expiry_on_error_skip(
        self, mock_prepare, mock_create_llm, sample_state
    ):
        """All candidates exceed deadline + on_error:skip → PipelineError(TIMEOUT_ERROR)."""
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)

        # Both candidates take longer than the timeout
        llm1 = _make_mock_llm("slow1", delay=5.0)
        llm2 = _make_mock_llm("slow2", delay=5.0)
        mock_create_llm.side_effect = [llm1, llm2]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "timeout": 0.1,
            "on_error": "skip",
            "candidates": [
                {"provider": "anthropic"},
                {"provider": "openai"},
            ],
        }

        node_fn = create_race_node("race_timeout", node_config, {})
        result = node_fn(sample_state)

        assert result["response"] is None
        assert result["current_step"] == "race_timeout"
        assert result["_loop_counts"]["race_timeout"] == 1
        errors = result["errors"]
        assert len(errors) == 1
        assert isinstance(errors[0], PipelineError)
        assert errors[0].type == ErrorType.TIMEOUT_ERROR
        assert "timed out" in errors[0].message.lower()

    @pytest.mark.req("REQ-YG-266")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_race_timeout_expiry_raises_without_on_error(
        self, mock_prepare, mock_create_llm, sample_state
    ):
        """All candidates exceed deadline + no on_error → raises exception."""
        from yamlgraph.node_factory.race_node import (
            AllCandidatesFailedError,
            create_race_node,
        )

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)

        llm1 = _make_mock_llm("slow1", delay=5.0)
        llm2 = _make_mock_llm("slow2", delay=5.0)
        mock_create_llm.side_effect = [llm1, llm2]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "timeout": 0.1,
            "candidates": [
                {"provider": "anthropic"},
                {"provider": "openai"},
            ],
        }

        node_fn = create_race_node("race_timeout", node_config, {})
        with pytest.raises(AllCandidatesFailedError, match="timed out"):
            node_fn(sample_state)

    @pytest.mark.req("REQ-YG-266")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_race_without_timeout_still_works(
        self, mock_prepare, mock_create_llm, sample_state
    ):
        """Regression: race node without explicit timeout continues to work."""
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)

        llm1 = _make_mock_llm("answer from anthropic")
        llm2 = _make_mock_llm("answer from openai", delay=0.1)
        mock_create_llm.side_effect = [llm1, llm2]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            # No timeout field
            "candidates": [
                {"provider": "anthropic"},
                {"provider": "openai"},
            ],
        }

        node_fn = create_race_node("race_node", node_config, {})
        result = node_fn(sample_state)

        assert result["response"] == "answer from anthropic"
        assert result["_race_winner"]["provider"] == "anthropic"
        assert result["current_step"] == "race_node"


# =============================================================================
# FR-270: Race node must not block on slow losers (REQ-YG-269)
# =============================================================================


@pytest.mark.req("REQ-YG-269")
def test_race_returns_on_first_success_not_after_slowest(monkeypatch):
    """Race must not block on slow losers; returns within fast_candidate_time + ε."""
    from yamlgraph.node_factory.race_node import create_race_node

    fast_llm = _make_mock_llm('{"ok": true}', delay=0.05)
    slow_llm = _make_mock_llm('{"ok": false}', delay=2.0)

    node_config = {
        "type": "race",
        "state_key": "result",
        "parse_json": True,
        "candidates": [
            {"provider": "fake-fast", "model": "x"},
            {"provider": "fake-slow", "model": "y"},
        ],
    }

    def fake_create_llm(*args, **kwargs):
        return fast_llm if kwargs.get("provider") == "fake-fast" else slow_llm

    with (
        patch(
            "yamlgraph.node_factory.race_node.create_llm", side_effect=fake_create_llm
        ),
        patch("yamlgraph.node_factory.race_node.prepare_messages") as mock_prepare,
    ):
        mock_prepare.return_value = ([MagicMock()], "fake-fast", "x")
        node_fn = create_race_node("test_race", node_config, {}, graph_path=None)

        t0 = time.monotonic()
        result = node_fn({"_loop_counts": {}})
        elapsed = time.monotonic() - t0

    assert elapsed < 1.0, f"race waited for slow loser: {elapsed:.1f}s"
    assert result["result"] == {"ok": True}
    assert result["_race_winner"]["provider"] == "fake-fast"


# =============================================================================
# FR-271: Async race node with cancellable candidates (REQ-YG-270)
# =============================================================================


class TestAsyncRaceCancellable:
    """FR-271: Race node uses asyncio.wait with cancellable async candidates."""

    @pytest.mark.req("REQ-YG-270")
    def test_no_thread_pool_executor_in_race_node(self):
        """ThreadPoolExecutor must not be present in race_node.py after FR-271."""
        import yamlgraph.node_factory.race_node as module

        source = inspect.getsource(module)
        assert (
            "ThreadPoolExecutor" not in source
        ), "ThreadPoolExecutor must be removed from race_node.py (FR-271)"

    @pytest.mark.req("REQ-YG-270")
    @pytest.mark.slow
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_loser_task_cancelled_after_winner(
        self, mock_prepare, mock_create_llm, sample_state
    ):
        """Condemning test: fast async (50 ms) + slow async (30 s); slow must be cancelled."""
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "fast-provider", "fast-model")

        cancelled_flag = {"value": False}

        async def slow_ainvoke(messages, config=None):
            try:
                await asyncio.sleep(30.0)
                result = MagicMock()
                result.content = "slow answer"
                return result
            except asyncio.CancelledError:
                cancelled_flag["value"] = True
                raise

        fast_llm = _make_mock_llm("fast answer", delay=0.05)

        slow_llm = MagicMock()
        slow_llm.ainvoke = slow_ainvoke
        slow_llm.with_structured_output = MagicMock(return_value=slow_llm)

        mock_create_llm.side_effect = [fast_llm, slow_llm]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "candidates": [
                {"provider": "fast-provider", "model": "fast-model"},
                {"provider": "slow-provider", "model": "slow-model"},
            ],
        }

        t0 = time.monotonic()
        result = create_race_node("race_async", node_config, {})(sample_state)
        elapsed = time.monotonic() - t0

        assert (
            result["response"] == "fast answer"
        ), f"Expected 'fast answer', got {result['response']!r}"
        assert elapsed < 1.0, f"node_fn took {elapsed:.2f}s — should be < 1s"
        assert (
            cancelled_flag["value"] is True
        ), "Slow task must be cancelled (CancelledError propagated in finally)"

    @pytest.mark.req("REQ-YG-270")
    def test_run_coro_sync_safe_exists(self):
        """_run_coro_sync_safe bridge function must exist in race_node module."""
        import yamlgraph.node_factory.race_node as rn_module

        assert hasattr(
            rn_module, "_run_coro_sync_safe"
        ), "_run_coro_sync_safe not found — asyncio bridge not implemented (FR-271)"
        assert callable(rn_module._run_coro_sync_safe)

    @pytest.mark.req("REQ-YG-270")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_all_candidates_fail_async_on_error_skip(
        self, mock_prepare, mock_create_llm, sample_state
    ):
        """All async candidates fail + on_error:skip → {state_key: None, errors: [...]}."""
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "p1", None)

        fail1 = _make_mock_llm("err1", fail=True)
        fail2 = _make_mock_llm("err2", fail=True)
        mock_create_llm.side_effect = [fail1, fail2]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "on_error": "skip",
            "candidates": [
                {"provider": "p1"},
                {"provider": "p2"},
            ],
        }

        result = create_race_node("race_async_fail", node_config, {})(sample_state)

        assert result["response"] is None
        assert result.get("errors"), "errors list must be populated"

    @pytest.mark.req("REQ-YG-270")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_all_candidates_fail_async_raises(
        self, mock_prepare, mock_create_llm, sample_state
    ):
        """All async candidates fail without on_error → raises AllCandidatesFailedError."""
        from yamlgraph.node_factory.race_node import (
            AllCandidatesFailedError,
            create_race_node,
        )

        mock_prepare.return_value = ([MagicMock()], "p1", None)

        fail1 = _make_mock_llm("err1", fail=True)
        fail2 = _make_mock_llm("err2", fail=True)
        mock_create_llm.side_effect = [fail1, fail2]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "candidates": [
                {"provider": "p1"},
                {"provider": "p2"},
            ],
        }

        with pytest.raises(AllCandidatesFailedError):
            create_race_node("race_async_fail", node_config, {})(sample_state)

    @pytest.mark.req("REQ-YG-270")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_timeout_async_on_error_skip(
        self, mock_prepare, mock_create_llm, sample_state
    ):
        """Timeout fires when no async candidate completes; on_error:skip → TIMEOUT_ERROR."""
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "p1", None)

        slow1 = _make_mock_llm("slow1", delay=10.0)
        slow2 = _make_mock_llm("slow2", delay=10.0)
        mock_create_llm.side_effect = [slow1, slow2]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "timeout": 0.1,
            "on_error": "skip",
            "candidates": [
                {"provider": "p1"},
                {"provider": "p2"},
            ],
        }

        result = create_race_node("race_timeout_async", node_config, {})(sample_state)

        assert result["response"] is None
        assert result["current_step"] == "race_timeout_async"
        errors = result["errors"]
        assert len(errors) == 1
        assert isinstance(errors[0], PipelineError)
        assert errors[0].type == ErrorType.TIMEOUT_ERROR
        assert "timed out" in errors[0].message.lower()

    @pytest.mark.req("REQ-YG-270")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_async_race_winner_metadata(
        self, mock_prepare, mock_create_llm, sample_state
    ):
        """_race_winner metadata preserved in async path."""
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "p1", None)

        fast = _make_mock_llm("fast answer", delay=0.0)
        slow = _make_mock_llm("slow answer", delay=0.5)
        mock_create_llm.side_effect = [fast, slow]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "candidates": [
                {"provider": "fast-p", "model": "fast-m"},
                {"provider": "slow-p", "model": "slow-m"},
            ],
        }

        result = create_race_node("race_async_meta", node_config, {})(sample_state)

        assert result["response"] == "fast answer"
        assert result["_race_winner"]["provider"] == "fast-p"
        assert result["_race_winner"]["model"] == "fast-m"
        assert result["current_step"] == "race_async_meta"


class TestRaceStructuredOutputFallback:
    """FR-464: Race node falls back to JSON extraction when structured output rejected."""

    @pytest.mark.req("REQ-YG-465")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_fallback_on_response_format_rejection(
        self, mock_prepare, mock_create_llm, sample_state
    ):
        """Race candidate falls back to extract_json when with_structured_output fails."""
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "deepseek", None)

        # LLM that rejects structured output but returns JSON in plain response
        llm1 = MagicMock()
        structured_llm = MagicMock()
        structured_llm.ainvoke = AsyncMock(
            side_effect=Exception(
                "Error code: 400 - {'error': {'message': 'This response_format type is unavailable now'}}"
            )
        )
        llm1.with_structured_output = MagicMock(return_value=structured_llm)
        # Plain ainvoke returns JSON text
        plain_response = MagicMock()
        plain_response.content = '{"answer": "fallback result"}'
        llm1.ainvoke = AsyncMock(return_value=plain_response)

        mock_create_llm.side_effect = [llm1]

        node_config = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "output_model": "tests.unit.test_race_node.RaceTestOutput",
            "candidates": [
                {"provider": "deepseek"},
            ],
        }

        node_fn = create_race_node("race_node", node_config, {})
        result = node_fn(sample_state)

        assert isinstance(result["response"], RaceTestOutput)
        assert result["response"].answer == "fallback result"


# =============================================================================
# FR-705: Race timeout error must enumerate pending candidates (REQ-YG-266)
# =============================================================================


class TestRaceTimeoutCandidateFidelity:
    """FR-705: the NC-361 incident — timeout reported 'All 1 … ?/?' while
    two named providers were pending. The error must enumerate every
    candidate with its identity."""

    CANDIDATES = [
        {"provider": "google", "model": "gemini-2.0-flash"},
        {"provider": "azure", "model": "gpt-4o"},
    ]

    def _config(self, **overrides):
        cfg = {
            "type": "race",
            "prompt": "test_prompt",
            "state_key": "response",
            "timeout": 0.1,
            "candidates": [dict(c) for c in self.CANDIDATES],
        }
        cfg.update(overrides)
        return cfg

    @pytest.mark.req("REQ-YG-266")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_timeout_enumerates_all_pending_candidates(
        self, mock_prepare, mock_create_llm, sample_state
    ):
        """Both candidates pending at deadline → both named, count correct."""
        from yamlgraph.node_factory.race_node import (
            AllCandidatesFailedError,
            create_race_node,
        )

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)
        mock_create_llm.side_effect = [
            _make_mock_llm("slow", delay=10.0),
            _make_mock_llm("slow", delay=10.0),
        ]

        node_fn = create_race_node("race_timeout", self._config(), {})
        with pytest.raises(AllCandidatesFailedError) as excinfo:
            node_fn(sample_state)

        msg = str(excinfo.value)
        assert "All 2 race candidates failed" in msg, msg
        assert "google/gemini-2.0-flash" in msg, msg
        assert "azure/gpt-4o" in msg, msg
        assert "timed out" in msg  # F4: substring existing tests match
        assert "?/?" not in msg, f"anonymous candidate leaked: {msg}"
        # F2/programmatic consumers: candidate dicts preserved, never {}
        assert all(c for c, _ in excinfo.value.errors)

    @pytest.mark.req("REQ-YG-266")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_timeout_mixed_fast_failure_and_pending(
        self, mock_prepare, mock_create_llm, sample_state
    ):
        """One real failure + one pending at deadline → each with its own error."""
        from yamlgraph.node_factory.race_node import (
            AllCandidatesFailedError,
            create_race_node,
        )

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)
        mock_create_llm.side_effect = [
            _make_mock_llm("boom", fail=True),
            _make_mock_llm("slow", delay=10.0),
        ]

        node_fn = create_race_node("race_mixed", self._config(), {})
        with pytest.raises(AllCandidatesFailedError) as excinfo:
            node_fn(sample_state)

        errors = excinfo.value.errors
        assert len(errors) == 2
        by_provider = {c.get("provider"): e for c, e in errors}
        assert isinstance(by_provider["google"], RuntimeError)  # real exception
        assert isinstance(by_provider["azure"], TimeoutError)  # pending at deadline

    @pytest.mark.req("REQ-YG-266")
    @patch("yamlgraph.node_factory.race_node.create_llm")
    @patch("yamlgraph.node_factory.race_node.prepare_messages")
    def test_timeout_mixed_skip_tags_timeout_error(
        self, mock_prepare, mock_create_llm, sample_state
    ):
        """F2: skip + any pending TimeoutError → PipelineError type TIMEOUT_ERROR."""
        from yamlgraph.node_factory.race_node import create_race_node

        mock_prepare.return_value = ([MagicMock()], "anthropic", None)
        mock_create_llm.side_effect = [
            _make_mock_llm("boom", fail=True),
            _make_mock_llm("slow", delay=10.0),
        ]

        node_fn = create_race_node("race_skip", self._config(on_error="skip"), {})
        result = node_fn(sample_state)

        assert result["response"] is None
        assert result["errors"][0].type == ErrorType.TIMEOUT_ERROR
