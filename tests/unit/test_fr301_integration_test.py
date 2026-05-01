"""FR-301: Watcher FSM Integration Test (No-LLM End-to-End).

Acceptance tests for the integration pipeline and dispatcher configs.
These validate config structure, state mapping, and tooling — NOT the
actual end-to-end run (which requires GitHub API access).
"""

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

WORKTREE = Path(__file__).resolve().parents[2]
CHAPLAIN = WORKTREE / ".chaplain"
INTEGRATION_PIPELINE = CHAPLAIN / "config" / "integration-pipeline.yaml"
INTEGRATION_DISPATCHER = CHAPLAIN / "config" / "integration-dispatcher.yaml"
PRODUCTION_PIPELINE = CHAPLAIN / "config" / "watcher-pipeline.yaml"
PRODUCTION_DISPATCHER = CHAPLAIN / "config" / "watcher-dispatcher.yaml"
INTEGRATION_SCRIPT = WORKTREE / "scripts" / "run-integration-test.sh"
CONFESSIONS = WORKTREE / "docs" / "confessions.md"

HAS_FSM_CLI = shutil.which("statemachine-lint") is not None
requires_fsm_cli = pytest.mark.skipif(
    not HAS_FSM_CLI, reason="statemachine CLI tools not installed"
)


def load_config(path: Path) -> dict:
    """Load YAML config."""
    assert path.exists(), f"Config not found: {path}"
    with open(path) as f:
        return yaml.safe_load(f)


def get_action_types(config: dict) -> set[str]:
    """Extract all action types from config."""
    types = set()
    for _state, action_list in config.get("actions", {}).items():
        if isinstance(action_list, list):
            for action in action_list:
                if isinstance(action, dict):
                    types.add(action.get("type", ""))
    return types


def get_action_type_for_state(config: dict, state: str) -> str | None:
    """Get the action type for a specific state."""
    actions = config.get("actions", {})
    action_list = actions.get(state, [])
    if isinstance(action_list, list) and action_list:
        return action_list[0].get("type")
    return None


# ════════════════════════════════════════════════════════════════════════
# AC: Pipeline config structure
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
class TestIntegrationPipelineConfig:
    """Integration pipeline config validation."""

    def test_config_exists(self):
        """Integration pipeline config file exists."""
        assert INTEGRATION_PIPELINE.exists()

    def test_machine_name(self):
        """machine_name matches filename convention."""
        config = load_config(INTEGRATION_PIPELINE)
        assert config["metadata"]["machine_name"] == "integration-pipeline"

    def test_no_yamlgraph_async_actions(self):
        """No yamlgraph_async actions — all LLM steps are stubbed."""
        config = load_config(INTEGRATION_PIPELINE)
        action_types = get_action_types(config)
        assert (
            "yamlgraph_async" not in action_types
        ), f"Integration pipeline must not use yamlgraph_async: {action_types}"

    def test_has_state_mapping_comment(self):
        """A5: State mapping comment block at top of file."""
        text = INTEGRATION_PIPELINE.read_text()
        assert "STATE MAPPING" in text, "Missing state mapping comment block (A5)"
        assert "REAL" in text
        assert "STUBBED" in text
        assert "REMOVED" in text

    def test_planning_states_present(self):
        """Pipeline has planning phase states."""
        config = load_config(INTEGRATION_PIPELINE)
        states = set(config.get("states", []))
        planning = {
            "preflight",
            "worktree_setup",
            "planning",
            "committing_plan",
            "researching",
            "committing_research",
            "judging",
        }
        missing = planning - states
        assert not missing, f"Missing planning states: {missing}"

    def test_enforcement_states_present(self):
        """Pipeline has enforcement phase states."""
        config = load_config(INTEGRATION_PIPELINE)
        states = set(config.get("states", []))
        enforcement = {
            "implementing",
            "committing_implementation",
            "finalizing",
            "pushing",
            "creating_pr",
            "waiting_ci",
            "merging",
            "cleaning_up",
        }
        missing = enforcement - states
        assert not missing, f"Missing enforcement states: {missing}"

    def test_terminal_states_present(self):
        """Pipeline has terminal states."""
        config = load_config(INTEGRATION_PIPELINE)
        states = set(config.get("states", []))
        terminal = {"completed", "failed", "stopped"}
        missing = terminal - states
        assert not missing, f"Missing terminal states: {missing}"

    def test_removed_states_absent(self):
        """Removed production states are not in integration pipeline."""
        config = load_config(INTEGRATION_PIPELINE)
        states = set(config.get("states", []))
        removed = {
            "writing_tests",
            "verifying_red",
            "testing_demo",
            "critiquing",
            "remediating_ci",
            "forensics",
        }
        overlap = states & removed
        assert not overlap, f"Removed states still present: {overlap}"


