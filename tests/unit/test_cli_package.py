"""Tests for CLI package structure (Phase 7.1).

TDD tests for splitting cli.py into a cli/ package.
"""

import argparse


# =============================================================================
# Package Structure Tests
# =============================================================================


class TestCLIPackageStructure:
    """Tests for CLI package imports."""

    def test_cli_package_importable(self):
        """showcase.cli should be importable as package."""
        import showcase.cli

        assert showcase.cli is not None

    def test_main_function_available(self):
        """main() should be available from package."""
        from showcase.cli import main

        assert callable(main)

    def test_validators_submodule_exists(self):
        """validators submodule should exist."""
        from showcase.cli import validators

        assert validators is not None

    def test_validate_run_args_in_validators(self):
        """validate_run_args should be in validators module."""
        from showcase.cli.validators import validate_run_args

        assert callable(validate_run_args)

    def test_commands_submodule_exists(self):
        """commands submodule should exist."""
        from showcase.cli import commands

        assert commands is not None

    def test_cmd_list_runs_in_commands(self):
        """cmd_list_runs should be in commands module."""
        from showcase.cli.commands import cmd_list_runs

        assert callable(cmd_list_runs)


# =============================================================================
# Backward Compatibility Tests
# =============================================================================


class TestBackwardCompatibility:
    """Ensure old imports still work."""

    def test_cmd_list_runs_from_cli(self):
        """cmd_list_runs should still be importable from showcase.cli."""
        from showcase.cli import cmd_list_runs

        assert callable(cmd_list_runs)

    def test_cmd_resume_from_cli(self):
        """cmd_resume should still be importable from showcase.cli."""
        from showcase.cli import cmd_resume

        assert callable(cmd_resume)


# =============================================================================
# Validator Tests (moved from cli module)
# =============================================================================


class TestValidatorsModule:
    """Tests for validators module functionality."""

    def _create_run_args(self, topic="test topic", word_count=300, style="informative"):
        """Helper to create run args namespace."""
        return argparse.Namespace(
            topic=topic,
            word_count=word_count,
            style=style,
        )

    def test_validate_run_args_valid(self):
        """Valid run args pass validation."""
        from showcase.cli.validators import validate_run_args

        args = self._create_run_args()
        assert validate_run_args(args) is True

    def test_validate_run_args_empty_topic(self):
        """Empty topic fails validation."""
        from showcase.cli.validators import validate_run_args

        args = self._create_run_args(topic="")
        assert validate_run_args(args) is False
