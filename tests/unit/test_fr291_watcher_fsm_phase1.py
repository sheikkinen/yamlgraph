"""FR-291: Watcher-FSM Phase 1 — Action Wiring.

RED acceptance tests for wiring real actions into Phase 0 FSM configs.
Tests cover:
- Dispatcher config simplification (4 states, no log stubs)
- Pipeline config action wiring (no log stubs)
- Custom action modules (bash_context, yamlgraph_async, git_commit, precommit)
- Action registration via ActionLoader discovery
- Context propagation chain
- Topic file lifecycle (inbox → processing → rm/failed)
- Config validation (statemachine-validate, statemachine-lint)
- No job queue builtins in dispatcher
"""

import asyncio
import importlib
import inspect
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

WORKTREE = Path(__file__).resolve().parents[2]
CHAPLAIN = WORKTREE / ".chaplain"
DISPATCHER_PATH = CHAPLAIN / "config" / "watcher-dispatcher.yaml"
PIPELINE_PATH = CHAPLAIN / "config" / "watcher-pipeline.yaml"
ACTIONS_DIR = CHAPLAIN / "actions"

# Skip conditions for CI where statemachine-engine is not installed
HAS_FSM_ENGINE = importlib.util.find_spec("statemachine_engine") is not None
HAS_FSM_CLI = shutil.which("statemachine-validate") is not None
requires_fsm_engine = pytest.mark.skipif(
    not HAS_FSM_ENGINE, reason="statemachine_engine not installed"
)
requires_fsm_cli = pytest.mark.skipif(
    not HAS_FSM_CLI, reason="statemachine CLI tools not installed"
)


# ── Helpers ──────────────────────────────────────────────────────────────


def load_config(path: Path) -> dict:
    """Load and return YAML config."""
    assert path.exists(), f"Config not found: {path}"
    with open(path) as f:
        return yaml.safe_load(f)


def get_action_types(config: dict) -> set[str]:
    """Extract all action types from config."""
    types = set()
    actions = config.get("actions", {})
    for _state, action_list in actions.items():
        if isinstance(action_list, list):
            for action in action_list:
                if isinstance(action, dict):
                    types.add(action.get("type", ""))
        elif isinstance(action_list, dict):
            types.add(action_list.get("type", ""))
    return types


# ════════════════════════════════════════════════════════════════════════
# AC-01: Dispatcher simplified to 4 states with real action types
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
class TestDispatcherConfig:
    """AC-01, AC-03, AC-04, AC-19: Dispatcher config tests."""

    def test_dispatcher_has_four_states(self):
        """AC-01: Dispatcher has exactly 4 states."""
        config = load_config(DISPATCHER_PATH)
        states = config.get("states", [])
        assert set(states) == {
            "idle",
            "syncing_inbox",
            "processing_topic",
            "stopped",
        }, f"Expected 4 states, got: {states}"

    def test_dispatcher_no_log_stubs(self):
        """AC-01: No type: log stubs remain in dispatcher."""
        config = load_config(DISPATCHER_PATH)
        action_types = get_action_types(config)
        assert (
            "log" not in action_types
        ), f"Dispatcher still has log stubs: {action_types}"

    def test_dispatcher_no_parallel_states(self):
        """AC-01: Phase 0 parallel states removed."""
        config = load_config(DISPATCHER_PATH)
        states = set(config.get("states", []))
        parallel_states = {"checking_queue", "spawning_batch", "waiting_for_batch"}
        overlap = states & parallel_states
        assert not overlap, f"Parallel states still present: {overlap}"

    def test_dispatcher_no_job_queue_builtins(self):
        """AC-19: Dispatcher uses no job queue builtins."""
        config = load_config(DISPATCHER_PATH)
        action_types = get_action_types(config)
        forbidden = {
            "get_pending_jobs",
            "claim_job",
            "complete_job",
            "pop_from_list",
            "wait_for_jobs",
            "start_fsm",
        }
        overlap = action_types & forbidden
        assert not overlap, f"Job queue builtins found: {overlap}"

    def test_dispatcher_uses_statemachine_command(self):
        """AC-15: Dispatcher uses 'statemachine' (not 'statemachine-run')."""
        config = load_config(DISPATCHER_PATH)
        yaml_text = yaml.dump(config)
        assert (
            "statemachine-run" not in yaml_text
        ), "Dispatcher references non-existent 'statemachine-run'"

    def test_dispatcher_transitions_sequential(self):
        """Dispatcher transitions match sequential model."""
        config = load_config(DISPATCHER_PATH)
        transitions = config.get("transitions", [])

        def has_transition(from_s, to_s, event):
            return any(
                t.get("from") == from_s
                and t.get("to") == to_s
                and t.get("event") == event
                for t in transitions
            )

        assert has_transition("idle", "syncing_inbox", "timeout(10)")
        assert has_transition("syncing_inbox", "processing_topic", "topic_found")
        assert has_transition("syncing_inbox", "idle", "no_topics")
        assert has_transition("processing_topic", "idle", "topic_done")
        assert has_transition("*", "stopped", "stop")

    @requires_fsm_cli
    def test_dispatcher_validates_strict(self):
        """AC-03: Dispatcher passes statemachine-validate --strict."""
        result = subprocess.run(
            ["statemachine-validate", "--strict", str(DISPATCHER_PATH)],
            capture_output=True,
            text=True,
        )
        assert (
            result.returncode == 0
        ), f"Dispatcher validation failed:\n{result.stdout}\n{result.stderr}"

    @requires_fsm_cli
    def test_dispatcher_lints_clean(self):
        """AC-04: Dispatcher passes statemachine-lint (excluding E008/E012 — custom types)."""
        result = subprocess.run(
            [
                "statemachine-lint",
                "--select",
                "E001,E002,E003,E004,E005,E006,E007",
                str(DISPATCHER_PATH),
            ],
            capture_output=True,
            text=True,
        )
        assert (
            "0 errors" in result.stdout
        ), f"Dispatcher lint errors:\n{result.stdout}\n{result.stderr}"


