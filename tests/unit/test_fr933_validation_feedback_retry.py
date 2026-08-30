"""FR-933: a deterministic schema rejection must not be retried identically.

`on_error: retry` re-issues a byte-identical request. At `temperature: 0.0`
a Pydantic `ValidationError` is therefore retried into the same failure and
`max_retries` buys only latency. These tests condemn that and pin the cure:
the retry after a validation failure carries bounded, diagnostic-only
feedback — field path, message, limit/actual length — and never the value
that was rejected.
"""

from unittest.mock import patch

import pytest
from pydantic import BaseModel, Field, ValidationError

from yamlgraph.models import PipelineError
from yamlgraph.node_factory import create_node_function

OVER_LENGTH = "z" * 420
CANARY = "canary-substring-of-the-rejected-value"


class Finding(BaseModel):
    """Stand-in for the research-route persona schema."""

    rationale: str = Field(min_length=1, max_length=400)


def _validation_error(value: str = OVER_LENGTH) -> ValidationError:
    try:
        Finding(rationale=value)
    except ValidationError as exc:
        return exc
    raise AssertionError("expected a ValidationError")


def _node(max_retries: int = 2):
    return create_node_function(
        "generate",
        {
            "prompt": "generate",
            "on_error": "retry",
            "max_retries": max_retries,
            "state_key": "generated",
        },
        {},
    )


@pytest.mark.req("REQ-YG-027")
@patch("yamlgraph.node_factory.llm_nodes.execute_prompt")
def test_validation_retry_carries_bounded_feedback(mock_execute):
    """AC-01/AC-02: the retry after a ValidationError differs from attempt 1."""
    mock_execute.side_effect = _validation_error()

    _node()({"topic": "test"})

    first, retry = mock_execute.call_args_list[0], mock_execute.call_args_list[1]
    assert first.kwargs.get("retry_feedback") is None, "attempt 1 has nothing to report"

    feedback = retry.kwargs.get("retry_feedback")
    assert feedback, "the retry must be told why attempt 1 was rejected"
    assert "rationale" in feedback, "the failing field path"
    assert "400" in feedback, "the limit"
    assert "420" in feedback, "the actual length"


@pytest.mark.req("REQ-YG-027")
@patch("yamlgraph.node_factory.llm_nodes.execute_prompt")
def test_retry_feedback_never_leaks_the_rejected_value(mock_execute):
    """AC-03/AC-08: report the constraint, never echo the value.

    Carrying the rejected text back would reintroduce the over-length
    string the schema just refused, and `str(ValidationError)` embeds it in
    `input_value`. The feedback is built from structured error data instead.
    """
    mock_execute.side_effect = _validation_error(CANARY + "y" * 420)

    _node()({"topic": "test"})

    feedback = mock_execute.call_args_list[1].kwargs.get("retry_feedback")
    assert feedback, "guard against a vacuous pass: there must be feedback to inspect"
    assert CANARY not in feedback, "the rejected value leaked into the retry"


@pytest.mark.req("REQ-YG-027")
@patch("yamlgraph.node_factory.llm_nodes.execute_prompt")
def test_feedback_retry_can_converge(mock_execute):
    """AC-04: feedback must be able to produce a pass, not merely differ."""
    mock_execute.side_effect = [_validation_error(), Finding(rationale="brief")]

    result = _node()({"topic": "test"})

    assert result["generated"].rationale == "brief"


@pytest.mark.req("REQ-YG-027", "REQ-YG-029")
@patch("yamlgraph.node_factory.llm_nodes.execute_prompt")
def test_exhausted_validation_retry_surfaces_the_error(mock_execute):
    """AC-05: exhaustion surfaces; it never truncates, coerces or fakes success."""
    mock_execute.side_effect = _validation_error()

    result = _node()({"topic": "test"})

    assert "generated" not in result or result["generated"] is None
    error = result["errors"][0]
    assert isinstance(error, PipelineError)
    assert error.node == "generate"
    assert "rationale" in error.message
    assert CANARY not in error.message


@pytest.mark.req("REQ-YG-027")
@patch("yamlgraph.node_factory.llm_nodes.execute_prompt")
def test_non_validation_retry_input_is_unchanged(mock_execute):
    """AC-06: only validation failures gain feedback; transient faults do not.

    A timeout carries no constraint to report, and retrying it identically
    is the correct strategy — that is what retry was built for.
    """
    mock_execute.side_effect = TimeoutError("connection reset")

    _node()({"topic": "test"})

    inputs = [c.kwargs.get("retry_feedback") for c in mock_execute.call_args_list]
    assert inputs == [None] * len(inputs), "a transient fault must be retried as-is"
