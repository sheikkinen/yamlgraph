"""
Unit tests for FR-071: Graph-Level Thinking Budget (REQ-YG-083)
"""

import os
from unittest.mock import patch

import pytest
from langchain_anthropic import ChatAnthropic
from pydantic import ValidationError

from yamlgraph.models.graph_schema import GraphConfigSchema, NodeConfig
from yamlgraph.utils.llm_factory import clear_cache, create_llm


@pytest.mark.req("REQ-YG-083")
class TestThinkingBudgetValidation:
    """Test thinking_budget field validation in schema models."""

    def test_thinking_budget_none_allowed(self):
        """thinking_budget=None (not set) is valid."""
        config = GraphConfigSchema(
            nodes={"test": NodeConfig(prompt="test", state_key="test")},
            edges=[],
        )
        assert config.defaults.get("thinking_budget") is None

    def test_thinking_budget_zero_allowed(self):
        """thinking_budget=0 (explicit disable) is valid."""
        config = GraphConfigSchema(
            defaults={"thinking_budget": 0},
            nodes={"test": NodeConfig(prompt="test", state_key="test")},
            edges=[],
        )
        assert config.defaults["thinking_budget"] == 0

    def test_thinking_budget_1024_allowed(self):
        """thinking_budget=1024 (minimum valid) is valid."""
        config = GraphConfigSchema(
            defaults={"thinking_budget": 1024},
            nodes={"test": NodeConfig(prompt="test", state_key="test")},
            edges=[],
        )
        assert config.defaults["thinking_budget"] == 1024

    def test_thinking_budget_above_1024_allowed(self):
        """thinking_budget > 1024 is valid."""
        config = GraphConfigSchema(
            defaults={"thinking_budget": 8000},
            nodes={"test": NodeConfig(prompt="test", state_key="test")},
            edges=[],
        )
        assert config.defaults["thinking_budget"] == 8000

    def test_thinking_budget_below_1024_raises(self):
        """thinking_budget in range 1-1023 raises ValueError."""
        with pytest.raises(ValidationError, match="thinking_budget"):
            GraphConfigSchema(
                defaults={"thinking_budget": 1023},
                nodes={"test": NodeConfig(prompt="test", state_key="test")},
                edges=[],
            )

    def test_thinking_budget_negative_raises(self):
        """Negative thinking_budget raises ValueError."""
        with pytest.raises(ValidationError, match="thinking_budget"):
            GraphConfigSchema(
                defaults={"thinking_budget": -1},
                nodes={"test": NodeConfig(prompt="test", state_key="test")},
                edges=[],
            )

    def test_node_thinking_budget_override(self):
        """Node-level thinking_budget overrides graph default."""
        config = GraphConfigSchema(
            defaults={"thinking_budget": 8000},
            nodes={
                "plan": NodeConfig(
                    prompt="plan", state_key="plan", thinking_budget=4096
                ),
                "summarize": NodeConfig(
                    prompt="summarize", state_key="summary", thinking_budget=0
                ),
            },
            edges=[],
        )
        assert config.defaults["thinking_budget"] == 8000
        assert config.nodes["plan"].thinking_budget == 4096
        assert config.nodes["summarize"].thinking_budget == 0


