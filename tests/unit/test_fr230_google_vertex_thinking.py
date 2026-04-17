"""
Unit tests for FR-230: Google/Vertex Thinking Budget Support (REQ-YG-230)

Covers:
- Schema validator accepts -1 (Google auto mode) and rejects -2
- create_llm does not raise for google/vertex with thinking_budget >= 1024
- create_llm still raises for mistral/openai with thinking_budget >= 1024
- ChatGoogleGenerativeAI receives thinking_budget kwarg for google/vertex
- Temperature is NOT overridden for google/vertex (Anthropic-only constraint)
- Linter W071-1 does not fire for google/vertex
- Linter W071-2 does not fire for google/vertex
- Linter W071-4 does not fire for google/vertex
- Linter W071-3 does not fire for gemini-2.5-flash with thinking_budget > 0
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from yamlgraph.models.graph_schema import GraphConfigSchema, NodeConfig
from yamlgraph.utils.llm_factory import clear_cache, create_llm


@pytest.mark.req("REQ-YG-230")
class TestSchemaValidatorFR230:
    """Schema validator accepts Google-specific values."""

    def test_thinking_budget_minus_one_allowed_in_node(self):
        """-1 is accepted as Google automatic mode in NodeConfig."""
        node = NodeConfig(prompt="test", state_key="test", thinking_budget=-1)
        assert node.thinking_budget == -1

    def test_thinking_budget_minus_two_rejected_in_node(self):
        """-2 is rejected as invalid."""
        with pytest.raises(ValidationError, match="thinking_budget"):
            NodeConfig(prompt="test", state_key="test", thinking_budget=-2)

    def test_thinking_budget_minus_one_allowed_in_defaults(self):
        """-1 is accepted in graph defaults."""
        config = GraphConfigSchema(
            defaults={"thinking_budget": -1},
            nodes={"test": NodeConfig(prompt="test", state_key="test")},
            edges=[],
        )
        assert config.defaults["thinking_budget"] == -1

    def test_thinking_budget_minus_two_rejected_in_defaults(self):
        """-2 is rejected in graph defaults."""
        with pytest.raises(ValidationError, match="thinking_budget"):
            GraphConfigSchema(
                defaults={"thinking_budget": -2},
                nodes={"test": NodeConfig(prompt="test", state_key="test")},
                edges=[],
            )


@pytest.mark.req("REQ-YG-230")
class TestCreateLLMThinkingFR230:
    """create_llm passes thinking_budget to google/vertex without raising."""

    def setup_method(self):
        clear_cache()

    def test_google_thinking_budget_does_not_raise(self):
        """create_llm(provider='google', thinking_budget=8000) does not raise."""
        mock_llm = MagicMock()
        with patch(
            "yamlgraph.utils.llm_factory._create_google_llm", return_value=mock_llm
        ) as mock_create:
            result = create_llm(provider="google", thinking_budget=8000)
            assert result is mock_llm
            mock_create.assert_called_once()
            _, kwargs = mock_create.call_args[0], mock_create.call_args[1]
            # thinking_budget passed positionally or as kwarg
            args = mock_create.call_args[0]
            assert 8000 in args or kwargs.get("thinking_budget") == 8000

    def test_vertex_thinking_budget_does_not_raise(self):
        """create_llm(provider='vertex', thinking_budget=8000) does not raise."""
        mock_llm = MagicMock()
        with patch(
            "yamlgraph.utils.llm_factory._create_vertex_llm", return_value=mock_llm
        ) as mock_create:
            result = create_llm(provider="vertex", thinking_budget=8000)
            assert result is mock_llm
            mock_create.assert_called_once()

    def test_mistral_thinking_budget_still_raises(self):
        """create_llm(provider='mistral', thinking_budget=8000) still raises."""
        with pytest.raises(ValueError, match="thinking_budget"):
            create_llm(provider="mistral", thinking_budget=8000)

    def test_openai_thinking_budget_still_raises(self):
        """create_llm(provider='openai', thinking_budget=8000) still raises."""
        with pytest.raises(ValueError, match="thinking_budget"):
            create_llm(provider="openai", thinking_budget=8000)

    def test_google_temperature_not_overridden(self):
        """Temperature is NOT forced to 1 for google even with thinking_budget >= 1024."""
        mock_llm = MagicMock()
        with patch(
            "yamlgraph.utils.llm_factory._create_google_llm", return_value=mock_llm
        ) as mock_create:
            create_llm(provider="google", thinking_budget=8000, temperature=0.7)
            args = mock_create.call_args[0]
            # second positional arg is temperature
            temperature_arg = args[1]
            assert (
                temperature_arg == 0.7
            ), f"Temperature should not be overridden for google, got {temperature_arg}"

    def test_vertex_temperature_not_overridden(self):
        """Temperature is NOT forced to 1 for vertex even with thinking_budget >= 1024."""
        mock_llm = MagicMock()
        with patch(
            "yamlgraph.utils.llm_factory._create_vertex_llm", return_value=mock_llm
        ) as mock_create:
            create_llm(provider="vertex", thinking_budget=8000, temperature=0.5)
            args = mock_create.call_args[0]
            temperature_arg = args[1]
            assert (
                temperature_arg == 0.5
            ), f"Temperature should not be overridden for vertex, got {temperature_arg}"


@pytest.mark.req("REQ-YG-230")
class TestGoogleLLMReceivesThinkingBudget:
    """ChatGoogleGenerativeAI receives thinking_budget kwarg."""

    def setup_method(self):
        clear_cache()

    def test_google_llm_receives_thinking_budget_kwarg(self):
        """_create_google_llm passes thinking_budget to ChatGoogleGenerativeAI."""
        from yamlgraph.utils.llm_factory import _create_google_llm

        mock_instance = MagicMock()
        with patch(
            "langchain_google_genai.ChatGoogleGenerativeAI",
            return_value=mock_instance,
        ) as MockChat:
            _create_google_llm("gemini-2.5-flash", 0.7, thinking_budget=8000)
            call_kwargs = MockChat.call_args[1]
            assert call_kwargs.get("thinking_budget") == 8000

    def test_google_llm_no_thinking_budget_kwarg_when_none(self):
        """_create_google_llm does NOT pass thinking_budget when None."""
        from yamlgraph.utils.llm_factory import _create_google_llm

        mock_instance = MagicMock()
        with patch(
            "langchain_google_genai.ChatGoogleGenerativeAI",
            return_value=mock_instance,
        ) as MockChat:
            _create_google_llm("gemini-2.5-flash", 0.7, thinking_budget=None)
            call_kwargs = MockChat.call_args[1]
            assert "thinking_budget" not in call_kwargs

    def test_vertex_llm_receives_thinking_budget_kwarg(self):
        """_create_vertex_llm passes thinking_budget to ChatGoogleGenerativeAI."""
        from yamlgraph.utils.llm_factory import _create_vertex_llm

        mock_instance = MagicMock()
        with (
            patch.dict(os.environ, {"VERTEX_API_KEY": "test-key"}),
            patch(
                "langchain_google_genai.ChatGoogleGenerativeAI",
                return_value=mock_instance,
            ) as MockChat,
        ):
            _create_vertex_llm("gemini-2.5-flash", 0.7, thinking_budget=8000)
            call_kwargs = MockChat.call_args[1]
            assert call_kwargs.get("thinking_budget") == 8000


@pytest.mark.req("REQ-YG-230")
class TestLinterFR230:
    """Linter does not fire W071-1/2/4 for google/vertex, W071-3 for gemini-2.5."""

    def test_w071_2_does_not_fire_for_google(self, tmp_path):
        """W071-2 (unsupported provider) does not fire for provider='google'."""
        graph_file = tmp_path / "graph.yaml"
        graph_file.write_text("""
