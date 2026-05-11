"""RED acceptance tests for FR-369 FSM snapshot contract + hook wiring."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


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


def _dataclass_fields(path: Path, class_name: str) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                item.target.id
                for item in node.body
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
            }
    return set()


@pytest.mark.req("REQ-YG-347")
class TestFR369SnapshotHooksRed:
    def test_ac01_registry_entries_for_cap146_and_reqyg347_exist(self) -> None:
        """AC-01: capability/requirement registry includes FR-369 contract."""
        cap_files = sorted((ROOT / "capabilities").glob("CAP-146-*.yaml"))
        assert cap_files, "Expected CAP-146 capability file to exist"

        architecture = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
        assert "REQ-YG-347" in architecture

    def test_ac02_snapshot_dataclass_contract_exists(self) -> None:
        """AC-02: snapshot module defines SnapshotParams contract fields."""
        snapshot_path = ROOT / "yamlgraph" / "utils" / "fsm" / "snapshot.py"
        assert (
            snapshot_path.exists()
        ), "Expected yamlgraph/utils/fsm/snapshot.py to exist"

        fields = _dataclass_fields(snapshot_path, "SnapshotParams")
        assert {
            "graph_path",
            "initial_state",
            "input_key",
            "output_key",
            "event_key",
            "event_map",
            "success_event",
            "failure_event",
            "thread_id",
            "phase",
            "payload_keys",
        }.issubset(fields)

    def test_ac03_snapshot_params_requires_graph(self) -> None:
        """AC-03: snapshot_params raises ValueError when graph is missing."""
        snapshot_path = ROOT / "yamlgraph" / "utils" / "fsm" / "snapshot.py"
        assert snapshot_path.exists(), "Expected snapshot module to exist"

        spec = importlib.util.spec_from_file_location("fr369_snapshot", snapshot_path)
        assert spec is not None and spec.loader is not None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with pytest.raises(ValueError):
            module.snapshot_params({}, {})

    def test_ac04_snapshot_params_maps_fields_and_defaults(self) -> None:
        """AC-04: snapshot_params maps fields and applies documented defaults."""
        snapshot_path = ROOT / "yamlgraph" / "utils" / "fsm" / "snapshot.py"
        assert snapshot_path.exists(), "Expected snapshot module to exist"

        spec = importlib.util.spec_from_file_location("fr369_snapshot", snapshot_path)
        assert spec is not None and spec.loader is not None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        params = {
            "graph": "graphs/test.yaml",
            "input_key": "user_input",
            "input_value": "{utterance}",
            "variables": {"session_id": "{sid}"},
            "success": "ok",
            "failure": "error",
        }
        context = {"utterance": "hello", "sid": "s-1"}

        snap = module.snapshot_params(params, context)
        assert snap.success_event == "ok"
        assert snap.failure_event == "error"
        assert snap.initial_state["user_input"] == "hello"
        assert snap.initial_state["session_id"] == "s-1"
        assert snap.phase == "graph"
        assert snap.payload_keys is None

    def test_ac05_action_exposes_required_hook_methods(self) -> None:
        """AC-05: action class defines lifecycle hook extension methods."""
        action_path = ROOT / "yamlgraph" / "utils" / "fsm" / "action.py"
        methods = _class_method_names(action_path, "YamlgraphAsyncAction")
        assert {"pre_snapshot", "on_success", "on_error", "pre_dispatch"}.issubset(
            methods
        )

    def test_ac06_action_wires_snapshot_and_hook_callbacks_to_dispatch(self) -> None:
        """AC-06: execute wires snapshot + callbacks into run_and_dispatch."""
        action_source = (ROOT / "yamlgraph" / "utils" / "fsm" / "action.py").read_text(
            encoding="utf-8"
        )
        assert "self.pre_snapshot(" in action_source
        assert "snapshot=" in action_source
        assert "pre_dispatch_fn=self.pre_dispatch" in action_source
        assert "on_success_fn=self.on_success" in action_source
        assert "on_error_fn=self.on_error" in action_source

    def test_ac07_graph_runner_supports_pre_dispatch_suppression(self) -> None:
        """AC-07: runner supports pre_dispatch hook and dispatch suppression."""
        graph_runner_source = (
            ROOT / "yamlgraph" / "utils" / "fsm" / "graph_runner.py"
        ).read_text(encoding="utf-8")
        assert "pre_dispatch_fn" in graph_runner_source
        assert "if should_dispatch" in graph_runner_source

    def test_ac08_graph_runner_calls_success_and_error_hooks(self) -> None:
        """AC-08: runner invokes success/error callbacks with elapsed metadata."""
        graph_runner_source = (
            ROOT / "yamlgraph" / "utils" / "fsm" / "graph_runner.py"
        ).read_text(encoding="utf-8")
        assert "on_success_fn(" in graph_runner_source
        assert "on_error_fn(" in graph_runner_source
        assert "elapsed_ms" in graph_runner_source

    def test_ac09_public_api_exports_snapshot_symbols(self) -> None:
        """AC-09: public fsm package exports snapshot symbols."""
        init_path = ROOT / "yamlgraph" / "utils" / "fsm" / "__init__.py"
        source = init_path.read_text(encoding="utf-8")
        assert "SnapshotParams" in source
        assert "snapshot_params" in source