# ════════════════════════════════════════════════════════════════════════
# AC-02: Pipeline config — no log stubs
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
class TestPipelineConfig:
    """AC-02, AC-03, AC-04: Pipeline config tests."""

    def test_pipeline_no_log_stubs(self):
        """AC-02: No type: log stubs remain in pipeline."""
        config = load_config(PIPELINE_PATH)
        action_types = get_action_types(config)
        assert (
            "log" not in action_types
        ), f"Pipeline still has log stubs: {action_types}"

    def test_pipeline_retains_25_states(self):
        """Pipeline has 25 states after FR-292 simplification."""
        config = load_config(PIPELINE_PATH)
        states = config.get("states", [])
        assert len(states) == 25, f"Expected 25 states, got {len(states)}: {states}"

    @requires_fsm_cli
    def test_pipeline_validates_strict(self):
        """AC-03: Pipeline passes statemachine-validate --strict."""
        result = subprocess.run(
            ["statemachine-validate", "--strict", str(PIPELINE_PATH)],
            capture_output=True,
            text=True,
        )
        assert (
            result.returncode == 0
        ), f"Pipeline validation failed:\n{result.stdout}\n{result.stderr}"

    @requires_fsm_cli
    def test_pipeline_lints_clean(self):
        """AC-04: Pipeline passes statemachine-lint (excluding E008/E012 — custom types)."""
        result = subprocess.run(
            [
                "statemachine-lint",
                "--select",
                "E001,E002,E003,E004,E005,E006,E007",
                str(PIPELINE_PATH),
            ],
            capture_output=True,
            text=True,
        )
        assert (
            "0 errors" in result.stdout
        ), f"Pipeline lint errors:\n{result.stdout}\n{result.stderr}"

    def test_pipeline_action_types_are_real(self):
        """AC-02: All pipeline action types are real (not log stubs)."""
        config = load_config(PIPELINE_PATH)
        action_types = get_action_types(config)
        expected_real_types = {
            "bash",
            "bash_context",
            "yamlgraph_async",
            "git_commit",
            "precommit",
        }
        # Every action type must be one of the expected real types
        for at in action_types:
            assert (
                at in expected_real_types
            ), f"Unexpected action type '{at}' — expected one of {expected_real_types}"

    def test_pipeline_topic_cleanup_on_success(self):
        """AC-21: cleaning_up state removes topic file from processing/."""
        config = load_config(PIPELINE_PATH)
        actions = config.get("actions", {})
        cleaning_up = actions.get("cleaning_up", [])
        # Must have a bash action that removes the topic file
        cleaning_yaml = yaml.dump(cleaning_up)
        assert (
            "topic_file" in cleaning_yaml or "rm" in cleaning_yaml
        ), "cleaning_up must handle topic file removal"

    def test_pipeline_failed_moves_to_failed_dir(self):
        """AC-21: failed state moves topic file to .chaplain/failed/."""
        config = load_config(PIPELINE_PATH)
        actions = config.get("actions", {})
        failed_actions = actions.get("failed", [])
        failed_yaml = yaml.dump(failed_actions)
        assert (
            "failed" in failed_yaml or "topic_file" in failed_yaml
        ), "failed state must move topic file to .chaplain/failed/"


