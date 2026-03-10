"""Tests for FR-173: Bug-Fix Pipeline with Condemning Test Phase.

Validates that the bugfix pipeline exists with 4 phases (condemn → fix → verify → submit),
scripts/bugfix_worktree.sh delegates to the graph, watch.sh routes Bug-type FRs to the
bugfix pipeline, and examples/bugfix/README.md documents the pipeline.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BUGFIX_GRAPH = REPO_ROOT / "examples" / "bugfix" / "graph.yaml"
BUGFIX_PROMPTS = REPO_ROOT / "examples" / "bugfix" / "prompts"
BUGFIX_README = REPO_ROOT / "examples" / "bugfix" / "README.md"
BUGFIX_SCRIPT = REPO_ROOT / "scripts" / "bugfix_worktree.sh"
WATCH_SCRIPT = REPO_ROOT / ".chaplain" / "watch.sh"


def _read(path: Path) -> str:
    return path.read_text()


# ---------------------------------------------------------------------------
# 1. Graph structure tests
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-157")
class TestBugfixGraphStructure:
    """examples/bugfix/graph.yaml defines a 4-phase pipeline."""

    def test_graph_file_exists(self):
        assert BUGFIX_GRAPH.exists(), "examples/bugfix/graph.yaml must exist"

    def test_graph_has_condemn_node(self):
        content = _read(BUGFIX_GRAPH)
        assert "condemn:" in content, "Graph must have a condemn node"

    def test_graph_has_fix_node(self):
        content = _read(BUGFIX_GRAPH)
        assert "fix:" in content, "Graph must have a fix node"

    def test_graph_has_verify_node(self):
        content = _read(BUGFIX_GRAPH)
        assert "verify:" in content, "Graph must have a verify node"

    def test_graph_has_submit_node(self):
        content = _read(BUGFIX_GRAPH)
        assert "submit_pr:" in content, "Graph must have a submit_pr node"

    def test_all_nodes_are_copilot_type(self):
        content = _read(BUGFIX_GRAPH)
        # Every node block should have type: copilot
        node_types = re.findall(r"type:\s*(\w+)", content)
        for t in node_types:
            assert t == "copilot", f"Expected type: copilot, got type: {t}"

    def test_graph_edges_form_condemn_to_submit_chain(self):
        """Edges: START → condemn → fix → verify → submit_pr → END."""
        content = _read(BUGFIX_GRAPH)
        assert "START" in content
        assert "END" in content
        # Must have edges connecting each phase in order
        edge_section = content[content.index("edges:") :]
        assert "condemn" in edge_section
        assert "fix" in edge_section
        assert "verify" in edge_section
        assert "submit_pr" in edge_section

    def test_graph_session_continuations(self):
        """Downstream phases resume the condemn session (FR-105 pattern)."""
        content = _read(BUGFIX_GRAPH)
        # fix, verify, submit_pr should reference condemn_result.session_id
        assert "condemn_result.session_id" in content

    def test_graph_passes_lint(self):
        """examples/bugfix/graph.yaml passes yamlgraph graph lint."""
        from yamlgraph.linter.graph_linter import lint_graph

        result = lint_graph(BUGFIX_GRAPH)
        errors = [i for i in result.issues if i.severity == "error"]
        assert (
            len(errors) == 0
        ), f"Graph lint errors: {[f'{e.code}: {e.message}' for e in errors]}"


# ---------------------------------------------------------------------------
# 2. Condemn prompt contract
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-157")
class TestCondemnPromptContract:
    """Condemn phase prompt enforces the condemning test protocol."""

    def test_condemn_prompt_exists(self):
        condemn_prompt = BUGFIX_PROMPTS / "bugfix-condemn.yaml"
        assert condemn_prompt.exists(), "prompts/bugfix-condemn.yaml must exist"

    def test_condemn_prompt_mentions_failing_test(self):
        content = _read(BUGFIX_PROMPTS / "bugfix-condemn.yaml")
        assert "fail" in content.lower(), "Condemn prompt must mention failure"

    def test_condemn_prompt_mentions_unmodified_code(self):
        content = _read(BUGFIX_PROMPTS / "bugfix-condemn.yaml")
        assert "unmodified" in content.lower() or "current" in content.lower()

    def test_condemn_prompt_mentions_skip_pytest(self):
        """RED commit uses SKIP=pytest to bypass test runner but keep linting."""
        content = _read(BUGFIX_PROMPTS / "bugfix-condemn.yaml")
        assert "SKIP=pytest" in content

    def test_condemn_prompt_mentions_req_marker(self):
        """Condemn prompt instructs adding @pytest.mark.req."""
        content = _read(BUGFIX_PROMPTS / "bugfix-condemn.yaml")
        assert "pytest.mark.req" in content


# ---------------------------------------------------------------------------
# 3. Fix, verify, submit prompts exist
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-157")
class TestBugfixPrompts:
    """All four prompts exist and follow the YAML prompt pattern."""

    @pytest.mark.parametrize(
        "name",
        [
            "bugfix-condemn.yaml",
            "bugfix-fix.yaml",
            "bugfix-verify.yaml",
            "bugfix-submit-pr.yaml",
        ],
    )
    def test_prompt_exists(self, name):
        path = BUGFIX_PROMPTS / name
        assert path.exists(), f"Missing prompt: {name}"

    @pytest.mark.parametrize(
        "name",
        [
            "bugfix-condemn.yaml",
            "bugfix-fix.yaml",
            "bugfix-verify.yaml",
            "bugfix-submit-pr.yaml",
        ],
    )
    def test_prompt_has_system_and_user_blocks(self, name):
        content = _read(BUGFIX_PROMPTS / name)
        assert "system:" in content, f"{name} must have system: block"
        assert "user:" in content, f"{name} must have user: block"

    def test_fix_prompt_mentions_minimal_change(self):
        content = _read(BUGFIX_PROMPTS / "bugfix-fix.yaml")
        assert "minimal" in content.lower()

    def test_verify_prompt_mentions_pytest(self):
        content = _read(BUGFIX_PROMPTS / "bugfix-verify.yaml")
        assert "pytest" in content.lower()

    def test_submit_prompt_mentions_fix_commit_type(self):
        content = _read(BUGFIX_PROMPTS / "bugfix-submit-pr.yaml")
        assert "fix(" in content


# ---------------------------------------------------------------------------
# 4. Bugfix worktree script
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-157")
class TestBugfixWorktreeScript:
    """scripts/bugfix_worktree.sh mirrors enforce_worktree.sh for bugs."""

    def test_script_exists(self):
        assert BUGFIX_SCRIPT.exists(), "scripts/bugfix_worktree.sh must exist"

    def test_script_is_executable(self):
        import os

        assert os.access(BUGFIX_SCRIPT, os.X_OK), "Script must be executable"

    def test_script_invokes_bugfix_graph(self):
        content = _read(BUGFIX_SCRIPT)
        assert "yamlgraph graph run examples/bugfix/graph.yaml" in content

    def test_script_passes_fr_path_var(self):
        content = _read(BUGFIX_SCRIPT)
        assert "--var fr_path=" in content

    def test_script_passes_branch_var(self):
        content = _read(BUGFIX_SCRIPT)
        assert "--var branch=" in content

    def test_script_uses_full_flag(self):
        content = _read(BUGFIX_SCRIPT)
        assert "--full" in content

    def test_script_has_cleanup_trap(self):
        content = _read(BUGFIX_SCRIPT)
        assert "trap cleanup EXIT" in content

    def test_script_has_worktree_add(self):
        content = _read(BUGFIX_SCRIPT)
        assert "git worktree add" in content

    def test_script_has_venv_symlink(self):
        content = _read(BUGFIX_SCRIPT)
        assert "ln -sf" in content and ".venv" in content

    def test_script_has_bare_guard(self):
        """FR-139: Guard against bare=true corruption."""
        content = _read(BUGFIX_SCRIPT)
        assert "core.bare" in content

    def test_script_unsets_git_env(self):
        """FR-140: Unset GIT_DIR/GIT_WORK_TREE."""
        content = _read(BUGFIX_SCRIPT)
        assert "unset GIT_DIR" in content

    def test_script_has_no_copilot_dash_p(self):
        """No inline copilot -p calls, delegates to graph."""
        content = _read(BUGFIX_SCRIPT)
        assert "copilot -p" not in content


# ---------------------------------------------------------------------------
# 5. Watch.sh routing
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-157")
class TestWatchShRouting:
    """watch.sh routes Type: Bug FRs to the bugfix pipeline."""

    def test_watch_detects_bug_type(self):
        content = _read(WATCH_SCRIPT)
        assert "Bug" in content, "watch.sh must detect 'Type.*Bug' FRs"

    def test_watch_spawns_bugfix_worktree(self):
        content = _read(WATCH_SCRIPT)
        assert "bugfix_worktree.sh" in content


# ---------------------------------------------------------------------------
# 6. Documentation
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-157")
class TestBugfixReadme:
    """examples/bugfix/README.md documents the pipeline."""

    def test_readme_exists(self):
        assert BUGFIX_README.exists(), "examples/bugfix/README.md must exist"

    def test_readme_mentions_condemn(self):
        content = _read(BUGFIX_README)
        assert "condemn" in content.lower()

    def test_readme_mentions_four_phases(self):
        """README documents all four phases."""
        content = _read(BUGFIX_README)
        for phase in ["condemn", "fix", "verify", "submit"]:
            assert phase in content.lower(), f"README must mention {phase} phase"
