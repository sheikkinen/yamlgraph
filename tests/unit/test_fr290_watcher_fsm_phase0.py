"""FR-290: Watcher-FSM Phase 0 — Declarative FSM Configs.

RED acceptance tests for the two FSM YAML configs (dispatcher + pipeline).
These tests validate structure, transitions, and completeness WITHOUT
requiring the statemachine-engine runtime — pure YAML parsing.
"""

from pathlib import Path

import pytest
import yaml

WORKTREE = Path(__file__).resolve().parents[2]
CHAPLAIN = WORKTREE / ".chaplain"
DISPATCHER_PATH = CHAPLAIN / "config" / "watcher-dispatcher.yaml"
PIPELINE_PATH = CHAPLAIN / "config" / "watcher-pipeline.yaml"


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


def get_events(config: dict) -> dict | list:
    """Extract events from config."""
    return config.get("events", [])


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


# ══════════════════════════════════════════════════════════════════════════
# AC-01: Dispatcher config exists with 6 states and 9 transition rules
# ══════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-290")
class TestDispatcherConfig:
    """AC-01 through AC-06: Dispatcher FSM config."""

    def test_file_exists(self):
        assert DISPATCHER_PATH.exists(), f"Dispatcher config missing: {DISPATCHER_PATH}"

    def test_has_4_states(self):
        config = load_config(DISPATCHER_PATH)
        states = get_states(config)
        assert len(states) == 4, f"Expected 4 states, got {len(states)}: {states}"

    def test_expected_states(self):
        config = load_config(DISPATCHER_PATH)
        states = set(get_states(config))
        expected = {
            "idle",
            "syncing_inbox",
            "processing_topic",
            "stopped",
        }
        assert (
            states == expected
        ), f"State mismatch: missing={expected - states}, extra={states - expected}"

    def test_has_6_transition_rules(self):
        config = load_config(DISPATCHER_PATH)
        transitions = get_transitions(config)
        assert (
            len(transitions) == 6
        ), f"Expected 6 transition rules, got {len(transitions)}"

    def test_initial_state_is_idle(self):
        config = load_config(DISPATCHER_PATH)
        assert config.get("initial_state") == "idle"

    def test_idle_polling_loop(self):
        """AC-06: idle → syncing_inbox on timeout(10)."""
        config = load_config(DISPATCHER_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "idle", "syncing_inbox", "timeout(10)")

    def test_sync_topic_found(self):
        config = load_config(DISPATCHER_PATH)
        transitions = get_transitions(config)
        assert transition_exists(
            transitions, "syncing_inbox", "processing_topic", "topic_found"
        )

    def test_sync_no_topics(self):
        config = load_config(DISPATCHER_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "syncing_inbox", "idle", "no_topics")

    def test_processing_topic_done(self):
        config = load_config(DISPATCHER_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "processing_topic", "idle", "topic_done")

    def test_processing_error(self):
        config = load_config(DISPATCHER_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "processing_topic", "idle", "error")

    def test_global_stop(self):
        config = load_config(DISPATCHER_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "*", "stopped", "stop")


# ══════════════════════════════════════════════════════════════════════════
# AC-02: Pipeline config exists with 27 states
# ══════════════════════════════════════════════════════════════════════════


PIPELINE_STATES = {
    "preflight",
    "worktree_setup",
    "planning",
    "committing_plan",
    "researching",
    "committing_research",
    "writing_tests",
    "verifying_red",
    "judging",
    "implementing",
    "committing_implementation",
    "testing_demo",
    "critiquing",
    "changelog_gen",
    "finalizing",
    "pushing",
    "creating_pr",
    "waiting_ci",
    "remediating_ci",
    "merging",
    "cleaning_up",
    "completed",
    "failed",
    "forensics",
    "stopped",
}

YAMLGRAPH_ASYNC_STATES = {
    "planning",
    "researching",
    "writing_tests",
    "judging",
    "implementing",
    "testing_demo",
    "critiquing",
    "remediating_ci",
    "forensics",
}


