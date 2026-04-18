"""Tests for race node type — FR-232.

Race nodes fire the same prompt to N provider/model candidates concurrently
and return the first successful result.
"""

import time
from unittest.mock import MagicMock, patch

import pytest

# =============================================================================
# Pydantic model for structured output test
# =============================================================================
from pydantic import BaseModel, Field

from yamlgraph.constants import NodeType


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

    mock.invoke = invoke
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
        from yamlgraph.node_compiler import NODE_TYPE_HANDLERS

        assert "race" in NODE_TYPE_HANDLERS
