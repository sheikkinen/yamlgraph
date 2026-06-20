"""FR-545 -- tests for the allegiance-transition ledger-fidelity witness.

Example-scoped (FR-474 J3): NO ``@pytest.mark.req``.

The witness reads the FINAL committed ``world_state.relationships`` and reports
bi-temporal allegiance transitions (a CLOSED edge ``valid_to == K`` crossing a frozen
stance antonym into a NEW current edge ``valid_from == K``). It counts *grounded
op-emission*, never break correctness -- a low number is the fidelity gap made
visible, not an all-clear (C4). Visibility-not-gate.
"""

from __future__ import annotations

import json
from pathlib import Path

from examples.dungeon_master.api import allegiance_ledger as al
from examples.dungeon_master.scripts import emit_continuity_witness as ew

_PROMPT = Path(__file__).resolve().parents[1] / "prompts" / "chapter_close.yaml"

_REVIEW_MD = """# Book Review

**Overall:** 4/5

## Continuity

Score: 2/5
- A bond silently flips.

## Synopsis delivery

Score: 5/5
"""


def _roster() -> dict:
    return {
        "roster": ["hilde", "gunnar"],
        "cards": {"hilde": {"name": "Hilde"}, "gunnar": {"name": "Gunnar"}},
    }


def _transition_doc(*, grounded: bool) -> dict:
    """Final ledger: a CLOSED enmity edge (valid_to=1) reconciled into a NEW
    romantic_bond edge (valid_from=1) for the same pair -- the bi-temporal stamp of
    one recorded stance reversal at ordinal 1.
    """
    new_cites = ["Ch2-recap: 'the shape of it was already love'"] if grounded else []
    return {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {},
                "2": {
                    "world_state": {
                        "relationships": [
                            {
                                "between": ["Hilde", "Gunnar"],
                                "type": "enmity",
                                "status": "archived",
                                "valid_from": 0,
                                "valid_to": 1,
                                "recap_citations": ["Ch1-recap: 'they drew steel'"],
                            },
                            {
                                "between": ["Hilde", "Gunnar"],
                                "type": "romantic_bond",
                                "status": "active",
                                "valid_from": 1,
                                "valid_to": None,
                                "recap_citations": new_cites,
                            },
                        ]
                    }
                },
            },
        },
        "characters": _roster(),
    }


def _static_ledger_doc() -> dict:
    """Mirrors the real 10031-BC final ledger: 3 all-current edges, NO closed edge.

    This is the total-fidelity-gap shape -- the writer recorded no transition at all,
    so the witness must read ``transition_count == 0`` (the gauge's headline reading).
    """
    return {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {},
                "2": {
                    "world_state": {
                        "relationships": [
                            {
                                "between": ["Hilde", "Gunnar"],
                                "type": "romantic_bond",
                                "status": "active",
                                "valid_from": 0,
                                "valid_to": None,
                                "recap_citations": ["c"],
                            },
                            {
                                "between": ["Hilde", "Reinmar"],
                                "type": "alliance",
                                "status": "active",
                                "valid_from": 1,
                                "valid_to": None,
                                "recap_citations": ["c"],
                            },
                            {
                                "between": ["Gunnar", "Reinmar"],
                                "type": "enmity",
                                "status": "active",
                                "valid_from": 1,
                                "valid_to": None,
                                "recap_citations": ["c"],
                            },
                        ]
                    }
                },
            },
        },
        "characters": {
            "roster": ["hilde", "gunnar", "reinmar"],
            "cards": {
                "hilde": {"name": "Hilde"},
                "gunnar": {"name": "Gunnar"},
                "reinmar": {"name": "Reinmar"},
            },
        },
    }


def test_counts_grounded_stance_reversal() -> None:
    summary = al.allegiance_transitions(_transition_doc(grounded=True))
    assert summary["transition_count"] == 1
    assert summary["ungrounded_count"] == 0
    assert summary["posture"] == "visibility-not-gate"
    assert summary["by_pair"] == [
        {
            "between": ["gunnar", "hilde"],
            "from": "enmity",
            "to": "romantic_bond",
            "at_chapter": 1,
            "grounded": True,
        }
    ]


def test_flags_ungrounded_transition() -> None:
    summary = al.allegiance_transitions(_transition_doc(grounded=False))
    # The crossing is detected but carries no citation on the new edge.
    assert summary["transition_count"] == 0
    assert summary["ungrounded_count"] == 1
    assert summary["by_pair"][0]["grounded"] is False


def test_static_ledger_has_zero_transitions() -> None:
    # The total-fidelity-gap reading: no closed edge => no recorded transition.
    summary = al.allegiance_transitions(_static_ledger_doc())
    assert summary["transition_count"] == 0
    assert summary["ungrounded_count"] == 0
    assert summary["by_pair"] == []


def test_empty_doc_is_additive_no_false_positive() -> None:
    summary = al.allegiance_transitions({})
    assert summary["transition_count"] == 0
    assert summary["by_pair"] == []
    assert summary["posture"] == "visibility-not-gate"


def test_non_roster_pair_is_ignored() -> None:
    doc = _transition_doc(grounded=True)
    # Drop both participants from the roster: the transition must not be counted.
    doc["characters"] = {"roster": ["ylva"], "cards": {"ylva": {"name": "Ylva"}}}
    summary = al.allegiance_transitions(doc)
    assert summary["transition_count"] == 0
    assert summary["by_pair"] == []


def test_does_not_mutate_doc() -> None:
    doc = _transition_doc(grounded=True)
    before = json.dumps(doc, sort_keys=True)
    al.allegiance_transitions(doc)
    assert json.dumps(doc, sort_keys=True) == before


def test_write_witness_includes_allegiance_transitions_block(tmp_path: Path) -> None:
    out = tmp_path / "10102-BC"
    (out / "story").mkdir(parents=True)
    (out / "review.md").write_text(_REVIEW_MD, encoding="utf-8")
    (out / "story" / "story.json").write_text(
        json.dumps(_transition_doc(grounded=True)), encoding="utf-8"
    )
    witness = ew.write_witness(out)
    assert witness is not None
    assert witness["allegiance_transitions"]["transition_count"] == 1
    assert witness["allegiance_transitions"]["posture"] == "visibility-not-gate"


def test_chapter_close_instructs_stance_change_ops() -> None:
    """C3: deterministic prompt-content assertion -- the only Part 2 acceptance.

    Writer *compliance* is a hope, not a gate; this asserts the instruction is
    present, not that a regenerated book records more transitions.
    """
    text = _PROMPT.read_text(encoding="utf-8").lower()
    # The prompt must instruct an op for stance changes, not only type turns.
    assert "stance" in text
    assert "cooling" in text or "side switch" in text or "side-switch" in text
