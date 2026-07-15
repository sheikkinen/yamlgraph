"""FR-736 WebLLM demo trace capture — lexical page tests.

Judgement pins witnessed here: F1 wire-fidelity (evidence header prints
the system prompt from the same `prompt` object the request uses),
F2 pipe+newline escaping for input_head, F3 single-identifier messages
array, F4 finish_reason in the tally table.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_HTML = REPO_ROOT / "docs" / "demos" / "webllm" / "index.html"


@pytest.fixture(scope="module")
def html() -> str:
    return INDEX_HTML.read_text()


@pytest.mark.req("REQ-YG-562")
class TestTraceObject:
    """AC-01 — full request/response pair captured per run."""

    def test_trace_keys_present(self, html):
        for key in ('"request"', '"response"', "finish_reason"):
            assert key in html, f"missing trace surface: {key}"

    def test_save_trace_link(self, html):
        assert "-trace.json" in html
        assert 'id="save-trace"' in html


@pytest.mark.req("REQ-YG-562")
class TestSingleIdentifierRequest:
    """F3 — the messages array is built once and flows everywhere."""

    def test_system_role_built_once(self, html):
        assert html.count('role: "system"') == 1

    def test_create_uses_shorthand(self, html):
        assert "messages," in html

    def test_trace_references_same_identifier(self, html):
        assert "request: { messages" in html


@pytest.mark.req("REQ-YG-562")
class TestWireFidelity:
    """F1 — the evidence header prints what was actually sent."""

    def test_system_prompt_in_evidence_header(self, html):
        assert "## system prompt (as sent)" in html

    def test_prompt_object_is_the_source(self, html):
        # prompt.system feeds both the messages array and the evidence
        # renderer — same object, no copy.
        assert html.count("prompt.system") >= 2


@pytest.mark.req("REQ-YG-562")
class TestStimulusColumns:
    """F4 tally shape + F2 escaping."""

    def test_tally_header_with_finish_and_input(self, html):
        assert (
            "| run | schema_valid | score | finish | ms | tok/s "
            "| input_chars | input_head | raw_chars |" in html
        )

    def test_input_head_escapes_pipes_and_newlines(self, html):
        assert 'replaceAll("|"' in html
        assert 'replaceAll("\\n"' in html
