"""FR-305: Watcher Pipeline FSM Simplification.

Tests for the v2 pipeline config:
- 9 operational states + 3 terminals
- Transition correctness (happy path, revise loop, failure paths, timeouts)
- Judge uses different model from plan (no session resume)
- FR-309: Judge event_map aligned to prompt vocabulary
- FR-309: Enforce session runs fresh (no resume)
- Action types correct for each state
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
    """AC-01: watcher-pipeline-v2.yaml has expected operational/terminal states."""

    def test_v2_config_exists(self):
        assert V2_PIPELINE_PATH.exists()

    def test_has_twelve_states_total(self):
        config = load_config(V2_PIPELINE_PATH)
        states = get_states(config)
        assert len(states) == 12, f"Expected 12 states, got {len(states)}: {states}"

    def test_operational_states(self):
        config = load_config(V2_PIPELINE_PATH)
        states = set(get_states(config))
        expected_operational = {
            "setup",
            "plan",
            "capture_fr",
            "judge",
            "enforce_session",
            "validate_fix",
            "sanity_check",
            "validate_gate",
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
        assert config["metadata"]["machine_name"] == "watcher-pipeline-v2"


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

    def test_plan_to_capture_fr(self):
        config = load_config(V2_PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "plan", "capture_fr", "plan_done")

    def test_capture_fr_to_judge(self):
        config = load_config(V2_PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "capture_fr", "judge", "fr_captured")

    def test_judge_to_enforce_session(self):
        config = load_config(V2_PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "judge", "enforce_session", "approve")

    def test_enforce_session_to_validate_fix(self):
        config = load_config(V2_PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(
            transitions, "enforce_session", "validate_fix", "enforce_done"
        )

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

    def test_judge_error_to_failed(self):
        """FR-309: judge error (no event_map match) must route to failed."""
        config = load_config(V2_PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "judge", "failed", "error")

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
            transitions, "enforce_session", "failed", "timeout(3600)"
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
# AC-08: Enforce session — fresh session (FR-309)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-316")
class TestV2EnforceSession:
    """FR-309 AC-09: Enforce runs fresh session (no resume)."""

    def test_enforce_session_graph_exists(self):
        assert ENFORCE_SESSION_PATH.exists()

    def test_enforce_session_prompt_exists(self):
        assert ENFORCE_PROMPT_PATH.exists()

    def test_enforce_does_not_use_resume(self):
        """FR-309 AC-09: Enforce runs fresh — no resume in cli_flags."""
        config = load_config(ENFORCE_SESSION_PATH)
        enforce_node = config["nodes"]["enforce"]
        cli_flags = enforce_node.get("cli_flags", {})
        assert "resume" not in cli_flags, "Enforce must not use resume (FR-309)"

    def test_enforce_has_allow_all_tools(self):
        """Enforce needs full tool access for TDD loop."""
        config = load_config(ENFORCE_SESSION_PATH)
        enforce_node = config["nodes"]["enforce"]
        cli_flags = enforce_node.get("cli_flags", {})
        assert cli_flags.get("allow_all_tools") is True

    def test_enforce_action_does_not_pass_session_id(self):
        """FR-309 AC-04: Pipeline enforce vars have no session_id."""
        config = load_config(V2_PIPELINE_PATH)
        enforce_actions = get_action_config(config, "enforce_session")
        assert len(enforce_actions) == 1
        vars_config = enforce_actions[0].get("vars", {})
        assert "session_id" not in vars_config


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

    def test_plan_done_has_no_session_id(self):
        """FR-309 AC-04: plan_done has no session_id context_map."""
        config = load_config(V2_PIPELINE_PATH)
        events = config.get("events", {})
        plan_done = events.get("plan_done", {})
        context_map = plan_done.get("context_map", {})
        assert "session_id" not in context_map

    def test_dispatcher_plan_commit_msg_uses_chore(self):
        """FR-305a: dispatcher must pass chore: prefix for plan commit."""
        dispatcher_path = CHAPLAIN / "config" / "watcher-dispatcher.yaml"
        config = load_config(dispatcher_path)
        actions = config["actions"]["processing_topic"]
        command = actions[0]["command"]
        assert "plan_commit_msg" in command
        assert (
            'plan_commit_msg\\":\\"chore' in command
        ), f"Dispatcher plan_commit_msg must use chore: prefix, got: {command}"


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

    def test_plan_captures_fr_path(self):
        """capture_fr state uses bash_context to find FR file."""
        config = load_config(V2_PIPELINE_PATH)
        actions = get_action_config(config, "capture_fr")
        assert actions[0]["type"] == "bash_context"
        assert "fr_path" in actions[0].get("capture_keys", [])

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


# ═══════════════════════════════════════════════════════════════════════════
# FR-309: Judge event vocabulary alignment
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-316")
class TestV2JudgeVocabularyAlignment:
    """FR-309: Judge event_map aligned to prompt vocabulary."""

    def test_judge_event_map_has_amend(self):
        """FR-309 AC-01: event_map contains AMEND → revise."""
        config = load_config(V2_PIPELINE_PATH)
        judge_actions = get_action_config(config, "judge")
        event_map = judge_actions[0]["event_map"]
        assert "AMEND" in event_map
        assert event_map["AMEND"] == "revise"

    def test_judge_event_map_has_split(self):
        """FR-309 AC-01: event_map contains SPLIT → revise."""
        config = load_config(V2_PIPELINE_PATH)
        judge_actions = get_action_config(config, "judge")
        event_map = judge_actions[0]["event_map"]
        assert "SPLIT" in event_map
        assert event_map["SPLIT"] == "revise"

    def test_judge_event_map_no_revise(self):
        """FR-309 AC-02: event_map does NOT contain REVISE (old vocabulary)."""
        config = load_config(V2_PIPELINE_PATH)
        judge_actions = get_action_config(config, "judge")
        event_map = judge_actions[0]["event_map"]
        assert "REVISE" not in event_map

    def test_judge_fallback_is_error(self):
        """FR-309 AC-03 / FR-308: no-match fallback is error, not approve."""
        config = load_config(V2_PIPELINE_PATH)
        judge_actions = get_action_config(config, "judge")
        assert judge_actions[0]["success"] == "error"

    def test_judge_event_map_has_approve(self):
        """APPROVE still maps to approve (unchanged)."""
        config = load_config(V2_PIPELINE_PATH)
        judge_actions = get_action_config(config, "judge")
        event_map = judge_actions[0]["event_map"]
        assert "APPROVE" in event_map
        assert event_map["APPROVE"] == "approve"

    def test_judge_event_map_has_reject(self):
        """REJECT still maps to reject (unchanged)."""
        config = load_config(V2_PIPELINE_PATH)
        judge_actions = get_action_config(config, "judge")
        event_map = judge_actions[0]["event_map"]
        assert "REJECT" in event_map
        assert event_map["REJECT"] == "reject"

    def test_split_triggers_revise_transition(self):
        """FR-309 AC-08: SPLIT verdict routes judge→plan via revise event."""
        config = load_config(V2_PIPELINE_PATH)
        judge_actions = get_action_config(config, "judge")
        event_map = judge_actions[0]["event_map"]
        # SPLIT maps to revise
        split_event = event_map["SPLIT"]
        # revise transition exists (judge→plan)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "judge", "plan", split_event)
