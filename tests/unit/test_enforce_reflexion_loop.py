"""Tests for FR-169: Enforce Pipeline Reflexion Loop.

Validates that the enforce pipeline includes a critique → refine reflexion loop
between test_and_demo and precommit_check, with diary reflection distillation
on loop exit.
"""

import os
import subprocess
import textwrap
from pathlib import Path

import pytest
import yaml

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GRAPH_PATH = Path("examples/enforce/graph.yaml")
_PROMPTS_DIR = Path("examples/enforce/prompts")
_FINALIZE_SCRIPT = Path("scripts/finalize_merge.sh")

# Strip git env vars that pre-commit injects
_GIT_ENV_POISON = {"GIT_INDEX_FILE", "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"}


def _clean_git_env(**extra: str) -> dict[str, str]:
    """Return os.environ minus git vars that pollute temp-repo subprocess calls."""
    env = {k: v for k, v in os.environ.items() if k not in _GIT_ENV_POISON}
    env.update(extra)
    return env


def _load_graph() -> dict:
    """Load and return the enforce graph YAML as a dict."""
    with open(_GRAPH_PATH) as f:
        return yaml.safe_load(f)


# =============================================================================
# AC-1: critique copilot node added after test_and_demo
# =============================================================================


@pytest.mark.req("REQ-YG-159")
class TestCritiqueNode:
    """Critique node exists and is properly configured."""

    def test_critique_node_exists(self):
        """Enforce graph has a 'critique' node."""
        graph = _load_graph()
        assert "critique" in graph["nodes"]

    def test_critique_node_is_copilot_type(self):
        """Critique node uses copilot type for tool access."""
        graph = _load_graph()
        assert graph["nodes"]["critique"]["type"] == "copilot"

    def test_critique_node_has_state_key(self):
        """Critique node writes to critique_result state key."""
        graph = _load_graph()
        assert graph["nodes"]["critique"]["state_key"] == "critique_result"

    def test_critique_node_has_prompt(self):
        """Critique node references enforce-critique prompt."""
        graph = _load_graph()
        assert graph["nodes"]["critique"]["prompt"] == "enforce-critique"

    def test_critique_node_resumes_session(self):
        """Critique node continues the implement session."""
        graph = _load_graph()
        cli_flags = graph["nodes"]["critique"].get("cli_flags", {})
        assert "resume" in cli_flags
        assert "implement_result.session_id" in cli_flags["resume"]

    def test_critique_node_has_timeout(self):
        """Critique node has a bounded timeout."""
        graph = _load_graph()
        assert graph["nodes"]["critique"]["timeout"] == 300

    def test_test_and_demo_routes_to_critique(self):
        """Edge from test_and_demo goes to critique (not precommit_check)."""
        graph = _load_graph()
        edges = graph["edges"]
        test_demo_targets = [e["to"] for e in edges if e["from"] == "test_and_demo"]
        assert "critique" in test_demo_targets
        assert "precommit_check" not in test_demo_targets


# =============================================================================
# AC-2: refine copilot node with conditional edge from critique
# =============================================================================


@pytest.mark.req("REQ-YG-159")
class TestRefineNode:
    """Refine node exists with conditional routing from critique."""

    def test_refine_node_exists(self):
        """Enforce graph has a 'refine' node."""
        graph = _load_graph()
        assert "refine" in graph["nodes"]

    def test_refine_node_is_copilot_type(self):
        """Refine node uses copilot type."""
        graph = _load_graph()
        assert graph["nodes"]["refine"]["type"] == "copilot"

    def test_refine_node_has_prompt(self):
        """Refine node references enforce-refine prompt."""
        graph = _load_graph()
        assert graph["nodes"]["refine"]["prompt"] == "enforce-refine"

    def test_refine_node_resumes_session(self):
        """Refine node continues the implement session."""
        graph = _load_graph()
        cli_flags = graph["nodes"]["refine"].get("cli_flags", {})
        assert "resume" in cli_flags

    def test_refine_node_has_timeout(self):
        """Refine node has a bounded timeout."""
        graph = _load_graph()
        assert graph["nodes"]["refine"]["timeout"] == 300

    def test_critique_to_refine_has_condition(self):
        """Edge from critique to refine has score threshold condition."""
        graph = _load_graph()
        edges = graph["edges"]
        crit_to_refine = [
            e for e in edges if e["from"] == "critique" and e["to"] == "refine"
        ]
        assert len(crit_to_refine) == 1
        assert "condition" in crit_to_refine[0]
        cond = crit_to_refine[0]["condition"]
        assert "critique_result.score" in cond
        assert "< 0.85" in cond or "<0.85" in cond

    def test_refine_routes_back_to_critique(self):
        """Edge from refine goes back to critique (loop)."""
        graph = _load_graph()
        edges = graph["edges"]
        refine_targets = [e["to"] for e in edges if e["from"] == "refine"]
        assert "critique" in refine_targets


