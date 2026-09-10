"""FR-1028 witnesses — ``graph run --provider/--model`` override of root graph
defaults (REQ-YG-671).

Frozen precedence (judgement C-3): explicit node field → overridden root
default → existing provider resolution; provider and model resolve
independently. Root graph only (AC-06); parsed YAML never mutated (AC-02).
Wrapper: RESEARCH_PROVIDER/RESEARCH_MODEL are a required pair, forwarded in
stable order, and the wrapper stamps exactly one ``- provider/model:`` line
before artifact verification (AC-08, AC-09).
"""

from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

pytestmark = pytest.mark.process  # exercises scripts/ (FR-756)

REPO_ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT_PY = REPO_ROOT / "scripts" / "research_preflight.py"
RESEARCH_SH = REPO_ROOT / "scripts" / "research.sh"
TOOLS_PY = (
    REPO_ROOT / "examples" / "demos" / "research-route" / "nodes" / "research_tools.py"
)
CLEAN_BRIEF = REPO_ROOT / "tests" / "fixtures" / "fr890" / "clean-brief.md"
PROVENANCE = "- provider/model:"

ROOT_GRAPH = """
version: "1.0"
name: fr1028-root
defaults:
  provider: anthropic
  model: claude-haiku-4-5
state:
  input: str
  answer: str
  agent_out: str
nodes:
  answer:
    type: llm
    prompt: p
    state_key: answer
  pinned:
    type: llm
    prompt: p
    provider: azure
    model: dep-a
    state_key: answer
  mixed:
    type: llm
    prompt: p
    model: dep-b
    state_key: answer
  librarian:
    type: agent
    prompt: p
    tools: []
    state_key: agent_out
edges:
  - from: START
    to: answer
  - from: answer
    to: END
"""


def _write_graph(tmp_path: Path, text: str = ROOT_GRAPH) -> Path:
    path = tmp_path / "graph.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def preflight():
    return _load_module("research_preflight_fr1028", PREFLIGHT_PY)


@pytest.fixture(scope="module")
def tools():
    return _load_module("research_tools_fr1028", TOOLS_PY)


# --- AC-01: parser -----------------------------------------------------------


@pytest.mark.req("REQ-YG-671")
def test_graph_run_parser_accepts_provider_and_model():
    from yamlgraph.cli import create_parser

    args = create_parser().parse_args(
        ["graph", "run", "g.yaml", "--provider", "azure", "--model", "dep"]
    )
    assert (args.provider, args.model) == ("azure", "dep")


@pytest.mark.req("REQ-YG-671")
def test_graph_run_parser_defaults_to_none():
    from yamlgraph.cli import create_parser

    args = create_parser().parse_args(["graph", "run", "g.yaml"])
    assert args.provider is None and args.model is None


# --- AC-02 / AC-03: loader ---------------------------------------------------


@pytest.mark.req("REQ-YG-671")
def test_loader_override_replaces_root_defaults_without_mutating_source(tmp_path):
    from yamlgraph.compile.graph_loader import load_graph_config

    path = _write_graph(tmp_path)
    overridden = load_graph_config(
        path, provider_override="azure", model_override="dep"
    )
    assert overridden.defaults["provider"] == "azure"
    assert overridden.defaults["model"] == "dep"
    assert overridden.provider == "azure"

    on_disk = yaml.safe_load(path.read_text(encoding="utf-8"))["defaults"]
    assert on_disk == {"provider": "anthropic", "model": "claude-haiku-4-5"}
    plain = load_graph_config(path)
    assert plain.defaults["provider"] == "anthropic"
    assert plain.defaults["model"] == "claude-haiku-4-5"


@pytest.mark.req("REQ-YG-671")
def test_loader_provider_only_and_model_only(tmp_path):
    from yamlgraph.compile.graph_loader import load_graph_config

    path = _write_graph(tmp_path)
    provider_only = load_graph_config(path, provider_override="azure")
    assert provider_only.defaults["provider"] == "azure"
    assert provider_only.defaults["model"] == "claude-haiku-4-5"
    model_only = load_graph_config(path, model_override="dep")
    assert model_only.defaults["provider"] == "anthropic"
    assert model_only.defaults["model"] == "dep"


# --- AC-04 / AC-05: node resolution for llm and agent ------------------------


def _agent_provider_model(node_config: dict, defaults: dict) -> tuple[str, str]:
    from yamlgraph.tools.agent import create_agent_node

    with (
        patch("yamlgraph.tools.agent.load_prompt") as mock_load,
        patch("yamlgraph.tools.agent.create_llm") as mock_create_llm,
    ):
        mock_load.return_value = {"system": "s", "user": "{input}"}
        llm = MagicMock()
        llm.bind_tools.return_value = llm
        llm.invoke.return_value = MagicMock(content="done", tool_calls=[])
        mock_create_llm.return_value = llm
        node_fn = create_agent_node(
            node_name="a", node_config=node_config, tools={}, defaults=defaults
        )
        node_fn({"input": "x"})
        kwargs = mock_create_llm.call_args.kwargs
        return kwargs.get("provider"), kwargs.get("model")


