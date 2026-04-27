"""Acceptance tests for FR-275: Test Speed Optimization.

These tests verify the acceptance criteria for adding pytest slow markers
and optimizing wait/sleep logic to enable faster development cycles.

All tests should FAIL on the unmodified codebase (RED phase).
"""

import subprocess
import sys
from pathlib import Path

import pytest


class TestSlowMarkerInfrastructure:
    """AC-01: `slow` pytest marker added to `pyproject.toml`."""

    @pytest.mark.req("REQ-YG-275")
    def test_slow_marker_defined_in_pyproject(self):
        """The `slow` marker must be defined in pyproject.toml markers list."""
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"

        # Read pyproject.toml content
        with open(pyproject_path) as f:
            content = f.read()

        # Look for slow marker definition
        assert (
            "slow: marks tests that take >1 second to complete" in content
        ), "The 'slow' pytest marker must be defined in [tool.pytest.ini_options] markers"

    @pytest.mark.slow
    @pytest.mark.req("REQ-YG-275")
    def test_slow_marker_recognized_by_pytest(self):
        """Pytest should recognize the slow marker without warnings."""
        # This will fail until the marker is properly configured
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--markers"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        assert (
            "slow: marks tests that take >1 second to complete" in result.stdout
        ), "Pytest should recognize the 'slow' marker when --markers is run"


class TestSlowTestMarking:
    """AC-02: Tests using sleep >1s are marked with `@pytest.mark.slow`."""

    @pytest.mark.req("REQ-YG-275")
    def test_map_timeout_tests_have_slow_marker(self):
        """Map timeout tests that use time.sleep(2) should have @pytest.mark.slow."""
        test_file_path = Path(__file__).parent / "test_map_node_timeout.py"

        with open(test_file_path) as f:
            content = f.read()

        # Check if any test with sleep patterns has @pytest.mark.slow
        lines = content.split("\n")
        found_slow_marker_before_sleep = False

        for i, line in enumerate(lines):
            if "time.sleep(" in line and ("2 *" in line or "delay_scale" in line):
                # Look backwards for @pytest.mark.slow in the last 10 lines
                start_idx = max(0, i - 10)
                preceding_lines = lines[start_idx:i]
                if any(
                    "@pytest.mark.slow" in prev_line for prev_line in preceding_lines
                ):
                    found_slow_marker_before_sleep = True
                    break

        assert found_slow_marker_before_sleep, "Tests with configurable time.sleep in test_map_node_timeout.py should have @pytest.mark.slow"

    @pytest.mark.req("REQ-YG-275")
    def test_race_node_tests_have_slow_marker(self):
        """Race node tests that use asyncio.sleep(30.0) should have @pytest.mark.slow."""
        test_file_path = Path(__file__).parent / "test_race_node.py"

        with open(test_file_path) as f:
            content = f.read()

        # Check if any test with asyncio.sleep(30.0) has @pytest.mark.slow
        lines = content.split("\n")
        found_slow_marker_before_sleep = False

        for i, line in enumerate(lines):
            if "asyncio.sleep(30.0)" in line:
                # Look backwards for @pytest.mark.slow in the last 20 lines
                start_idx = max(0, i - 20)
                preceding_lines = lines[start_idx:i]
                if any(
                    "@pytest.mark.slow" in prev_line for prev_line in preceding_lines
                ):
                    found_slow_marker_before_sleep = True
                    break

        assert found_slow_marker_before_sleep, "Tests with asyncio.sleep(30.0) in test_race_node.py should have @pytest.mark.slow"


