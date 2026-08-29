"""FR-910: the MCP server surface is retired.

Witness test for the retirement — the only permitted MCP-server mention
under ``tests/`` after the deletion sweep.
"""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]

DELETED_PATHS = [
    "yamlgraph/export/mcp.py",
    "reference/mcp-server.md",
    ".vscode/mcp.json",
    "tests/unit/test_mcp_server.py",
    "tests/unit/test_mcp_typed_tools.py",
    "tests/unit/test_fr355_mcp_schema_validation_gate_red.py",
]

SERVER_SURFACE_PATTERN = re.compile(
    r"yamlgraph\.export\.mcp"
    r"|yamlgraph/export/mcp\.py"
    r"|yamlgraph\.mcp_server"
    r"|mcp_server\.py"
    r"|yamlgraph_list_graphs"
    r"|yamlgraph_run_graph"
    r"|mcp_yamlgraph_"
)

SCANNED_SURFACES = [
    "yamlgraph",
    "tests",
    "reference",
    "README.md",
    "CLAUDE.md",
    ".github/copilot-instructions.md",
    "docs/concurrency-safety.md",
    "docs/dependency-rationale.yaml",
]


@pytest.mark.req("REQ-YG-428")
@pytest.mark.parametrize("relative_path", DELETED_PATHS)
def test_mcp_server_surface_files_are_deleted(relative_path):
    assert not (REPO_ROOT / relative_path).exists()


@pytest.mark.req("REQ-YG-428")
def test_mcp_capabilities_are_retired():
    for cap in (
        "CAP-19-mcp-server-interface.yaml",
        "CAP-136-per-graph-typed-mcp-tools.yaml",
    ):
        text = (REPO_ROOT / "capabilities" / cap).read_text()
        assert "status: retired" in text
        assert "RETIRED by FR-910" in text


@pytest.mark.req("REQ-YG-428")
def test_no_live_mcp_server_references():
    offenders: list[str] = []
    for surface in SCANNED_SURFACES:
        root = REPO_ROOT / surface
        if not root.exists():
            continue
        paths = [root] if root.is_file() else sorted(root.rglob("*"))
        for path in paths:
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            if path == Path(__file__):
                continue
            try:
                text = path.read_text()
            except (UnicodeDecodeError, OSError):
                continue
            if SERVER_SURFACE_PATTERN.search(text):
                offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == []


@pytest.mark.req("REQ-YG-428")
def test_mcp_extra_is_removed():
    pyproject = (REPO_ROOT / "pyproject.toml").read_text()
    assert "mcp = [" not in pyproject
    constraints = (REPO_ROOT / "constraints" / "dev-py312.txt").read_text()
    assert not re.search(r"^mcp==", constraints, re.MULTILINE)


@pytest.mark.req("REQ-YG-428")
def test_is_this_a_graph_names_cli_route_only():
    doctrine = (REPO_ROOT / ".github" / "copilot-instructions.md").read_text()
    clause_start = doctrine.index("is_this_a_graph:")
    clause = doctrine[clause_start : clause_start + 1500]
    assert "yamlgraph graph list" in clause
    assert "mcp" not in clause.lower()
