"""RED acceptance tests for FR-392 on_launch hook in shared FSM action."""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import yamlgraph.utils.fsm.action as action_module
from yamlgraph.utils.fsm.action import YamlgraphAsyncAction
from yamlgraph.utils.fsm.snapshot import SnapshotParams

ROOT = Path(__file__).resolve().parents[2]
ACTION_PATH = ROOT / "yamlgraph" / "utils" / "fsm" / "action.py"


def _class_method_names(path: Path, class_name: str) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                item.name
                for item in node.body
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef)
            }
    return set()


@pytest.mark.req("REQ-YG-347")
class TestFR392OnLaunchHookRed:
    def test_ac01_action_exposes_on_launch_hook_method(self) -> None:
        methods = _class_method_names(ACTION_PATH, "YamlgraphAsyncAction")
        assert "on_launch" in methods

    def test_ac02_execute_calls_on_launch_between_snapshot_and_create_task(
        self,
    ) -> None:
        source = ACTION_PATH.read_text(encoding="utf-8")
        snapshot_pos = source.find("snapshot = snapshot_params(")
        launch_hook_pos = source.find("self.on_launch(")
        create_task_pos = source.find("asyncio.create_task(")

        assert snapshot_pos != -1, "Expected snapshot materialization in execute()"
        assert launch_hook_pos != -1, "Expected execute() to call self.on_launch(...)"
        assert (
            create_task_pos != -1
        ), "Expected execute() to schedule run_and_dispatch task"
        assert snapshot_pos < launch_hook_pos < create_task_pos

    @pytest.mark.asyncio
    async def test_ac03_subclass_receives_resolved_snapshot_in_on_launch(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class ProbeAction(YamlgraphAsyncAction):
            def on_launch(
                self, snap: SnapshotParams, context: dict[str, Any]
            ) -> None:  # pragma: no cover - RED path until feature exists
                self.launch_calls.append((snap, dict(context)))

        action = ProbeAction.__new__(ProbeAction)
        action.config = {"params": {"graph": "graphs/demo.yaml", "failure": "failed"}}
        action.launch_calls = []

        snapshot = SnapshotParams(
            graph_path="graphs/demo.yaml",
            initial_state={"input": "hello"},
            input_key="input",
            output_key="result",
            event_key="result",
            event_map={},
            success_event="completed",
            failure_event="failed",
            thread_id=None,
            phase="graph",
            payload_keys=None,
        )

        def fake_snapshot_params(
            _params: dict[str, Any],
            _context: dict[str, Any],
            *,
            project_root: str | Path | None = None,
        ) -> SnapshotParams:
            assert project_root is None
            return snapshot

        async def fake_run_and_dispatch(**_kwargs: Any) -> None:
            return None

        created: list[Any] = []

        def fake_create_task(coro: Any) -> SimpleNamespace:
            created.append(coro)
            coro.close()
            return SimpleNamespace()

        monkeypatch.setattr(action_module, "snapshot_params", fake_snapshot_params)
        monkeypatch.setattr(action_module, "run_and_dispatch", fake_run_and_dispatch)
        monkeypatch.setattr(action_module.asyncio, "create_task", fake_create_task)

        context: dict[str, Any] = {"current_state": "judge", "machine_name": "watcher"}
        await action.execute(context)

        assert len(created) == 1
        assert action.launch_calls == [
            (snapshot, {"current_state": "judge", "machine_name": "watcher"})
        ]

    @pytest.mark.asyncio
    async def test_ac04_on_launch_not_called_when_snapshot_params_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class ProbeAction(YamlgraphAsyncAction):
            def on_launch(
                self, _snap: SnapshotParams, _context: dict[str, Any]
            ) -> None:  # pragma: no cover - RED path until feature exists
                self.launch_called = True

        action = ProbeAction.__new__(ProbeAction)
        action.config = {"params": {"failure": "launch_failed"}}
        action.launch_called = False

        def fake_snapshot_params(
            _params: dict[str, Any],
            _context: dict[str, Any],
            *,
            project_root: str | Path | None = None,
        ) -> SnapshotParams:
            raise ValueError("yamlgraph_async: no graph specified in params")

        monkeypatch.setattr(action_module, "snapshot_params", fake_snapshot_params)

        result = await action.execute({"current_state": "judge"})
        assert result == "launch_failed"
        assert action.launch_called is False