# ════════════════════════════════════════════════════════════════════════
# AC: A1 — git_commit actions use real action type
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
class TestGitCommitActions:
    """A1: committing_* states use real git_commit action type."""

    @pytest.fixture()
    def config(self):
        return load_config(INTEGRATION_PIPELINE)

    def test_committing_plan_uses_git_commit(self, config):
        """committing_plan uses git_commit action type."""
        assert get_action_type_for_state(config, "committing_plan") == "git_commit"

    def test_committing_research_uses_git_commit(self, config):
        """committing_research uses git_commit action type."""
        assert get_action_type_for_state(config, "committing_research") == "git_commit"

    def test_committing_implementation_uses_git_commit(self, config):
        """committing_implementation uses git_commit action type."""
        assert (
            get_action_type_for_state(config, "committing_implementation")
            == "git_commit"
        )


# ════════════════════════════════════════════════════════════════════════
# AC: A3 — Failure path cleanup
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
class TestFailurePath:
    """A3: Failed state does cleanup."""

    def test_failed_state_has_action(self):
        """Failed state has an action defined."""
        config = load_config(INTEGRATION_PIPELINE)
        actions = config.get("actions", {})
        assert "failed" in actions, "No action for failed state"

    def test_failed_action_does_cleanup(self):
        """Failed action cleans up worktree, branch, PR, and topic."""
        config = load_config(INTEGRATION_PIPELINE)
        failed_action = config["actions"]["failed"]
        command = failed_action[0].get("command", "")
        assert "worktree_teardown" in command, "Failed action doesn't clean up worktree"
        assert (
            "git push origin --delete" in command
        ), "Failed action doesn't delete remote branch"
        assert "gh pr close" in command, "Failed action doesn't close PR"
        assert (
            ".chaplain/failed" in command
        ), "Failed action doesn't move topic to failed/"

    def test_all_states_can_reach_failed(self):
        """All non-terminal states have a transition to failed."""
        config = load_config(INTEGRATION_PIPELINE)
        transitions = config.get("transitions", [])
        terminal = {"completed", "failed", "stopped"}
        non_terminal = set(config.get("states", [])) - terminal

        # Collect states that have a path to failed
        can_fail = set()
        for t in transitions:
            if t.get("to") == "failed":
                from_state = t.get("from")
                if from_state == "*":
                    can_fail = non_terminal
                    break
                can_fail.add(from_state)

        missing = non_terminal - can_fail
        assert not missing, f"States without failure path: {missing}"


# ════════════════════════════════════════════════════════════════════════
# AC: Dispatcher config
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
class TestIntegrationDispatcherConfig:
    """Integration dispatcher config validation."""

    def test_config_exists(self):
        """Integration dispatcher config file exists."""
        assert INTEGRATION_DISPATCHER.exists()

    def test_machine_name(self):
        """machine_name matches filename convention."""
        config = load_config(INTEGRATION_DISPATCHER)
        assert config["metadata"]["machine_name"] == "integration-dispatcher"

    def test_default_inbox(self):
        """Default inbox points to integration inbox."""
        config = load_config(INTEGRATION_DISPATCHER)
        assert config["context"]["inbox_dir"] == ".chaplain/inbox-integration"

    def test_launches_integration_pipeline(self):
        """Dispatcher launches integration-pipeline.yaml, not production."""
        config = load_config(INTEGRATION_DISPATCHER)
        actions = config.get("actions", {})
        processing = actions.get("processing_topic", [])
        command = processing[0].get("command", "")
        assert "integration-pipeline.yaml" in command
        assert "watcher-pipeline.yaml" not in command

    def test_no_inbox_sync(self):
        """Integration dispatcher doesn't call inbox_sync.sh (no GitHub)."""
        config = load_config(INTEGRATION_DISPATCHER)
        actions = config.get("actions", {})
        syncing = actions.get("syncing_inbox", [])
        command = syncing[0].get("command", "")
        assert "inbox_sync.sh" not in command


