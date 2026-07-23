"""Unit tests for inquisitor.sh commit-delta gate (FR-131).

Tests the commit-delta pre-flight gate that aborts the Inquisitor when
no feat: or fix: commits exist since the last audit. The gate logic is
pure shell, tested via subprocess with temporary git repositories
(same pattern as test_inquisitor_auto_propose.py).
"""

import os
import subprocess
import textwrap

import pytest

pytestmark = [pytest.mark.process, pytest.mark.slow]

# Strip git env vars that pre-commit injects (GIT_INDEX_FILE from stashing).
_GIT_ENV_POISON = {"GIT_INDEX_FILE", "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"}


def _clean_git_env(**extra: str) -> dict[str, str]:
    """Return os.environ minus git vars that pollute temp-repo subprocess calls."""
    env = {k: v for k, v in os.environ.items() if k not in _GIT_ENV_POISON}
    env.update(extra)
    return env


# ---------------------------------------------------------------------------
# Shell snippets — mirror the gate logic for isolated testing
# ---------------------------------------------------------------------------

# Extracts the HEAD SHA from the last audit's commit range in diary folder.
# Scans docs/diary/*inquisitor-audit* files sorted by name (most recent first).
_SHA_EXTRACT_SCRIPT = textwrap.dedent("""\
    #!/usr/bin/env bash
    set -euo pipefail
    DIARY_DIR="$1"
    LATEST_AUDIT=$(ls "$DIARY_DIR"/*inquisitor-audit* 2>/dev/null || true)
    LATEST_AUDIT=$(echo "$LATEST_AUDIT" | sort -r | head -1)
    if [[ -z "$LATEST_AUDIT" ]]; then
        echo "NO_SHA"
        exit 0
    fi
    LAST_SHA=$(sed -nE 's/.*`([a-f0-9]{7,})`\\.\\.`([a-f0-9]{7,})`.*/\\2/p' "$LATEST_AUDIT" | head -1)
    echo "${LAST_SHA:-NO_SHA}"
""")

# Gate decision logic isolated from git/diary — purely evaluates inputs.
_GATE_DECISION_SCRIPT = textwrap.dedent("""\
    #!/usr/bin/env bash
    set -euo pipefail

    if [[ -z "${LAST_SHA:-}" ]]; then
        echo "GATE_PASSED:no_sha"
        exit 0
    fi
    if [[ -n "${FORCE:-}" ]]; then
        echo "GATE_PASSED:forced"
        exit 0
    fi
    if [[ "${ACTIONABLE:-0}" -eq 0 ]]; then
        echo "⏭️  Inquisitor: No feat/fix commits since last audit (${LAST_SHA}..HEAD). Nothing to audit."
        echo "   Use --force to override."
        echo "GATE_BLOCKED"
        exit 0
    fi
    echo "GATE_PASSED:commits_found"
""")

# Flag parsing with --force and --propose via while/shift loop.
_FLAG_PARSE_SCRIPT = textwrap.dedent("""\
    #!/usr/bin/env bash
    set -euo pipefail

    FORCE=""
    PROPOSE=""
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --force) FORCE="true"; shift ;;
            --propose) PROPOSE="true"; shift ;;
            *) shift ;;
        esac
    done

    echo "FORCE=${FORCE:-false}"
    echo "PROPOSE=${PROPOSE:-false}"
""")

