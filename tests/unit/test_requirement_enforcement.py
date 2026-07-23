"""Test that requirement traceability is enforced at collection time.

This test verifies Commandment #10 and ADR-001 enforcement.
"""

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

pytestmark = pytest.mark.process


@pytest.mark.slow
@pytest.mark.req("REQ-YG-063")
def test_untagged_test_is_rejected(tmp_path: Path):
    """Verify pytest fails when a test lacks @pytest.mark.req."""
    # Create a test file without @pytest.mark.req
    test_file = tmp_path / "test_example.py"
    test_file.write_text(
        textwrap.dedent(
            """
            def test_missing_req_tag():
                '''This test has no @pytest.mark.req tag.'''
                assert True
            """
        )
    )

    # Copy conftest.py to tmp_path so enforcement hook is active
    conftest_src = Path(__file__).parent.parent / "conftest.py"
    conftest_dst = tmp_path / "conftest.py"
    conftest_dst.write_text(conftest_src.read_text())

    # Run pytest via subprocess - should fail at collection
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
        capture_output=True,
        text=True,
    )

    # Should fail with UsageError (non-zero exit)
    assert result.returncode != 0, "Pytest should reject tests without @pytest.mark.req"
    combined_output = result.stdout + result.stderr
    assert (
        "REQUIREMENT TRACEABILITY VIOLATION" in combined_output
    ), f"Expected enforcement error message in output. Got: {combined_output}"


@pytest.mark.slow
@pytest.mark.req("REQ-YG-063")
def test_tagged_test_is_accepted(tmp_path: Path):
    """Verify pytest allows tests with proper @pytest.mark.req."""
    # Create a test file WITH @pytest.mark.req
    test_file = tmp_path / "test_example.py"
    test_file.write_text(
        textwrap.dedent(
            """
            import pytest

            @pytest.mark.req("REQ-YG-001")
            def test_with_req_tag():
                '''This test has proper @pytest.mark.req tag.'''
                assert True
            """
        )
    )

    # Copy conftest.py to tmp_path so enforcement hook is active
    conftest_src = Path(__file__).parent.parent / "conftest.py"
    conftest_dst = tmp_path / "conftest.py"
    conftest_dst.write_text(conftest_src.read_text())

    # Run pytest via subprocess - should pass
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
        capture_output=True,
        text=True,
    )

    # Should succeed (0 exit code)
    assert (
        result.returncode == 0
    ), f"Pytest should accept tests with @pytest.mark.req. Output: {result.stdout}"


@pytest.mark.slow
@pytest.mark.req("REQ-YG-063")
def test_unmarked_process_boundary_module_is_rejected(tmp_path: Path):
    """FR-756: unmarked unit tests may not reference process boundaries."""
    unit_dir = tmp_path / "tests" / "unit"
    unit_dir.mkdir(parents=True)
    test_file = unit_dir / "test_example.py"
    test_file.write_text(
        textwrap.dedent(
            """
            import pytest

            @pytest.mark.req("REQ-YG-001")
            def test_boundary_reference_without_process_marker():
                payload = "examples/demo.yaml"
                assert payload.endswith(".yaml")
            """
        )
    )

    conftest_src = Path(__file__).parent.parent / "conftest.py"
    conftest_dst = tmp_path / "conftest.py"
    conftest_dst.write_text(conftest_src.read_text())

    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )

    assert result.returncode != 0
    combined_output = result.stdout + result.stderr
    assert "PROCESS BOUNDARY VIOLATION" in combined_output
