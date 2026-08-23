from pathlib import Path

import pytest
import yaml

from yamlgraph.compile.graph_loader import compile_graph, load_graph_config


@pytest.mark.req("REQ-YG-044")
class TestFR342HelloStructuredOutputDemo:
    """Acceptance tests for FR-342 structured output hello demo."""

    def test_ac01_greet_prompt_defines_inline_schema_fields(self):
        """AC-01: greet.yaml contains inline schema with required fields."""
        greet_yaml_path = Path("examples/demos/hello/prompts/greet.yaml")
        assert greet_yaml_path.exists()

        with open(greet_yaml_path) as f:
            content = yaml.safe_load(f)

        # Should have schema section
        assert "schema" in content
        assert "fields" in content["schema"]

        fields = content["schema"]["fields"]

        # Should have required fields
        assert "greeting" in fields
        assert "emoji" in fields
        assert "formality_level" in fields

        # Verify field types
        assert fields["greeting"]["type"] == "str"
        assert fields["emoji"]["type"] == "str"
        assert fields["formality_level"]["type"] == "str"

    def test_ac02_hello_graph_returns_structured_greeting_fields(self):
        """AC-02: Hello graph returns structured output, not raw text."""
        config = load_graph_config("examples/demos/hello/graph.yaml")
        state_graph = compile_graph(config)
        compiled = state_graph.compile()

        result = compiled.invoke({"name": "World", "style": "holy see of code"})

        # Should have greeting state key
        assert "greeting" in result
        greeting = result["greeting"]

        # Greeting should be structured object, not string
        assert isinstance(greeting, dict)

        # Should have required fields
        assert "greeting" in greeting
        assert "emoji" in greeting
        assert "formality_level" in greeting

        # Fields should be strings
        assert isinstance(greeting["greeting"], str)
        assert isinstance(greeting["emoji"], str)
        assert isinstance(greeting["formality_level"], str)

    def test_ac03_demo_output_log_contains_structured_success_evidence(self):
        """AC-03: demo-output.log shows successful structured run."""
        log_path = Path("examples/demos/hello/demo-output.log")
        assert log_path.exists()

        content = log_path.read_text()

        # Should contain structured field names
        assert (
            "greeting:" in content
            or "formality_level:" in content
            or "emoji:" in content
        )

        # Should not show error
        assert "ERROR" not in content

    def test_ac04_hello_coupled_contract_tests_expect_structured_shape(self):
        """AC-04: Tests expecting scalar greeting should be updated."""
        # This test verifies that tests assuming scalar greeting
        # have been updated to handle structured output

        # Check that existing hello tests don't break with structured output
        config = load_graph_config("examples/demos/hello/graph.yaml")
        state_graph = compile_graph(config)
        compiled = state_graph.compile()

        result = compiled.invoke({"name": "World", "style": "formal"})

        # The greeting should be structured
        greeting = result["greeting"]
        assert isinstance(greeting, dict)

        # Tolerant matching: live LLM may inflect case ("the world")
        assert "world" in greeting["greeting"].lower()
