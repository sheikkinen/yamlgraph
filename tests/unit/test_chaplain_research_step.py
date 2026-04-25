"""Tests for FR-257: Chaplain Research Step.

Validates that the Chaplain pipeline inserts a Research step between
Plan and Judge, with a structured research prompt and updated Judge
criteria for strategic classification.
"""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CHAPLAIN_GRAPH = REPO_ROOT / ".chaplain" / "graphs" / "copilot" / "graph.yaml"
PROMPTS_DIR = REPO_ROOT / ".chaplain" / "graphs" / "copilot" / "prompts"


def _load_graph() -> dict:
    """Load the chaplain copilot graph YAML."""
    return yaml.safe_load(CHAPLAIN_GRAPH.read_text())


# ===========================================================================
# Graph structure: research node exists and is wired correctly
# ===========================================================================


@pytest.mark.req("REQ-YG-260")
class TestResearchNodeExists:
    """Research node must exist in the chaplain copilot graph."""

    def test_research_node_in_graph(self):
        """graph.yaml must have a 'research' node."""
        graph = _load_graph()
        assert "research" in graph["nodes"], (
            "Missing 'research' node in .chaplain/graphs/copilot/graph.yaml"
        )

    def test_research_node_type_copilot(self):
        """research node must be type: copilot."""
        graph = _load_graph()
        research = graph["nodes"]["research"]
        assert research["type"] == "copilot"

    def test_research_node_has_prompt(self):
        """research node must reference 'research' prompt."""
        graph = _load_graph()
        research = graph["nodes"]["research"]
        assert research["prompt"] == "research"

    def test_research_node_state_key(self):
        """research node must write to state_key: research_brief."""
        graph = _load_graph()
        research = graph["nodes"]["research"]
        assert research["state_key"] == "research_brief"

    def test_research_node_has_cli_backend(self):
        """research node must use cli backend."""
        graph = _load_graph()
        research = graph["nodes"]["research"]
        assert research["backend"] == "cli"

    def test_research_node_resumes_plan_session(self):
        """research node must resume plan session for context continuity."""
        graph = _load_graph()
        research = graph["nodes"]["research"]
        cli_flags = research.get("cli_flags", {})
        resume_val = cli_flags.get("resume", "")
        assert "plan_result" in resume_val and "session_id" in resume_val, (
            f"research node must resume plan session, got: {resume_val}"
        )

    def test_research_node_has_drafts_dir_variable(self):
        """research node must pass drafts_dir variable."""
        graph = _load_graph()
        research = graph["nodes"]["research"]
        variables = research.get("variables", {})
        assert "drafts_dir" in variables


# ===========================================================================
# Edges: plan → research → judge
# ===========================================================================


@pytest.mark.req("REQ-YG-260")
class TestResearchEdges:
    """Research node must be wired between plan and judge."""

    def _edge_pairs(self) -> list[tuple[str, str]]:
        """Return list of (from, to) edge tuples."""
        graph = _load_graph()
        return [(e["from"], e["to"]) for e in graph["edges"]]

    def test_plan_to_research_edge(self):
        """Edge from plan → research must exist."""
        pairs = self._edge_pairs()
        assert (
            "plan",
            "research",
        ) in pairs, f"Missing plan → research edge. Edges: {pairs}"

    def test_research_to_judge_edge(self):
        """Research must connect to judge (directly or via intermediate nodes)."""
        pairs = self._edge_pairs()
        # FR-260 inserts create_worktree → write_acceptance_tests between
        # research and judge; the invariant is that research eventually leads
        # to judge through the edge chain
        research_targets = [to for (frm, to) in pairs if frm == "research"]
        assert research_targets, f"research has no outgoing edges. Edges: {pairs}"
        # Trace the chain from research to judge
        visited = set()
        frontier = set(research_targets)
        while frontier:
            node = frontier.pop()
            if node == "judge":
                break
            visited.add(node)
            frontier |= {to for (frm, to) in pairs if frm == node and to not in visited}
        else:
            raise AssertionError(f"No path from research → judge. Edges: {pairs}")

    def test_no_direct_plan_to_judge_edge(self):
        """Old plan → judge edge must be removed."""
        pairs = self._edge_pairs()
        assert ("plan", "judge") not in pairs, (
            "Direct plan → judge edge still exists; should go through research"
        )


# ===========================================================================
# State: research_brief field declared
# ===========================================================================


@pytest.mark.req("REQ-YG-260")
class TestResearchState:
    """Graph state must include research_brief."""

    def test_state_has_research_brief(self):
        """state declaration must include research_brief."""
        graph = _load_graph()
        state = graph.get("state", {})
        assert "research_brief" in state, (
            f"Missing research_brief in state. Keys: {list(state.keys())}"
        )


# ===========================================================================
# Research prompt: exists and has required sections
# ===========================================================================


