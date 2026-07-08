"""FR-692: World-pressure admission + kinship reciprocity gates (REQ-YG-531/532).

The world-pressure pass grows canon additively under two mechanical rules:
admission (a new entity must cite a live thread it pressurizes) and reciprocity
(a kinship edge must be acknowledged in reverse). One implementation in
`nodes/world_pressure_gates.py`, two callers.

RED contract: `world_pressure_gates.py` ships as always-valid stubs; every
invalid-fixture test below fails until the real logic lands (GREEN). Schema
tests pass immediately (the schema is not stubbed).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest
import yaml

NOVEL_FANDOM_DIR = (
    Path(__file__).parent.parent.parent / "examples" / "novel_fandom"
).resolve()
_nf_str = str(NOVEL_FANDOM_DIR)
if _nf_str not in sys.path:
    sys.path.insert(0, _nf_str)


def _load(mod_name: str, rel_path: str) -> ModuleType:
    fpath = NOVEL_FANDOM_DIR / rel_path
    spec = importlib.util.spec_from_file_location(mod_name, fpath)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


_canon = _load("novel_fandom_schema_canon_fr692", "schema/canon.py")
_gates = _load(
    "novel_fandom_nodes_world_pressure_gates", "nodes/world_pressure_gates.py"
)

Character = _canon.Character
Faction = _canon.Faction
Location = _canon.Location
check_pressure_admission = _gates.check_pressure_admission
check_reciprocity = _gates.check_reciprocity
gate_admission = _gates.gate_admission
gate_reciprocity = _gates.gate_reciprocity

RECIPROCAL_KINDS = {"mother", "father", "clanmate"}


def _char(cid: str, rels: list[dict]) -> dict:
    return {
        "type": "character",
        "id": cid,
        "lane": "dynamic",
        "name": cid,
        "relationships": rels,
    }


def _rel(to: str, kind: str) -> dict:
    return {"to": to, "kind": kind, "valence": "positive"}


def _load_canon_char(cid: str) -> dict:
    path = NOVEL_FANDOM_DIR / "canon" / "character" / f"{cid}.yaml"
    return yaml.safe_load(path.read_text())


# ------------------------------------------------------------------ schema


@pytest.mark.req("REQ-YG-531")
def test_pressurizes_defaults_empty_on_all_world_entities() -> None:
    """pressurizes is optional (default empty) so pre-existing canon validates."""
    assert Character(id="x", lane="dynamic", name="X").pressurizes == []
    assert Faction(id="f", lane="dynamic", name="F").pressurizes == []
    assert Location(id="l", lane="dynamic", name="L").pressurizes == []


@pytest.mark.req("REQ-YG-531")
def test_pressurizes_accepts_thread_ids() -> None:
    c = Character(id="x", lane="dynamic", name="X", pressurizes=["t_feud", "t_bond"])
    assert c.pressurizes == ["t_feud", "t_bond"]


# ------------------------------------------------------- admission gate (RED)


@pytest.mark.req("REQ-YG-531")
def test_admission_rejects_entity_with_no_thread_citation() -> None:
    entities = [{"id": "gunnar_father", "pressurizes": []}]
    result = check_pressure_admission(entities, {"t_feud", "t_bond"})
    assert result["valid"] is False
    assert any("gunnar_father" in v for v in result["violations"])


@pytest.mark.req("REQ-YG-531")
def test_admission_rejects_missing_pressurizes_key() -> None:
    entities = [{"id": "orphan"}]  # no pressurizes field at all
    result = check_pressure_admission(entities, {"t_feud"})
    assert result["valid"] is False


@pytest.mark.req("REQ-YG-531")
def test_admission_rejects_nonexistent_thread_id() -> None:
    entities = [{"id": "berno_kin", "pressurizes": ["t_ghost"]}]
    result = check_pressure_admission(entities, {"t_feud", "t_bond"})
    assert result["valid"] is False
    assert any("t_ghost" in v for v in result["violations"])


@pytest.mark.req("REQ-YG-531")
def test_admission_flags_only_the_bad_entity() -> None:
    entities = [
        {"id": "good", "pressurizes": ["t_feud"]},
        {"id": "bad", "pressurizes": ["t_missing"]},
    ]
    result = check_pressure_admission(entities, {"t_feud"})
    assert result["valid"] is False
    assert all("good" not in v for v in result["violations"])
    assert any("bad" in v for v in result["violations"])


@pytest.mark.req("REQ-YG-531")
def test_admission_passes_when_all_cite_live_threads() -> None:
    entities = [
        {"id": "a", "pressurizes": ["t_feud"]},
        {"id": "b", "pressurizes": ["t_feud", "t_bond"]},
    ]
    result = check_pressure_admission(entities, {"t_feud", "t_bond"})
    assert result["valid"] is True
    assert result["violations"] == []


# ------------------------------------------------------ reciprocity gate (RED)


@pytest.mark.req("REQ-YG-532")
def test_reciprocity_rejects_unacknowledged_mother_edge() -> None:
    chars = [
        _char("reinthilde", [_rel("hilde", "mother")]),
        _char("hilde", []),  # no reverse edge
    ]
    result = check_reciprocity(chars, RECIPROCAL_KINDS)
    assert result["valid"] is False
    assert any("hilde" in v and "reinthilde" in v for v in result["violations"])


@pytest.mark.req("REQ-YG-532")
def test_reciprocity_rejects_one_directional_clanmate() -> None:
    chars = [
        _char("berno", [_rel("gunnar", "clanmate")]),
        _char("gunnar", []),
    ]
    result = check_reciprocity(chars, RECIPROCAL_KINDS)
    assert result["valid"] is False


@pytest.mark.req("REQ-YG-532")
def test_reciprocity_accepts_any_reverse_edge() -> None:
    """Reciprocity = mutual acknowledgment; the reverse kind may differ."""
    chars = [
        _char("reinthilde", [_rel("hilde", "mother")]),
        _char("hilde", [_rel("reinthilde", "daughter")]),
    ]
    result = check_reciprocity(chars, RECIPROCAL_KINDS)
    assert result["valid"] is True


@pytest.mark.req("REQ-YG-532")
def test_reciprocity_ignores_non_reciprocal_kinds() -> None:
    chars = [
        _char("hilde", [_rel("reinmar", "follower")]),
        _char("reinmar", []),
    ]
    result = check_reciprocity(chars, RECIPROCAL_KINDS)
    assert result["valid"] is True


@pytest.mark.req("REQ-YG-532")
def test_reciprocity_holds_on_repaired_canon() -> None:
    """After the FR-692 additive repair, the 4 kinship principals reciprocate.

    Passes trivially under the RED stub; under GREEN it enforces that the
    repair edges (hilde->reinthilde, gunnar->reinthilde, gunnar->berno) exist.
    """
    chars = [_load_canon_char(c) for c in ("reinthilde", "hilde", "gunnar", "berno")]
    result = check_reciprocity(chars, RECIPROCAL_KINDS)
    assert result["valid"] is True, result["violations"]


# -------------------------------------------------------------- graph adapters


@pytest.mark.req("REQ-YG-532")
def test_gate_reciprocity_adapter_reads_canon_pages() -> None:
    canon_pages = {
        "reinthilde": _char("reinthilde", [_rel("hilde", "mother")]),
        "hilde": _char("hilde", []),  # no reverse edge
        "the_lake": {"type": "location", "id": "the_lake"},  # ignored
    }
    out = gate_reciprocity({"canon_pages": canon_pages})
    assert out["gate_result"]["valid"] is False


@pytest.mark.req("REQ-YG-531")
def test_gate_admission_adapter_derives_threads_from_state() -> None:
    state = {
        "candidates": [{"id": "kin", "pressurizes": ["t_feud"]}],
        "thread_ids": ["t_feud"],
    }
    out = gate_admission(state)
    assert out["gate_result"]["valid"] is True


@pytest.mark.req("REQ-YG-531")
def test_gate_admission_adapter_rejects_uncited_candidate() -> None:
    state = {
        "candidates": [{"id": "orphan", "pressurizes": []}],
        "thread_ids": ["t_feud"],
    }
    out = gate_admission(state)
    assert out["gate_result"]["valid"] is False
