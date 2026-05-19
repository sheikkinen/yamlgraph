"""Acceptance tests for watcher2 validate_fix + validate_gate states.

These tests define RED contracts for inserting validate_fix/validate_gate states
into watcher-pipeline-v2 and tightening enforce/validate prompt boundaries.
"""

from pathlib import Path

import pytest
import yaml

WORKTREE = Path(__file__).resolve().parents[2]
CHAPLAIN = WORKTREE / ".chaplain"

PIPELINE_V2 = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml"
ENFORCE_PROMPT = (
    CHAPLAIN / "graphs" / "watcher-enforce" / "prompts" / "enforce-session.yaml"
)
VALIDATE_GRAPH = CHAPLAIN / "graphs" / "watcher-enforce" / "validate-session.yaml"
VALIDATE_PROMPT = (
    CHAPLAIN / "graphs" / "watcher-enforce" / "prompts" / "validate-session.yaml"
)


def _load_yaml(path: Path) -> dict:
    assert path.exists(), f"Missing YAML file: {path}"
    with path.open() as f:
        return yaml.safe_load(f)


def _load_text(path: Path) -> str:
    assert path.exists(), f"Missing file: {path}"
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
        assert (
            len(action) == 1
        ), f"Expected single action for state {state}, got: {len(action)}"
        return action[0]
    return action


@pytest.mark.req("REQ-YG-318")
class TestFR310PipelineStates:
    """AC-01..AC-06: FSM states, transitions, and gate action contract."""

    def test_ac01_adds_validate_fix_and_validate_gate_states(self):
        config = _load_yaml(PIPELINE_V2)
        states = set(config.get("states", []))
        assert (
            "validate_fix" in states
        ), "Expected new validate_fix state in watcher-pipeline-v2"
        assert (
            "validate_gate" in states
        ), "Expected new validate_gate state in watcher-pipeline-v2"

    def test_ac02_removes_direct_enforce_session_to_done_transition(self):
        config = _load_yaml(PIPELINE_V2)
        transitions = config.get("transitions", [])
        assert not _transition_exists(
            transitions, "enforce_session", "done", "pass"
        ), "enforce_session should not transition directly to done"

    def test_ac03_adds_micro_remediation_before_validate_fix_gate_happy_path(self):
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

    def test_ac04_validate_gate_failure_loops_back_to_validate_fix(self):
        config = _load_yaml(PIPELINE_V2)
        transitions = config.get("transitions", [])
        assert _transition_exists(
            transitions, "validate_gate", "validate_fix", "fix_needed"
        )

    def test_ac05_validate_gate_attempt_cap_routes_to_failed(self):
        config = _load_yaml(PIPELINE_V2)
        transitions = config.get("transitions", [])
        assert _transition_exists(transitions, "validate_gate", "failed", "error")

    def test_ac06_validate_gate_uses_deterministic_action_with_retry(self):
        config = _load_yaml(PIPELINE_V2)
        action = _action_for(config, "validate_gate")
        assert (
            action["type"] == "validate_gate"
        ), "validate_gate must use validate_gate action type"
        assert action.get("max_attempts", 0) > 0, "must configure max_attempts"
        assert "retry" in action, "must configure retry event for fix_needed routing"
        assert "success" in action, "must configure success event"
        assert "error" in action, "must configure error event for attempt exhaustion"


@pytest.mark.req("REQ-YG-318")
class TestFR310ValidateArtifacts:
    """AC-07..AC-08: validate graph and prompt contracts."""

    def test_ac07_validate_graph_and_prompt_files_exist(self):
        assert VALIDATE_GRAPH.exists(), f"Missing validate graph: {VALIDATE_GRAPH}"
        assert VALIDATE_PROMPT.exists(), f"Missing validate prompt: {VALIDATE_PROMPT}"

    def test_ac08_validate_prompt_runs_mechanical_quality_commands(self):
        content = _load_text(VALIDATE_PROMPT)
        assert "ruff check --fix" in content
        assert "ruff format" in content
        assert "pytest tests/unit/ -q --no-cov -x" in content


@pytest.mark.req("REQ-YG-318")
class TestFR310EnforcePromptBoundary:
    """AC-09: enforce prompt no longer owns pre-commit/pytest gate execution."""

    def test_ac09_enforce_prompt_removes_precommit_gate_instructions(self):
        content = _load_text(ENFORCE_PROMPT).lower()
        assert (
            "pre-commit run --all-files" not in content
        ), "enforce prompt must not run pre-commit gate directly"
        assert (
            "pytest tests/ --no-cov -x" not in content
        ), "enforce prompt must not claim ownership of full pytest gate"
        assert (
            "validate" in content
        ), "enforce prompt should point validation ownership to validate state"
