"""FR-622 move 2 (C2): deterministic authored-arc validator.

The FR-613 K=6 read found the coherence gate scored invalid arcs as success.
This validator rejects the *specific* invalid arcs that read condemned, turning
the read's findings into a regression suite (the ``investigation_before_fix``
pattern). It walks the authored ``briefs`` arc only (no LLM, no prose) and flags:

- ``phantom_close``    - a ``close`` for a ``(char, kind)`` thread never opened
                         (loom draw2: ``close Mara/hope`` for an unopened thread).
- ``final_chapter_open`` - an ``open`` in the last chapter, which cannot close by
                         position (salt-road ``relief`` ch8; horror ``loss`` ch4).
- ``scene_type_dose``  - a ``proactive`` chapter that accumulates >= 2 unclosed
                         opens (horror 4/4 proactive over grief/guilt/loss). The
                         MRU prescription: a proactive scene spends feeling through
                         action (low dose); lingering, accumulating interior is
                         reactive-class work mislabelled proactive.

A clean arc (the detective draw) yields zero violations - including the
legitimate proactive cases the rule must NOT flag: a single visceral spike
(1 open) and an all-close climax (feeling spent through the disaster).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

EXAMPLE_DIR = Path(__file__).resolve().parents[2] / "examples" / "plot_modeller"


def _load_tools():
    if str(EXAMPLE_DIR) not in sys.path:
        sys.path.insert(0, str(EXAMPLE_DIR))
    spec = importlib.util.spec_from_file_location(
        "roundtrip_tools_fr622", EXAMPLE_DIR / "nodes" / "roundtrip_tools.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_mod = _load_tools()
validate_authored_arc = _mod.validate_authored_arc
coherence_gate = _mod.coherence_gate


def _op(char, kind, op):
    return {"char": char, "kind": kind, "op": op}


# --- The K=6 defect fixtures (each must red-flag) ---------------------------

_PHANTOM_CLOSE = {  # loom draw2: ch4 closes a thread never opened
    "chapters": [
        {
            "chapter_id": 1,
            "scene_type": "proactive",
            "eff_affect": [_op("Mara", "resolve", "open")],
        },
        {
            "chapter_id": 2,
            "scene_type": "reactive",
            "eff_affect": [
                _op("Mara", "resolve", "close"),
                _op("Mara", "hope", "close"),  # hope was never opened
            ],
        },
    ]
}

_FINAL_CHAPTER_OPEN = {  # salt-road: relief opened in the last chapter
    "chapters": [
        {
            "chapter_id": 1,
            "scene_type": "reactive",
            "eff_affect": [_op("Naima", "grief", "open")],
        },
        {
            "chapter_id": 2,
            "scene_type": "reactive",
            "eff_affect": [_op("Naima", "grief", "close")],
        },
        {
            "chapter_id": 3,
            "scene_type": "reactive",
            "eff_affect": [_op("Naima", "relief", "open")],
        },  # last
    ]
}

_SCENE_TYPE_DOSE = {  # horror: proactive chapters accumulating unclosed interior
    "chapters": [
        {
            "chapter_id": 1,
            "scene_type": "proactive",
            "eff_affect": [
                _op("Cara", "grief", "open"),
                _op("Cara", "guilt", "open"),
                _op("Cara", "loss", "open"),
            ],
        },
        {
            "chapter_id": 2,
            "scene_type": "proactive",
            "eff_affect": [
                _op("Cara", "grief", "close"),
                _op("Cara", "guilt", "close"),
                _op("Cara", "loss", "close"),
            ],
        },
    ]
}

_CLEAN = {  # detective draw: fully closed, no violations
    "chapters": [
        {
            "chapter_id": 1,
            "scene_type": "proactive",
            "eff_affect": [_op("Marren", "fear", "open")],
        },
        {
            "chapter_id": 2,
            "scene_type": "proactive",
            "eff_affect": [_op("Marren", "doubt", "open")],
        },
        {
            "chapter_id": 3,
            "scene_type": "reactive",
            "eff_affect": [_op("Marren", "guilt", "open")],
        },
        {
            "chapter_id": 4,
            "scene_type": "reactive",
            "eff_affect": [
                _op("Marren", "guilt", "close"),
                _op("Marren", "hope", "open"),
            ],
        },
        {
            "chapter_id": 5,
            "scene_type": "proactive",
            "eff_affect": [
                _op("Marren", "hope", "close"),
                _op("Marren", "fear", "close"),
                _op("Marren", "doubt", "close"),
            ],
        },
    ]
}


def _kinds(violations):
    return sorted({v["kind"] for v in violations})


@pytest.mark.req("REQ-YG-020")
def test_phantom_close_flagged():
    v = validate_authored_arc(_PHANTOM_CLOSE)
    assert "phantom_close" in _kinds(v)
    pc = [x for x in v if x["kind"] == "phantom_close"]
    assert any(x["char"] == "Mara" and x["affect"] == "hope" for x in pc)


@pytest.mark.req("REQ-YG-020")
def test_final_chapter_open_flagged():
    v = validate_authored_arc(_FINAL_CHAPTER_OPEN)
    assert "final_chapter_open" in _kinds(v)
    fco = [x for x in v if x["kind"] == "final_chapter_open"]
    assert any(x["chapter_id"] == 3 and x["affect"] == "relief" for x in fco)


@pytest.mark.req("REQ-YG-020")
def test_scene_type_dose_flagged_on_proactive_accumulation():
    v = validate_authored_arc(_SCENE_TYPE_DOSE)
    dose = [x for x in v if x["kind"] == "scene_type_dose"]
    # Chapter 1 accumulates 3 opens with no close on a proactive scene.
    assert any(x["chapter_id"] == 1 for x in dose)


@pytest.mark.req("REQ-YG-020")
def test_clean_arc_has_no_violations():
    assert validate_authored_arc(_CLEAN) == []


@pytest.mark.req("REQ-YG-020")
def test_single_open_proactive_not_flagged():
    """A proactive visceral spike (1 open) is legitimate, not a dose violation."""
    arc = {
        "chapters": [
            {
                "chapter_id": 1,
                "scene_type": "proactive",
                "eff_affect": [_op("X", "fear", "open")],
            },
            {
                "chapter_id": 2,
                "scene_type": "reactive",
                "eff_affect": [_op("X", "fear", "close")],
            },
        ]
    }
    assert [
        x for x in validate_authored_arc(arc) if x["kind"] == "scene_type_dose"
    ] == []


@pytest.mark.req("REQ-YG-020")
def test_all_close_proactive_climax_not_flagged():
    """A proactive climax spending feeling through action (all-close) is legitimate."""
    arc = {
        "chapters": [
            {
                "chapter_id": 1,
                "scene_type": "reactive",
                "eff_affect": [
                    _op("X", "hope", "open"),
                    _op("X", "fear", "open"),
                ],
            },
            {
                "chapter_id": 2,
                "scene_type": "proactive",
                "eff_affect": [
                    _op("X", "hope", "close"),
                    _op("X", "fear", "close"),
                ],
            },
        ]
    }
    assert [
        x for x in validate_authored_arc(arc) if x["kind"] == "scene_type_dose"
    ] == []


@pytest.mark.req("REQ-YG-020")
def test_coherence_gate_surfaces_invalid_arc_verdict():
    """The gate must not silently score 0.0 on an invalid arc (AC #2)."""
    report = coherence_gate({"briefs": _PHANTOM_CLOSE})["coherence"]
    assert report["arc_valid"] is False
    assert report["verdict"] == "fail"
    assert any(x["kind"] == "phantom_close" for x in report["arc_violations"])


@pytest.mark.req("REQ-YG-020")
def test_coherence_gate_clean_arc_passes():
    report = coherence_gate({"briefs": _CLEAN})["coherence"]
    assert report["arc_valid"] is True
    assert report["verdict"] == "pass"
    assert report["arc_violations"] == []
