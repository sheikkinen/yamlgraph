"""FR-775: book-summary loop redesign (extends FR-773/774, CAP-218).

Splitter extension tests (REQ-YG-577): mode=info page-count probe,
allow_empty_selection loop windows, absolute page metadata (R-1/R-2/R-3).

Demo helper tests: envelope gates (R-4), batch planning without inline
arithmetic (R-1), page-identity accumulation killing the sorted_add
_map_index-restart interleave (R-3/AC-05), cursor termination (AC-06).

Artifact tests: the committed graph probes via mode=info, fetches with
state-only args, declares the loop budget, and wires gates before
map/reduce; a forced loop_limits hit routes to combine via loop_exits.

RED contract: the splitter lacks mode=info / allow_empty_selection /
page metadata, and the demo is still the FR-774 linear pipeline.
"""

import importlib.util
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

pytestmark = pytest.mark.process

FIXTURE = Path("examples/demos/book-summary/fixture.pdf")
DEMO_GRAPH = Path("examples/demos/book-summary/graph.yaml")
DEMO_TOOLS = Path("examples/demos/book-summary/tools.py")
PROMPTS = Path("examples/demos/book-summary/prompts")
README = Path("examples/demos/book-summary/README.md")


def _split_document():
    from examples.shared.split_document import split_document

    return split_document


def _demo_tools():
    spec = importlib.util.spec_from_file_location("book_summary_tools", DEMO_TOOLS)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _mock_poppler(monkeypatch, total, page_text):
    """Fake pdfinfo/pdftotext; returns the recorded command list."""
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        if cmd[0] == "pdfinfo":
            return subprocess.CompletedProcess(
                cmd, 0, stdout=f"Pages: {total}\n", stderr=""
            )
        first = int(cmd[cmd.index("-f") + 1])
        last = int(cmd[cmd.index("-l") + 1])
        text = "\n".join(page_text(p) for p in range(first, last + 1))
        return subprocess.CompletedProcess(cmd, 0, stdout=text, stderr="")

    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/true")
    monkeypatch.setattr(subprocess, "run", fake_run)
    return calls


def _envelope(success, result=None, error=None):
    return {
        "task_id": None,
        "tool": "split_document",
        "success": success,
        "result": result,
        "error": error,
    }


# --- Splitter: mode=info probe (R-1, AC-02/AC-03) ---


@pytest.mark.req("REQ-YG-577")
def test_mode_info_returns_total_without_pdftotext(monkeypatch):
    calls = _mock_poppler(monkeypatch, 418, lambda p: f"page {p}")
    result = _split_document()(path=str(FIXTURE), mode="info")
    assert result == {"total": 418}
    assert all(c[0] == "pdfinfo" for c in calls)


# --- Splitter: absolute page metadata (R-3, AC-02) ---


@pytest.mark.req("REQ-YG-577")
def test_per_page_chunks_carry_absolute_page(monkeypatch):
    _mock_poppler(monkeypatch, 20, lambda p: f"text of page {p}")
    result = _split_document()(path=str(FIXTURE), start=5, end=7)
    assert [c["page"] for c in result["chunks"]] == [5, 6, 7]
    assert [c["index"] for c in result["chunks"]] == [0, 1, 2]


@pytest.mark.req("REQ-YG-577")
def test_batched_chunks_carry_page_span(monkeypatch):
    _mock_poppler(monkeypatch, 25, lambda p: f"text of page {p}")
    result = _split_document()(path=str(FIXTURE), pages_per_chunk=10)
    spans = [(c["page_start"], c["page_end"]) for c in result["chunks"]]
    assert spans == [(1, 10), (11, 20), (21, 25)]


@pytest.mark.req("REQ-YG-577")
def test_min_chars_filtering_preserves_absolute_pages(monkeypatch):
    texts = {1: "x" * 50, 2: "ab", 3: "y" * 50, 4: "z" * 50}
    _mock_poppler(monkeypatch, 4, lambda p: texts[p])
    result = _split_document()(path=str(FIXTURE), min_chars=10)
    assert [c["page"] for c in result["chunks"]] == [1, 3, 4]
    assert [c["index"] for c in result["chunks"]] == [0, 1, 2]


# --- Splitter: allow_empty_selection (R-2, AC-02/AC-04, C-3) ---


@pytest.mark.req("REQ-YG-577")
def test_allow_empty_selection_returns_blank_window(monkeypatch):
    _mock_poppler(monkeypatch, 418, lambda p: "")
    result = _split_document()(
        path=str(FIXTURE), start=11, end=20, allow_empty_selection=True
    )
    assert len(result["chunks"]) == 10
    assert [c["page"] for c in result["chunks"]] == list(range(11, 21))


