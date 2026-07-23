"""RED acceptance tests for FR-311 git_commit hook-fix retry behavior."""

import asyncio
import importlib.util
import sys
import types
from pathlib import Path

import pytest

pytestmark = pytest.mark.process

WORKTREE = Path(__file__).resolve().parents[2]
ACTION_PATH = WORKTREE / ".chaplain" / "actions" / "git_commit_action.py"


class _StubBaseAction:
    """Minimal BaseAction stub for loading chaplain action modules in tests."""

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    def get_config_value(self, key: str, default=None):
        return self.config.get(key, default)

    def get_machine_name(self, _context: dict) -> str:
        return "watcher-pipeline-v2"


class _FakeProcess:
    """Async subprocess shim for deterministic command simulation."""

    def __init__(self, returncode: int, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self._stdout = stdout.encode()
        self._stderr = stderr.encode()

    async def communicate(self):
        return self._stdout, self._stderr


def _load_git_commit_action(monkeypatch):
    """Import GitCommitAction from .chaplain/actions with stubbed BaseAction."""
    sm_pkg = types.ModuleType("statemachine_engine")
    sm_actions_pkg = types.ModuleType("statemachine_engine.actions")
    sm_base_mod = types.ModuleType("statemachine_engine.actions.base")
    sm_base_mod.BaseAction = _StubBaseAction

    monkeypatch.setitem(sys.modules, "statemachine_engine", sm_pkg)
    monkeypatch.setitem(sys.modules, "statemachine_engine.actions", sm_actions_pkg)
    monkeypatch.setitem(sys.modules, "statemachine_engine.actions.base", sm_base_mod)

    spec = importlib.util.spec_from_file_location(
        "chaplain_git_commit_action", ACTION_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.GitCommitAction


def _build_action(monkeypatch, **config):
    git_commit_action_cls = _load_git_commit_action(monkeypatch)
    action_config = {
        "message": "chore(watcher): plan artifacts",
        "success": "committed",
        "error": "error",
    }
    action_config.update(config)
    return git_commit_action_cls(action_config)


@pytest.mark.req("REQ-YG-027")
class TestFR311GitCommitHookRetry:
    """AC-01/AC-02/AC-04 RED contracts for hook-modification retry behavior."""

    def test_ac01_retries_and_succeeds_after_hook_modification(self, monkeypatch):
        action = _build_action(monkeypatch)
        calls: list[list[str]] = []
        commit_attempt = 0

        async def fake_create_subprocess_exec(*cmd, **_kwargs):
            nonlocal commit_attempt
            argv = list(cmd)
            calls.append(argv)

            if argv[:4] == ["git", "config", "--get", "user.name"]:
                return _FakeProcess(0, stdout="Sheikki\n")
            if argv[:4] == ["git", "config", "--get", "user.email"]:
                return _FakeProcess(0, stdout="sheikki@example.com\n")
            if argv[:2] == ["git", "add"]:
                return _FakeProcess(0)
            if argv[:4] == ["git", "diff", "--cached", "--quiet"]:
                return _FakeProcess(1)  # staged diff exists
            if argv[:2] == ["git", "commit"]:
                commit_attempt += 1
                if commit_attempt == 1:
                    return _FakeProcess(
                        1, stdout="files were modified by this hook\nFixing..."
                    )
                return _FakeProcess(0, stdout="[main abc123] commit ok\n")
            if argv[:2] == ["git", "diff"]:
                return _FakeProcess(0, stdout="feature-requests/FR-311-test.md\n")
            return _FakeProcess(0)

        monkeypatch.setattr(
            asyncio, "create_subprocess_exec", fake_create_subprocess_exec
        )

        event = asyncio.run(action.execute({"wt_dir": "."}))

        commit_calls = [c for c in calls if c[:2] == ["git", "commit"]]
        assert event == "committed"
        assert (
            len(commit_calls) == 2
        ), "Expected retry commit after hook file modifications"
        assert any(c[:3] == ["git", "add", "-u"] for c in calls), "Expected re-stage"

    def test_ac02_stops_after_three_attempts_and_reports_retries(
        self, monkeypatch, caplog
    ):
        action = _build_action(monkeypatch, max_attempts=3)
        calls: list[list[str]] = []

        async def fake_create_subprocess_exec(*cmd, **_kwargs):
            argv = list(cmd)
            calls.append(argv)

            if argv[:4] == ["git", "config", "--get", "user.name"]:
                return _FakeProcess(0, stdout="Sheikki\n")
            if argv[:4] == ["git", "config", "--get", "user.email"]:
                return _FakeProcess(0, stdout="sheikki@example.com\n")
            if argv[:2] == ["git", "add"]:
                return _FakeProcess(0)
            if argv[:4] == ["git", "diff", "--cached", "--quiet"]:
                return _FakeProcess(1)
            if argv[:2] == ["git", "commit"]:
                return _FakeProcess(
                    1, stdout="files were modified by this hook\nFixing..."
                )
            if argv[:2] == ["git", "diff"]:
                return _FakeProcess(0, stdout="yamlgraph/core.py\n")
            return _FakeProcess(0)

        monkeypatch.setattr(
            asyncio, "create_subprocess_exec", fake_create_subprocess_exec
        )
        caplog.set_level("INFO")

        event = asyncio.run(action.execute({"wt_dir": "."}))

        commit_calls = [c for c in calls if c[:2] == ["git", "commit"]]
        retry_logs = [
            rec
            for rec in caplog.records
            if (
                "retry" in rec.getMessage().lower()
                or "attempt" in rec.getMessage().lower()
            )
        ]
        assert event == "error"
        assert len(commit_calls) == 3, "Expected default retry cap of 3 attempts"
        assert (
            len(retry_logs) >= 2
        ), "Expected retry attempt logs for operator forensics"

    def test_ac04_non_hook_commit_failures_do_not_retry(self, monkeypatch):
        action = _build_action(monkeypatch, max_attempts=3)
        calls: list[list[str]] = []

        async def fake_create_subprocess_exec(*cmd, **_kwargs):
            argv = list(cmd)
            calls.append(argv)

            if argv[:4] == ["git", "config", "--get", "user.name"]:
                return _FakeProcess(0, stdout="Sheikki\n")
            if argv[:4] == ["git", "config", "--get", "user.email"]:
                return _FakeProcess(0, stdout="sheikki@example.com\n")
            if argv[:2] == ["git", "add"]:
                return _FakeProcess(0)
            if argv[:4] == ["git", "diff", "--cached", "--quiet"]:
                return _FakeProcess(1)
            if argv[:2] == ["git", "commit"]:
                return _FakeProcess(1, stderr="fatal: not a git repository")
            if argv[:2] == ["git", "diff"]:
                return _FakeProcess(0, stdout="")  # no hook-modified files
            return _FakeProcess(0)

        monkeypatch.setattr(
            asyncio, "create_subprocess_exec", fake_create_subprocess_exec
        )

        event = asyncio.run(action.execute({"wt_dir": "."}))

        commit_calls = [c for c in calls if c[:2] == ["git", "commit"]]
        assert event == "error"
        assert len(commit_calls) == 1, "Genuine failures should not trigger retry loop"
        assert not any(c[:3] == ["git", "add", "-u"] for c in calls)

    def test_ac05_missing_user_name_fails_before_commit(self, monkeypatch):
        action = _build_action(monkeypatch)
        calls: list[list[str]] = []

        async def fake_create_subprocess_exec(*cmd, **_kwargs):
            argv = list(cmd)
            calls.append(argv)

            if argv[:2] == ["git", "add"]:
                return _FakeProcess(0)
            if argv[:4] == ["git", "diff", "--cached", "--quiet"]:
                return _FakeProcess(1)
            if argv[:4] == ["git", "config", "--get", "user.name"]:
                return _FakeProcess(1)
            if argv[:4] == ["git", "config", "--get", "user.email"]:
                return _FakeProcess(0, stdout="sheikki@example.com\n")
            if argv[:2] == ["git", "commit"]:
                return _FakeProcess(0, stdout="unexpected commit\n")
            return _FakeProcess(0)

        monkeypatch.setattr(
            asyncio, "create_subprocess_exec", fake_create_subprocess_exec
        )

        event = asyncio.run(action.execute({"wt_dir": "."}))

        assert event == "error"
        assert not any(c[:2] == ["git", "commit"] for c in calls)

    def test_ac06_missing_user_email_fails_before_commit(self, monkeypatch):
        action = _build_action(monkeypatch)
        calls: list[list[str]] = []

        async def fake_create_subprocess_exec(*cmd, **_kwargs):
            argv = list(cmd)
            calls.append(argv)

            if argv[:2] == ["git", "add"]:
                return _FakeProcess(0)
            if argv[:4] == ["git", "diff", "--cached", "--quiet"]:
                return _FakeProcess(1)
            if argv[:4] == ["git", "config", "--get", "user.name"]:
                return _FakeProcess(0, stdout="Sheikki\n")
            if argv[:4] == ["git", "config", "--get", "user.email"]:
                return _FakeProcess(1)
            if argv[:2] == ["git", "commit"]:
                return _FakeProcess(0, stdout="unexpected commit\n")
            return _FakeProcess(0)

        monkeypatch.setattr(
            asyncio, "create_subprocess_exec", fake_create_subprocess_exec
        )

        event = asyncio.run(action.execute({"wt_dir": "."}))

        assert event == "error"
        assert not any(c[:2] == ["git", "commit"] for c in calls)

    def test_ac07_blocklisted_identity_fails_before_commit(self, monkeypatch):
        action = _build_action(monkeypatch)
        calls: list[list[str]] = []

        async def fake_create_subprocess_exec(*cmd, **_kwargs):
            argv = list(cmd)
            calls.append(argv)

            if argv[:2] == ["git", "add"]:
                return _FakeProcess(0)
            if argv[:4] == ["git", "diff", "--cached", "--quiet"]:
                return _FakeProcess(1)
            if argv[:4] == ["git", "config", "--get", "user.name"]:
                return _FakeProcess(0, stdout="Test\n")
            if argv[:4] == ["git", "config", "--get", "user.email"]:
                return _FakeProcess(0, stdout="test@test.com\n")
            if argv[:2] == ["git", "commit"]:
                return _FakeProcess(0, stdout="unexpected commit\n")
            return _FakeProcess(0)

        monkeypatch.setattr(
            asyncio, "create_subprocess_exec", fake_create_subprocess_exec
        )

        event = asyncio.run(action.execute({"wt_dir": "."}))

        assert event == "error"
        assert not any(c[:2] == ["git", "commit"] for c in calls)

    def test_ac08_valid_identity_sets_author_and_committer_env(self, monkeypatch):
        action = _build_action(monkeypatch)
        commit_env: dict | None = None

        async def fake_create_subprocess_exec(*cmd, **kwargs):
            nonlocal commit_env
            argv = list(cmd)

            if argv[:2] == ["git", "add"]:
                return _FakeProcess(0)
            if argv[:4] == ["git", "diff", "--cached", "--quiet"]:
                return _FakeProcess(1)
            if argv[:4] == ["git", "config", "--get", "user.name"]:
                return _FakeProcess(0, stdout="Sheikki\n")
            if argv[:4] == ["git", "config", "--get", "user.email"]:
                return _FakeProcess(0, stdout="sheikki@example.com\n")
            if argv[:2] == ["git", "commit"]:
                commit_env = kwargs.get("env")
                return _FakeProcess(0, stdout="[main abc123] commit ok\n")
            return _FakeProcess(0)

        monkeypatch.setattr(
            asyncio, "create_subprocess_exec", fake_create_subprocess_exec
        )

        event = asyncio.run(action.execute({"wt_dir": "."}))

        assert event == "committed"
        assert commit_env is not None
        assert commit_env.get("GIT_AUTHOR_NAME") == "Sheikki"
        assert commit_env.get("GIT_AUTHOR_EMAIL") == "sheikki@example.com"
        assert commit_env.get("GIT_COMMITTER_NAME") == "Sheikki"
        assert commit_env.get("GIT_COMMITTER_EMAIL") == "sheikki@example.com"
