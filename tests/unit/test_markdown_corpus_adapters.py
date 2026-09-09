"""FR-1033 RED: bounded local-Markdown corpus adapters.

Fail-closed witnesses for the two defects the judgement named: silent
population loss (a prefix instead of an error) and silent content loss (a
truncation instead of an error), plus the byte-identity freeze that makes a
ledger row provably about the file that was read.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from examples.demos.corpus_census.adapters.markdown_adapters import (
    MD_MAX_CHARS,
    MD_MAX_ITEMS,
    MarkdownItemRef,
    md_discover,
    md_extract,
)
from yamlgraph.tools.tool_slots import resolve_tool_slots

# References examples/ (process boundary, FR-756)
pytestmark = pytest.mark.process

ADAPTER_DIR = Path("examples/demos/corpus_census/adapters")
GRAPH_PATH = Path("examples/demos/corpus_census/graph.yaml")


def _write(folder: Path, name: str, text: str) -> Path:
    path = folder / name
    path.write_text(text, encoding="utf-8")
    return path


def _ref(item: str) -> dict:
    return json.loads(item)


# --- AC-01/03: listing contract ------------------------------------------


@pytest.mark.req("REQ-YG-674")
def test_discover_lists_every_markdown_sorted(tmp_path):
    _write(tmp_path, "b.md", "beta")
    _write(tmp_path, "a.md", "alpha")
    _write(tmp_path, "c.txt", "not markdown")
    (tmp_path / "sub").mkdir()
    _write(tmp_path / "sub", "nested.md", "ignored")

    items = md_discover({"source": str(tmp_path)})

    assert [_ref(i)["path"] for i in items] == [
        str(tmp_path / "a.md"),
        str(tmp_path / "b.md"),
    ]


@pytest.mark.req("REQ-YG-674")
def test_discover_rejects_non_directory(tmp_path):
    target = _write(tmp_path, "a.md", "alpha")
    with pytest.raises(NotADirectoryError):
        md_discover({"source": str(target)})


@pytest.mark.req("REQ-YG-674")
def test_discover_rejects_empty_directory(tmp_path):
    with pytest.raises(ValueError, match="no markdown"):
        md_discover({"source": str(tmp_path)})


# --- AC-02: fail closed on population, never a prefix --------------------


@pytest.mark.req("REQ-YG-674")
def test_discover_fails_closed_over_ceiling(tmp_path):
    for i in range(MD_MAX_ITEMS + 1):
        _write(tmp_path, f"f{i:04d}.md", "x")

    with pytest.raises(ValueError) as excinfo:
        md_discover({"source": str(tmp_path)})

    message = str(excinfo.value)
    assert str(MD_MAX_ITEMS + 1) in message, "error must name the observed count"
    assert str(MD_MAX_ITEMS) in message, "error must name the ceiling"


# --- AC-04: deterministic identity ---------------------------------------


@pytest.mark.req("REQ-YG-674")
def test_item_ref_round_trips_deterministically(tmp_path):
    body = "invariant: never rename a node id — ünïcödé ✓\n"
    path = _write(tmp_path, "ünïcödé.md", body)

    first = md_discover({"source": str(tmp_path)})
    second = md_discover({"source": str(tmp_path)})
    assert first == second, "serialization must be deterministic"

    ref = MarkdownItemRef.model_validate_json(first[0])
    raw = path.read_bytes()
    assert ref.path == str(path)
    assert ref.bytes == len(raw)
    assert ref.sha256 == hashlib.sha256(raw).hexdigest()


# --- AC-05: mutation between discovery and extraction --------------------


@pytest.mark.req("REQ-YG-674")
def test_extract_detects_byte_count_change(tmp_path):
    path = _write(tmp_path, "a.md", "original")
    item = md_discover({"source": str(tmp_path)})[0]
    path.write_text("original plus more", encoding="utf-8")

    with pytest.raises(ValueError, match="bytes"):
        md_extract({"item": item})


@pytest.mark.req("REQ-YG-674")
def test_extract_detects_digest_change_at_equal_length(tmp_path):
    path = _write(tmp_path, "a.md", "aaaa")
    item = md_discover({"source": str(tmp_path)})[0]
    path.write_text("bbbb", encoding="utf-8")  # same byte count, different bytes

    with pytest.raises(ValueError, match="sha256"):
        md_extract({"item": item})


@pytest.mark.req("REQ-YG-674")
def test_extract_rejects_malformed_item_reference():
    with pytest.raises(ValueError):
        md_extract({"item": "not json at all"})


@pytest.mark.req("REQ-YG-674")
def test_extract_rejects_missing_file(tmp_path):
    path = _write(tmp_path, "a.md", "alpha")
    item = md_discover({"source": str(tmp_path)})[0]
    path.unlink()

    with pytest.raises(FileNotFoundError):
        md_extract({"item": item})


# --- AC-06: reject oversize, never truncate ------------------------------


@pytest.mark.req("REQ-YG-674")
def test_extract_fails_closed_on_oversize_file(tmp_path):
    _write(tmp_path, "big.md", "x" * (MD_MAX_CHARS + 1))
    item = md_discover({"source": str(tmp_path)})[0]

    with pytest.raises(ValueError) as excinfo:
        md_extract({"item": item})

    message = str(excinfo.value)
    assert "big.md" in message, "error must name the path"
    assert str(MD_MAX_CHARS + 1) in message, "error must name the observed count"
    assert str(MD_MAX_CHARS) in message, "error must name the ceiling"


@pytest.mark.req("REQ-YG-674")
def test_extract_returns_whole_content_at_ceiling(tmp_path):
    body = "y" * MD_MAX_CHARS
    _write(tmp_path, "exact.md", body)
    item = md_discover({"source": str(tmp_path)})[0]

    assert md_extract({"item": item}) == body


# --- AC-07: replacement decoding only after identity verification --------


@pytest.mark.req("REQ-YG-674")
def test_invalid_utf8_decodes_with_replacement_after_identity_check(tmp_path):
    path = tmp_path / "bad.md"
    path.write_bytes(b"rule: never \xff\xfe rename\n")

    item = md_discover({"source": str(tmp_path)})[0]
    text = md_extract({"item": item})

    assert "rule: never" in text
    assert "�" in text, "invalid bytes decode to the replacement character"


@pytest.mark.req("REQ-YG-674")
def test_identity_is_checked_before_decoding(tmp_path):
    """A mutated invalid-UTF-8 file must raise on identity, not decode."""
    path = tmp_path / "bad.md"
    path.write_bytes(b"\xff\xfe original")
    item = md_discover({"source": str(tmp_path)})[0]
    path.write_bytes(b"\xff\xfe changed to something longer")

    with pytest.raises(ValueError, match="bytes|sha256"):
        md_extract({"item": item})


# --- AC-09: manifest declarations ----------------------------------------


@pytest.mark.req("REQ-YG-674")
@pytest.mark.parametrize(
    ("manifest", "function"),
    [
        ("md-discover.tool.yaml", "md_discover"),
        ("md-extract.tool.yaml", "md_extract"),
    ],
)
def test_manifest_declares_python_runtime(manifest, function):
    spec = yaml.safe_load((ADAPTER_DIR / manifest).read_text(encoding="utf-8"))
    assert spec["runtime"]["type"] == "python"
    assert spec["runtime"]["path"] == "markdown_adapters.py"
    assert spec["runtime"]["function"] == function


# --- AC-08: the real slot-binding path -----------------------------------


@pytest.mark.req("REQ-YG-674")
def test_manifests_resolve_through_slot_binding_and_chain(tmp_path):
    """Bind both manifests the way the CLI does, then run discover→extract."""
    graph = yaml.safe_load(GRAPH_PATH.read_text(encoding="utf-8"))
    resolved = resolve_tool_slots(
        graph["tools"],
        {
            "discover": str(ADAPTER_DIR / "md-discover.tool.yaml"),
            "extract": str(ADAPTER_DIR / "md-extract.tool.yaml"),
        },
        Path("."),
    )

    # Resolution flattens the manifest's runtime block into the tool entry
    # and drops the slot declaration entirely.
    assert "slot" not in resolved["discover"], "the slot declaration is replaced"
    assert resolved["discover"]["type"] == "python"
    assert resolved["discover"]["function"] == "md_discover"
    assert resolved["extract"]["function"] == "md_extract"
    assert Path(resolved["extract"]["path"]).name == "markdown_adapters.py"

    _write(tmp_path, "one.md", "first rule")
    _write(tmp_path, "two.md", "second rule")

    items = md_discover({"source": str(tmp_path)})
    contents = [md_extract({"item": item}) for item in items]

    assert len(contents) == len(items) == 2, "row count must equal item count"
    assert contents == ["first rule", "second rule"]
