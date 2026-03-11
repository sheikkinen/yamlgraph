"""Tests for probe_recap tool nodes (FR-178, OC-005).

REQ-YG-083: Outcaller probe-recap target extraction
REQ-YG-084: Outcaller probe-recap phase routing
REQ-YG-085: Outcaller probe-recap confirmation/correction loop
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from projects.outcaller.nodes.probe_recap import (
    apply_corrections,
    check_missing,
    merge_extraction,
    parse_targets,
)

# ---------------------------------------------------------------------------
# parse_targets
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-083")
def test_parse_targets_basic():
    state = {"targets": "name:Full name|dob:Date of birth"}
    result = parse_targets(state)
    assert result["target_fields"] == [
        {"id": "name", "description": "Full name"},
        {"id": "dob", "description": "Date of birth"},
    ]
    assert result["extracted"] == {"name": None, "dob": None}
    assert result["missing_fields"] == ["name", "dob"]
    assert result["phase"] == "probe"
    assert result["probe_count"] == 0
    assert result["recap_count"] == 0


@pytest.mark.req("REQ-YG-083")
def test_parse_targets_single_field():
    state = {"targets": "reason:Reason for call"}
    result = parse_targets(state)
    assert len(result["target_fields"]) == 1
    assert result["target_fields"][0]["id"] == "reason"


@pytest.mark.req("REQ-YG-083")
def test_parse_targets_empty():
    state = {"targets": ""}
    result = parse_targets(state)
    assert result["target_fields"] == []
    assert result["extracted"] == {}
    assert result["missing_fields"] == []


@pytest.mark.req("REQ-YG-083")
def test_parse_targets_initializes_answers():
    state = {"targets": "x:y"}
    result = parse_targets(state)
    assert result["answers"] == []


@pytest.mark.req("REQ-YG-083")
def test_parse_targets_preserves_existing_answers():
    state = {"targets": "x:y", "answers": ["hello"]}
    result = parse_targets(state)
    assert result["answers"] == ["hello"]


@pytest.mark.req("REQ-YG-083")
def test_parse_targets_prompts_dir_absolute_if_relative():
    state = {"targets": "x:y"}
    result = parse_targets(state)
    from pathlib import Path

    assert Path(result["prompts_dir"]).is_absolute()


# ---------------------------------------------------------------------------
# merge_extraction — FR-178: no LLM call, pure state merge
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-083")
def test_merge_extraction_merges_non_null():
    """FR-178: merge_extraction reads extraction_result from state, no LLM call."""
    extraction_result = MagicMock()
    extraction_result.updates = {"name": "Alice", "dob": None}
    extraction_result.user_refused = False

    state = {
        "extraction_result": extraction_result,
        "extracted": {"name": None, "dob": None},
        "probe_count": 0,
    }
    result = merge_extraction(state)

    assert result["extracted"] == {"name": "Alice", "dob": None}
    assert result["probe_count"] == 1
    assert result["user_refused"] is False


@pytest.mark.req("REQ-YG-083")
def test_merge_extraction_does_not_overwrite_with_null():
    extraction_result = MagicMock()
    extraction_result.updates = {"name": None}
    extraction_result.user_refused = False

    state = {
        "extraction_result": extraction_result,
        "extracted": {"name": "Bob"},
        "probe_count": 2,
    }
    result = merge_extraction(state)
    assert result["extracted"]["name"] == "Bob"
    assert result["probe_count"] == 3


@pytest.mark.req("REQ-YG-083")
def test_merge_extraction_user_refused():
    extraction_result = MagicMock()
    extraction_result.updates = {}
    extraction_result.user_refused = True

    state = {
        "extraction_result": extraction_result,
        "extracted": {"name": None},
        "probe_count": 1,
    }
    result = merge_extraction(state)
    assert result["user_refused"] is True


# ---------------------------------------------------------------------------
# check_missing
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-083")
def test_check_missing_routes_to_probe_when_missing():
    state = {"extracted": {"name": "Alice", "dob": None}, "probe_count": 1}
    result = check_missing(state)
    assert "dob" in result["missing_fields"]
    assert result["phase"] == "probe"


@pytest.mark.req("REQ-YG-083")
def test_check_missing_routes_to_recap_when_complete():
    state = {"extracted": {"name": "Alice", "dob": "1990-01-01"}, "probe_count": 1}
    result = check_missing(state)
    assert result["missing_fields"] == []
    assert result["phase"] == "recap"


@pytest.mark.req("REQ-YG-083")
def test_check_missing_routes_at_limit():
    state = {"extracted": {"name": None}, "probe_count": 5}
    result = check_missing(state)
    assert result["phase"] == "recap"


# ---------------------------------------------------------------------------
# apply_corrections
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-083")
def test_apply_corrections_from_pydantic_model():
    recap_analysis = MagicMock()
    recap_analysis.corrections = {"name": "Charlie"}

    state = {
        "recap_analysis": recap_analysis,
        "extracted": {"name": "Alice", "dob": "1990"},
        "recap_count": 0,
    }
    result = apply_corrections(state)
    assert result["extracted"]["name"] == "Charlie"
    assert result["extracted"]["dob"] == "1990"
    assert result["recap_count"] == 1


@pytest.mark.req("REQ-YG-083")
def test_apply_corrections_from_dict():
    state = {
        "recap_analysis": {"corrections": {"name": "Dave"}},
        "extracted": {"name": "Alice"},
        "recap_count": 1,
    }
    result = apply_corrections(state)
    assert result["extracted"]["name"] == "Dave"
    assert result["recap_count"] == 2


@pytest.mark.req("REQ-YG-083")
def test_apply_corrections_ignores_unknown_fields():
    state = {
        "recap_analysis": {"corrections": {"unknown_field": "value"}},
        "extracted": {"name": "Alice"},
        "recap_count": 0,
    }
    result = apply_corrections(state)
    assert "unknown_field" not in result["extracted"]
    assert result["extracted"]["name"] == "Alice"