@pytest.mark.req("REQ-YG-671")
def test_defaults_only_llm_and_agent_nodes_inherit_override(tmp_path):
    from yamlgraph.compile.graph_loader import load_graph_config
    from yamlgraph.node_factory.llm_nodes import resolve_llm_node_config

    cfg = load_graph_config(
        _write_graph(tmp_path), provider_override="azure", model_override="dep"
    )
    llm = resolve_llm_node_config("answer", cfg.nodes["answer"], cfg.defaults, None)
    assert (llm.provider, llm.model) == ("azure", "dep")
    assert _agent_provider_model({"tools": []}, cfg.defaults) == ("azure", "dep")


@pytest.mark.req("REQ-YG-671")
def test_explicit_pins_win_and_mixed_pin_inherits_unpinned_field(tmp_path):
    from yamlgraph.compile.graph_loader import load_graph_config
    from yamlgraph.node_factory.llm_nodes import resolve_llm_node_config

    cfg = load_graph_config(
        _write_graph(tmp_path), provider_override="openai", model_override="dep"
    )
    pinned = resolve_llm_node_config("pinned", cfg.nodes["pinned"], cfg.defaults, None)
    assert (pinned.provider, pinned.model) == ("azure", "dep-a")
    mixed = resolve_llm_node_config("mixed", cfg.nodes["mixed"], cfg.defaults, None)
    assert (mixed.provider, mixed.model) == ("openai", "dep-b")
    assert _agent_provider_model(
        {"tools": [], "provider": "azure", "model": "dep-a"}, cfg.defaults
    ) == ("azure", "dep-a")
    assert _agent_provider_model({"tools": [], "model": "dep-b"}, cfg.defaults) == (
        "openai",
        "dep-b",
    )


# --- AC-06: root only ----------------------------------------------------------


@pytest.mark.req("REQ-YG-671")
def test_override_not_forwarded_to_graph_tool_child(tmp_path):
    from yamlgraph.compile import graph_loader

    child = tmp_path / "child.yaml"
    child.write_text(
        "version: '1.0'\nname: child\ndefaults:\n  provider: anthropic\n"
        "state:\n  x: str\nnodes:\n  n:\n    type: python\n    tool: noop\n"
        "tools:\n  noop:\n    type: python\n    path: noop.py\n    function: noop\n"
        "edges:\n  - from: START\n    to: n\n  - from: n\n    to: END\n",
        encoding="utf-8",
    )
    (tmp_path / "noop.py").write_text("def noop(state):\n    return {}\n")
    root = tmp_path / "root.yaml"
    root.write_text(
        "version: '1.0'\nname: root\ndefaults:\n  provider: anthropic\n"
        "state:\n  x: str\n"
        "tools:\n  kid:\n    type: graph\n    path: child.yaml\n"
        "nodes:\n  n:\n    type: python\n    tool: noop\n"
        "edges:\n  - from: START\n    to: n\n  - from: n\n    to: END\n",
        encoding="utf-8",
    )
    cfg = graph_loader.load_graph_config(root, provider_override="azure")
    real = graph_loader.load_graph_config
    with patch.object(graph_loader, "load_graph_config", wraps=real) as spy:
        graph_loader._parse_graph_tools(cfg)
    child_calls = [
        c for c in spy.call_args_list if Path(c.args[0]).name == "child.yaml"
    ]
    assert child_calls, "child graph must be loaded through load_graph_config"
    for call in child_calls:
        assert call.kwargs.get("provider_override") is None
        assert call.kwargs.get("model_override") is None


# --- AC-07: no-flag path unchanged ------------------------------------------


@pytest.mark.req("REQ-YG-671")
def test_no_flag_load_matches_yaml(tmp_path):
    from yamlgraph.compile.graph_loader import load_graph_config

    cfg = load_graph_config(_write_graph(tmp_path))
    assert cfg.defaults == {"provider": "anthropic", "model": "claude-haiku-4-5"}


# --- AC-08 / AC-09: wrapper --------------------------------------------------