# =============================================================================
# AC-3: refine writes to refine_result (not test_result)
# =============================================================================


@pytest.mark.req("REQ-YG-159")
class TestStateKeySeparation:
    """Refine node writes to separate state key to preserve test results."""

    def test_refine_uses_refine_result_key(self):
        """Refine node writes to refine_result state key."""
        graph = _load_graph()
        assert graph["nodes"]["refine"]["state_key"] == "refine_result"

    def test_refine_does_not_use_test_result_key(self):
        """Refine node must NOT use test_result state key."""
        graph = _load_graph()
        assert graph["nodes"]["refine"]["state_key"] != "test_result"

    def test_state_declares_refine_result(self):
        """Graph state declares refine_result field."""
        graph = _load_graph()
        assert "refine_result" in graph["state"]

    def test_state_declares_critique_result(self):
        """Graph state declares critique_result field."""
        graph = _load_graph()
        assert "critique_result" in graph["state"]

    def test_state_declares_reflection_draft(self):
        """Graph state declares reflection_draft field."""
        graph = _load_graph()
        assert "reflection_draft" in graph["state"]


# =============================================================================
# AC-4: Loop limits (critique=3, refine=2)
# =============================================================================


@pytest.mark.req("REQ-YG-159")
class TestLoopLimits:
    """Reflexion loop is bounded by loop_limits."""

    def test_loop_limits_defined(self):
        """Graph defines loop_limits section."""
        graph = _load_graph()
        assert "loop_limits" in graph

    def test_critique_loop_limit(self):
        """Critique node limited to 3 iterations."""
        graph = _load_graph()
        assert graph["loop_limits"]["critique"] == 3

    def test_refine_loop_limit(self):
        """Refine node limited to 2 iterations."""
        graph = _load_graph()
        assert graph["loop_limits"]["refine"] == 2


# =============================================================================
# AC-5: loop_exits configured
# =============================================================================


@pytest.mark.req("REQ-YG-159")
class TestLoopExits:
    """Loop exits ensure post-loop pipeline continues."""

    def test_loop_exits_defined(self):
        """Graph defines loop_exits section."""
        graph = _load_graph()
        assert "loop_exits" in graph

    def test_critique_loop_exit_target(self):
        """Critique loop exit routes to distill_reflection (not END)."""
        graph = _load_graph()
        assert graph["loop_exits"]["critique"] == "distill_reflection"


# =============================================================================
# AC-6: distill_reflection copilot node
# =============================================================================


@pytest.mark.req("REQ-YG-159")
class TestDistillReflectionNode:
    """Distill reflection node generates diary draft."""

    def test_distill_node_exists(self):
        """Enforce graph has a 'distill_reflection' node."""
        graph = _load_graph()
        assert "distill_reflection" in graph["nodes"]

    def test_distill_node_is_copilot_type(self):
        """Distill node uses copilot type."""
        graph = _load_graph()
        assert graph["nodes"]["distill_reflection"]["type"] == "copilot"

    def test_distill_node_state_key(self):
        """Distill node writes to reflection_draft state key."""
        graph = _load_graph()
        assert graph["nodes"]["distill_reflection"]["state_key"] == "reflection_draft"

    def test_distill_node_has_prompt(self):
        """Distill node references enforce-distill prompt."""
        graph = _load_graph()
        assert graph["nodes"]["distill_reflection"]["prompt"] == "enforce-distill"

    def test_distill_node_resumes_session(self):
        """Distill node continues the implement session."""
        graph = _load_graph()
        cli_flags = graph["nodes"]["distill_reflection"].get("cli_flags", {})
        assert "resume" in cli_flags

    def test_distill_node_has_timeout(self):
        """Distill node has a bounded timeout."""
        graph = _load_graph()
        assert graph["nodes"]["distill_reflection"]["timeout"] == 300

    def test_distill_routes_to_precommit(self):
        """Edge from distill_reflection goes to precommit_check."""
        graph = _load_graph()
        edges = graph["edges"]
        distill_targets = [e["to"] for e in edges if e["from"] == "distill_reflection"]
        assert "precommit_check" in distill_targets


# =============================================================================
# AC-8/9/10: Prompt files exist
# =============================================================================


