"""FR-1113 meta-map demo — REQ-YG-703 witnesses.

Tool tests call `examples/demos/meta_map/tools.py` directly. Graph tests
build the real demo graph with `load_and_compile` and stub only
`execute_prompt`, so the map dispatch, subgraph branches, failure
channel and join run as compiled.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from yamlgraph.models.map_results import MapFailure, MapVerdict

pytestmark = pytest.mark.process

DEMO = Path("examples/demos/meta_map")
GRAPH = DEMO / "graph.yaml"
POISON = [
    "examples/demos/hello/graph.yaml",
    "feature-requests/FR-1113-meta-map-demo.md",
    "yamlgraph/compile/map_compiler.py",
]

MAP_GRAPH = """\
name: g
nodes:
  fan:
    type: map
    over: "{state.items}"
    as: item
    max_items: 5
    node:
      type: python
      tool: t
      state_key: out
    collect: outs
  other:
    type: python
    tool: t
"""
PLAIN_GRAPH = "name: h\nnodes:\n  greet:\n    type: llm\n    prompt: greet\n"
NON_GRAPH = "paths:\n  - a\n"
MARKDOWN = "# Feature Request\n\n```yaml\nnodes:\n  summarize:\n    type: map\n```\n"
PYTHON = "def compile_map_node(name):\n    return {'type': 'map'}\n"
CORE = {"over": "{state.x}", "as": "x", "node": {"type": "python"}, "collect": "y"}


def _tools():
    return importlib.import_module("examples.demos.meta_map.tools")


def _claim(nodes: list[str]) -> dict:
    return {"map_nodes": nodes, "intent": "An intent.", "map_role": "A role."}


def _reconcile(path: str, text: str, nodes: list[str]):
    tools = _tools()
    state = {
        "path": path,
        "source": tools.SourceText(path=path, text=text),
        "claim": _claim(nodes),
    }
    return tools.reconcile_claim(state)["graph_record"]


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    root = tmp_path / "corpus"
    (root / "sub").mkdir(parents=True)
    (root / "map.yaml").write_text(MAP_GRAPH, encoding="utf-8")
    (root / "sub" / "plain.yaml").write_text(PLAIN_GRAPH, encoding="utf-8")
    (root / "data.yaml").write_text(NON_GRAPH, encoding="utf-8")
    return root


# ---------------------------------------------------------------------------
# AC-1: discovery
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-703")
class TestDiscover:
    def test_returns_only_map_graphs(self, corpus):
        out = _tools().discover_map_graphs({"scan_roots": [str(corpus)]})
        assert out["paths"] == [(corpus / "map.yaml").as_posix()]

    def test_malformed_yaml_raises_naming_path(self, corpus):
        bad = corpus / "bad.yaml"
        bad.write_text("nodes: [unclosed\n", encoding="utf-8")
        with pytest.raises(ValueError, match=r"bad\.yaml"):
            _tools().discover_map_graphs({"scan_roots": [str(corpus)]})


# ---------------------------------------------------------------------------
# AC-1b: poison + plain reader
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-703")
class TestPoisonAndRead:
    def test_poison_appended_in_declared_order(self):
        out = _tools().poison_the_source(
            {"paths": ["a.yaml", "b.yaml"], "poison": {"paths": POISON}}
        )
        assert out["paths"] == ["a.yaml", "b.yaml", *POISON]

    def test_missing_poison_path_raises(self):
        with pytest.raises(FileNotFoundError, match=r"no/such/file\.yaml"):
            _tools().poison_the_source(
                {"paths": [], "poison": {"paths": ["no/such/file.yaml"]}}
            )

    @pytest.mark.parametrize("suffix", [".yaml", ".md", ".py"])
    def test_read_source_is_byte_for_byte(self, tmp_path, suffix):
        raw = b"first: line\r\n  second\tline\nthird \xc3\xa4\n"
        path = tmp_path / f"f{suffix}"
        path.write_bytes(raw)
        source = _tools().read_source({"path": str(path)})["source"]
        assert source.path == str(path)
        assert source.text.encode("utf-8") == raw

    def test_source_text_has_no_classifying_field(self):
        assert set(_tools().SourceText.model_fields) == {"path", "text"}


# ---------------------------------------------------------------------------
# AC-1c: reconcile
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-703")
class TestReconcile:
    def test_correct_claim_accepted(self):
        record = _reconcile("g.yaml", MAP_GRAPH, ["fan"])
        assert record.path == "g.yaml"
        assert [n.name for n in record.map_nodes] == ["fan"]
        node = record.map_nodes[0]
        assert node.sub_node_type == "python"
        assert node.declared_keys == ["over", "as", "max_items", "node", "collect"]
        assert node.version == "capped"
        assert record.graph_version == "capped"
        assert record.intent == "An intent."
        assert record.map_role == "A role."

    def test_claim_as_model_instance_accepted(self):
        tools = _tools()
        state = {
            "path": "g.yaml",
            "source": tools.SourceText(path="g.yaml", text=MAP_GRAPH),
            "claim": tools.MapClaim(**_claim(["fan"])),
        }
        assert tools.reconcile_claim(state)["graph_record"].path == "g.yaml"

    @pytest.mark.parametrize(
        ("text", "claimed"),
        [
            (MAP_GRAPH, []),
            (MAP_GRAPH, ["fan", "other"]),
            (MAP_GRAPH, ["other"]),
            (PLAIN_GRAPH, ["greet"]),
            (PLAIN_GRAPH, []),
            (MARKDOWN, ["summarize"]),
            (MARKDOWN, []),
            (PYTHON, ["compile_map_node"]),
        ],
        ids=[
            "empty",
            "invented",
            "wrong",
            "non-map",
            "non-map-empty",
            "md",
            "md-empty",
            "py",
        ],
    )
    def test_mismatch_raises_with_claim_and_parse(self, text, claimed):
        tools = _tools()
        with pytest.raises(tools.ClaimMismatchError) as exc:
            _reconcile("x", text, claimed)
        message = str(exc.value)
        assert f"claimed {sorted(claimed)}" in message
        assert "parsed [" in message

    def test_selection_and_grading_share_one_parse(self, corpus, monkeypatch):
        tools = _tools()
        calls: list[str] = []
        real = tools.parse_map_nodes

        def spy(text):
            calls.append(text)
            return real(text)

        monkeypatch.setattr(tools, "parse_map_nodes", spy)
        tools.discover_map_graphs({"scan_roots": [str(corpus)]})
        assert MAP_GRAPH in calls
        calls.clear()
        _reconcile("g.yaml", MAP_GRAPH, ["fan"])
        assert calls == [MAP_GRAPH]

    def test_describe_schema_has_no_decline_field(self):
        prompt = yaml.safe_load(
            (DEMO / "prompts" / "describe_graph.yaml").read_text(encoding="utf-8")
        )
        expected = {"map_nodes", "intent", "map_role"}
        assert set(prompt["schema"]["fields"]) == expected
        assert set(_tools().MapClaim.model_fields) == expected


# ---------------------------------------------------------------------------
# AC-2: version classifier
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-703")
class TestClassifyMapVersion:
    @pytest.mark.parametrize(
        ("extra", "version"),
        [
            ({"on_overflow": "error"}, "overflow"),
            ({"failures": "f"}, "result-contract"),
            ({"min_success": 0.9}, "result-contract"),
            ({"timeout": 10}, "timeout"),
            ({"max_items": 5}, "capped"),
            ({}, "core"),
        ],
    )
    def test_rule(self, extra, version):
        assert _tools().classify_map_version({**CORE, **extra}) == version

    def test_precedence_overflow_over_timeout(self):
        cfg = {**CORE, "timeout": 10, "on_overflow": "truncate", "max_items": 3}
        assert _tools().classify_map_version(cfg) == "overflow"


# ---------------------------------------------------------------------------
# AC-3: real repository discovery equals an independent walk
# ---------------------------------------------------------------------------


def _independent_walk() -> set[str]:
    found = set()
    for root in ("examples", "graphs"):
        for path in Path(root).rglob("*"):
            if path.suffix not in (".yaml", ".yml") or not path.is_file():
                continue
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
            nodes = doc.get("nodes") if isinstance(doc, dict) else None
            if isinstance(nodes, dict) and any(
                isinstance(n, dict) and n.get("type") == "map" for n in nodes.values()
            ):
                found.add(path.as_posix())
    return found


@pytest.mark.req("REQ-YG-703")
class TestRealRepositoryDiscovery:
    def test_path_set_equals_independent_walk(self):
        paths = _tools().discover_map_graphs({})["paths"]
        assert len(paths) == len(set(paths))
        assert set(paths) == _independent_walk()


# ---------------------------------------------------------------------------
# AC-6: render + reduce inputs
# ---------------------------------------------------------------------------


def _record(path: str, index: int, version: str = "capped") -> dict:
    return {
        "_map_index": index,
        "path": path,
        "graph_version": version,
        "map_nodes": [
            {
                "name": f"fan{index}",
                "sub_node_type": "llm",
                "declared_keys": ["over", "as", "node", "collect", "max_items"],
                "version": version,
            }
        ],
        "intent": f"Intent {index}.",
        "map_role": f"Role {index}.",
    }


def _failure(index: int, error_type: str, message: str) -> MapFailure:
    return MapFailure(
        map="summarize",
        dispatch="d1",
        index=index,
        error_type=error_type,
        message=message,
        node="_map_summarize_sub",
        tolerated=False,
    )


def _render_state(tmp_path: Path) -> dict:
    paths = ["r/a.yaml", "r/b.yaml", "r/c.yaml", "r/failed_real.yaml", *POISON]
    return {
        "paths": paths,
        "summaries": [_record("r/c.yaml", 2, "timeout"), _record("r/a.yaml", 0)],
        "summary_failures": [
            _failure(4, "ClaimMismatchError", "hello: claimed ['greet'], parsed []"),
            _failure(1, "TimeoutError", "Branch timed out after 120s"),
            _failure(3, "ClaimMismatchError", "real: claimed ['x'], parsed ['y']"),
            _failure(5, "ClaimMismatchError", "fr: claimed [], parsed []"),
            _failure(6, "ValidationError", "1 validation error for MapClaim"),
        ],
        "_map_verdict": {
            "summarize": MapVerdict(
                dispatch="d1",
                dispatched=7,
                succeeded=2,
                tolerated=0,
                failed=5,
                accepted=2,
                min_success=0.9,
                met=False,
            )
        },
        "overall": "REDUCED SUMMARY TEXT",
        "output_path": str(tmp_path / "out" / "report.md"),
    }


@pytest.mark.req("REQ-YG-703")
class TestRenderReport:
    def test_every_index_once_ordered_and_verbatim(self, tmp_path):
        state = _render_state(tmp_path)
        out = _tools().render_report(state)
        text = Path(out["report_path"]).read_text(encoding="utf-8")
        for path in state["paths"]:
            assert text.count(path) == 1, path
        assert text.index("r/a.yaml") < text.index("r/c.yaml")
        for failure in state["summary_failures"]:
            assert failure.message in text
        assert "over, as, node, collect, max_items" in text
        assert "7 dispatched · 2 succeeded · 0 tolerated · 5 failed" in text
        assert "REDUCED SUMMARY TEXT" in text

    def test_failed_path_resolved_by_index(self, tmp_path):
        state = _render_state(tmp_path)
        text = Path(_tools().render_report(state)["report_path"]).read_text(
            encoding="utf-8"
        )
        row = next(line for line in text.splitlines() if "r/failed_real.yaml" in line)
        assert "| 3 |" in row
        assert "claimed ['x'], parsed ['y']" in row

    def test_unaccounted_index_raises(self, tmp_path):
        state = _render_state(tmp_path)
        state["summary_failures"] = state["summary_failures"][1:]
        with pytest.raises(ValueError, match=r"index"):
            _tools().render_report(state)

    def test_missing_verdict_raises(self, tmp_path):
        state = _render_state(tmp_path)
        state["_map_verdict"] = {}
        with pytest.raises(KeyError):
            _tools().render_report(state)


@pytest.mark.req("REQ-YG-703")
class TestReduceInputs:
    def test_counts_come_from_verdict_and_records(self, tmp_path):
        state = _render_state(tmp_path)
        out = _tools().reduce_inputs(state)["reduce_input"]
        assert out["counts"]["dispatched"] == 7
        assert out["counts"]["succeeded"] == 2
        assert out["counts"]["failed"] == 5
        assert out["counts"]["by_version"] == {"capped": 1, "timeout": 1}
        assert [r["path"] for r in out["records"]] == ["r/a.yaml", "r/c.yaml"]


# ---------------------------------------------------------------------------
# AC-4 / AC-5 / AC-5b / AC-11: the demo graph
# ---------------------------------------------------------------------------


def _write_corpus(root: Path, count: int) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        (root / f"g{i:03d}.yaml").write_text(
            MAP_GRAPH.replace("fan:", f"fan{i}:"), encoding="utf-8"
        )


def _correct(path: str) -> dict:
    index = int(Path(path).stem[1:])
    return _claim([f"fan{index}"])


def _poison_stub(path: str) -> dict:
    if path == POISON[0]:
        return _claim(["greet"])
    if path == POISON[1]:
        return _claim([])
    if path == POISON[2]:
        raise ValueError("stub provider error")
    return _correct(path)


def _invoke(tmp_path: Path, root: Path, describe, calls: list | None = None):
    from yamlgraph.compile.graph_loader import load_and_compile, load_graph_config

    def fake(**kwargs):
        if "describe" in str(kwargs["prompt_name"]):
            if calls is not None:
                calls.append(kwargs["variables"]["path"])
            return describe(kwargs["variables"]["path"])
        return "REDUCED"

    # The CLI merges data_files into the initial state; a raw invoke must too.
    data = load_graph_config(str(GRAPH)).data
    with patch("yamlgraph.node_factory.llm_nodes.execute_prompt", side_effect=fake):
        app = load_and_compile(str(GRAPH)).compile()
        return app.invoke(
            {
                **data,
                "scan_roots": [str(root)],
                "output_path": str(tmp_path / "report.md"),
            }
        )


def _field(record, name):
    return record[name] if isinstance(record, dict) else getattr(record, name)


@pytest.mark.req("REQ-YG-703")
class TestDemoGraph:
    def test_poison_fails_untolerated_and_threshold_met(self, tmp_path):
        from yamlgraph.models.schemas import PipelineError

        root = tmp_path / "corpus"
        _write_corpus(root, 27)
        out = _invoke(tmp_path, root, _poison_stub)

        paths = out["paths"]
        assert paths[-3:] == POISON
        failures = [MapFailure.model_validate(f) for f in out["summary_failures"]]
        by_path = {paths[f.index]: f for f in failures}
        assert set(by_path) == set(POISON)
        assert by_path[POISON[0]].error_type == "ClaimMismatchError"
        assert by_path[POISON[1]].error_type == "ClaimMismatchError"
        assert "stub provider error" in by_path[POISON[2]].message
        assert not any(f.tolerated for f in failures)
        assert not {r["path"] for r in out["summaries"]} & set(POISON)

        verdict = MapVerdict.model_validate(out["_map_verdict"]["summarize"])
        assert (verdict.dispatched, verdict.failed, verdict.tolerated) == (30, 3, 0)
        assert verdict.met is True
        pipeline_errors = [e for e in out["errors"] if isinstance(e, PipelineError)]
        assert len(pipeline_errors) == 3 == len(out["errors"])
        assert Path(out["report_path"]).is_file()

    def test_below_threshold_raises_completeness_error(self, tmp_path):
        from yamlgraph.models.map_results import MapCompletenessError

        root = tmp_path / "corpus"
        _write_corpus(root, 27)

        def misreads_one(path):
            if path.endswith("g000.yaml"):
                return _claim(["invented"])
            return _poison_stub(path)

        with pytest.raises(MapCompletenessError):
            _invoke(tmp_path, root, misreads_one)

    def test_overflow_raises_before_any_branch(self, tmp_path):
        root = tmp_path / "corpus"
        _write_corpus(root, 98)
        calls: list[str] = []
        with pytest.raises(Exception, match=r"summarize"):
            _invoke(tmp_path, root, _poison_stub, calls)
        assert calls == []

    def test_subgraph_boundary_mappings(self, tmp_path):
        root = tmp_path / "corpus"
        _write_corpus(root, 27)
        out = _invoke(tmp_path, root, _poison_stub)
        fields = set(_tools().GraphRecord.model_fields)
        assert len(out["summaries"]) == 27
        for record in out["summaries"]:
            assert set(record) - {"_map_index"} == fields
            assert record["path"] == out["paths"][record["_map_index"]]

    def test_declared_map_config(self):
        graph = yaml.safe_load(GRAPH.read_text(encoding="utf-8"))
        summarize = graph["nodes"]["summarize"]
        assert summarize["type"] == "map"
        assert summarize["max_items"] == 100
        assert summarize["on_overflow"] == "error"
        assert summarize["timeout"] == 120
        assert summarize["min_success"] == 0.9
        assert summarize["failures"] == "summary_failures"
        assert summarize["collect"] == "summaries"
        node = summarize["node"]
        assert node["type"] == "subgraph"
        assert node["input_mapping"] == {"path": "path"}
        assert node["output_mapping"] == {"summary": "graph_record"}
        assert "on_error" not in node and "on_error" not in summarize
        assert graph["config"]["max_concurrency"] == 8
        assert graph["defaults"]["provider"] == "inception"
        assert graph["defaults"]["model"] == "mercury-2.5"

    def test_poison_declared_once_in_data_file(self):
        graph = yaml.safe_load(GRAPH.read_text(encoding="utf-8"))
        assert graph["data_files"] == {"poison": "poison.yaml"}
        poison = yaml.safe_load((DEMO / "poison.yaml").read_text(encoding="utf-8"))
        assert poison == {"paths": POISON}
        assert list(graph["nodes"]) == [
            "discover",
            "poison_the_source",
            "summarize",
            "prepare_reduce",
            "reduce",
            "render",
        ]
