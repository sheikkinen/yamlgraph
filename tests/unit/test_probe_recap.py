"""Unit tests for OC-005 probe-recap python tools.

Tests for:
- parse_targets: Parse 'key:desc|key:desc' into structured target fields
- extract_answers: Merge LLM extractions into existing extracted dict
- check_missing: Compute missing fields and set phase routing
- apply_corrections: Merge caller corrections into extracted dict

OC-005: Outcaller probe-recap capability (target extraction, phase routing, confirmation)
"""

import pytest


@pytest.mark.req("OC-005")
class TestParseTargets:
    """OC-005: Parse targets string into structured fields."""

    def test_parse_simple_targets(self) -> None:
        """Parse two simple key:description pairs."""
        from projects.outcaller.nodes.probe_recap import parse_targets

        state = {"targets": "name:Your full name|age:Your age"}
        result = parse_targets(state)

        assert result["target_fields"] == [
            {"id": "name", "description": "Your full name"},
            {"id": "age", "description": "Your age"},
        ]
        assert result["extracted"] == {"name": None, "age": None}
        assert result["missing_fields"] == ["name", "age"]
        assert result["phase"] == "probe"
        assert result["probe_count"] == 0
        assert result["recap_count"] == 0

    def test_parse_targets_with_commas_in_description(self) -> None:
        """Descriptions may contain commas (pipe delimiter)."""
        from projects.outcaller.nodes.probe_recap import parse_targets

        state = {"targets": "satisfaction:How satisfied are you, on a scale of 1-5"}
        result = parse_targets(state)

        assert result["target_fields"] == [
            {
                "id": "satisfaction",
                "description": "How satisfied are you, on a scale of 1-5",
            },
        ]

    def test_parse_empty_targets(self) -> None:
        """Empty targets string returns empty structures."""
        from projects.outcaller.nodes.probe_recap import parse_targets

        state = {"targets": ""}
        result = parse_targets(state)

        assert result["target_fields"] == []
        assert result["extracted"] == {}
        assert result["missing_fields"] == []

    def test_parse_targets_trims_whitespace(self) -> None:
        """Whitespace around keys and descriptions is trimmed."""
        from projects.outcaller.nodes.probe_recap import parse_targets

        state = {"targets": "  name : Your name  |  age : Your age  "}
        result = parse_targets(state)

        assert result["target_fields"][0]["id"] == "name"
        assert result["target_fields"][0]["description"] == "Your name"


@pytest.mark.req("OC-005")
class TestExtractAnswers:
    """OC-005: Extract answers from transcript and merge into existing dict."""

    def test_extract_merges_non_null_values(self) -> None:
        """Non-null extractions are merged; null values preserve existing."""
        from unittest.mock import MagicMock, patch

        from projects.outcaller.nodes.probe_recap import extract_answers

        # Mock execute_prompt to return partial extraction
        mock_result = MagicMock()
        mock_result.updates = {"name": "John", "age": None}

        state = {
            "target_fields": [{"id": "name"}, {"id": "age"}],
            "extracted": {"name": None, "age": None},
            "transcript": "My name is John",
            "answers": [],
            "probe_count": 0,
        }

        with patch(
            "yamlgraph.executor.execute_prompt",
            return_value=mock_result,
        ):
            result = extract_answers(state)

        assert result["extracted"]["name"] == "John"
        assert result["extracted"]["age"] is None  # Not overwritten
        assert result["probe_count"] == 1

    def test_extract_preserves_previous_values(self) -> None:
        """Previously extracted values are not overwritten by null."""
        from unittest.mock import MagicMock, patch

        from projects.outcaller.nodes.probe_recap import extract_answers

        mock_result = MagicMock()
        mock_result.updates = {"name": None, "age": "25"}

        state = {
            "target_fields": [{"id": "name"}, {"id": "age"}],
            "extracted": {"name": "John", "age": None},  # name already extracted
            "transcript": "I am 25 years old",
            "answers": ["My name is John"],
            "probe_count": 1,
        }

        with patch(
            "yamlgraph.executor.execute_prompt",
            return_value=mock_result,
        ):
            result = extract_answers(state)

        assert result["extracted"]["name"] == "John"  # Preserved
        assert result["extracted"]["age"] == "25"  # New extraction
        assert result["probe_count"] == 2