@pytest.mark.req("REQ-YG-159")
class TestPromptFiles:
    """New prompt YAML files exist with required content."""

    def test_enforce_critique_prompt_exists(self):
        """enforce-critique.yaml prompt file exists."""
        assert (_PROMPTS_DIR / "enforce-critique.yaml").is_file()

    def test_enforce_refine_prompt_exists(self):
        """enforce-refine.yaml prompt file exists."""
        assert (_PROMPTS_DIR / "enforce-refine.yaml").is_file()

    def test_enforce_distill_prompt_exists(self):
        """enforce-distill.yaml prompt file exists."""
        assert (_PROMPTS_DIR / "enforce-distill.yaml").is_file()

    def test_critique_prompt_mentions_acceptance_criteria(self):
        """Critique prompt instructs evaluation against FR acceptance criteria."""
        content = (_PROMPTS_DIR / "enforce-critique.yaml").read_text()
        assert "acceptance criteria" in content.lower()

    def test_critique_prompt_mentions_git_diff(self):
        """Critique prompt instructs reviewing git diff."""
        content = (_PROMPTS_DIR / "enforce-critique.yaml").read_text()
        assert "git diff" in content.lower()

    def test_refine_prompt_mentions_feedback(self):
        """Refine prompt receives critique feedback."""
        content = (_PROMPTS_DIR / "enforce-refine.yaml").read_text()
        assert "feedback" in content.lower()

    def test_distill_prompt_mentions_diary(self):
        """Distill prompt generates diary reflection."""
        content = (_PROMPTS_DIR / "enforce-distill.yaml").read_text()
        assert "diary" in content.lower() or "reflection" in content.lower()

    def test_distill_prompt_mentions_trap_vocabulary(self):
        """Distill prompt references Scripture's trap vocabulary."""
        content = (_PROMPTS_DIR / "enforce-distill.yaml").read_text()
        assert "trap" in content.lower()
        assert "seed" in content.lower()


# =============================================================================
# AC-12: Enforce graph still lints
# =============================================================================


@pytest.mark.req("REQ-YG-159")
class TestEnforceGraphLint:
    """Updated enforce graph passes lint validation."""

    def test_enforce_graph_passes_lint(self):
        """examples/enforce/graph.yaml passes yamlgraph graph lint."""
        from yamlgraph.linter.graph_linter import lint_graph

        result = lint_graph(_GRAPH_PATH)
        errors = [i for i in result.issues if i.severity.value == "error"]
        assert (
            len(errors) == 0
        ), f"Graph lint errors: {[f'{e.code}: {e.message}' for e in errors]}"


# =============================================================================
# AC-13: Full edge flow verification
# =============================================================================


@pytest.mark.req("REQ-YG-159")
class TestEdgeFlow:
    """Complete edge flow through reflexion loop."""

    def test_critique_quality_gate_edge(self):
        """Edge from critique to distill_reflection when score >= 0.85."""
        graph = _load_graph()
        edges = graph["edges"]
        quality_edges = [
            e
            for e in edges
            if e["from"] == "critique" and e["to"] == "distill_reflection"
        ]
        assert len(quality_edges) == 1
        cond = quality_edges[0]["condition"]
        assert ">= 0.85" in cond or ">=0.85" in cond

    def test_full_pipeline_flow(self):
        """Verify the full pipeline edge chain."""
        graph = _load_graph()
        edges = graph["edges"]

        # Build adjacency list
        adj: dict[str, list[str]] = {}
        for e in edges:
            adj.setdefault(e["from"], []).append(e["to"])

        # START → implement → test_and_demo → critique
        assert "implement" in adj["START"]
        assert "test_and_demo" in adj["implement"]
        assert "critique" in adj["test_and_demo"]

        # critique → refine (loop) and critique → distill_reflection (exit)
        assert "refine" in adj["critique"]
        assert "distill_reflection" in adj["critique"]

        # refine → critique (loop back)
        assert "critique" in adj["refine"]

        # distill_reflection → precommit_check → submit_pr → END
        assert "precommit_check" in adj["distill_reflection"]
        assert "submit_pr" in adj["precommit_check"]
        assert "END" in adj["submit_pr"]


# =============================================================================
# AC-15: Timeout budget
# =============================================================================


