"""Tests for FR-128: YAMLGraphication of Enforcer.

Validates that scripts/enforce_worktree.sh delegates all LLM phases to
examples/enforce/graph.yaml instead of using inline copilot -p calls.
"""

import os
from pathlib import Path

import pytest

_SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "scripts", "enforce_worktree.sh"
)


def _read_enforce_script() -> str:
    """Read the current enforce_worktree.sh content."""
    with open(_SCRIPT_PATH) as f:
        return f.read()


@pytest.mark.req("REQ-YG-128")
class TestEnforceScriptDelegatesToGraph:
    """Verify shell script delegates to yamlgraph graph run."""

    def test_script_invokes_yamlgraph_graph_run(self):
        """Script calls yamlgraph graph run examples/enforce/graph.yaml."""
        content = _read_enforce_script()
        assert "yamlgraph graph run examples/enforce/graph.yaml" in content

    def test_script_passes_fr_path_var(self):
        """Script passes --var fr_path to the graph run."""
        content = _read_enforce_script()
        assert "--var fr_path=" in content or "--var fr_path=" in content

    def test_script_passes_branch_var(self):
        """Script passes --var branch to the graph run."""
        content = _read_enforce_script()
        assert "--var branch=" in content or "--var branch=" in content

    def test_script_uses_full_flag(self):
        """Script uses --full flag for complete graph output."""
        content = _read_enforce_script()
        assert "--full" in content


@pytest.mark.req("REQ-YG-128")
class TestEnforceScriptNoHardcodedPrompts:
    """Verify all inline prompt strings are removed."""

    def test_no_implement_prompt_variable(self):
        """IMPLEMENT_PROMPT shell variable is removed."""
        content = _read_enforce_script()
        assert "IMPLEMENT_PROMPT" not in content

    def test_no_test_prompt_variable(self):
        """TEST_PROMPT shell variable is removed."""
        content = _read_enforce_script()
        assert "TEST_PROMPT" not in content

    def test_no_fix_prompt_variable(self):
        """FIX_PROMPT shell variable is removed."""
        content = _read_enforce_script()
        assert "FIX_PROMPT" not in content

    def test_no_copilot_dash_p_invocations(self):
        """No copilot -p calls remain in the script."""
        content = _read_enforce_script()
        assert "copilot -p" not in content


@pytest.mark.req("REQ-YG-128")
class TestEnforceScriptNoInlinePhases:
    """Verify phases 3-5 inline code is removed."""

    def test_no_precommit_retry_loop(self):
        """Pre-commit retry loop (seq 1 $MAX_PRECOMMIT_ATTEMPTS) is removed."""
        content = _read_enforce_script()
        assert "MAX_PRECOMMIT_ATTEMPTS" not in content
        assert "seq 1" not in content

    def test_no_inline_git_commit(self):
        """No inline git commit for phase 4 (only FR commit before worktree is ok)."""
        content = _read_enforce_script()
        lines = content.splitlines()
        # Count git commit occurrences - only the FR commit before worktree is allowed
        git_commit_lines = [
            line
            for line in lines
            if "git commit" in line and "# " not in line.lstrip()[:2]
        ]
        # The FR commit (line ~69) is acceptable; the phase 4 commit is not
        # After thinning, there should be at most 1 git commit (the FR pre-commit)
        assert len(git_commit_lines) <= 1, (
            f"Expected at most 1 git commit (FR pre-commit), found {len(git_commit_lines)}: "
            f"{git_commit_lines}"
        )

    def test_no_inline_gh_pr_create(self):
        """No inline gh pr create for phase 5."""
        content = _read_enforce_script()
        assert "gh pr create" not in content

    def test_no_inline_git_push_for_phase4(self):
        """No inline git push -u origin for phase 4 (FR push is ok)."""
        content = _read_enforce_script()
        assert "git push -u origin" not in content


@pytest.mark.req("REQ-YG-128")
class TestEnforceScriptRetainsLifecycle:
    """Verify worktree lifecycle operations remain in the script."""

    def test_retains_worktree_add(self):
        """git worktree add command is retained."""
        content = _read_enforce_script()
        assert "git worktree add" in content

    def test_retains_cleanup_trap(self):
        """Trap-based cleanup function is retained."""
        content = _read_enforce_script()
        assert "trap cleanup EXIT" in content

    def test_retains_venv_symlink(self):
        """Shared .venv symlink logic is retained."""
        content = _read_enforce_script()
        assert "ln -sf" in content
        assert ".venv" in content

    def test_retains_argument_validation(self):
        """Argument validation is retained."""
        content = _read_enforce_script()
        assert "Usage:" in content

    def test_retains_fr_file_check(self):
        """FR file existence check is retained."""
        content = _read_enforce_script()
        assert "not found" in content.lower() or "! -f" in content

    def test_retains_clean_working_tree_validation(self):
        """Clean working tree validation is retained."""
        content = _read_enforce_script()
        assert "validate_clean_working_tree" in content

    def test_retains_next_steps_banner(self):
        """NEXT STEPS output banner is retained."""
        content = _read_enforce_script()
        assert "NEXT STEPS" in content


@pytest.mark.req("REQ-YG-128")
class TestEnforceScriptSize:
    """Verify the script has been thinned appropriately."""

    def test_script_under_150_lines(self):
        """Thinned script should be under 150 lines (was ~205, target ~80 core + banner)."""
        content = _read_enforce_script()
        line_count = len(content.strip().splitlines())
        assert (
            line_count <= 150
        ), f"Script has {line_count} lines, expected ≤ 150 after thinning"


@pytest.mark.req("REQ-YG-128")
class TestEnforceGraphLint:
    """Verify the enforce graph passes lint."""

    def test_enforce_graph_passes_lint(self):
        """examples/enforce/graph.yaml passes yamlgraph graph lint."""
        from yamlgraph.linter.graph_linter import lint_graph

        graph_path = Path("examples/enforce/graph.yaml")
        result = lint_graph(graph_path)
        errors = [i for i in result.issues if i.severity.value == "error"]
        assert (
            len(errors) == 0
        ), f"Graph lint errors: {[f'{e.code}: {e.message}' for e in errors]}"
