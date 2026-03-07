"""Unit tests for enforce detection logic (FR-114).

Tests SHA state file read/write and feature request detection via
git diff between stored and current HEAD SHAs.
"""

import subprocess

import pytest


@pytest.mark.req("REQ-YG-114")
class TestReadEnforceSha:
    """Tests for read_enforce_sha()."""

    def test_returns_file_content(self, tmp_path):
        """Reads SHA string from state file."""
        from yamlgraph.utils.worktree_helpers import read_enforce_sha

        state_file = tmp_path / ".last-enforce-sha"
        state_file.write_text("abc123def\n")
        result = read_enforce_sha(str(state_file))
        assert result == "abc123def"

    def test_returns_none_when_file_missing(self, tmp_path):
        """Returns None when state file does not exist."""
        from yamlgraph.utils.worktree_helpers import read_enforce_sha

        result = read_enforce_sha(str(tmp_path / "nonexistent"))
        assert result is None

    def test_strips_whitespace(self, tmp_path):
        """Strips trailing newline and whitespace from SHA."""
        from yamlgraph.utils.worktree_helpers import read_enforce_sha

        state_file = tmp_path / ".last-enforce-sha"
        state_file.write_text("  abc123  \n")
        result = read_enforce_sha(str(state_file))
        assert result == "abc123"

    def test_returns_none_for_empty_file(self, tmp_path):
        """Returns None when state file is empty."""
        from yamlgraph.utils.worktree_helpers import read_enforce_sha

        state_file = tmp_path / ".last-enforce-sha"
        state_file.write_text("")
        result = read_enforce_sha(str(state_file))
        assert result is None


@pytest.mark.req("REQ-YG-114")
class TestWriteEnforceSha:
    """Tests for write_enforce_sha()."""

    def test_creates_file_with_sha(self, tmp_path):
        """Creates state file with SHA content."""
        from yamlgraph.utils.worktree_helpers import write_enforce_sha

        state_file = tmp_path / ".last-enforce-sha"
        write_enforce_sha(str(state_file), "abc123def")
        assert state_file.read_text().strip() == "abc123def"

    def test_overwrites_existing(self, tmp_path):
        """Overwrites existing SHA in state file."""
        from yamlgraph.utils.worktree_helpers import write_enforce_sha

        state_file = tmp_path / ".last-enforce-sha"
        state_file.write_text("old_sha\n")
        write_enforce_sha(str(state_file), "new_sha")
        assert state_file.read_text().strip() == "new_sha"

    def test_creates_parent_directories(self, tmp_path):
        """Creates parent directories if they don't exist."""
        from yamlgraph.utils.worktree_helpers import write_enforce_sha

        state_file = tmp_path / "nested" / "dir" / ".last-enforce-sha"
        write_enforce_sha(str(state_file), "abc123")
        assert state_file.read_text().strip() == "abc123"


@pytest.mark.req("REQ-YG-114")
class TestDetectNewFeatureRequests:
    """Tests for detect_new_feature_requests()."""

    def test_returns_matching_fr_files(self, monkeypatch):
        """Detects FR files added between two SHAs."""
        from yamlgraph.utils.worktree_helpers import detect_new_feature_requests

        def mock_run(cmd, **kwargs):
            return subprocess.CompletedProcess(
                cmd,
                returncode=0,
                stdout="feature-requests/FR-107-new-feature.md\n",
                stderr="",
            )

        monkeypatch.setattr(subprocess, "run", mock_run)
        result = detect_new_feature_requests("sha1", "sha2")
        assert result == ["feature-requests/FR-107-new-feature.md"]

    def test_excludes_template(self, monkeypatch):
        """TEMPLATE.md is excluded from detection."""
        from yamlgraph.utils.worktree_helpers import detect_new_feature_requests

        def mock_run(cmd, **kwargs):
            return subprocess.CompletedProcess(
                cmd,
                returncode=0,
                stdout="feature-requests/TEMPLATE.md\nfeature-requests/FR-107-test.md\n",
                stderr="",
            )

        monkeypatch.setattr(subprocess, "run", mock_run)
        result = detect_new_feature_requests("sha1", "sha2")
        assert result == ["feature-requests/FR-107-test.md"]

    def test_excludes_readme(self, monkeypatch):
        """README.md is excluded from detection."""
        from yamlgraph.utils.worktree_helpers import detect_new_feature_requests

        def mock_run(cmd, **kwargs):
            return subprocess.CompletedProcess(
                cmd,
                returncode=0,
                stdout="feature-requests/README.md\nfeature-requests/FR-108-real.md\n",
                stderr="",
            )

        monkeypatch.setattr(subprocess, "run", mock_run)
        result = detect_new_feature_requests("sha1", "sha2")
        assert result == ["feature-requests/FR-108-real.md"]

    def test_returns_empty_when_shas_match(self, monkeypatch):
        """Returns empty list when from_sha equals to_sha."""
        from yamlgraph.utils.worktree_helpers import detect_new_feature_requests

        result = detect_new_feature_requests("same_sha", "same_sha")
        assert result == []

    def test_returns_empty_when_no_fr_changes(self, monkeypatch):
        """Returns empty list when changes are outside feature-requests/."""
        from yamlgraph.utils.worktree_helpers import detect_new_feature_requests

        def mock_run(cmd, **kwargs):
            return subprocess.CompletedProcess(
                cmd,
                returncode=0,
                stdout="",
                stderr="",
            )

        monkeypatch.setattr(subprocess, "run", mock_run)
        result = detect_new_feature_requests("sha1", "sha2")
        assert result == []

    def test_matches_fr_pattern_only(self, monkeypatch):
        """Only files matching FR-[0-9]+- pattern are detected."""
        from yamlgraph.utils.worktree_helpers import detect_new_feature_requests

        def mock_run(cmd, **kwargs):
            return subprocess.CompletedProcess(
                cmd,
                returncode=0,
                stdout=(
                    "feature-requests/FR-107-valid.md\n"
                    "feature-requests/draft-something.md\n"
                    "feature-requests/038-feat-old-style.md\n"
                    "feature-requests/FR-invalid.md\n"
                ),
                stderr="",
            )

        monkeypatch.setattr(subprocess, "run", mock_run)
        result = detect_new_feature_requests("sha1", "sha2")
        assert result == ["feature-requests/FR-107-valid.md"]

    def test_returns_multiple_frs(self, monkeypatch):
        """Multiple FRs in a single push are all detected."""
        from yamlgraph.utils.worktree_helpers import detect_new_feature_requests

        def mock_run(cmd, **kwargs):
            return subprocess.CompletedProcess(
                cmd,
                returncode=0,
                stdout=(
                    "feature-requests/FR-107-feature-a.md\n"
                    "feature-requests/FR-108-feature-b.md\n"
                ),
                stderr="",
            )

        monkeypatch.setattr(subprocess, "run", mock_run)
        result = detect_new_feature_requests("sha1", "sha2")
        assert len(result) == 2
        assert "feature-requests/FR-107-feature-a.md" in result
        assert "feature-requests/FR-108-feature-b.md" in result

    def test_passes_correct_git_command(self, monkeypatch):
        """Invokes git diff with correct arguments."""
        from yamlgraph.utils.worktree_helpers import detect_new_feature_requests

        captured_cmd = []

        def mock_run(cmd, **kwargs):
            captured_cmd.extend(cmd)
            return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

        monkeypatch.setattr(subprocess, "run", mock_run)
        detect_new_feature_requests("sha_a", "sha_b")
        assert captured_cmd == [
            "git", "diff", "--name-only", "sha_a", "sha_b",
            "--", "feature-requests/",
        ]
