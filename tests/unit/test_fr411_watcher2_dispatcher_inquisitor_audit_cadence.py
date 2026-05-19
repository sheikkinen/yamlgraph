"""Acceptance tests for FR-411 watcher2 inquisitor audit cadence reintegration."""

import asyncio
import importlib.util
import sys
import types
from pathlib import Path

import pytest
import yaml

WORKTREE = Path(__file__).resolve().parents[2]
CHAPLAIN = WORKTREE / ".chaplain"
DISPATCHER_CONFIG = CHAPLAIN / "config" / "watcher-dispatcher.yaml"
SYNCING_INBOX_ACTION_PATH = CHAPLAIN / "actions" / "syncing_inbox_action.py"
AUDIT_ACTION_PATH = CHAPLAIN / "actions" / "audit_action.py"


class _StubBaseAction:
    """Minimal BaseAction stub for loading chaplain action modules in tests."""

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    def get_config_value(self, key: str, default=None):
        return self.config.get(key, default)

    def get_machine_name(self, context: dict) -> str:
        return context.get("machine_name", "watcher-dispatcher")


class _FakeProcess:
    """Async subprocess shim for deterministic command simulation."""

    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self._stdout = stdout.encode()
        self._stderr = stderr.encode()

    async def communicate(self):
        return self._stdout, self._stderr


def _load_yaml(path: Path) -> dict:
    assert path.exists(), f"Missing YAML file: {path}"
    with path.open() as f:
        return yaml.safe_load(f)


def _transition_exists(
    transitions: list[dict], from_state: str, to_state: str, event: str
) -> bool:
    return any(
        t.get("from") == from_state
        and t.get("to") == to_state
        and t.get("event") == event
        for t in transitions
    )


def _load_action_module(monkeypatch, path: Path, module_name: str):
    sm_pkg = types.ModuleType("statemachine_engine")
    sm_actions_pkg = types.ModuleType("statemachine_engine.actions")
    sm_base_mod = types.ModuleType("statemachine_engine.actions.base")
    sm_base_mod.BaseAction = _StubBaseAction

    monkeypatch.setitem(sys.modules, "statemachine_engine", sm_pkg)
    monkeypatch.setitem(sys.modules, "statemachine_engine.actions", sm_actions_pkg)
    monkeypatch.setitem(sys.modules, "statemachine_engine.actions.base", sm_base_mod)

    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.mark.req("REQ-YG-407")
