"""FR-301/FR-303: Watcher FSM Integration Test (Unified Pipeline).

Acceptance tests for the unified watcher pipeline and integration dispatcher.
FR-303 unified the separate integration-pipeline.yaml into watcher-pipeline.yaml
with action directory swap (--actions-dir .chaplain/actions-stub).

These validate config structure, stub directory, and tooling — NOT the
actual end-to-end run (which requires GitHub API access).
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

WORKTREE = Path(__file__).resolve().parents[2]
CHAPLAIN = WORKTREE / ".chaplain"
UNIFIED_PIPELINE = CHAPLAIN / "config" / "watcher-pipeline.yaml"
INTEGRATION_DISPATCHER = CHAPLAIN / "config" / "integration-dispatcher.yaml"
PRODUCTION_DISPATCHER = CHAPLAIN / "config" / "watcher-dispatcher.yaml"
INTEGRATION_SCRIPT = WORKTREE / "scripts" / "run-integration-test.sh"
CONFESSIONS = WORKTREE / "docs" / "confessions.md"
ACTIONS_DIR = CHAPLAIN / "actions"
ACTIONS_STUB_DIR = CHAPLAIN / "actions-stub"

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
class TestUnifiedPipelineConfig:
    """Unified pipeline config validation (FR-303)."""

    def test_config_exists(self):
        """Unified pipeline config file exists."""
        assert UNIFIED_PIPELINE.exists()

    def test_machine_name(self):
        """machine_name matches filename convention."""
        config = load_config(UNIFIED_PIPELINE)
        assert config["metadata"]["machine_name"] == "watcher2_pipeline"

    def test_has_yamlgraph_async_actions(self):
        """Unified pipeline uses yamlgraph_async for LLM steps."""
        config = load_config(UNIFIED_PIPELINE)
        action_types = get_action_types(config)
        assert "yamlgraph_async" in action_types

    def test_planning_states_present(self):
        """Pipeline has all planning phase states."""
        config = load_config(UNIFIED_PIPELINE)
        states = set(config.get("states", []))
        planning = {
            "preflight",
            "worktree_setup",
            "planning",
            "committing_plan",
            "researching",
            "committing_research",
            "writing_tests",
            "verifying_red",
            "judging",
        }
        missing = planning - states
        assert not missing, f"Missing planning states: {missing}"

    def test_enforcement_states_present(self):
        """Pipeline has all enforcement phase states."""
        config = load_config(UNIFIED_PIPELINE)
        states = set(config.get("states", []))
        enforcement = {
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
        }
        missing = enforcement - states
        assert not missing, f"Missing enforcement states: {missing}"

    def test_terminal_states_present(self):
        """Pipeline has terminal states."""
        config = load_config(UNIFIED_PIPELINE)
        states = set(config.get("states", []))
        terminal = {"completed", "failed", "forensics", "stopped"}
        missing = terminal - states
        assert not missing, f"Missing terminal states: {missing}"

    def test_error_event_declared(self):
        """Pipeline has failure paths (timeout or explicit transitions to failed)."""
        config = load_config(UNIFIED_PIPELINE)
        transitions = config.get("transitions", [])
        to_failed = [t for t in transitions if t.get("to") == "failed"]
        assert (
            len(to_failed) >= 3
        ), f"Expected at least 3 paths to failed, got {len(to_failed)}"

    def test_llm_states_have_timeout_to_failed(self):
        """LLM-dependent states have timeout(600) -> failed."""
        config = load_config(UNIFIED_PIPELINE)
        transitions = config.get("transitions", [])
        timeout_states = set()
        for t in transitions:
            if t.get("to") == "failed" and "timeout" in str(t.get("event", "")):
                timeout_states.add(t.get("from"))
        # At minimum planning and researching should have timeouts
        assert (
            "planning" in timeout_states or len(timeout_states) >= 2
        ), f"Expected timeout guards on LLM states, got: {timeout_states}"


# ════════════════════════════════════════════════════════════════════════
# FR-303 Phase 1: Custom action types
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
class TestCustomActionTypes:
    """Pipeline action types match current implementation."""

    def test_verify_red_uses_bash(self):
        """verifying_red uses bash action type (inline pytest invocation)."""
        config = load_config(UNIFIED_PIPELINE)
        assert get_action_type_for_state(config, "verifying_red") == "bash"

    def test_changelog_gen_uses_bash(self):
        """changelog_gen uses bash action type."""
        config = load_config(UNIFIED_PIPELINE)
        assert get_action_type_for_state(config, "changelog_gen") == "bash"

    def test_failed_uses_bash(self):
        """failed uses bash action type (move topic to failed/)."""
        config = load_config(UNIFIED_PIPELINE)
        assert get_action_type_for_state(config, "failed") == "bash"

    def test_production_action_files_exist(self):
        """Core custom action files exist in production actions dir."""
        assert (ACTIONS_DIR / "bash_context_action.py").exists()
        assert (ACTIONS_DIR / "yamlgraph_async_action.py").exists()
        assert (ACTIONS_DIR / "git_commit_action.py").exists()
        assert (ACTIONS_DIR / "precommit_action.py").exists()


# ════════════════════════════════════════════════════════════════════════
# Context variable interpolation
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
class TestContextVariables:
    """Pipeline actions use context variable interpolation."""

    def test_merging_uses_pr_number(self):
        """merging command references {pr_number}."""
        config = load_config(UNIFIED_PIPELINE)
        merging = config["actions"]["merging"]
        command = merging[0].get("command", "")
        assert "{pr_number}" in command

    def test_creating_pr_uses_branch(self):
        """creating_pr command references {wt_branch}."""
        config = load_config(UNIFIED_PIPELINE)
        creating_pr = config["actions"]["creating_pr"]
        command = creating_pr[0].get("command", "")
        assert "{wt_branch}" in command

    def test_completed_runs_post_merge(self):
        """completed command calls post_merge.sh."""
        config = load_config(UNIFIED_PIPELINE)
        completed = config["actions"]["completed"]
        command = completed[0].get("command", "")
        assert "post_merge" in command

    def test_committing_plan_uses_topic_file(self):
        """committing_plan references {topic_file} in commit message."""
        config = load_config(UNIFIED_PIPELINE)
        committing = config["actions"]["committing_plan"]
        message = committing[0].get("message", "")
        assert "{topic_file}" in message

    def test_committing_plan_adds_feature_requests(self):
        """committing_plan stages feature-requests/ directory."""
        config = load_config(UNIFIED_PIPELINE)
        committing = config["actions"]["committing_plan"]
        add_paths = committing[0].get("add_paths", [])
        assert "feature-requests/" in add_paths


# ════════════════════════════════════════════════════════════════════════
# FR-303 Phase 3: Stub directory
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
class TestStubDirectory:
    """FR-303 Phase 3: actions-stub/ directory with stubs and symlinks."""

    def test_stub_dir_exists(self):
        """actions-stub/ directory exists."""
        assert ACTIONS_STUB_DIR.exists()
        assert ACTIONS_STUB_DIR.is_dir()

    def test_stub_yamlgraph_async_exists(self):
        """Stub yamlgraph_async_action.py exists (not a symlink)."""
        stub = ACTIONS_STUB_DIR / "yamlgraph_async_action.py"
        assert stub.exists()
        assert not stub.is_symlink()

    def test_stub_verify_red_exists(self):
        """Stub verify_red_action.py exists (not a symlink)."""
        stub = ACTIONS_STUB_DIR / "verify_red_action.py"
        assert stub.exists()
        assert not stub.is_symlink()

    def test_stub_changelog_gen_exists(self):
        """Stub changelog_gen_action.py exists (not a symlink)."""
        stub = ACTIONS_STUB_DIR / "changelog_gen_action.py"
        assert stub.exists()
        assert not stub.is_symlink()

    def test_stub_failure_cleanup_exists(self):
        """Stub failure_cleanup_action.py exists (not a symlink)."""
        stub = ACTIONS_STUB_DIR / "failure_cleanup_action.py"
        assert stub.exists()
        assert not stub.is_symlink()

    def test_bash_context_symlinked(self):
        """bash_context_action.py is symlinked to real action."""
        stub = ACTIONS_STUB_DIR / "bash_context_action.py"
        assert stub.exists()
        assert stub.is_symlink()

    def test_git_commit_symlinked(self):
        """git_commit_action.py is symlinked to real action."""
        stub = ACTIONS_STUB_DIR / "git_commit_action.py"
        assert stub.exists()
        assert stub.is_symlink()

    def test_precommit_symlinked(self):
        """precommit_action.py is symlinked to real action."""
        stub = ACTIONS_STUB_DIR / "precommit_action.py"
        assert stub.exists()
        assert stub.is_symlink()

    def test_symlinks_resolve(self):
        """All symlinks resolve to existing files."""
        for name in [
            "bash_context_action.py",
            "git_commit_action.py",
            "precommit_action.py",
        ]:
            stub = ACTIONS_STUB_DIR / name
            assert stub.resolve().exists(), f"Symlink {name} does not resolve"

    def test_stub_yamlgraph_async_has_intent_sequence(self):
        """Stub yamlgraph_async supports _intent_sequence pattern."""
        text = (ACTIONS_STUB_DIR / "yamlgraph_async_action.py").read_text()
        assert "_intent_sequence" in text

    def test_stub_yamlgraph_async_creates_files(self):
        """Stub yamlgraph_async creates placeholder files in worktree."""
        text = (ACTIONS_STUB_DIR / "yamlgraph_async_action.py").read_text()
        assert "watcher-integration.md" in text


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

    def test_launches_unified_pipeline(self):
        """Dispatcher launches watcher-pipeline.yaml with actions-stub (FR-303)."""
        config = load_config(INTEGRATION_DISPATCHER)
        actions = config.get("actions", {})
        processing = actions.get("processing_topic", [])
        command = processing[0].get("command", "")
        assert "watcher-pipeline.yaml" in command
        assert "actions-stub" in command

    def test_passes_integration_context_variables(self):
        """Dispatcher passes integration profile context variables."""
        config = load_config(INTEGRATION_DISPATCHER)
        actions = config.get("actions", {})
        processing = actions.get("processing_topic", [])
        command = processing[0].get("command", "")
        assert "merge_flags" in command
        assert "pr_title_flag" in command
        assert "post_merge_cmd" in command
        assert "plan_commit_msg" in command

    def test_no_inbox_sync(self):
        """Integration dispatcher doesn't call inbox_sync.sh (no GitHub)."""
        config = load_config(INTEGRATION_DISPATCHER)
        actions = config.get("actions", {})
        syncing = actions.get("syncing_inbox", [])
        command = syncing[0].get("command", "")
        assert "inbox_sync.sh" not in command


