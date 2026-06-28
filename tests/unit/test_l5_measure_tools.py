"""FR-594 unit tests for the deterministic L5 prose-regenerability tools.

The Judgement (2026-06-25) granted Authority to *build the ruler, not swing it*.
These pin the three deterministic (no-LLM, no-GT) tools the graph rests on:

- ``render_l5_beats`` — extracted from ``spike_regenerate_prose.py``; turns a list
  of L5 beats into the predicate stream the regenerate prompt consumes. Pure and
  deterministic.
- ``score_simulability`` — counts ``[UNDERDETERMINED]`` markers in the regenerated
  prose against the real beat count (Judge correction #3: simulability is the
  deterministic axis; it never trusts the model's self-reported COVERAGE line).
- ``combine_l5_measure`` — merges the deterministic simulability axis and the noisy
  fidelity axis WITHOUT collapsing them to one scalar (Judge correction #3: the
  record must stay attributable — which axis fired, never an opaque average).

The fidelity judge (the LLM axis) is witnessed live against the labeled scifi
inversion in the acceptance run, not here (Judge correction #2).
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
        "plot_modeller_tools_fr594", EXAMPLE_DIR / "nodes" / "tools.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_mod = _load_tools()
render_l5_beats = _mod.render_l5_beats
count_underdetermined = _mod.count_underdetermined
score_simulability = _mod.score_simulability
combine_l5_measure = _mod.combine_l5_measure
measure_l5_verdict = _mod.measure_l5_verdict


_BEATS = [
    {
        "id": "F1",
        "kind": "departure",
        "pre_world": [{"pred": "at", "args": ["Mara", "Lab"], "value": True}],
        "eff_world": [
            {"pred": "at", "args": ["Mara", "Lab"], "value": False},
            {"pred": "at", "args": ["Mara", "Seoul"], "value": True},
        ],
    },
    {
        "id": "F2",
        "pre_world": [],
        "eff_world": [],
    },
]


# ---------------------------------------------------------------------------
# render_l5_beats — pure predicate-stream rendering
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-020")
def test_render_beats_emits_id_kind_before_changes():
    out = render_l5_beats(_BEATS)
    assert "Beat F1 [departure]" in out
    assert "before: at(Mara, Lab)=True" in out
    assert "changes: at(Mara, Lab)=False; at(Mara, Seoul)=True" in out


@pytest.mark.req("REQ-YG-020")
def test_render_beats_marks_empty_slices_none():
    out = render_l5_beats(_BEATS)
    # F2 has no pre/eff — both slices render as "(none)", never blank.
    assert "Beat F2" in out
    assert "before: (none)" in out
    assert "changes: (none)" in out


@pytest.mark.req("REQ-YG-020")
def test_render_beats_is_deterministic():
    assert render_l5_beats(_BEATS) == render_l5_beats(_BEATS)


@pytest.mark.req("REQ-YG-020")
def test_render_beats_dual_mode_state_dict():
    """As a graph tool it receives the full state and writes ``beats``."""
    out = render_l5_beats({"l5_beats": _BEATS})
    assert isinstance(out, dict)
    assert "Beat F1 [departure]" in out["beats"]


# ---------------------------------------------------------------------------
# score_simulability — deterministic UNDERDETERMINED accounting
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-020")
def test_count_underdetermined_counts_markers_not_self_report():
    prose = (
        "Mara left the lab. [UNDERDETERMINED: why she leaves]\n"
        "She arrived in Seoul. [UNDERDETERMINED: what Seoul means]\n"
        "COVERAGE: 9 underdetermined markers / 12 beats."  # model's claim — ignored
    )
    # We count the real markers (2), never the model's self-reported 9.
    assert count_underdetermined(prose) == 2


@pytest.mark.req("REQ-YG-020")
def test_score_simulability_ratio_uses_real_beat_count():
    prose = "A. [UNDERDETERMINED: x]\nB. plain sentence."
    state = {"regen_prose": prose, "l5_beats": _BEATS}
    out = score_simulability(state)
    sim = out["simulability"]
    assert sim["underdetermined"] == 1
    assert sim["beats"] == 2
    assert sim["ratio"] == pytest.approx(0.5)


@pytest.mark.req("REQ-YG-020")
def test_score_simulability_zero_beats_is_safe():
    out = score_simulability({"regen_prose": "nothing", "l5_beats": []})
    assert out["simulability"]["beats"] == 0
    assert out["simulability"]["ratio"] == 0.0


# ---------------------------------------------------------------------------
# combine_l5_measure — orthogonal, attributable verdict (no collapsed scalar)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-020")
def test_combine_keeps_axes_separate_and_attributable():
    state = {
        "simulability": {"underdetermined": 2, "beats": 13, "ratio": 0.15},
        "fidelity": {
            "recovered": ["a", "b"],
            "missing": ["c"],
            "inverted": ["climax flipped: rollback read as ARIA winning"],
            "score": 0.6,
        },
    }
    out = combine_l5_measure(state)["l5_measure"]
    # Both axes preserved verbatim — never averaged into one number.
    assert out["simulability"]["ratio"] == 0.15
    assert out["fidelity"]["score"] == 0.6
    assert out["inverted_count"] == 1
    # The verdict names which axis fired; inversion must surface as a concern.
    assert "fidelity_inverted" in out["concerns"]


@pytest.mark.req("REQ-YG-020")
def test_combine_flags_high_underdetermined_axis():
    state = {
        "simulability": {"underdetermined": 8, "beats": 8, "ratio": 1.0},
        "fidelity": {"recovered": [], "missing": [], "inverted": [], "score": 0.9},
    }
    out = combine_l5_measure(state)["l5_measure"]
    assert "low_simulability" in out["concerns"]
    assert "fidelity_inverted" not in out["concerns"]


@pytest.mark.req("REQ-YG-020")
def test_combine_clean_case_has_no_concerns():
    state = {
        "simulability": {"underdetermined": 1, "beats": 10, "ratio": 0.1},
        "fidelity": {"recovered": ["a"], "missing": [], "inverted": [], "score": 0.95},
    }
    out = combine_l5_measure(state)["l5_measure"]
    assert out["concerns"] == []


@pytest.mark.req("REQ-YG-020")
def test_combine_coerces_pydantic_fidelity_model():
    """The judge node yields a Pydantic model; combine must read it like a dict."""

    class _Fidelity:
        def model_dump(self):
            return {
                "recovered": ["a"],
                "missing": [],
                "inverted": ["climax flipped"],
                "score": 0.4,
            }

    state = {
        "simulability": {"underdetermined": 2, "beats": 13, "ratio": 0.15},
        "fidelity": _Fidelity(),
    }
    out = combine_l5_measure(state)["l5_measure"]
    assert out["inverted_count"] == 1
    assert "fidelity_inverted" in out["concerns"]
    assert "low_fidelity" in out["concerns"]
    assert out["fidelity"]["score"] == 0.4


# ---------------------------------------------------------------------------
# measure_l5_verdict — FR-595 powered, GT-anchored discrimination gate
# ---------------------------------------------------------------------------
#
# Power analysis (FR-594, n=5): paired gap gt_sim - ours_sim = 0.337 +/- 0.035,
# t(4)=21.6. The verdict gates ONLY on the corpus-mean gap, never on absolute
# values (corpus-mean sd 0.085) or per-genre (worst-cell sd 0.22).


@pytest.mark.req("REQ-YG-020")
def test_verdict_go_on_observed_corpus_gap():
    """The live corpus gap (~0.34, ours more regenerable than GT) is a GO."""
    out = measure_l5_verdict(0.295, 0.632)
    assert out["verdict"] == "GO"
    assert round(out["gap"], 3) == 0.337
    assert out["ours_sim_mean"] == 0.295
    assert out["gt_sim_mean"] == 0.632


@pytest.mark.req("REQ-YG-020")
def test_verdict_revise_on_marginal_gap():
    """A gap inside the noisy band (>=0.05, <0.15) is REVISE, not GO."""
    out = measure_l5_verdict(0.50, 0.58)
    assert out["verdict"] == "REVISE"


@pytest.mark.req("REQ-YG-020")
def test_verdict_kill_on_collapsed_gap():
    """When ours is no more regenerable than the lossy GT skeleton, KILL."""
    out = measure_l5_verdict(0.60, 0.62)
    assert out["verdict"] == "KILL"


@pytest.mark.req("REQ-YG-020")
def test_verdict_kill_when_ours_worse_than_gt():
    """Negative gap (ours LESS regenerable than GT) is a KILL, never GO."""
    out = measure_l5_verdict(0.70, 0.40)
    assert out["verdict"] == "KILL"
    assert out["gap"] < 0


@pytest.mark.req("REQ-YG-020")
def test_verdict_records_gt_anchored_basis_not_absolute():
    """The verdict must declare it is a GT-anchored paired-gap call, not absolute."""
    out = measure_l5_verdict(0.295, 0.632)
    assert "gt_anchored" in out["basis"]
    # power provenance is carried so a reader cannot mistake it for a single-run
    # absolute threshold (FR-594 power analysis).
    assert "power" in out
