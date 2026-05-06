"""Tests for deterministic guard expression evaluator (FR-344)."""

from pathlib import Path

import pytest

from yamlgraph.utils.guard_evaluator import (
    GuardExpressionError,
    evaluate_guard_expression,
)


@pytest.mark.req("REQ-YG-154")
def test_guard_expression_supports_filters_and_membership(tmp_path: Path):
    """Evaluator supports filters, membership operators, and boolean logic."""
    marker_file = tmp_path / "marker.txt"
    marker_file.write_text("ok")

    state = {
        "fr_path": str(marker_file),
        "tags": ["urgent", "feature"],
        "score": 0.8,
    }
    output = {"summary": "short text", "meta": {"owner": "core"}}

    assert evaluate_guard_expression(
        "state.fr_path | file_exists", state=state, output=output
    )
    assert evaluate_guard_expression(
        "'urgent' in state.tags", state=state, output=output
    )
    assert evaluate_guard_expression(
        "output.summary | length < 20 and state.score >= 0.7",
        state=state,
        output=output,
    )
    assert evaluate_guard_expression(
        "'meta' in output | keys", state=state, output=output
    )


@pytest.mark.req("REQ-YG-154")
def test_guard_evaluator_rejects_unsafe_or_unknown_syntax():
    """Unsafe syntax, invalid filter names, and malformed expressions are rejected."""
    with pytest.raises(GuardExpressionError, match="Unsupported syntax"):
        evaluate_guard_expression(
            "__import__('os').system('echo hacked')",
            state={},
            output=None,
        )
    with pytest.raises(GuardExpressionError, match="Unknown guard filter"):
        evaluate_guard_expression("state.path | mystery_filter", state={}, output=None)
    with pytest.raises(GuardExpressionError, match="Invalid guard expression syntax"):
        evaluate_guard_expression("state.value and", state={}, output=None)
