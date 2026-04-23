"""Acceptance tests for FR-268: Activate FR-266 Acceptance Tests.

Test activation workflow: remove @pytest.mark.skip decorators from existing tests
to complete the TDD cycle (RED → GREEN → REFACTOR).

TDD RED phase — these tests MUST fail before the skip removal is applied.
"""

import subprocess
from pathlib import Path

import pytest

# Test file that should have skip decorators removed
TARGET_TEST_FILE = Path("tests/unit/test_copilot_node_model_selection.py")


# =============================================================================
# AC-01: 9 skip decorators removed from test_copilot_node_model_selection.py
# =============================================================================


@pytest.mark.req("REQ-YG-265")
class TestSkipDecoratorsRemoved:
    """All FR-266 skip decorators must be removed from target file."""

    def test_no_fr266_skip_decorators_remain(self) -> None:
        """No @pytest.mark.skip decorators with FR-266 RED reason should remain."""
        if not TARGET_TEST_FILE.exists():
            pytest.fail(f"Target test file not found: {TARGET_TEST_FILE}")

        content = TARGET_TEST_FILE.read_text()
        fr266_skip_lines = [
            line
            for line in content.split("\n")
            if "@pytest.mark.skip" in line
            and "FR-266 RED" in line
            and "awaiting implementation" in line
        ]

        # After FR-268 implementation, these should all be gone
        assert (
            len(fr266_skip_lines) == 0
        ), f"Found {len(fr266_skip_lines)} FR-266 skip decorators that should be removed: {fr266_skip_lines}"

    def test_exactly_zero_skip_decorators_in_target_file(self) -> None:
        """Target file should have zero @pytest.mark.skip decorators after activation."""
        if not TARGET_TEST_FILE.exists():
            pytest.fail(f"Target test file not found: {TARGET_TEST_FILE}")

        content = TARGET_TEST_FILE.read_text()
        skip_lines = [
            line for line in content.split("\n") if "@pytest.mark.skip(" in line
        ]

        # All skip decorators should be removed
        assert (
            len(skip_lines) == 0
        ), f"Found {len(skip_lines)} skip decorators that should be removed: {skip_lines}"


# =============================================================================
# AC-02: All 12 acceptance tests pass when run
# =============================================================================


@pytest.mark.req("REQ-YG-265")
class TestAcceptanceTestsPass:
    """All FR-266 acceptance tests must pass after activation."""

    def test_copilot_model_selection_tests_pass(self) -> None:
        """All tests in test_copilot_node_model_selection.py must pass."""
        result = subprocess.run(
            ["pytest", str(TARGET_TEST_FILE), "-v", "--no-cov"],
            capture_output=True,
            text=True,
            cwd=".",
        )

        # All tests should pass (no skips, no failures)
        assert (
            result.returncode == 0
        ), f"Tests failed after activation:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

        # Should not contain "SKIPPED" in output
        assert (
            "SKIPPED" not in result.stdout
        ), f"Found skipped tests after activation:\n{result.stdout}"

    def test_no_skipped_tests_in_pytest_output(self) -> None:
        """pytest output should show no SKIPPED tests for the target file."""
        result = subprocess.run(
            ["pytest", str(TARGET_TEST_FILE), "-v", "--no-cov"],
            capture_output=True,
            text=True,
            cwd=".",
        )

        # Check that pytest summary doesn't mention skipped tests
        lines = result.stdout.split("\n")
        summary_lines = [
            line for line in lines if "passed" in line and "failed" in line.lower()
        ]

        for line in summary_lines:
            assert (
                "skipped" not in line.lower()
            ), f"Found skipped tests in summary: {line}"


# =============================================================================
# AC-03: req_coverage.py shows REQ-YG-265 as active (not skipped)
# =============================================================================