@pytest.mark.req("REQ-YG-577")
def test_default_still_raises_on_all_empty(monkeypatch):
    _mock_poppler(monkeypatch, 10, lambda p: "")
    with pytest.raises(ValueError, match="scanned|image-only"):
        _split_document()(path=str(FIXTURE))


@pytest.mark.req("REQ-YG-577")
def test_allow_empty_selection_suppresses_all_filtered_raise(monkeypatch):
    _mock_poppler(monkeypatch, 5, lambda p: "abc")
    result = _split_document()(
        path=str(FIXTURE), min_chars=100, allow_empty_selection=True
    )
    assert result["chunks"] == []
    assert result["total"] == 5


@pytest.mark.req("REQ-YG-577")
def test_default_still_raises_on_all_filtered(monkeypatch):
    _mock_poppler(monkeypatch, 5, lambda p: "abc")
    with pytest.raises(ValueError, match="min_chars"):
        _split_document()(path=str(FIXTURE), min_chars=100)


# --- Demo helpers: envelope gates (R-4, AC-07) ---


@pytest.mark.req("REQ-YG-577")
def test_gate_probe_seeds_total_and_cursor():
    update = _demo_tools().gate_probe({"probe_result": _envelope(True, {"total": 418})})
    assert update["total"] == 418
    assert update["cursor"] == 1


@pytest.mark.req("REQ-YG-577")
def test_gate_probe_raises_on_failed_envelope():
    with pytest.raises(ValueError, match="pdfinfo exploded"):
        _demo_tools().gate_probe(
            {"probe_result": _envelope(False, error="pdfinfo exploded")}
        )


@pytest.mark.req("REQ-YG-577")
def test_gate_fetch_raises_on_failed_envelope():
    with pytest.raises(ValueError, match="pdftotext exploded"):
        _demo_tools().gate_fetch(
            {"fetch_result": _envelope(False, error="pdftotext exploded")}
        )


# --- Demo helpers: batch planning (R-1, AC-03) ---


@pytest.mark.req("REQ-YG-577")
def test_prepare_batch_computes_window():
    update = _demo_tools().prepare_batch({"cursor": 1, "total": 418})
    assert (update["batch_start"], update["batch_end"]) == (1, 10)


@pytest.mark.req("REQ-YG-577")
def test_prepare_batch_clamps_final_window():
    update = _demo_tools().prepare_batch({"cursor": 411, "total": 418})
    assert (update["batch_start"], update["batch_end"]) == (411, 418)


@pytest.mark.req("REQ-YG-577")
def test_advance_increments_cursor():
    assert _demo_tools().advance({"cursor": 11})["cursor"] == 21


# --- Demo helpers: page-identity accumulation (R-3, AC-05, C-4) ---


def _summary(map_index, page, text):
    # map_compiler flattens dict results: {"_map_index": i, **model_dump}
    return {"_map_index": map_index, "page": page, "summary": text}


@pytest.mark.req("REQ-YG-577")
def test_accumulate_filters_current_window_exactly_once_sorted():
    # Three accumulated batches with repeated _map_index values (the
    # sorted_add stable-sort interleave shape); current window is 21-30.
    collected = [
        _summary(0, 1, "s1"),
        _summary(0, 11, "s11"),
        _summary(0, 21, "s21"),
        _summary(1, 2, "s2"),
        _summary(1, 12, "s12"),
        _summary(1, 22, ""),
        _summary(2, 23, "s23"),
    ]
    state = {
        "page_summaries": collected,
        "batch_start": 21,
        "batch_end": 30,
        "fetch_result": _envelope(
            True,
            {
                "chunks": [
                    {"page": p, "index": p - 21, "text": "t"} for p in range(21, 31)
                ],
                "total": 30,
            },
        ),
    }
    update = _demo_tools().accumulate(state)
    fragment = update["all_summaries"]
    assert [e["page"] for e in fragment] == [21, 23]  # window only, empty dropped
    assert "all_summaries" in update and len(update) <= 3  # fragment, not combined


@pytest.mark.req("REQ-YG-577")
def test_accumulate_rejects_page_outside_fetched_chunks():
    state = {
        "page_summaries": [_summary(0, 13, "s13")],
        "batch_start": 11,
        "batch_end": 20,
        "fetch_result": _envelope(
            True,
            {
                "chunks": [
                    {"page": p, "index": i, "text": "t"}
                    for i, p in enumerate([11, 12, 14])
                ],
                "total": 20,
            },
        ),
    }
    with pytest.raises(ValueError, match="13"):
        _demo_tools().accumulate(state)


