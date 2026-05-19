"""RED acceptance tests for FR-413 Chaplain shared FSM bridge migration."""

from __future__ import annotations

import ast
import asyncio
import importlib.util
import sys
import types
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
ACTION_PATH = ROOT / ".chaplain" / "actions" / "yamlgraph_async_action.py"


class _StubBaseAction:
    """Minimal BaseAction stub for loading action modules in isolation."""

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    def get_config_value(self, key: str, default: Any = None):
        return self.config.get(key, default)

    def get_machine_name(self, context: dict[str, Any]) -> str:
        return context.get("machine_name", "watcher-pipeline-v2")


class _FakeProcess:
    """Async subprocess shim to prevent external command execution in RED tests."""

    def __init__(self, returncode: int = 0, stdout: str = "APPROVE", stderr: str = ""):
        self.returncode = returncode
        self._stdout = stdout.encode()
        self._stderr = stderr.encode()

    async def communicate(self):
        return self._stdout, self._stderr


def _load_chaplain_action(monkeypatch: pytest.MonkeyPatch):
    """Import Chaplain action module with a stubbed statemachine dependency."""
    sm_pkg = types.ModuleType("statemachine_engine")
    sm_actions_pkg = types.ModuleType("statemachine_engine.actions")
    sm_base_mod = types.ModuleType("statemachine_engine.actions.base")
    sm_base_mod.BaseAction = _StubBaseAction

    monkeypatch.setitem(sys.modules, "statemachine_engine", sm_pkg)
    monkeypatch.setitem(sys.modules, "statemachine_engine.actions", sm_actions_pkg)
    monkeypatch.setitem(sys.modules, "statemachine_engine.actions.base", sm_base_mod)

    for name in list(sys.modules):
        if name.startswith("yamlgraph.utils.fsm"):
            sys.modules.pop(name, None)

    spec = importlib.util.spec_from_file_location(
        "chaplain_yamlgraph_action", ACTION_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module, module.YamlgraphAsyncAction


def _class_bases(tree: ast.AST, class_name: str) -> list[str]:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            bases: list[str] = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(base.attr)
            return bases
    return []


@pytest.mark.req("REQ-YG-319")
class TestFR413ChaplainYamlgraphAsyncSharedBridgeRed:
    def test_ac01_action_is_thin_subclass_of_shared_bridge(self) -> None:
        tree = ast.parse(ACTION_PATH.read_text(encoding="utf-8"))
        has_shared_import = any(
            isinstance(node, ast.ImportFrom)
            and node.module == "yamlgraph.utils.fsm"
            and any(alias.name == "YamlgraphAsyncAction" for alias in node.names)
            for node in tree.body
        )
        assert has_shared_import
        assert set(_class_bases(tree, "YamlgraphAsyncAction")) & {
            "_SharedYamlgraphAsyncAction",
            "YamlgraphAsyncAction",
        }

    def test_ac02_no_subprocess_execution_path_remains_in_chaplain_action(self) -> None:
        source = ACTION_PATH.read_text(encoding="utf-8")
        assert "create_subprocess_exec" not in source
        assert "create_subprocess_shell" not in source
        assert "yamlgraph graph run" not in source

    def test_ac03_legacy_top_level_config_translates_to_shared_params(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, action_cls = _load_chaplain_action(monkeypatch)
        action = action_cls(
            {
                "graph": ".chaplain/graphs/watcher-plan/step-judge-v2.yaml",
                "vars": {"topic_file": "{topic_file}", "fr_path": "{fr_path}"},
                "event_map": {
                    "CONTINUE": "revise",
                    "DONE": "approve",
                    "APPROVE": "approve",
                },
                "success": "plan_done",
                "error": "error",
            }
        )

        params = action.config.get("params")
        assert isinstance(params, dict)
        assert params.get("graph") == ".chaplain/graphs/watcher-plan/step-judge-v2.yaml"
        assert params.get("variables", {}).get("topic_file") == "{topic_file}"
        assert params.get("variables", {}).get("fr_path") == "{fr_path}"
        assert params.get("success") == "plan_done"
        assert params.get("failure") == "error"
        assert params.get("event_map", {}).get("continue") == "revise"
        assert params.get("event_map", {}).get("done") == "approve"
        assert params.get("event_map", {}).get("approve") == "approve"

    @pytest.mark.asyncio
    async def test_ac04_execute_uses_shared_dispatch_contract_and_preserves_legacy_runtime_rules(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        module, action_cls = _load_chaplain_action(monkeypatch)

        async def fake_create_subprocess_exec(*_argv: str, **_kwargs: Any):
            return _FakeProcess(returncode=0)

        monkeypatch.setattr(
            asyncio,
            "create_subprocess_exec",
            fake_create_subprocess_exec,
            raising=False,
        )

        import yamlgraph.utils.fsm.action as shared_action_module

        captured: dict[str, Any] = {}

        async def fake_run_and_dispatch(**kwargs: Any) -> None:
            captured.update(kwargs)

        created: list[Any] = []

        def fake_create_task(coro: Any):
            task = asyncio.get_running_loop().create_task(coro)
            created.append(task)
            return task

        monkeypatch.setattr(
            shared_action_module,
            "run_and_dispatch",
            fake_run_and_dispatch,
            raising=False,
        )
        monkeypatch.setattr(
            shared_action_module.asyncio,
            "create_task",
            fake_create_task,
            raising=False,
        )
        monkeypatch.setattr(
            module.asyncio,
            "create_task",
            fake_create_task,
            raising=False,
        )

        action = action_cls(
            {
                "graph": ".chaplain/graphs/watcher-plan/step-judge-v2.yaml",
                "vars": {
                    "topic_file": "{topic_file}",
                    "fr_path": "{fr_path}",
                    "precommit_output": "{precommit_output}",
                    "validate_gate_output": "{validate_gate_output}",
                },
                "event_map": {
                    "CONTINUE": "revise",
                    "DONE": "approve",
                    "APPROVE": "approve",
                },
                "success": "plan_done",
                "error": "error",
            }
        )

        result = await action.execute(
            {
                "current_state": "judge",
                "machine_name": "watcher-pipeline-v2",
                "main_dir": "/repo",
                "topic_file": ".chaplain/processing/gh-415.md",
                "fr_path": "feature-requests/FR-413-chaplain-yamlgraph-async-shared-bridge.md",
            }
        )
        await asyncio.sleep(0)

        assert result is None
        assert created, "Expected fire-and-forget task scheduling via shared action"
        assert (
            captured.get("graph_path")
            == "/repo/.chaplain/graphs/watcher-plan/step-judge-v2.yaml"
        )
        assert captured.get("success_event") == "plan_done"
        assert captured.get("failure_event") == "error"
        assert captured.get("event_map", {}).get("continue") == "revise"
        assert captured.get("event_map", {}).get("done") == "approve"

        initial_state = captured.get("initial_state", {})
        assert initial_state.get("topic_file") == ".chaplain/processing/gh-415.md"
        assert (
            initial_state.get("fr_path")
            == "feature-requests/FR-413-chaplain-yamlgraph-async-shared-bridge.md"
        )
        assert initial_state.get("precommit_output") == ""
        assert initial_state.get("validate_gate_output") == ""
