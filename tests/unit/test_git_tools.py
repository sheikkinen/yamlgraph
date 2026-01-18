"""Tests for git analysis tools."""

from yamlgraph.tools.analysis.git_tools import git_blame, git_log


class TestGitBlame:
    """Tests for git_blame function."""

    def test_returns_author_for_valid_line(self):
        """Returns author info for a valid file/line."""
        # Use a known file in the project
        result = git_blame("yamlgraph/__init__.py", 1)

        assert "error" not in result
        assert "author" in result
        assert "date" in result
        assert "commit" in result
        assert isinstance(result["author"], str)
        assert len(result["author"]) > 0

    def test_returns_commit_message(self):
        """Returns commit message summary."""
        result = git_blame("yamlgraph/__init__.py", 1)

        assert "error" not in result
        assert "summary" in result
        assert isinstance(result["summary"], str)

    def test_returns_error_for_invalid_file(self):
        """Returns error for non-existent file."""
        result = git_blame("nonexistent/file.py", 1)

        assert "error" in result
        assert (
            "not found" in result["error"].lower() or "fatal" in result["error"].lower()
        )

    def test_returns_error_for_invalid_line(self):
        """Returns error for line beyond file length."""
        result = git_blame("yamlgraph/__init__.py", 99999)

        assert "error" in result

    def test_returns_line_content(self):
        """Returns the actual line content."""
        result = git_blame("yamlgraph/__init__.py", 1)

        assert "error" not in result
        assert "line_content" in result
        assert isinstance(result["line_content"], str)


class TestGitLog:
    """Tests for git_log function."""

    def test_returns_recent_commits(self):
        """Returns list of recent commits for file."""
        result = git_log("yamlgraph/__init__.py")

        assert "error" not in result
        assert "commits" in result
        assert isinstance(result["commits"], list)
        assert len(result["commits"]) > 0

    def test_each_commit_has_required_fields(self):
        """Each commit has hash, author, date, message."""
        result = git_log("yamlgraph/__init__.py")

        assert "error" not in result
        for commit in result["commits"]:
            assert "hash" in commit
            assert "author" in commit
            assert "date" in commit
            assert "message" in commit

    def test_respects_n_limit(self):
        """Returns at most n commits."""
        result = git_log("yamlgraph/__init__.py", n=2)

        assert "error" not in result
        assert len(result["commits"]) <= 2

    def test_returns_error_for_invalid_file(self):
        """Returns error for non-existent file."""
        result = git_log("nonexistent/file.py")

        assert "error" in result

    def test_returns_error_for_untracked_file(self):
        """Returns error for file not in git."""
        # Create a temp file that won't be tracked
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"# temp file")
            temp_path = f.name

        try:
            result = git_log(temp_path)
            # Should either error or return empty commits
            assert "error" in result or len(result.get("commits", [])) == 0
        finally:
            Path(temp_path).unlink()

    def test_default_n_is_5(self):
        """Default returns up to 5 commits."""
        result = git_log("yamlgraph/__init__.py")

        assert "error" not in result
        # Can be less than 5 if file has fewer commits
        assert len(result["commits"]) <= 5
