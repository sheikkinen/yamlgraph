"""Condemn the INCOHERENT lifecycle record at the close seam (FR-526 Judgement).

THE DEFECT (forensic, from outputs/dungeon-master/10024-BC story.json):
    Chapter 3 ("Arnulf Lost and Returned") committed a self-contradictory
    ``character_lifecycle`` row::

        {"name": "Arnulf", "existence_state": "confirmed_dead",
         "allowed_reappearance_from_chapter": 3, "source_chapter": 3}

    A *confirmed*-dead actor cannot also be *allowed to reappear*. The mechanism:
    the close LLM derived ``confirmed_dead`` from the loss; ``_planned_reappearance_
    chapter`` (a name + return-signal scan over ALL chapters, the current one
    included) found Arnulf's return beat in Ch3's own card, so ``_clamp_lifecycle_
    reappearance_to_plan`` wrote a non-null ``allowed_reappearance_from_chapter`` —
    but the clamp only reconciles the *index*, never the *state*. No invariant
    rejected the pairing, so the incoherent row was committed and carried forward.

    The cure (FR-526, behind FR-525) is a PURE, packet-only coherence invariant
    normalized where the record is committed (``the_one_law``): a planned
    reappearance (``allowed_reappearance_from_chapter is not None``) implies the
    character is only *presumed* dead, never *confirmed* dead. The death is softened
    to ``missing_presumed_dead``; the authored return intent is preserved (the
    opposite fix — clearing the reappearance — would erase intent, J4).

    The non-vacuous negative control (J4): a GENUINELY confirmed-dead character with
    ``allowed_reappearance_from_chapter = None`` stays ``confirmed_dead`` — the
    invariant measures the incoherent pairing, not the mere presence of a death.

Example tests are requirement-exempt (FR-474 J3): no ``@pytest.mark.req``.
"""

from __future__ import annotations

from examples.dungeon_master.api import chapter_ops


def _packet(*lifecycle: dict) -> dict:
    """A minimal seam packet carrying only the lifecycle rows under test."""
    return {"character_lifecycle": [dict(item) for item in lifecycle]}


# The exact 10024-BC Ch3 shape: confirmed_dead AND a non-null reappearance (J7).
_INCOHERENT_ROW = {
    "name": "Arnulf",
    "existence_state": "confirmed_dead",
    "visibility_mode": "absent",
    "allowed_reappearance_from_chapter": 3,
    "source_chapter": 3,
}

# A genuinely confirmed-dead character: no planned return, no reappearance allowance.
_GENUINE_DEATH_ROW = {
    "name": "Barengrim",
    "existence_state": "confirmed_dead",
    "visibility_mode": "absent",
    "allowed_reappearance_from_chapter": None,
    "source_chapter": 2,
}


def test_confirmed_dead_with_planned_return_is_softened_to_presumed():
    # The defect: confirmed_dead + a non-null reappearance is incoherent. The
    # invariant downgrades the state to missing_presumed_dead, PRESERVING the
    # reappearance allowance (the authored return intent stays intact, J4).
    out = chapter_ops._enforce_reappearance_state_coherence(_packet(_INCOHERENT_ROW))
    row = out["character_lifecycle"][0]
    assert row["existence_state"] == "missing_presumed_dead"
    assert row["allowed_reappearance_from_chapter"] == 3  # intent preserved
    assert row["name"] == "Arnulf"


def test_genuine_confirmed_death_is_left_untouched_negative_control():
    # Non-vacuous negative control (J4): a real death with NO reappearance allowance
    # stays confirmed_dead -- the invariant fires on the incoherent pairing, not on
    # the mere presence of a confirmed death.
    out = chapter_ops._enforce_reappearance_state_coherence(_packet(_GENUINE_DEATH_ROW))
    row = out["character_lifecycle"][0]
    assert row["existence_state"] == "confirmed_dead"
    assert row["allowed_reappearance_from_chapter"] is None


def test_living_character_with_reappearance_is_left_untouched():
    # Only confirmed_dead downgrades; an alive (or already presumed-dead) row with a
    # reappearance allowance is already coherent and passes through unchanged.
    alive = {
        "name": "Reinmar",
        "existence_state": "alive",
        "visibility_mode": "absent",
        "allowed_reappearance_from_chapter": 5,
        "source_chapter": 7,
    }
    presumed = {
        "name": "Svala",
        "existence_state": "missing_presumed_dead",
        "visibility_mode": "absent",
        "allowed_reappearance_from_chapter": 4,
        "source_chapter": 2,
    }
    out = chapter_ops._enforce_reappearance_state_coherence(_packet(alive, presumed))
    states = {r["name"]: r["existence_state"] for r in out["character_lifecycle"]}
    assert states == {"Reinmar": "alive", "Svala": "missing_presumed_dead"}


def test_empty_and_missing_lifecycle_do_not_crash():
    # Boundary: an absent or empty character_lifecycle is a no-op, not a crash.
    assert (
        chapter_ops._enforce_reappearance_state_coherence({})["character_lifecycle"]
        == []
    )
    assert (
        chapter_ops._enforce_reappearance_state_coherence(_packet())[
            "character_lifecycle"
        ]
        == []
    )


def test_coherence_does_not_mutate_input_packet():
    # Purity: the invariant returns a new packet; the input row is untouched.
    packet = _packet(_INCOHERENT_ROW)
    chapter_ops._enforce_reappearance_state_coherence(packet)
    assert packet["character_lifecycle"][0]["existence_state"] == "confirmed_dead"
