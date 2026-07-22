"""RED acceptance tests for FR-316 watcher2 sanity_check state."""

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.process

WORKTREE = Path(__file__).resolve().parents[2]
CHAPLAIN = WORKTREE / ".chaplain"

PIPELINE_V2 = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml"
ENFORCE_PROMPT = (
    CHAPLAIN / "graphs" / "watcher-enforce" / "prompts" / "enforce-session.yaml"
)
SANITY_GRAPH = CHAPLAIN / "graphs" / "watcher-enforce" / "sanity-check-session.yaml"
SANITY_PROMPT = (
    CHAPLAIN / "graphs" / "watcher-enforce" / "prompts" / "sanity-check-session.yaml"
)


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
class TestFR316Watcher2SanityCheckState:
    """AC-01..AC-08 contracts for sanity-check insertion and ownership split."""

    def test_ac01_adds_sanity_check_state(self):
        config = _load_yaml(PIPELINE_V2)
        states = set(config.get("states", []))
        assert (
            "sanity_check" in states
        ), "Expected sanity_check state in watcher-pipeline-v2"

    def test_ac02_removes_direct_validate_to_precommit_transition(self):
        config = _load_yaml(PIPELINE_V2)
        transitions = config.get("transitions", [])
        assert not _transition_exists(
            transitions, "validate_fix", "validate_gate", "validate_done"
        ), "validate_fix should route to sanity_check first, not directly to validate_gate"

    def test_ac03_ac04_routes_validate_to_sanity_then_precommit_with_warn_non_blocking(
        self,
    ):
        config = _load_yaml(PIPELINE_V2)
        transitions = config.get("transitions", [])
        assert _transition_exists(
            transitions, "validate_fix", "sanity_check", "validate_done"
        )
        assert _transition_exists(transitions, "sanity_check", "validate_gate", "pass")
        assert _transition_exists(
            transitions, "sanity_check", "validate_gate", "warn"
        ), "warn should be non-blocking and continue to validate_gate"

    def test_ac05_sanity_check_state_uses_yamlgraph_async_action(self):
        config = _load_yaml(PIPELINE_V2)
        action = _action_for(config, "sanity_check")
        assert action["type"] == "yamlgraph_async"
        assert (
            action.get("graph")
            == ".chaplain/graphs/watcher-enforce/sanity-check-session.yaml"
        )

    def test_ac06_sanity_check_graph_and_prompt_exist(self):
        assert SANITY_GRAPH.exists(), f"Missing sanity graph file: {SANITY_GRAPH}"
        assert SANITY_PROMPT.exists(), f"Missing sanity prompt file: {SANITY_PROMPT}"

    def test_ac07_sanity_prompt_covers_review_dimensions_and_diary_seed(self):
        content = _load_text(SANITY_PROMPT).lower()
        assert "proportionality" in content
        assert "test quality" in content
        assert "fr" in content and "diff" in content
        assert "pipeline log" in content
        assert "docs/diary/" in content
        assert "seed:" in content
        assert "warn" in content

    def test_ac08_enforce_prompt_no_longer_owns_diary_generation(self):
        content = _load_text(ENFORCE_PROMPT).lower()
        assert (
            "create a metacognitive reflection" not in content
        ), "Diary ownership should move from enforce prompt to sanity_check prompt"
