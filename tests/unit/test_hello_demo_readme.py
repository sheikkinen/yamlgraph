"""Tests for FR-182: Hello World Smoke Test.

Validates that examples/demos/hello/README.md exists with proper documentation
including run command and validation instructions.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HELLO_DIR = REPO_ROOT / "examples" / "demos" / "hello"
README_PATH = HELLO_DIR / "README.md"


def _read_readme() -> str:
    """Read hello demo README.md content."""
    assert README_PATH.exists(), f"Hello README.md not found at {README_PATH}"
    return README_PATH.read_text()


@pytest.mark.req("REQ-YG-161")
class TestHelloDemoReadme:
    """FR-182: Hello demo README must document usage and validation."""

    def test_readme_exists(self) -> None:
        """AC-1: examples/demos/hello/README.md exists with documentation."""
        assert README_PATH.exists(), "examples/demos/hello/README.md must exist"
        content = README_PATH.read_text()
        assert len(content) > 100, "README must contain substantive documentation"

    def test_readme_documents_run_command(self) -> None:
        """AC-2: README explains how to run the hello graph."""
        readme = _read_readme()
        assert (
            "yamlgraph graph run" in readme
        ), "README must contain 'yamlgraph graph run' command"
        assert (
            "examples/demos/hello/graph.yaml" in readme
        ), "README must reference the hello graph path"

    def test_readme_documents_variables(self) -> None:
        """AC-2 (implicit): README shows required --var arguments."""
        readme = _read_readme()
        assert "--var name=" in readme, "README must show --var name= usage"
        assert "--var style=" in readme, "README must show --var style= usage"

    def test_readme_documents_lint_validation(self) -> None:
        """README documents graph lint as a validation step."""
        readme = _read_readme()
        assert (
            "yamlgraph graph lint" in readme
        ), "README must document 'yamlgraph graph lint' for validation"
