"""Tests for FR-135: Examples & Demos Value Audit.

Validates that examples/README.md accurately indexes all on-disk examples
and demos, organized into documented sections with inclusion criteria.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples"
DEMOS_DIR = EXAMPLES_DIR / "demos"
README_PATH = EXAMPLES_DIR / "README.md"

# Directories inside demos/ that are NOT demos (test infrastructure, etc.)
DEMO_EXCLUSIONS = {"tests", "__pycache__"}

# Top-level directories inside examples/ that are NOT examples
TOPLEVEL_EXCLUSIONS = {"demos", "shared", "__pycache__"}


def _read_readme() -> str:
    """Read examples/README.md content."""
    assert README_PATH.exists(), f"examples/README.md not found at {README_PATH}"
    return README_PATH.read_text()


def _get_demo_dirs() -> list[str]:
    """Get all demo directory names on disk (excluding non-demo dirs)."""
    return sorted(
        d.name
        for d in DEMOS_DIR.iterdir()
        if d.is_dir() and d.name not in DEMO_EXCLUSIONS and not d.name.startswith(".")
    )


def _get_toplevel_example_dirs() -> list[str]:
    """Get all top-level example directory names on disk."""
    return sorted(
        d.name
        for d in EXAMPLES_DIR.iterdir()
        if d.is_dir()
        and d.name not in TOPLEVEL_EXCLUSIONS
        and not d.name.startswith(".")
        and not d.name.startswith("__")
    )


@pytest.mark.req("REQ-YG-147")
def test_all_demos_listed_in_readme():
    """Every demo directory in examples/demos/ must appear in README.md."""
    readme = _read_readme()
    demos = _get_demo_dirs()
    missing = [d for d in demos if f"demos/{d}" not in readme and f"{d}" not in readme]
    assert not missing, f"Demos missing from examples/README.md: {missing}"


@pytest.mark.req("REQ-YG-147")
def test_all_toplevel_examples_listed_in_readme():
    """Every top-level example directory must appear in README.md."""
    readme = _read_readme()
    examples = _get_toplevel_example_dirs()
    missing = [e for e in examples if f"{e}/" not in readme and f"{e}]" not in readme]
    assert not missing, f"Top-level examples missing from README.md: {missing}"


@pytest.mark.req("REQ-YG-147")
def test_demos_index_has_three_sections():
    """Demos Index must be split into Learning / Utility / FR Validation."""
    readme = _read_readme()
    assert "### Learning Demos" in readme, "Missing '### Learning Demos' section"
    assert "### Utility Demos" in readme, "Missing '### Utility Demos' section"
    assert (
        "### FR Validation Demos" in readme
    ), "Missing '### FR Validation Demos' section"


@pytest.mark.req("REQ-YG-147")
def test_inclusion_criteria_documented():
    """Inclusion criteria must be documented in README.md."""
    readme = _read_readme()
    assert "## Inclusion Criteria" in readme, "Missing '## Inclusion Criteria' section"
    assert (
        "README.md" in readme.split("## Inclusion Criteria")[1].split("##")[0]
    ), "Inclusion criteria must mention README.md requirement"


@pytest.mark.req("REQ-YG-147")
def test_quality_bar_readme_exists():
    """Every listed demo must have a README.md file."""
    demos = _get_demo_dirs()
    missing_readme = [d for d in demos if not (DEMOS_DIR / d / "README.md").exists()]
    assert not missing_readme, f"Demos missing README.md: {missing_readme}"


@pytest.mark.req("REQ-YG-147")
def test_quality_bar_runnable_artifact():
    """Every listed demo must have a runnable artifact (YAML graph, demo.sh, or Python script)."""
    demos = _get_demo_dirs()
    missing_artifact = []
    for d in demos:
        demo_path = DEMOS_DIR / d
        has_yaml = any(demo_path.glob("*.yaml")) or any(demo_path.glob("*.yml"))
        has_demo_sh = (demo_path / "demo.sh").exists()
        has_python = any(demo_path.glob("*.py")) and not all(
            f.name.startswith("__") for f in demo_path.glob("*.py")
        )
        if not (has_yaml or has_demo_sh or has_python):
            missing_artifact.append(d)
    assert not missing_artifact, f"Demos missing runnable artifact: {missing_artifact}"


@pytest.mark.req("REQ-YG-147")
def test_toplevel_examples_have_readme():
    """Every top-level example must have a README.md file."""
    examples = _get_toplevel_example_dirs()
    missing = [e for e in examples if not (EXAMPLES_DIR / e / "README.md").exists()]
    assert not missing, f"Top-level examples missing README.md: {missing}"