# Full gate integration — sets up in a git repo dir, parses diary folder, runs gate.
_FULL_GATE_SCRIPT = textwrap.dedent("""\
    #!/usr/bin/env bash
    set -euo pipefail
    cd "$TEST_DIR"

    # Parse flags
    FORCE=""
    PROPOSE=""
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --force) FORCE="true"; shift ;;
            --propose) PROPOSE="true"; shift ;;
            *) shift ;;
        esac
    done

    # --- Commit-delta gate (FR-131, FR-134) ---
    DIARY_DIR="docs/diary"
    LATEST_AUDIT=$(ls "$DIARY_DIR"/*inquisitor-audit* 2>/dev/null || true)
    LATEST_AUDIT=$(echo "$LATEST_AUDIT" | sort -r | head -1)
    if [[ -n "$LATEST_AUDIT" ]]; then
        LAST_SHA=$(sed -nE 's/.*`([a-f0-9]{7,})`\\.\\.`([a-f0-9]{7,})`.*/\\2/p' "$LATEST_AUDIT" | head -1)
    else
        LAST_SHA=""
    fi

    if [[ -n "$LAST_SHA" ]] && git rev-parse --verify "$LAST_SHA^{commit}" >/dev/null 2>&1; then
        ACTIONABLE=$(git log --oneline "$LAST_SHA"..HEAD | grep -cE '^[a-f0-9]+ (feat|fix)' || true)
        if [[ "$ACTIONABLE" -eq 0 && -z "$FORCE" ]]; then
            echo "⏭️  Inquisitor: No feat/fix commits since last audit ($LAST_SHA..HEAD). Nothing to audit."
            echo "   Use --force to override."
            echo "GATE_BLOCKED"
            exit 0
        fi
    fi

    echo "GATE_PASSED"
    if [[ -n "$PROPOSE" ]]; then
        echo "PROPOSE_MODE"
    fi
""")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_sha_extract(diary_dir: str) -> str:
    """Run SHA extraction script against a diary directory."""
    result = subprocess.run(
        ["bash", "-c", _SHA_EXTRACT_SCRIPT, "--", diary_dir],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    return result.stdout.strip()


def _run_gate_decision(
    last_sha: str = "",
    actionable: int = 0,
    force: str = "",
) -> str:
    """Run gate decision script with given inputs."""
    result = subprocess.run(
        ["bash", "-c", _GATE_DECISION_SCRIPT],
        env=_clean_git_env(
            LAST_SHA=last_sha,
            ACTIONABLE=str(actionable),
            FORCE=force,
        ),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    return result.stdout.strip()


def _run_flag_parse(args: list[str] | None = None) -> str:
    """Run flag parsing script and return stdout."""
    cmd = ["bash", "-c", _FLAG_PARSE_SCRIPT, "--"] + (args or [])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    return result.stdout.strip()


def _setup_git_repo(path, commits: list[str]) -> list[str]:
    """Initialize a git repo at *path* and create commits; return short SHAs."""
    env = _clean_git_env()
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True, env=env)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=path,
        capture_output=True,
        check=True,
        env=env,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=path,
        capture_output=True,
        check=True,
        env=env,
    )
    shas: list[str] = []
    for i, msg in enumerate(commits):
        (path / f"file_{i}.txt").write_text(f"commit {i}\n")
        subprocess.run(
            ["git", "add", "."], cwd=path, capture_output=True, check=True, env=env
        )
        subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=path,
            capture_output=True,
            check=True,
            env=env,
        )
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
        shas.append(result.stdout.strip())
    return shas


