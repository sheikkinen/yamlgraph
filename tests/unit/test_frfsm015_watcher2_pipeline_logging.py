"""FR-FSM-015: Dispatcher pipeline logging contract."""

from pathlib import Path

import pytest
import yaml

WORKTREE = Path(__file__).resolve().parents[2]
DISPATCHER_CONFIG_PATH = WORKTREE / ".chaplain" / "config" / "watcher-dispatcher.yaml"
START_SYSTEM_PATH = WORKTREE / ".chaplain" / "scripts" / "start-system.sh"


def _load_dispatcher_config() -> dict:
    with open(DISPATCHER_CONFIG_PATH) as f:
        return yaml.safe_load(f)


def _processing_topic_command() -> str:
    config = _load_dispatcher_config()
    actions = config["actions"]["processing_topic"]
    return actions[0]["command"]


@pytest.mark.req("REQ-YG-316")
class TestFRFSM015Watcher2PipelineLogging:
    """Acceptance criteria coverage for per-pipeline logs in dispatcher."""

    def test_writes_pipeline_output_to_topic_and_timestamp_named_log(self):
        command = _processing_topic_command()
        assert 'BASENAME=$(basename "$TOPIC" .md)' in command
        assert (
            'LOG="logs/fsm-pipeline-${BASENAME}-$(date +%Y%m%d-%H%M%S).log"' in command
        )
        assert '2>&1 | tee "$LOG"' in command

    def test_enables_debug_logging_for_pipeline_subprocess(self):
        command = _processing_topic_command()
        assert "--debug" in command

    def test_rotates_pipeline_logs_to_keep_last_twenty(self):
        command = _processing_topic_command()
        assert "ls -1t logs/fsm-pipeline-*.log" in command
        assert "tail -n +21" in command

    def test_pipeline_log_path_is_emitted_for_operator_visibility(self):
        command = _processing_topic_command()
        assert 'echo "Pipeline log: $LOG"' in command

    def test_dispatcher_log_contract_remains_unchanged(self):
        start_system = START_SYSTEM_PATH.read_text()
        assert "> logs/fsm-dispatcher.log 2>&1" in start_system