# ════════════════════════════════════════════════════════════════════════
# AC: Production configs unchanged
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
class TestProductionUnchanged:
    """Production configs must not be modified by FR-301."""

    def test_production_pipeline_has_yamlgraph_async(self):
        """Production pipeline still uses yamlgraph_async for LLM steps."""
        config = load_config(PRODUCTION_PIPELINE)
        action_types = get_action_types(config)
        assert "yamlgraph_async" in action_types

    def test_production_dispatcher_machine_name(self):
        """Production dispatcher machine_name unchanged."""
        config = load_config(PRODUCTION_DISPATCHER)
        assert config["metadata"]["machine_name"] == "watcher-dispatcher"


# ════════════════════════════════════════════════════════════════════════
# AC: A4 — Test script wrapper
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
class TestIntegrationScript:
    """A4: run-integration-test.sh exists and is executable."""

    def test_script_exists(self):
        """Integration test wrapper script exists."""
        assert INTEGRATION_SCRIPT.exists()

    def test_script_executable(self):
        """Script has executable permission."""
        import os

        assert os.access(INTEGRATION_SCRIPT, os.X_OK)

    def test_script_seeds_inbox(self):
        """Script seeds the integration inbox."""
        text = INTEGRATION_SCRIPT.read_text()
        assert "inbox-integration" in text
        assert "TOPIC_SLUG" in text

    def test_script_runs_dispatcher(self):
        """Script invokes integration-dispatcher.yaml."""
        text = INTEGRATION_SCRIPT.read_text()
        assert "integration-dispatcher.yaml" in text


# ════════════════════════════════════════════════════════════════════════
# AC: A2 — Confession entry
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
class TestConfessionEntry:
    """A2: --no-verify documented in confessions."""

    def test_confession_exists(self):
        """CONF-300 documents --no-verify exception."""
        text = CONFESSIONS.read_text()
        assert "CONF-300" in text
        assert "--no-verify" in text
        assert "integration-pipeline" in text


# ════════════════════════════════════════════════════════════════════════
# AC: Lint validation
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
class TestLintValidation:
    """Both integration configs pass statemachine-lint."""

    @requires_fsm_cli
    def test_pipeline_lints_clean(self):
        """Integration pipeline passes statemachine-lint (excluding E008/E012 — custom types)."""
        result = subprocess.run(
            [
                "statemachine-lint",
                "--select",
                "E001,E002,E003,E004,E005,E006,E007",
                str(INTEGRATION_PIPELINE),
            ],
            capture_output=True,
            text=True,
        )
        assert (
            "0 errors" in result.stdout
        ), f"statemachine-lint failed:\n{result.stdout}\n{result.stderr}"

    @requires_fsm_cli
    def test_dispatcher_lints_clean(self):
        """Integration dispatcher passes statemachine-lint (excluding E008/E012 — custom types)."""
        result = subprocess.run(
            [
                "statemachine-lint",
                "--select",
                "E001,E002,E003,E004,E005,E006,E007",
                str(INTEGRATION_DISPATCHER),
            ],
            capture_output=True,
            text=True,
        )
        assert (
            "0 errors" in result.stdout
        ), f"statemachine-lint failed:\n{result.stdout}\n{result.stderr}"


# ════════════════════════════════════════════════════════════════════════
# FR-302: Integration Test CI Compliance
# ════════════════════════════════════════════════════════════════════════


CREATE_PR_SCRIPT = CHAPLAIN / "lib" / "watcher" / "create_pr.sh"
PREFLIGHT_SCRIPT = CHAPLAIN / "lib" / "watcher" / "preflight.sh"