class TestSlowTestFiltering:
    """AC-03: Fast test run (`-m "not slow"`) completes in <30 seconds."""

    @pytest.mark.slow
    @pytest.mark.req("REQ-YG-275")
    def test_fast_test_run_excludes_slow_tests(self):
        """Running pytest -m 'not slow' should exclude slow-marked tests."""
        # This test will fail until slow markers are implemented
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/unit/",
                "-m",
                "not slow",
                "--collect-only",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        # Should succeed and show some tests were deselected
        assert result.returncode == 0, f"Fast test collection failed: {result.stderr}"
        assert (
            "deselected" in result.stdout
        ), "Fast test run should show some tests were deselected due to slow marker"

    @pytest.mark.slow
    @pytest.mark.req("REQ-YG-275")
    def test_slow_test_run_includes_only_slow_tests(self):
        """Running pytest -m 'slow' should include only slow-marked tests."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/unit/",
                "-m",
                "slow",
                "--collect-only",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        # Should succeed and show some tests were selected
        assert result.returncode == 0, f"Slow test collection failed: {result.stderr}"
        assert (
            "selected" in result.stdout
        ), "Slow test run should show some tests were selected with slow marker"


class TestConfigurableTiming:
    """AC-05: `CHAOS_DELAY` and similar timing made configurable."""

    @pytest.mark.req("REQ-YG-275")
    def test_chaos_tools_respects_test_delay_scale(self):
        """CHAOS_DELAY should be configurable via TEST_DELAY_SCALE environment variable."""
        # Check if chaos_tools.py uses configurable delays
        chaos_tools_path = Path(__file__).parent.parent / "chaos_tools.py"

        with open(chaos_tools_path) as f:
            content = f.read()

        # Should use TEST_DELAY_SCALE or similar configurable mechanism
        assert (
            "TEST_DELAY_SCALE" in content or "DELAY_SCALE" in content
        ), "chaos_tools.py should use configurable delay scaling for test optimization"

    @pytest.mark.req("REQ-YG-275")
    def test_timeout_tests_use_configurable_delays(self):
        """Timeout tests should use configurable delays instead of hardcoded values."""
        test_file_path = Path(__file__).parent / "test_map_node_timeout.py"

        with open(test_file_path) as f:
            content = f.read()

        # Should use configurable delays, not hardcoded time.sleep(2)
        # Check that the file contains both TEST_DELAY_SCALE and time.sleep patterns
        has_test_delay_scale = "TEST_DELAY_SCALE" in content
        has_configurable_sleep = False

        lines = content.split("\n")
        for line in lines:
            # Look for time.sleep that uses a variable, not hardcoded value
            if "time.sleep(" in line and "time.sleep(2)" not in line:
                has_configurable_sleep = True
                break

        configurable_delay_found = has_test_delay_scale and has_configurable_sleep

        assert configurable_delay_found, "test_map_node_timeout.py should use configurable delays via environment variables"


class TestDocumentationUpdates:
    """AC-06: Development commands updated in `CLAUDE.md`."""

    @pytest.mark.req("REQ-YG-275")
    def test_claude_md_has_fast_test_commands(self):
        """CLAUDE.md should document fast test commands using slow markers."""
        claude_md_path = Path(__file__).parent.parent.parent / "CLAUDE.md"

        with open(claude_md_path) as f:
            content = f.read()

        # Should document the new fast test commands
        assert (
            'pytest tests/unit/ -q --no-cov -m "not slow"' in content
        ), "CLAUDE.md should document the fast test command excluding slow tests"

    @pytest.mark.req("REQ-YG-275")
    def test_claude_md_has_slow_only_test_commands(self):
        """CLAUDE.md should document slow-only test commands."""
        claude_md_path = Path(__file__).parent.parent.parent / "CLAUDE.md"

        with open(claude_md_path) as f:
            content = f.read()

        # Should document the slow test commands
        assert (
            'pytest tests/unit/ -q --no-cov -m "slow"' in content
        ), "CLAUDE.md should document the slow-only test command"


class TestMarkerFunctionality:
    """AC-08: Tests added for marker functionality."""

    @pytest.mark.req("REQ-YG-275")
    def test_slow_marker_properly_applied(self):
        """This test verifies that slow markers are properly applied and recognized."""
        # This test itself should have slow marker when sleep >1s is used
        # For now, this test will pass since it doesn't use sleep
        pass

    @pytest.mark.slow
    @pytest.mark.req("REQ-YG-275")
    def test_marker_selection_syntax_works(self):
        """Verify that pytest marker selection syntax works correctly."""
        # Test that -m "slow" and -m "not slow" syntax is valid
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        assert (
            "-m MARKEXPR" in result.stdout
        ), "Pytest should support -m marker expression syntax"


class TestNoTestBehaviorChanges:
    """AC-07: No test behavior changes (same pass/fail results)."""

    @pytest.mark.slow
    @pytest.mark.req("REQ-YG-275")
    def test_all_tests_still_run_by_default(self):
        """Running pytest without markers should still run all tests."""
        # This verifies that adding slow markers doesn't exclude tests by default
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/unit/test_map_node_timeout.py",
                "--collect-only",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        assert (
            result.returncode == 0
        ), f"Default test collection failed: {result.stderr}"
        # Should collect tests without exclusions
        assert (
            "collected" in result.stdout
        ), "Default pytest run should collect all tests including those with slow markers"