@pytest.mark.req("REQ-YG-159")
class TestTimeoutBudget:
    """Total worst-case timeout increase ≤ 30 min (1800s)."""

    def test_new_nodes_timeout_sum(self):
        """Sum of new node timeouts ≤ 1800s worst-case."""
        graph = _load_graph()
        nodes = graph["nodes"]
        # Worst case: 3 critique + 2 refine + 1 distill
        critique_timeout = nodes["critique"]["timeout"]
        refine_timeout = nodes["refine"]["timeout"]
        distill_timeout = nodes["distill_reflection"]["timeout"]

        worst_case = (3 * critique_timeout) + (2 * refine_timeout) + distill_timeout
        assert (
            worst_case <= 1800
        ), f"Worst-case timeout {worst_case}s exceeds 30min budget"


# =============================================================================
# AC-11: finalize_merge.sh skip-if-exists guard
# =============================================================================


@pytest.mark.req("REQ-YG-159")
class TestFinalizeMergeSkipGuard:
    """finalize_merge.sh skips diary stub when reflection already exists."""

    def test_finalize_script_has_skip_guard(self):
        """Script checks if diary file exists before creating stub."""
        content = _FINALIZE_SCRIPT.read_text()
        assert "! -f" in content or "-f" in content
        # The guard should be around the cat > block
        assert "DIARY_ENTRY" in content

    def test_finalize_skips_existing_reflection(self, tmp_path):
        """When reflection file already exists, finalize does not overwrite it."""
        repo = self._make_repo(tmp_path)
        fr_rel = self._write_fr(repo, "FR-300-skip-test.md")

        # Pre-create the diary reflection (as pipeline would)
        diary_dir = repo / "docs" / "diary"
        # Find what date the script would use
        import datetime

        date_str = datetime.date.today().strftime("%Y-%m-%d")
        diary_file = diary_dir / f"{date_str}-reflection-FR-300.md"
        diary_file.write_text(
            "## Pipeline-generated reflection\n\n"
            "**Trap:** quick_confidence\n"
            "**Heuristic:** Test before reading\n"
            "**Seed:** Can we automate this?\n"
        )

        # Run finalize — should NOT overwrite
        self._run_finalize(repo, fr_rel)

        content = diary_file.read_text()
        assert "Pipeline-generated reflection" in content
        assert "[What cognitive trap" not in content

    # ── Helpers (copied from test_finalize_merge.py pattern) ──

    @staticmethod
    def _make_repo(tmp_path):
        """Bootstrap a minimal git repo on branch 'main'."""
        repo = tmp_path / "repo"
        repo.mkdir()
        env = _clean_git_env()

        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=repo,
            check=True,
            capture_output=True,
            env=env,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo,
            check=True,
            capture_output=True,
            env=env,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo,
            check=True,
            capture_output=True,
            env=env,
        )

        changelog = repo / "CHANGELOG.md"
        changelog.write_text(
            textwrap.dedent("""\
            # Changelog

            ## [Unreleased]

            ### Added
            - **FR-100 Existing Feature**: Some existing entry (REQ-YG-100)
        """)
        )

        (repo / "docs").mkdir()
        (repo / "docs" / "diary").mkdir()
        (repo / "feature-requests").mkdir()
        (repo / "tmp").mkdir()

        subprocess.run(
            ["git", "add", "."], cwd=repo, check=True, capture_output=True, env=env
        )
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=repo,
            check=True,
            capture_output=True,
            env=env,
        )
        return repo

    @staticmethod
    def _write_fr(repo, filename):
        """Write a feature request file and commit it."""
        fr_path = repo / "feature-requests" / filename
        fr_num = (
            filename.replace(".md", "").split("-")[0]
            + "-"
            + filename.replace(".md", "").split("-")[1]
        )
        fr_path.write_text(
            f"# Feature Request: {fr_num.upper()} Test Feature\n\n"
            f"**Status:** Approved\n\n"
            f"## Summary\n\nTest feature for {fr_num.upper()}.\n"
        )
        env = _clean_git_env()
        subprocess.run(
            ["git", "add", str(fr_path)],
            cwd=repo,
            check=True,
            capture_output=True,
            env=env,
        )
        subprocess.run(
            ["git", "commit", "-m", f"add {filename}"],
            cwd=repo,
            check=True,
            capture_output=True,
            env=env,
        )
        return f"feature-requests/{filename}"

    @staticmethod
    def _run_finalize(repo, fr_rel_path):
        """Run finalize_merge.sh in the test repo."""
        script_abs = os.path.abspath(_FINALIZE_SCRIPT)
        result = subprocess.run(
            ["bash", script_abs, fr_rel_path],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=30,
            env=_clean_git_env(GIT_TERMINAL_PROMPT="0"),
        )
        assert result.returncode == 0, (
            f"finalize_merge.sh failed (rc={result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        return result.stdout
