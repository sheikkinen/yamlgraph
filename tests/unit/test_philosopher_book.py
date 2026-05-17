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
def test_load_trap_returns_single_trap():
    """load_trap with chapter_num returns exactly one trap dict."""
    from examples.demos.philosopher_book.tools import load_trap

    result = load_trap({"chapter_num": 5})
    assert "trap" in result
    trap = result["trap"]
    assert trap["chapter_num"] == 5
    assert "trap_name" in trap
    assert "definition" in trap
    assert "cure" in trap


@pytest.mark.req("REQ-YG-404")
def test_load_trap_requires_chapter_num():
    """load_trap raises ValueError if chapter_num missing."""
    from examples.demos.philosopher_book.tools import load_trap

    with pytest.raises(ValueError, match="chapter_num is required"):
        load_trap({})


@pytest.mark.req("REQ-YG-404")
def test_load_trap_out_of_range():
    """load_trap raises ValueError for chapter_num > 21."""
    from examples.demos.philosopher_book.tools import load_trap

    with pytest.raises(ValueError, match="out of range"):
        load_trap({"chapter_num": 99})


@pytest.mark.req("REQ-YG-404")
def test_save_chapter_writes_file(tmp_path):
    """save_chapter writes chapter text to chapters/ subdir."""
    from examples.demos.philosopher_book.tools import save_chapter

    state = {
        "trap": {"chapter_num": 5, "trap_name": "false_duplicate"},
        "chapter_text": "# Chapter 5\n\nContent here.",
        "output_dir": str(tmp_path),
    }
    save_chapter(state)
    out = tmp_path / "chapters" / "ch-05-false_duplicate.md"
    assert out.exists()
    assert "Content here." in out.read_text()


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

    content = read_file({}, path=".github/copilot-instructions.md")
    assert len(content) <= 8000


@pytest.mark.req("REQ-YG-404")
def test_load_trap_list_single_chapter():
    """chapter_num in state returns only that one chapter."""
    from examples.demos.philosopher_book.tools import load_trap_list

    result = load_trap_list({"chapter_num": 5})
    chapters = result["trap_chapters"]
    assert len(chapters) == 1
    assert chapters[0]["chapter_num"] == 5


@pytest.mark.req("REQ-YG-404")
def test_load_trap_list_chapter_num_zero_returns_all():
    """chapter_num=0 (default) returns all 21 chapters."""
    from examples.demos.philosopher_book.tools import load_trap_list

    result = load_trap_list({"chapter_num": 0})
    assert len(result["trap_chapters"]) == 21


@pytest.mark.req("REQ-YG-404")
def test_assemble_book_reads_saved_chapter_files(tmp_path):
    """assemble_book prefers saved chapter files over state list."""
    from examples.demos.philosopher_book.tools import assemble_book

    chapters_dir = tmp_path / "chapters"
    chapters_dir.mkdir()
    (chapters_dir / "ch-01-downstream_fix.md").write_text(
        "# Chapter 1\n\nSaved content.", encoding="utf-8"
    )

    state = {
        "trap_chapters": [
            {
                "chapter_num": 1,
                "trap_name": "downstream_fix",
                "title": "Where You Guard Is Where You Failed",
                "part": "Part I",
            }
        ],
        "chapters": ["stale state content"],
        "epilogue": "",
        "output_dir": str(tmp_path),
    }
    result = assemble_book(state)
    content = Path(result["assembled_path"]).read_text()
    assert "Saved content." in content
    assert "stale state content" not in content


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


@pytest.mark.req("REQ-YG-405")
def test_load_chapters_snapshots_and_sorts_markdown_files(tmp_path, monkeypatch):
    from examples.demos.philosopher_book import tools

    monkeypatch.setattr(tools, "REPO_ROOT", tmp_path)
    input_dir = tmp_path / "drafts"
    output_dir = tmp_path / "edited"
    input_dir.mkdir()
    (input_dir / "ch-02-second.md").write_text("# Chapter 2\n\nSecond text.", "utf-8")
    (input_dir / "ch-01-first.md").write_text("# Chapter 1\n\nFirst text.", "utf-8")
    (input_dir / "notes.txt").write_text("ignored", "utf-8")

    result = tools.load_chapters(
        {"input_dir": "drafts", "output_dir": "edited", "glob_pattern": "*.md"}
    )

    chapters = result["chapters"]
    assert [chapter["filename"] for chapter in chapters] == [
        "ch-01-first.md",
        "ch-02-second.md",
    ]
    assert chapters[0]["chapter_num"] == 1
    assert chapters[0]["title"] == "Chapter 1"
    assert chapters[0]["word_count"] == 4
    assert (output_dir / "_input_snapshot" / "ch-01-first.md").exists()