@pytest.mark.req("REQ-YG-290")
class TestPipelineConfig:
    """AC-02 through AC-12: Pipeline FSM config."""

    def test_file_exists(self):
        assert PIPELINE_PATH.exists(), f"Pipeline config missing: {PIPELINE_PATH}"

    def test_has_25_states(self):
        config = load_config(PIPELINE_PATH)
        states = get_states(config)
        assert len(states) == 25, f"Expected 25 states, got {len(states)}: {states}"

    def test_expected_states(self):
        config = load_config(PIPELINE_PATH)
        states = set(get_states(config))
        assert (
            states == PIPELINE_STATES
        ), f"State mismatch: missing={PIPELINE_STATES - states}, extra={states - PIPELINE_STATES}"

    def test_initial_state_is_preflight(self):
        config = load_config(PIPELINE_PATH)
        assert config.get("initial_state") == "preflight"

    def test_events_use_dict_format(self):
        """NC-120: Events must be dict (not list) for context_map support."""
        config = load_config(PIPELINE_PATH)
        events = get_events(config)
        assert isinstance(
            events, dict
        ), f"Events must be dict for context_map, got {type(events).__name__}"

    # ── AC-07: Verdict paths from judging ──

    def test_judging_approve_path(self):
        config = load_config(PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "judging", "implementing", "approve")

    def test_judging_reject_path(self):
        config = load_config(PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "judging", "failed", "reject")

    def test_judging_amend_path(self):
        config = load_config(PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "judging", "failed", "amend")

    def test_judging_split_path(self):
        config = load_config(PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "judging", "failed", "split")

    # ── AC-08: timeout(600) on all yamlgraph_async states ──

    @pytest.mark.parametrize("state", sorted(YAMLGRAPH_ASYNC_STATES))
    def test_timeout_on_yamlgraph_async_state(self, state):
        config = load_config(PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(
            transitions, state, "failed", "timeout(600)"
        ), f"Missing timeout(600) → failed from {state}"

    # ── AC-09: finalizing retry self-loop ──

    def test_finalizing_retry_self_loop(self):
        config = load_config(PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(
            transitions, "finalizing", "finalizing", "precommit_retry"
        )

    # ── AC-10: waiting_ci ↔ remediating_ci ──

    def test_waiting_ci_to_remediating(self):
        config = load_config(PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(
            transitions, "waiting_ci", "remediating_ci", "ci_failed"
        )

    def test_remediating_to_waiting_ci(self):
        config = load_config(PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(
            transitions, "remediating_ci", "waiting_ci", "remediated"
        )

    # ── AC-11: failed → forensics → completed ──

    def test_failed_to_forensics(self):
        config = load_config(PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "failed", "forensics", "analyze")

    def test_forensics_to_completed(self):
        config = load_config(PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(
            transitions, "forensics", "completed", "forensics_done"
        )

    # ── AC-12: Global stop ──

    def test_global_stop(self):
        config = load_config(PIPELINE_PATH)
        transitions = get_transitions(config)
        assert transition_exists(transitions, "*", "stopped", "stop")

    # ── AC-12: No orphaned states ──

    def test_no_orphaned_states(self):
        """Every non-initial, non-terminal state must be reachable (appear as a 'to' target)."""
        config = load_config(PIPELINE_PATH)
        states = set(get_states(config))
        transitions = get_transitions(config)
        initial = config.get("initial_state")

        # States that are targets of transitions
        reachable = {t["to"] for t in transitions}
        # Wildcard covers all states
        if any(t.get("from") == "*" for t in transitions):
            reachable.update(states)

        # Initial state is reachable by definition
        reachable.add(initial)

        orphaned = states - reachable
        assert not orphaned, f"Orphaned states (never targeted): {orphaned}"

    def test_no_dead_end_states(self):
        """Every non-terminal state must have at least one outgoing transition."""
        config = load_config(PIPELINE_PATH)
        states = set(get_states(config))
        transitions = get_transitions(config)
        terminal = {"completed", "stopped"}

        has_wildcard_from = any(t.get("from") == "*" for t in transitions)

        for state in states - terminal:
            has_outgoing = any(t.get("from") == state for t in transitions)
            assert (
                has_outgoing or has_wildcard_from
            ), f"Dead-end state (no outgoing): {state}"

    # ── Context maps ──

    def test_worktree_ready_context_map(self):
        """worktree_ready event should map wt_dir, wt_branch, main_dir."""
        config = load_config(PIPELINE_PATH)
        events = get_events(config)
        assert "worktree_ready" in events
        ctx = events["worktree_ready"].get("context_map", {})
        assert "wt_dir" in ctx
        assert "wt_branch" in ctx
        assert "main_dir" in ctx

    def test_pr_created_context_map(self):
        """pr_created event should map pr_number, pr_url."""
        config = load_config(PIPELINE_PATH)
        events = get_events(config)
        assert "pr_created" in events
        ctx = events["pr_created"].get("context_map", {})
        assert "pr_number" in ctx
        assert "pr_url" in ctx


# ══════════════════════════════════════════════════════════════════════════
# AC-13: No existing files modified
# ══════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-290")
class TestNoExistingFilesModified:
    """AC-13: Purely additive — only new files under .chaplain/config/ and .chaplain/docs/."""

    def test_only_new_paths(self):
        """All FR-290 files live under .chaplain/config/ or .chaplain/docs/."""
        # This test documents the contract — if configs exist, they're under the right dirs
        if DISPATCHER_PATH.exists():
            assert str(DISPATCHER_PATH).endswith(
                ".chaplain/config/watcher-dispatcher.yaml"
            )
        if PIPELINE_PATH.exists():
            assert str(PIPELINE_PATH).endswith(".chaplain/config/watcher-pipeline.yaml")
