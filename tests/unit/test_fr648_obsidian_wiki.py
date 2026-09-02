"""Tests for FR-648 Obsidian-compatible wiki output.

Tests:
- render_page produces YAML frontmatter + markdown body (REQ-YG-498)
- References rendered as [[wiki_links]] (REQ-YG-498)
- Relationships rendered as linked list (REQ-YG-498)
- Prose fields rendered as sections, not frontmatter (REQ-YG-498)
- Frontmatter is valid YAML (REQ-YG-498)
- render_wiki writes files to output dir (REQ-YG-498)
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


_render = _load("novel_fandom_nodes_render_wiki", "nodes/render_wiki.py")

render_page = _render.render_page
render_wiki = _render.render_wiki


# --- render_page (REQ-YG-498) ---


class TestRenderPageCharacter:
    @pytest.mark.req("REQ-YG-498")
    def test_produces_frontmatter_and_body(self):
        page = {
            "type": "character",
            "id": "kaelen",
            "name": "Kaelen",
            "lane": "dynamic",
            "faction": "ashguard",
            "birth_year": 175,
            "depth": 1,
            "goals": ["Reforge the Emberbrand"],
            "fears": ["That the Ashfall was his fault"],
            "backstory": "Kaelen grew up in the shadow of the Great Forge.",
            "references": ["maren", "voss", "age_of_cinders"],
            "relationships": [
                {"to": "maren", "kind": "mentor", "valence": "trust"},
                {"to": "voss", "kind": "rival", "valence": "enmity"},
            ],
        }
        result = render_page(page)
        assert result.startswith("---\n")
        assert "\n---\n" in result  # frontmatter boundary
        assert "# Kaelen" in result

    @pytest.mark.req("REQ-YG-498")
    def test_references_as_wiki_links(self):
        page = {
            "type": "character",
            "id": "kaelen",
            "name": "Kaelen",
            "lane": "dynamic",
            "references": ["maren", "voss"],
            "backstory": "",
        }
        result = render_page(page)
        assert "[[maren]]" in result
        assert "[[voss]]" in result

    @pytest.mark.req("REQ-YG-498")
    def test_relationships_as_linked_list(self):
        page = {
            "type": "character",
            "id": "kaelen",
            "name": "Kaelen",
            "lane": "dynamic",
            "relationships": [
                {"to": "maren", "kind": "mentor", "valence": "trust"},
            ],
            "backstory": "",
        }
        result = render_page(page)
        assert "[[maren]]" in result
        assert "mentor" in result
        assert "trust" in result

    @pytest.mark.req("REQ-YG-498")
    def test_backstory_in_body_not_frontmatter(self):
        page = {
            "type": "character",
            "id": "kaelen",
            "name": "Kaelen",
            "lane": "dynamic",
            "backstory": "Born under a blood moon.",
        }
        result = render_page(page)
        # Split frontmatter from body
        parts = result.split("---\n", 2)
        frontmatter_str = parts[1]
        body = parts[2]
        fm = yaml.safe_load(frontmatter_str)
        assert "backstory" not in fm  # not in frontmatter
        assert "Born under a blood moon." in body  # in body

    @pytest.mark.req("REQ-YG-498")
    def test_valid_frontmatter_yaml(self):
        page = {
            "type": "character",
            "id": "kaelen",
            "name": "Kaelen",
            "lane": "dynamic",
            "goals": ["goal1"],
            "backstory": "text",
        }
        result = render_page(page)
        parts = result.split("---\n", 2)
        fm = yaml.safe_load(parts[1])
        assert fm["type"] == "character"
        assert fm["id"] == "kaelen"


class TestRenderPageEvent:
    @pytest.mark.req("REQ-YG-498")
    def test_event_renders(self):
        page = {
            "type": "event",
            "id": "age_of_cinders",
            "lane": "dynamic",
            "window": "age_of_cinders",
            "year": 0,
            "scope": "world",
            "participants": ["kaelen", "maren"],
            "consequences": ["The old forge lies dormant"],
        }
        result = render_page(page)
        assert "# age_of_cinders" in result
        assert "[[kaelen]]" in result


class TestRenderPageLocation:
    @pytest.mark.req("REQ-YG-498")
    def test_description_in_body(self):
        page = {
            "type": "location",
            "id": "great_forge",
            "name": "The Great Forge",
            "lane": "dynamic",
            "description": "A vast underground complex.",
        }
        result = render_page(page)
        parts = result.split("---\n", 2)
        fm = yaml.safe_load(parts[1])
        assert "description" not in fm
        assert "A vast underground complex." in parts[2]


class TestRenderPagePremise:
    @pytest.mark.req("REQ-YG-498")
    def test_text_in_body(self):
        page = {
            "type": "premise",
            "id": "ashfall_premise",
            "lane": "dynamic",
            "text": "Two centuries after the Ashfall...",
        }
        result = render_page(page)
        parts = result.split("---\n", 2)
        fm = yaml.safe_load(parts[1])
        assert "text" not in fm
        assert "Two centuries after the Ashfall..." in parts[2]


# --- render_wiki (REQ-YG-498) ---


class TestRenderWiki:
    @pytest.mark.req("REQ-YG-498")
    def test_writes_md_files(self, tmp_path):
        canon_dir = tmp_path / "canon"
        canon_dir.mkdir()
        wiki_dir = tmp_path / "wiki"

        page = {
            "type": "character",
            "id": "kaelen",
            "name": "Kaelen",
            "lane": "dynamic",
            "backstory": "Test backstory.",
        }
        (canon_dir / "kaelen.yaml").write_text(yaml.dump(page), encoding="utf-8")

        render_wiki(str(canon_dir), str(wiki_dir))

        md_file = wiki_dir / "kaelen.md"
        assert md_file.exists()
        content = md_file.read_text(encoding="utf-8")
        assert "# Kaelen" in content
        assert "Test backstory." in content

    @pytest.mark.req("REQ-YG-498")
    def test_creates_output_dir(self, tmp_path):
        canon_dir = tmp_path / "canon"
        canon_dir.mkdir()
        wiki_dir = tmp_path / "wiki"

        page = {
            "type": "rule",
            "id": "test_rule",
            "lane": "dynamic",
            "domain": "magic_system",
            "title": "Test",
            "description": "A rule.",
        }
        (canon_dir / "test_rule.yaml").write_text(yaml.dump(page), encoding="utf-8")

        assert not wiki_dir.exists()
        render_wiki(str(canon_dir), str(wiki_dir))
        assert wiki_dir.exists()
