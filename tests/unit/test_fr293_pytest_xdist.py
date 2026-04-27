"""FR-293: pytest-xdist parallel test execution.

Structural tests verifying xdist is properly configured.
"""

import subprocess
import sys

import pytest


@pytest.mark.req("REQ-YG-012")
def test_xdist_is_installed():
    """pytest-xdist must be importable."""
    import xdist  # noqa: F401


@pytest.mark.req("REQ-YG-012")
def test_xdist_in_pyproject_dev_deps():
    """pytest-xdist must be listed in pyproject.toml dev dependencies."""
    from pathlib import Path

    pyproject = Path(__file__).parents[2] / "pyproject.toml"
    content = pyproject.read_text()
    assert "pytest-xdist" in content, "pytest-xdist missing from pyproject.toml"


@pytest.mark.req("REQ-YG-012")
def test_precommit_uses_parallel_flag():
    """Pre-commit pytest hook must include -n auto for parallel execution."""
    from pathlib import Path

    config = Path(__file__).parents[2] / ".pre-commit-config.yaml"
    content = config.read_text()
    assert "-n auto" in content, "Pre-commit pytest hook missing -n auto flag"


@pytest.mark.req("REQ-YG-012")
def test_precommit_excludes_slow_tests():
    """Pre-commit pytest hook must include -m 'not slow' filter."""
    from pathlib import Path

    config = Path(__file__).parents[2] / ".pre-commit-config.yaml"
    content = config.read_text()
    assert "not slow" in content, "Pre-commit pytest hook missing slow filter"


@pytest.mark.req("REQ-YG-012")
def test_dependency_rationale_entry():
    """pytest-xdist must have an entry in dependency-rationale.yaml."""
    from pathlib import Path

    rationale = Path(__file__).parents[2] / "docs" / "dependency-rationale.yaml"
    content = rationale.read_text()
    assert (
        "pytest-xdist" in content
    ), "pytest-xdist missing from dependency-rationale.yaml"


@pytest.mark.req("REQ-YG-012")
def test_no_surrogate_unicode_in_image_node():
    """image_node.py must not contain surrogate Unicode escape sequences.

    Surrogates crash xdist workers (execnet can't serialize them).
    """
    from pathlib import Path

    image_node = (
        Path(__file__).parents[2]
        / "examples"
        / "storyboard"
        / "nodes"
        / "image_node.py"
    )
    content = image_node.read_text(encoding="utf-8")
    # Verify no surrogate escapes in source
    assert "\\ud83d" not in content, "Surrogate escape sequences found in image_node.py"


@pytest.mark.req("REQ-YG-012")
@pytest.mark.slow
def test_xdist_n_flag_accepted():
    """pytest must accept -n auto flag (xdist plugin loaded)."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--co",
            "-q",
            "-n",
            "auto",
            "tests/unit/test_fr293_pytest_xdist.py",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"pytest -n auto rejected: {result.stderr}"
