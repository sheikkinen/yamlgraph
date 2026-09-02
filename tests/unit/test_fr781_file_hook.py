"""FR-781 — macOS file-hook demo: pairing idempotence, filename safety,
confidence gating, vision max_dim downscale, plist/install-script contracts.

RED-first suite. Requirements: REQ-YG-582 (file-hook example),
REQ-YG-583 (vision downscale + schema extension, CAP-217).
"""

from __future__ import annotations

import importlib
import plistlib
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
DEMO = REPO / "examples" / "demos" / "file-hook"
HOOKS = DEMO / "hooks"
PLIST_TEMPLATE = HOOKS / "com.yamlgraph.file-hook.plist.template"
INSTALL_SH = HOOKS / "install-hook.sh"

pytestmark = pytest.mark.process


def _tools():
    return importlib.import_module("examples.demos.file-hook.tools")


def _png(path: Path) -> Path:
    """Write a minimal valid PNG (1x1, pre-encoded) at path."""
    data = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000d4944415478da63fcffff3f0300050201f34e42600000000049454e44ae426082"
    )
    path.write_bytes(data)
    return path


# ─── AC-03: pairing idempotence — the .md twin is the ledger ─────────────


@pytest.mark.req("REQ-YG-582")
def test_find_unpaired_returns_png_without_twin(tmp_path):
    _png(tmp_path / "a.png")
    result = _tools().find_unpaired(str(tmp_path))
    assert [Path(p).name for p in result] == ["a.png"]


@pytest.mark.req("REQ-YG-582")
def test_find_unpaired_skips_png_with_md_twin(tmp_path):
    _png(tmp_path / "a.png")
    (tmp_path / "a.md").write_text("# done\n", encoding="utf-8")
    assert _tools().find_unpaired(str(tmp_path)) == []


@pytest.mark.req("REQ-YG-582")
def test_second_run_is_noop_after_publish(tmp_path, monkeypatch):
    tools = _tools()
    _png(tmp_path / "art.png")
    monkeypatch.setattr(
        tools, "describe_image", lambda *a, **k: _description(confidence="high")
    )
    first = tools.find_unpaired(str(tmp_path))
    assert len(first) == 1
    tools.process_artwork(first[0])
    assert tools.find_unpaired(str(tmp_path)) == []


# ─── AC-04: filename safety and collision policy ─────────────────────────


@pytest.mark.req("REQ-YG-582")
@pytest.mark.parametrize(
    "title",
    ["../escape", "a/b", "a\\b", "", ".", "..", "x\x00y", "x\ny"],
)
def test_safe_basename_rejects_or_transforms_unsafe(title):
    tools = _tools()
    result = tools.safe_basename(title)
    if result is not None:
        assert "/" not in result and "\\" not in result
        assert result not in {"", ".", ".."}
        assert not any(ord(c) < 32 for c in result)


@pytest.mark.req("REQ-YG-582")
def test_safe_basename_confined_to_watched_dir(tmp_path):
    tools = _tools()
    name = tools.safe_basename("../../outside")
    if name is not None:
        assert (tmp_path / f"{name}.md").resolve().is_relative_to(tmp_path.resolve())


@pytest.mark.req("REQ-YG-582")
def test_collision_appends_numeric_suffix(tmp_path, monkeypatch):
    tools = _tools()
    (tmp_path / "Same Title.md").write_text("existing\n", encoding="utf-8")
    (tmp_path / "Same Title.png").write_bytes(b"other")
    src = _png(tmp_path / "new.png")
    monkeypatch.setattr(
        tools,
        "describe_image",
        lambda *a, **k: _description(title="Same Title", confidence="high"),
    )
    result = tools.process_artwork(str(src))
    assert result["status"] == "published"
    assert (tmp_path / "Same Title.md").read_text(encoding="utf-8") == "existing\n"
    assert (tmp_path / "Same Title-2.md").exists()
    assert (tmp_path / "Same Title-2.png").exists()


@pytest.mark.req("REQ-YG-582")
def test_unsafe_title_leaves_source_unmodified(tmp_path, monkeypatch):
    tools = _tools()
    src = _png(tmp_path / "orig.png")
    before = src.read_bytes()
    monkeypatch.setattr(
        tools,
        "describe_image",
        lambda *a, **k: _description(title="..", confidence="high"),
    )
    result = tools.process_artwork(str(src))
    assert result["status"] != "published"
    assert src.exists() and src.read_bytes() == before
    assert list(tmp_path.glob("*.md")) == []


# ─── AC-05: confidence gate — only "high" publishes ──────────────────────


def _description(title="A Title", confidence=None):
    vision = importlib.import_module("examples.shared.vision_tool")
    return vision.ImageDescription(
        title=title,
        description="desc",
        tags=["t"],
        quote="q",
        confidence=confidence,
    )


@pytest.mark.req("REQ-YG-582")
@pytest.mark.parametrize("confidence", ["medium", "low", None])
def test_blocked_confidence_writes_nothing(tmp_path, monkeypatch, confidence):
    tools = _tools()
    src = _png(tmp_path / "orig.png")
    monkeypatch.setattr(
        tools, "describe_image", lambda *a, **k: _description(confidence=confidence)
    )
    result = tools.process_artwork(str(src))
    assert result["status"] == "blocked"
    assert src.exists()
    assert list(tmp_path.glob("*.md")) == []
    assert [p.name for p in tmp_path.glob("*.png")] == ["orig.png"]


