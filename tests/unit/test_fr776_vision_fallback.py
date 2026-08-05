"""FR-776: vision fallback for scanned (OCR-less) PDFs in book-summary.

Shared tool tests (REQ-YG-578): render_page payload/raise contract
(R-5), typed PageTranscription + page-echo validation (R-2), provider
preflight before rendering (R-3).

Demo helper tests: partition/text_seen aggregate detection (R-1),
render/transcribe gates and window-filtered merge (R-4), the graph-level
FR-774 default guard at the combine boundary (R-1/AC-03).

Artifact tests: the committed graph declares the render manifest, wires
preflight before the render map, bounds both vision maps, and routes the
loop exit through the guard.

RED contract: render_page/transcribe_page/preflight do not exist, the
demo helpers lack the vision branch, and the graph is the FR-775 shape.
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
README = Path("examples/demos/book-summary/README.md")
RENDER_MANIFEST = Path("examples/shared/render_page.tool.yaml")

GUARD_MATCH = "no extractable text.*scanned/image-only"


def _render_page():
    from examples.shared.render_page import render_page

    return render_page


def _vision():
    import examples.shared.vision_tool as vt

    return vt


def _demo_tools():
    spec = importlib.util.spec_from_file_location("book_summary_tools", DEMO_TOOLS)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _mock_pdftoppm(monkeypatch, tmp_path, returncode=0, create_output=True):
    """Fake pdftoppm; records commands and kwargs, optionally emits a PNG."""
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((list(cmd), kwargs))
        if create_output and returncode == 0:
            prefix = Path(cmd[-1])
            prefix.parent.mkdir(parents=True, exist_ok=True)
            page = cmd[cmd.index("-f") + 1]
            Path(f"{prefix}-{page}.png").write_bytes(b"\x89PNG fake")
        return subprocess.CompletedProcess(cmd, returncode, stdout="", stderr="boom")

    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/true")
    monkeypatch.setattr(subprocess, "run", fake_run)
    return calls


# --- render_page: payload/raise contract (AC-01, R-5) ---


@pytest.mark.req("REQ-YG-578")
def test_render_page_success_returns_payload(monkeypatch, tmp_path):
    calls = _mock_pdftoppm(monkeypatch, tmp_path)
    result = _render_page()(str(FIXTURE), 2, out_dir=str(tmp_path))
    assert result["page"] == 2
    assert result["image"].endswith(".png")
    assert Path(result["image"]).is_file()
    cmd, kwargs = calls[0]
    assert cmd[0] == "pdftoppm"
    assert "-png" in cmd
    assert cmd[cmd.index("-f") + 1] == "2"
    assert cmd[cmd.index("-l") + 1] == "2"
    assert not kwargs.get("shell")


@pytest.mark.req("REQ-YG-578")
def test_render_page_default_out_dir_is_tmp(monkeypatch, tmp_path):
    _mock_pdftoppm(monkeypatch, tmp_path)
    result = _render_page()(str(FIXTURE), 1)
    assert result["image"].startswith("tmp/pages")


@pytest.mark.req("REQ-YG-578")
def test_render_page_missing_pdf_raises():
    with pytest.raises(FileNotFoundError, match="nope.pdf"):
        _render_page()("tmp/nope.pdf", 1)


@pytest.mark.req("REQ-YG-578")
def test_render_page_invalid_page_raises():
    with pytest.raises(ValueError, match="[Pp]age"):
        _render_page()(str(FIXTURE), 0)


@pytest.mark.req("REQ-YG-578")
def test_render_page_missing_binary_raises(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _: None)
    with pytest.raises(FileNotFoundError, match="pdftoppm|poppler"):
        _render_page()(str(FIXTURE), 1)


@pytest.mark.req("REQ-YG-578")
def test_render_page_nonzero_exit_raises(monkeypatch, tmp_path):
    _mock_pdftoppm(monkeypatch, tmp_path, returncode=1)
    with pytest.raises(ValueError, match="pdftoppm"):
        _render_page()(str(FIXTURE), 1, out_dir=str(tmp_path))


@pytest.mark.req("REQ-YG-578")
def test_render_page_missing_output_raises(monkeypatch, tmp_path):
    _mock_pdftoppm(monkeypatch, tmp_path, create_output=False)
    with pytest.raises(ValueError, match="output|PNG|png"):
        _render_page()(str(FIXTURE), 1, out_dir=str(tmp_path))


# --- render_page manifest (AC-02) ---


@pytest.mark.req("REQ-YG-578")
def test_render_manifest_declares_shared_module():
    raw = yaml.safe_load(RENDER_MANIFEST.read_text())
    assert raw["name"] == "render_page"
    assert raw["runtime"]["module"] == "examples.shared.render_page"
    assert raw["runtime"]["function"] == "render_page"


@pytest.mark.req("REQ-YG-578")
def test_graph_declares_render_via_manifest_only():
    raw = yaml.safe_load(DEMO_GRAPH.read_text())
    entry = raw["tools"]["render_page"]
    assert set(entry) == {"manifest"}
    assert entry["manifest"].endswith("render_page.tool.yaml")


@pytest.mark.req("REQ-YG-578")
def test_render_subnode_args_resolve_to_real_kwargs():
    """The committed render map subnode resolves state refs to kwargs."""
    from yamlgraph.node_factory import create_tool_call_node

    raw = yaml.safe_load(DEMO_GRAPH.read_text())
    sub = raw["nodes"]["render_pages"]["node"]
    item_key = raw["nodes"]["render_pages"]["as"]
    received = {}

    def recorder(**kwargs):
        received.update(kwargs)
        return {"page": 7, "image": "tmp/pages/p7.png"}

    node = create_tool_call_node("render_sub", sub, {"render_page": recorder})
    node({"pdf": str(FIXTURE), item_key: {"page": 7, "text": ""}})
    assert received.get("path") == str(FIXTURE)
    assert str(received.get("page")) == "7"
    for value in received.values():
        assert "{state." not in str(value)


# --- Typed transcription (AC-05, R-2) ---


@pytest.mark.req("REQ-YG-578")
def test_page_transcription_model_shape():
    vt = _vision()
    t = vt.PageTranscription(page=3, text="hello")
    assert t.page == 3
    assert t.text == "hello"
    assert t.is_blank is False


@pytest.mark.req("REQ-YG-578")
def test_transcribe_page_unsupported_provider_raises_before_llm(tmp_path):
    vt = _vision()
    img = tmp_path / "p.png"
    img.write_bytes(b"\x89PNG fake")
    with (
        patch.object(vt, "create_llm", side_effect=AssertionError("LLM called")),
        pytest.raises(ValueError, match="deepseek"),
    ):
        vt.transcribe_page(img, 1, provider="deepseek")


@pytest.mark.req("REQ-YG-578")
def test_transcribe_page_local_image_and_echo(tmp_path):
    vt = _vision()
    img = tmp_path / "p.png"
    img.write_bytes(b"\x89PNG fake")

    class FakeStructured:
        def invoke(self, _msgs):
            return vt.PageTranscription(page=7, text="page seven text")

    class FakeLLM:
        def with_structured_output(self, _model):
            return FakeStructured()

    with patch.object(vt, "create_llm", return_value=FakeLLM()):
        result = vt.transcribe_page(img, 7, provider="google")
    assert result.page == 7
    assert result.text == "page seven text"


@pytest.mark.req("REQ-YG-578")
def test_transcribe_page_echo_mismatch_raises(tmp_path):
    vt = _vision()
    img = tmp_path / "p.png"
    img.write_bytes(b"\x89PNG fake")

    class FakeStructured:
        def invoke(self, _msgs):
            return vt.PageTranscription(page=9, text="wrong page")

    class FakeLLM:
        def with_structured_output(self, _model):
            return FakeStructured()

    with (
        patch.object(vt, "create_llm", return_value=FakeLLM()),
        pytest.raises(ValueError, match="[Pp]age"),
    ):
        vt.transcribe_page(img, 7, provider="google")


@pytest.mark.req("REQ-YG-578")
def test_transcribe_page_blank_page_accepted(tmp_path):
    vt = _vision()
    img = tmp_path / "p.png"
    img.write_bytes(b"\x89PNG fake")

    class FakeStructured:
        def invoke(self, _msgs):
            return vt.PageTranscription(page=4, text="", is_blank=True)

    class FakeLLM:
        def with_structured_output(self, _model):
            return FakeStructured()

    with patch.object(vt, "create_llm", return_value=FakeLLM()):
        result = vt.transcribe_page(img, 4, provider="google")
    assert result.is_blank is True


@pytest.mark.req("REQ-YG-578")
def test_transcribe_page_malformed_output_raises(tmp_path):
    vt = _vision()
    img = tmp_path / "p.png"
    img.write_bytes(b"\x89PNG fake")

    class FakeStructured:
        def invoke(self, _msgs):
            return None

    class FakeLLM:
        def with_structured_output(self, _model):
            return FakeStructured()

    with (
        patch.object(vt, "create_llm", return_value=FakeLLM()),
        pytest.raises(ValueError),
    ):
        vt.transcribe_page(img, 1, provider="google")


@pytest.mark.req("REQ-YG-578")
def test_validate_vision_provider_contract(monkeypatch):
    vt = _vision()
    provider, model = vt.validate_vision_provider(provider="google")
    assert provider == "google"
    assert model
    with pytest.raises(ValueError, match="mistral"):
        vt.validate_vision_provider(provider="mistral")


# --- Demo helpers: preflight (R-3) ---


@pytest.mark.req("REQ-YG-578")
def test_preflight_vision_disabled_is_noop(monkeypatch):
    monkeypatch.setenv("PROVIDER", "deepseek")
    tools = _demo_tools()
    assert tools.preflight_vision({"vision_fallback": False}) == {}


@pytest.mark.req("REQ-YG-578")
def test_preflight_vision_enabled_bad_provider_raises(monkeypatch):
    monkeypatch.setenv("PROVIDER", "deepseek")
    tools = _demo_tools()
    with pytest.raises(ValueError, match="deepseek"):
        tools.preflight_vision({"vision_fallback": True})


# --- Demo helpers: partition (R-1, R-4) ---


def _chunks(spec):
    return [{"index": i, "page": p, "text": t} for i, (p, t) in enumerate(spec)]


@pytest.mark.req("REQ-YG-578")
def test_partition_splits_text_and_empty():
    tools = _demo_tools()
    out = tools.partition_chunks(
        {"chunks": _chunks([(1, "  "), (2, "words")]), "vision_fallback": False}
    )
    assert [c["page"] for c in out["text_chunks"]] == [2]
    assert [c["page"] for c in out["empty_chunks"]] == [1]
    assert out["chunks"] == out["text_chunks"]
    assert out["text_seen"] is True
    assert out["vision_route"] == "direct"


@pytest.mark.req("REQ-YG-578")
def test_partition_routes_vision_when_enabled():
    tools = _demo_tools()
    out = tools.partition_chunks(
        {"chunks": _chunks([(1, ""), (2, "x")]), "vision_fallback": True}
    )
    assert out["vision_route"] == "vision"


@pytest.mark.req("REQ-YG-578")
def test_partition_text_seen_accumulates_across_windows():
    tools = _demo_tools()
    out = tools.partition_chunks(
        {"chunks": _chunks([(11, "")]), "vision_fallback": False, "text_seen": True}
    )
    assert out["text_seen"] is True
    out2 = tools.partition_chunks(
        {"chunks": _chunks([(1, "")]), "vision_fallback": False}
    )
    assert out2["text_seen"] is False


# --- Demo helpers: gate_render (R-4, AC-07) ---


def _render_state(results, empty_pages, lo=1, hi=10):
    return {
        "render_results": results,
        "empty_chunks": [{"page": p, "text": ""} for p in empty_pages],
        "batch_start": lo,
        "batch_end": hi,
    }


@pytest.mark.req("REQ-YG-578")
def test_gate_render_error_entry_raises():
    tools = _demo_tools()
    state = _render_state(
        [{"_map_index": 0, "_error": "pdftoppm exploded"}], empty_pages=[1]
    )
    with pytest.raises(ValueError, match="render"):
        tools.gate_render(state)


@pytest.mark.req("REQ-YG-578")
def test_gate_render_filters_stale_and_verifies_membership():
    tools = _demo_tools()
    state = _render_state(
        [
            {"_map_index": 0, "page": 40, "image": "tmp/pages/p40.png"},
            {"_map_index": 1, "page": 3, "image": "tmp/pages/p3.png"},
        ],
        empty_pages=[3],
    )
    out = tools.gate_render(state)
    assert [r["page"] for r in out["renders"]] == [3]
    bad = _render_state(
        [{"_map_index": 0, "page": 5, "image": "tmp/pages/p5.png"}], empty_pages=[3]
    )
    with pytest.raises(ValueError, match="page 5"):
        tools.gate_render(bad)


@pytest.mark.req("REQ-YG-578")
def test_gate_render_duplicate_page_raises():
    tools = _demo_tools()
    state = _render_state(
        [
            {"_map_index": 0, "page": 3, "image": "a.png"},
            {"_map_index": 1, "page": 3, "image": "b.png"},
        ],
        empty_pages=[3],
    )
    with pytest.raises(ValueError, match="duplicate"):
        tools.gate_render(state)


# --- Demo helpers: transcribe_render subnode (R-2 wiring) ---


@pytest.mark.req("REQ-YG-578")
def test_transcribe_render_calls_shared_helper():
    tools = _demo_tools()
    vt = _vision()
    with patch.object(
        vt, "transcribe_page", return_value=vt.PageTranscription(page=3, text="hi")
    ) as spy:
        out = tools.transcribe_render({"render": {"page": 3, "image": "p3.png"}})
    assert spy.call_args.args[0] == "p3.png"
    assert spy.call_args.args[1] == 3
    assert out["transcription"] == {"page": 3, "text": "hi", "is_blank": False}


# --- Demo helpers: merge_vision (R-4, AC-06/07/08) ---


def _merge_state(transcriptions, text_pages, empty_pages, lo=1, hi=10):
    return {
        "transcriptions": transcriptions,
        "text_chunks": [{"page": p, "text": f"text {p}"} for p in text_pages],
        "empty_chunks": [{"page": p, "text": ""} for p in empty_pages],
        "batch_start": lo,
        "batch_end": hi,
    }


def _t(page, text, blank=False, idx=0):
    return {"_map_index": idx, "page": page, "text": text, "is_blank": blank}


@pytest.mark.req("REQ-YG-578")
def test_merge_vision_merges_sorted_by_page():
    tools = _demo_tools()
    out = tools.merge_vision(
        _merge_state([_t(1, "one"), _t(3, "three", idx=1)], [2, 4], [1, 3])
    )
    assert [c["page"] for c in out["chunks"]] == [1, 2, 3, 4]
    assert out["chunks"][0]["text"] == "one"
    assert out["chunks"][1]["text"] == "text 2"


@pytest.mark.req("REQ-YG-578")
def test_merge_vision_drops_blank_transcriptions():
    tools = _demo_tools()
    out = tools.merge_vision(
        _merge_state([_t(1, "", blank=True), _t(3, "x", idx=1)], [2], [1, 3])
    )
    assert [c["page"] for c in out["chunks"]] == [2, 3]


@pytest.mark.req("REQ-YG-578")
def test_merge_vision_error_entry_raises():
    tools = _demo_tools()
    state = _merge_state([{"_map_index": 0, "_error": "vision timeout"}], [2], [1])
    with pytest.raises(ValueError, match="transcri"):
        tools.merge_vision(state)


@pytest.mark.req("REQ-YG-578")
def test_merge_vision_filters_stale_window_entries():
    tools = _demo_tools()
    out = tools.merge_vision(
        _merge_state([_t(40, "stale"), _t(1, "fresh", idx=1)], [2], [1])
    )
    assert [c["page"] for c in out["chunks"]] == [1, 2]


@pytest.mark.req("REQ-YG-578")
def test_merge_vision_unknown_page_raises():
    tools = _demo_tools()
    with pytest.raises(ValueError, match="page 5"):
        tools.merge_vision(_merge_state([_t(5, "ghost")], [2], [1]))


@pytest.mark.req("REQ-YG-578")
def test_merge_vision_duplicate_page_raises():
    tools = _demo_tools()
    state = _merge_state([_t(1, "a"), _t(1, "b", idx=1)], [2], [1])
    with pytest.raises(ValueError, match="duplicate"):
        tools.merge_vision(state)


# --- Demo helpers: guard_extractable (R-1, AC-03) ---


@pytest.mark.req("REQ-YG-578")
def test_guard_raises_fr774_message_when_ocrless_and_no_flag():
    tools = _demo_tools()
    state = {"pdf": "tmp/scan.pdf", "text_seen": False, "vision_fallback": False}
    with pytest.raises(ValueError, match=GUARD_MATCH):
        tools.guard_extractable(state)


@pytest.mark.req("REQ-YG-578")
def test_guard_passes_when_text_seen():
    tools = _demo_tools()
    assert (
        tools.guard_extractable(
            {"pdf": "x.pdf", "text_seen": True, "vision_fallback": False}
        )
        == {}
    )


@pytest.mark.req("REQ-YG-578")
def test_guard_passes_when_vision_enabled():
    tools = _demo_tools()
    assert (
        tools.guard_extractable(
            {"pdf": "x.pdf", "text_seen": False, "vision_fallback": True}
        )
        == {}
    )


# --- Committed graph artifact wiring (R-3, R-4, AC-09) ---


@pytest.mark.req("REQ-YG-578")
def test_graph_wires_preflight_before_loop_and_guard_before_combine():
    raw = yaml.safe_load(DEMO_GRAPH.read_text())
    edges = [(e["from"], e["to"]) for e in raw["edges"]]
    assert ("gate_probe", "preflight_vision") in edges
    assert ("preflight_vision", "prepare_batch") in edges
    assert raw["loop_exits"]["advance"] == "guard_extractable"
    assert ("guard_extractable", "combine") in edges
    advance_exits = [
        e for e in raw["edges"] if e["from"] == "advance" and "condition" in e
    ]
    assert any(e["to"] == "guard_extractable" for e in advance_exits)


@pytest.mark.req("REQ-YG-578")
def test_graph_routes_partition_between_gate_fetch_and_maps():
    raw = yaml.safe_load(DEMO_GRAPH.read_text())
    edges = [(e["from"], e["to"]) for e in raw["edges"]]
    assert ("gate_fetch", "partition") in edges
    routed = {e["to"] for e in raw["edges"] if e["from"] == "partition"}
    assert routed == {"render_pages", "summarize_pages"}
    conditions = [e["condition"] for e in raw["edges"] if e["from"] == "partition"]
    assert all("vision_route" in c for c in conditions)
    assert ("merge_vision", "summarize_pages") in edges


@pytest.mark.req("REQ-YG-578")
def test_graph_vision_maps_are_bounded_and_retry():
    raw = yaml.safe_load(DEMO_GRAPH.read_text())
    render = raw["nodes"]["render_pages"]
    transcribe = raw["nodes"]["transcribe_pages"]
    assert render["type"] == "map"
    assert render["max_items"] == 10
    assert render["collect"] == "render_results"
    assert "empty_chunks" in render["over"]
    assert render["node"]["on_error"] == "retry"
    assert transcribe["type"] == "map"
    assert transcribe["max_items"] == 10
    assert transcribe["collect"] == "transcriptions"
    assert transcribe["node"]["on_error"] == "retry"


@pytest.mark.req("REQ-YG-578")
def test_readme_states_vision_contract():
    text = README.read_text()
    assert "vision_fallback" in text
    assert "pdftoppm" in text
    assert "google" in text and "anthropic" in text


# --- Compiled-graph witnesses (AC-03, AC-04, AC-08) ---


def _compiled(monkeypatch, total, page_text):
    """Compile the committed graph with mocked poppler."""
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

    from yamlgraph.compile.graph_loader import compile_graph, load_graph_config

    config = load_graph_config(DEMO_GRAPH)
    for node in config.loop_limits:
        config.loop_limits[node] = 100
    return compile_graph(config).compile()


def _fake_prompt(**kwargs):
    prompt = kwargs.get("prompt_name")
    state = kwargs.get("state") or {}
    if prompt == "summarize_page":
        page = state["chunk"]["page"]
        text = state["chunk"]["text"]
        return {"page": page, "summary": f"summary {page}" if text.strip() else ""}
    return "combined book summary"


@pytest.mark.req("REQ-YG-578")
def test_default_image_only_pdf_raises_before_combine(monkeypatch):
    """AC-03: fully OCR-less PDF + no flag -> FR-774 guard, no combine LLM."""
    graph = _compiled(monkeypatch, total=5, page_text=lambda p: "")
    with (
        patch(
            "yamlgraph.node_factory.llm_nodes.execute_prompt", side_effect=_fake_prompt
        ) as llm,
        pytest.raises(ValueError, match=GUARD_MATCH),
    ):
        graph.invoke(
            {"pdf": str(FIXTURE), "vision_fallback": False},
            config={"recursion_limit": 500},
        )
    combine_calls = [
        c for c in llm.call_args_list if c.kwargs.get("prompt_name") != "summarize_page"
    ]
    assert combine_calls == []


@pytest.mark.req("REQ-YG-578")
def test_text_pdf_with_blank_window_completes(monkeypatch):
    """AC-03: blank internal windows stay nonfatal when text exists."""
    graph = _compiled(
        monkeypatch, total=15, page_text=lambda p: f"words {p}" if p > 10 else ""
    )
    with patch(
        "yamlgraph.node_factory.llm_nodes.execute_prompt", side_effect=_fake_prompt
    ):
        result = graph.invoke(
            {"pdf": str(FIXTURE), "vision_fallback": False},
            config={"recursion_limit": 500},
        )
    assert result["book_summary"]
    assert [e["page"] for e in result["all_summaries"]] == list(range(11, 16))


@pytest.mark.req("REQ-YG-578")
def test_vision_unsupported_provider_renders_nothing(monkeypatch):
    """AC-04: preflight fires before any pdftoppm invocation."""
    monkeypatch.setenv("PROVIDER", "deepseek")
    import examples.shared.render_page as rp

    with patch.object(rp, "render_page") as render_spy:
        graph = _compiled(monkeypatch, total=5, page_text=lambda p: "")
        with (
            patch(
                "yamlgraph.node_factory.llm_nodes.execute_prompt",
                side_effect=_fake_prompt,
            ),
            pytest.raises(ValueError, match="deepseek"),
        ):
            graph.invoke(
                {"pdf": str(FIXTURE), "vision_fallback": True},
                config={"recursion_limit": 500},
            )
    assert render_spy.call_count == 0


@pytest.mark.req("REQ-YG-578")
def test_vision_two_batch_loop_no_stale_leak(monkeypatch):
    """AC-08: two OCR-less batches; window filtering blocks stale entries."""
    monkeypatch.setenv("PROVIDER", "google")
    from examples.shared import render_page as rp
    from examples.shared import vision_tool as vt

    def fake_render(path, page, **kwargs):
        return {"page": page, "image": f"tmp/pages/p{page}.png"}

    def fake_transcribe(image, page, **kwargs):
        return vt.PageTranscription(page=page, text=f"transcript {page}")

    with (
        patch.object(rp, "render_page", side_effect=fake_render) as render_spy,
        patch.object(vt, "transcribe_page", side_effect=fake_transcribe),
    ):
        graph = _compiled(monkeypatch, total=20, page_text=lambda p: "")
        with patch(
            "yamlgraph.node_factory.llm_nodes.execute_prompt",
            side_effect=_fake_prompt,
        ):
            result = graph.invoke(
                {"pdf": str(FIXTURE), "vision_fallback": True},
                config={"recursion_limit": 500},
            )
    assert render_spy.call_count == 20
    pages = [e["page"] for e in result["all_summaries"]]
    assert pages == list(range(1, 21))
    assert result["book_summary"]