@pytest.mark.req("REQ-YG-577")
def test_loop_terminates_exact_multiple_and_partial():
    tools = _demo_tools()
    for total, expected_windows in (
        (20, [(1, 10), (11, 20)]),
        (18, [(1, 10), (11, 18)]),
    ):
        cursor, windows = 1, []
        while cursor <= total:
            update = tools.prepare_batch({"cursor": cursor, "total": total})
            windows.append((update["batch_start"], update["batch_end"]))
            cursor = tools.advance({"cursor": cursor})["cursor"]
        assert windows == expected_windows


# --- Committed artifact wiring (AC-03/AC-04/AC-06/AC-07) ---


@pytest.mark.req("REQ-YG-577")
def test_graph_probes_via_mode_info():
    raw = yaml.safe_load(DEMO_GRAPH.read_text())
    assert raw["nodes"]["probe"]["args"]["mode"] == "info"


@pytest.mark.req("REQ-YG-577")
def test_fetch_args_reference_state_only():
    raw = yaml.safe_load(DEMO_GRAPH.read_text())
    args = raw["nodes"]["fetch_batch"]["args"]
    assert args["start"] == "{state.batch_start}"
    assert args["end"] == "{state.batch_end}"
    assert args["pages_per_chunk"] == 1
    assert args["min_chars"] == 0
    assert args["allow_empty_selection"] is True
    assert not any("+" in str(v) for v in args.values())


@pytest.mark.req("REQ-YG-577")
def test_graph_declares_loop_budget_and_exit():
    raw = yaml.safe_load(DEMO_GRAPH.read_text())
    assert raw["loop_limits"]["advance"] == 100
    # FR-776 R-1: the loop exit routes through the document-level guard.
    assert raw["loop_exits"]["advance"] == "guard_extractable"
    readme = README.read_text()
    assert "1000" in readme
    assert "unbounded" not in readme.lower()
    assert "any book" not in readme.lower()


@pytest.mark.req("REQ-YG-577")
def test_graph_wires_gates_before_map_and_reduce():
    raw = yaml.safe_load(DEMO_GRAPH.read_text())
    edges = {(e["from"], e["to"]) for e in raw["edges"]}
    assert ("probe", "gate_probe") in edges
    assert ("fetch_batch", "gate_fetch") in edges
    # FR-776 R-4: partition sits between gate_fetch and the summarize map.
    assert ("gate_fetch", "partition") in edges
    assert ("partition", "summarize_pages") in edges
    # FR-776 R-3: provider preflight sits between gate_probe and the loop.
    assert ("gate_probe", "preflight_vision") in edges
    assert ("preflight_vision", "prepare_batch") in edges


@pytest.mark.req("REQ-YG-577")
def test_summarize_prompt_echoes_provided_page():
    prompt = yaml.safe_load((PROMPTS / "summarize_page.yaml").read_text())
    fields = prompt["schema"]["fields"]
    assert "page" in fields and "summary" in fields
    assert "chunk.page" in prompt["user"]


@pytest.mark.req("REQ-YG-577")
def test_forced_loop_limit_routes_to_combine(monkeypatch):
    _mock_poppler(monkeypatch, 30, lambda p: f"text of page {p} " * 20)
    from yamlgraph.compile.graph_loader import compile_graph, load_graph_config

    config = load_graph_config(DEMO_GRAPH)
    config.loop_limits["advance"] = 1  # force the hit on advance's 2nd run

    def fake_prompt(**kwargs):
        if "combine" in kwargs["prompt_name"]:
            return "combined summary"
        page = (kwargs.get("state") or {}).get("chunk", {}).get("page", 0)
        return {"page": page, "summary": f"summary of page {page}"}

    with patch(
        "yamlgraph.node_factory.llm_nodes.execute_prompt", side_effect=fake_prompt
    ):
        app = compile_graph(config).compile()
        result = app.invoke({"pdf": str(FIXTURE)}, config={"recursion_limit": 200})
    assert result.get("book_summary")  # combine reached via loop_exits
    pages = [e["page"] for e in result.get("all_summaries", [])]
    # advance executed once (cursor 1->11), hit its limit before the third
    # window: exactly batches 1-10 and 11-20 accumulated, 21-30 never ran.
    assert sorted(pages) == list(range(1, 21))
