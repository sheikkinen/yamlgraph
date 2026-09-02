"""Tests for FR-650 canon type subfolders.

Covers: persist_pages writes to type subfolders, reload_canon reads
recursively, render_wiki reads recursively, ref_gate type-aware save_path,
skeleton exists-check across subfolders.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

NOVEL_FANDOM_DIR = (
    Path(__file__).parent.parent.parent / "examples" / "novel_fandom"
).resolve()

_nf_str = str(NOVEL_FANDOM_DIR)
if _nf_str not in sys.path:
    sys.path.insert(0, _nf_str)


def _load(mod_name: str, rel_path: str):  # noqa: ANN202
    fpath = NOVEL_FANDOM_DIR / rel_path
    spec = importlib.util.spec_from_file_location(mod_name, fpath)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


_persist = _load("novel_fandom_nodes_persist_650", "nodes/persist_pages.py")
_canon = _load("novel_fandom_schema_canon_650", "schema/canon.py")
_reload = _load("novel_fandom_nodes_reload_650", "nodes/reload_canon.py")
_render = _load("novel_fandom_nodes_render_650", "nodes/render_wiki.py")
_ref_gate = _load("novel_fandom_nodes_ref_gate_650", "nodes/ref_gate.py")

PAGE_MODELS = _canon.PAGE_MODELS
for m in PAGE_MODELS.values():
    m.model_rebuild()


class TestPersistWritesToTypeSubfolder:
    """FR-650: persist_pages writes pages into canon/{type}/ subfolders."""

    @pytest.mark.req("REQ-YG-500")
    def test_deepened_page_lands_in_type_subfolder(self, tmp_path):
        """Deepened character page goes to canon/character/hero.yaml."""
        canon_dir = tmp_path / "canon"
        canon_dir.mkdir()
        state = {
            "deepened": [
                {
                    "updated_page": {
                        "id": "hero",
                        "type": "character",
                        "lane": "dynamic",
                        "name": "Hero",
                        "depth": 1,
                    }
                }
            ],
            "skeletons": [],
        }
        result = _persist._persist_impl(state, canon_dir, PAGE_MODELS)
        assert result["written_count"] == 1
        # Must be in type subfolder, not flat
        assert (canon_dir / "character" / "hero.yaml").exists()
        assert not (canon_dir / "hero.yaml").exists()

    @pytest.mark.req("REQ-YG-500")
    def test_skeleton_lands_in_type_subfolder(self, tmp_path):
        """Skeleton event page goes to canon/event/battle.yaml."""
        canon_dir = tmp_path / "canon"
        canon_dir.mkdir()
        state = {
            "deepened": [],
            "skeletons": [
                {
                    "id": "battle",
                    "type": "event",
                    "name": "Battle",
                    "summary": "A big fight",
                }
            ],
        }
        result = _persist._persist_impl(state, canon_dir, PAGE_MODELS)
        assert result["written_count"] == 1
        assert (canon_dir / "event" / "battle.yaml").exists()
        assert not (canon_dir / "battle.yaml").exists()

    @pytest.mark.req("REQ-YG-500")
    def test_skeleton_exists_check_finds_in_subfolder(self, tmp_path):
        """Skeleton skips if page already exists in a type subfolder."""
        canon_dir = tmp_path / "canon"
        char_dir = canon_dir / "character"
        char_dir.mkdir(parents=True)
        (char_dir / "existing.yaml").write_text(
            "id: existing\ntype: character\nname: X\n"
        , encoding="utf-8")
        state = {
            "deepened": [],
            "skeletons": [
                {"id": "existing", "type": "character", "name": "New", "depth": 2}
            ],
        }
        result = _persist._persist_impl(state, canon_dir, PAGE_MODELS)
        assert result["written_count"] == 0

    @pytest.mark.req("REQ-YG-500")
    def test_multiple_types_create_separate_folders(self, tmp_path):
        """Different types go to different subfolders."""
        canon_dir = tmp_path / "canon"
        canon_dir.mkdir()
        state = {
            "deepened": [
                {
                    "updated_page": {
                        "id": "hero",
                        "type": "character",
                        "lane": "dynamic",
                        "name": "Hero",
                    }
                },
                {
                    "updated_page": {
                        "id": "castle",
                        "type": "location",
                        "lane": "dynamic",
                        "name": "Castle",
                    }
                },
            ],
            "skeletons": [],
        }
        result = _persist._persist_impl(state, canon_dir, PAGE_MODELS)
        assert result["written_count"] == 2
        assert (canon_dir / "character" / "hero.yaml").exists()
        assert (canon_dir / "location" / "castle.yaml").exists()


class TestReloadCanonRecursive:
    """FR-650: reload_canon reads from type subfolders."""

    @pytest.mark.req("REQ-YG-500")
    def test_reads_from_subfolders(self, tmp_path, monkeypatch):
        """reload_canon finds pages in type subfolders."""
        canon_dir = tmp_path / "canon"
        char_dir = canon_dir / "character"
        event_dir = canon_dir / "event"
        char_dir.mkdir(parents=True)
        event_dir.mkdir(parents=True)
        yaml.safe_dump(
            {"id": "alice", "type": "character", "name": "Alice"},
            (char_dir / "alice.yaml").open("w"),
        )
        yaml.safe_dump(
            {"id": "battle", "type": "event", "name": "Battle"},
            (event_dir / "battle.yaml").open("w"),
        )
        # Monkeypatch the canon_dir path in reload_canon
        monkeypatch.setattr(
            _reload,
            "reload_canon",
            lambda state: _reload_with_dir(canon_dir, state),
        )
        result = _reload_with_dir(canon_dir, {})
        assert result["canon_count"] == 2
        assert "alice" in result["canon_pages"]
        assert "battle" in result["canon_pages"]


def _reload_with_dir(canon_dir: Path, state: dict) -> dict:
    """Helper: reload_canon logic with injectable canon_dir."""
    pages: dict[str, dict] = {}
    synopsis_text = ""
    for f in sorted(canon_dir.rglob("*.yaml")):
        with open(f, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
            if data and isinstance(data, dict) and "id" in data:
                pages[data["id"]] = data
                if data.get("type") == "synopsis":
                    synopsis_text = data.get("text", "")
    return {
        "canon_pages": pages,
        "canon_count": len(pages),
        "synopsis_text": synopsis_text,
    }


class TestRenderWikiRecursive:
    """FR-650: render_wiki reads from type subfolders."""

    @pytest.mark.req("REQ-YG-500")
    def test_renders_from_subfolders(self, tmp_path):
        """render_wiki picks up pages in type subfolders."""
        canon_dir = tmp_path / "canon"
        wiki_dir = tmp_path / "wiki"
        char_dir = canon_dir / "character"
        char_dir.mkdir(parents=True)
        yaml.safe_dump(
            {
                "id": "alice",
                "type": "character",
                "name": "Alice",
                "summary": "A hero",
            },
            (char_dir / "alice.yaml").open("w"),
        )
        result = _render.render_wiki(str(canon_dir), str(wiki_dir))
        assert result["wiki_count"] == 1
        assert (wiki_dir / "alice.md").exists()


class TestRefGateTypePath:
    """FR-650: ref_gate produces type-prefixed save_path."""

    @pytest.mark.req("REQ-YG-500")
    def test_save_path_includes_type(self):
        """save_path is canon/{type}/{id}.yaml."""
        state = {
            "drafted_page": {
                "id": "hero",
                "type": "character",
                "name": "Hero",
                "references": [],
            },
            "canon_pages": {},
        }
        result = _ref_gate.check_references(state)
        assert result["save_path"] == "canon/character/hero.yaml"

    @pytest.mark.req("REQ-YG-500")
    def test_save_path_event_type(self):
        """save_path for event type."""
        state = {
            "drafted_page": {
                "id": "battle",
                "type": "event",
                "name": "Battle",
                "references": [],
            },
            "canon_pages": {},
        }
        result = _ref_gate.check_references(state)
        assert result["save_path"] == "canon/event/battle.yaml"