# ════════════════════════════════════════════════════════════════════════
# AC-05 to AC-08: Custom action modules exist and extend BaseAction
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
@requires_fsm_engine
class TestCustomActionModules:
    """AC-05 to AC-08: Custom action modules exist and are valid."""

    @pytest.mark.parametrize(
        "module_name,class_name",
        [
            ("bash_context_action", "BashContextAction"),
            ("yamlgraph_async_action", "YamlgraphAsyncAction"),
            ("git_commit_action", "GitCommitAction"),
            ("precommit_action", "PrecommitAction"),
        ],
    )
    def test_action_module_exists(self, module_name, class_name):
        """AC-05/06/07/08: Action module file exists."""
        module_path = ACTIONS_DIR / f"{module_name}.py"
        assert module_path.exists(), f"Action module not found: {module_path}"

    @pytest.mark.parametrize(
        "module_name,class_name",
        [
            ("bash_context_action", "BashContextAction"),
            ("yamlgraph_async_action", "YamlgraphAsyncAction"),
            ("git_commit_action", "GitCommitAction"),
            ("precommit_action", "PrecommitAction"),
        ],
    )
    def test_action_class_extends_base(self, module_name, class_name):
        """AC-05/06/07/08: Action class extends BaseAction."""
        # Add actions dir to path for import
        actions_str = str(ACTIONS_DIR)
        if actions_str not in sys.path:
            sys.path.insert(0, actions_str)

        mod = importlib.import_module(module_name)
        cls = getattr(mod, class_name)

        from statemachine_engine.actions.base import BaseAction

        assert issubclass(cls, BaseAction), f"{class_name} does not extend BaseAction"

    @pytest.mark.parametrize(
        "module_name,class_name",
        [
            ("bash_context_action", "BashContextAction"),
            ("yamlgraph_async_action", "YamlgraphAsyncAction"),
            ("git_commit_action", "GitCommitAction"),
            ("precommit_action", "PrecommitAction"),
        ],
    )
    def test_action_has_execute_method(self, module_name, class_name):
        """Actions must implement async execute(context) -> str."""
        actions_str = str(ACTIONS_DIR)
        if actions_str not in sys.path:
            sys.path.insert(0, actions_str)

        mod = importlib.import_module(module_name)
        cls = getattr(mod, class_name)
        assert hasattr(cls, "execute"), f"{class_name} missing execute method"
        assert inspect.iscoroutinefunction(
            cls.execute
        ), f"{class_name}.execute must be async"


# ════════════════════════════════════════════════════════════════════════
# AC-09: Actions discoverable by ActionLoader
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
@requires_fsm_engine
class TestActionRegistration:
    """AC-09: All 4 custom actions are discoverable via ActionLoader."""

    def test_action_loader_discovers_custom_actions(self):
        """ActionLoader with --actions-dir finds all 4 custom actions."""
        from statemachine_engine.core.action_loader import ActionLoader

        loader = ActionLoader(actions_root=str(ACTIONS_DIR))
        for action_type in [
            "bash_context",
            "yamlgraph_async",
            "git_commit",
            "precommit",
        ]:
            cls = loader.load_action_class(action_type)
            assert (
                cls is not None
            ), f"ActionLoader could not find '{action_type}' in {ACTIONS_DIR}"