defaults:
  provider: google
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
        w071_2 = [i for i in result.issues if i.code == "W071-2"]
        assert len(w071_2) == 0, f"W071-2 should not fire for google: {w071_2}"

    def test_w071_2_does_not_fire_for_vertex(self, tmp_path):
        """W071-2 does not fire for provider='vertex'."""
        graph_file = tmp_path / "graph.yaml"
        graph_file.write_text("""
defaults:
  provider: vertex
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
        w071_2 = [i for i in result.issues if i.code == "W071-2"]
        assert len(w071_2) == 0, f"W071-2 should not fire for vertex: {w071_2}"

    def test_w071_2_still_fires_for_openai(self, tmp_path):
        """W071-2 still fires for unsupported provider like openai."""
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
        w071_2 = [i for i in result.issues if i.code == "W071-2"]
        assert len(w071_2) == 1

    def test_w071_1_does_not_fire_for_google(self, tmp_path):
        """W071-1 (temperature override warning) does not fire for google."""
        graph_file = tmp_path / "graph.yaml"
        graph_file.write_text("""
defaults:
  provider: google
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
        w071_1 = [i for i in result.issues if i.code == "W071-1"]
        assert len(w071_1) == 0, f"W071-1 should not fire for google: {w071_1}"

    def test_w071_1_does_not_fire_for_vertex(self, tmp_path):
        """W071-1 does not fire for vertex."""
        graph_file = tmp_path / "graph.yaml"
        graph_file.write_text("""
defaults:
  provider: vertex
  temperature: 0.5
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
        w071_1 = [i for i in result.issues if i.code == "W071-1"]
        assert len(w071_1) == 0, f"W071-1 should not fire for vertex: {w071_1}"

    def test_w071_4_does_not_fire_for_google(self, tmp_path):
        """W071-4 (below minimum) does not fire for google (no minimum enforced)."""
        graph_file = tmp_path / "graph.yaml"
        graph_file.write_text("""
defaults:
  provider: google
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
        w071_4 = [i for i in result.issues if i.code == "W071-4"]
        assert len(w071_4) == 0, f"W071-4 should not fire for google: {w071_4}"

    def test_w071_4_does_not_fire_for_vertex(self, tmp_path):
        """W071-4 does not fire for vertex."""
        graph_file = tmp_path / "graph.yaml"
        graph_file.write_text("""
defaults:
  provider: vertex
  thinking_budget: 100
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
        w071_4 = [i for i in result.issues if i.code == "W071-4"]
        assert len(w071_4) == 0, f"W071-4 should not fire for vertex: {w071_4}"

    def test_w071_3_does_not_fire_for_gemini_25(self, tmp_path):
        """W071-3 does not fire for gemini-2.5-flash (thinking-capable)."""
        graph_file = tmp_path / "graph.yaml"
        graph_file.write_text("""
defaults:
  provider: google
  model: gemini-2.5-flash
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
        w071_3 = [i for i in result.issues if i.code == "W071-3"]
        assert (
            len(w071_3) == 0
        ), f"W071-3 should not fire for gemini-2.5-flash: {w071_3}"

    def test_w071_3_does_not_fire_for_gemini_3(self, tmp_path):
        """W071-3 does not fire for gemini-3 models (thinking-capable)."""
        graph_file = tmp_path / "graph.yaml"
        graph_file.write_text("""
defaults:
  provider: google
  model: gemini-3-flash
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
        w071_3 = [i for i in result.issues if i.code == "W071-3"]
        assert len(w071_3) == 0, f"W071-3 should not fire for gemini-3 model: {w071_3}"
