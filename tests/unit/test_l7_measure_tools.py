"""FR-597 unit tests for the deterministic L7 affect-regenerability tools.

The Judgement (2026-06-25) granted Authority to *build the ruler, not swing it* —
the node-for-node affect port of FR-594's L5 regenerability graph. These pin the
deterministic (no-LLM, no-GT) tools the ``l7_measure`` graph rests on:

- ``render_l7_affect`` — turns a list of affect beats ``[{id, eff_affect:[...]}]``
  into the per-beat delta stream the ``regenerate_affect_arc`` prompt consumes.
  Pure and deterministic; renders only affect-bearing beats (the denominator).
- ``score_affect_simulability`` — counts ``[UNDERDETERMINED]`` markers in the
  regenerated emotional arc against the real affect-bearing beat count (Judge C2:
  the load-bearing witness is the deterministic marker, not the LLM judge).
- ``combine_l7_measure`` — merges the deterministic simulability axis and the noisy
  fidelity axis WITHOUT collapsing them (Judge C4: the verdict is simulability-led;
  the fidelity judge informs attribution only).
- ``l7_regenerability_exit`` — the binary two-way exit (Judge C1, anti-deferral):
  GT pooled ratio >= ~0.70 confirms the thesis (branch a → demotion FR), else
  refutes it (branch b → affect_recall stands). Either branch un-blocks the encoder.

The fidelity judge (the LLM axis) is witnessed live against the detective
``betrayal → Hagen`` vs ``guilt → Pell`` under-determination in the acceptance run,
not here (Judge C2).
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
        "plot_modeller_tools_fr597", EXAMPLE_DIR / "nodes" / "tools.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_mod = _load_tools()
render_l7_affect = _mod.render_l7_affect
score_affect_simulability = _mod.score_affect_simulability
combine_l7_measure = _mod.combine_l7_measure
l7_regenerability_exit = _mod.l7_regenerability_exit


_AFFECT_BEATS = [
    {
        "id": "F2",
        "eff_affect": [
            {"op": "open", "char": "Marren", "kind": "loss"},
            {"op": "open", "char": "Hagen", "kind": "betrayal", "toward": "Marren"},
        ],
    },
    {
        "id": "F3",
        "eff_affect": [],  # non-affect beat — excluded from the denominator
    },
    {
        "id": "F4",
        "eff_affect": [
            {"op": "close", "char": "Marren", "kind": "loss"},
        ],
    },
]


# ---------------------------------------------------------------------------
# render_l7_affect — pure per-beat delta-stream rendering
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-020")
def test_render_affect_emits_beat_and_deltas():
    out = render_l7_affect(_AFFECT_BEATS)
    assert "Beat F2" in out
    assert "open Marren loss" in out
    assert "close Marren loss" in out


@pytest.mark.req("REQ-YG-020")
def test_render_affect_includes_relational_toward():
    out = render_l7_affect(_AFFECT_BEATS)
    # relational kinds carry their target so the judge can score char + toward.
    assert "open Hagen betrayal toward Marren" in out


@pytest.mark.req("REQ-YG-020")
def test_render_affect_skips_non_affect_beats():
    out = render_l7_affect(_AFFECT_BEATS)
    # F3 has no deltas — it must not appear as a rendered block.
    assert "Beat F3" not in out


@pytest.mark.req("REQ-YG-020")
def test_render_affect_dict_mode_returns_state_update():
    # Graph python-tool mode: receives the full state, reads `affect_beats`.
    out = render_l7_affect({"affect_beats": _AFFECT_BEATS})
    assert isinstance(out, dict)
    assert "affect_skeleton" in out
    assert "open Marren loss" in out["affect_skeleton"]


# ---------------------------------------------------------------------------
# score_affect_simulability — deterministic UNDERDETERMINED / affect-beats
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-020")
def test_score_affect_simulability_counts_markers_over_affect_beats():
    state = {
        "regen_arc": (
            "Marren feels her case collapse. [UNDERDETERMINED: why Hagen]\n"
            "Later the loss closes. [UNDERDETERMINED: what blessing]"
        ),
        "affect_beats": _AFFECT_BEATS,
    }
    out = score_affect_simulability(state)["simulability"]
    # 2 markers; denominator is affect-bearing beats only (F2, F4) = 2.
    assert out["underdetermined"] == 2
    assert out["beats"] == 2
    assert out["ratio"] == pytest.approx(1.0)


@pytest.mark.req("REQ-YG-020")
def test_score_affect_simulability_zero_beats_is_safe():
    out = score_affect_simulability({"regen_arc": "", "affect_beats": []})[
        "simulability"
    ]
    assert out["beats"] == 0
    assert out["ratio"] == 0.0


# ---------------------------------------------------------------------------
# combine_l7_measure — attributable two-axis record (never one scalar)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-020")
def test_combine_l7_preserves_both_axes_attributable():
    state = {
        "simulability": {"underdetermined": 5, "beats": 6, "ratio": 0.83},
        "fidelity": {
            "recovered": ["loss opens"],
            "missing": [],
            "inverted": ["betrayal target flipped"],
            "score": 0.3,
        },
    }
    rec = combine_l7_measure(state)["l7_measure"]
    # Both axes preserved verbatim — never averaged into one opaque scalar.
    assert rec["simulability"]["ratio"] == 0.83
    assert rec["fidelity"]["score"] == 0.3
    assert rec["inverted_count"] == 1
    assert rec["diagnostic_only"] is True
    # Attributable: which axis fired.
    assert "low_simulability" in rec["concerns"]
    assert "fidelity_inverted" in rec["concerns"]
    assert "low_fidelity" in rec["concerns"]
    # Judge C4: the verdict is simulability-led; the record must say so.
    assert rec["verdict_basis"] == "simulability"


@pytest.mark.req("REQ-YG-020")
def test_combine_l7_clean_record_has_no_concerns():
    state = {
        "simulability": {"underdetermined": 0, "beats": 6, "ratio": 0.0},
        "fidelity": {
            "recovered": ["a", "b"],
            "missing": [],
            "inverted": [],
            "score": 1.0,
        },
    }
    rec = combine_l7_measure(state)["l7_measure"]
    assert rec["concerns"] == []
    assert rec["inverted_count"] == 0


# ---------------------------------------------------------------------------
# l7_regenerability_exit — the binary two-way exit (Judge C1)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-020")
def test_exit_thesis_confirmed_branch_a():
    out = l7_regenerability_exit(0.80)
    assert out["branch"] == "a"
    assert out["thesis"] == "confirmed"
    # Branch a authorizes the demotion FR and resumes the encoder against it.
    assert "demot" in out["authorizes"].lower()


@pytest.mark.req("REQ-YG-020")
def test_exit_thesis_refuted_branch_b():
    out = l7_regenerability_exit(0.30)
    assert out["branch"] == "b"
    assert out["thesis"] == "refuted"
    # Branch b keeps affect_recall and resumes the encoder against its 0.50 gate.
    assert "affect_recall" in out["authorizes"]


@pytest.mark.req("REQ-YG-020")
def test_exit_threshold_boundary_confirms():
    # The 0.70 threshold is inclusive — exactly at the floor confirms the thesis.
    assert l7_regenerability_exit(0.70)["branch"] == "a"
