"""Unit tests for inquisitor.sh worktree gate (FR-142).

Tests the worktree-detection gate that suppresses audit and propose phases
when running inside a git worktree (i.e., during an enforce pipeline).
The gate fires before the commit-delta gate (FR-131) and is bypassed by --force.

Detection method: in a worktree, the repo root's .git is a *file* (gitdir pointer),
not a *directory*. The gate checks `-f "$REPO_ROOT/.git"`.
"""

import os
import subprocess
import textwrap

# Strip git env vars that pre-commit injects (GIT_INDEX_FILE from stashing).
import pytest

pytestmark = pytest.mark.process

_GIT_ENV_POISON = {"GIT_INDEX_FILE", "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"}


def _clean_git_env(**extra: str) -> dict[str, str]:
    """Return os.environ minus git vars that pollute temp-repo subprocess calls."""
    env = {k: v for k, v in os.environ.items() if k not in _GIT_ENV_POISON}
    env.update(extra)
    return env


# ---------------------------------------------------------------------------
# Shell snippet — mirrors the worktree gate logic for isolated testing
# ---------------------------------------------------------------------------

_WORKTREE_GATE_SCRIPT = textwrap.dedent("""\
    #!/usr/bin/env bash
    set -euo pipefail
    cd "$TEST_DIR"

    # Parse flags
    FORCE=""
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --force) FORCE="true"; shift ;;
            *) shift ;;
        esac
    done

    # --- Worktree gate (FR-142) ---
    REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
    if [[ -n "$REPO_ROOT" && -f "$REPO_ROOT/.git" && -z "$FORCE" ]]; then
        echo "WORKTREE_GATE_BLOCKED"
        exit 0
    fi

    echo "WORKTREE_GATE_PASSED"
""")


def _run_gate(test_dir: str, *args: str) -> subprocess.CompletedProcess:
    """Run the worktree gate script in the given directory."""
    return subprocess.run(
        ["bash", "-c", _WORKTREE_GATE_SCRIPT, "--", *args],
        capture_output=True,
        text=True,
        env=_clean_git_env(TEST_DIR=str(test_dir)),
        timeout=10,
    )


def _init_repo(path) -> None:
    """Initialise a minimal git repo with one commit."""
    env = _clean_git_env()
    subprocess.run(
        ["git", "init"], cwd=str(path), env=env, capture_output=True, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test"],
        cwd=str(path),
        env=env,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=str(path),
        env=env,
        capture_output=True,
        check=True,
    )
    (path / "README.md").write_text("init", encoding="utf-8")
    subprocess.run(
        ["git", "add", "."], cwd=str(path), env=env, capture_output=True, check=True
    )
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=str(path),
        env=env,
        capture_output=True,
        check=True,
    )


@pytest.mark.slow
@pytest.mark.req("REQ-YG-142")
class TestWorktreeGateDetection:
    """Tests that the gate detects worktree vs main context."""

    def test_gate_passes_in_normal_repo(self, tmp_path):
        """Normal repo (.git is a directory) → gate passes."""
        _init_repo(tmp_path)
        result = _run_gate(tmp_path)
        assert result.returncode == 0
        assert "WORKTREE_GATE_PASSED" in result.stdout

    def test_gate_blocks_in_worktree(self, tmp_path):
        """Worktree (.git is a file) → gate blocks."""
        _init_repo(tmp_path)
        env = _clean_git_env()
        wt_path = tmp_path / "worktree"
        subprocess.run(
            ["git", "worktree", "add", str(wt_path), "-b", "test-wt"],
            cwd=str(tmp_path),
            env=env,
            capture_output=True,
            check=True,
        )
        # Verify .git is a file in worktree
        assert (wt_path / ".git").is_file(), ".git should be a file in worktree"

        result = _run_gate(wt_path)
        assert result.returncode == 0
        assert "WORKTREE_GATE_BLOCKED" in result.stdout

    def test_gate_passes_when_git_not_available(self, tmp_path):
        """Non-git directory → gate degrades gracefully (passes)."""
        # tmp_path is not a git repo; git rev-parse will fail
        result = subprocess.run(
            [
                "bash",
                "-c",
                textwrap.dedent("""\
                #!/usr/bin/env bash
                set -euo pipefail
                cd "$TEST_DIR"
                FORCE=""
                REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
                if [[ -n "$REPO_ROOT" && -f "$REPO_ROOT/.git" && -z "$FORCE" ]]; then
                    echo "WORKTREE_GATE_BLOCKED"
                    exit 0
                fi
                echo "WORKTREE_GATE_PASSED"
            """),
            ],
            capture_output=True,
            text=True,
            env=_clean_git_env(TEST_DIR=str(tmp_path)),
            timeout=10,
        )
        assert result.returncode == 0
        assert "WORKTREE_GATE_PASSED" in result.stdout


@pytest.mark.slow
@pytest.mark.req("REQ-YG-142")
class TestWorktreeGateForceBypass:
    """Tests that --force bypasses the worktree gate."""

    def test_force_bypasses_gate_in_worktree(self, tmp_path):
        """--force in a worktree → gate passes."""
        _init_repo(tmp_path)
        env = _clean_git_env()
        wt_path = tmp_path / "worktree"
        subprocess.run(
            ["git", "worktree", "add", str(wt_path), "-b", "test-force-wt"],
            cwd=str(tmp_path),
            env=env,
            capture_output=True,
            check=True,
        )
        result = _run_gate(wt_path, "--force")
        assert result.returncode == 0
        assert "WORKTREE_GATE_PASSED" in result.stdout

    def test_force_still_passes_in_normal_repo(self, tmp_path):
        """--force in normal repo → gate passes (no-op)."""
        _init_repo(tmp_path)
        result = _run_gate(tmp_path, "--force")
        assert result.returncode == 0
        assert "WORKTREE_GATE_PASSED" in result.stdout


@pytest.mark.req("REQ-YG-142")
class TestWorktreeGateInFullScript:
    """Integration test: verify the actual inquisitor.sh contains the worktree gate."""

    def test_inquisitor_script_contains_worktree_gate(self):
        """The inquisitor.sh script must contain the FR-142 worktree gate."""
        script_path = os.path.join(
            os.path.dirname(__file__), "..", "..", ".chaplain", "inquisitor.sh"
        )
        assert os.path.exists(script_path), f"inquisitor.sh not found at {script_path}"
        with open(script_path, encoding="utf-8") as f:
            content = f.read()
        assert (
            "Worktree gate" in content
            or "worktree gate" in content
            or "FR-142" in content
        ), "inquisitor.sh must contain the FR-142 worktree gate"

    def test_worktree_gate_before_commit_delta_gate(self):
        """Worktree gate must appear before the commit-delta gate in inquisitor.sh."""
        script_path = os.path.join(
            os.path.dirname(__file__), "..", "..", ".chaplain", "inquisitor.sh"
        )
        with open(script_path, encoding="utf-8") as f:
            content = f.read()
        # Match the gate section markers, not header comments
        wt_pos = content.find("# --- Worktree gate (FR-142)")
        delta_pos = content.find("# --- Commit-delta gate (FR-131")
        assert wt_pos != -1, "FR-142 gate section not found in inquisitor.sh"
        assert delta_pos != -1, "FR-131 gate section not found in inquisitor.sh"
        assert (
            wt_pos < delta_pos
        ), "Worktree gate (FR-142) must appear before commit-delta gate (FR-131)"