@pytest.mark.req("REQ-YG-582")
def test_high_confidence_publishes_and_renames(tmp_path, monkeypatch):
    tools = _tools()
    src = _png(tmp_path / "orig.png")
    monkeypatch.setattr(
        tools,
        "describe_image",
        lambda *a, **k: _description(title="Poetic Title", confidence="high"),
    )
    result = tools.process_artwork(str(src))
    assert result["status"] == "published"
    assert not src.exists()
    assert (tmp_path / "Poetic Title.png").exists()
    md = (tmp_path / "Poetic Title.md").read_text(encoding="utf-8")
    assert "Poetic Title" in md and "desc" in md


# ─── AC-06: ImageDescription schema extension ────────────────────────────


@pytest.mark.req("REQ-YG-583")
def test_quote_and_confidence_default_none():
    vision = importlib.import_module("examples.shared.vision_tool")
    d = vision.ImageDescription(title="t", description="d", tags=[])
    assert d.quote is None and d.confidence is None


@pytest.mark.req("REQ-YG-583")
def test_confidence_rejects_out_of_domain_value():
    vision = importlib.import_module("examples.shared.vision_tool")
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        vision.ImageDescription(
            title="t", description="d", tags=[], confidence="certain"
        )


# ─── AC-07/AC-08: max_dim downscale + missing-extra fail-fast ────────────


@pytest.mark.req("REQ-YG-583")
def test_max_dim_downscales_before_encoding(tmp_path):
    PIL_Image = pytest.importorskip("PIL.Image")
    vision = importlib.import_module("examples.shared.vision_tool")
    big = tmp_path / "big.png"
    PIL_Image.new("RGB", (2000, 1000)).save(big)
    full = vision._image_content_part(big)
    small = vision._image_content_part(big, max_dim=512)
    assert len(small["image_url"]["url"]) < len(full["image_url"]["url"])
    import base64
    import io

    b64 = small["image_url"]["url"].split(",", 1)[1]
    img = PIL_Image.open(io.BytesIO(base64.b64decode(b64)))
    assert max(img.size) <= 512


@pytest.mark.req("REQ-YG-583")
def test_max_dim_none_preserves_full_size_path(tmp_path):
    vision = importlib.import_module("examples.shared.vision_tool")
    png = _png(tmp_path / "small.png")
    part = vision._image_content_part(png)
    import base64

    b64 = part["image_url"]["url"].split(",", 1)[1]
    assert base64.b64decode(b64) == png.read_bytes()


@pytest.mark.req("REQ-YG-583")
def test_max_dim_ignored_for_urls_with_warning(caplog):
    vision = importlib.import_module("examples.shared.vision_tool")
    with caplog.at_level("WARNING"):
        part = vision._image_content_part("https://example.com/x.png", max_dim=512)
    assert part["image_url"]["url"] == "https://example.com/x.png"
    assert any("max_dim" in r.message for r in caplog.records)


@pytest.mark.req("REQ-YG-583")
def test_max_dim_without_pillow_fails_fast_naming_extra(tmp_path, monkeypatch):
    vision = importlib.import_module("examples.shared.vision_tool")
    png = _png(tmp_path / "a.png")
    monkeypatch.setattr(vision, "_load_pillow", vision._pillow_missing)
    with pytest.raises(Exception, match=r"yamlgraph\[vision\]"):
        vision._image_content_part(png, max_dim=512)


# ─── AC-10: plist template + install-hook.sh render-only ─────────────────


@pytest.mark.req("REQ-YG-582")
def test_plist_template_contains_required_keys():
    text = PLIST_TEMPLATE.read_text(encoding="utf-8")
    for key in [
        "WatchPaths",
        "ThrottleInterval",
        "WorkingDirectory",
        "StandardOutPath",
        "StandardErrorPath",
        "ProgramArguments",
    ]:
        assert f"<key>{key}</key>" in text, f"missing {key}"


@pytest.mark.req("REQ-YG-582")
def test_install_hook_render_only_substitutes_absolute_paths(tmp_path):
    watched = tmp_path / "watched"
    watched.mkdir()
    out = subprocess.run(
        ["bash", str(INSTALL_SH), "--render-only", str(watched)],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    assert out.returncode == 0, out.stderr
    rendered = plistlib.loads(out.stdout.encode())
    assert rendered["WatchPaths"] == [str(watched)]
    args = rendered["ProgramArguments"]
    assert all(not a.startswith("{{") for a in args)
    assert Path(args[0]).is_absolute()
    assert str(watched) in " ".join(args)
    assert "launchctl load" in out.stderr or "launchctl" in out.stderr


# ─── AC-02 surface: committed graph artifact shape ───────────────────────


@pytest.mark.req("REQ-YG-582")
def test_demo_graph_compiles_with_map_over_unpaired():
    import yaml

    from yamlgraph.compile.graph_loader import load_graph_config

    load_graph_config(str(DEMO / "graph.yaml"))  # must validate
    raw = yaml.safe_load((DEMO / "graph.yaml").read_text(encoding="utf-8"))
    assert any(n["type"] == "map" for n in raw["nodes"].values())
