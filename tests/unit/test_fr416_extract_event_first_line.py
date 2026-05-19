"""Tests for FR-416: extract_event first-line verdict matching.

The translate_legacy_config tests were retired when that shim was deleted in FR-419.
EventKey passthrough is now covered by test_fr419_action_config_schema_boundary.py.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from yamlgraph.utils.fsm.helpers import extract_event


class _CopilotResult(BaseModel):
    output: str


JUDGE_EVENT_MAP = {
    "approve": "approve",
    "amend": "revise",
    "reject": "reject",
    "split": "revise",
}


@pytest.mark.req("REQ-YG-319")
class TestExtractEventFirstLine:
    """extract_event matches first-line verdict tokens in multiline output."""

    def test_multiline_string_first_line_approve(self) -> None:
        """Plain multiline string: verdict on first line, rationale below."""
        raw = "APPROVE\n\nRationale: The feature request is well-scoped."
        assert extract_event(raw, JUDGE_EVENT_MAP) == "approve"

    def test_multiline_string_first_line_amend(self) -> None:
        raw = "AMEND\n\nThe acceptance criteria need more detail."
        assert extract_event(raw, JUDGE_EVENT_MAP) == "revise"

    def test_multiline_string_first_line_reject(self) -> None:
        raw = "REJECT\n\nOut of scope for this sprint."
        assert extract_event(raw, JUDGE_EVENT_MAP) == "reject"

    def test_multiline_string_first_line_split(self) -> None:
        raw = "SPLIT\n\nThis request is too large; split into two FRs."
        assert extract_event(raw, JUDGE_EVENT_MAP) == "revise"

    def test_pydantic_model_multiline_output_approve(self) -> None:
        """CopilotResult-style Pydantic model with multiline output field."""
        result = _CopilotResult(output="APPROVE\n\nRationale: Looks good.")
        assert extract_event(result, JUDGE_EVENT_MAP) == "approve"

    def test_pydantic_model_multiline_output_reject(self) -> None:
        result = _CopilotResult(output="REJECT\n\nDoes not meet requirements.")
        assert extract_event(result, JUDGE_EVENT_MAP) == "reject"

    def test_exact_string_match_still_works(self) -> None:
        """Regression: exact single-value strings must still match."""
        assert extract_event("approve", JUDGE_EVENT_MAP) == "approve"
        assert extract_event(" APPROVE ", JUDGE_EVENT_MAP) == "approve"
        assert extract_event("unknown", JUDGE_EVENT_MAP) is None

    def test_exact_pydantic_field_still_works(self) -> None:
        """Regression: Pydantic model with exact single-value field still matches."""
        result = _CopilotResult(output="approve")
        assert extract_event(result, JUDGE_EVENT_MAP) == "approve"

    def test_none_returns_none(self) -> None:
        assert extract_event(None, JUDGE_EVENT_MAP) is None
