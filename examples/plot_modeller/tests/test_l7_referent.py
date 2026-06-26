"""FR-607 — goal-anchored affect referent: validator + additive referent scorer.

Witness tests for the production branches added to ``evaluate.py``:

  validate_referents   — every enriched GT delta names a referent drawn from the
                         file's goal vocabulary (``motivation.goal`` /
                         ``threatens.goal``, NOT the top-level ``goals:`` block —
                         FR-607 judgement correction 2). All five GT files are
                         valid; a synthetic out-of-vocab referent is flagged.
  _l7_counts_referent  — the ADDITIVE referent-aware tally. ``require_referent``
                         demands the named goal match (goal-injected arm); without
                         it the matcher only relaxes beat -> goal-beat-set (the
                         control arm that quantifies the relaxation, J correction 1).
"""

from __future__ import annotations

from pathlib import Path

import yaml
from evaluate import (
    _goal_vocab,
    _l7_counts_referent,
    audit_goal_descriptions,
    validate_referents,
)

GT_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "ground-truth"
GOAL_DESCS = (
    Path(__file__).resolve().parent.parent / "fixtures" / "goal_descriptions.yaml"
)


# Minimal quest fixture: retrieve_crown opens at F4 (hope), closes at F6 (loss+hope).
_TRUTH = {
    "F4": [
        {"op": "open", "char": "Eira", "kind": "hope", "referent": "retrieve_crown"}
    ],
    "F6": [
        {"op": "close", "char": "Eira", "kind": "loss", "referent": "retrieve_crown"},
        {"op": "close", "char": "Eira", "kind": "hope", "referent": "retrieve_crown"},
    ],
}


def _pred(beat: str, **delta) -> list:
    return [{"id": beat, "eff_affect": [delta]}]


def test_all_gt_files_have_valid_referents() -> None:
    for path in sorted(GT_DIR.glob("*.yaml")):
        assert validate_referents(path) == [], path.name


def test_goal_vocab_reads_motivation_and_threatens_not_goals_block() -> None:
    quest = GT_DIR / "quest-adventure-the-sunken-crown.yaml"
    vocab = _goal_vocab(quest)
    assert "retrieve_crown" in vocab
    assert "legitimize_queen" in vocab


def test_validator_flags_out_of_vocab_referent(tmp_path: Path) -> None:
    bad = tmp_path / "g.yaml"
    bad.write_text(
        "functions:\n"
        "  - id: F1\n"
        "    motivation: {agent: Eira, goal: retrieve_crown}\n"
        "    eff_affect:\n"
        "      - op: open\n"
        "        char: Eira\n"
        "        kind: hope\n"
        "        referent: not_a_real_goal\n",
        encoding="utf-8",
    )
    violations = validate_referents(bad)
    assert len(violations) == 1
    assert "not_a_real_goal" in violations[0]


def test_validator_flags_missing_referent(tmp_path: Path) -> None:
    bad = tmp_path / "g.yaml"
    bad.write_text(
        "functions:\n"
        "  - id: F1\n"
        "    motivation: {agent: Eira, goal: retrieve_crown}\n"
        "    eff_affect:\n"
        "      - op: open\n"
        "        char: Eira\n"
        "        kind: hope\n",
        encoding="utf-8",
    )
    assert validate_referents(bad) == ["F1: open hope has no referent"]


def test_referent_match_is_a_hit_when_goal_named() -> None:
    pred = _pred("F4", op="open", char="Eira", kind="hope", referent="retrieve_crown")
    c = _l7_counts_referent(pred, _TRUTH, require_referent=True)
    assert c["recall_hits"] == 1
    assert c["precision_hits"] == 1


def test_wrong_referent_is_not_a_hit_under_require() -> None:
    pred = _pred("F4", op="open", char="Eira", kind="hope", referent="legitimize_queen")
    c = _l7_counts_referent(pred, _TRUTH, require_referent=True)
    assert c["recall_hits"] == 0
    assert c["precision_hits"] == 0


def test_control_arm_relaxes_beat_to_goal_beat_set() -> None:
    # open-hope predicted at F6 (GT places it at F4). Same goal's beat-set is
    # {F4, F6}, so the relaxed control arm counts it; this is exactly the
    # scorer-loosening the honest-lift subtraction must control for.
    pred = _pred("F6", op="open", char="Eira", kind="hope")
    relaxed = _l7_counts_referent(pred, _TRUTH, require_referent=False)
    assert relaxed["recall_hits"] == 1


def test_referent_off_set_beat_is_not_a_hit() -> None:
    # F1 is outside retrieve_crown's beat-set {F4, F6} -> no credit even relaxed.
    pred = _pred("F1", op="open", char="Eira", kind="hope")
    c = _l7_counts_referent(pred, _TRUTH, require_referent=False)
    assert c["recall_hits"] == 0


def test_invented_kind_is_a_false_positive() -> None:
    pred = _pred("F4", op="open", char="Eira", kind="joy", referent="retrieve_crown")
    c = _l7_counts_referent(pred, _TRUTH, require_referent=True)
    assert c["recall_hits"] == 0
    assert c["precision_hits"] == 0
    assert c["pred"] == 1


def test_injected_goal_descriptions_are_leak_free() -> None:
    # The fattest leak surface (J correction 2): every authored description must
    # share NO run of >=3 consecutive words with any beat gloss, and every GT
    # referent must have a description to inject.
    desc_all = yaml.safe_load(GOAL_DESCS.read_text(encoding="utf-8"))
    for path in sorted(GT_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        glosses = [fn.get("gloss", "") for fn in data["functions"]]
        descs = desc_all[path.stem]
        assert audit_goal_descriptions(descs, glosses) == [], path.stem
        referents = {
            a["referent"]
            for fn in data["functions"]
            for a in (fn.get("eff_affect") or [])
        }
        assert referents <= set(descs), f"{path.stem}: referents lacking description"


def test_audit_flags_a_leaking_description() -> None:
    glosses = ["Eira surfaces with the lost royal regalia at last."]
    leaks = audit_goal_descriptions(
        {"retrieve_crown": "seize the lost royal regalia"}, glosses
    )
    assert "retrieve_crown: 'lost royal regalia'" in leaks
