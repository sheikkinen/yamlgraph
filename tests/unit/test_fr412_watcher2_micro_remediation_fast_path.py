"""Acceptance tests for FR-412 watcher2 micro-remediation fast path."""

from pathlib import Path

import pytest
import yaml

WORKTREE = Path(__file__).resolve().parents[2]
CHAPLAIN = WORKTREE / ".chaplain"
PIPELINE_V2 = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml"
VALIDATE_GATE_ACTION = CHAPLAIN / "actions" / "validate_gate_action.py"


def _load_yaml(path: Path) -> dict:
    assert path.exists(), f"Missing YAML file: {path}"
    with path.open() as f:
        return yaml.safe_load(f)


def _load_text(path: Path) -> str:
    assert path.exists(), f"Missing text file: {path}"
    return path.read_text()


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
class TestFR412MicroRemediationFastPath:
    """AC-01..AC-08 contracts for pre-gate micro-remediation."""

    def test_ac01_adds_micro_changelog_and_micro_title_states(self):
        config = _load_yaml(PIPELINE_V2)
        states = set(config.get("states", []))
        assert "micro_changelog" in states
        assert "micro_title" in states

    def test_ac02_routes_happy_path_through_micro_steps_before_gate(self):
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
        assert _transition_exists(transitions, "sanity_check", "validate_gate", "pass")
        assert _transition_exists(transitions, "sanity_check", "validate_gate", "warn")

    def test_ac03_removes_direct_enforce_to_validate_fix_happy_path_edge(self):
        config = _load_yaml(PIPELINE_V2)
        transitions = config.get("transitions", [])
        assert not _transition_exists(
            transitions, "enforce_session", "validate_fix", "enforce_done"
        )

    def test_ac04_preserves_validate_gate_fix_needed_fallback_to_validate_fix(self):
        config = _load_yaml(PIPELINE_V2)
        transitions = config.get("transitions", [])
        assert _transition_exists(
            transitions, "validate_gate", "validate_fix", "fix_needed"
        )

    def test_ac05_micro_changelog_uses_changelog_gen_action_contract(self):
        config = _load_yaml(PIPELINE_V2)
        action = _action_for(config, "micro_changelog")
        assert action["type"] == "changelog_gen"
        assert action["success"] == "changelog_done"
        assert action["error"] == "error"
        assert int(action.get("timeout", 0)) > 0

    def test_ac06_micro_title_repairs_title_contract_deterministically(self):
        config = _load_yaml(PIPELINE_V2)
        action = _action_for(config, "micro_title")
        assert action["type"] in {"bash", "bash_context"}
        command = action["command"]
        assert "git log -1 --format=%s" in command
        assert "git commit --amend" in command
        assert "FR-" in command
        assert action["success"] == "title_done"
        assert action["error"] == "error"

    def test_ac07_micro_steps_have_independent_timeouts_and_fallback_routes(self):
        config = _load_yaml(PIPELINE_V2)
        transitions = config.get("transitions", [])
        changelog_action = _action_for(config, "micro_changelog")
        title_action = _action_for(config, "micro_title")
        assert int(changelog_action.get("timeout", 0)) > 0
        assert int(title_action.get("timeout", 0)) > 0
        assert _transition_exists(
            transitions, "micro_changelog", "validate_fix", "error"
        )
        assert _transition_exists(transitions, "micro_title", "validate_fix", "error")

    def test_ac08_validate_gate_contract_unchanged_after_micro_step_insertion(self):
        config = _load_yaml(PIPELINE_V2)
        action = _action_for(config, "validate_gate")
        assert action["type"] == "validate_gate"
        assert action.get("max_attempts", 0) > 0
        assert action["success"] == "pass"
        assert action["retry"] == "fix_needed"
        assert action["error"] == "error"
        content = _load_text(VALIDATE_GATE_ACTION)
        assert '["pre-commit", "run", "--all-files"]' in content
        assert '["git", "log", "-1", "--format=%s"]' in content
