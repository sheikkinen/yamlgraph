"""FR-1152: ``--token-usage`` counts thinking tokens.

The tracker sums ``usage_metadata["output_token_details"]["reasoning"]`` (LangChain's normalised field; Anthropic's
``output_tokens_details.thinking_tokens``). The count is part of the output tokens, never added to the total. The
printed line adds ``, N thinking`` only when N > 0.
"""

from argparse import Namespace
from unittest.mock import MagicMock

import pytest

from yamlgraph.cli.graph_run_helpers import _emit_success_output
from yamlgraph.utils.token_tracker import TokenUsageCallbackHandler


def _result(input_tokens, output_tokens, details="absent"):
    usage = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }
    if details != "absent":
        usage["output_token_details"] = details
    message = MagicMock()
    message.usage_metadata = usage
    generation = MagicMock()
    generation.message = message
    result = MagicMock()
    result.generations = [[generation]]
    return result


def _printed(handler, capsys):
    _emit_success_output(Namespace(full=False), {}, handler, None, json_mode=False)
    return [ln for ln in capsys.readouterr().out.splitlines() if "Token usage" in ln][0]


@pytest.mark.req("REQ-YG-064")
def test_reasoning_tokens_are_summed():
    """AC-01."""
    handler = TokenUsageCallbackHandler()
    handler.on_llm_end(_result(100, 80, {"reasoning": 30}))
    handler.on_llm_end(_result(50, 40, {"reasoning": 12}))
    summary = handler.summary()
    assert summary["total_reasoning_tokens"] == 42
    assert (
        summary["total_input_tokens"],
        summary["total_output_tokens"],
        summary["total_calls"],
    ) == (150, 120, 2)


@pytest.mark.req("REQ-YG-064")
@pytest.mark.parametrize(
    "details", ["absent", {}, {"audio": 3}], ids=["no-details", "empty", "no-reasoning"]
)
def test_missing_reasoning_adds_zero(details):
    """AC-02."""
    handler = TokenUsageCallbackHandler()
    handler.on_llm_end(_result(10, 5, details))
    assert handler.summary()["total_reasoning_tokens"] == 0


@pytest.mark.req("REQ-YG-064")
def test_none_reasoning_adds_zero():
    """AC-09."""
    handler = TokenUsageCallbackHandler()
    handler.on_llm_end(_result(10, 5, {"reasoning": None}))
    assert handler.summary()["total_reasoning_tokens"] == 0


@pytest.mark.req("REQ-YG-064")
def test_thinking_is_part_of_output_not_added():
    """AC-08."""
    handler = TokenUsageCallbackHandler()
    handler.on_llm_end(_result(100, 80, {"reasoning": 30}))
    summary = handler.summary()
    assert summary["total_tokens"] == summary["total_input_tokens"] + 80


@pytest.mark.req("REQ-YG-064")
def test_printed_line_adds_thinking(capsys):
    """AC-03."""
    handler = TokenUsageCallbackHandler()
    handler.on_llm_end(_result(100, 80, {"reasoning": 30}))
    handler.on_llm_end(_result(50, 40, {"reasoning": 12}))
    assert _printed(handler, capsys).endswith("(2 calls), 42 thinking")


@pytest.mark.req("REQ-YG-064")
def test_printed_line_unchanged_without_thinking(capsys):
    """AC-03: character for character."""
    handler = TokenUsageCallbackHandler()
    handler.on_llm_end(_result(100, 50, {"reasoning": 0}))
    assert (
        _printed(handler, capsys) == "\U0001f4ca Token usage: 100 in / 50 out (1 call)"
    )
