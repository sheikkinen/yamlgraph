"""RED tests for FR-638 novel_fandom plot pathfinder.

Tests:
- retrieve_window deterministic context retrieval (REQ-YG-487)
- Path gate rejects orphan beat references (REQ-YG-488)
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

NOVEL_FANDOM_DIR = (
    Path(__file__).parent.parent.parent / "examples" / "novel_fandom"
).resolve()

_nf_str = str(NOVEL_FANDOM_DIR)
if _nf_str not in sys.path:
    sys.path.insert(0, _nf_str)


def _load(mod_name: str, rel_path: str):  # noqa: ANN202
    """Load a module from examples/novel_fandom by file path."""
    fpath = NOVEL_FANDOM_DIR / rel_path
    spec = importlib.util.spec_from_file_location(mod_name, fpath)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


_retrieve = _load("novel_fandom_nodes_retrieve_window", "nodes/retrieve_window.py")
_path_gate = _load("novel_fandom_nodes_path_gate", "nodes/path_gate.py")

retrieve_window = _retrieve.retrieve_window
check_path_references = _path_gate.check_path_references


# --- Fixtures ---


@pytest.fixture()
def seed_canon() -> dict[str, dict]:
    """Load all seed canon YAML files into a dict keyed by id."""
    import yaml

    canon_dir = NOVEL_FANDOM_DIR / "canon"
    canon: dict[str, dict] = {}
    for path in sorted(canon_dir.rglob("*.yaml")):
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        canon[data["id"]] = data
    return canon


# --- retrieve_window tests (REQ-YG-487) ---


class TestRetrieveWindow:
    """Deterministic context retrieval from canon."""

    @pytest.mark.req("REQ-YG-487")
    def test_returns_roster_pages(self, seed_canon: dict[str, dict]) -> None:
        """retrieve_window returns pages for requested roster characters."""
        state = {
            "canon": seed_canon,
            "window": "great_flood",
            "roster": ["hilde", "gunnar"],
        }
        result = retrieve_window(state)
        ctx = result["context"]
        ids = [p["id"] for p in ctx["roster_pages"]]
        assert "hilde" in ids
        assert "gunnar" in ids
        assert len(ctx["roster_pages"]) == 2

    @pytest.mark.req("REQ-YG-487")
    def test_extracts_unmet_goals(self) -> None:
        """retrieve_window extracts unmet goals as tensions."""
        canon = {
            "hero": {
                "id": "hero",
                "type": "character",
                "goals": ["avenge father", "unite clans"],
            },
        }
        state = {"canon": canon, "window": "flood", "roster": ["hero"]}
        result = retrieve_window(state)
        goal_tensions = [
            t for t in result["context"]["tensions"] if t["type"] == "unmet_goal"
        ]
        assert len(goal_tensions) == 2
        assert all(t["actor"] == "hero" for t in goal_tensions)

    @pytest.mark.req("REQ-YG-487")
    def test_extracts_internal_conflict(self) -> None:
        """retrieve_window extracts wants≠needs as internal conflict."""
        canon = {
            "hero": {
                "id": "hero",
                "type": "character",
                "wants": "vengeance",
                "needs": "peace",
            },
        }
        state = {"canon": canon, "window": "flood", "roster": ["hero"]}
        result = retrieve_window(state)
        conflicts = [
            t for t in result["context"]["tensions"] if t["type"] == "internal_conflict"
        ]
        assert len(conflicts) == 1
        assert conflicts[0]["wants"] != conflicts[0]["needs"]

    @pytest.mark.req("REQ-YG-487")
    def test_extracts_fears(self) -> None:
        """retrieve_window extracts fears as tension levers."""
        canon = {
            "hero": {
                "id": "hero",
                "type": "character",
                "fears": ["betrayal", "exile"],
            },
        }
        state = {"canon": canon, "window": "flood", "roster": ["hero"]}
        result = retrieve_window(state)
        fear_tensions = [
            t for t in result["context"]["tensions"] if t["type"] == "fear"
        ]
        assert len(fear_tensions) == 2

    @pytest.mark.req("REQ-YG-487")
    def test_extracts_unresolved_edges(self) -> None:
        """retrieve_window extracts unresolved relationship edges."""
        canon = {
            "hero": {
                "id": "hero",
                "type": "character",
                "relationships": [
                    {"to": "rival", "kind": "enemy", "valence": "distrust"},
                ],
            },
        }
        state = {"canon": canon, "window": "flood", "roster": ["hero"]}
        result = retrieve_window(state)
        edges = [
            t for t in result["context"]["tensions"] if t["type"] == "unresolved_edge"
        ]
        assert len(edges) == 1
        assert edges[0]["from"] == "hero"
        assert edges[0]["valence"] == "distrust"

    @pytest.mark.req("REQ-YG-487")
    def test_extracts_triggers(self, seed_canon: dict[str, dict]) -> None:
        """retrieve_window extracts triggers as beat generators."""
        # Triggers field is optional in the entity schema;
        # test that extraction works when present (synthetic character data)
        canon_with_triggers = dict(seed_canon)
        canon_with_triggers["test_char"] = {
            "id": "test_char",
            "type": "character",
            "triggers": ["flood aftermath", "clan scattering"],
        }
        state = {
            "canon": canon_with_triggers,
            "window": "great_flood",
            "roster": ["test_char"],
        }
        result = retrieve_window(state)
        triggers = [t for t in result["context"]["tensions"] if t["type"] == "trigger"]
        assert len(triggers) >= 2

    @pytest.mark.req("REQ-YG-487")
    def test_includes_rules_referenced_by_roster(self) -> None:
        """retrieve_window includes world rules referenced by roster characters."""
        canon = {
            "hero": {
                "id": "hero",
                "type": "character",
                "references": ["blood_feud"],
            },
            "blood_feud": {
                "id": "blood_feud",
                "type": "rule",
                "summary": "Blood must answer blood.",
            },
        }
        state = {"canon": canon, "window": "flood", "roster": ["hero"]}
        result = retrieve_window(state)
        rules = result["context"]["rules"]
        rule_ids = [r["id"] for r in rules]
        assert "blood_feud" in rule_ids

    @pytest.mark.req("REQ-YG-487")
    def test_ignores_nonexistent_roster_ids(self, seed_canon: dict[str, dict]) -> None:
        """retrieve_window silently skips roster ids not in canon."""
        state = {
            "canon": seed_canon,
            "window": "great_flood",
            "roster": ["hilde", "phantom_character"],
        }
        result = retrieve_window(state)
        ids = [p["id"] for p in result["context"]["roster_pages"]]
        assert "hilde" in ids
        assert "phantom_character" not in ids

    @pytest.mark.req("REQ-YG-487")
    def test_window_event_included(self, seed_canon: dict[str, dict]) -> None:
        """retrieve_window includes the window event data when it exists."""
        state = {
            "canon": seed_canon,
            "window": "great_flood",
            "roster": ["hilde"],
        }
        result = retrieve_window(state)
        assert result["context"]["window_event"] is not None
        assert result["context"]["window_event"]["id"] == "great_flood"


# --- Path gate tests (REQ-YG-488) ---


class TestPathGate:
    """Gate rejects beats with orphan references."""

    @pytest.mark.req("REQ-YG-488")
    def test_valid_beats_pass(self) -> None:
        """Beats referencing only canon entities pass the gate."""
        state = {
            "plot_path": {
                "window": "age_of_cinders",
                "beats": [
                    {
                        "actors": ["kaelen", "voss"],
                        "action": "Confrontation at the forge",
                        "moves_tension": {
                            "edge": "kaelen->voss",
                            "toward": "confrontation",
                        },
                        "references": ["kaelen", "voss", "ashguard"],
                    },
                ],
            },
            "canon": {
                "kaelen": {"id": "kaelen", "type": "character"},
                "voss": {"id": "voss", "type": "character"},
                "ashguard": {"id": "ashguard", "type": "faction"},
            },
        }
        result = check_path_references(state)
        assert result["gate_result"]["valid"] is True

    @pytest.mark.req("REQ-YG-488")
    def test_orphan_actor_rejected(self) -> None:
        """Beat with an actor not in canon is rejected."""
        state = {
            "plot_path": {
                "window": "age_of_cinders",
                "beats": [
                    {
                        "actors": ["kaelen", "phantom"],
                        "action": "test",
                        "moves_tension": {},
                        "references": ["kaelen"],
                    },
                ],
            },
            "canon": {
                "kaelen": {"id": "kaelen", "type": "character"},
            },
        }
        result = check_path_references(state)
        assert result["gate_result"]["valid"] is False
        assert any("phantom" in v for v in result["gate_result"]["violations"])

    @pytest.mark.req("REQ-YG-488")
    def test_orphan_reference_rejected(self) -> None:
        """Beat with a reference not in canon is rejected."""
        state = {
            "plot_path": {
                "window": "age_of_cinders",
                "beats": [
                    {
                        "actors": ["kaelen"],
                        "action": "test",
                        "moves_tension": {},
                        "references": ["kaelen", "invented_location"],
                    },
                ],
            },
            "canon": {
                "kaelen": {"id": "kaelen", "type": "character"},
            },
        }
        result = check_path_references(state)
        assert result["gate_result"]["valid"] is False
        assert any(
            "invented_location" in v for v in result["gate_result"]["violations"]
        )

    @pytest.mark.req("REQ-YG-488")
    def test_orphan_edge_target_rejected(self) -> None:
        """Beat with an edge target not in canon is rejected."""
        state = {
            "plot_path": {
                "window": "age_of_cinders",
                "beats": [
                    {
                        "actors": ["kaelen"],
                        "action": "test",
                        "moves_tension": {
                            "edge": "kaelen->ghost",
                            "toward": "conflict",
                        },
                        "references": ["kaelen"],
                    },
                ],
            },
            "canon": {
                "kaelen": {"id": "kaelen", "type": "character"},
            },
        }
        result = check_path_references(state)
        assert result["gate_result"]["valid"] is False
        assert any("ghost" in v for v in result["gate_result"]["violations"])

    @pytest.mark.req("REQ-YG-488")
    def test_multiple_beats_all_checked(self) -> None:
        """All beats are checked, not just the first."""
        state = {
            "plot_path": {
                "window": "age_of_cinders",
                "beats": [
                    {
                        "actors": ["kaelen"],
                        "action": "ok beat",
                        "moves_tension": {},
                        "references": ["kaelen"],
                    },
                    {
                        "actors": ["kaelen", "phantom"],
                        "action": "bad beat",
                        "moves_tension": {},
                        "references": ["kaelen"],
                    },
                ],
            },
            "canon": {
                "kaelen": {"id": "kaelen", "type": "character"},
            },
        }
        result = check_path_references(state)
        assert result["gate_result"]["valid"] is False
        assert any("beat 1" in v for v in result["gate_result"]["violations"])
