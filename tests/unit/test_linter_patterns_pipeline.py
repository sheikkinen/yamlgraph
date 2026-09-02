"""Unit tests for FR-235: Pipeline template linter patterns.

Validates that the linter catches structural issues in pipeline nodes:
- Missing or empty items
- Missing or empty stages
- Unresolved {item.*} references
"""

import tempfile
from pathlib import Path

import pytest
import yaml


def _write_graph(graph: dict) -> Path:
    """Write a graph dict to a temp YAML file and return its path."""
    with tempfile.NamedTemporaryFile(encoding="utf-8", suffix=".yaml", delete=False, mode="w") as tmp:
        yaml.dump(graph, tmp)
    return Path(tmp.name)


class TestPipelineLintChecks:
    """Linter validates pipeline node structure."""

    @pytest.mark.req("REQ-YG-236")
    def test_missing_items_reports_error(self):
        """Pipeline node without 'items' field → E401."""
        from yamlgraph.linter.patterns.pipeline import check_pipeline_patterns

        graph = {
            "nodes": {
                "chapters": {
                    "type": "pipeline",
                    "stages": [
                        {
                            "name": "write",
                            "type": "copilot",
                            "prompt": "write/ch",
                            "state_key": "out",
                        }
                    ],
                }
            },
            "edges": [],
        }
        path = _write_graph(graph)

        issues = check_pipeline_patterns(path)
        codes = [i.code for i in issues]
        assert "E401" in codes

    @pytest.mark.req("REQ-YG-236")
    def test_empty_items_reports_error(self):
        """Pipeline node with empty items list → E401."""
        from yamlgraph.linter.patterns.pipeline import check_pipeline_patterns

        graph = {
            "nodes": {
                "chapters": {
                    "type": "pipeline",
                    "items": [],
                    "stages": [
                        {
                            "name": "write",
                            "type": "copilot",
                            "prompt": "write/ch",
                            "state_key": "out",
                        }
                    ],
                }
            },
            "edges": [],
        }
        path = _write_graph(graph)

        issues = check_pipeline_patterns(path)
        codes = [i.code for i in issues]
        assert "E401" in codes

    @pytest.mark.req("REQ-YG-236")
    def test_missing_stages_reports_error(self):
        """Pipeline node without 'stages' field → E402."""
        from yamlgraph.linter.patterns.pipeline import check_pipeline_patterns

        graph = {
            "nodes": {
                "chapters": {
                    "type": "pipeline",
                    "items": [{"name": "ch1", "prompt_prefix": "ch/1"}],
                }
            },
            "edges": [],
        }
        path = _write_graph(graph)

        issues = check_pipeline_patterns(path)
        codes = [i.code for i in issues]
        assert "E402" in codes

    @pytest.mark.req("REQ-YG-236")
    def test_empty_stages_reports_error(self):
        """Pipeline node with empty stages list → E402."""
        from yamlgraph.linter.patterns.pipeline import check_pipeline_patterns

        graph = {
            "nodes": {
                "chapters": {
                    "type": "pipeline",
                    "items": [{"name": "ch1", "prompt_prefix": "ch/1"}],
                    "stages": [],
                }
            },
            "edges": [],
        }
        path = _write_graph(graph)

        issues = check_pipeline_patterns(path)
        codes = [i.code for i in issues]
        assert "E402" in codes

    @pytest.mark.req("REQ-YG-236")
    def test_unresolved_item_reference_reports_error(self):
        """Stage referencing {item.nonexistent} → E403."""
        from yamlgraph.linter.patterns.pipeline import check_pipeline_patterns

        graph = {
            "nodes": {
                "chapters": {
                    "type": "pipeline",
                    "items": [{"name": "ch1", "prompt_prefix": "ch/1"}],
                    "stages": [
                        {
                            "name": "write",
                            "type": "copilot",
                            "prompt": "{item.nonexistent_field}",
                            "state_key": "out",
                        }
                    ],
                }
            },
            "edges": [],
        }
        path = _write_graph(graph)

        issues = check_pipeline_patterns(path)
        codes = [i.code for i in issues]
        assert "E403" in codes

    @pytest.mark.req("REQ-YG-236")
    def test_resolved_item_reference_no_error(self):
        """Stage referencing valid {item.prompt_prefix} → no E403."""
        from yamlgraph.linter.patterns.pipeline import check_pipeline_patterns

        graph = {
            "nodes": {
                "chapters": {
                    "type": "pipeline",
                    "items": [{"name": "ch1", "prompt_prefix": "ch/1"}],
                    "stages": [
                        {
                            "name": "write",
                            "type": "copilot",
                            "prompt": "{item.prompt_prefix}",
                            "state_key": "out",
                        }
                    ],
                }
            },
            "edges": [],
        }
        path = _write_graph(graph)

        issues = check_pipeline_patterns(path)
        codes = [i.code for i in issues]
        assert "E403" not in codes

    @pytest.mark.req("REQ-YG-236")
    def test_item_missing_name_reports_error(self):
        """Item without 'name' field → E404."""
        from yamlgraph.linter.patterns.pipeline import check_pipeline_patterns

        graph = {
            "nodes": {
                "chapters": {
                    "type": "pipeline",
                    "items": [{"prompt_prefix": "ch/1"}],
                    "stages": [
                        {
                            "name": "write",
                            "type": "copilot",
                            "prompt": "{item.prompt_prefix}",
                            "state_key": "out",
                        }
                    ],
                }
            },
            "edges": [],
        }
        path = _write_graph(graph)

        issues = check_pipeline_patterns(path)
        codes = [i.code for i in issues]
        assert "E404" in codes

    @pytest.mark.req("REQ-YG-236")
    def test_stage_missing_name_reports_error(self):
        """Stage without 'name' field → E404."""
        from yamlgraph.linter.patterns.pipeline import check_pipeline_patterns

        graph = {
            "nodes": {
                "chapters": {
                    "type": "pipeline",
                    "items": [{"name": "ch1", "prompt_prefix": "ch/1"}],
                    "stages": [
                        {
                            "type": "copilot",
                            "prompt": "{item.prompt_prefix}",
                            "state_key": "out",
                        }
                    ],
                }
            },
            "edges": [],
        }
        path = _write_graph(graph)

        issues = check_pipeline_patterns(path)
        codes = [i.code for i in issues]
        assert "E404" in codes

    @pytest.mark.req("REQ-YG-236")
    def test_valid_pipeline_no_errors(self):
        """Well-formed pipeline node → no errors."""
        from yamlgraph.linter.patterns.pipeline import check_pipeline_patterns

        graph = {
            "nodes": {
                "chapters": {
                    "type": "pipeline",
                    "items": [
                        {"name": "ch1", "prompt_prefix": "ch/1"},
                        {"name": "ch2", "prompt_prefix": "ch/2"},
                    ],
                    "stages": [
                        {
                            "name": "write",
                            "type": "copilot",
                            "prompt": "{item.prompt_prefix}",
                            "state_key": "out",
                        },
                        {
                            "name": "judge",
                            "type": "copilot",
                            "prompt": "judge/ch",
                            "state_key": "out",
                        },
                    ],
                }
            },
            "edges": [],
        }
        path = _write_graph(graph)

        issues = check_pipeline_patterns(path)
        error_issues = [i for i in issues if i.severity == "error"]
        assert len(error_issues) == 0


class TestPipelineInValidNodeTypes:
    """Pipeline should be in VALID_NODE_TYPES so check_node_types doesn't flag it."""

    @pytest.mark.req("REQ-YG-236")
    def test_pipeline_in_valid_node_types(self):
        """'pipeline' is in VALID_NODE_TYPES."""
        from yamlgraph.linter.checks import VALID_NODE_TYPES

        assert "pipeline" in VALID_NODE_TYPES
