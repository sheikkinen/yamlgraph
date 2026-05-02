"""FR-305: Watcher Pipeline FSM Simplification.

Tests for the v2 pipeline config:
- 6 operational states + 2 terminals
- Transition correctness (happy path, revise loop, failure paths, timeouts)
- Judge uses different model from plan (no session resume)
- Enforce session uses resume from plan session
- Action types correct for each state
- Context propagation (session_id from plan → enforce)
"""

from pathlib import Path

import pytest
import yaml

WORKTREE = Path(__file__).resolve().parents[2]
CHAPLAIN = WORKTREE / ".chaplain"
V2_PIPELINE_PATH = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml"

# Graph paths
PLAN_UNIFIED_PATH = CHAPLAIN / "graphs" / "watcher-plan" / "step-plan-unified.yaml"
JUDGE_V2_PATH = CHAPLAIN / "graphs" / "watcher-plan" / "step-judge-v2.yaml"
ENFORCE_SESSION_PATH = CHAPLAIN / "graphs" / "watcher-enforce" / "enforce-session.yaml"
ENFORCE_PROMPT_PATH = (
    CHAPLAIN / "graphs" / "watcher-enforce" / "prompts" / "enforce-session.yaml"
)


# ── Helpers ──────────────────────────────────────────────────────────────


def load_config(path: Path) -> dict:
    """Load and return YAML config."""
    assert path.exists(), f"Config not found: {path}"
    with open(path) as f:
        return yaml.safe_load(f)


def get_states(config: dict) -> list[str]:
    """Extract state names from config."""
    return config.get("states", [])


def get_transitions(config: dict) -> list[dict]:
    """Extract transitions from config."""
    return config.get("transitions", [])


def transition_exists(
    transitions: list[dict], from_state: str, to_state: str, event: str
) -> bool:
    """Check if a specific transition exists."""
    return any(
        t.get("from") == from_state
        and t.get("to") == to_state
        and t.get("event") == event
        for t in transitions
    )


def get_action_config(config: dict, state: str) -> list[dict]:
    """Get action list for a state."""
    actions = config.get("actions", {})
    action = actions.get(state, [])
    if isinstance(action, dict):
        return [action]
    return action


# ═══════════════════════════════════════════════════════════════════════════
# AC-01: v2 pipeline config validates and has correct structure
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-316")
class TestV2PipelineStructure:
    """AC-01: watcher-pipeline-v2.yaml has 6 operational + 2 terminal states."""

    def test_v2_config_exists(self):
        assert V2_PIPELINE_PATH.exists()

    def test_has_nine_states_total(self):
        config = load_config(V2_PIPELINE_PATH)
        states = get_states(config)
        assert len(states) == 9, f"Expected 9 states, got {len(states)}: {states}"

    def test_operational_states(self):
        config = load_config(V2_PIPELINE_PATH)
        states = set(get_states(config))
        expected_operational = {
            "setup",
            "plan",
            "commit_plan",
            "judge",
            "enforce_session",
            "done",
        }
        assert expected_operational.issubset(
            states
        ), f"Missing operational states: {expected_operational - states}"

    def test_terminal_states(self):
        config = load_config(V2_PIPELINE_PATH)
        states = set(get_states(config))
        expected_terminal = {"completed", "failed", "stopped"}
        assert expected_terminal.issubset(
            states
        ), f"Missing terminal states: {expected_terminal - states}"

    def test_initial_state_is_setup(self):
        config = load_config(V2_PIPELINE_PATH)
        assert config["initial_state"] == "setup"

    def test_metadata_version(self):
        config = load_config(V2_PIPELINE_PATH)
        assert config["metadata"]["version"] == "1.0.0"
        assert config["metadata"]["machine_name"] == "watcher2_pipeline_v2"


# ═══════════════════════════════════════════════════════════════════════════
# AC-02: Happy path transitions
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-316")
class TestV2HappyPath:
    """AC-02: Happy path transitions from setup to done."""

    def test_setup_to_plan(self):
        config = load_config(V2_PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "setup", "plan", "setup_done")

    def test_plan_to_commit_plan(self):
        config = load_config(V2_PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "plan", "commit_plan", "plan_done")

    def test_commit_plan_to_judge(self):
        config = load_config(V2_PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "commit_plan", "judge", "committed")

    def test_judge_to_enforce_session(self):
        config = load_config(V2_PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "judge", "enforce_session", "approve")

    def test_enforce_session_to_done(self):
        config = load_config(V2_PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "enforce_session", "done", "pass")

    def test_done_to_completed(self):
        config = load_config(V2_PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "done", "completed", "completed")


