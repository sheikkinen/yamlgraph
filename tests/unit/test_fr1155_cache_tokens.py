"""FR-1155: ``--token-usage`` counts prompt-cache reads and writes.

Both counts come from ``usage_metadata["input_token_details"]`` and are parts of ``input_tokens``, never added to it.
``langchain-anthropic`` 1.7.0 zeroes ``cache_creation`` when the per-TTL breakdown is present, so the write count is
``max(cache_creation, ephemeral_5m + ephemeral_1h)``.
"""

from argparse import Namespace
from unittest.mock import MagicMock

import pytest

from yamlgraph.cli.graph_run_helpers import _emit_success_output
from yamlgraph.utils.token_tracker import TokenUsageCallbackHandler

WRITE_2927 = {
    "cache_read": 0,
    "cache_creation": 0,
    "ephemeral_5m_input_tokens": 2927,
    "ephemeral_1h_input_tokens": 0,
}
READ_2927 = {
    "cache_read": 2927,
    "cache_creation": 0,
    "ephemeral_5m_input_tokens": 0,
    "ephemeral_1h_input_tokens": 0,
}


def _result(input_tokens, output_tokens, details="absent", output_details=None):
    usage = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }
    if details != "absent":
        usage["input_token_details"] = details
    if output_details is not None:
        usage["output_token_details"] = output_details
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
def test_cache_reads_and_writes_are_summed():
    """AC-01."""
    handler = TokenUsageCallbackHandler()
    handler.on_llm_end(_result(2938, 32, WRITE_2927))
    handler.on_llm_end(_result(2938, 32, READ_2927))
    summary = handler.summary()
    assert summary["total_cache_write_tokens"] == 2927
    assert summary["total_cache_read_tokens"] == 2927
    assert (
        summary["total_input_tokens"],
        summary["total_output_tokens"],
        summary["total_calls"],
    ) == (5876, 64, 2)


@pytest.mark.req("REQ-YG-064")
@pytest.mark.parametrize(
    ("details", "expected"),
    [
        ({"cache_creation": 500}, 500),
        ({"ephemeral_1h_input_tokens": 700}, 700),
        ({"cache_creation": 900, "ephemeral_5m_input_tokens": 900}, 900),
        ({"ephemeral_5m_input_tokens": 300, "ephemeral_1h_input_tokens": 700}, 1000),
        (
            {
                "cache_creation": 1200,
                "ephemeral_5m_input_tokens": 300,
                "ephemeral_1h_input_tokens": 700,
            },
            1200,
        ),
        (
            {
                "cache_creation": 800,
                "ephemeral_5m_input_tokens": 300,
                "ephemeral_1h_input_tokens": 700,
            },
            1000,
        ),
    ],
    ids=[
        "creation-only",
        "1h-only",
        "equal-overlap",
        "mixed-ttl",
        "creation-larger",
        "breakdown-larger",
    ],
)
def test_write_rule_is_max_of_creation_and_breakdown(details, expected):
    """AC-02."""
    handler = TokenUsageCallbackHandler()
    handler.on_llm_end(_result(3000, 10, details))
    assert handler.summary()["total_cache_write_tokens"] == expected


@pytest.mark.req("REQ-YG-064")
@pytest.mark.parametrize(
    "details",
    [
        "absent",
        None,
        {},
        {"audio": 5},
        {
            "cache_read": None,
            "cache_creation": None,
            "ephemeral_5m_input_tokens": None,
            "ephemeral_1h_input_tokens": None,
        },
    ],
    ids=["no-details", "none-details", "empty", "unrelated", "all-none"],
)
def test_missing_cache_details_add_zero(details):
    """AC-03."""
    handler = TokenUsageCallbackHandler()
    handler.on_llm_end(_result(10, 5, details))
    summary = handler.summary()
    assert summary["total_cache_read_tokens"] == 0
    assert summary["total_cache_write_tokens"] == 0


@pytest.mark.req("REQ-YG-064")
def test_cache_counts_are_part_of_input_not_added():
    """AC-04."""
    handler = TokenUsageCallbackHandler()
    handler.on_llm_end(_result(2938, 32, WRITE_2927))
    handler.on_llm_end(_result(2938, 32, READ_2927))
    summary = handler.summary()
    assert summary["total_input_tokens"] == 5876
    assert summary["total_tokens"] == 5876 + 64
    assert "parts of" in TokenUsageCallbackHandler.__doc__


@pytest.mark.req("REQ-YG-064")
def test_printed_line_adds_cache_read_and_write(capsys):
    """AC-05: both positive."""
    handler = TokenUsageCallbackHandler()
    handler.on_llm_end(_result(2938, 32, WRITE_2927))
    handler.on_llm_end(_result(2938, 32, READ_2927))
    assert _printed(handler, capsys).endswith(
        "(2 calls), 2927 cache read, 2927 cache write"
    )


@pytest.mark.req("REQ-YG-064")
def test_printed_line_orders_thinking_read_write(capsys):
    """AC-05: thinking first, then read, then write."""
    handler = TokenUsageCallbackHandler()
    handler.on_llm_end(_result(2938, 32, WRITE_2927, {"reasoning": 32}))
    handler.on_llm_end(_result(2938, 32, READ_2927, {"reasoning": 32}))
    assert _printed(handler, capsys).endswith(
        ", 64 thinking, 2927 cache read, 2927 cache write"
    )


@pytest.mark.req("REQ-YG-064")
def test_printed_line_read_only(capsys):
    """AC-05 (R-1)."""
    handler = TokenUsageCallbackHandler()
    handler.on_llm_end(_result(2938, 32, READ_2927))
    assert (
        _printed(handler, capsys)
        == "\U0001f4ca Token usage: 2938 in / 32 out (1 call), 2927 cache read"
    )


@pytest.mark.req("REQ-YG-064")
def test_printed_line_write_only(capsys):
    """AC-05 (R-1)."""
    handler = TokenUsageCallbackHandler()
    handler.on_llm_end(_result(2938, 32, WRITE_2927))
    assert (
        _printed(handler, capsys)
        == "\U0001f4ca Token usage: 2938 in / 32 out (1 call), 2927 cache write"
    )


@pytest.mark.req("REQ-YG-064")
def test_printed_line_unchanged_without_cache(capsys):
    """AC-05: character for character."""
    handler = TokenUsageCallbackHandler()
    handler.on_llm_end(
        _result(
            100,
            50,
            {"cache_read": 0, "cache_creation": 0, "ephemeral_5m_input_tokens": 0},
        )
    )
    assert (
        _printed(handler, capsys) == "\U0001f4ca Token usage: 100 in / 50 out (1 call)"
    )