# ════════════════════════════════════════════════════════════════════════
# Production dispatcher context variables
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
class TestProductionDispatcher:
    """Production dispatcher passes production context variables."""

    def test_production_pipeline_has_yamlgraph_async(self):
        """Production pipeline still uses yamlgraph_async for LLM steps."""
        config = load_config(UNIFIED_PIPELINE)
        action_types = get_action_types(config)
        assert "yamlgraph_async" in action_types

    def test_production_dispatcher_machine_name(self):
        """Production dispatcher machine_name unchanged."""
        config = load_config(PRODUCTION_DISPATCHER)
        assert config["metadata"]["machine_name"] == "watcher-dispatcher"

    def test_production_dispatcher_passes_delete_branch(self):
        """Production dispatcher passes --delete-branch in merge_flags."""
        config = load_config(PRODUCTION_DISPATCHER)
        actions = config.get("actions", {})
        processing = actions.get("processing_topic", [])
        command = processing[0].get("command", "")
        assert "--delete-branch" in command

    def test_production_dispatcher_passes_post_merge(self):
        """Production dispatcher passes post_merge.sh command."""
        config = load_config(PRODUCTION_DISPATCHER)
        actions = config.get("actions", {})
        processing = actions.get("processing_topic", [])
        command = processing[0].get("command", "")
        assert "post_merge.sh" in command


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


