"""FR-700 Timeframe Recap Demo — Unit tests (LLM-free).

Tests that the recap graph (deterministic git collection via tool nodes +
one synthesis LLM node) loads, lints clean, has the frozen structure, and
fails loudly on a non-git repo_path. Integration tests (real LLM) live in
tests/integration/.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

GRAPH_PATH = "examples/demos/recap/graph.yaml"
DEMO_DIR = (
    Path(__file__).resolve().parent.parent.parent / "examples" / "demos" / "recap"
)

TOOL_NODES = {"get_commits", "get_churn", "get_frs", "get_fragments", "get_fr_statuses"}


class TestRecapGraphStructure:
    """Graph structure matches the frozen FR-700 scope."""

    @pytest.mark.req("REQ-YG-531")
    def test_graph_config_loads(self) -> None:
        """Graph config loads via yamlgraph."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        assert config.name == "recap"

    @pytest.mark.req("REQ-YG-531")
    def test_graph_lint_passes(self) -> None:
        """Graph passes yamlgraph lint with zero errors."""
        from yamlgraph.linter.graph_linter import lint_graph

        result = lint_graph(GRAPH_PATH)
        errors = [i for i in result.issues if i.severity == "error"]
        assert errors == [], f"Lint errors: {errors}"

    @pytest.mark.req("REQ-YG-531")
    def test_exactly_one_llm_node(self) -> None:
        """Prompt contract: one judgement — exactly one LLM node."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        llm_nodes = [
            n for n, c in raw["nodes"].items() if c.get("type", "llm") == "llm"
        ]
        assert llm_nodes == ["synthesize"]

    @pytest.mark.req("REQ-YG-531")
    def test_collection_is_tool_nodes(self) -> None:
        """All collection nodes are deterministic type: tool."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        tool_nodes = {n for n, c in raw["nodes"].items() if c.get("type") == "tool"}
        assert tool_nodes == TOOL_NODES

    @pytest.mark.req("REQ-YG-531")
    def test_git_commands_are_portable(self) -> None:
        """Every git shell tool uses -C {repo_path}; no reflog syntax; capped."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        commands = [
            t["command"] for t in raw["tools"].values() if t.get("type") == "shell"
        ]
        assert commands, "shell tools section must not be empty"
        for cmd in commands:
            assert "git -C {repo_path}" in cmd, f"not portable: {cmd}"
            assert "@{" not in cmd, f"reflog syntax forbidden: {cmd}"
        capped = [c for c in commands if "-n 300" in c]
        assert capped, "commit collection must be capped at -n 300"

    @pytest.mark.req("REQ-YG-531")
    def test_no_silent_fallback_in_commands(self) -> None:
        """No '|| true' — non-repo must fail loudly (Commandment 6).

        FR-702's '|| [ $? -eq 1 ]' is boundary normalization, not a silent
        fallback: exit >=2 (real error) still fails.
        """
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        for tool in raw["tools"].values():
            if tool.get("type") != "shell":
                continue
            assert "|| true" not in tool["command"], f"silent fallback: {tool}"

    @pytest.mark.req("REQ-YG-531")
    def test_prompt_schema_frozen_fields(self) -> None:
        """Inline schema carries only judgement fields.

        Evolution trail: F6 froze 4 fields; W026 cut conventions_detected
        (FR-700 enforce); FR-704 moved orphans to code. What remains is
        judgement: workstreams + hotspots.
        """
        prompt = yaml.safe_load((DEMO_DIR / "prompts" / "recap.yaml").read_text())
        fields = prompt["schema"]["fields"]
        assert set(fields) == {"workstreams", "hotspots"}

    @pytest.mark.req("REQ-YG-531")
    def test_prompt_partitions_via_jinja(self) -> None:
        """File-kind partitioning is Jinja2 in the template, not model judgement."""
        text = (DEMO_DIR / "prompts" / "recap.yaml").read_text()
        assert "{%" in text, "expected Jinja2 partitioning in prompt template"

    @pytest.mark.req("REQ-YG-531")
    def test_edge_flow(self) -> None:
        """START → tool chain → partition → synthesize → finalize_recap → END."""
        from yamlgraph.compile.graph_loader import load_graph_config

        config = load_graph_config(GRAPH_PATH)
        edge_pairs = [(e["from"], e["to"]) for e in config.edges]
        assert ("START", "get_commits") in edge_pairs
        assert ("get_fr_statuses", "partition") in edge_pairs
        assert ("partition", "synthesize") in edge_pairs
        assert ("synthesize", "finalize_recap") in edge_pairs
        assert ("finalize_recap", "END") in edge_pairs


class TestRecapFailsLoudly:
    """A repo_path that is not a git repository raises — no empty-recap fallback."""

    @pytest.mark.req("REQ-YG-531")
    def test_non_git_repo_path_raises(self, tmp_path: Path) -> None:
        """First tool node raises RuntimeError before any LLM involvement."""
        from yamlgraph.tools.nodes import create_tool_node
        from yamlgraph.tools.shell import parse_tools

        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        tools = parse_tools(raw["tools"])
        node_fn = create_tool_node("get_commits", raw["nodes"]["get_commits"], tools)
        state = {"repo_path": str(tmp_path), "since": "1 week ago"}
        with pytest.raises(RuntimeError, match="get_commits"):
            node_fn(state)

    @pytest.mark.req("REQ-YG-531")
    def test_missing_convention_paths_are_silent(self, tmp_path: Path) -> None:
        """git log -- <missing-path> on a real repo exits 0 with empty output."""
        env = {
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@t",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@t",
            "PATH": "/usr/bin:/bin",
            "HOME": str(tmp_path),
        }
        subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, env=env)
        subprocess.run(
            ["git", "-C", str(tmp_path), "commit", "--allow-empty", "-q", "-m", "init"],
            check=True,
            env=env,
        )
        from yamlgraph.tools.nodes import create_tool_node
        from yamlgraph.tools.shell import parse_tools

        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        tools = parse_tools(raw["tools"])
        node_fn = create_tool_node("get_frs", raw["nodes"]["get_frs"], tools)
        state = {"repo_path": str(tmp_path), "since": "10 years ago"}
        result = node_fn(state)
        assert result["fr_changes"].strip() == ""
