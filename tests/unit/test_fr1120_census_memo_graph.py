"""FR-1120 AC-07/AC-08/AC-09: the memoized census graph, provider-free.

The census tree is copied into a temporary root and the graph runs from
there, so the cwd-relative signature files can be edited without touching
the repository. Discovery, versions and extraction are bound to stub
manifests with call logs; the LLM is stubbed at `execute_prompt`.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.process

REPO = Path(__file__).resolve().parents[2]
CENSUS = Path("examples/demos/person_profile_census")
GRAPH = CENSUS / "graph.yaml"
SIGNATURE_FILES = [
    "examples/demos/person_profile_census/graph.yaml",
    "examples/demos/person_profile_census/prompts/classify_pr.yaml",
    "examples/demos/person_profile_census/tools.py",
    "examples/demos/corpus_census/adapters/corpus_adapters.py",
]
REFS = ["acme/a#1", "acme/a#2", "acme/a#3", "acme/b#4", "acme/b#5"]
FAILING = "acme/a#3"

STUBS = """
import json
from pathlib import Path

HERE = Path(__file__).parent


def _fixture():
    return json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))


def _log(kind, value):
    with (HERE / "calls.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps([kind, value]) + "\\n")


def discover(state):
    _log("discover", state["source"])
    return sorted(_fixture()["versions"])


def versions(state):
    _log("versions", state["source"])
    return dict(sorted(_fixture()["versions"].items()))


def extract(state):
    _log("extract", state["item"])
    return json.dumps(_fixture()["bundles"][state["item"]])
"""


def _manifest(name: str, function: str) -> str:
    return (
        f"name: {name}\ndescription: stub\nruntime:\n  type: python\n"
        f"  path: stubs.py\n  function: {function}\n"
    )


def _bundle(ref: str, rev: str) -> dict:
    repo, number = ref.split("#")
    return {
        "repo": repo,
        "number": int(number),
        "url": f"https://github.com/{repo}/pull/{number}",
        "title": f"feat: change {number} {rev}",
        "state": "merged",
        "created_at": "2026-09-01T00:00:00Z",
        "merged_at": "2026-09-02T00:00:00Z",
        "additions": int(number) * 10,
        "deletions": 1,
        "changed_files": 1,
        "labels": [],
        "base_sha": "a" * 40,
        "head_sha": "b" * 40,
        "body_head": "body",
    }


@pytest.fixture
def root(tmp_path: Path, monkeypatch) -> Path:
    base = tmp_path / "root"
    shutil.copytree(REPO / CENSUS, base / CENSUS)
    adapters = base / "examples/demos/corpus_census/adapters"
    adapters.mkdir(parents=True)
    shutil.copy(
        REPO / "examples/demos/corpus_census/adapters/corpus_adapters.py", adapters
    )
    shutil.copytree(REPO / "examples/shared", base / "examples/shared")
    stubs = base / "stubs"
    stubs.mkdir()
    (stubs / "stubs.py").write_text(STUBS, encoding="utf-8")
    for name in ("discover", "versions", "extract"):
        (stubs / f"{name}.tool.yaml").write_text(
            _manifest(name, name), encoding="utf-8"
        )
    for var in ("AZURE_AI_ENDPOINT", "AZURE_AI_API_KEY", "AZURE_MODEL"):
        monkeypatch.setenv(var, "stub")
    monkeypatch.chdir(base)
    saved = list(sys.path)
    yield base
    sys.path[:] = saved


def _write_fixture(root: Path, revs: dict[str, str]) -> None:
    fixture = {
        "versions": {ref: f"2026-09-0{revs.get(ref, '1')}T00:00:00Z" for ref in REFS},
        "bundles": {ref: _bundle(ref, revs.get(ref, "r1")) for ref in REFS},
    }
    (root / "stubs/fixture.json").write_text(json.dumps(fixture), encoding="utf-8")


def _calls(root: Path, kind: str) -> list:
    log = root / "stubs/calls.jsonl"
    if not log.exists():
        return []
    rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    return [value for k, value in rows if k == kind]


def _vars(root: Path, store: str | None, **overrides) -> dict:
    state = {
        "source": "sheikkinen@acme:2026-01-01",
        "visibility": '["private"]',
        "rubric": "Classify.",
        "problem_labels": '["tooling","tests"]',
        "surface_labels": '["backend","docs"]',
        "azure_model": "model-a",
        "output_path": str(root / "out/ledger.md"),
        "brief_path": str(root / "out/brief.md"),
        "brief_rubric": "Profile.",
    }
    if store is not None:
        state["memo_store"] = store
    return {**state, **overrides}


def _run(root: Path, store: str | None = "memo.sqlite", **overrides):
    from yamlgraph.compile.graph_loader import compile_graph, load_graph_config

    classify: list[str] = []

    def fake(**kwargs):
        name = str(kwargs["prompt_name"])
        if "classify" in name:
            bundle = json.loads(kwargs["variables"]["evidence_bundle"])
            ref = f"{bundle['repo']}#{bundle['number']}"
            classify.append(ref)
            if ref == FAILING:
                raise ValueError("stub provider error")
            return {
                "problem_class": "tooling",
                "change_kind": "feat",
                "surfaces": ["backend"],
                "intent": f"intent {ref}",
                "evidence_span": bundle["title"],
            }
        return {"title": "Profile"}

    stubs = root / "stubs"
    config = load_graph_config(
        str(root / GRAPH),
        tool_bindings={
            "preflight": str(root / CENSUS / "preflight.tool.yaml"),
            "discover": str(stubs / "discover.tool.yaml"),
            "versions": str(stubs / "versions.tool.yaml"),
            "extract": str(stubs / "extract.tool.yaml"),
        },
    )
    before = len(_calls(root, "extract"))
    with patch("yamlgraph.node_factory.llm_nodes.execute_prompt", side_effect=fake):
        app = compile_graph(config).compile()
        out = app.invoke(_vars(root, store, **overrides))
    extracts = _calls(root, "extract")[before:]
    jsonl = (root / "out/ledger.jsonl").read_bytes()
    return out, extracts, classify, jsonl


def _statuses(jsonl: bytes) -> dict[str, str]:
    rows = [json.loads(line) for line in jsonl.splitlines()]
    return {r["item_ref"]: r["classification_status"] for r in rows}


@pytest.mark.req("REQ-YG-709")
def test_three_runs_reuse_and_recompute(root):
    _write_fixture(root, {})
    _, ext1, cls1, jsonl1 = _run(root)
    assert sorted(ext1) == REFS and sorted(cls1) == REFS
    assert _statuses(jsonl1)[FAILING] == "row_failed"

    _, ext2, cls2, jsonl2 = _run(root)
    assert ext2 == [] and cls2 == []
    assert jsonl2 == jsonl1
    assert _statuses(jsonl2)[FAILING] == "row_failed"

    _write_fixture(root, {"acme/b#4": "2"})
    _, ext3, cls3, jsonl3 = _run(root)
    assert ext3 == ["acme/b#4"] and cls3 == ["acme/b#4"]

    _, _, _, clean = _run(root, store="clean.sqlite")
    assert jsonl3 == clean
    assert jsonl3 != jsonl1


@pytest.mark.req("REQ-YG-709")
@pytest.mark.parametrize(
    ("var", "value"),
    [
        ("rubric", "Classify differently."),
        ("problem_labels", '["tooling","tests","docs"]'),
        ("surface_labels", '["backend","docs","ci"]'),
        ("azure_model", "model-b"),
    ],
)
def test_each_signature_input_reruns_everything(root, var, value):
    _write_fixture(root, {})
    _run(root)
    _, ext, cls, _ = _run(root, **{var: value})
    assert sorted(ext) == REFS and sorted(cls) == REFS


@pytest.mark.req("REQ-YG-709")
def test_graph_passes_exactly_the_four_signature_files():
    import yaml

    graph = yaml.safe_load((REPO / GRAPH).read_text(encoding="utf-8"))
    args = graph["nodes"]["memo_split"]["args"]
    assert args["signature_files"] == SIGNATURE_FILES


@pytest.mark.req("REQ-YG-709")
def test_signature_file_change_reruns_everything(root):
    _write_fixture(root, {})
    _run(root)
    tools = root / CENSUS / "tools.py"
    tools.write_text(
        tools.read_text(encoding="utf-8") + "\n# edited\n", encoding="utf-8"
    )
    _, ext, cls, _ = _run(root)
    assert sorted(ext) == REFS and sorted(cls) == REFS


@pytest.mark.req("REQ-YG-709")
def test_missing_memo_store_fails_before_extract(root):
    _write_fixture(root, {})
    with pytest.raises(Exception, match="memo_store"):
        _run(root, store=None)
    assert _calls(root, "extract") == []
    assert not any(root.rglob("*.sqlite"))
