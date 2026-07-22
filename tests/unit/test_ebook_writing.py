"""Tests for examples/ebook/nodes/writing.py — eBook chapter writing tool.

FR-100: YAMLGraph Development Pipeline eBook.
REQ-YG-091: write_chapters_tool writes formatted chapter content to disk.
"""

import pytest

pytestmark = pytest.mark.process


class TestWriteChaptersTool:
    """Test suite for write_chapters_tool."""

    @pytest.mark.req("REQ-YG-091")
    def test_writes_chapters_to_output_dir(self, tmp_path):
        """Should write all chapter content to the output directory."""
        from examples.ebook.nodes.writing import write_chapters_tool

        state = {
            "output_dir": str(tmp_path),
            "chapter_introduction": "# Introduction\n\nThis is the intro.",
            "chapter_doctrine": "# Doctrine\n\nThe 10 Commandments.",
            "chapter_precommit": "# Pre-commit Gates\n\nHooks table.",
            "chapter_chaplain": "# Chaplain Pipeline\n\nWatch loop.",
            "chapter_inquisitor": "# Inquisitor\n\nAudit loop.",
            "chapter_diary": "# Diary System\n\nSchema and rotation.",
        }

        result = write_chapters_tool(state)

        assert "written" in result
        assert len(result["written"]) == 6

        # Check files exist with correct content
        assert (tmp_path / "00-introduction.md").read_text() == state[
            "chapter_introduction"
        ]
        assert (tmp_path / "01-doctrine.md").read_text() == state["chapter_doctrine"]
        assert (tmp_path / "02-precommit-gates.md").read_text() == state[
            "chapter_precommit"
        ]
        assert (tmp_path / "03-chaplain-pipeline.md").read_text() == state[
            "chapter_chaplain"
        ]
        assert (tmp_path / "04-inquisitor.md").read_text() == state[
            "chapter_inquisitor"
        ]
        assert (tmp_path / "05-diary-system.md").read_text() == state["chapter_diary"]

    @pytest.mark.req("REQ-YG-091")
    def test_creates_output_dir_if_missing(self, tmp_path):
        """Should create output directory if it doesn't exist."""
        from examples.ebook.nodes.writing import write_chapters_tool

        nested_dir = tmp_path / "nested" / "ebook"
        state = {
            "output_dir": str(nested_dir),
            "chapter_introduction": "# Intro",
            "chapter_doctrine": "",
            "chapter_precommit": "",
            "chapter_chaplain": "",
            "chapter_inquisitor": "",
            "chapter_diary": "",
        }

        write_chapters_tool(state)

        assert nested_dir.exists()
        assert (nested_dir / "00-introduction.md").exists()

    @pytest.mark.req("REQ-YG-091")
    def test_returns_written_paths(self, tmp_path):
        """Should return list of written file paths."""
        from examples.ebook.nodes.writing import write_chapters_tool

        state = {
            "output_dir": str(tmp_path),
            "chapter_introduction": "# Intro",
            "chapter_doctrine": "# Doc",
            "chapter_precommit": "# Pre",
            "chapter_chaplain": "# Chap",
            "chapter_inquisitor": "# Inq",
            "chapter_diary": "# Diary",
        }

        result = write_chapters_tool(state)

        expected_paths = [
            str(tmp_path / "00-introduction.md"),
            str(tmp_path / "01-doctrine.md"),
            str(tmp_path / "02-precommit-gates.md"),
            str(tmp_path / "03-chaplain-pipeline.md"),
            str(tmp_path / "04-inquisitor.md"),
            str(tmp_path / "05-diary-system.md"),
        ]
        assert result["written"] == expected_paths

    @pytest.mark.req("REQ-YG-091")
    def test_skips_empty_chapters(self, tmp_path):
        """Should skip writing chapters with empty content."""
        from examples.ebook.nodes.writing import write_chapters_tool

        state = {
            "output_dir": str(tmp_path),
            "chapter_introduction": "# Intro",
            "chapter_doctrine": "",  # Empty - should skip
            "chapter_precommit": None,  # None - should skip
            "chapter_chaplain": "# Chaplain",
            "chapter_inquisitor": "",
            "chapter_diary": "# Diary",
        }

        result = write_chapters_tool(state)

        # Only 3 chapters with content
        assert len(result["written"]) == 3
        assert not (tmp_path / "01-doctrine.md").exists()
        assert not (tmp_path / "02-precommit-gates.md").exists()
        assert not (tmp_path / "04-inquisitor.md").exists()
