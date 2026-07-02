"""Tests for FR-643v2 novel_fandom world expansion (deepening + red links).

Tests:
- Schema additions: backstory, depth fields (REQ-YG-494)
- select_thin deterministic thinness filter (REQ-YG-495)
- collect_red_links dedup (REQ-YG-495)
- validate_pages gate (REQ-YG-495)
- persist_pages Pydantic validation + atomic write (REQ-YG-495)
- reload_canon runtime reload (REQ-YG-495)
- worldgen.yaml lints clean (REQ-YG-494)
- Seed canon lane:dynamic (REQ-YG-494)
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


_canon = _load("novel_fandom_schema_canon_v2", "schema/canon.py")
_select = _load("novel_fandom_nodes_select_thin", "nodes/select_thin.py")
_collect = _load("novel_fandom_nodes_collect_red_links", "nodes/collect_red_links.py")
_validate = _load("novel_fandom_nodes_validate_pages", "nodes/validate_pages.py")
_persist = _load("novel_fandom_nodes_persist_pages", "nodes/persist_pages.py")
_persist = _load("novel_fandom_nodes_persist_pages", "nodes/persist_pages.py")
_reload = _load("novel_fandom_nodes_reload_canon", "nodes/reload_canon.py")

Character = _canon.Character
Event = _canon.Event
Faction = _canon.Faction
Location = _canon.Location
Rule = _canon.Rule
PAGE_MODELS = _canon.PAGE_MODELS
validate_page = _canon.validate_page
select_thin = _select.select_thin
collect_red_links = _collect.collect_red_links
validate_pages = _validate.validate_pages
reload_canon = _reload.reload_canon


# --- Schema additions (REQ-YG-494) ---


class TestSchemaAdditions:
    @pytest.mark.req("REQ-YG-494")
    def test_character_has_backstory_field(self):
        c = Character(id="test", lane="dynamic", name="Test")
        assert c.backstory == ""

    @pytest.mark.req("REQ-YG-494")
    def test_character_backstory_accepts_prose(self):
        c = Character(
            id="test",
            lane="dynamic",
            name="Test",
            backstory="Born in the shadow of the old forge, he knew only ash.",
        )
        assert "forge" in c.backstory

    @pytest.mark.req("REQ-YG-494")
    def test_character_has_depth_field(self):
        c = Character(id="test", lane="dynamic", name="Test")
        assert c.depth == 0

    @pytest.mark.req("REQ-YG-494")
    def test_event_has_depth_field(self):
        e = Event(id="test", lane="dynamic")
        assert e.depth == 0

    @pytest.mark.req("REQ-YG-494")
    def test_faction_has_depth_field(self):
        f = Faction(id="test", lane="dynamic", name="Test")
        assert f.depth == 0

    @pytest.mark.req("REQ-YG-494")
    def test_location_has_depth_field(self):
        loc = Location(id="test", lane="dynamic", name="Test")
        assert loc.depth == 0

    @pytest.mark.req("REQ-YG-494")
    def test_rule_has_depth_field(self):
        r = Rule(id="test", lane="dynamic", domain="magic_system", title="Test")
        assert r.depth == 0

    @pytest.mark.req("REQ-YG-494")
    def test_depth_roundtrips_through_dict(self):
        c = Character(id="test", lane="dynamic", name="Test", depth=2)
        d = c.model_dump()
        assert d["depth"] == 2
        c2 = Character(**d)
        assert c2.depth == 2


# --- select_thin (REQ-YG-495) ---


class TestSelectThin:
    @pytest.mark.req("REQ-YG-495")
    def test_character_thin_no_backstory(self):
        pages = {
            "hero": {
                "type": "character",
                "id": "hero",
                "name": "Hero",
                "backstory": "",
                "triggers": ["x"],
                "relationships": [
                    {"to": "a", "kind": "ally", "valence": "trust"},
                    {"to": "b", "kind": "rival", "valence": "enmity"},
                ],
                "depth": 0,
            },
        }
        result = select_thin({"canon_pages": pages, "max_depth": 2})
        assert not result["done"]
        assert len(result["thin_entities"]) == 1
        assert "backstory" in result["thin_entities"][0]["thin_reason"]

    @pytest.mark.req("REQ-YG-495")
    def test_character_not_thin_when_rich(self):
        pages = {
            "hero": {
                "type": "character",
                "id": "hero",
                "name": "Hero",
                "backstory": " ".join(["word"] * 60),
                "triggers": ["provoked"],
                "relationships": [
                    {"to": "a", "kind": "ally", "valence": "trust"},
                    {"to": "b", "kind": "rival", "valence": "enmity"},
                ],
                "depth": 0,
            },
        }
        result = select_thin({"canon_pages": pages, "max_depth": 2})
        assert result["done"]

    @pytest.mark.req("REQ-YG-495")
    def test_skips_pages_at_max_depth(self):
        pages = {
            "deep": {
                "type": "character",
                "id": "deep",
                "name": "Deep",
                "backstory": "",
                "triggers": [],
                "relationships": [],
                "depth": 2,
            },
        }
        result = select_thin({"canon_pages": pages, "max_depth": 2})
        assert result["done"]
        assert len(result["thin_entities"]) == 0

    @pytest.mark.req("REQ-YG-495")
    def test_sorted_by_thin_score(self):
        pages = {
            "a": {
                "type": "character",
                "id": "a",
                "name": "A",
                "backstory": "",
                "triggers": ["x"],
                "relationships": [
                    {"to": "b", "kind": "x", "valence": "y"},
                    {"to": "c", "kind": "x", "valence": "y"},
                ],
                "depth": 0,
            },
            "b": {
                "type": "character",
                "id": "b",
                "name": "B",
                "backstory": "",
                "triggers": [],
                "relationships": [],
                "depth": 0,
            },
        }
        result = select_thin({"canon_pages": pages, "max_depth": 2})
        # b has 3 thin reasons, a has 1 — b should come first
        assert result["thin_entities"][0]["entity_id"] == "b"

    @pytest.mark.req("REQ-YG-495")
    def test_event_thin_no_consequences(self):
        pages = {
            "ev": {
                "type": "event",
                "id": "ev",
                "consequences": [],
                "participants": ["a", "b"],
                "depth": 0,
            },
        }
        result = select_thin({"canon_pages": pages, "max_depth": 2})
        assert not result["done"]

    @pytest.mark.req("REQ-YG-495")
    def test_faction_thin_few_members(self):
        pages = {
            "fac": {
                "type": "faction",
                "id": "fac",
                "name": "F",
                "members": ["one"],
                "depth": 0,
            },
        }
        result = select_thin({"canon_pages": pages, "max_depth": 2})
        assert not result["done"]

    @pytest.mark.req("REQ-YG-495")
    def test_location_thin_no_atmosphere(self):
        pages = {
            "loc": {
                "type": "location",
                "id": "loc",
                "name": "L",
                "atmosphere": [],
                "sensory": [],
                "depth": 0,
            },
        }
        result = select_thin({"canon_pages": pages, "max_depth": 2})
        assert not result["done"]

    @pytest.mark.req("REQ-YG-495")
    def test_skips_premise_synopsis_rule(self):
        pages = {
            "p": {"type": "premise", "id": "p", "depth": 0},
            "s": {"type": "synopsis", "id": "s", "depth": 0},
            "r": {"type": "rule", "id": "r", "depth": 0},
        }
        result = select_thin({"canon_pages": pages, "max_depth": 2})
        assert result["done"]


# --- collect_red_links (REQ-YG-495) ---


class TestCollectRedLinks:
    @pytest.mark.req("REQ-YG-495")
    def test_dedup_by_id(self):
        deepened = [
            {
                "new_entities": [
                    {
                        "id": "brennan",
                        "type": "character",
                        "name": "Brennan",
                        "summary": "mentor",
                    }
                ]
            },
            {
                "new_entities": [
                    {
                        "id": "brennan",
                        "type": "character",
                        "name": "Brennan",
                        "summary": "old forge-master",
                    }
                ]
            },
        ]
        result = collect_red_links(
            {
                "deepened": deepened,
                "canon_pages": {},
            }
        )
        assert result["red_link_count"] == 1

    @pytest.mark.req("REQ-YG-495")
    def test_filters_existing_pages(self):
        deepened = [
            {
                "new_entities": [
                    {
                        "id": "kaelen",
                        "type": "character",
                        "name": "Kaelen",
                        "summary": "exists",
                    }
                ]
            },
        ]
        result = collect_red_links(
            {
                "deepened": deepened,
                "canon_pages": {"kaelen": {"type": "character", "id": "kaelen"}},
            }
        )
        assert result["red_link_count"] == 0

    @pytest.mark.req("REQ-YG-495")
    def test_multiple_new_entities(self):
        deepened = [
            {
                "new_entities": [
                    {"id": "brennan", "type": "character", "name": "B", "summary": "x"},
                    {
                        "id": "high_forge",
                        "type": "location",
                        "name": "HF",
                        "summary": "y",
                    },
                ]
            },
        ]
        result = collect_red_links(
            {
                "deepened": deepened,
                "canon_pages": {},
            }
        )
        assert result["red_link_count"] == 2


# --- collect_red_links + reflection (REQ-YG-496, FR-646) ---


class TestCollectRedLinksReflexion:
    """AC-4a, AC-7: reflection missing_entities merge into collect_red_links."""

    @pytest.mark.req("REQ-YG-496")
    def test_reflection_missing_entities_added(self):
        """AC-4a: mock reflection with dragonsteel → collect includes it."""
        result = collect_red_links(
            {
                "deepened": [],
                "canon_pages": {"kaelen": {"type": "character"}},
                "reflection": {
                    "missing_entities": [
                        {
                            "id": "dragonsteel",
                            "type": "rule",
                            "name": "Dragonsteel",
                            "summary": "Rare forging material",
                            "cited_in": ["kaelen", "emberbrand_rule"],
                        }
                    ],
                    "verdict": "Dragonsteel lacks a page.",
                },
            }
        )
        assert result["red_link_count"] == 1
        assert result["red_links"][0]["id"] == "dragonsteel"

    @pytest.mark.req("REQ-YG-496")
    def test_both_sources_merged(self):
        """AC-7: new_entities from deepen + missing_entities from reflection."""
        result = collect_red_links(
            {
                "deepened": [
                    {
                        "new_entities": [
                            {
                                "id": "brennan",
                                "type": "character",
                                "name": "B",
                                "summary": "x",
                            }
                        ]
                    }
                ],
                "canon_pages": {},
                "reflection": {
                    "missing_entities": [
                        {
                            "id": "dragonsteel",
                            "type": "rule",
                            "name": "D",
                            "summary": "y",
                        }
                    ],
                    "verdict": "ok",
                },
            }
        )
        ids = {r["id"] for r in result["red_links"]}
        assert ids == {"brennan", "dragonsteel"}
        assert result["red_link_count"] == 2

    @pytest.mark.req("REQ-YG-496")
    def test_reflection_dedup_with_deepened(self):
        """Reflection names same entity as deepen — no duplicate."""
        result = collect_red_links(
            {
                "deepened": [
                    {
                        "new_entities": [
                            {
                                "id": "brennan",
                                "type": "character",
                                "name": "B",
                                "summary": "x",
                            }
                        ]
                    }
                ],
                "canon_pages": {},
                "reflection": {
                    "missing_entities": [
                        {
                            "id": "brennan",
                            "type": "character",
                            "name": "Brennan",
                            "summary": "z",
                        }
                    ],
                    "verdict": "ok",
                },
            }
        )
        assert result["red_link_count"] == 1

    @pytest.mark.req("REQ-YG-496")
    def test_reflection_filters_existing_pages(self):
        """Reflection names entity that already has a page — excluded."""
        result = collect_red_links(
            {
                "deepened": [],
                "canon_pages": {"kaelen": {"type": "character"}},
                "reflection": {
                    "missing_entities": [
                        {
                            "id": "kaelen",
                            "type": "character",
                            "name": "K",
                            "summary": "x",
                        }
                    ],
                    "verdict": "ok",
                },
            }
        )
        assert result["red_link_count"] == 0

    @pytest.mark.req("REQ-YG-496")
    def test_no_reflection_still_works(self):
        """No reflection in state — original behavior unchanged."""
        result = collect_red_links(
            {
                "deepened": [
                    {
                        "new_entities": [
                            {
                                "id": "brennan",
                                "type": "character",
                                "name": "B",
                                "summary": "x",
                            }
                        ]
                    }
                ],
                "canon_pages": {},
            }
        )
        assert result["red_link_count"] == 1

    @pytest.mark.req("REQ-YG-496")
    def test_reflection_empty_missing_entities(self):
        """Reflection with empty missing_entities — no crash."""
        result = collect_red_links(
            {
                "deepened": [],
                "canon_pages": {},
                "reflection": {"missing_entities": [], "verdict": "All good."},
            }
        )
        assert result["red_link_count"] == 0


# --- validate_pages gate (REQ-YG-495) ---


class TestValidatePages:
    @pytest.mark.req("REQ-YG-495")
    def test_valid_refs(self):
        result = validate_pages(
            {
                "canon_pages": {"kaelen": {"type": "character"}},
                "deepened": [
                    {
                        "updated_page": {
                            "id": "kaelen",
                            "type": "character",
                            "references": ["maren"],
                        }
                    }
                ],
                "skeletons": [{"id": "maren", "type": "character", "references": []}],
            }
        )
        assert result["gate_result"]["valid"]

    @pytest.mark.req("REQ-YG-495")
    def test_orphan_ref_fails(self):
        result = validate_pages(
            {
                "canon_pages": {},
                "deepened": [
                    {
                        "updated_page": {
                            "id": "kaelen",
                            "type": "character",
                            "references": ["nonexistent"],
                        }
                    }
                ],
                "skeletons": [],
            }
        )
        assert not result["gate_result"]["valid"]
        assert "orphan ref" in result["gate_result"]["violations"][0]

    @pytest.mark.req("REQ-YG-495")
    def test_self_reference_allowed(self):
        result = validate_pages(
            {
                "canon_pages": {},
                "deepened": [
                    {
                        "updated_page": {
                            "id": "kaelen",
                            "type": "character",
                            "references": ["kaelen"],
                        }
                    }
                ],
                "skeletons": [],
            }
        )
        assert result["gate_result"]["valid"]


# --- persist_pages (REQ-YG-495) ---


class TestPersistPages:
    @pytest.mark.req("REQ-YG-495")
    def test_validates_before_writing(self, tmp_path):
        canon_dir = tmp_path / "canon"
        canon_dir.mkdir()
        # Invalid page (missing required 'name' for character)
        state = {
            "deepened": [
                {
                    "updated_page": {
                        "id": "bad",
                        "type": "character",
                        "lane": "dynamic",
                        # Missing 'name' — fails Pydantic but FR-649 persists anyway
                    }
                }
            ],
            "skeletons": [],
        }
        result = _persist._persist_impl(state, canon_dir, PAGE_MODELS)
        # FR-649: invalid pages are now persisted with warning (not dropped)
        assert result["written_count"] == 1

    @pytest.mark.req("REQ-YG-495")
    def test_writes_valid_page(self, tmp_path):
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
                        "backstory": "A brave soul.",
                    }
                }
            ],
            "skeletons": [],
        }
        result = _persist._persist_impl(state, canon_dir, PAGE_MODELS)
        assert result["written_count"] == 1
        # FR-650: pages now land in type subfolder
        written = yaml.safe_load((canon_dir / "character" / "hero.yaml").read_text())
        assert written["name"] == "Hero"

    @pytest.mark.req("REQ-YG-495")
    def test_skeleton_no_overwrite(self, tmp_path):
        canon_dir = tmp_path / "canon"
        canon_dir.mkdir()
        # Pre-existing page
        (canon_dir / "existing.yaml").write_text("id: existing\ntype: character\n")
        state = {
            "deepened": [],
            "skeletons": [
                {
                    "id": "existing",
                    "type": "character",
                    "lane": "dynamic",
                    "name": "New",
                    "depth": 2,
                }
            ],
        }
        result = _persist._persist_impl(state, canon_dir, PAGE_MODELS)
        assert result["written_count"] == 0
        # Original content preserved
        content = (canon_dir / "existing.yaml").read_text()
        assert "New" not in content


# --- reload_canon (REQ-YG-495) ---


class TestReloadCanon:
    @pytest.mark.req("REQ-YG-495")
    def test_reads_canon_dir(self):
        result = reload_canon({})
        assert result["canon_count"] >= 10
        assert "hilde" in result["canon_pages"]
        assert result["synopsis_text"]  # synopsis text extracted

    @pytest.mark.req("REQ-YG-495")
    def test_synopsis_text_populated(self):
        result = reload_canon({})
        assert (
            "Hilde" in result["synopsis_text"]
            or "flood" in result["synopsis_text"].lower()
        )


# --- Seed canon lane (REQ-YG-494) ---


class TestSeedCanon:
    @pytest.mark.req("REQ-YG-494")
    def test_all_seed_pages_dynamic(self):
        canon_dir = NOVEL_FANDOM_DIR / "canon"
        for f in canon_dir.glob("**/*.yaml"):
            data = yaml.safe_load(f.read_text())
            assert data.get("lane") == "dynamic", f"{f.name} is not lane:dynamic"


# --- Graph lint (REQ-YG-494) ---


class TestWorldgenGraph:
    @pytest.mark.req("REQ-YG-494")
    def test_worldgen_yaml_exists(self):
        graph_path = NOVEL_FANDOM_DIR / "worldgen.yaml"
        assert graph_path.exists()

    @pytest.mark.req("REQ-YG-494")
    def test_worldgen_yaml_valid_structure(self):
        graph_path = NOVEL_FANDOM_DIR / "worldgen.yaml"
        data = yaml.safe_load(graph_path.read_text())
        assert data["name"] == "novel-fandom-worldgen"
        assert "reload" in data["nodes"]
        assert "select" in data["nodes"]
        assert "deepen" in data["nodes"]
        assert "collect" in data["nodes"]
        assert "create_skeletons" in data["nodes"]
        assert "gate" in data["nodes"]
        assert "persist" in data["nodes"]

    @pytest.mark.req("REQ-YG-494")
    def test_worldgen_has_loop_limits(self):
        graph_path = NOVEL_FANDOM_DIR / "worldgen.yaml"
        data = yaml.safe_load(graph_path.read_text())
        limits = data.get("loop_limits", {})
        assert "deepen" in limits
        assert "reload" in limits
