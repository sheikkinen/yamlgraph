"""Tests for FR-183: Simplify Enforce Pipeline.

Validates the simplified 4-node enforce pipeline structure:
implement → test_and_demo → critique_and_distill → finalize
"""

from pathlib import Path

import pytest
import yaml

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GRAPH_PATH = Path(".chaplain/graphs/enforce/graph.yaml")
_PROMPTS_DIR = Path(".chaplain/graphs/enforce/prompts")


def _load_graph() -> dict:
    """Load and return the enforce graph YAML as a dict."""
    with open(_GRAPH_PATH) as f:
        return yaml.safe_load(f)


# =============================================================================
# AC-1: Graph has exactly 4 nodes
# =============================================================================


@pytest.mark.req("REQ-YG-001")  # Config Loading & Validation
class TestFourNodeStructure:
    """FR-183 AC-1: Graph has exactly 4 nodes."""

    def test_graph_has_exactly_four_nodes(self):
        """Graph should have exactly 4 nodes after simplification."""
        graph = _load_graph()
        expected_nodes = {
            "implement",
            "test_and_demo",
            "critique_and_distill",
            "finalize",
        }
        actual_nodes = set(graph["nodes"].keys())
        assert actual_nodes == expected_nodes, (
            f"Expected 4 nodes {expected_nodes}, got {actual_nodes}"
        )

    def test_no_critique_node(self):
        """Old 'critique' node should be removed."""
        graph = _load_graph()
        assert "critique" not in graph["nodes"], "Old 'critique' node should be removed"

    def test_no_refine_node(self):
        """Old 'refine' node should be removed."""
        graph = _load_graph()
        assert "refine" not in graph["nodes"], "Old 'refine' node should be removed"

    def test_no_distill_reflection_node(self):
        """Old 'distill_reflection' node should be removed."""
        graph = _load_graph()
        assert "distill_reflection" not in graph["nodes"], (
            "Old 'distill_reflection' node should be removed"
        )

    def test_no_precommit_check_node(self):
        """Old 'precommit_check' node should be removed."""
        graph = _load_graph()
        assert "precommit_check" not in graph["nodes"], (
            "Old 'precommit_check' node should be removed"
        )

    def test_no_submit_pr_node(self):
        """Old 'submit_pr' node should be removed."""
        graph = _load_graph()
        assert "submit_pr" not in graph["nodes"], (
            "Old 'submit_pr' node should be removed"
        )


# =============================================================================
# AC-2: Graph has exactly 5 edges forming linear chain
# =============================================================================


@pytest.mark.req("REQ-YG-001")
class TestLinearEdges:
    """FR-183 AC-2: 5 edges forming START→implement→test_and_demo→critique_and_distill→finalize→END."""

    def test_edge_count(self):
        """Graph should have exactly 5 edges."""
        graph = _load_graph()
        edges = graph.get("edges", [])
        assert len(edges) == 5, f"Expected 5 edges, got {len(edges)}"

    def test_start_to_implement(self):
        """First edge: START → implement."""
        graph = _load_graph()
        edges = graph.get("edges", [])
        start_edge = {"from": "START", "to": "implement"}
        assert start_edge in edges

    def test_implement_to_test(self):
        """Second edge: implement → test_and_demo."""
        graph = _load_graph()
        edges = graph.get("edges", [])
        edge = {"from": "implement", "to": "test_and_demo"}
        assert edge in edges

    def test_test_to_critique_and_distill(self):
        """Third edge: test_and_demo → critique_and_distill."""
        graph = _load_graph()
        edges = graph.get("edges", [])
        edge = {"from": "test_and_demo", "to": "critique_and_distill"}
        assert edge in edges

    def test_critique_and_distill_to_finalize(self):
        """Fourth edge: critique_and_distill → finalize."""
        graph = _load_graph()
        edges = graph.get("edges", [])
        edge = {"from": "critique_and_distill", "to": "finalize"}
        assert edge in edges

    def test_finalize_to_end(self):
        """Fifth edge: finalize → END."""
        graph = _load_graph()
        edges = graph.get("edges", [])
        end_edge = {"from": "finalize", "to": "END"}
        assert end_edge in edges


# =============================================================================
# AC-3: No loop_limits or loop_exits
# =============================================================================


