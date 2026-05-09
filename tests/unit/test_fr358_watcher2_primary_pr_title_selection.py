"""Acceptance tests for FR-358 watcher2 primary PR title selection."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

WORKTREE = Path(__file__).resolve().parents[2]
CHAPLAIN = WORKTREE / ".chaplain"
PIPELINE_V2 = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml"
VALIDATE_GATE_ACTION = CHAPLAIN / "actions" / "validate_gate_action.py"
SELECT_PRIMARY_TITLE = CHAPLAIN / "lib" / "watcher" / "select_primary_pr_title.sh"
ARCHITECTURE = WORKTREE / "ARCHITECTURE.md"
CAP_140 = WORKTREE / "capabilities" / "CAP-140-watcher2-validate-split-fix-gate.yaml"


def _load_yaml(path: Path) -> dict:
    assert path.exists(), f"Missing YAML file: {path}"
    with path.open() as f:
        return yaml.safe_load(f)


def _load_text(path: Path) -> str:
    assert path.exists(), f"Missing text file: {path}"
    return path.read_text()


def _action_for(config: dict, state: str) -> dict:
    action = config["actions"][state]
    if isinstance(action, list):
        assert len(action) == 1, f"Expected one action for {state}, got {len(action)}"
        return action[0]
    return action


def _run_selector_with_history(
    oldest_first_subjects: list[str], fallback_latest: str = "docs: latest"
) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        git_mock = Path(tmpdir) / "git"
        history = "\n".join(oldest_first_subjects)
        git_mock.write_text(
            "#!/usr/bin/env bash\n"
            'if [[ "$1 $2 $3 $4" == "log --reverse --format=%s origin/main..HEAD" ]]; then\n'
            "cat <<'EOF'\n"
            f"{history}\n"
            "EOF\n"
            "exit 0\n"
            "fi\n"
            'if [[ "$1 $2 $3" == "log -1 --format=%s" ]]; then\n'
            f'echo "{fallback_latest}"\n'
            "exit 0\n"
            "fi\n"
            'echo "unexpected git invocation: $*" >&2\n'
            "exit 1\n"
        )
        git_mock.chmod(0o755)
        env = os.environ.copy()
        env["PATH"] = f"{tmpdir}:{env['PATH']}"
        return subprocess.run(
            ["bash", str(SELECT_PRIMARY_TITLE)],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )


@pytest.mark.req("REQ-YG-318")
class TestFR358Watcher2PrimaryPRTitleSelection:
    """AC-01..AC-06 contracts for branch primary PR title policy."""

    def test_ac01_done_no_longer_uses_latest_commit_subject_for_pr_title(self):
        config = _load_yaml(PIPELINE_V2)
        command = _action_for(config, "done")["command"]
        assert "PR_TITLE=$(git log -1 --format=%s)" not in command
        assert "select_primary_pr_title.sh" in command

    def test_ac02_prefers_first_feat_or_fix_subject_when_later_diary_commit_exists(
        self,
    ):
        result = _run_selector_with_history(
            [
                "feat(mcp): FR-358 primary title policy",
                "chore(format): normalize imports",
                "docs(diary): reflection for FR-358",
            ]
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "feat(mcp): FR-358 primary title policy"

    def test_ac03_fallback_selects_first_non_docs_non_chore_subject(self):
        result = _run_selector_with_history(
            [
                "docs: annotate context",
                "chore: format files",
                "refactor(watcher): simplify selector",
                "docs: add notes",
            ]
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "refactor(watcher): simplify selector"

    def test_ac04_docs_only_branch_falls_back_to_first_subject(self):
        result = _run_selector_with_history(
            [
                "docs: first branch note",
                "chore: tidy markdown",
                "docs: final reflection",
            ]
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "docs: first branch note"

    def test_ac05_validate_gate_uses_same_primary_title_policy_as_done(self):
        command = _action_for(_load_yaml(PIPELINE_V2), "done")["command"]
        action_content = _load_text(VALIDATE_GATE_ACTION)
        assert "select_primary_pr_title.sh" in command
        assert '["bash", PRIMARY_TITLE_SELECTOR]' in action_content
        assert 'diary_checked = primary_title_type in {"feat", "fix"}' in action_content

    def test_ac06_req_yg_318_and_cap140_contract_text_updated_for_primary_title_policy(
        self,
    ):
        architecture_req_lines = [
            line
            for line in _load_text(ARCHITECTURE).splitlines()
            if line.strip().startswith("| REQ-YG-318 |")
        ]
        assert architecture_req_lines
        for line in architecture_req_lines:
            assert "primary PR title selector" in line
            assert "`git log -1 --format=%s`" not in line

        cap_text = _load_text(CAP_140)
        assert "primary PR title selector" in cap_text
        assert "`git log -1 --format=%s`" not in cap_text
