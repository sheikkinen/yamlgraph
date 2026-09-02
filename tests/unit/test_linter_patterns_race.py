"""Tests for race node linter patterns — FR-232."""

import tempfile
from pathlib import Path

import pytest
import yaml


def _write_graph(graph: dict) -> Path:
    """Write graph dict to temp YAML file."""
    with tempfile.NamedTemporaryFile(encoding="utf-8", mode="w", suffix=".yaml", delete=False) as tmpfile:
        yaml.dump(graph, tmpfile)
    return Path(tmpfile.name)


def _make_graph(nodes: dict) -> dict:
    """Build minimal valid graph with given nodes."""
    return {
        "name": "test-race-lint",
        "nodes": nodes,
        "edges": [
            {"from": "START", "to": list(nodes.keys())[0]},
            {"from": list(nodes.keys())[-1], "to": "END"},
        ],
    }


class TestRaceLintPatterns:
    """Linter catches race node configuration errors."""

    @pytest.mark.req("REQ-YG-233")
    def test_valid_race_node_passes_lint(self):
        """Properly configured race node produces no errors."""
        from yamlgraph.linter.patterns.race import check_race_patterns

        graph = _make_graph(
            {
                "fast_response": {
                    "type": "race",
                    "prompt": "generate_response",
                    "state_key": "response",
                    "candidates": [
                        {"provider": "anthropic", "model": "claude-3-5-haiku-20241022"},
                        {"provider": "openai", "model": "gpt-4o-mini"},
                    ],
                }
            }
        )
        path = _write_graph(graph)
        issues = check_race_patterns(path)
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0

    @pytest.mark.req("REQ-YG-233")
    def test_missing_candidates(self):
        """Race node without candidates field raises lint error."""
        from yamlgraph.linter.patterns.race import check_race_node_structure

        issues = check_race_node_structure(
            "fast",
            {
                "type": "race",
                "prompt": "test",
                "state_key": "result",
            },
        )
        codes = [i.code for i in issues]
        assert "E301" in codes

    @pytest.mark.req("REQ-YG-233")
    def test_too_few_candidates(self):
        """Race node with < 2 candidates raises lint error."""
        from yamlgraph.linter.patterns.race import check_race_node_structure

        issues = check_race_node_structure(
            "fast",
            {
                "type": "race",
                "prompt": "test",
                "state_key": "result",
                "candidates": [{"provider": "anthropic"}],
            },
        )
        codes = [i.code for i in issues]
        assert "E302" in codes

    @pytest.mark.req("REQ-YG-233")
    def test_candidate_missing_provider_and_model(self):
        """Candidate without provider or model raises lint error."""
        from yamlgraph.linter.patterns.race import check_race_node_structure

        issues = check_race_node_structure(
            "fast",
            {
                "type": "race",
                "prompt": "test",
                "state_key": "result",
                "candidates": [
                    {"provider": "anthropic"},
                    {},
                ],
            },
        )
        codes = [i.code for i in issues]
        assert "E303" in codes

    @pytest.mark.req("REQ-YG-233")
    def test_missing_prompt(self):
        """Race node without prompt raises lint error."""
        from yamlgraph.linter.patterns.race import check_race_node_structure

        issues = check_race_node_structure(
            "fast",
            {
                "type": "race",
                "state_key": "result",
                "candidates": [
                    {"provider": "anthropic"},
                    {"provider": "openai"},
                ],
            },
        )
        codes = [i.code for i in issues]
        assert "E304" in codes

    @pytest.mark.req("REQ-YG-233")
    def test_race_in_valid_node_types(self):
        """'race' should be in VALID_NODE_TYPES for the base node type check."""
        from yamlgraph.linter.checks import VALID_NODE_TYPES

        assert "race" in VALID_NODE_TYPES
