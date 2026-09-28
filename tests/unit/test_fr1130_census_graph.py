"""FR-1130 AC-06..AC-08: the LangGraph issues census graph, provider-free.

The census trees are copied into a temporary root and the graph runs from
there. The real gh-issues manifests are bound to the slots; `gh` is stubbed
at `subprocess.run` with the committed raw-read fixture and the LLM at
`execute_prompt`, answering each item with its fixture expectation.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.process

REPO = Path(__file__).resolve().parents[2]
CENSUS = Path("examples/demos/langgraph_issues_census")
GRAPH = CENSUS / "graph.yaml"
ADAPTERS = Path("examples/demos/corpus_census/adapters")
FIXTURE = REPO / "tests/fixtures/fr1130/raw_read.json"
DATA = json.loads(FIXTURE.read_text(encoding="utf-8"))
SLUG = "langchain-ai/langgraph"
REFS = [f"{SLUG}#{n}" for n in sorted(r["number"] for r in DATA["records"])]
CANARY = next(ref for ref, e in DATA["expected"].items() if e["role"] == "canary")
FAILING = f"{SLUG}#5000"
SIGNATURE_FILES = [
    "examples/demos/langgraph_issues_census/graph.yaml",
    "examples/demos/corpus_census/prompts/judge_item.yaml",
    "examples/demos/corpus_census/tools.py",
    "examples/demos/corpus_census/adapters/gh_issues_adapters.py",
    "examples/demos/corpus_census/adapters/gh_issues_report.py",
]


@pytest.fixture
def root(tmp_path: Path, monkeypatch) -> Path:
    base = tmp_path / "root"
    shutil.copytree(
        REPO / CENSUS, base / CENSUS, ignore=shutil.ignore_patterns("results")
    )
    shutil.copytree(
        REPO / "examples/demos/corpus_census",
        base / "examples/demos/corpus_census",
        ignore=shutil.ignore_patterns("proofs", "*.log"),
    )
    shutil.copytree(REPO / "examples/shared", base / "examples/shared")
    for var in ("AZURE_AI_ENDPOINT", "AZURE_AI_API_KEY", "AZURE_MODEL"):
        monkeypatch.setenv(var, "stub")
    monkeypatch.chdir(base)
    saved = list(sys.path)
    yield base
    sys.path[:] = saved


def _gh(argv, **kwargs):
    stdout = "".join(json.dumps(r) + "\n" for r in DATA["records"])
    return subprocess.CompletedProcess(argv, 0, stdout, "")


def _vars(root: Path, **overrides) -> dict:
    labels = json.loads((REPO / CENSUS / "labels.json").read_text(encoding="utf-8"))
    state = {
        "source": SLUG,
        "rubric": "Classify under the FR-1130 taxonomy.",
        "labels": json.dumps(labels),
        "provider": "azure",
        "model": "model-a",
        "output_path": str(root / "out/ledger.md"),
        "results_dir": str(root / "out"),
        "fixture_path": str(FIXTURE),
        "memo_store": str(root / "memo.sqlite"),
    }
    return {**state, **overrides}


def _run(
    root: Path,
    fail: set[str] = frozenset(),
    answer=None,
    judged: list[str] | None = None,
    **overrides,
):
    from yamlgraph.compile.graph_loader import compile_graph, load_graph_config

    judged = [] if judged is None else judged

    def fake(**kwargs):
        variables = kwargs["variables"]
        bundle = json.loads(variables["content"])
        ref = f"{SLUG}#{bundle['number']}"
        judged.append(ref)
        if ref in fail:
            raise ValueError("stub provider error")
        category = (answer or {}).get(ref) or DATA["expected"][ref]["category"]
        return {
            "source_index": int(variables["source_index"]),
            "judgement": category,
            "confidence": 0.9,
            "evidence_span": bundle["title"],
            "abstained": False,
            "abstain_reason": "",
        }

    config = load_graph_config(
        str(root / GRAPH),
        tool_bindings={
            "discover": str(root / ADAPTERS / "gh-issues-discover.tool.yaml"),
            "versions": str(root / ADAPTERS / "gh-issues-versions.tool.yaml"),
            "extract": str(root / ADAPTERS / "gh-issues-extract.tool.yaml"),
        },
    )
    with (
        patch.object(subprocess, "run", _gh),
        patch("yamlgraph.node_factory.llm_nodes.execute_prompt", side_effect=fake),
    ):
        app = compile_graph(config).compile()
        out = app.invoke(_vars(root, **overrides))
    return out, judged


def _artifacts(root: Path) -> tuple[bytes, bytes]:
    return (
        (root / "out/ledger.jsonl").read_bytes(),
        (root / "out/crosstab.md").read_bytes(),
    )


def _forget(root: Path, refs: list[str]) -> None:
    db = sqlite3.connect(root / "memo.sqlite")
    with db:
        db.executemany("DELETE FROM memo WHERE key = ?", [(r,) for r in refs])
    db.close()


@pytest.mark.req("REQ-YG-717")
def test_failure_blocks_then_recovers_only_that_item_then_reuses(root):
    with pytest.raises(Exception, match="abstain|row_failed|unresolved"):
        _run(root, fail={FAILING})
    assert not (root / "out/crosstab.md").exists()

    # The failure is memoized as row_failed: a replay judges nothing and
    # still refuses — a cached failure must never end the run silently.
    judged: list[str] = []
    with pytest.raises(Exception, match="abstain|row_failed|unresolved"):
        _run(root, judged=judged)
    assert judged == []
    assert not (root / "out/crosstab.md").exists()

    _forget(root, [FAILING])
    _, judged = _run(root)
    assert judged == [FAILING]
    rows = [
        json.loads(line)
        for line in (root / "out/ledger.jsonl").read_text().splitlines()
    ]
    assert [r["item_ref"] for r in rows] == REFS
    assert not any(r["abstained"] for r in rows)
    first = _artifacts(root)

    _, judged = _run(root)
    assert judged == []
    assert _artifacts(root) == first


@pytest.mark.req("REQ-YG-717")
def test_canary_mismatch_refuses_final_artifacts(root):
    with pytest.raises(Exception, match="canary"):
        _run(root, answer={CANARY: "docs"})
    assert not (root / "out/crosstab.md").exists()


@pytest.mark.req("REQ-YG-717")
@pytest.mark.parametrize(
    ("var", "value"),
    [("rubric", "Classify differently."), ("provider", "openai"), ("model", "model-b")],
)
def test_each_signature_input_rejudges_everything(root, var, value):
    _run(root)
    _, judged = _run(root, **{var: value})
    assert sorted(judged) == REFS


@pytest.mark.req("REQ-YG-717")
def test_signature_file_change_rejudges_everything(root):
    _run(root)
    adapters = root / ADAPTERS / "gh_issues_adapters.py"
    adapters.write_text(
        adapters.read_text(encoding="utf-8") + "\n# edited\n", encoding="utf-8"
    )
    _, judged = _run(root)
    assert sorted(judged) == REFS


@pytest.mark.req("REQ-YG-717")
def test_graph_contract():
    import yaml

    graph = yaml.safe_load((REPO / GRAPH).read_text(encoding="utf-8"))
    nodes = graph["nodes"]
    assert nodes["memo_split"]["args"]["signature_files"] == SIGNATURE_FILES
    assert nodes["extract_items"]["max_items"] == 10000
    assert nodes["judge_items"]["max_items"] == 10000
    assert graph["config"]["max_concurrency"] == 8
    labels = json.loads((REPO / CENSUS / "labels.json").read_text(encoding="utf-8"))
    from examples.demos.corpus_census.adapters import gh_issues_report as gir

    assert labels == gir.TAXONOMY
    assert gir.SIGNATURE_FILES == SIGNATURE_FILES
