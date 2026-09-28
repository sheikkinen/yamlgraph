"""FR-275: the `slow` pytest marker is registered (REQ-YG-275)."""

from pathlib import Path

import pytest


@pytest.mark.req("REQ-YG-275")
def test_slow_marker_defined_in_pyproject():
    """The `slow` marker must be defined in pyproject.toml markers list."""
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    content = pyproject_path.read_text(encoding="utf-8")
    assert "slow: marks tests that take >1 second to complete" in content, (
        "The 'slow' pytest marker must be defined in [tool.pytest.ini_options] markers"
    )
