"""Acceptance tests for FR-390 watcher validate_fix context + sanity timeout."""

import asyncio
import importlib.util
import sys
import types
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.process

WORKTREE = Path(__file__).resolve().parents[2]
CHAPLAIN = WORKTREE / ".chaplain"
ACTION_PATH = CHAPLAIN / "actions" / "yamlgraph_async_action.py"
PIPELINE_V2 = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml"
SANITY_GRAPH = CHAPLAIN / "graphs" / "watcher-enforce" / "sanity-check-session.yaml"


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


def _load_yaml(path: Path) -> dict:
    assert path.exists(), f"Missing YAML file: {path}"
    with path.open() as f:
        return yaml.safe_load(f)


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


def _patch_subprocess_capture(monkeypatch):
    captured: dict[str, tuple[str, ...]] = {}

    async def fake_create_subprocess_exec(*argv, **_kwargs):
        captured["argv"] = argv
        return _FakeProcess(returncode=0)

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    return captured


def _extract_var_pairs(argv: tuple[str, ...]) -> dict[str, str]:
    tokens = list(argv)
    pairs: dict[str, str] = {}
    for i, fragment in enumerate(tokens[:-1]):
        if fragment == "--var":
            key, value = tokens[i + 1].split("=", 1)
            pairs[key] = value
    return pairs


def _transition_exists(
    transitions: list[dict], from_state: str, to_state: str, event: str
) -> bool:
    return any(
        t.get("from") == from_state
        and t.get("to") == to_state
        and t.get("event") == event
        for t in transitions
    )


@pytest.mark.req("REQ-YG-318")
class TestFR390WatcherValidateFixContextAndSanityTimeout:
    """AC-01..AC-05 contracts for post-enforce context normalization + timeout budget."""

    def test_ac01_first_validate_fix_pass_omits_literal_placeholder_payloads(
        self, monkeypatch
    ):
        action_cls = _load_yamlgraph_action(monkeypatch)
        action = action_cls(
            {
                "graph": ".chaplain/graphs/watcher-enforce/validate-session.yaml",
                "vars": {
                    "precommit_output": "{precommit_output}",
                    "validate_gate_output": "{validate_gate_output}",
                },
                "success": "validate_done",
                "error": "error",
            }
        )
        captured = _patch_subprocess_capture(monkeypatch)

        event = asyncio.run(action.execute({"main_dir": "/repo", "wt_dir": "tmp/wt"}))

        assert event == "validate_done"
        pairs = _extract_var_pairs(captured["argv"])
        assert pairs["precommit_output"] == ""
        assert pairs["validate_gate_output"] == ""

    def test_ac02_retry_validate_fix_pass_forwards_real_gate_diagnostics(
        self, monkeypatch
    ):
        action_cls = _load_yamlgraph_action(monkeypatch)
        action = action_cls(
            {
                "graph": ".chaplain/graphs/watcher-enforce/validate-session.yaml",
                "vars": {
                    "precommit_output": "{precommit_output}",
                    "validate_gate_output": "{validate_gate_output}",
                },
                "success": "validate_done",
                "error": "error",
            }
        )
        captured = _patch_subprocess_capture(monkeypatch)

        precommit_output = "ruff failed: E501"
        validate_gate_output = '{"checks":[{"name":"diary_parity","passed":false}]}'
        event = asyncio.run(
            action.execute(
                {
                    "main_dir": "/repo",
                    "wt_dir": "tmp/wt",
                    "precommit_output": precommit_output,
                    "validate_gate_output": validate_gate_output,
                }
            )
        )

        assert event == "validate_done"
        pairs = _extract_var_pairs(captured["argv"])
        assert pairs["precommit_output"] == precommit_output
        assert pairs["validate_gate_output"] == validate_gate_output

    def test_ac03_pipeline_sanity_check_timeout_is_at_least_1200(self):
        pipeline = _load_yaml(PIPELINE_V2)
        action = pipeline["actions"]["sanity_check"][0]
        assert int(action["timeout"]) >= 1200

    def test_ac04_sanity_graph_node_timeout_is_at_least_1200(self):
        graph = _load_yaml(SANITY_GRAPH)
        node = graph["nodes"]["sanity_check"]
        assert int(node["timeout"]) >= 1200

    def test_ac05_sanity_pass_warn_routing_to_validate_gate_preserved(self):
        pipeline = _load_yaml(PIPELINE_V2)
        transitions = pipeline.get("transitions", [])
        assert _transition_exists(transitions, "sanity_check", "validate_gate", "pass")
        assert _transition_exists(transitions, "sanity_check", "validate_gate", "warn")