class TestFR411Watcher2DispatcherInquisitorAuditCadence:
    """AC-01..AC-09 contracts for audit cadence in watcher-dispatcher."""

    def test_ac01_dispatcher_declares_auditing_state_and_audit_events(self):
        config = _load_yaml(DISPATCHER_CONFIG)
        states = set(config.get("states", []))
        events = set(config.get("events", []))
        assert "auditing" in states
        assert "audit_needed" in events
        assert "audit_done" in events

    def test_ac02_dispatcher_context_includes_last_audit_ts(self):
        config = _load_yaml(DISPATCHER_CONFIG)
        assert config.get("context", {}).get("last_audit_ts") == 0

    def test_ac03_syncing_inbox_emits_audit_needed_when_cadence_elapsed(
        self, monkeypatch
    ):
        module = _load_action_module(
            monkeypatch, SYNCING_INBOX_ACTION_PATH, "chaplain_syncing_inbox_action"
        )
        action = module.SyncingInboxAction(
            {
                "success": "topic_found",
                "error": "no_topics",
                "audit_needed": "audit_needed",
            }
        )
        queue = [
            _FakeProcess(returncode=0),
            _FakeProcess(returncode=1, stderr="No topic files found"),
        ]

        async def fake_create_subprocess_exec(*_argv, **_kwargs):
            return queue.pop(0)

        monkeypatch.setattr(
            asyncio, "create_subprocess_exec", fake_create_subprocess_exec
        )
        monkeypatch.setattr(module.time, "time", lambda: 200000)

        event = asyncio.run(
            action.execute({"inbox_dir": ".chaplain/inbox", "last_audit_ts": 0})
        )
        assert event == "audit_needed"

    def test_ac04_syncing_inbox_emits_no_topics_when_cadence_not_elapsed(
        self, monkeypatch
    ):
        module = _load_action_module(
            monkeypatch, SYNCING_INBOX_ACTION_PATH, "chaplain_syncing_inbox_action"
        )
        action = module.SyncingInboxAction(
            {
                "success": "topic_found",
                "error": "no_topics",
                "audit_needed": "audit_needed",
            }
        )
        queue = [
            _FakeProcess(returncode=0),
            _FakeProcess(returncode=1, stderr="No topic files found"),
        ]

        async def fake_create_subprocess_exec(*_argv, **_kwargs):
            return queue.pop(0)

        monkeypatch.setattr(
            asyncio, "create_subprocess_exec", fake_create_subprocess_exec
        )
        monkeypatch.setattr(module.time, "time", lambda: 200000)

        event = asyncio.run(
            action.execute(
                {"inbox_dir": ".chaplain/inbox", "last_audit_ts": 200000 - 60}
            )
        )
        assert event == "no_topics"

    def test_ac05_syncing_inbox_preserves_topic_found_priority(self, monkeypatch):
        module = _load_action_module(
            monkeypatch, SYNCING_INBOX_ACTION_PATH, "chaplain_syncing_inbox_action"
        )
        action = module.SyncingInboxAction(
            {
                "success": "topic_found",
                "error": "no_topics",
                "audit_needed": "audit_needed",
                "capture_keys": ["topic_file", "project", "work_dir"],
            }
        )
        queue = [
            _FakeProcess(returncode=0),
            _FakeProcess(
                returncode=0,
                stdout='{"topic_file":".chaplain/processing/gh-411.md","project":"yamlgraph","work_dir":"."}',
            ),
        ]

        async def fake_create_subprocess_exec(*_argv, **_kwargs):
            return queue.pop(0)

        monkeypatch.setattr(
            asyncio, "create_subprocess_exec", fake_create_subprocess_exec
        )
        context = {"inbox_dir": ".chaplain/inbox", "last_audit_ts": 0}
        event = asyncio.run(action.execute(context))
        assert event == "topic_found"
        assert context["topic_file"] == ".chaplain/processing/gh-411.md"
        assert context["project"] == "yamlgraph"
        assert context["work_dir"] == "."

    def test_ac06_audit_action_invokes_inquisitor_with_propose_flag(self, monkeypatch):
        module = _load_action_module(
            monkeypatch, AUDIT_ACTION_PATH, "chaplain_audit_action"
        )
        action = module.AuditAction({"success": "audit_done", "error": "error"})
        calls: list[tuple[str, ...]] = []

        async def fake_create_subprocess_exec(*argv, **_kwargs):
            calls.append(tuple(argv))
            return _FakeProcess(returncode=0)

        monkeypatch.setattr(
            asyncio, "create_subprocess_exec", fake_create_subprocess_exec
        )
        event = asyncio.run(action.execute({}))
        assert event == "audit_done"
        assert calls[0][:3] == ("bash", ".chaplain/inquisitor.sh", "--propose")

    def test_ac07_audit_action_updates_last_audit_ts_on_success(self, monkeypatch):
        module = _load_action_module(
            monkeypatch, AUDIT_ACTION_PATH, "chaplain_audit_action"
        )
        action = module.AuditAction({"success": "audit_done", "error": "error"})

        async def fake_create_subprocess_exec(*_argv, **_kwargs):
            return _FakeProcess(returncode=0)

        monkeypatch.setattr(
            asyncio, "create_subprocess_exec", fake_create_subprocess_exec
        )
        monkeypatch.setattr(module.time, "time", lambda: 1234567890)

        context: dict[str, int] = {}
        event = asyncio.run(action.execute(context))
        assert event == "audit_done"
        assert context["last_audit_ts"] == 1234567890

    def test_ac08_audit_error_routes_back_to_idle(self, monkeypatch):
        config = _load_yaml(DISPATCHER_CONFIG)
        transitions = config.get("transitions", [])
        assert _transition_exists(transitions, "auditing", "idle", "error")

        module = _load_action_module(
            monkeypatch, AUDIT_ACTION_PATH, "chaplain_audit_action"
        )
        action = module.AuditAction({"success": "audit_done", "error": "error"})

        async def fake_create_subprocess_exec(*_argv, **_kwargs):
            return _FakeProcess(returncode=1, stderr="audit failed")

        monkeypatch.setattr(
            asyncio, "create_subprocess_exec", fake_create_subprocess_exec
        )
        event = asyncio.run(action.execute({}))
        assert event == "error"

    def test_ac09_syncing_inbox_returns_no_topics_on_shell_failure(self, monkeypatch):
        module = _load_action_module(
            monkeypatch, SYNCING_INBOX_ACTION_PATH, "chaplain_syncing_inbox_action"
        )
        action = module.SyncingInboxAction(
            {
                "success": "topic_found",
                "error": "no_topics",
                "audit_needed": "audit_needed",
            }
        )

        async def failing_create_subprocess_exec(*_argv, **_kwargs):
            raise OSError("cannot start process")

        monkeypatch.setattr(
            asyncio, "create_subprocess_exec", failing_create_subprocess_exec
        )
        event = asyncio.run(action.execute({"inbox_dir": ".chaplain/inbox"}))
        assert event == "no_topics"
