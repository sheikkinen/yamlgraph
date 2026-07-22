"""RED acceptance tests for FR-319 yamlgraph_async shell-safe vars."""

import asyncio
import importlib.util
import sys
import types
from pathlib import Path

import pytest

pytestmark = [pytest.mark.process, pytest.mark.slow]

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

    def __init__(
        self, returncode: int = 0, stdout: str = "VALIDATE_DONE", stderr: str = ""
    ):
        self.returncode = returncode
        self._stdout = stdout.encode()
        self._stderr = stderr.encode()

    async def communicate(self):
        return self._stdout, self._stderr


def _load_yamlgraph_action(monkeypatch):
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


def _build_action(monkeypatch, *, vars_override: dict[str, str] | None = None):
    action_cls = _load_yamlgraph_action(monkeypatch)
    action_config = {
        "graph": ".chaplain/graphs/watcher-enforce/validate-session.yaml",
        "vars": {
            "precommit_output": "{precommit_output}",
            "topic_file": "{topic_file}",
        },
        "success": "validate_done",
        "error": "error",
        "timeout": 30,
    }
    if vars_override is not None:
        action_config["vars"] = vars_override
    return action_cls(action_config)


def _patch_subprocess_capture(monkeypatch):
    captured: dict[str, tuple[str, ...]] = {}

    async def fake_create_subprocess_exec(*argv, **_kwargs):
        captured["argv"] = argv
        return _FakeProcess(returncode=0)

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    return captured


def _extract_var_pairs(argv: tuple[str, ...]) -> list[str]:
    tokens = list(argv)
    return [
        tokens[i + 1]
        for i, arg_fragment in enumerate(tokens[:-1])
        if arg_fragment == "--var"
    ]


@pytest.mark.req("REQ-YG-027")
class TestFR319WatcherYamlgraphAsyncShellSafeVars:
    """AC-01..AC-04 contracts for shell-safe --var encoding."""

    def test_ac01_precommit_output_with_inner_quotes_is_single_var_token(
        self, monkeypatch
    ):
        action = _build_action(monkeypatch)
        captured = _patch_subprocess_capture(monkeypatch)

        precommit_output = 'pytestmark = pytest.mark.skip(reason="FR-316 obsolete")'
        event = asyncio.run(
            action.execute(
                {
                    "main_dir": "/repo",
                    "wt_dir": "tmp/worktrees/feat/watcher2-gh-304",
                    "topic_file": ".chaplain/processing/gh-304.md",
                    "precommit_output": precommit_output,
                    "machine_name": "watcher2",
                }
            )
        )

        assert event == "validate_done"
        pairs = _extract_var_pairs(captured["argv"])
        pair = next(p for p in pairs if p.startswith("precommit_output="))
        assert pair == f"precommit_output={precommit_output}"

    def test_ac02_shell_metacharacters_pass_as_literal_argv(self, monkeypatch):
        action = _build_action(monkeypatch)
        captured = _patch_subprocess_capture(monkeypatch)

        precommit_output = '$(uname) && echo "$HOME" `id` ; (x)'
        asyncio.run(
            action.execute(
                {
                    "main_dir": "/repo",
                    "wt_dir": "tmp/worktrees/feat/watcher2-gh-304",
                    "topic_file": ".chaplain/processing/gh-304.md",
                    "precommit_output": precommit_output,
                    "machine_name": "watcher2",
                }
            )
        )

        pairs = _extract_var_pairs(captured["argv"])
        pair = next(p for p in pairs if p.startswith("precommit_output="))
        assert pair == f"precommit_output={precommit_output}"

    def test_ac04_context_placeholders_resolve_before_var_encoding(self, monkeypatch):
        action = _build_action(
            monkeypatch,
            vars_override={
                "precommit_output": "PREFIX:{precommit_output}:SUFFIX",
            },
        )
        captured = _patch_subprocess_capture(monkeypatch)

        source_value = 'line("A")'
        asyncio.run(
            action.execute(
                {
                    "main_dir": "/repo",
                    "wt_dir": "tmp/worktrees/feat/watcher2-gh-304",
                    "precommit_output": source_value,
                    "machine_name": "watcher2",
                }
            )
        )

        pairs = _extract_var_pairs(captured["argv"])
        pair = next(p for p in pairs if p.startswith("precommit_output="))
        assert pair == f"precommit_output=PREFIX:{source_value}:SUFFIX"
