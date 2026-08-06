"""FR-777 — Shared shell toolbelt manifests (CAP-220 / REQ-YG-579).

First committed shell-runtime manifest consumers: the four shell tools
duplicated verbatim across the planner, enforcer, and judge demos are
extracted to examples/shared/toolbelt/ and referenced via manifest keys.

Contract under test (judgement 2026-08-06):
- AC-01: four toolbelt manifests exist, validate as ToolManifest
  (extra=forbid), runtime.type shell.
- AC-02: the three graphs reference them via manifest: keys; zero
  inline copies of the four commands remain.
- AC-03: effective shell config equivalence — command, canonical
  description, parse, timeout == 30 (R-2: effective config, not raw
  dict bytes).
- AC-04: canonical search description is the union of the drifted
  glob example lists.
- AC-05: demo-specific tools stay inline.
"""

from pathlib import Path

import pytest
import yaml

from yamlgraph.compile.graph_loader import load_graph_config
from yamlgraph.tools.manifest import ToolManifest
from yamlgraph.tools.shell import parse_tools

# References examples/ artifacts (FR-756 process boundary)
pytestmark = pytest.mark.process

REPO = Path(__file__).resolve().parents[2]
TOOLBELT = REPO / "examples" / "shared" / "toolbelt"
GRAPHS = {
    "planner": REPO / "examples" / "demos" / "planner" / "graph.yaml",
    "enforcer": REPO / "examples" / "demos" / "enforcer" / "graph.yaml",
    "judge": REPO / "examples" / "demos" / "judge" / "graph.yaml",
}

# Canonical contracts (judgement D-1; search description = union, AC-04)
CANONICAL = {
    "read_file": {
        "command": "cat {file}",
        "description": "Read a project file in full.",
    },
    "search": {
        "command": "rg -n --glob {glob} {pattern} .",
        "description": (
            "Search files matching a glob pattern. Examples: --glob "
            "'ARCHITECTURE.md', --glob 'feature-requests/*.md', --glob "
            "'yamlgraph/**/*.py', --glob 'tests/**/*.py', --glob "
            "'capabilities/*.yaml'."
        ),
    },
    "list_dir": {
        "command": "ls {dir}",
        "description": "List contents of a directory.",
    },
    "git_log": {
        "command": "git log --oneline --all --grep={pattern}",
        "description": (
            "Search git history for commits mentioning a pattern. "
            "Find prior attempts, related FRs, rejected work."
        ),
    },
}

# Previously drifted glob examples that the union must contain (AC-04)
DRIFTED_GLOB_EXAMPLES = [
    "--glob 'ARCHITECTURE.md'",
    "--glob 'feature-requests/*.md'",
    "--glob 'yamlgraph/**/*.py'",
    "--glob 'tests/**/*.py'",
    "--glob 'capabilities/*.yaml'",
]

# Demo-specific tools that must remain inline (AC-05)
INLINE_ONLY = {
    "planner": ["write_file"],
    "enforcer": ["git_diff", "lint", "run_tests", "write_file", "edit_file"],
    "judge": ["run_tests"],
}


@pytest.mark.req("REQ-YG-579")
@pytest.mark.parametrize("tool", sorted(CANONICAL))
def test_toolbelt_manifest_exists_and_validates(tool):
    """AC-01: each manifest exists and validates as a shell ToolManifest."""
    path = TOOLBELT / f"{tool}.tool.yaml"
    assert path.exists(), f"missing manifest: {path}"
    manifest = ToolManifest.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )
    assert manifest.name == tool
    assert manifest.runtime.type == "shell"
    assert manifest.runtime.command == CANONICAL[tool]["command"]


@pytest.mark.req("REQ-YG-579")
def test_toolbelt_manifest_rejects_unknown_fields():
    """AC-01: extra=forbid holds for the committed manifest shape."""
    path = TOOLBELT / "read_file.tool.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["speculative"] = True
    with pytest.raises(Exception, match="speculative"):
        ToolManifest.model_validate(data)


@pytest.mark.req("REQ-YG-579")
@pytest.mark.parametrize("demo", sorted(GRAPHS))
def test_graph_references_toolbelt_via_manifest_keys(demo):
    """AC-02: raw graph YAML declares the four tools by manifest reference."""
    raw = yaml.safe_load(GRAPHS[demo].read_text(encoding="utf-8"))
    for tool in CANONICAL:
        entry = raw["tools"][tool]
        assert set(entry) == {
            "manifest"
        }, f"{demo}.{tool} must be a pure manifest reference, got {entry}"
        assert entry["manifest"].endswith(f"toolbelt/{tool}.tool.yaml")


@pytest.mark.req("REQ-YG-579")
@pytest.mark.parametrize("demo", sorted(GRAPHS))
def test_no_inline_copies_of_toolbelt_commands_remain(demo):
    """AC-02: zero inline copies of the four commands in the graph file."""
    text = GRAPHS[demo].read_text(encoding="utf-8")
    for tool, contract in CANONICAL.items():
        assert (
            f"command: {contract['command']}" not in text
        ), f"{demo} still declares {tool} inline"


@pytest.mark.req("REQ-YG-579")
@pytest.mark.parametrize("demo", sorted(GRAPHS))
def test_effective_shell_config_matches_canonical_contract(demo):
    """AC-03 (R-2): effective parsed config — command, description,
    parse, timeout == 30 — not raw dict bytes."""
    config = load_graph_config(GRAPHS[demo])
    registry = parse_tools(config.tools)
    for tool, contract in CANONICAL.items():
        cfg = registry[tool]
        assert cfg.command == contract["command"]
        assert cfg.description == contract["description"]
        assert cfg.parse == "text"
        assert cfg.timeout == 30


@pytest.mark.req("REQ-YG-579")
def test_search_description_is_union_of_drifted_examples():
    """AC-04: the canonical search description contains every glob
    example that previously appeared in any of the three copies."""
    manifest = ToolManifest.model_validate(
        yaml.safe_load((TOOLBELT / "search.tool.yaml").read_text(encoding="utf-8"))
    )
    for example in DRIFTED_GLOB_EXAMPLES:
        assert example in manifest.description, f"missing {example}"


@pytest.mark.req("REQ-YG-579")
@pytest.mark.parametrize("demo", sorted(GRAPHS))
def test_demo_specific_tools_remain_inline(demo):
    """AC-05: demo-local tools are declared inline, not via manifest."""
    raw = yaml.safe_load(GRAPHS[demo].read_text(encoding="utf-8"))
    for tool in INLINE_ONLY[demo]:
        entry = raw["tools"].get(tool)
        assert entry is not None, f"{demo} lost its inline tool {tool}"
        assert (
            "manifest" not in entry
        ), f"{demo}.{tool} is demo-specific and must stay inline"


@pytest.mark.req("REQ-YG-579")
@pytest.mark.parametrize("demo", sorted(GRAPHS))
def test_agent_node_tool_list_unchanged(demo):
    """Conversion must not change which tools the agent node sees."""
    expected = {
        "planner": ["read_file", "search", "list_dir", "git_log", "write_file"],
        "enforcer": None,  # asserted as superset below
        "judge": ["read_file", "search", "list_dir", "git_log", "run_tests"],
    }[demo]
    raw = yaml.safe_load(GRAPHS[demo].read_text(encoding="utf-8"))
    node = next(iter(raw["nodes"].values()))
    if expected is None:
        assert set(CANONICAL) <= set(node["tools"])
    else:
        assert node["tools"] == expected