def _write_stub(path: Path, body: str) -> Path:
    path.write_text(f"#!/usr/bin/env bash\n{body}\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def _run_wrapper(workdir: Path, stub: Path | None, extra_env: dict | None = None):
    env = {
        k: v
        for k, v in os.environ.items()
        if k
        not in (
            "RESEARCH_EXECUTION",
            "YAMLGRAPH_BIN",
            "RESEARCH_PROVIDER",
            "RESEARCH_MODEL",
        )
    }
    env["RESEARCH_WORKDIR"] = str(workdir)
    if stub is not None:
        env["YAMLGRAPH_BIN"] = str(stub)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(RESEARCH_SH), str(CLEAN_BRIEF)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def _valid_artifact(tools, base: Path) -> Path:
    findings = [
        {
            "persona": p,
            "candidate": f"cand-{i}",
            "solution_class": c,
            "verdict": "pursue",
            "rationale": "r",
            "precedent": pre,
            "is_this_a_graph": "no",
            "effort_risk": "low/low",
        }
        for i, (p, c, pre) in enumerate(
            [
                ("os-infra-primitivist", "os-permissions", "FR-889 chmod"),
                ("data-process-planner", "schema-data", "FR-884 skeleton"),
                (
                    "yamlgraph-native-planner",
                    "graph-pipeline",
                    "examples/demos/map/graph.yaml",
                ),
                ("subtractionist", "subtraction", "growth_as_default (Scripture)"),
                (
                    "librarian",
                    "external-method",
                    "OPA https://www.openpolicyagent.org/",
                ),
            ]
        )
    ]
    tools.reduce_findings(
        findings,
        str(CLEAN_BRIEF),
        base_dir=str(base),
        librarian_tool_results=[
            {"tool": "search_web", "output": "https://www.openpolicyagent.org/"}
        ],
        repo_root=str(REPO_ROOT),
    )
    return base / "tmp" / "draft-alternatives.md"


def _copy_stub(tmp_path: Path, fixture: Path) -> Path:
    return _write_stub(
        tmp_path / "yg",
        'mkdir -p "$RESEARCH_WORKDIR/tmp"\n'
        'printf "%s\\n" "$@" > "$RESEARCH_WORKDIR/tmp/argv"\n'
        f'cp "{fixture}" "$RESEARCH_WORKDIR/tmp/draft-alternatives.md"',
    )


@pytest.mark.req("REQ-YG-671")
def test_wrapper_forwards_nothing_when_pair_unset(tools, tmp_path):
    fixture = _valid_artifact(tools, tmp_path / "valid")
    result = _run_wrapper(tmp_path, _copy_stub(tmp_path, fixture))
    assert result.returncode == 0, result.stderr
    argv = (tmp_path / "tmp" / "argv").read_text(encoding="utf-8")
    assert "--provider" not in argv and "--model" not in argv
    text = (tmp_path / "tmp" / "draft-alternatives.md").read_text(encoding="utf-8")
    assert PROVENANCE not in text


@pytest.mark.req("REQ-YG-671")
def test_wrapper_forwards_pair_in_stable_order_and_stamps_once(tools, tmp_path):
    fixture = _valid_artifact(tools, tmp_path / "valid")
    result = _run_wrapper(
        tmp_path,
        _copy_stub(tmp_path, fixture),
        {"RESEARCH_PROVIDER": "azure", "RESEARCH_MODEL": "dep-1"},
    )
    assert result.returncode == 0, result.stderr
    argv = (tmp_path / "tmp" / "argv").read_text(encoding="utf-8").splitlines()
    i = argv.index("--provider")
    assert argv[i : i + 4] == ["--provider", "azure", "--model", "dep-1"]
    text = (tmp_path / "tmp" / "draft-alternatives.md").read_text(encoding="utf-8")
    assert text.count(PROVENANCE) == 1
    assert f"{PROVENANCE} azure/dep-1" in text


@pytest.mark.req("REQ-YG-671")
@pytest.mark.parametrize(
    "env", [{"RESEARCH_PROVIDER": "azure"}, {"RESEARCH_MODEL": "dep-1"}]
)
def test_wrapper_half_pair_exits_64_before_executor(tools, tmp_path, env):
    fixture = _valid_artifact(tools, tmp_path / "valid")
    result = _run_wrapper(tmp_path, _copy_stub(tmp_path, fixture), env)
    assert result.returncode == 64
    assert "RESEARCH_PROVIDER" in result.stderr and "RESEARCH_MODEL" in result.stderr
    assert not (tmp_path / "tmp" / "argv").exists(), "executor must not run"


@pytest.mark.req("REQ-YG-671")
def test_verify_artifact_provenance_line(preflight, tools, tmp_path):
    text = _valid_artifact(tools, tmp_path).read_text(encoding="utf-8")
    assert preflight.verify_artifact(text) == []  # legacy: no line
    good = text.replace("\n", f"\n{PROVENANCE} azure/dep-1\n", 1)
    assert preflight.verify_artifact(good) == []
    for bad_line in (
        f"{PROVENANCE}",
        f"{PROVENANCE} azure",
        f"{PROVENANCE} azure/dep 1",
    ):
        bad = text.replace("\n", f"\n{bad_line}\n", 1)
        assert any("provider/model" in v for v in preflight.verify_artifact(bad)), (
            bad_line
        )
    dup = text.replace(
        "\n", f"\n{PROVENANCE} azure/dep-1\n{PROVENANCE} azure/dep-1\n", 1
    )
    assert any("provider/model" in v for v in preflight.verify_artifact(dup))