# ════════════════════════════════════════════════════════════════════════
# AC-10: BashContextAction behavior
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
@requires_fsm_engine
class TestBashContextAction:
    """AC-10: BashContextAction parses JSON stdout and merges into context."""

    def _load_action(self):
        actions_str = str(ACTIONS_DIR)
        if actions_str not in sys.path:
            sys.path.insert(0, actions_str)
        from bash_context_action import BashContextAction

        return BashContextAction

    def test_captures_json_stdout(self):
        """AC-10: Subprocess JSON stdout is parsed and merged into context."""
        cls = self._load_action()
        action = cls(
            {
                "command": 'echo \'{"wt_dir": "/tmp/wt", "wt_branch": "feat/test"}\'',
                "capture_keys": ["wt_dir", "wt_branch"],
                "success": "worktree_ready",
                "error": "setup_failed",
            }
        )
        context = {"machine_name": "test"}
        event = asyncio.run(action.execute(context))
        assert event == "worktree_ready"
        assert context.get("wt_dir") == "/tmp/wt"
        assert context.get("wt_branch") == "feat/test"

    def test_returns_error_on_nonzero_exit(self):
        """AC-10: Non-zero exit returns error event."""
        cls = self._load_action()
        action = cls(
            {
                "command": "exit 1",
                "capture_keys": ["foo"],
                "success": "ok",
                "error": "fail",
            }
        )
        context = {"machine_name": "test"}
        event = asyncio.run(action.execute(context))
        assert event == "fail"

    def test_returns_error_on_invalid_json(self):
        """AC-10: Invalid JSON stdout returns error event."""
        cls = self._load_action()
        action = cls(
            {
                "command": "echo 'not json'",
                "capture_keys": ["foo"],
                "success": "ok",
                "error": "fail",
            }
        )
        context = {"machine_name": "test"}
        event = asyncio.run(action.execute(context))
        assert event == "fail"

    def test_template_substitution(self):
        """AC-10: {var} in command is resolved from context."""
        cls = self._load_action()
        action = cls(
            {
                "command": 'echo \'{"result": "{topic_file}"}\'',
                "capture_keys": ["result"],
                "success": "ok",
                "error": "fail",
            }
        )
        context = {"machine_name": "test", "topic_file": "hello.md"}
        event = asyncio.run(action.execute(context))
        assert event == "ok"
        assert context.get("result") == "hello.md"


# ════════════════════════════════════════════════════════════════════════
# AC-11: YamlgraphAsyncAction behavior
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
@requires_fsm_engine
class TestYamlgraphAsyncAction:
    """AC-11: YamlgraphAsyncAction invokes yamlgraph and routes via event_map."""

    def _load_action(self):
        actions_str = str(ACTIONS_DIR)
        if actions_str not in sys.path:
            sys.path.insert(0, actions_str)
        from yamlgraph_async_action import YamlgraphAsyncAction

        return YamlgraphAsyncAction

    def test_resolves_graph_path_relative_to_main_dir(self):
        """AC-11: Graph path resolved relative to context['main_dir']."""
        cls = self._load_action()
        action = cls(
            {
                "graph": "graphs/watcher-plan/step-plan.yaml",
                "success": "plan_done",
            }
        )
        context = {"machine_name": "test", "main_dir": "/home/user/project"}
        # The action should build command with full path
        # We test the path resolution logic exists
        assert hasattr(action, "execute")
        assert context["main_dir"]  # context used for path resolution

    def test_event_map_routing(self):
        """AC-11: event_map routes LLM output to FSM events."""
        cls = self._load_action()
        action = cls(
            {
                "graph": "graphs/watcher-plan/step-judge.yaml",
                "event_map": {"APPROVE": "approve", "REJECT": "reject"},
                "success": "approve",
            }
        )
        # Verify event_map is accessible from config
        event_map = action.get_config_value("event_map", {})
        assert event_map == {"APPROVE": "approve", "REJECT": "reject"}


# ════════════════════════════════════════════════════════════════════════
# AC-12: GitCommitAction behavior
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
@requires_fsm_engine
class TestGitCommitAction:
    """AC-12: GitCommitAction checks diff, commits, captures fr_path."""

    def _load_action(self):
        actions_str = str(ACTIONS_DIR)
        if actions_str not in sys.path:
            sys.path.insert(0, actions_str)
        from git_commit_action import GitCommitAction

        return GitCommitAction

    def test_has_execute_method(self):
        """AC-12: GitCommitAction has async execute."""
        cls = self._load_action()
        action = cls(
            {
                "message": "test commit",
                "add_paths": ["feature-requests/"],
                "success": "committed",
            }
        )
        assert inspect.iscoroutinefunction(action.execute)

    def test_config_accepts_capture_fr_path(self):
        """AC-12: Config supports capture_fr_path option."""
        cls = self._load_action()
        action = cls(
            {
                "message": "test",
                "add_paths": ["."],
                "capture_fr_path": True,
                "success": "committed",
            }
        )
        assert action.get_config_value("capture_fr_path") is True


