"""FR-296: Watcher FSM System Startup Script.

Tests for .chaplain/scripts/start-system.sh — validates the script exists,
is executable, has correct structure (phases, signal handling, --inbox flag),
and uses the correct statemachine CLI invocations.
"""

import os
import stat
from pathlib import Path

import pytest

pytestmark = pytest.mark.process

WORKTREE = Path(__file__).resolve().parents[2]
SCRIPT_PATH = WORKTREE / ".chaplain" / "scripts" / "start-system.sh"


@pytest.mark.req("REQ-YG-315")
class TestStartSystemScript:
    """FR-296 acceptance tests for start-system.sh."""

    def test_script_exists(self):
        assert SCRIPT_PATH.exists(), f"Script not found: {SCRIPT_PATH}"

    def test_script_is_executable(self):
        mode = os.stat(SCRIPT_PATH).st_mode
        assert mode & stat.S_IXUSR, "Script is not executable"

    def test_has_bash_shebang(self):
        first_line = SCRIPT_PATH.read_text(encoding="utf-8").splitlines()[0]
        assert first_line.startswith("#!/"), f"Missing shebang: {first_line}"
        assert "bash" in first_line

    def test_has_set_euo_pipefail(self):
        content = SCRIPT_PATH.read_text(encoding="utf-8")
        assert "set -euo pipefail" in content

    def test_has_trap_cleanup(self):
        content = SCRIPT_PATH.read_text(encoding="utf-8")
        assert "trap cleanup INT TERM" in content

    def test_cleanup_function_exists(self):
        content = SCRIPT_PATH.read_text(encoding="utf-8")
        assert "cleanup()" in content or "cleanup ()" in content

    def test_validates_configs(self):
        content = SCRIPT_PATH.read_text(encoding="utf-8")
        assert "statemachine-validate" in content

    def test_generates_diagrams(self):
        content = SCRIPT_PATH.read_text(encoding="utf-8")
        assert "statemachine-diagrams" in content

    def test_starts_ui_before_dispatcher(self):
        content = SCRIPT_PATH.read_text(encoding="utf-8")
        ui_pos = content.find("statemachine-ui")
        dispatcher_pos = content.find(
            'statemachine "$CONFIG_DIR/watcher-dispatcher.yaml"'
        )
        assert ui_pos > 0, "statemachine-ui not found"
        assert dispatcher_pos > 0, "dispatcher start not found"
        assert ui_pos < dispatcher_pos, "UI must start before dispatcher"

    def test_waits_for_event_socket(self):
        content = SCRIPT_PATH.read_text(encoding="utf-8")
        assert "EVENT_SOCKET" in content
        assert "/tmp/statemachine-events.sock" in content

    def test_uses_initial_context(self):
        content = SCRIPT_PATH.read_text(encoding="utf-8")
        assert "--initial-context" in content
        assert "--context " not in content.replace("--initial-context", "")

    def test_inbox_flag_support(self):
        content = SCRIPT_PATH.read_text(encoding="utf-8")
        assert "--inbox" in content
        assert "INBOX_DIR" in content

    def test_writes_pid_files(self):
        content = SCRIPT_PATH.read_text(encoding="utf-8")
        assert "fsm-ui.pid" in content
        assert "fsm-dispatcher.pid" in content

    def test_keep_alive_loop(self):
        content = SCRIPT_PATH.read_text(encoding="utf-8")
        assert "while true" in content
        assert "sleep 1" in content

    def test_kills_by_pid_in_cleanup(self):
        content = SCRIPT_PATH.read_text(encoding="utf-8")
        # cleanup should kill by PID variable, not just pkill
        assert (
            'kill "$DISPATCHER_PID"' in content or 'kill "$DISPATCHER_PID"' in content
        )
        assert 'kill "$UI_PID"' in content or 'kill "$UI_PID"' in content

    def test_pkill_fallback_in_cleanup(self):
        content = SCRIPT_PATH.read_text(encoding="utf-8")
        assert 'pkill -f "statemachine .chaplain"' in content

    def test_venv_check(self):
        content = SCRIPT_PATH.read_text(encoding="utf-8")
        assert "VIRTUAL_ENV" in content
        assert ".venv/bin/activate" in content

    def test_both_configs_referenced(self):
        content = SCRIPT_PATH.read_text(encoding="utf-8")
        assert "watcher-dispatcher.yaml" in content
        assert "watcher-pipeline-v2.yaml" in content

    def test_syntax_valid(self):
        """bash -n checks syntax without executing."""
        import subprocess

        result = subprocess.run(
            ["bash", "-n", str(SCRIPT_PATH)],  # noqa: S603
            capture_output=True,
        )
        assert (
            result.returncode == 0
        ), f"Script has syntax errors: {result.stderr.decode()}"
