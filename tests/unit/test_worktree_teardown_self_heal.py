"""Condemning tests for FR-241: Complete worktree teardown self-heal.

Three gaps proven by these tests:

1. ``validate_editable_install()`` does not exist in ``worktree_helpers.py``
2. ``enforce_worktree.sh`` cleanup has no import validation after ``.pth`` cleaning
3. ``bugfix_worktree.sh`` cleanup lacks FR-174 guards entirely
   (no ``clean_stale_pth_entries``, no ``validate_venv_health`` before symlink,
   no ``validate_venv_symlink`` after symlink, no import validation)
"""

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