@pytest.mark.req("OC-005")
class TestCheckMissing:
    """OC-005: Compute missing fields and route to probe/recap."""

    def test_check_missing_all_missing(self) -> None:
        """All fields missing -> phase = 'probe'."""
        from projects.outcaller.nodes.probe_recap import check_missing

        state = {
            "extracted": {"name": None, "age": None},
            "probe_count": 0,
        }
        result = check_missing(state)

        assert result["missing_fields"] == ["name", "age"]
        assert result["phase"] == "probe"

    def test_check_missing_some_missing(self) -> None:
        """Some fields missing -> phase = 'probe'."""
        from projects.outcaller.nodes.probe_recap import check_missing

        state = {
            "extracted": {"name": "John", "age": None},
            "probe_count": 1,
        }
        result = check_missing(state)

        assert result["missing_fields"] == ["age"]
        assert result["phase"] == "probe"

    def test_check_missing_none_missing(self) -> None:
        """No fields missing -> phase = 'recap'."""
        from projects.outcaller.nodes.probe_recap import check_missing

        state = {
            "extracted": {"name": "John", "age": "25"},
            "probe_count": 2,
        }
        result = check_missing(state)

        assert result["missing_fields"] == []
        assert result["phase"] == "recap"

    def test_check_missing_probe_limit_reached(self) -> None:
        """Probe limit (5) reached -> phase = 'recap' even with missing."""
        from projects.outcaller.nodes.probe_recap import check_missing

        state = {
            "extracted": {"name": "John", "age": None},  # age still missing
            "probe_count": 5,  # limit reached
        }
        result = check_missing(state)

        assert result["missing_fields"] == ["age"]
        assert result["phase"] == "recap"  # Exit to recap despite missing


@pytest.mark.req("OC-005")
class TestApplyCorrections:
    """OC-005: Apply caller corrections from recap response."""

    def test_apply_corrections_merges_values(self) -> None:
        """Corrections are merged into extracted dict."""
        from unittest.mock import MagicMock

        from projects.outcaller.nodes.probe_recap import apply_corrections

        mock_analysis = MagicMock()
        mock_analysis.corrections = {"name": "Jonathan"}

        state = {
            "recap_analysis": mock_analysis,
            "extracted": {"name": "John", "age": "25"},
            "recap_count": 0,
        }
        result = apply_corrections(state)

        assert result["extracted"]["name"] == "Jonathan"  # Corrected
        assert result["extracted"]["age"] == "25"  # Unchanged
        assert result["recap_count"] == 1

    def test_apply_corrections_ignores_unknown_fields(self) -> None:
        """Corrections for unknown fields are ignored."""
        from unittest.mock import MagicMock

        from projects.outcaller.nodes.probe_recap import apply_corrections

        mock_analysis = MagicMock()
        mock_analysis.corrections = {"unknown_field": "value"}

        state = {
            "recap_analysis": mock_analysis,
            "extracted": {"name": "John"},
            "recap_count": 0,
        }
        result = apply_corrections(state)

        assert "unknown_field" not in result["extracted"]
        assert result["extracted"]["name"] == "John"

    def test_apply_corrections_handles_dict_analysis(self) -> None:
        """Works with dict-based analysis (non-Pydantic)."""
        from projects.outcaller.nodes.probe_recap import apply_corrections

        state = {
            "recap_analysis": {"corrections": {"age": "30"}},
            "extracted": {"name": "John", "age": "25"},
            "recap_count": 1,
        }
        result = apply_corrections(state)

        assert result["extracted"]["age"] == "30"
        assert result["recap_count"] == 2
