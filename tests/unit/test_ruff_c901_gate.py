"""Tests for Ruff C901 cognitive complexity gate (FR-221).

Verifies that cognitive complexity is enforced via ruff C901 at threshold 15,
closing the gap where radon CC (grade D ≥ 21) misses deeply-nested functions.
"""

import subprocess
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"


def _load_pyproject() -> dict:
    """Load pyproject.toml as a dict."""
    return tomllib.loads(PYPROJECT.read_text())


class TestRuffC901Config:
    """Verify C901 is configured in pyproject.toml."""

    @pytest.mark.req("REQ-YG-221")
    def test_c901_in_ruff_select(self) -> None:
        """C901 must be in ruff lint select list."""
        data = _load_pyproject()
        select = data["tool"]["ruff"]["lint"]["select"]
        assert "C901" in select, (
            "C901 not found in [tool.ruff.lint] select. "
            "FR-221 requires cognitive complexity gating."
        )

    @pytest.mark.req("REQ-YG-221")
    def test_mccabe_max_complexity_set(self) -> None:
        """max-complexity must be set to 15 in [tool.ruff.lint.mccabe]."""
        data = _load_pyproject()
        mccabe = data["tool"]["ruff"]["lint"]["mccabe"]
        assert mccabe["max-complexity"] == 15, (
            f"Expected max-complexity = 15, got {mccabe.get('max-complexity')}. "
            "FR-221 sets threshold at 15 to catch worst offenders."
        )


class TestRuffC901Passes:
    """Verify ruff check passes with C901 enabled."""

    @pytest.mark.req("REQ-YG-221")
    def test_ruff_check_passes(self) -> None:
        """ruff check yamlgraph/ must pass with C901 enabled."""
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "yamlgraph/"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert (
            result.returncode == 0
        ), f"ruff check failed with C901 enabled:\n{result.stdout}\n{result.stderr}"


class TestC901NoqaConfessions:
    """Verify all C901 noqa suppressions are documented in confessions.md."""

    @pytest.mark.req("REQ-YG-221")
    def test_c901_noqa_suppressions_confessed(self) -> None:
        """Every C901 suppression in yamlgraph/ must have a CONF entry."""
        confessions_path = REPO_ROOT / "docs" / "confessions.md"
        assert confessions_path.exists(), "docs/confessions.md not found"
        confessions_text = confessions_path.read_text()

        # Build marker dynamically to avoid noqa scanner false positive
        marker = "# " + "noqa" + ": C901"

        # Find all C901 suppressions in yamlgraph/
        noqa_files: list[str] = []
        for py_file in sorted(REPO_ROOT.joinpath("yamlgraph").rglob("*.py")):
            rel = py_file.relative_to(REPO_ROOT)
            for i, line in enumerate(py_file.read_text().splitlines(), 1):
                if marker in line:
                    noqa_files.append(f"{rel}:{i}")

        # Each suppression must be documented
        for location in noqa_files:
            file_part = location.split(":")[0]
            assert file_part in confessions_text, (
                f"C901 suppression at {location} not documented in confessions.md. "
                "See docs/confessions.md 'Adding New Confessions' section."
            )