@pytest.mark.req("REQ-YG-001")
class TestNoLoopConfig:
    """FR-183 AC-3: No loop_limits or loop_exits in graph config."""

    def test_no_loop_limits(self):
        """Graph should not have loop_limits after simplification."""
        graph = _load_graph()
        assert "loop_limits" not in graph, "loop_limits should be removed"

    def test_no_loop_exits(self):
        """Graph should not have loop_exits after simplification."""
        graph = _load_graph()
        assert "loop_exits" not in graph, "loop_exits should be removed"


# =============================================================================
# AC-4 & AC-5: New prompts exist
# =============================================================================


@pytest.mark.req("REQ-YG-012")  # Prompt Execution
class TestNewPrompts:
    """FR-183 AC-4/AC-5: New merged prompts exist."""

    def test_critique_and_distill_prompt_exists(self):
        """enforce-critique-and-distill.yaml should exist."""
        prompt_path = _PROMPTS_DIR / "enforce-critique-and-distill.yaml"
        assert prompt_path.exists(), f"Missing prompt: {prompt_path}"

    def test_finalize_prompt_exists(self):
        """enforce-finalize.yaml should exist."""
        prompt_path = _PROMPTS_DIR / "enforce-finalize.yaml"
        assert prompt_path.exists(), f"Missing prompt: {prompt_path}"


# =============================================================================
# AC-6: Old prompts deleted
# =============================================================================


@pytest.mark.req("REQ-YG-012")
class TestOldPromptsDeleted:
    """FR-183 AC-6: Old prompts are deleted."""

    def test_no_critique_prompt(self):
        """enforce-critique.yaml should be deleted."""
        prompt_path = _PROMPTS_DIR / "enforce-critique.yaml"
        assert not prompt_path.exists(), f"Old prompt should be deleted: {prompt_path}"

    def test_no_distill_prompt(self):
        """enforce-distill.yaml should be deleted."""
        prompt_path = _PROMPTS_DIR / "enforce-distill.yaml"
        assert not prompt_path.exists(), f"Old prompt should be deleted: {prompt_path}"

    def test_no_refine_prompt(self):
        """enforce-refine.yaml should be deleted."""
        prompt_path = _PROMPTS_DIR / "enforce-refine.yaml"
        assert not prompt_path.exists(), f"Old prompt should be deleted: {prompt_path}"

    def test_no_precommit_prompt(self):
        """enforce-precommit.yaml should be deleted."""
        prompt_path = _PROMPTS_DIR / "enforce-precommit.yaml"
        assert not prompt_path.exists(), f"Old prompt should be deleted: {prompt_path}"

    def test_no_submit_pr_prompt(self):
        """enforce-submit-pr.yaml should be deleted."""
        prompt_path = _PROMPTS_DIR / "enforce-submit-pr.yaml"
        assert not prompt_path.exists(), f"Old prompt should be deleted: {prompt_path}"


# =============================================================================
# AC-7: State schema has no orphaned keys
# =============================================================================


@pytest.mark.req("REQ-YG-001")
class TestStateSchemaClean:
    """FR-183 AC-7: No orphaned state keys."""

    def test_no_refine_result(self):
        """refine_result should be removed from state."""
        graph = _load_graph()
        state = graph.get("state", {})
        assert "refine_result" not in state

    def test_no_reflection_draft(self):
        """reflection_draft should be removed from state."""
        graph = _load_graph()
        state = graph.get("state", {})
        assert "reflection_draft" not in state

    def test_no_precommit_result(self):
        """precommit_result should be removed from state."""
        graph = _load_graph()
        state = graph.get("state", {})
        assert "precommit_result" not in state

    def test_no_pr_result(self):
        """pr_result should be removed from state."""
        graph = _load_graph()
        state = graph.get("state", {})
        assert "pr_result" not in state

    def test_has_finalize_result(self):
        """finalize_result should be in state."""
        graph = _load_graph()
        state = graph.get("state", {})
        assert "finalize_result" in state


# =============================================================================
# AC-10: Graph header comments updated
# =============================================================================


@pytest.mark.req("REQ-YG-001")
class TestHeaderComments:
    """FR-183 AC-10: Graph header comments reflect 4-phase pipeline."""

    def test_header_mentions_four_phases(self):
        """Graph file should mention 4-phase/4-node structure in comments."""
        with open(_GRAPH_PATH) as f:
            content = f.read()
        # Check for four-phase description
        assert "four" in content.lower() or "4" in content, (
            "Graph header should mention 4-phase pipeline"
        )
