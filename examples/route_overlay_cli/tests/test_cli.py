import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def cli_module():
    cli_path = REPO_ROOT / "examples" / "route_overlay_cli" / "cli.py"
    spec = importlib.util.spec_from_file_location("route_overlay_cli_cli", cli_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module spec for {cli_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_min_graph(path):
    path.write_text(
        """
version: "1.0"
name: route-overlay-cli-test
nodes:
  step:
    type: passthrough
edges:
  - from: START
    to: step
  - from: step
    to: END
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _write_route(path):
    line = {
        "event": "route",
        "node": "step",
        "value": "default",
        "target": "END",
        "thread_id": None,
    }
    path.write_text(json.dumps(line) + "\n", encoding="utf-8")


def test_render_requires_route_argument(tmp_path, cli_module):
    graph = tmp_path / "graph.yaml"
    _write_min_graph(graph)

    with pytest.raises(SystemExit) as exc:
        cli_module.main(["render", "--graph", str(graph)])

    assert exc.value.code == 2


def test_render_invalid_route_path_fails_with_diagnostic(tmp_path, capsys, cli_module):
    graph = tmp_path / "graph.yaml"
    _write_min_graph(graph)

    code = cli_module.main(
        [
            "render",
            "--graph",
            str(graph),
            "--route",
            str(tmp_path / "missing.route.jsonl"),
        ]
    )

    assert code == 2
    assert "Route file not found" in capsys.readouterr().err


def test_render_invalid_route_content_fails_parse_gate(tmp_path, capsys, cli_module):
    graph = tmp_path / "graph.yaml"
    route = tmp_path / "route.jsonl"
    _write_min_graph(graph)
    route.write_text('{"event":"not-route"}\n', encoding="utf-8")

    code = cli_module.main(
        [
            "render",
            "--graph",
            str(graph),
            "--route",
            str(route),
            "--out-dir",
            str(tmp_path),
        ]
    )

    assert code == 2
    stderr = capsys.readouterr().err
    assert str(route) in stderr
    assert "contains no valid route events" in stderr


def test_render_success_writes_mmd_and_invokes_mmdc_twice(
    tmp_path, monkeypatch, capsys, cli_module
):
    graph = tmp_path / "graph.yaml"
    route = tmp_path / "route.jsonl"
    out_dir = tmp_path / "out"
    _write_min_graph(graph)
    _write_route(route)

    monkeypatch.setattr(cli_module.shutil, "which", lambda _: "/usr/local/bin/mmdc")

    calls = []

    def _fake_run(cmd, check, capture_output, text):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(cli_module.subprocess, "run", _fake_run)

    code = cli_module.main(
        [
            "render",
            "--graph",
            str(graph),
            "--route",
            str(route),
            "--out-dir",
            str(out_dir),
            "--format",
            "svg",
        ]
    )

    assert code == 0
    assert (out_dir / "graph.authored.mmd").exists()
    assert (out_dir / "graph.overlay.mmd").exists()

    assert len(calls) == 2

    first = calls[0]
    second = calls[1]

    assert first[0] == "/usr/local/bin/mmdc"
    assert second[0] == "/usr/local/bin/mmdc"

    first_in = first[first.index("-i") + 1]
    first_out = first[first.index("-o") + 1]
    second_in = second[second.index("-i") + 1]
    second_out = second[second.index("-o") + 1]

    assert first_in != second_in
    assert first_out != second_out
    assert first_in.endswith("graph.authored.mmd")
    assert second_in.endswith("graph.overlay.mmd")
    assert first_out.endswith("graph.authored.svg")
    assert second_out.endswith("graph.overlay.svg")

    stdout = capsys.readouterr().out
    assert "authored_mmd=" in stdout
    assert "overlay_mmd=" in stdout
    assert "authored_image=" in stdout
    assert "overlay_image=" in stdout


def test_render_missing_mmdc_fails_preflight(tmp_path, monkeypatch, capsys, cli_module):
    graph = tmp_path / "graph.yaml"
    route = tmp_path / "route.jsonl"
    _write_min_graph(graph)
    _write_route(route)

    monkeypatch.setattr(cli_module.shutil, "which", lambda _: None)

    code = cli_module.main(
        [
            "render",
            "--graph",
            str(graph),
            "--route",
            str(route),
            "--out-dir",
            str(tmp_path),
        ]
    )

    assert code == 2
    assert "mmdc not found" in capsys.readouterr().err
