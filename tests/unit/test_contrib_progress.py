"""Tests for yamlgraph.contrib.progress module (FR-044d).

Tests for SkipReport - reads PipelineErrors from state["errors"]
and provides human-readable skip summaries.
"""

import pytest

from yamlgraph.models import ErrorType, PipelineError


class TestSkipReport:
    """Tests for SkipReport class."""

    @pytest.mark.req("REQ-YG-071")
    def test_no_errors_returns_success_message(self):
        """Empty errors list reports all nodes completed."""
        from yamlgraph.contrib.progress import SkipReport

        report = SkipReport(errors=[])
        assert report.count == 0
        assert "completed successfully" in report.summary().lower()

    @pytest.mark.req("REQ-YG-071")
    def test_with_errors_shows_count_and_nodes(self):
        """Errors list produces summary with count and node names."""
        from yamlgraph.contrib.progress import SkipReport

        errors = [
            PipelineError(
                node="scamper",
                type=ErrorType.LLM_ERROR,
                message="API timeout",
            ),
            PipelineError(
                node="five_whys",
                type=ErrorType.VALIDATION_ERROR,
                message="Missing field",
            ),
        ]
        report = SkipReport(errors=errors)

        assert report.count == 2
        summary = report.summary()
        assert "2" in summary
        assert "scamper" in summary
        assert "five_whys" in summary

    @pytest.mark.req("REQ-YG-071")
    def test_from_state_extracts_errors(self):
        """from_state() builds report from state dict."""
        from yamlgraph.contrib.progress import SkipReport

        state = {
            "errors": [
                PipelineError(
                    node="test_node",
                    type=ErrorType.UNKNOWN_ERROR,
                    message="Test error",
                ),
            ],
            "other_key": "ignored",
        }
        report = SkipReport.from_state(state)

        assert report.count == 1
        assert "test_node" in report.summary()

    @pytest.mark.req("REQ-YG-071")
    def test_to_dict_is_serializable(self):
        """to_dict() returns JSON-serializable output."""
        from yamlgraph.contrib.progress import SkipReport

        errors = [
            PipelineError(
                node="node_a",
                type=ErrorType.LLM_ERROR,
                message="Error A",
            ),
        ]
        report = SkipReport(errors=errors)
        data = report.to_dict()

        assert data["skipped_count"] == 1
        assert len(data["skipped_nodes"]) == 1
        assert data["skipped_nodes"][0]["node"] == "node_a"
        assert data["skipped_nodes"][0]["error"] == "Error A"
        assert data["skipped_nodes"][0]["type"] == "llm_error"

    @pytest.mark.req("REQ-YG-071")
    def test_with_total_nodes_shows_fraction(self):
        """When total_nodes provided, summary shows X/Y format."""
        from yamlgraph.contrib.progress import SkipReport

        errors = [
            PipelineError(
                node="tool_3",
                type=ErrorType.UNKNOWN_ERROR,
                message="Failed",
            ),
            PipelineError(
                node="tool_7",
                type=ErrorType.UNKNOWN_ERROR,
                message="Also failed",
            ),
        ]
        report = SkipReport(errors=errors, total_nodes=9)

        summary = report.summary()
        assert "2" in summary
        assert "9" in summary  # Should show 2/9 or similar
