"""FR-774: book-summary scale hardening (extends FR-773, CAP-218).

Direct splitter tests (REQ-YG-577): pages_per_chunk batching, min_chars
filtering, argument validation, all-empty OCR-less detection (the one
intentional new default failure mode, R-1), all-filtered-by-threshold
rejection (R-4), and the mechanical 418-page witness (R-2/AC-06).

Artifact tests: committed demo graph batches and filters (AC-07), its
map cap covers the reported 418-page case (AC-06), and prompts/README
speak chunk/excerpt semantics with a bounded page budget (R-3/AC-08).

RED contract: the splitter lacks the new kwargs and the demo still
fans out per page.
"""

import math
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.process

FIXTURE = Path("examples/demos/book-summary/fixture.pdf")
DEMO_GRAPH = Path("examples/demos/book-summary/graph.yaml")
PROMPTS = Path("examples/demos/book-summary/prompts")
README = Path("examples/demos/book-summary/README.md")


def _split_document():
    from examples.shared.split_document import split_document

    return split_document


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


# --- Argument validation (AC-02) ---


@pytest.mark.req("REQ-YG-577")
def test_pages_per_chunk_below_one_raises():
    with pytest.raises(ValueError, match="pages_per_chunk"):
        _split_document()(path=str(FIXTURE), pages_per_chunk=0)


@pytest.mark.req("REQ-YG-577")
def test_negative_min_chars_raises():
    with pytest.raises(ValueError, match="min_chars"):
        _split_document()(path=str(FIXTURE), min_chars=-1)


# --- Batching (AC-03) + 418-page witness (R-2, AC-06) ---


@pytest.mark.req("REQ-YG-577")
def test_418_pages_batch_into_42_chunks(monkeypatch):
    calls = _mock_poppler(monkeypatch, 418, lambda p: f"text of page {p}")
    result = _split_document()(path=str(FIXTURE), pages_per_chunk=10)
    assert len(result["chunks"]) == 42
    assert result["total"] == 418
    assert [c["index"] for c in result["chunks"]] == list(range(42))
    spans = [
        (int(c[c.index("-f") + 1]), int(c[c.index("-l") + 1]))
        for c in calls
        if c[0] == "pdftotext"
    ]
    assert len(spans) == 42
    assert spans[0] == (1, 10)
    assert spans[-1] == (411, 418)


@pytest.mark.req("REQ-YG-577")
def test_chunk_text_concatenates_its_span_only(monkeypatch):
    _mock_poppler(monkeypatch, 25, lambda p: f"<p{p}>")
    result = _split_document()(path=str(FIXTURE), pages_per_chunk=10)
    first_chunk = result["chunks"][0]["text"]
    assert "<p1>" in first_chunk and "<p10>" in first_chunk
    assert "<p11>" not in first_chunk
    assert len(result["chunks"]) == 3


@pytest.mark.req("REQ-YG-577")
def test_batching_composes_with_page_range(monkeypatch):
    calls = _mock_poppler(monkeypatch, 100, lambda p: f"<p{p}>")
    result = _split_document()(path=str(FIXTURE), start=5, end=24, pages_per_chunk=10)
    spans = [
        (int(c[c.index("-f") + 1]), int(c[c.index("-l") + 1]))
        for c in calls
        if c[0] == "pdftotext"
    ]
    assert spans == [(5, 14), (15, 24)]
    assert len(result["chunks"]) == 2
    assert result["total"] == 100


# --- min_chars filtering (AC-04, R-4) ---


@pytest.mark.req("REQ-YG-577")
def test_min_chars_drops_and_renumbers(monkeypatch):
    texts = {1: "x" * 50, 2: "ab", 3: "", 4: "y" * 50}
    _mock_poppler(monkeypatch, 4, lambda p: texts[p])
    result = _split_document()(path=str(FIXTURE), min_chars=10)
    assert [c["index"] for c in result["chunks"]] == [0, 1]
    assert result["chunks"][0]["text"].strip() == "x" * 50
    assert result["chunks"][1]["text"].strip() == "y" * 50
    assert result["total"] == 4


@pytest.mark.req("REQ-YG-577")
def test_all_filtered_by_threshold_raises_naming_min_chars(monkeypatch):
    _mock_poppler(monkeypatch, 3, lambda p: "abc")
    with pytest.raises(ValueError, match="min_chars"):
        _split_document()(path=str(FIXTURE), min_chars=100)


# --- OCR-less detection (AC-05, R-1: intentional new default failure) ---


@pytest.mark.req("REQ-YG-577")
def test_all_empty_extraction_raises_scanned_hint_by_default(monkeypatch):
    _mock_poppler(monkeypatch, 5, lambda p: "")
    with pytest.raises(ValueError, match="scanned|image-only") as excinfo:
        _split_document()(path=str(FIXTURE))
    assert "FR-774" in str(excinfo.value)


# --- Committed demo artifact (AC-06, AC-07, AC-08) ---
# FR-775 contract evolution: the linear split node was retired for a
# cursor loop (probe/fetch_batch windows). Batching now happens at the
# fetch window, blank filtering via allow_empty_selection + empty
# per-page summaries; the finite budget is loop_limits x window size.


@pytest.mark.req("REQ-YG-577")
def test_demo_graph_batches_and_filters():
    raw = yaml.safe_load(DEMO_GRAPH.read_text())
    args = raw["nodes"]["fetch_batch"]["args"]
    assert args["pages_per_chunk"] == 1
    assert args["min_chars"] == 0
    assert args["allow_empty_selection"] is True


@pytest.mark.req("REQ-YG-577")
def test_demo_cap_covers_reported_418_page_case():
    raw = yaml.safe_load(DEMO_GRAPH.read_text())
    window = 10  # tools.py BATCH_SIZE window
    budget = raw["loop_limits"]["advance"]
    assert math.ceil(418 / window) <= budget
    assert raw["nodes"]["summarize_pages"]["max_items"] >= window


@pytest.mark.req("REQ-YG-577")
def test_prompts_speak_single_page_honestly():
    # FR-774 pinned excerpt semantics for 10-page chunks; FR-775 fetches
    # one page per chunk, so the prompts must speak per-page truthfully.
    summarize = (PROMPTS / "summarize_page.yaml").read_text().lower()
    combine = (PROMPTS / "combine_summaries.yaml").read_text().lower()
    assert "one page" in summarize
    assert "excerpt" not in summarize
    assert "all_summaries" in combine


@pytest.mark.req("REQ-YG-577")
def test_readme_states_bounded_page_budget():
    readme = README.read_text().lower()
    assert "1000" in readme  # loop_limits 100 x 10-page windows
