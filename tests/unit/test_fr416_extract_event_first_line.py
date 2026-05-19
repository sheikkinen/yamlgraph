"""Tests for FR-416: extract_event first-line verdict matching and
chaplain translate_legacy_config event_key passthrough."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from pydantic import BaseModel

from yamlgraph.utils.fsm.helpers import extract_event

# Load ChaplainYamlgraphAsyncAction from .chaplain/actions/ (outside package)
_ACTION_FILE = (
    Path(__file__).resolve().parents[2]
    / ".chaplain"
    / "actions"
    / "yamlgraph_async_action.py"
)
_spec = importlib.util.spec_from_file_location("_chaplain_action", _ACTION_FILE)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]
_translate = _mod.YamlgraphAsyncAction._translate_legacy_config


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


class TestTranslateLegacyConfigEventKey:
    """Condemn: _translate_legacy_config dropped event_key, breaking judge routing."""

    @pytest.mark.req("REQ-YG-319")
    def test_event_key_passes_through_to_params(self) -> None:
        """event_key in top-level config must appear in params output."""
        config = {
            "graph": ".chaplain/graphs/watcher-plan/step-judge-v2.yaml",
            "vars": {"topic_file": "{topic_file}"},
            "event_key": "judge_result",
            "success": "done",
            "error": "error",
        }
        params = _translate(config)
        assert params.get("event_key") == "judge_result", (
            "event_key must be forwarded to params so snapshot_params() can read it; "
            "without it, snapshot_params falls back to 'yamlgraph_result' and "
            "judge output is never found."
        )

    @pytest.mark.req("REQ-YG-319")
    def test_missing_event_key_does_not_crash(self) -> None:
        """When event_key is absent, params must not contain event_key key."""
        config = {"graph": "foo.yaml"}
        params = _translate(config)
        assert "event_key" not in params
