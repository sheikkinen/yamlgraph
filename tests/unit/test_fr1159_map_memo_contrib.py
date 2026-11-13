"""FR-1159 map memo shipped as contrib — REQ-YG-726 witnesses."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.process

REPO = Path(__file__).resolve().parents[2]
DEMO = REPO / "examples" / "demos" / "map_memo"
GRAPH = DEMO / "graph.yaml"


# AC-01
@pytest.mark.req("REQ-YG-726")
def test_memo_lives_only_in_contrib():
    assert (REPO / "yamlgraph" / "contrib" / "map_memo.py").is_file()
    assert not (REPO / "examples" / "shared" / "map_memo.py").exists()


# AC-05
@pytest.mark.req("REQ-YG-726")
def test_contrib_import_is_lazy():
    code = (
        "import sys, yamlgraph.contrib\n"
        "print('yamlgraph.contrib.map_memo' in sys.modules)\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
        cwd=REPO,
    )
    assert out.stdout.strip() == "False"


# AC-04
_INSTALLED_PROBE = r"""
import json, sys
from pathlib import Path
from yamlgraph.tools.python_tool import load_python_function, parse_python_tools
import yamlgraph.contrib.map_memo as mm

a = json.loads(sys.argv[1])
tools = parse_python_tools({
    n: {"type": "python", "module": "yamlgraph.contrib.map_memo", "function": n}
    for n in ("map_memo_split", "map_memo_merge")
})
split = load_python_function(tools["map_memo_split"], tool_name="map_memo_split")
merge = load_python_function(tools["map_memo_merge"], tool_name="map_memo_merge")
plan = split(items=a["items"], signature_files=a["sig"], store=a["store"])
merge(plan=plan, results=[{"_map_index": i} for i in range(len(plan["todo"]))],
      failures=[], map_name="m", map_dispatch="d")
again = split(items=a["items"], signature_files=a["sig"], store=a["store"])
print(json.dumps({"file": mm.__file__, "first": len(plan["todo"]),
                  "second": len(again["todo"])}))
"""


def _venv_python(venv: Path) -> Path:
    scripts = venv / ("Scripts" if os.name == "nt" else "bin")
    return scripts / ("python.exe" if os.name == "nt" else "python")


@pytest.mark.slow
@pytest.mark.req("REQ-YG-726")
def test_installed_wheel_ships_and_runs_memo(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    for name in ("pyproject.toml", "README.md", "LICENSE"):
        shutil.copy2(REPO / name, src / name)
    shutil.copytree(
        REPO / "yamlgraph",
        src / "yamlgraph",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    dist = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "pip", "wheel", str(src), "--no-deps"]
        + ["--no-build-isolation", "-q", "-w", str(dist)],
        check=True,
        cwd=tmp_path,
    )
    (wheel,) = dist.glob("yamlgraph-*.whl")
    names = zipfile.ZipFile(wheel).namelist()
    assert "yamlgraph/contrib/map_memo.py" in names
    assert not any(n.endswith("examples/shared/map_memo.py") for n in names)

    venv = tmp_path / "venv"
    subprocess.run(
        [sys.executable, "-m", "venv", "--system-site-packages", str(venv)],
        check=True,
    )
    py = _venv_python(venv)
    subprocess.run(
        [str(py), "-m", "pip", "install", "-q", "--no-deps", "--no-index"]
        + ["--force-reinstall", str(wheel)],
        check=True,
    )

    work = tmp_path / "work"
    work.mkdir()
    items = []
    for i in range(3):
        p = work / f"f{i}.txt"
        p.write_text(f"file {i}\n", encoding="utf-8")
        items.append(str(p))
    sig = work / "sig.yaml"
    sig.write_text("v: 1\n", encoding="utf-8")
    args = {"items": items, "sig": [str(sig)], "store": str(work / "m.sqlite")}
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    out = subprocess.run(
        [str(py), "-c", _INSTALLED_PROBE, json.dumps(args)],
        capture_output=True,
        text=True,
        check=True,
        cwd=work,
        env=env,
    )
    result = json.loads(out.stdout.strip().splitlines()[-1])
    assert Path(result["file"]).resolve().is_relative_to(venv.resolve())
    assert (result["first"], result["second"]) == (3, 0)


# AC-06
NOTES = {"alpha.md": "Alpha note.\n", "beta.md": "Beta note.\n", "gamma.md": "Gamma.\n"}


def _invoke(notes_dir: Path, store: Path, calls: list) -> dict:
    from yamlgraph.compile.graph_loader import load_and_compile

    def fake(**kwargs):
        if "summarize" in str(kwargs["prompt_name"]):
            calls.append(kwargs["variables"])
            return "SUMMARY"
        raise AssertionError(f"unexpected prompt {kwargs['prompt_name']}")

    with patch("yamlgraph.node_factory.llm_nodes.execute_prompt", side_effect=fake):
        app = load_and_compile(str(GRAPH)).compile()
        return app.invoke({"notes_dir": str(notes_dir), "store": str(store)})


def _records(out: dict) -> list:
    return out["merged"]["result"]["records"]


@pytest.mark.req("REQ-YG-726")
def test_demo_reuses_unchanged_notes(tmp_path):
    notes = tmp_path / "notes"
    notes.mkdir()
    for name, text in NOTES.items():
        (notes / name).write_text(text, encoding="utf-8")
    store = tmp_path / "memo.sqlite"

    calls: list = []
    first = _invoke(notes, store, calls)
    assert len(calls) == 3

    calls.clear()
    second = _invoke(notes, store, calls)
    assert calls == []
    assert second["merged"]["result"]["counts"]["reused_ok"] == 3
    assert _records(second) == _records(first)

    (notes / "beta.md").write_text("Beta note, edited.\n", encoding="utf-8")
    calls.clear()
    third = _invoke(notes, store, calls)
    assert len(calls) == 1
    counts = third["merged"]["result"]["counts"]
    assert (counts["reused_ok"], counts["executed_ok"]) == (2, 1)