@pytest.mark.req("REQ-YG-260")
class TestResearchPrompt:
    """Research prompt must exist with required instructions."""

    def test_research_prompt_file_exists(self):
        """prompts/research.yaml must exist."""
        assert (PROMPTS_DIR / "research.yaml").exists(), (
            "Missing .chaplain/graphs/copilot/prompts/research.yaml"
        )

    def test_research_prompt_has_system(self):
        """research.yaml must have a system prompt."""
        prompt = yaml.safe_load((PROMPTS_DIR / "research.yaml").read_text())
        assert "system" in prompt, "research.yaml must have 'system' key"

    def test_research_prompt_has_user(self):
        """research.yaml must have a user prompt."""
        prompt = yaml.safe_load((PROMPTS_DIR / "research.yaml").read_text())
        assert "user" in prompt, "research.yaml must have 'user' key"

    def test_research_prompt_mentions_existing_abstractions(self):
        """User prompt must instruct searching for existing abstractions."""
        prompt = yaml.safe_load((PROMPTS_DIR / "research.yaml").read_text())
        user = prompt["user"].lower()
        assert "existing abstraction" in user or "overlapping" in user

    def test_research_prompt_mentions_diary(self):
        """User prompt must reference docs/diary/ for precedents."""
        prompt = yaml.safe_load((PROMPTS_DIR / "research.yaml").read_text())
        user = prompt["user"]
        assert "diary" in user.lower()

    def test_research_prompt_mentions_classification(self):
        """User prompt must include classification signal."""
        prompt = yaml.safe_load((PROMPTS_DIR / "research.yaml").read_text())
        user = prompt["user"].lower()
        assert "classification" in user or "classify" in user

    def test_research_prompt_mentions_usage_evidence(self):
        """User prompt must instruct gathering usage evidence."""
        prompt = yaml.safe_load((PROMPTS_DIR / "research.yaml").read_text())
        user = prompt["user"].lower()
        assert "usage" in user

    def test_research_prompt_references_feature_requests(self):
        """User prompt must reference feature-requests/ directory."""
        prompt = yaml.safe_load((PROMPTS_DIR / "research.yaml").read_text())
        assert "feature-requests/" in prompt["user"]


# ===========================================================================
# Judge prompt: includes strategic classification criterion
# ===========================================================================


@pytest.mark.req("REQ-YG-260")
class TestJudgePromptUpdated:
    """Judge prompt must include strategic classification based on research brief."""

    def test_judge_mentions_research_brief(self):
        """Judge prompt must reference the research brief."""
        prompt = yaml.safe_load((PROMPTS_DIR / "judge.yaml").read_text())
        user = prompt["user"].lower()
        assert "research brief" in user or "research" in user

    def test_judge_mentions_framework_primitive(self):
        """Judge prompt must include 'framework primitive' classification."""
        prompt = yaml.safe_load((PROMPTS_DIR / "judge.yaml").read_text())
        user = prompt["user"].lower()
        assert "framework primitive" in user or "primitive" in user

    def test_judge_mentions_pattern_documentation(self):
        """Judge prompt must include 'pattern documentation' classification."""
        prompt = yaml.safe_load((PROMPTS_DIR / "judge.yaml").read_text())
        user = prompt["user"].lower()
        assert "pattern documentation" in user or "pattern doc" in user

    def test_judge_mentions_contrib(self):
        """Judge prompt must include 'contrib' classification."""
        prompt = yaml.safe_load((PROMPTS_DIR / "judge.yaml").read_text())
        user = prompt["user"].lower()
        assert "contrib" in user


# ===========================================================================
# Graph lints clean
# ===========================================================================


@pytest.mark.req("REQ-YG-260")
class TestGraphLintsClean:
    """The modified chaplain graph must lint without errors."""

    def test_graph_yaml_valid(self):
        """graph.yaml must be valid YAML that loads without error."""
        graph = _load_graph()
        assert graph["version"] == "1.0"
        assert "nodes" in graph
        assert "edges" in graph

    def test_all_edge_targets_exist(self):
        """Every edge target must be a declared node or START/END."""
        graph = _load_graph()
        node_names = set(graph["nodes"].keys()) | {"START", "END"}
        for edge in graph["edges"]:
            assert edge["from"] in node_names, (
                f"Edge 'from' references unknown node: {edge['from']}"
            )
            assert edge["to"] in node_names, (
                f"Edge 'to' references unknown node: {edge['to']}"
            )

    def test_all_nodes_have_edges(self):
        """Every node must appear in at least one edge."""
        graph = _load_graph()
        edge_nodes = set()
        for edge in graph["edges"]:
            edge_nodes.add(edge["from"])
            edge_nodes.add(edge["to"])
        for node_name in graph["nodes"]:
            assert node_name in edge_nodes, (
                f"Node '{node_name}' not referenced in any edge"
            )
