"""RED tests for FR-639 novel_fandom prose + close loop.

Tests:
- apply_deltas: all 4 op types (REQ-YG-489)
- Carry-forward floor, lane guard, target validation (REQ-YG-490)
- Invalidate-not-delete, prose mention gate (REQ-YG-491)
"""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.process

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


_deltas = _load("novel_fandom_nodes_apply_deltas", "nodes/apply_deltas.py")
_prose_gate = _load("novel_fandom_nodes_prose_gate", "nodes/prose_gate.py")

apply_deltas = _deltas.apply_deltas
check_prose_mentions = _prose_gate.check_prose_mentions


# --- Fixtures ---


def _make_canon() -> dict[str, dict]:
    """Return a minimal mutable canon for delta testing."""
    return {
        "kaelen": {
            "type": "character",
            "id": "kaelen",
            "lane": "dynamic",
            "name": "Kaelen",
            "relationships": [
                {"to": "voss", "kind": "rival", "valence": "enmity"},
            ],
            "references": ["voss", "ashguard"],
        },
        "voss": {
            "type": "character",
            "id": "voss",
            "lane": "dynamic",
            "name": "Voss",
            "relationships": [],
            "references": [],
        },
        "ashguard": {
            "type": "faction",
            "id": "ashguard",
            "lane": "static",
            "name": "Ashguard",
            "references": [],
        },
        "age_of_cinders": {
            "type": "event",
            "id": "age_of_cinders",
            "lane": "static",
            "references": [],
        },
    }


# --- apply_deltas op tests (REQ-YG-489) ---


class TestApplyDeltaOps:
    """Each delta op type works correctly."""

    @pytest.mark.req("REQ-YG-489")
    def test_add_event(self) -> None:
        """add_event creates a new dynamic event page in canon."""
        canon = _make_canon()
        state = {
            "deltas": [
                {
                    "op": "add_event",
                    "id": "forge_duel",
                    "window": "age_of_cinders",
                    "participants": ["kaelen", "voss"],
                    "consequences": ["Voss wounded"],
                    "references": ["kaelen", "voss"],
                },
            ],
            "canon": canon,
        }
        result = apply_deltas(state)
        assert len(result["applied"]) == 1
        assert "forge_duel" in canon
        assert canon["forge_duel"]["lane"] == "dynamic"
        assert canon["forge_duel"]["type"] == "event"

    @pytest.mark.req("REQ-YG-489")
    def test_add_edge(self) -> None:
        """add_edge appends a relationship to an existing dynamic character."""
        canon = _make_canon()
        state = {
            "deltas": [
                {
                    "op": "add_edge",
                    "character": "voss",
                    "to": "kaelen",
                    "kind": "grudge",
                    "valence": "hatred",
                },
            ],
            "canon": canon,
        }
        result = apply_deltas(state)
        assert len(result["applied"]) == 1
        rels = canon["voss"]["relationships"]
        assert any(r["to"] == "kaelen" and r["valence"] == "hatred" for r in rels)

    @pytest.mark.req("REQ-YG-489")
    def test_update_valence(self) -> None:
        """update_valence changes an existing relationship's valence."""
        canon = _make_canon()
        state = {
            "deltas": [
                {
                    "op": "update_valence",
                    "character": "kaelen",
                    "to": "voss",
                    "new_valence": "grudging_respect",
                },
            ],
            "canon": canon,
        }
        result = apply_deltas(state)
        assert len(result["applied"]) == 1
        rel = next(r for r in canon["kaelen"]["relationships"] if r["to"] == "voss")
        assert rel["valence"] == "grudging_respect"

    @pytest.mark.req("REQ-YG-489")
    def test_invalidate_edge(self) -> None:
        """invalidate_edge sets valid_to on an existing relationship."""
        canon = _make_canon()
        state = {
            "deltas": [
                {
                    "op": "invalidate_edge",
                    "character": "kaelen",
                    "to": "voss",
                },
            ],
            "canon": canon,
        }
        result = apply_deltas(state)
        assert len(result["applied"]) == 1
        rel = next(r for r in canon["kaelen"]["relationships"] if r["to"] == "voss")
        assert rel.get("valid_to") is not None

    @pytest.mark.req("REQ-YG-489")
    def test_unknown_op_rejected(self) -> None:
        """Unknown op types are rejected."""
        state = {
            "deltas": [{"op": "delete_page", "id": "kaelen"}],
            "canon": _make_canon(),
        }
        result = apply_deltas(state)
        assert len(result["rejected"]) == 1
        assert "unknown op" in result["rejected"][0]

    @pytest.mark.req("REQ-YG-489")
    def test_ops_wrapped_in_dict(self) -> None:
        """Deltas wrapped in {"ops": [...]} are unwrapped correctly."""
        canon = _make_canon()
        state = {
            "deltas": {
                "ops": [
                    {
                        "op": "add_event",
                        "id": "test_event",
                        "window": "age_of_cinders",
                        "participants": ["kaelen"],
                        "consequences": [],
                        "references": ["kaelen"],
                    },
                ],
            },
            "canon": canon,
        }
        result = apply_deltas(state)
        assert len(result["applied"]) == 1


# --- Carry-forward, lane guard, target validation (REQ-YG-490) ---


