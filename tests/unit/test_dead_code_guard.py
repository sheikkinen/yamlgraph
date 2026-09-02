"""Guard tests for FR-162: Vulture Dead Code Cleanup.

These tests ensure dead code stays dead and the vulture whitelist
is properly maintained.
"""

import importlib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.req("REQ-YG-046")
class TestDeadCodeRemoval:
    """Verify that genuinely dead code has been removed."""

    def test_sanitize_module_does_not_exist(self):
        """sanitize.py was dead code — it must not exist."""
        sanitize_path = PROJECT_ROOT / "yamlgraph" / "utils" / "sanitize.py"
        assert (
            not sanitize_path.exists()
        ), f"Dead code module still exists: {sanitize_path}"

    def test_sanitize_module_not_importable(self):
        """Importing the deleted module must raise ModuleNotFoundError."""
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("yamlgraph.utils.sanitize")

    def test_sanitize_tests_do_not_exist(self):
        """Orphaned tests for dead code must be removed."""
        test_path = PROJECT_ROOT / "tests" / "unit" / "test_sanitize.py"
        assert not test_path.exists(), f"Orphaned test file still exists: {test_path}"


@pytest.mark.req("REQ-YG-046")
class TestVultureWhitelist:
    """Verify the vulture whitelist is properly configured."""

    def test_whitelist_file_exists(self):
        """vulture_whitelist.py must exist at project root."""
        whitelist_path = PROJECT_ROOT / "vulture_whitelist.py"
        assert whitelist_path.exists(), "vulture_whitelist.py missing at project root"

    def test_whitelist_contains_worktree_helpers(self):
        """Whitelist must suppress worktree_helpers false positives."""
        whitelist_path = PROJECT_ROOT / "vulture_whitelist.py"
        content = whitelist_path.read_text(encoding="utf-8")
        assert "derive_branch_name" in content
        assert "construct_worktree_path" in content
        assert "validate_clean_working_tree" in content