@pytest.mark.req("REQ-YG-083")
class TestCreateLLMThinking:
    """Test create_llm thinking parameter and temperature override."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cache()

    def test_thinking_budget_none_no_thinking(self):
        """thinking_budget=None does not enable thinking."""
        llm = create_llm(provider="anthropic", thinking_budget=None)
        assert isinstance(llm, ChatAnthropic)
        # Check that thinking was not enabled (will check internals after implementation)

    def test_thinking_budget_zero_no_thinking(self):
        """thinking_budget=0 does not enable thinking."""
        llm = create_llm(provider="anthropic", thinking_budget=0)
        assert isinstance(llm, ChatAnthropic)

    def test_thinking_budget_enabled_anthropic(self):
        """thinking_budget >= 1024 with anthropic enables thinking."""
        llm = create_llm(provider="anthropic", thinking_budget=8000)
        assert isinstance(llm, ChatAnthropic)
        # After implementation, check llm.thinking is set correctly

    def test_thinking_budget_forces_temperature_one(self):
        """thinking_budget >= 1024 forces temperature=1."""
        llm = create_llm(provider="anthropic", thinking_budget=8000, temperature=0.7)
        assert isinstance(llm, ChatAnthropic)
        assert llm.temperature == 1

    def test_thinking_budget_non_anthropic_raises(self):
        """thinking_budget >= 1024 with non-Anthropic provider raises."""
        with (
            patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}),
            pytest.raises(ValueError, match="(?i)thinking_budget.*anthropic"),
        ):
            create_llm(provider="openai", thinking_budget=8000)

    def test_thinking_budget_in_cache_key(self):
        """thinking_budget is included in LLM cache key."""
        llm1 = create_llm(provider="anthropic", thinking_budget=8000)
        llm2 = create_llm(provider="anthropic", thinking_budget=8000)
        llm3 = create_llm(provider="anthropic", thinking_budget=4096)
        llm4 = create_llm(provider="anthropic", thinking_budget=None)

        # llm1 and llm2 should be the same cached instance
        assert llm1 is llm2
        # llm3 has different budget, should be different instance
        assert llm1 is not llm3
        # llm4 has no thinking, should be different instance
        assert llm1 is not llm4

    def test_temperature_override_before_cache_key(self):
        """Temperature override happens before cache key computation."""
        # First call with temperature=0.5 and thinking_budget=8000
        llm1 = create_llm(provider="anthropic", thinking_budget=8000, temperature=0.5)
        # Second call with temperature=1 and thinking_budget=8000
        llm2 = create_llm(provider="anthropic", thinking_budget=8000, temperature=1)

        # Both should return the same cached instance because both use temperature=1
        # after override
        assert llm1 is llm2


@pytest.mark.req("REQ-YG-083")
class TestThinkingBudgetLinter:
    """Test linter warnings for thinking_budget configuration."""

    def test_linter_warns_non_anthropic_provider(self, tmp_path):
        """Linter warns when thinking_budget > 0 with non-Anthropic provider."""
        graph_file = tmp_path / "graph.yaml"
        graph_file.write_text("""
defaults:
  provider: openai
  thinking_budget: 8000
nodes:
  test:
    prompt: test
    state_key: test
edges:
  - from: START
    to: test
  - from: test
    to: END
""")
        from yamlgraph.linter import lint_graph

        result = lint_graph(graph_file)
        warnings = [i for i in result.issues if i.code == "W071-2"]
        assert len(warnings) == 1
        assert "anthropic" in warnings[0].message.lower()

    def test_linter_warns_old_model(self, tmp_path):
        """Linter warns when thinking_budget > 0 with pre-3.7 model."""
        graph_file = tmp_path / "graph.yaml"
        graph_file.write_text("""
defaults:
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  thinking_budget: 8000
nodes:
  test:
    prompt: test
    state_key: test
edges:
  - from: START
    to: test
  - from: test
    to: END
""")
        from yamlgraph.linter import lint_graph

        result = lint_graph(graph_file)
        warnings = [i for i in result.issues if i.code == "W071-3"]
        assert len(warnings) == 1
        assert "3.7" in warnings[0].message

    def test_linter_warns_below_minimum(self, tmp_path):
        """Linter warns when 0 < thinking_budget < 1024."""
        graph_file = tmp_path / "graph.yaml"
        graph_file.write_text("""
defaults:
  provider: anthropic
  thinking_budget: 500
nodes:
  test:
    prompt: test
    state_key: test
edges:
  - from: START
    to: test
  - from: test
    to: END
""")
        from yamlgraph.linter import lint_graph

        result = lint_graph(graph_file)
        warnings = [i for i in result.issues if i.code == "W071-4"]
        assert len(warnings) == 1
        assert "1024" in warnings[0].message

    def test_linter_warns_temperature_conflict(self, tmp_path):
        """Linter warns when explicit temperature != 1 with thinking_budget > 0."""
        graph_file = tmp_path / "graph.yaml"
        graph_file.write_text("""
defaults:
  provider: anthropic
  temperature: 0.7
  thinking_budget: 8000
nodes:
  test:
    prompt: test
    state_key: test
edges:
  - from: START
    to: test
  - from: test
    to: END
""")
        from yamlgraph.linter import lint_graph

        result = lint_graph(graph_file)
        warnings = [i for i in result.issues if i.code == "W071-1"]
        assert len(warnings) == 1
        assert "temperature" in warnings[0].message.lower()
