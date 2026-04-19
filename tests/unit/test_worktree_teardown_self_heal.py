"""Condemning tests for FR-241: Complete worktree teardown self-heal.

Three gaps proven by these tests:

1. ``validate_editable_install()`` does not exist in ``worktree_helpers.py``
2. ``enforce_worktree.sh`` cleanup has no import validation after ``.pth`` cleaning
3. ``bugfix_worktree.sh`` cleanup lacks FR-174 guards entirely
   (no ``clean_stale_pth_entries``, no ``validate_venv_health`` before symlink,
   no ``validate_venv_symlink`` after symlink, no import validation)
"""

from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Gap 1: validate_editable_install() does not exist
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-244")
class TestValidateEditableInstall:
    """validate_editable_install() must exist and correctly probe import health."""

    def test_function_exists(self) -> None:
        """worktree_helpers must expose validate_editable_install."""
        from yamlgraph.utils import worktree_helpers

        assert hasattr(
            worktree_helpers, "validate_editable_install"
        ), "worktree_helpers must expose validate_editable_install"

    def test_returns_false_for_unimportable_package(self) -> None:
        """Returns False when the target package cannot be imported."""
        from yamlgraph.utils.worktree_helpers import validate_editable_install

        result = validate_editable_install(package="nonexistent_pkg_xyz_999")
        assert result is False

    def test_returns_true_for_importable_package(self) -> None:
        """Returns True when the target package can be imported (e.g. 'os')."""
        from yamlgraph.utils.worktree_helpers import validate_editable_install

        result = validate_editable_install(package="os")
        assert result is True

    def test_uses_same_python_as_caller(self) -> None:
        """The check must use sys.executable, not an arbitrary python3."""
        from yamlgraph.utils.worktree_helpers import validate_editable_install

        # If the function exists and works, it should use subprocess with
        # sys.executable so that venv isolation is respected.
        # We just confirm it doesn't crash and returns a bool.
        result = validate_editable_install(package="json")
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# Gap 2: enforce_worktree.sh cleanup lacks import validation
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-244")
class TestEnforceWorktreeImportGuard:
    """enforce_worktree.sh cleanup() must validate 'import yamlgraph' after
    worktree removal and .pth cleaning."""

    @pytest.fixture()
    def enforce_script(self) -> str:
        """Read the enforce_worktree.sh script."""
        script = Path("scripts/enforce_worktree.sh")
        assert script.is_file(), "enforce_worktree.sh must exist"
        return script.read_text()

    def test_cleanup_has_import_validation(self, enforce_script: str) -> None:
        """cleanup() must include an 'import yamlgraph' check after .pth cleaning."""
        # The cleanup function should validate the editable install is healthy
        # after removing stale .pth entries.  FR-174 added .pth cleaning but
        # not import validation — that's the gap.
        assert "import yamlgraph" in enforce_script, (
            "enforce_worktree.sh cleanup() must validate editable install "
            "via 'import yamlgraph' after worktree removal"
        )

    def test_cleanup_has_self_heal_reinstall(self, enforce_script: str) -> None:
        """cleanup() must auto-reinstall when import validation fails."""
        assert "pip install -e" in enforce_script, (
            "enforce_worktree.sh cleanup() must self-heal with "
            "'pip install -e' when import validation fails"
        )


# ---------------------------------------------------------------------------
# Gap 3: bugfix_worktree.sh lacks FR-174 guards
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-244")
class TestBugfixWorktreeFR174Parity:
    """bugfix_worktree.sh must have FR-174 guards at parity with
    enforce_worktree.sh: venv health, symlink validation, .pth cleaning,
    and import validation in cleanup."""

    @pytest.fixture()
    def bugfix_script(self) -> str:
        """Read the bugfix_worktree.sh script."""
        script = Path("scripts/bugfix_worktree.sh")
        assert script.is_file(), "bugfix_worktree.sh must exist"
        return script.read_text()

    def test_has_venv_health_validation(self, bugfix_script: str) -> None:
        """Must call validate_venv_health before symlinking .venv."""
        assert "validate_venv_health" in bugfix_script, (
            "bugfix_worktree.sh must validate .venv health before "
            "symlinking (FR-174 parity with enforce_worktree.sh)"
        )

    def test_has_venv_symlink_validation(self, bugfix_script: str) -> None:
        """Must call validate_venv_symlink after symlinking .venv."""
        assert "validate_venv_symlink" in bugfix_script, (
            "bugfix_worktree.sh must validate .venv symlink resolves "
            "after creation (FR-174 parity with enforce_worktree.sh)"
        )

    def test_cleanup_has_pth_cleaning(self, bugfix_script: str) -> None:
        """cleanup() must call clean_stale_pth_entries."""
        assert "clean_stale_pth_entries" in bugfix_script, (
            "bugfix_worktree.sh cleanup() must clean stale .pth entries "
            "(FR-174 parity with enforce_worktree.sh)"
        )

    def test_cleanup_has_import_validation(self, bugfix_script: str) -> None:
        """cleanup() must validate 'import yamlgraph' after worktree removal."""
        assert "import yamlgraph" in bugfix_script, (
            "bugfix_worktree.sh cleanup() must validate editable install "
            "via 'import yamlgraph' after worktree removal"
        )

    def test_cleanup_has_self_heal_reinstall(self, bugfix_script: str) -> None:
        """cleanup() must auto-reinstall when import validation fails."""
        assert "pip install -e" in bugfix_script, (
            "bugfix_worktree.sh cleanup() must self-heal with "
            "'pip install -e' when import validation fails"
        )
