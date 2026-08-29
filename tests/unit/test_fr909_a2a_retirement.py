"""FR-909: the A2A protocol surface is retired.

Witness test for the retirement — the only permitted A2A mention under
``tests/`` after the deletion sweep.
"""

import re
from pathlib import Path

import pytest

from yamlgraph.cli import create_parser

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]

DELETED_PATHS = [
    "yamlgraph/a2a",
    "yamlgraph/cli/a2a_commands.py",
    "yamlgraph/contrib/a2a_client.py",
    "reference/a2a-server.md",
    "examples/demos/a2a_call",
    "examples/demos/a2a_server",
]

LIVE_REFERENCE_PATTERN = re.compile(
    r"\ba2a\b|send_a2a_message|create_a2a_app|parse_a2a_message", re.IGNORECASE
)


@pytest.mark.req("REQ-YG-032")
def test_cli_parser_rejects_a2a_subcommand():
    """The top-level parser no longer knows the retired ``a2a`` subcommand."""
    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["a2a", "serve"])


@pytest.mark.req("REQ-YG-032")
def test_cli_package_has_no_a2a_wiring():
    source = (REPO_ROOT / "yamlgraph" / "cli" / "__init__.py").read_text()
    assert "cmd_a2a_dispatch" not in source
    assert "a2a" not in source.lower()


@pytest.mark.req("REQ-YG-032")
@pytest.mark.parametrize("relative_path", DELETED_PATHS)
def test_a2a_surface_files_are_deleted(relative_path):
    assert not (REPO_ROOT / relative_path).exists()


@pytest.mark.req("REQ-YG-032")
def test_no_live_a2a_references_in_package():
    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path in sorted((REPO_ROOT / "yamlgraph").rglob("*.py"))
        if "__pycache__" not in path.parts
        and LIVE_REFERENCE_PATTERN.search(path.read_text())
    ]
    assert offenders == []
