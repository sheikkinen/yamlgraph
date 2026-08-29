"""FR-915: the Mastra MCP integration demo is retired.

Witness test for the retirement — the only permitted Mastra mention under
``tests/`` after the deletion sweep.
"""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = REPO_ROOT / "examples"


@pytest.mark.req("REQ-YG-428")
def test_mastra_demo_directory_is_deleted():
    assert not (EXAMPLES / "demos" / "mastra-integration").exists()


@pytest.mark.req("REQ-YG-428")
def test_no_mastra_references_in_live_example_surfaces():
    """No live advertising of the retired demo.

    ``demo-output.log`` files are frozen CAP-79 proof artifacts of other
    demos' real runs; editing one to satisfy a grep would falsify evidence.
    """
    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path in sorted(EXAMPLES.rglob("*"))
        if path.is_file()
        and path.name != "demo-output.log"
        and "node_modules" not in path.parts
        and _mentions_mastra(path)
    ]
    assert offenders == []


def _mentions_mastra(path: Path) -> bool:
    try:
        return re.search("mastra", path.read_text(), re.IGNORECASE) is not None
    except (UnicodeDecodeError, OSError):
        return False


@pytest.mark.req("REQ-YG-428")
def test_typescript_demo_survives_as_the_integration_witness():
    """C-5: typescript-node is the surviving TypeScript integration."""
    assert (EXAMPLES / "demos" / "typescript-node").is_dir()
    readme = (EXAMPLES / "README.md").read_text()
    assert "typescript-node" in readme