@pytest.mark.req("REQ-YG-162")
class TestFR302TitleOverride:
    """AC-1/AC-2: create_pr.sh supports --title flag, pipeline uses docs: title."""

    def test_create_pr_accepts_title_flag(self):
        """AC-1: create_pr.sh parses --title argument."""
        text = CREATE_PR_SCRIPT.read_text()
        assert "--title" in text, "create_pr.sh must accept --title flag"
        assert "TITLE_OVERRIDE" in text, "create_pr.sh must use TITLE_OVERRIDE variable"

    def test_pipeline_passes_docs_title(self):
        """AC-2: Integration pipeline uses docs(integration) PR title."""
        config = load_config(INTEGRATION_PIPELINE)
        creating_pr = config["actions"]["creating_pr"]
        command = creating_pr[0].get("command", "")
        assert '--title "docs(integration): smoke test"' in command


@pytest.mark.req("REQ-YG-162")
class TestFR302PreflightRuff:
    """AC-3: Ruff check added to preflight.sh."""

    def test_preflight_checks_ruff(self):
        """AC-3: preflight.sh runs ruff check and ruff format."""
        text = PREFLIGHT_SCRIPT.read_text()
        assert "ruff check" in text, "preflight.sh must run ruff check"
        assert "ruff format" in text, "preflight.sh must run ruff format"


@pytest.mark.req("REQ-YG-162")
class TestFR302ChangelogGenRemoved:
    """AC-6: changelog_gen state fully removed from integration pipeline."""

    def test_changelog_gen_not_in_states(self):
        """changelog_gen is not in the states list."""
        config = load_config(INTEGRATION_PIPELINE)
        states = config.get("states", [])
        assert "changelog_gen" not in states

    def test_changelog_done_not_in_events(self):
        """changelog_done event is removed."""
        config = load_config(INTEGRATION_PIPELINE)
        events = config.get("events", {})
        assert "changelog_done" not in events

    def test_no_changelog_gen_action_block(self):
        """No action block for changelog_gen."""
        config = load_config(INTEGRATION_PIPELINE)
        actions = config.get("actions", {})
        assert "changelog_gen" not in actions

    def test_implementation_committed_routes_to_finalizing(self):
        """implementation_committed routes directly to finalizing."""
        config = load_config(INTEGRATION_PIPELINE)
        transitions = config.get("transitions", [])
        ic_transitions = [
            t for t in transitions if t.get("event") == "implementation_committed"
        ]
        assert len(ic_transitions) == 1
        assert ic_transitions[0]["from"] == "committing_implementation"
        assert ic_transitions[0]["to"] == "finalizing"


@pytest.mark.req("REQ-YG-162")
class TestFR302CompletedTermination:
    """AC-7: completed state terminates cleanly via job_done → stopped."""

    def test_completed_has_job_done_transition(self):
        """completed state transitions to stopped on job_done."""
        config = load_config(INTEGRATION_PIPELINE)
        transitions = config.get("transitions", [])
        completed_transitions = [
            t
            for t in transitions
            if t.get("from") == "completed" and t.get("event") == "job_done"
        ]
        assert len(completed_transitions) == 1
        assert completed_transitions[0]["to"] == "stopped"


@pytest.mark.req("REQ-YG-162")
class TestFR302RunScript:
    """AC-4: run-integration-test.sh kills dispatcher and asserts exit code."""

    def test_script_backgrounds_dispatcher(self):
        """Script runs dispatcher in background."""
        text = INTEGRATION_SCRIPT.read_text()
        assert "DISPATCHER_PID" in text, "Script must capture dispatcher PID"

    def test_script_kills_dispatcher(self):
        """Script kills dispatcher after pipeline terminates."""
        text = INTEGRATION_SCRIPT.read_text()
        assert 'kill "$DISPATCHER_PID"' in text

    def test_script_checks_completed(self):
        """Script asserts pipeline reached completed state."""
        text = INTEGRATION_SCRIPT.read_text()
        assert "completed --job_done--> stopped" in text
