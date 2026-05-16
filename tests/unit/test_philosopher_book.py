"""Tests for FR-404 Philosopher's Book demo tools."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DEMO_DIR = ROOT / "examples" / "demos" / "philosopher_book"


@pytest.mark.req("REQ-YG-404")
def test_load_trap_list_returns_21_chapters():
    from examples.demos.philosopher_book.tools import load_trap_list

    result = load_trap_list({})
    assert isinstance(result, dict)
    assert "trap_chapters" in result
    assert len(result["trap_chapters"]) == 21


@pytest.mark.req("REQ-YG-404")
def test_load_trap_list_part_assignments():
    from examples.demos.philosopher_book.tools import load_trap_list

    result = load_trap_list({})
    chapters = result["trap_chapters"]
    part_i = [c for c in chapters if c["part"] == "Part I"]
    part_v = [c for c in chapters if c["part"] == "Part V"]
    assert len(part_i) == 6
    assert len(part_v) == 2


@pytest.mark.req("REQ-YG-404")
def test_load_trap_list_has_required_keys():
    from examples.demos.philosopher_book.tools import load_trap_list

    result = load_trap_list({})
    for ch in result["trap_chapters"]:
        assert "trap_name" in ch
        assert "definition" in ch
        assert "cure" in ch
        assert "part" in ch
        assert "chapter_num" in ch
        assert "title" in ch


@pytest.mark.req("REQ-YG-404")
def test_search_diary_returns_list():
    from examples.demos.philosopher_book.tools import search_diary

    results = search_diary({}, query="downstream_fix")
    assert isinstance(results, list)


@pytest.mark.req("REQ-YG-404")
def test_search_diary_max_results():
    from examples.demos.philosopher_book.tools import search_diary

    results = search_diary({}, query="audit", max_results=3)
    assert len(results) <= 3


@pytest.mark.req("REQ-YG-404")
def test_read_file_allowed_path():
    from examples.demos.philosopher_book.tools import read_file

    content = read_file({}, path="docs/letter-to-the-philosopher.md")
    assert isinstance(content, str)
    assert len(content) > 0


@pytest.mark.req("REQ-YG-404")
def test_read_file_disallowed_path():
    from examples.demos.philosopher_book.tools import read_file

    with pytest.raises(ValueError):
        read_file({}, path="/etc/passwd")


@pytest.mark.req("REQ-YG-404")
def test_read_file_truncates():
    from examples.demos.philosopher_book.tools import read_file

    # Any large file should be truncated to 8000 chars
    # Use .github/copilot-instructions.md which is definitely > 8000 chars
    content = read_file({}, path=".github/copilot-instructions.md")
    assert len(content) <= 8000


@pytest.mark.req("REQ-YG-404")
def test_assemble_book_creates_file(tmp_path):
    from examples.demos.philosopher_book.tools import assemble_book

    state = {
        "trap_chapters": [
            {
                "chapter_num": 1,
                "trap_name": "test_trap",
                "title": "Test Chapter",
                "part": "Part I",
            }
        ],
        "chapters": ["# Chapter 1\n\nTest content."],
        "epilogue": "# Epilogue\n\nThe One Law.",
        "output_dir": str(tmp_path),
    }
    result = assemble_book(state)
    assert "assembled_path" in result
    assert Path(result["assembled_path"]).exists()


@pytest.mark.req("REQ-YG-404")
def test_assemble_book_includes_toc(tmp_path):
    from examples.demos.philosopher_book.tools import assemble_book

    state = {
        "trap_chapters": [
            {
                "chapter_num": 1,
                "trap_name": "downstream_fix",
                "title": "Where You Guard Is Where You Failed",
                "part": "Part I",
            },
            {
                "chapter_num": 2,
                "trap_name": "symptom_patch",
                "title": "The Root You Didn't Trace",
                "part": "Part I",
            },
        ],
        "chapters": ["# Chapter 1\n\nContent.", "# Chapter 2\n\nContent."],
        "epilogue": "# Epilogue\n\nThe One Law.",
        "output_dir": str(tmp_path),
    }
    result = assemble_book(state)
    content = Path(result["assembled_path"]).read_text()
    assert "Table of Contents" in content or "Contents" in content
