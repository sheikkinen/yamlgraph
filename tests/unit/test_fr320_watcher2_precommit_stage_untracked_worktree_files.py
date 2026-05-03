"""RED acceptance tests for FR-320 precommit staging boundary."""

import asyncio
import importlib.util
import sys
import types
from pathlib import Path

import pytest

WORKTREE = Path(__file__).resolve().parents[2]
ACTION_PATH = WORKTREE / ".chaplain" / "actions" / "precommit_action.py"


class _StubBaseAction:
    """Minimal BaseAction stub for loading chaplain action modules in tests."""

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    def get_config_value(self, key: str, default=None):
        return self.config.get(key, default)

    def get_machine_name(self, _context: dict) -> str:
        return "watcher-pipeline-v2"


class _RunResult:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _load_precommit_action_module(monkeypatch):
    """Import PrecommitAction from .chaplain/actions with stubbed BaseAction."""
    sm_pkg = types.ModuleType("statemachine_engine")
    sm_actions_pkg = types.ModuleType("statemachine_engine.actions")
    sm_base_mod = types.ModuleType("statemachine_engine.actions.base")
    sm_base_mod.BaseAction = _StubBaseAction

    monkeypatch.setitem(sys.modules, "statemachine_engine", sm_pkg)
    monkeypatch.setitem(sys.modules, "statemachine_engine.actions", sm_actions_pkg)
    monkeypatch.setitem(sys.modules, "statemachine_engine.actions.base", sm_base_mod)

    spec = importlib.util.spec_from_file_location(
        "chaplain_precommit_action", ACTION_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _build_action(monkeypatch, **config):
    module = _load_precommit_action_module(monkeypatch)
    action_config = {
        "max_attempts": 5,
        "success": "pass",
        "retry": "fix_needed",
    }
    action_config.update(config)
    return module.PrecommitAction(action_config), module


@pytest.mark.req("REQ-YG-316")
class TestFR320PrecommitStageUntracked:
    def test_ac01_stages_all_changes_before_precommit_run(self, monkeypatch):
        action, module = _build_action(monkeypatch)
        calls: list[list[str]] = []

        def fake_run(cmd, **_kwargs):
            calls.append(list(cmd))
            if list(cmd)[:3] == ["pre-commit", "run", "--all-files"]:
                return _RunResult(0, stdout="ok")
            if list(cmd)[:3] == ["git", "add", "-A"]:
                return _RunResult(0)
            return _RunResult(0)

        monkeypatch.setattr(module.subprocess, "run", fake_run)
        event = asyncio.run(action.execute({"wt_dir": "."}))

        assert event == "pass"
        add_index = next(
            (idx for idx, call in enumerate(calls) if call[:3] == ["git", "add", "-A"]),
            -1,
        )
        precommit_index = next(
            (
                idx
                for idx, call in enumerate(calls)
                if call[:3] == ["pre-commit", "run", "--all-files"]
            ),
            -1,
        )
        assert add_index != -1, "Expected git add -A before pre-commit"
        assert precommit_index != -1, "Expected pre-commit command"
        assert add_index < precommit_index, "git add -A must run before pre-commit"

    def test_ac02_stage_failure_returns_error_without_running_precommit(
        self, monkeypatch
    ):
        action, module = _build_action(monkeypatch)
        calls: list[list[str]] = []

        def fake_run(cmd, **_kwargs):
            call = list(cmd)
            calls.append(call)
            if call[:3] == ["git", "add", "-A"]:
                return _RunResult(1, stderr="fatal: stage failed")
            if call[:3] == ["pre-commit", "run", "--all-files"]:
                return _RunResult(0, stdout="ok")
            return _RunResult(0)

        monkeypatch.setattr(module.subprocess, "run", fake_run)
        event = asyncio.run(action.execute({"wt_dir": "."}))

        assert event == "error", "Pre-stage failure must emit error"
        assert not any(
            call[:3] == ["pre-commit", "run", "--all-files"] for call in calls
        ), "pre-commit must not run when staging fails"

    def test_ac03_retry_restage_uses_git_add_a_not_u(self, monkeypatch):
        action, module = _build_action(monkeypatch)
        calls: list[list[str]] = []

        def fake_run(cmd, **_kwargs):
            call = list(cmd)
            calls.append(call)
            if call[:3] == ["git", "add", "-A"]:
                return _RunResult(0)
            if call[:3] == ["pre-commit", "run", "--all-files"]:
                return _RunResult(1, stdout="files were modified by this hook")
            if call[:3] == ["git", "add", "-u"]:
                return _RunResult(0)
            return _RunResult(0)

        monkeypatch.setattr(module.subprocess, "run", fake_run)
        event = asyncio.run(action.execute({"wt_dir": "."}))

        assert event == "fix_needed"
        assert any(call[:3] == ["git", "add", "-A"] for call in calls)
        assert not any(
            call[:3] == ["git", "add", "-u"] for call in calls
        ), "Retry restage should not use git add -u"

    def test_ac04_ac05_retry_and_success_contracts_preserved(self, monkeypatch):
        action, module = _build_action(monkeypatch)
        context = {"wt_dir": "."}

        def fake_run(cmd, **_kwargs):
            call = list(cmd)
            if call[:3] == ["git", "add", "-A"]:
                return _RunResult(0)
            if call[:3] == ["pre-commit", "run", "--all-files"]:
                return _RunResult(1, stdout="hook failure output")
            return _RunResult(0)

        monkeypatch.setattr(module.subprocess, "run", fake_run)
        event = asyncio.run(action.execute(context))

        assert event == "fix_needed"
        assert context["precommit_output"] == "hook failure output"