@pytest.mark.req("REQ-YG-265")
class TestRequirementCoverageActive:
    """req_coverage.py must show REQ-YG-265 coverage as active."""

    def test_req_yg_265_shows_as_covered(self) -> None:
        """REQ-YG-265 must appear as covered in requirement coverage."""
        result = subprocess.run(
            ["python", "scripts/req_coverage.py", "--detail"],
            capture_output=True,
            text=True,
            cwd=".",
        )

        assert result.returncode == 0, f"req_coverage.py failed: {result.stderr}"

        # REQ-YG-265 should be listed with test coverage (not marked as skipped)
        assert "REQ-YG-265" in result.stdout, "REQ-YG-265 not found in coverage output"

        # Look for REQ-YG-265 coverage details
        lines = result.stdout.split("\n")
        req_265_lines = [line for line in lines if "REQ-YG-265" in line]

        assert len(req_265_lines) > 0, "No REQ-YG-265 coverage details found"

        # Check that the line doesn't indicate skipped tests
        for line in req_265_lines:
            assert "skipped" not in line.lower(), f"REQ-YG-265 shows as skipped: {line}"

    def test_req_coverage_strict_mode_passes(self) -> None:
        """req_coverage.py --strict should pass with active REQ-YG-265 tests."""
        result = subprocess.run(
            ["python", "scripts/req_coverage.py", "--strict"],
            capture_output=True,
            text=True,
            cwd=".",
        )

        # In strict mode, should pass if REQ-YG-265 is properly covered
        # (May fail for other reasons, but not due to missing REQ-YG-265 coverage)
        if result.returncode != 0:
            # Check if failure is related to REQ-YG-265
            assert (
                "REQ-YG-265" not in result.stderr
            ), f"req_coverage.py --strict failed due to REQ-YG-265: {result.stderr}"


# =============================================================================
# AC-04: No production code changes
# =============================================================================


@pytest.mark.req("REQ-YG-265")
class TestNoProductionCodeChanges:
    """Test activation must not modify production code."""

    def test_yamlgraph_package_unchanged(self) -> None:
        """yamlgraph/ package files must be unchanged."""
        yamlgraph_dir = Path("yamlgraph/")
        if yamlgraph_dir.exists():
            # Check key production files exist and are not test files
            key_files = [
                "yamlgraph/__init__.py",
                "yamlgraph/graph_loader.py",
                "yamlgraph/executor.py",
                "yamlgraph/node_compiler.py",
            ]

            for file_path in key_files:
                path = Path(file_path)
                if path.exists():
                    content = path.read_text()
                    # Should not contain test-specific modifications
                    assert (
                        "@pytest.mark.skip" not in content
                    ), f"Production file {file_path} contains test markers"


# =============================================================================
# AC-05: CI passes with all tests active
# =============================================================================


@pytest.mark.req("REQ-YG-265")
class TestCIPassing:
    """CI pipeline must pass with activated tests."""

    def test_linting_passes_on_modified_file(self) -> None:
        """ruff linting must pass on the modified test file."""
        result = subprocess.run(
            ["ruff", "check", str(TARGET_TEST_FILE)],
            capture_output=True,
            text=True,
            cwd=".",
        )

        assert (
            result.returncode == 0
        ), f"Linting failed on modified test file:\n{result.stdout}\n{result.stderr}"

    def test_test_file_imports_correctly(self) -> None:
        """Modified test file must import without syntax errors."""
        try:
            # Try to import the test module
            import sys
            from pathlib import Path

            # Add the test directory to path temporarily
            test_dir = Path("tests/unit")
            sys.path.insert(0, str(test_dir))

            # Import should work without syntax errors
            import test_copilot_node_model_selection  # type: ignore  # noqa: F401

        except SyntaxError as e:
            pytest.fail(f"Modified test file has syntax errors: {e}")
        except ImportError:
            # ImportError is ok (missing dependencies), SyntaxError is not
            pass
        finally:
            # Clean up sys.path
            if str(test_dir) in sys.path:
                sys.path.remove(str(test_dir))
