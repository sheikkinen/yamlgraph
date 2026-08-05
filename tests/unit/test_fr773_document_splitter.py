"""FR-773: shared document splitter manifest + book-summary feeder demo.

Direct splitter tests (REQ-YG-577, judgement AC-01/AC-02): kwargs
contract, page-range slicing, chunk shape, and the explicit failure
contract (unknown mode, missing file, missing/failing poppler binaries,
unparseable page count) — no silent fallback (C-3).

Artifact tests (REQ-YG-574/REQ-YG-576, AC-04/AC-05): the committed
book-summary demo declares the splitter via manifest only, and its
tool_call node resolves inline args to real kwargs.

RED contract: neither the shared splitter nor the demo exists yet.
"""

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.process

FIXTURE = Path("examples/demos/book-summary/fixture.pdf")
DEMO_GRAPH = Path("examples/demos/book-summary/graph.yaml")
MANIFEST = Path("examples/shared/split_document.tool.yaml")

poppler = pytest.mark.skipif(
    shutil.which("pdfinfo") is None or shutil.which("pdftotext") is None,
    reason="poppler not installed",
)


def _split_document():
    from examples.shared.split_document import split_document

    return split_document


# --- Direct splitter contract (REQ-YG-577) ---


@pytest.mark.req("REQ-YG-577")
@poppler
def test_page_mode_returns_one_chunk_per_page():
    result = _split_document()(path=str(FIXTURE))
    assert result["total"] >= 2
    assert len(result["chunks"]) == result["total"]
    for i, chunk in enumerate(result["chunks"]):
        assert chunk["index"] == i
        assert isinstance(chunk["text"], str)
        # FR-775 R-3: single-page chunks carry absolute page identity
        assert set(chunk) == {"index", "text", "page"}
        assert chunk["page"] == i + 1


@pytest.mark.req("REQ-YG-577")
@poppler
def test_page_range_slices_and_reindexes_from_zero():
    full = _split_document()(path=str(FIXTURE))
    sliced = _split_document()(path=str(FIXTURE), start=2, end=2)
    assert len(sliced["chunks"]) == 1
    assert sliced["chunks"][0]["index"] == 0
    assert sliced["chunks"][0]["text"] == full["chunks"][1]["text"]
    assert sliced["total"] == full["total"]


@pytest.mark.req("REQ-YG-577")
def test_unknown_mode_raises_naming_mode():
    with pytest.raises(ValueError, match="mode.*chapter"):
        _split_document()(path=str(FIXTURE), mode="chapter")


@pytest.mark.req("REQ-YG-577")
def test_missing_file_raises_naming_path():
    with pytest.raises(ValueError, match="no-such-book.pdf"):
        _split_document()(path="tmp/no-such-book.pdf")


@pytest.mark.req("REQ-YG-577")
def test_missing_poppler_raises_with_install_hint(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _: None)
    with pytest.raises(ValueError, match="poppler"):
        _split_document()(path=str(FIXTURE))


@pytest.mark.req("REQ-YG-577")
def test_nonzero_subprocess_raises(monkeypatch):
    def failing_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="boom")

    monkeypatch.setattr(subprocess, "run", failing_run)
    with pytest.raises(ValueError, match="pdfinfo"):
        _split_document()(path=str(FIXTURE))


@pytest.mark.req("REQ-YG-577")
def test_unparseable_page_count_raises(monkeypatch):
    def pageless_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, stdout="Title: x\n", stderr="")

    monkeypatch.setattr(subprocess, "run", pageless_run)
    with pytest.raises(ValueError, match="[Pp]age"):
        _split_document()(path=str(FIXTURE))


# --- Committed artifact wiring (AC-04, AC-05) ---


@pytest.mark.req("REQ-YG-574")
def test_demo_declares_splitter_via_manifest_only():
    raw = yaml.safe_load(DEMO_GRAPH.read_text())
    entry = raw["tools"]["split_document"]
    assert set(entry) == {"manifest"}


@pytest.mark.req("REQ-YG-574")
def test_manifest_translates_to_shared_module():
    from yamlgraph.compile.graph_loader import load_graph_config

    config = load_graph_config(DEMO_GRAPH)
    translated = config.tools["split_document"]
    assert translated["type"] == "python"
    assert translated["module"] == "examples.shared.split_document"
    assert translated["function"] == "split_document"


@pytest.mark.req("REQ-YG-576")
def test_committed_split_args_resolve_to_real_kwargs():
    """AC-05: no {} collapse, no literal '{state.' kwarg, kwargs dispatch.

    FR-775 contract evolution: the linear split node was retired; the
    loop's fetch_batch node carries the state-referencing args now.
    """
    from yamlgraph.node_factory import create_tool_call_node

    raw = yaml.safe_load(DEMO_GRAPH.read_text())
    received = {}

    def recorder(**kwargs):
        received.update(kwargs)
        return {"chunks": [], "total": 0}

    node_config = raw["nodes"]["fetch_batch"]
    node = create_tool_call_node(
        "fetch_batch", node_config, {"split_document": recorder}
    )
    node({"pdf": str(FIXTURE), "batch_start": 1, "batch_end": 10})
    assert received.get("path") == str(FIXTURE)
    assert str(received.get("start")) == "1"
    assert str(received.get("end")) == "10"
    for value in received.values():
        assert "{state." not in str(value)


@pytest.mark.req("REQ-YG-577")
def test_fixture_is_committed_and_multipage():
    assert FIXTURE.is_file()
    assert FIXTURE.read_bytes()[:5] == b"%PDF-"
