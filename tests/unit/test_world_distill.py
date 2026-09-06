#!/usr/bin/env python3


"""FR-744: world_distill — witnesses (REQ-YG-563).

Pins (judgement 2026-07-17):
- F2/Commandment 6: zero surviving articles RAISES — never a polite
  empty world (the daily_digest exhibit: 100% payload loss exited 0).
- F3: distill input capped — title + source + ≤500-char excerpt.
- F1: the FILE contract is dated header + prose (philosopher slurps);
  the schema binds the distill node's envelope, not the file.
- Deps fail with a naming error at import (the resend/feedparser
  exhibit: the digest was DOA on its least essential dependency).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.process

REPO = Path(__file__).resolve().parents[2]
TOOLS = REPO / "graphs/world_distill/tools.py"


def _load_tools():
    spec = importlib.util.spec_from_file_location("wd_tools", TOOLS)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["wd_tools"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.req("REQ-YG-563")
def test_zero_yield_raises():
    """Commandment 6: when the filter yields nothing, raise."""
    wd = _load_tools()
    with pytest.raises(ValueError, match="[Zz]ero|[Nn]o articles"):
        wd.prepare_distill_input({"articles": []})


@pytest.mark.req("REQ-YG-563")
def test_excerpt_cap_500_chars():
    """F3: title + source + ≤500-char excerpt per article, never full content."""
    wd = _load_tools()
    articles = [
        {"title": "T1", "source": "hn", "content": "x" * 5000},
        {"title": "T2", "source": "rss", "content": "y" * 100},
    ]
    out = wd.prepare_distill_input({"articles": articles})
    text = out["distill_input"]
    assert "T1" in text and "T2" in text
    assert "x" * 501 not in text
    assert "x" * 400 in text  # excerpt present, not dropped


@pytest.mark.req("REQ-YG-563")
def test_write_context_dated_header(tmp_path):
    """F1: dated header + prose sections — the slurp contract."""
    wd = _load_tools()
    distilled = {
        "highlights": ["LangGraph 2.0 released"],
        "themes": ["evaluation-as-code"],
        "open_questions": ["what replaces RAG?"],
    }
    out_path = tmp_path / "world-context.md"
    result = wd.write_context(
        {"distilled": distilled, "output_path": str(out_path), "date": "2026-07-17"}
    )
    assert result["written"] is True
    text = out_path.read_text(encoding="utf-8")
    assert "Last updated: 2026-07-17" in text
    assert "LangGraph 2.0 released" in text
    assert "evaluation-as-code" in text


@pytest.mark.req("REQ-YG-563")
def test_write_context_refuses_empty_distill(tmp_path):
    """Commandment 6 at the write boundary: an empty distill result must
    not overwrite the world with nothing."""
    wd = _load_tools()
    with pytest.raises(ValueError):
        wd.write_context(
            {
                "distilled": {"highlights": [], "themes": [], "open_questions": []},
                "output_path": str(tmp_path / "w.md"),
                "date": "2026-07-17",
            }
        )
