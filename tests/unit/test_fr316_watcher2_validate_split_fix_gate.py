"""Acceptance tests for FR-316 watcher2 validate split (fix + deterministic gate)."""

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.process

WORKTREE = Path(__file__).resolve().parents[2]
CHAPLAIN = WORKTREE / ".chaplain"
PIPELINE_V2 = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml"
VALIDATE_FIX_PROMPT = (
    CHAPLAIN / "graphs" / "watcher-enforce" / "prompts" / "validate-session.yaml"
)
VALIDATE_GATE_ACTION = CHAPLAIN / "actions" / "validate_gate_action.py"


def _load_yaml(path: Path) -> dict:
    assert path.exists(), f"Missing YAML file: {path}"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_text(path: Path) -> str:
    assert path.exists(), f"Missing text file: {path}"
    return path.read_text(encoding="utf-8")


def _transition_exists(
    transitions: list[dict], from_state: str, to_state: str, event: str
) -> bool:
    return any(
        t.get("from") == from_state
        and t.get("to") == to_state
        and t.get("event") == event
        for t in transitions
    )


def _action_for(config: dict, state: str) -> dict:
    action = config["actions"][state]
    if isinstance(action, list):
        assert len(action) == 1, f"Expected one action for {state}, got {len(action)}"
        return action[0]
    return action


@pytest.mark.req("REQ-YG-318")
class TestFR316ValidateSplitFixGate:
    """AC-01..AC-09 contracts for validate_fix + validate_gate split."""

    def test_ac01_adds_validate_fix_and_validate_gate_states(self):
        config = _load_yaml(PIPELINE_V2)
        states = set(config.get("states", []))
        assert "validate_fix" in states
        assert "validate_gate" in states

    def test_ac02_removes_legacy_validate_and_precommit_check_states(self):
        config = _load_yaml(PIPELINE_V2)
        states = set(config.get("states", []))
        assert "validate" not in states
        assert "precommit_check" not in states

    def test_ac03_routes_enforce_micro_validatefix_sanity_validategate_done(self):
        config = _load_yaml(PIPELINE_V2)
        transitions = config.get("transitions", [])
        assert _transition_exists(
            transitions, "enforce_session", "micro_changelog", "enforce_done"
        )
        assert _transition_exists(
            transitions, "micro_changelog", "micro_title", "changelog_done"
        )
        assert _transition_exists(
            transitions, "micro_title", "sanity_check", "title_done"
        )
        assert _transition_exists(
            transitions, "validate_fix", "sanity_check", "validate_done"
        )
        assert _transition_exists(transitions, "sanity_check", "validate_gate", "pass")
        assert _transition_exists(transitions, "sanity_check", "validate_gate", "warn")
        assert _transition_exists(transitions, "validate_gate", "done", "pass")

    def test_ac04_validate_gate_loops_fix_needed_and_errors_to_failed(self):
        config = _load_yaml(PIPELINE_V2)
        transitions = config.get("transitions", [])
        assert _transition_exists(
            transitions, "validate_gate", "validate_fix", "fix_needed"
        )
        assert _transition_exists(transitions, "validate_gate", "failed", "error")

    def test_ac05_sanity_warn_routes_to_validate_gate(self):
        config = _load_yaml(PIPELINE_V2)
        transitions = config.get("transitions", [])
        assert _transition_exists(transitions, "sanity_check", "validate_gate", "warn")

    def test_ac06_validate_gate_has_deterministic_retry_contract(self):
        config = _load_yaml(PIPELINE_V2)
        action = _action_for(config, "validate_gate")
        assert action["type"] == "validate_gate"
        assert action.get("max_attempts", 0) > 0
        assert action["success"] == "pass"
        assert action["retry"] == "fix_needed"
        assert action["error"] == "error"

    def test_ac07_validate_gate_checks_ci_parity_rules(self):
        content = _load_text(VALIDATE_GATE_ACTION)
        assert '["pre-commit", "run", "--all-files"]' in content
        assert '["git", "log", "-1", "--format=%s"]' in content
        assert '["git", "fetch", "origin", "main"]' in content
        assert (
            '["git", "merge-base", "--is-ancestor", "origin/main", "HEAD"]' in content
        )
        assert "docs/diary/" in content and "reflection" in content and "fr-" in content

    def test_ac08_validate_fix_prompt_covers_mechanical_repairs(self):
        content = _load_text(VALIDATE_FIX_PROMPT).lower()
        assert "repair artifact staging/amend" in content
        assert "repair commit title contract" in content
        assert "repair branch freshness" in content
        assert "git rebase origin/main" in content
        assert "ruff check --fix" in content
        assert "pytest tests/unit/ -q --no-cov -x" in content

    def test_ac09_done_pr_title_uses_primary_selector_policy(self):
        config = _load_yaml(PIPELINE_V2)
        action = _action_for(config, "done")
        command = action["command"]
        assert "select_primary_pr_title.sh" in command
        assert "PR_TITLE=$(git log -1 --format=%s)" not in command