def _run_full_gate(test_dir: str, args: list[str] | None = None) -> str:
    """Run the full gate integration script in *test_dir*."""
    cmd = ["bash", "-c", _FULL_GATE_SCRIPT, "--"] + (args or [])
    result = subprocess.run(
        cmd,
        env=_clean_git_env(TEST_DIR=str(test_dir)),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    return result.stdout.strip()


def _read_inquisitor_sh() -> str:
    """Read the current inquisitor.sh content."""
    inquisitor_path = os.path.join(
        os.path.dirname(__file__), "..", "..", ".chaplain", "inquisitor.sh"
    )
    with open(inquisitor_path) as f:
        return f.read()


# ---------------------------------------------------------------------------
# Tests — SHA Extraction
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-131")
class TestSHAExtraction:
    """Tests for extracting last audit SHA from diary folder."""

    def test_extracts_sha_from_latest_audit_file(self, tmp_path):
        """Latest inquisitor-audit file (by name sort) yields the end-of-range SHA."""
        diary_dir = tmp_path / "diary"
        diary_dir.mkdir()
        (diary_dir / "2026-03-07-inquisitor-audit-xxiii.md").write_text(
            "**Context:** Audit covering commits `f3c6b73`..`5c33f8c` (5 commits)\n"
        )
        assert _run_sha_extract(str(diary_dir)) == "5c33f8c"

    def test_extracts_sha_from_longer_sha(self, tmp_path):
        """Longer abbreviated SHAs (8+ chars) are extracted correctly."""
        diary_dir = tmp_path / "diary"
        diary_dir.mkdir()
        (diary_dir / "2026-03-07-inquisitor-audit-xxii.md").write_text(
            "**Context:** commits `a27f3968`..`b171deed` (3 commits)\n"
        )
        assert _run_sha_extract(str(diary_dir)) == "b171deed"

    def test_returns_most_recent_audit_by_filename(self, tmp_path):
        """Most recent audit file (by filename sort -r) wins."""
        diary_dir = tmp_path / "diary"
        diary_dir.mkdir()
        (diary_dir / "2026-03-06-inquisitor-audit-xxi.md").write_text(
            "**Context:** commits `ccc3333`..`ddd4444` (older)\n"
        )
        (diary_dir / "2026-03-07-inquisitor-audit-xxii.md").write_text(
            "**Context:** commits `aaa1111`..`bbb2222` (latest)\n"
        )
        assert _run_sha_extract(str(diary_dir)) == "bbb2222"

    def test_returns_no_sha_for_empty_directory(self, tmp_path):
        """Empty diary directory yields NO_SHA."""
        diary_dir = tmp_path / "diary"
        diary_dir.mkdir()
        assert _run_sha_extract(str(diary_dir)) == "NO_SHA"

    def test_returns_no_sha_when_no_audit_files(self, tmp_path):
        """Diary directory with no inquisitor-audit files yields NO_SHA."""
        diary_dir = tmp_path / "diary"
        diary_dir.mkdir()
        (diary_dir / "2026-03-07-reflection-fr-125.md").write_text("No audit here.\n")
        assert _run_sha_extract(str(diary_dir)) == "NO_SHA"

    def test_returns_no_sha_for_no_commit_range(self, tmp_path):
        """Audit file without commit range pattern yields NO_SHA."""
        diary_dir = tmp_path / "diary"
        diary_dir.mkdir()
        (diary_dir / "2026-03-07-inquisitor-audit-xx.md").write_text(
            "Some text without any commit ranges.\n"
        )
        assert _run_sha_extract(str(diary_dir)) == "NO_SHA"


# ---------------------------------------------------------------------------
# Tests — Gate Decision
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-131")
class TestGateDecision:
    """Tests for the gate decision logic (AC-1, AC-2, AC-3)."""

    def test_blocks_when_no_actionable_commits(self):
        """Gate blocks when zero feat/fix commits since last audit."""
        output = _run_gate_decision(last_sha="abc1234", actionable=0)
        assert "GATE_BLOCKED" in output

    def test_passes_when_actionable_commits_exist(self):
        """Gate passes when feat/fix commits exist since last audit."""
        output = _run_gate_decision(last_sha="abc1234", actionable=3)
        assert "GATE_PASSED:commits_found" in output

    def test_passes_when_no_sha_found(self):
        """Gate passes (degrades) when no SHA extracted from diary."""
        output = _run_gate_decision(last_sha="", actionable=0)
        assert "GATE_PASSED:no_sha" in output

    def test_force_bypasses_gate(self):
        """--force bypasses gate unconditionally (AC-3)."""
        output = _run_gate_decision(last_sha="abc1234", actionable=0, force="true")
        assert "GATE_PASSED:forced" in output

    def test_blocked_message_mentions_override(self):
        """Exit message tells user how to override (AC-2)."""
        output = _run_gate_decision(last_sha="abc1234", actionable=0)
        assert "--force" in output

    def test_blocked_message_mentions_reason(self):
        """Exit message states the reason for blocking (AC-2)."""
        output = _run_gate_decision(last_sha="abc1234", actionable=0)
        assert "No feat/fix commits" in output


# ---------------------------------------------------------------------------
# Tests — Flag Parsing
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-131")
class TestFlagParsing:
    """Tests for --force / --propose flag parsing via while/shift."""

    def test_no_flags(self):
        """No flags → audit-only, no force."""
        output = _run_flag_parse()
        assert "FORCE=false" in output
        assert "PROPOSE=false" in output

    def test_force_only(self):
        """--force alone sets FORCE=true."""
        output = _run_flag_parse(["--force"])
        assert "FORCE=true" in output
        assert "PROPOSE=false" in output

    def test_propose_only(self):
        """--propose alone sets PROPOSE=true."""
        output = _run_flag_parse(["--propose"])
        assert "FORCE=false" in output
        assert "PROPOSE=true" in output

    def test_force_and_propose(self):
        """--force --propose sets both flags."""
        output = _run_flag_parse(["--force", "--propose"])
        assert "FORCE=true" in output
        assert "PROPOSE=true" in output

    def test_propose_and_force_reversed(self):
        """--propose --force (reversed order) sets both flags."""
        output = _run_flag_parse(["--propose", "--force"])
        assert "FORCE=true" in output
        assert "PROPOSE=true" in output

    def test_unknown_flags_ignored(self):
        """Unknown flags are silently ignored."""
        output = _run_flag_parse(["--unknown", "--force"])
        assert "FORCE=true" in output
        assert "PROPOSE=false" in output


# ---------------------------------------------------------------------------
# Tests — Full Gate Integration (git repo)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-131")
class TestFullGateIntegration:
    """Integration tests with real git repos testing end-to-end gate."""

    def test_gate_blocks_without_feat_fix_commits(self, tmp_path):
        """Gate blocks when only docs/chore commits since last audit (AC-1)."""
        shas = _setup_git_repo(
            tmp_path,
            [
                "feat: initial feature",
                "docs: update readme",
                "chore: cleanup",
            ],
        )
        diary_dir = tmp_path / "docs" / "diary"
        diary_dir.mkdir(parents=True)
        (diary_dir / "2026-03-07-inquisitor-audit-xxiii.md").write_text(
            f"**Context:** commits `{shas[0]}`..`{shas[0]}` (1 commit)\n"
        )
        output = _run_full_gate(str(tmp_path))
        assert "GATE_BLOCKED" in output

    def test_gate_passes_with_feat_commit(self, tmp_path):
        """Gate passes when a feat: commit exists since last audit."""
        shas = _setup_git_repo(
            tmp_path,
            [
                "chore: initial",
                "docs: update readme",
                "feat: new feature",
            ],
        )
        diary_dir = tmp_path / "docs" / "diary"
        diary_dir.mkdir(parents=True)
        (diary_dir / "2026-03-07-inquisitor-audit-xxiii.md").write_text(
            f"**Context:** commits `{shas[0]}`..`{shas[0]}` (1 commit)\n"
        )
        output = _run_full_gate(str(tmp_path))
        assert "GATE_PASSED" in output

    def test_gate_passes_with_fix_commit(self, tmp_path):
        """Gate passes when a fix: commit exists since last audit."""
        shas = _setup_git_repo(
            tmp_path,
            [
                "chore: initial",
                "docs: update readme",
                "fix: bug fix",
            ],
        )
        diary_dir = tmp_path / "docs" / "diary"
        diary_dir.mkdir(parents=True)
        (diary_dir / "2026-03-07-inquisitor-audit-xxiii.md").write_text(
            f"**Context:** commits `{shas[0]}`..`{shas[0]}` (1 commit)\n"
        )
        output = _run_full_gate(str(tmp_path))
        assert "GATE_PASSED" in output

    def test_gate_passes_when_no_diary_dir(self, tmp_path):
        """Gate degrades gracefully when diary/ directory doesn't exist (AC-6)."""
        _setup_git_repo(tmp_path, ["chore: initial"])
        output = _run_full_gate(str(tmp_path))
        assert "GATE_PASSED" in output

    def test_gate_passes_when_diary_has_no_audit_files(self, tmp_path):
        """Gate degrades when diary dir exists but has no audit entries (AC-6)."""
        _setup_git_repo(tmp_path, ["chore: initial"])
        diary_dir = tmp_path / "docs" / "diary"
        diary_dir.mkdir(parents=True)
        (diary_dir / "2026-03-07-reflection-fr-125.md").write_text(
            "# Not an audit file\n"
        )
        output = _run_full_gate(str(tmp_path))
        assert "GATE_PASSED" in output

    def test_gate_passes_when_sha_unresolvable(self, tmp_path):
        """Gate degrades when diary SHA doesn't exist in repo (AC-6)."""
        _setup_git_repo(tmp_path, ["chore: initial"])
        diary_dir = tmp_path / "docs" / "diary"
        diary_dir.mkdir(parents=True)
        (diary_dir / "2026-03-07-inquisitor-audit-xxiii.md").write_text(
            "**Context:** commits `0000000`..`fffffff` (1 commit)\n"
        )
        output = _run_full_gate(str(tmp_path))
        assert "GATE_PASSED" in output

    def test_force_bypasses_gate(self, tmp_path):
        """--force bypasses gate even with no feat/fix commits (AC-3)."""
        shas = _setup_git_repo(
            tmp_path,
            [
                "feat: initial",
                "docs: only docs",
            ],
        )
        diary_dir = tmp_path / "docs" / "diary"
        diary_dir.mkdir(parents=True)
        (diary_dir / "2026-03-07-inquisitor-audit-xxiii.md").write_text(
            f"**Context:** commits `{shas[0]}`..`{shas[0]}` (1 commit)\n"
        )
        output = _run_full_gate(str(tmp_path), ["--force"])
        assert "GATE_PASSED" in output

    def test_propose_respects_gate(self, tmp_path):
        """--propose without --force still blocks on gate (AC-4)."""
        shas = _setup_git_repo(
            tmp_path,
            [
                "feat: initial",
                "docs: only docs",
            ],
        )
        diary_dir = tmp_path / "docs" / "diary"
        diary_dir.mkdir(parents=True)
        (diary_dir / "2026-03-07-inquisitor-audit-xxiii.md").write_text(
            f"**Context:** commits `{shas[0]}`..`{shas[0]}` (1 commit)\n"
        )
        output = _run_full_gate(str(tmp_path), ["--propose"])
        assert "GATE_BLOCKED" in output
        assert "PROPOSE_MODE" not in output

    def test_force_propose_bypasses_gate_and_proposes(self, tmp_path):
        """--force --propose bypasses gate and enables propose mode (AC-5)."""
        shas = _setup_git_repo(
            tmp_path,
            [
                "feat: initial",
                "docs: only docs",
            ],
        )
        diary_dir = tmp_path / "docs" / "diary"
        diary_dir.mkdir(parents=True)
        (diary_dir / "2026-03-07-inquisitor-audit-xxiii.md").write_text(
            f"**Context:** commits `{shas[0]}`..`{shas[0]}` (1 commit)\n"
        )
        output = _run_full_gate(str(tmp_path), ["--force", "--propose"])
        assert "GATE_PASSED" in output
        assert "PROPOSE_MODE" in output

    def test_gate_passes_with_scoped_feat_commit(self, tmp_path):
        """Gate recognises scoped feat(scope): commits."""
        shas = _setup_git_repo(
            tmp_path,
            [
                "chore: initial",
                "feat(streaming): add subgraph support",
            ],
        )
        diary_dir = tmp_path / "docs" / "diary"
        diary_dir.mkdir(parents=True)
        (diary_dir / "2026-03-07-inquisitor-audit-xxiii.md").write_text(
            f"**Context:** commits `{shas[0]}`..`{shas[0]}` (1 commit)\n"
        )
        output = _run_full_gate(str(tmp_path))
        assert "GATE_PASSED" in output


# ---------------------------------------------------------------------------
# Tests — inquisitor.sh Content Integration
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-131")
class TestInquisitorShellIntegration:
    """Integration tests verifying inquisitor.sh contains the gate logic."""

    def test_has_force_flag(self):
        """inquisitor.sh supports --force flag."""
        content = _read_inquisitor_sh()
        assert "--force" in content

    def test_has_force_variable(self):
        """inquisitor.sh declares FORCE variable."""
        content = _read_inquisitor_sh()
        assert "FORCE=" in content

    def test_has_commit_delta_gate_comment(self):
        """inquisitor.sh contains commit-delta gate section."""
        content = _read_inquisitor_sh()
        assert "Commit-delta gate" in content

    def test_extracts_sha_from_diary_folder(self):
        """Gate logic scans diary folder for inquisitor-audit files."""
        content = _read_inquisitor_sh()
        assert "LAST_SHA" in content
        assert "inquisitor-audit" in content

    def test_uses_filename_sorted_lookup(self):
        """Gate logic uses sort -r for filename-based ordering."""
        content = _read_inquisitor_sh()
        assert "sort -r" in content

    def test_counts_actionable_commits(self):
        """Gate logic counts feat/fix commits via git log."""
        content = _read_inquisitor_sh()
        assert "ACTIONABLE" in content
        assert "git log" in content

    def test_exit_message_mentions_force(self):
        """Gate exit message tells user about --force override."""
        content = _read_inquisitor_sh()
        assert "--force" in content

    def test_header_documents_gate(self):
        """Script header references FR-131."""
        content = _read_inquisitor_sh()
        header = "\n".join(content.split("\n")[:10])
        assert "FR-131" in header

    def test_header_documents_force_flag(self):
        """Script usage line includes --force."""
        content = _read_inquisitor_sh()
        header = "\n".join(content.split("\n")[:10])
        assert "--force" in header

    def test_gate_is_pure_shell(self):
        """Gate section (LAST_SHA to copilot call) has no copilot/python."""
        content = _read_inquisitor_sh()
        gate_start = content.find("LAST_SHA=")
        gate_end = content.find("copilot", gate_start)
        assert gate_start != -1, "LAST_SHA assignment not found"
        assert gate_end != -1, "copilot call not found after gate"
        gate_section = content[gate_start:gate_end]
        assert "python" not in gate_section.lower()
        assert "copilot" not in gate_section

    def test_existing_audit_block_preserved(self):
        """Original audit copilot call is unchanged."""
        content = _read_inquisitor_sh()
        assert "**Inquisit.**" in content
        assert "You are the Inquisitor. Your duty: audit" in content

    def test_existing_propose_block_preserved(self):
        """Propose copilot call is unchanged."""
        content = _read_inquisitor_sh()
        assert "**Propose.**" in content
        assert 'if [[ -n "$PROPOSE" ]]' in content