@pytest.mark.req("REQ-YG-405")
def test_load_chapters_rejects_path_traversal(tmp_path, monkeypatch):
    from examples.demos.philosopher_book import tools

    monkeypatch.setattr(tools, "REPO_ROOT", tmp_path)

    with pytest.raises(ValueError, match="outside repository"):
        tools.load_chapters({"input_dir": "../outside", "output_dir": "edited"})


@pytest.mark.req("REQ-YG-405")
def test_load_chapters_raises_for_empty_input(tmp_path, monkeypatch):
    from examples.demos.philosopher_book import tools

    monkeypatch.setattr(tools, "REPO_ROOT", tmp_path)
    (tmp_path / "drafts").mkdir()

    with pytest.raises(ValueError, match="No chapter files found"):
        tools.load_chapters({"input_dir": "drafts", "output_dir": "edited"})


@pytest.mark.req("REQ-YG-405")
def test_save_edited_chapters_preserves_filenames_and_originals(tmp_path, monkeypatch):
    from examples.demos.philosopher_book import tools

    monkeypatch.setattr(tools, "REPO_ROOT", tmp_path)
    input_dir = tmp_path / "drafts"
    input_dir.mkdir()
    original = input_dir / "ch-01-first.md"
    original.write_text("# Chapter 1\n\nOriginal text.", "utf-8")

    state = {
        "input_dir": "drafts",
        "output_dir": "edited",
        "chapters": [
            {
                "filename": "ch-01-first.md",
                "text": "# Chapter 1\n\nOriginal text.",
                "word_count": 4,
            }
        ],
        "edited_chapters": [
            {
                "_map_index": 0,
                "edited_markdown": "# Chapter 1\n\nEdited text.",
                "editorial_notes": ["Cut repetition."],
                "compression_summary": "Shortened.",
            }
        ],
    }

    result = tools.save_edited_chapters(state)

    edited = tmp_path / "edited" / "ch-01-first.md"
    assert edited.read_text("utf-8") == "# Chapter 1\n\nEdited text.\n"
    assert original.read_text("utf-8") == "# Chapter 1\n\nOriginal text."
    assert result["saved_chapters"][0]["filename"] == "ch-01-first.md"
    assert result["saved_chapters"][0]["original_word_count"] == 4
    assert result["saved_chapters"][0]["edited_word_count"] == 4


@pytest.mark.req("REQ-YG-405")
def test_save_edited_chapters_rejects_input_output_collision(tmp_path, monkeypatch):
    from examples.demos.philosopher_book import tools

    monkeypatch.setattr(tools, "REPO_ROOT", tmp_path)
    (tmp_path / "drafts").mkdir()

    with pytest.raises(ValueError, match="must differ"):
        tools.save_edited_chapters(
            {
                "input_dir": "drafts",
                "output_dir": "drafts",
                "chapters": [],
                "edited_chapters": [],
            }
        )


@pytest.mark.req("REQ-YG-405")
def test_write_editorial_report_includes_counts_and_notes(tmp_path, monkeypatch):
    from examples.demos.philosopher_book import tools

    monkeypatch.setattr(tools, "REPO_ROOT", tmp_path)
    state = {
        "output_dir": "edited",
        "editorial_brief": {
            "summary": "Reduce repeated NC-291 examples.",
            "global_constraints": ["Preserve voice."],
        },
        "saved_chapters": [
            {
                "filename": "ch-01-first.md",
                "original_word_count": 100,
                "edited_word_count": 75,
                "compression_ratio": 0.25,
                "editorial_notes": ["Removed repeated aphorisms."],
                "compression_summary": "Compressed by one quarter.",
            }
        ],
    }

    result = tools.write_editorial_report(state)

    report = Path(result["editorial_report_path"])
    content = report.read_text("utf-8")
    assert "Reduce repeated NC-291 examples." in content
    assert "ch-01-first.md" in content
    assert "25.0%" in content
    assert "Removed repeated aphorisms." in content


@pytest.mark.req("REQ-YG-405")
def test_editorial_graph_and_prompts_exist():
    assert (DEMO_DIR / "editorial_graph.yaml").exists()
    assert (DEMO_DIR / "prompts" / "editorial_brief.yaml").exists()
    assert (DEMO_DIR / "prompts" / "edit_chapter.yaml").exists()