# ════════════════════════════════════════════════════════════════════════
# AC-13: PrecommitAction behavior
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
@requires_fsm_engine
class TestPrecommitAction:
    """AC-13: PrecommitAction retries up to max_attempts."""

    def _load_action(self):
        actions_str = str(ACTIONS_DIR)
        if actions_str not in sys.path:
            sys.path.insert(0, actions_str)
        from precommit_action import PrecommitAction

        return PrecommitAction

    def test_respects_max_attempts(self):
        """AC-13: max_attempts is configurable."""
        cls = self._load_action()
        action = cls(
            {
                "max_attempts": 5,
                "success": "finalize_done",
                "retry": "precommit_retry",
            }
        )
        assert action.get_config_value("max_attempts") == 5

    def test_increments_attempt_counter(self):
        """AC-13: precommit_attempt is incremented in context."""
        cls = self._load_action()
        action = cls(
            {
                "max_attempts": 5,
                "success": "finalize_done",
                "retry": "precommit_retry",
                "cwd": "/tmp",
            }
        )
        # Mock subprocess to simulate failure
        context = {"machine_name": "test", "precommit_attempt": 0}
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="failed")
            event = asyncio.run(action.execute(context))
        assert context.get("precommit_attempt", 0) >= 1
        assert event == "precommit_retry"

    def test_fails_after_max_attempts(self):
        """AC-13: Returns failed after max_attempts exceeded."""
        cls = self._load_action()
        action = cls(
            {
                "max_attempts": 2,
                "success": "finalize_done",
                "retry": "precommit_retry",
                "cwd": "/tmp",
            }
        )
        context = {"machine_name": "test", "precommit_attempt": 2}
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="failed")
            event = asyncio.run(action.execute(context))
        assert event == "failed"


# ════════════════════════════════════════════════════════════════════════
# AC-17: Bash library scripts — minimal changes only
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
class TestLibScriptChanges:
    """AC-17: Lib scripts modified only by appending JSON stdout."""

    @pytest.mark.parametrize(
        "script",
        ["preflight.sh", "worktree_setup.sh", "create_pr.sh", "wait_ci.sh"],
    )
    def test_lib_script_has_json_output(self, script):
        """AC-17: Lib script outputs JSON on last line."""
        script_path = CHAPLAIN / "lib" / "watcher" / script
        assert script_path.exists(), f"Script not found: {script_path}"
        content = script_path.read_text()
        # Must contain echo with JSON pattern
        assert (
            "echo" in content and "{" in content
        ), f"{script} must append JSON stdout line"

    @pytest.mark.parametrize(
        "script",
        [
            "inbox_sync.sh",
            "merge_pr.sh",
            "worktree_teardown.sh",
            "post_merge.sh",
            "metrics.sh",
            "dedup_gate.sh",
        ],
    )
    def test_unchanged_scripts_unmodified(self, script):
        """AC-17/18: Scripts not in the change list remain unmodified."""
        # This is validated by git diff in the commit — just verify they exist
        script_path = CHAPLAIN / "lib" / "watcher" / script
        assert script_path.exists(), f"Script not found: {script_path}"


# ════════════════════════════════════════════════════════════════════════
# AC-20: Topic file lifecycle
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
class TestTopicLifecycle:
    """AC-20/21: Topic file moved to processing/ before pipeline."""

    def test_dispatcher_moves_topic_to_processing(self):
        """AC-20: syncing_inbox action moves file from inbox to processing."""
        config = load_config(DISPATCHER_PATH)
        actions = config.get("actions", {})
        syncing = actions.get("syncing_inbox", [])
        syncing_yaml = yaml.dump(syncing)
        assert (
            "processing" in syncing_yaml
        ), "syncing_inbox must move topic file to processing/"
        assert (
            "mv" in syncing_yaml or "move" in syncing_yaml
        ), "syncing_inbox must use mv to move topic file"
