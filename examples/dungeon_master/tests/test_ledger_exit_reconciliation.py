"""Condemn the close-boundary ledger resurrection with a deterministic fixture (FR-542 A).

THE HYPOTHESIS (forensic, from outputs/dungeon-master/10029-BC):
    The director reports a structured ``cast_exit`` mid-chapter (Arnulf swept
    downriver in Ch2), but the chapter-close graph derives end-of-chapter
    ``world_state`` from the PROSE alone and can miss that exit — Ch2's ledger
    recorded Arnulf ``status="alive", location="lower bank"``. Ch3 then inherits a
    live-and-present Arnulf and narrates him back in: the "resurrection" surfaces
    chapters after the contradiction first entered, at the Ch2 close boundary.

THE FIX (normalize where the bad state enters — the close boundary, not three
chapters downstream): ``reconcile_ledger_exits`` corrects any character row the
director benched this chapter that the close graph still recorded as present.
Pure, roster-bounded, no LLM. ``chapter_cast_exits`` is the public read that
accumulates the director's exits across the whole played chapter.

Example tests are requirement-exempt (FR-474 J3): no ``@pytest.mark.req``.
"""

from __future__ import annotations

from examples.dungeon_master.api import turn_state
from examples.dungeon_master.api.ledger_reconcile import reconcile_ledger_exits


def _ledger(*characters: dict) -> dict:
    """A world_state ledger carrying the given character rows."""
    return {
        "characters": list(characters),
        "objects": [],
        "facts": [],
        "relationships": [],
    }


def _doc_with_turns(turns: list[dict]) -> dict:
    """One-chapter doc whose played turns carry the supplied director directions."""
    return {
        "chapters": {
            "order": ["1"],
            "cards": {"1": {"turns": turns}},
        }
    }


# ── reconcile_ledger_exits (the pure close-boundary fix) ─────────────────────


def test_reconcile_marks_exited_character_absent() -> None:
    """An exited actor the close graph logged 'alive' is corrected to absent."""
    ledger = _ledger(
        {"name": "Arnulf", "status": "alive", "location": "lower bank"},
        {"name": "Hilde", "status": "alive", "location": "the ledge"},
    )
    out = reconcile_ledger_exits(ledger, ["Arnulf"])
    arnulf = next(c for c in out["characters"] if c["name"] == "Arnulf")
    assert "alive" not in arnulf["status"].lower()
    # Hilde, who did not exit, is untouched.
    hilde = next(c for c in out["characters"] if c["name"] == "Hilde")
    assert hilde["status"] == "alive"


def test_reconcile_leaves_already_absent_status_untouched() -> None:
    """A row already marking absence/loss is not re-marked (idempotent)."""
    ledger = _ledger(
        {"name": "Arnulf", "status": "swept away, presumed drowned", "location": ""},
    )
    out = reconcile_ledger_exits(ledger, ["Arnulf"])
    arnulf = out["characters"][0]
    assert arnulf["status"] == "swept away, presumed drowned"


def test_reconcile_is_case_and_whitespace_insensitive_on_names() -> None:
    """Exit-name matching uses the same norm as the lifecycle gate."""
    ledger = _ledger({"name": "Arnulf the Elder", "status": "alive", "location": "x"})
    out = reconcile_ledger_exits(ledger, ["  arnulf   the elder "])
    assert "alive" not in out["characters"][0]["status"].lower()


def test_reconcile_no_exits_returns_ledger_unchanged() -> None:
    """No director exits this chapter ⇒ identity (additive: today's behavior)."""
    ledger = _ledger({"name": "Hilde", "status": "alive", "location": "the ledge"})
    out = reconcile_ledger_exits(ledger, [])
    assert out == ledger


def test_reconcile_does_not_mutate_input() -> None:
    """The reconcile is a pure read; the caller's ledger is never mutated."""
    ledger = _ledger({"name": "Arnulf", "status": "alive", "location": "lower bank"})
    reconcile_ledger_exits(ledger, ["Arnulf"])
    assert ledger["characters"][0]["status"] == "alive"


# ── chapter_cast_exits (accumulate the director's exits across the chapter) ───


def test_chapter_cast_exits_accumulates_across_all_played_turns() -> None:
    """Exits union across every played turn, de-duped, first-seen order."""
    doc = _doc_with_turns(
        [
            {"direction": {"cast_exits": ["Arnulf"]}},
            {"direction": {"cast_exits": []}},
            {"direction": {"cast_exits": ["Reinmar", "Arnulf"]}},
        ]
    )
    assert turn_state.chapter_cast_exits(doc, "1") == ["Arnulf", "Reinmar"]


def test_chapter_cast_exits_empty_when_no_turns() -> None:
    """A chapter with no played turns reports no exits."""
    doc = _doc_with_turns([])
    assert turn_state.chapter_cast_exits(doc, "1") == []
