"""FR-420: extract_event must handle plain dicts.

RED tests — written before the fix. All should FAIL until helpers.py is patched.

Addresses the LangGraph state serialization boundary:
  CopilotResult Pydantic model → LangGraph ainvoke → plain dict in result state
  extract_event(plain_dict, event_map) currently returns None → event=error
"""

from __future__ import annotations

import pytest

from yamlgraph.utils.fsm.helpers import extract_event

pytestmark = pytest.mark.req("REQ-YG-319")

_EVENT_MAP = {
    "approve": "approve",
    "amend": "revise",
    "reject": "reject",
    "split": "revise",
}

# ---------------------------------------------------------------------------
# RED: plain dict — the failing path (CopilotResult serialized by LangGraph)
# ---------------------------------------------------------------------------


class TestExtractEventPlainDict:
    """AC-01 to AC-04: extract_event handles CopilotResult.model_dump() output."""

    def test_ac01_approve_verdict_in_output_field(self) -> None:
        raw = {
            "output": "APPROVE\nScope frozen, authority granted.",
            "exit_code": 0,
            "backend": "cli",
        }
        assert extract_event(raw, _EVENT_MAP) == "approve"

    def test_ac02_amend_verdict_in_output_field(self) -> None:
        raw = {
            "output": "AMEND\nItem 3 lacks measurable acceptance criteria.",
            "exit_code": 0,
            "backend": "cli",
        }
        assert extract_event(raw, _EVENT_MAP) == "revise"

    def test_ac03_reject_verdict_in_output_field(self) -> None:
        raw = {
            "output": "REJECT\nProblem is not real; existing abstractions suffice.",
            "exit_code": 0,
            "backend": "cli",
        }
        assert extract_event(raw, _EVENT_MAP) == "reject"

    def test_ac04_split_verdict_in_output_field(self) -> None:
        raw = {
            "output": "SPLIT\nTwo orthogonal concerns bundled.",
            "exit_code": 0,
            "backend": "cli",
        }
        assert extract_event(raw, _EVENT_MAP) == "revise"

    def test_ac05_exact_single_word_dict_value(self) -> None:
        """Single-word string field also matches (no first-line split needed)."""
        raw = {"verdict": "approve"}
        assert extract_event(raw, _EVENT_MAP) == "approve"

    def test_ac06_none_returned_when_no_string_matches(self) -> None:
        """Dict with no string values matching event_map → None (not error raised)."""
        raw = {"exit_code": 0, "status": "done_but_not_an_event"}
        assert extract_event(raw, _EVENT_MAP) is None


# ---------------------------------------------------------------------------
# AC-07: bridge-level routing simulation (Amendment B constraint 4)
# — proves _resolve_event-equivalent path works with plain dict as event_key value
# ---------------------------------------------------------------------------


class TestResolveEventWithPlainDictEventKey:
    """AC-07: full state dict with event_key pointing to a plain dict routes correctly."""

    def test_ac07_state_dict_with_plain_dict_event_key(self) -> None:
        """Simulates graph_runner._resolve_event logic for the judge step.

        result = {"judge_result": {"output": "APPROVE\\n...", ...}}
        event_key = "judge_result"
        event_map (normalised) = {"approve": "approve", ...}
        Expected: extract_event returns "approve"
        """
        result = {
            "judge_result": {
                "output": "APPROVE\nScope frozen.",
                "exit_code": 0,
                "model": "claude-sonnet-4.6",
                "backend": "cli",
                "session_id": None,
            },
            "current_step": "judge",
        }
        event_key = "judge_result"
        mapped = extract_event(result.get(event_key), _EVENT_MAP)
        assert mapped == "approve"


# ---------------------------------------------------------------------------
# Regression guards: existing str and Pydantic-model paths must be unchanged
# ---------------------------------------------------------------------------


class TestExtractEventRegressionGuards:
    """Existing behavior must not regress under the dict fix."""

    def test_str_exact_match_unchanged(self) -> None:
        assert extract_event("approve", _EVENT_MAP) == "approve"

    def test_str_first_line_unchanged(self) -> None:
        assert extract_event("APPROVE\nfull reasoning text", _EVENT_MAP) == "approve"

    def test_pydantic_model_unchanged(self) -> None:
        from yamlgraph.models.schemas import CopilotResult

        cr = CopilotResult(output="AMEND\nreasoning", exit_code=0, backend="cli")
        assert extract_event(cr, _EVENT_MAP) == "revise"

    def test_none_returns_none(self) -> None:
        assert extract_event(None, _EVENT_MAP) is None


# ---------------------------------------------------------------------------
# Preamble: copilot CLI output has reasoning before the verdict keyword
# ---------------------------------------------------------------------------


class TestExtractEventPreamble:
    """Condemns the first-line-only assumption.

    The Copilot CLI outputs reasoning text before the verdict keyword.
    Captured from a real judge run on 2026-05-19:
        First line: "Now I have enough context for a thorough judgment..."
        Verdict:    "AMEND" on line 3

    Old first-line logic returned None → event=error.
    Fix: scan all lines for an exact event_map key match.
    """

    # Verbatim from a real standalone judge run (2026-05-19)
    _REAL_JUDGE_OUTPUT = {
        "output": (
            "Now I have enough context for a thorough judgment. "
            "Let me write the verdict back into the FR.\n\n"
            "AMEND\n\n"
            "**Three issues block APPROVE:**\n\n"
            "1. **AMEND-01 — Integration path is architecturally broken.**..."
        )
    }

    def test_verdict_after_preamble_matches(self) -> None:
        """AMEND on line 3, preamble on line 1 — must match to 'revise'."""
        assert extract_event(self._REAL_JUDGE_OUTPUT, _EVENT_MAP) == "revise"

    def test_verdict_after_markdown_header_matches(self) -> None:
        raw = {"output": "## Judgement\n\nAPPROVE\n\nReasoning..."}
        assert extract_event(raw, _EVENT_MAP) == "approve"

    def test_verdict_on_first_line_still_matches(self) -> None:
        """First-line verdict must still work after the fix."""
        raw = {"output": "APPROVE\n\nThe FR is clear."}
        assert extract_event(raw, _EVENT_MAP) == "approve"

    def test_str_preamble_matches(self) -> None:
        """str input with preamble must also scan all lines."""
        assert (
            extract_event("Reasoning text\n\nREJECT\n\nDetails", _EVENT_MAP) == "reject"
        )

    def test_buried_inline_does_not_match(self) -> None:
        """Verdict embedded mid-sentence must NOT match — only standalone lines."""
        assert (
            extract_event(
                {"output": "I would approve this if it were clearer."}, _EVENT_MAP
            )
            is None
        )
