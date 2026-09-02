"""Tests for ruff security rules enforcement (FR-222).

Verifies that the ruff S ruleset (flake8-bandit) is enabled in pyproject.toml
and passes clean on the yamlgraph/ codebase. All legitimate security-sensitive
patterns must be suppressed with documented noqa confessions.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestRuffSecurityConfig:
    """Verify ruff S ruleset is enabled in pyproject.toml."""

    @pytest.mark.req("REQ-YG-222")
    def test_ruff_config_includes_s_ruleset(self):
        """pyproject.toml [tool.ruff.lint] select must include 'S'."""
        pyproject = REPO_ROOT / "pyproject.toml"
        content = pyproject.read_text(encoding="utf-8")
        # Check that "S" appears in the select list (as a standalone entry)
        assert '"S"' in content or "'S'" in content, (
            "Ruff S ruleset (flake8-bandit) not found in "
            "[tool.ruff.lint] select in pyproject.toml. "
            "FR-222 requires security rules to be enabled."
        )


class TestRuffSecurityExecution:
    """Verify ruff S rules pass clean on the codebase."""

    @pytest.mark.req("REQ-YG-222")
    def test_ruff_security_rules_pass(self):
        """ruff check --select S must exit 0 on yamlgraph/."""
        ruff = Path(sys.executable).parent / "ruff"
        result = subprocess.run(
            [str(ruff), "check", "--select", "S", "yamlgraph/"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, (
            f"ruff check --select S failed with exit code {result.returncode}.\n"
            f"Unsuppressed security violations:\n{result.stdout}"
        )

    @pytest.mark.req("REQ-YG-222")
    def test_ruff_full_check_still_passes(self):
        """Full ruff check (all enabled rules) must still pass."""
        ruff = Path(sys.executable).parent / "ruff"
        result = subprocess.run(
            [str(ruff), "check", "yamlgraph/"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, (
            f"ruff check failed with exit code {result.returncode}.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