class TestDeltaInvariants:
    """Carry-forward floor, lane guard, and target validation."""

    @pytest.mark.req("REQ-YG-490")
    def test_carry_forward_floor(self) -> None:
        """Zero ops leave canon byte-identical."""
        canon = _make_canon()
        original = copy.deepcopy(canon)
        state = {"deltas": [], "canon": canon}
        result = apply_deltas(state)
        assert result["applied"] == []
        assert result["rejected"] == []
        assert canon == original

    @pytest.mark.req("REQ-YG-490")
    def test_lane_guard_rejects_static_add_edge(self) -> None:
        """add_edge targeting a lane:static character is rejected."""
        canon = _make_canon()
        # Make a static character for this test
        canon["static_char"] = {
            "type": "character",
            "id": "static_char",
            "lane": "static",
            "relationships": [],
            "references": [],
        }
        state = {
            "deltas": [
                {
                    "op": "add_edge",
                    "character": "static_char",
                    "to": "kaelen",
                    "kind": "ally",
                    "valence": "trust",
                },
            ],
            "canon": canon,
        }
        result = apply_deltas(state)
        assert len(result["rejected"]) == 1
        assert "static" in result["rejected"][0]

    @pytest.mark.req("REQ-YG-490")
    def test_lane_guard_rejects_static_update_valence(self) -> None:
        """update_valence targeting a lane:static character is rejected."""
        canon = _make_canon()
        canon["static_char"] = {
            "type": "character",
            "id": "static_char",
            "lane": "static",
            "relationships": [{"to": "kaelen", "kind": "ally", "valence": "trust"}],
            "references": ["kaelen"],
        }
        state = {
            "deltas": [
                {
                    "op": "update_valence",
                    "character": "static_char",
                    "to": "kaelen",
                    "new_valence": "hatred",
                },
            ],
            "canon": canon,
        }
        result = apply_deltas(state)
        assert len(result["rejected"]) == 1
        assert "static" in result["rejected"][0]

    @pytest.mark.req("REQ-YG-490")
    def test_target_validation_rejects_nonexistent_participant(self) -> None:
        """add_event with a non-existent participant is rejected."""
        state = {
            "deltas": [
                {
                    "op": "add_event",
                    "id": "bad_event",
                    "window": "age_of_cinders",
                    "participants": ["kaelen", "ghost"],
                    "consequences": [],
                    "references": ["kaelen"],
                },
            ],
            "canon": _make_canon(),
        }
        result = apply_deltas(state)
        assert len(result["rejected"]) == 1
        assert "ghost" in result["rejected"][0]

    @pytest.mark.req("REQ-YG-490")
    def test_target_validation_rejects_nonexistent_edge_target(self) -> None:
        """add_edge with a non-existent target entity is rejected."""
        state = {
            "deltas": [
                {
                    "op": "add_edge",
                    "character": "kaelen",
                    "to": "phantom",
                    "kind": "ally",
                    "valence": "trust",
                },
            ],
            "canon": _make_canon(),
        }
        result = apply_deltas(state)
        assert len(result["rejected"]) == 1
        assert "phantom" in result["rejected"][0]


# --- Invalidate-not-delete + prose gate (REQ-YG-491) ---


class TestBitemporalAndProseGate:
    """Invalidate-not-delete and prose mention gate."""

    @pytest.mark.req("REQ-YG-491")
    def test_invalidate_preserves_edge(self) -> None:
        """Invalidated edge is retained with valid_to, not deleted."""
        canon = _make_canon()
        state = {
            "deltas": [
                {
                    "op": "invalidate_edge",
                    "character": "kaelen",
                    "to": "voss",
                },
            ],
            "canon": canon,
        }
        apply_deltas(state)
        # Edge still exists
        rels = canon["kaelen"]["relationships"]
        assert len(rels) == 1
        assert rels[0]["to"] == "voss"
        assert rels[0].get("valid_to") is not None

    @pytest.mark.req("REQ-YG-491")
    def test_invalidate_then_add_preserves_history(self) -> None:
        """Invalidate old edge + add new edge preserves both."""
        canon = _make_canon()
        state = {
            "deltas": [
                {"op": "invalidate_edge", "character": "kaelen", "to": "voss"},
                {
                    "op": "add_edge",
                    "character": "kaelen",
                    "to": "voss",
                    "kind": "reluctant_ally",
                    "valence": "grudging_respect",
                },
            ],
            "canon": canon,
        }
        result = apply_deltas(state)
        assert len(result["applied"]) == 2
        rels = canon["kaelen"]["relationships"]
        assert len(rels) == 2  # old invalidated + new

    @pytest.mark.req("REQ-YG-491")
    def test_prose_gate_passes_valid_mentions(self) -> None:
        """Prose mentions that all resolve to canon pass the gate."""
        state = {
            "prose_mentions": {"mentions": ["kaelen", "voss", "ashguard"]},
            "canon": {
                "kaelen": {"id": "kaelen"},
                "voss": {"id": "voss"},
                "ashguard": {"id": "ashguard"},
            },
        }
        result = check_prose_mentions(state)
        assert result["gate_result"]["valid"] is True

    @pytest.mark.req("REQ-YG-491")
    def test_prose_gate_rejects_noncanon_mention(self) -> None:
        """Prose mention of a non-canon entity is rejected."""
        state = {
            "prose_mentions": {"mentions": ["kaelen", "invented_wizard"]},
            "canon": {
                "kaelen": {"id": "kaelen"},
            },
        }
        result = check_prose_mentions(state)
        assert result["gate_result"]["valid"] is False
        assert any("invented_wizard" in v for v in result["gate_result"]["violations"])

    @pytest.mark.req("REQ-YG-491")
    def test_prose_gate_empty_mentions_pass(self) -> None:
        """Empty mentions list passes the gate."""
        state = {
            "prose_mentions": {"mentions": []},
            "canon": {"kaelen": {"id": "kaelen"}},
        }
        result = check_prose_mentions(state)
        assert result["gate_result"]["valid"] is True
