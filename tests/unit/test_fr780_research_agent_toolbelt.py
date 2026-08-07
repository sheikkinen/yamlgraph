"""FR-780 — Research-agent toolbelt conversion (CAP-220 / REQ-YG-579).

Fourth committed shell-manifest consumer: research-agent's inline tool
variants (head -80 read, py-only capped grep, py-only find) convert to
the canonical examples/shared/toolbelt/ manifests; count_lines stays
inline (demo-local, fit boundary).

Contract under test (judgement 2026-08-07):
- AC-01: read_file/search/list_dir/git_log declared solely via
  manifest: refs; count_lines inline.
- AC-02: effective shell config equivalence — command, canonical
  description, parse, timeout == 30.
- AC-03: agent tool lists use canonical names; zero search_code /
  list_files references anywhere in the demo.
- AC-04: prompts teach canonical names/args and scope translation
  (search.glob, list_dir.dir); no py-only / first-80-lines semantics.
- AC-05: FR-779 boundary preserved — {state...} bindings and the
  empty-findings/low-confidence terminal route survive conversion.
"""

from pathlib import Path

import pytest
import yaml

from yamlgraph.compile.graph_loader import load_graph_config
from yamlgraph.tools.shell import parse_tools

# References examples/ artifacts (FR-756 process boundary)
pytestmark = pytest.mark.process

REPO = Path(__file__).resolve().parents[2]
DEMO = REPO / "examples" / "demos" / "research-agent"
GRAPH = DEMO / "graph.yaml"

# Canonical contracts shared with test_fr777_shell_toolbelt.py
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

LEGACY_NAMES = ("search_code", "list_files")


def _raw() -> dict:
    return yaml.safe_load(GRAPH.read_text(encoding="utf-8"))


class TestManifestConversion:
    @pytest.mark.req("REQ-YG-579")
    @pytest.mark.parametrize("tool", sorted(CANONICAL))
    def test_declares_shared_tools_via_manifest_refs(self, tool):
        """AC-01: pure manifest references for the four shared tools."""
        entry = _raw()["tools"].get(tool)
        assert entry is not None, f"research-agent missing tool {tool}"
        assert set(entry) == {
            "manifest"
        }, f"research-agent.{tool} must be a pure manifest reference, got {entry}"
        assert entry["manifest"].endswith(f"toolbelt/{tool}.tool.yaml")

    @pytest.mark.req("REQ-YG-579")
    def test_count_lines_stays_inline(self):
        """AC-01: demo-local tool keeps inline declaration."""
        entry = _raw()["tools"].get("count_lines")
        assert entry is not None, "research-agent lost count_lines"
        assert "manifest" not in entry, "count_lines must stay inline"
        assert entry["command"] == "wc -l {file}"

    @pytest.mark.req("REQ-YG-579")
    def test_effective_shell_config_matches_canonical_contract(self):
        """AC-02: effective parsed config equals the manifest contract."""
        config = load_graph_config(GRAPH)
        registry = parse_tools(config.tools)
        for tool, contract in CANONICAL.items():
            cfg = registry[tool]
            assert cfg.command == contract["command"]
            assert cfg.description == contract["description"]
            assert cfg.parse == "text"
            assert cfg.timeout == 30


class TestNameCleanup:
    @pytest.mark.req("REQ-YG-579")
    def test_agent_tool_lists_use_canonical_names(self):
        """AC-03: agent nodes reference canonical tool names."""
        nodes = _raw()["nodes"]
        assert nodes["plan_research"]["tools"] == ["search", "list_dir"]
        assert nodes["execute_research"]["tools"] == [
            "search",
            "list_dir",
            "read_file",
            "count_lines",
            "git_log",
        ]

    @pytest.mark.req("REQ-YG-579")
    def test_no_legacy_names_anywhere_in_demo(self):
        """AC-03: zero search_code / list_files references in the demo."""
        offenders = []
        for path in DEMO.rglob("*"):
            if path.is_file() and path.suffix in {".yaml", ".md"}:
                text = path.read_text(encoding="utf-8")
                for name in LEGACY_NAMES:
                    if name in text:
                        offenders.append(f"{path.name}: {name}")
        assert not offenders, f"legacy tool names remain: {offenders}"

    @pytest.mark.req("REQ-YG-579")
    def test_prompts_teach_canonical_args_and_scope_translation(self):
        """AC-04: prompts name canonical args and route scope through
        search.glob / list_dir.dir; truncating semantics removed."""
        for name in ("plan_research", "execute_research"):
            text = (DEMO / "prompts" / f"{name}.yaml").read_text(encoding="utf-8")
            assert "glob" in text, f"{name} prompt must teach search glob arg"
            assert "list_dir" in text, f"{name} prompt must teach list_dir"
            assert "first 80 lines" not in text, f"{name} keeps truncation text"
            assert "Python files" not in text, f"{name} keeps py-only text"


class TestFr779BoundaryPreserved:
    @pytest.mark.req("REQ-YG-579")
    def test_state_bindings_survive(self):
        """AC-05: {state...} bindings and declarations survive conversion."""
        raw = _raw()
        assert raw["state"]["query"] == "str"
        assert raw["state"]["scope"] == "str"
        assert raw["nodes"]["extract_intent"]["variables"]["query"] == "{state.query}"
        assert raw["nodes"]["execute_research"]["variables"]["scope"] == "{state.scope}"

    @pytest.mark.req("REQ-YG-579")
    def test_empty_findings_terminal_route_survives(self):
        """AC-05: the FR-779 synthesis gate survives conversion."""
        edges = _raw()["edges"]
        end_conditions = [
            e.get("condition", "")
            for e in edges
            if e["from"] == "validate_findings" and e["to"] == "END"
        ]
        assert any(
            "validation.confidence == 'low'" in c and "findings == ''" in c
            for c in end_conditions
        ), "empty-findings terminal route lost in conversion"
