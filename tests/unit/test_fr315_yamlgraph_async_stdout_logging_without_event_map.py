"""RED acceptance tests for FR-315 yamlgraph_async stdout logging."""

import asyncio
import importlib.util
import logging
import sys
import types
from pathlib import Path

import pytest

WORKTREE = Path(__file__).resolve().parents[2]
ACTION_PATH = WORKTREE / ".chaplain" / "actions" / "yamlgraph_async_action.py"


class _StubBaseAction:
    """Minimal BaseAction stub for loading chaplain action modules in tests."""

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    def get_config_value(self, key: str, default=None):
        return self.config.get(key, default)

    def get_machine_name(self, context: dict) -> str:
        return context.get("machine_name", "watcher-pipeline-v2")


class _FakeProcess:
    """Async subprocess shim for deterministic command simulation."""

    def __init__(self, returncode: int, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self._stdout = stdout.encode()
        self._stderr = stderr.encode()

    async def communicate(self):
        return self._stdout, self._stderr


def _load_yamlgraph_action(monkeypatch):
    """Import YamlgraphAsyncAction with a stubbed BaseAction dependency."""
    sm_pkg = types.ModuleType("statemachine_engine")
    sm_actions_pkg = types.ModuleType("statemachine_engine.actions")
    sm_base_mod = types.ModuleType("statemachine_engine.actions.base")
    sm_base_mod.BaseAction = _StubBaseAction

    monkeypatch.setitem(sys.modules, "statemachine_engine", sm_pkg)
    monkeypatch.setitem(sys.modules, "statemachine_engine.actions", sm_actions_pkg)
    monkeypatch.setitem(sys.modules, "statemachine_engine.actions.base", sm_base_mod)

    spec = importlib.util.spec_from_file_location(
        "chaplain_yamlgraph_action", ACTION_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.YamlgraphAsyncAction


def _build_action(monkeypatch, **config):
    action_cls = _load_yamlgraph_action(monkeypatch)
    action_config = {
        "graph": ".chaplain/graphs/watcher-plan/step-plan-unified.yaml",
        "vars": {"topic_file": "{topic_file}"},
        "success": "plan_done",
        "error": "error",
        "timeout": 30,
    }
    action_config.update(config)
    return action_cls(action_config)


def _patch_subprocess(
    monkeypatch, *, stdout: str, stderr: str = "", returncode: int = 0
):
    async def fake_create_subprocess_exec(*_args, **_kwargs):
        return _FakeProcess(returncode=returncode, stdout=stdout, stderr=stderr)

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)


@pytest.mark.req("REQ-YG-027")
class TestFR315YamlgraphAsyncStdoutLoggingWithoutEventMap:
    """AC-01..AC-04 contracts for stdout logging and routing safety."""

    def test_ac01_logs_stdout_debug_when_event_map_not_configured(
        self, monkeypatch, caplog
    ):
        """AC-01: no event_map still logs stdout at DEBUG before success return."""
        action = _build_action(monkeypatch)
        _patch_subprocess(
            monkeypatch,
            stdout="PLAN_OUTPUT: generated feature request content",
            returncode=0,
        )
        caplog.set_level(logging.DEBUG)

        event = asyncio.run(
            action.execute(
                {
                    "main_dir": "/repo",
                    "wt_dir": "tmp/worktrees/feat/watcher2-gh-288",
                    "topic_file": ".chaplain/processing/gh-288.md",
                    "machine_name": "watcher2",
                }
            )
        )

        assert event == "plan_done"
        debug_lines = [
            rec.getMessage()
            for rec in caplog.records
            if "yamlgraph stdout:" in rec.getMessage()
        ]
        assert debug_lines, "Expected DEBUG stdout log even when event_map is omitted"
        assert any("PLAN_OUTPUT" in line for line in debug_lines)

    def test_ac02_logs_stdout_debug_when_event_map_is_empty_dict(
        self, monkeypatch, caplog
    ):
        """AC-02: explicit empty event_map still logs stdout at DEBUG."""
        action = _build_action(monkeypatch, event_map={})
        _patch_subprocess(
            monkeypatch,
            stdout="ENFORCE_OUTPUT: changes prepared",
            returncode=0,
        )
        caplog.set_level(logging.DEBUG)

        event = asyncio.run(
            action.execute(
                {
                    "main_dir": "/repo",
                    "wt_dir": "tmp/worktrees/feat/watcher2-gh-288",
                    "topic_file": ".chaplain/processing/gh-288.md",
                    "machine_name": "watcher2",
                }
            )
        )

        assert event == "plan_done"
        debug_lines = [
            rec.getMessage()
            for rec in caplog.records
            if "yamlgraph stdout:" in rec.getMessage()
        ]
        assert debug_lines, "Expected DEBUG stdout log when event_map is {}"
        assert any("ENFORCE_OUTPUT" in line for line in debug_lines)

    def test_ac03_stdout_debug_log_is_capped_to_2000_chars(self, monkeypatch, caplog):
        """AC-03: stdout debug dump is bounded to 2000 chars."""
        action = _build_action(monkeypatch)
        stdout_text = "A" * 2500
        _patch_subprocess(monkeypatch, stdout=stdout_text, returncode=0)
        caplog.set_level(logging.DEBUG)

        event = asyncio.run(
            action.execute(
                {
                    "main_dir": "/repo",
                    "wt_dir": "tmp/worktrees/feat/watcher2-gh-288",
                    "topic_file": ".chaplain/processing/gh-288.md",
                    "machine_name": "watcher2",
                }
            )
        )

        assert event == "plan_done"
        debug_lines = [
            rec.getMessage()
            for rec in caplog.records
            if "yamlgraph stdout:" in rec.getMessage()
        ]
        assert debug_lines, "Expected DEBUG stdout log for successful no-event_map run"

        payload = debug_lines[-1].split("yamlgraph stdout: ", 1)[1]
        assert (
            len(payload) == 2000
        ), "Expected stdout debug payload to be truncated at 2000 chars"

    def test_ac04_event_map_routing_behavior_is_unchanged(self, monkeypatch):
        """AC-04: event_map match still returns mapped event."""
        action = _build_action(
            monkeypatch, success="done", event_map={"APPROVE": "approve"}
        )
        _patch_subprocess(monkeypatch, stdout="APPROVE", returncode=0)

        event = asyncio.run(
            action.execute(
                {
                    "main_dir": "/repo",
                    "wt_dir": "tmp/worktrees/feat/watcher2-gh-288",
                    "topic_file": ".chaplain/processing/gh-288.md",
                    "machine_name": "watcher2",
                }
            )
        )

        assert event == "approve"