# ════════════════════════════════════════════════════════════════════════
# AC: Lint validation
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
class TestLintValidation:
    """Unified pipeline and dispatcher pass statemachine-lint."""

    @requires_fsm_cli
    def test_pipeline_lints_clean(self):
        """Unified pipeline passes statemachine-lint."""
        result = subprocess.run(
            [
                "statemachine-lint",
                "--select",
                "E001,E002,E003,E004,E005,E006,E007",
                str(UNIFIED_PIPELINE),
            ],
            capture_output=True,
            text=True,
        )
        assert (
            "0 errors" in result.stdout
        ), f"statemachine-lint failed:\n{result.stdout}\n{result.stderr}"

    @requires_fsm_cli
    def test_dispatcher_lints_clean(self):
        """Integration dispatcher passes statemachine-lint."""
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
    """AC-1/AC-2: create_pr.sh supports --title flag, dispatcher passes it."""

    def test_create_pr_accepts_title_flag(self):
        """AC-1: create_pr.sh parses --title argument."""
        text = CREATE_PR_SCRIPT.read_text()
        assert "--title" in text, "create_pr.sh must accept --title flag"
        assert "TITLE_OVERRIDE" in text

    def test_dispatcher_passes_docs_title(self):
        """AC-2: Integration dispatcher passes docs(integration) PR title via context."""
        config = load_config(INTEGRATION_DISPATCHER)
        actions = config.get("actions", {})
        processing = actions.get("processing_topic", [])
        command = processing[0].get("command", "")
        assert "docs(integration): smoke test" in command


@pytest.mark.req("REQ-YG-162")
class TestFR302PreflightRuff:
    """AC-3: Ruff check added to preflight.sh."""

    def test_preflight_checks_ruff(self):
        """AC-3: preflight.sh runs ruff check and ruff format."""
        text = PREFLIGHT_SCRIPT.read_text()
        assert "ruff check" in text, "preflight.sh must run ruff check"
        assert "ruff format" in text, "preflight.sh must run ruff format"


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
        assert "terminal state: completed" in text