# ═══════════════════════════════════════════════════════════════════════════
# AC-03: Revise loop (judge → plan)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-316")
class TestV2ReviseLoop:
    """AC-04: revise loops back to plan."""

    def test_judge_revise_to_plan(self):
        config = load_config(V2_PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "judge", "plan", "revise")


# ═══════════════════════════════════════════════════════════════════════════
# AC-04: Failure paths
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-316")
class TestV2FailurePaths:
    """AC-05: All states can reach failed on error."""

    def test_setup_error_to_failed(self):
        config = load_config(V2_PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "setup", "failed", "error")

    def test_plan_error_to_failed(self):
        config = load_config(V2_PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "plan", "failed", "error")

    def test_judge_reject_to_failed(self):
        config = load_config(V2_PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "judge", "failed", "reject")

    def test_enforce_error_to_failed(self):
        config = load_config(V2_PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "enforce_session", "failed", "error")

    def test_done_error_to_failed(self):
        config = load_config(V2_PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "done", "failed", "error")


# ═══════════════════════════════════════════════════════════════════════════
# AC-05: Timeout transitions
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-316")
class TestV2Timeouts:
    """AC-06: Timeouts route to failed."""

    def test_plan_timeout(self):
        config = load_config(V2_PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "plan", "failed", "timeout(600)")

    def test_judge_timeout(self):
        config = load_config(V2_PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "judge", "failed", "timeout(600)")

    def test_enforce_timeout(self):
        config = load_config(V2_PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(
            transitions, "enforce_session", "failed", "timeout(900)"
        )


# ═══════════════════════════════════════════════════════════════════════════
# AC-06: Global stop
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-316")
class TestV2GlobalStop:
    """AC-07: Wildcard stop transitions to stopped."""

    def test_wildcard_stop(self):
        config = load_config(V2_PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "*", "stopped", "stop")


# ═══════════════════════════════════════════════════════════════════════════
# AC-07: Judge uses different model from plan (no session resume)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-316")
class TestV2JudgeModelIndependence:
    """AC-03: Judge uses fresh session, different model from plan."""

    def test_judge_graph_exists(self):
        assert JUDGE_V2_PATH.exists()

    def test_judge_does_not_resume_session(self):
        """Judge MUST NOT resume plan session — fresh eyes, no anchoring."""
        config = load_config(JUDGE_V2_PATH)
        judge_node = config["nodes"]["judge"]
        cli_flags = judge_node.get("cli_flags", {})
        assert (
            "resume" not in cli_flags
        ), "Judge must NOT resume plan session (model independence)"

    def test_judge_uses_different_model_from_plan(self):
        """Plan and judge must use different models for bias diversity."""
        plan_config = load_config(PLAN_UNIFIED_PATH)
        judge_config = load_config(JUDGE_V2_PATH)

        plan_model = plan_config["nodes"]["plan_unified"]["cli_flags"]["model"]
        judge_model = judge_config["nodes"]["judge"]["cli_flags"]["model"]

        assert (
            plan_model != judge_model
        ), f"Judge model ({judge_model}) must differ from plan model ({plan_model})"

    def test_judge_v2_referenced_in_pipeline(self):
        """Pipeline v2 judge action references step-judge-v2.yaml."""
        config = load_config(V2_PIPELINE_PATH)
        judge_actions = get_action_config(config, "judge")
        assert len(judge_actions) == 1
        assert "step-judge-v2" in judge_actions[0]["graph"]


# ═══════════════════════════════════════════════════════════════════════════
# AC-08: Enforce session resumes plan session
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-316")
class TestV2EnforceSession:
    """AC-05: Enforce resumes own session on re-entry."""

    def test_enforce_session_graph_exists(self):
        assert ENFORCE_SESSION_PATH.exists()

    def test_enforce_session_prompt_exists(self):
        assert ENFORCE_PROMPT_PATH.exists()

    def test_enforce_uses_resume(self):
        """Enforce resumes the plan session for full context continuity."""
        config = load_config(ENFORCE_SESSION_PATH)
        enforce_node = config["nodes"]["enforce"]
        cli_flags = enforce_node.get("cli_flags", {})
        assert "resume" in cli_flags
        assert "session_id" in cli_flags["resume"]

    def test_enforce_has_allow_all_tools(self):
        """Enforce needs full tool access for TDD loop."""
        config = load_config(ENFORCE_SESSION_PATH)
        enforce_node = config["nodes"]["enforce"]
        cli_flags = enforce_node.get("cli_flags", {})
        assert cli_flags.get("allow_all_tools") is True

    def test_enforce_action_passes_session_id(self):
        """Pipeline v2 enforce action passes session_id from context."""
        config = load_config(V2_PIPELINE_PATH)
        enforce_actions = get_action_config(config, "enforce_session")
        assert len(enforce_actions) == 1
        vars_config = enforce_actions[0].get("vars", {})
        assert "session_id" in vars_config
        assert "{session_id}" in vars_config["session_id"]


# ═══════════════════════════════════════════════════════════════════════════
# AC-09: Context propagation chain
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-316")
class TestV2ContextPropagation:
    """Context flows correctly through the pipeline."""

    def test_setup_captures_worktree_context(self):
        """setup_done event captures wt_dir, wt_branch, main_dir."""
        config = load_config(V2_PIPELINE_PATH)
        events = config.get("events", {})
        setup_done = events.get("setup_done", {})
        context_map = setup_done.get("context_map", {})
        assert "wt_dir" in context_map
        assert "wt_branch" in context_map
        assert "main_dir" in context_map

    def test_plan_done_captures_session_id(self):
        """plan_done event captures session_id for enforce continuation."""
        config = load_config(V2_PIPELINE_PATH)
        events = config.get("events", {})
        plan_done = events.get("plan_done", {})
        context_map = plan_done.get("context_map", {})
        assert "session_id" in context_map


# ═══════════════════════════════════════════════════════════════════════════
# AC-10: Plan unified graph structure
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-316")
class TestV2PlanUnified:
    """AC-02: Plan produces FR + research in one invocation."""

    def test_plan_unified_graph_exists(self):
        assert PLAN_UNIFIED_PATH.exists()

    def test_plan_unified_has_single_node(self):
        """Plan should be a single copilot node (unified session)."""
        config = load_config(PLAN_UNIFIED_PATH)
        nodes = config.get("nodes", {})
        assert len(nodes) == 1

    def test_plan_unified_is_copilot_type(self):
        config = load_config(PLAN_UNIFIED_PATH)
        node = list(config["nodes"].values())[0]
        assert node["type"] == "copilot"

    def test_plan_unified_does_not_resume(self):
        """Plan starts a fresh session."""
        config = load_config(PLAN_UNIFIED_PATH)
        node = list(config["nodes"].values())[0]
        cli_flags = node.get("cli_flags", {})
        assert "resume" not in cli_flags


# ═══════════════════════════════════════════════════════════════════════════
# AC-11: Action types are correct
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-316")
class TestV2ActionTypes:
    """Action types match the state design."""

    def test_setup_is_bash_context(self):
        config = load_config(V2_PIPELINE_PATH)
        actions = get_action_config(config, "setup")
        assert actions[0]["type"] == "bash_context"

    def test_plan_is_yamlgraph_async(self):
        config = load_config(V2_PIPELINE_PATH)
        actions = get_action_config(config, "plan")
        assert actions[0]["type"] == "yamlgraph_async"

    def test_commit_plan_is_git_commit(self):
        config = load_config(V2_PIPELINE_PATH)
        actions = get_action_config(config, "commit_plan")
        assert actions[0]["type"] == "git_commit"

    def test_judge_is_yamlgraph_async(self):
        config = load_config(V2_PIPELINE_PATH)
        actions = get_action_config(config, "judge")
        assert actions[0]["type"] == "yamlgraph_async"

    def test_enforce_session_is_yamlgraph_async(self):
        config = load_config(V2_PIPELINE_PATH)
        actions = get_action_config(config, "enforce_session")
        assert actions[0]["type"] == "yamlgraph_async"

    def test_done_is_bash(self):
        config = load_config(V2_PIPELINE_PATH)
        actions = get_action_config(config, "done")
        assert actions[0]["type"] == "bash"
