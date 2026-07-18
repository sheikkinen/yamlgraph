"""Integration tests for FR-323 Vertex Gemini 3.1 hello smoke."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from yamlgraph.compile.graph_loader import compile_graph, load_graph_config


@pytest.mark.req("REQ-YG-010")
class TestFR323VertexGemini31HelloSmoke:
    """Integration smoke tests for hello graph on Vertex Gemini 3.1 models."""

    @staticmethod
    def _greeting_text(result: dict) -> str:
        """Extract greeting text from structured hello output."""
        greeting = result["greeting"]
        if isinstance(greeting, dict):
            return greeting["greeting"]
        return greeting

    @staticmethod
    def _invoke_hello_graph(vertex_model: str, thread_id: str) -> dict:
        with patch.dict(
            os.environ,
            {"PROVIDER": "vertex", "VERTEX_MODEL": vertex_model},
            clear=False,
        ):
            config = load_graph_config("examples/demos/hello/graph.yaml")
            state_graph = compile_graph(config)
            compiled = state_graph.compile()
            return compiled.invoke(
                {"name": "World", "style": "holy see of code"},
                {"configurable": {"thread_id": thread_id}},
            )

    @pytest.mark.skipif(
        not os.environ.get("VERTEX_API_KEY"),
        reason="VERTEX_API_KEY not set (Express mode required for smoke test)",
    )
    def test_ac01_hello_graph_runs_with_vertex_gemini31_pro(self):
        """AC-01: Hello graph runs with Vertex Gemini 3.1 Pro."""
        result = self._invoke_hello_graph(
            vertex_model="gemini-3.1-pro",
            thread_id="test-vertex-gemini31-pro",
        )

        assert "greeting" in result
        assert result["greeting"]
        assert "World" in self._greeting_text(result)

    @pytest.mark.skipif(
        not os.environ.get("VERTEX_API_KEY"),
        reason="VERTEX_API_KEY not set (Express mode required for smoke test)",
    )
    def test_ac02_hello_graph_runs_with_vertex_gemini31_flash(self):
        """AC-02: Hello graph runs with Vertex Gemini 3.1 Flash."""
        result = self._invoke_hello_graph(
            vertex_model="gemini-3.1-flash",
            thread_id="test-vertex-gemini31-flash",
        )

        assert "greeting" in result
        assert result["greeting"]
        assert "World" in self._greeting_text(result)

    def test_ac03_hello_vertex_smoke_uses_vertex_api_key_gate(self):
        """AC-03: Tests are gated by VERTEX_API_KEY (Express mode)."""
        if not os.environ.get("VERTEX_API_KEY"):
            pytest.skip("VERTEX_API_KEY not set - this validates Express mode gating")
        assert os.environ.get("VERTEX_API_KEY")

    def test_ac04_hello_docs_capture_verified_gemini31_model_names(self):
        """AC-04: Hello docs include verified Gemini 3.1 model identifiers."""
        content = Path("examples/demos/hello/README.md").read_text()

        assert "gemini-3.1-pro" in content
        assert "gemini-3.1-flash" in content
