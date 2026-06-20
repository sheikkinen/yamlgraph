"""Condemn the silent resolved-fact reversal with a deterministic fixture (FR-542 B).

THE HYPOTHESIS (forensic, from outputs/dungeon-master/10029-BC):
    Chapter 3 RESOLVES the food bundle ("pulled fully onto the ledge into the
    shared supply space" -- secured); Chapter 4 reopens it as "sat unclaimed" in
    the boat. The seam ledger already records ``resolved_events`` /
    ``forbidden_regressions``, but they are only rendered into prose context where a
    0.7-temperature sampler can silently undo them. There is no deterministic
    detector for a resolved fact being un-resolved.

THE FIX: ``fact_reversal_gap`` diffs consecutive chapters' committed ledger lines
for a closed antonym reversal (secured<->unclaimed, present<->absent,
closed<->reopened) about a SHARED subject -- roster/closed-set bounded, no
free-text NLP. ``fact_reversal_summary`` aggregates it into the continuity witness
(measurement-first, FR-538 posture); it never gates the run in Phase 1.

Example tests are requirement-exempt (FR-474 J3): no ``@pytest.mark.req``.
"""

from __future__ import annotations

from examples.dungeon_master.api.fact_reversal import fact_reversal_gap
from examples.dungeon_master.scripts.emit_continuity_witness import (
    _proper_noun_entities,
    fact_reversal_summary,
)


def _card(*, resolved=None, open_threads=None, forbidden=None, deltas=None) -> dict:
    """A chapter card carrying only the committed chapter_memory fields under test."""
    return {
        "chapter_memory": {
            "resolved_events": list(resolved or []),
            "open_threads": list(open_threads or []),
            "forbidden_regressions": list(forbidden or []),
            "character_state_deltas": list(deltas or []),
            "irreversible_facts": [],
        }
    }


# ── fact_reversal_gap: the resolved-event reversal (the food bundle) ──────────


def test_food_bundle_reversal_is_flagged() -> None:
    """Ch3 secures the bundle; Ch4 reopens it unclaimed -> a reversal."""
    prev = _card(resolved=["The food bundle is secured on the ledge supply space"])
    card = _card(open_threads=["The food bundle sat unclaimed in the drifting boat"])
    result = fact_reversal_gap(prev, card)
    assert result["gap_count"] == 1
    gap = result["gaps"][0]
    assert gap["reason"] == "resolved_event_reversal"
    assert "bundle" in (gap["prior_fact"] + gap["reversed_fact"]).lower()


def test_clean_succession_is_not_flagged() -> None:
    """An unrelated resolved fact in the successor is not a reversal."""
    prev = _card(resolved=["The food bundle is secured on the ledge"])
    card = _card(resolved=["The signal fire kept burning through the night"])
    assert fact_reversal_gap(prev, card)["gap_count"] == 0


def test_antonym_without_shared_subject_is_not_flagged() -> None:
    """Opposite antonym sides about DIFFERENT subjects do not compose a reversal."""
    prev = _card(resolved=["The gate is secured against the river"])
    card = _card(open_threads=["The empty boat drifted unclaimed downstream"])
    # 'secured' vs 'unclaimed' are opposite sides, but 'gate' and 'boat' share no
    # subject token -- subject-bounded, not mere antonym co-occurrence.
    assert fact_reversal_gap(prev, card)["gap_count"] == 0


def test_forbidden_regression_violation_is_flagged() -> None:
    """A forbidden regression the successor's ledger contradicts is flagged."""
    prev = _card(forbidden=["The ford stays closed to the clan after the collapse"])
    card = _card(resolved=["The ford was reopened and the clan crossed at dawn"])
    result = fact_reversal_gap(prev, card)
    assert result["gap_count"] == 1
    assert result["gaps"][0]["reason"] == "forbidden_regression_violation"


def test_empty_ledgers_degrade_to_no_gap() -> None:
    """Absent committed ledgers ⇒ no reversal (additive: today's behavior)."""
    assert fact_reversal_gap(_card(), _card())["gap_count"] == 0
    assert fact_reversal_gap({}, {})["gap_count"] == 0


# ── fact_reversal_summary: the additive witness block ────────────────────────


def _story(cards_in_order: list[dict]) -> dict:
    """A story doc whose chapters carry the supplied cards in order."""
    order = [str(i + 1) for i in range(len(cards_in_order))]
    return {
        "chapters": {
            "order": order,
            "cards": dict(zip(order, cards_in_order, strict=True)),
        }
    }


def test_summary_sums_reversals_across_chapter_pairs() -> None:
    """The witness aggregator walks adjacent pairs and totals the reversals."""
    doc = _story(
        [
            _card(resolved=["The food bundle is secured on the ledge"]),
            _card(
                resolved=["The ford is closed to the clan after the collapse"],
                open_threads=["The food bundle sat unclaimed in the drifting boat"],
            ),
            _card(open_threads=["The ford was reopened and the clan crossed"]),
        ]
    )
    summary = fact_reversal_summary(doc)
    # Pair (Ch1->Ch2) reverses the bundle; pair (Ch2->Ch3) reverses the ford -> 2.
    assert summary["gap_count"] == 2
    assert summary["posture"] == "visibility-not-gate"


def test_summary_zero_when_no_reversal() -> None:
    """A coherent story yields an empty, non-gating witness block."""
    doc = _story(
        [
            _card(resolved=["The fire was lit"]),
            _card(resolved=["The clan reached the ridge"]),
        ]
    )
    assert fact_reversal_summary(doc)["gap_count"] == 0


# ── FR-547: entity-disagreement suppression (the locative false positive) ─────


def test_distinct_entity_subjects_suppress_locative_collision() -> None:
    """10032-BC: two facts about DIFFERENT named entities sharing only 'flood zone'."""
    prev = _card(resolved=["Reinmar arrived at the flood zone by the salt road."])
    card = _card(
        open_threads=["Arnulf is still missing in the flood zone and unconfirmed dead."]
    )
    entities = {"reinmar", "arnulf"}
    # Both lines name a DISTINCT entity -> disjoint -> suppressed.
    assert fact_reversal_gap(prev, card, entities=entities)["gap_count"] == 0
    # Absent an entity set, the detector keeps today's (over-eager) behavior.
    assert fact_reversal_gap(prev, card)["gap_count"] == 1


def test_ford_reversal_without_entities_still_flagged() -> None:
    """Ford guard: a place reversal naming no entity must NOT be suppressed."""
    prev = _card(forbidden=["The ford was sealed against the clan"])
    card = _card(resolved=["The ford was reopened and the clan crossed"])
    entities = {"reinmar", "arnulf"}
    # Neither line names Reinmar or Arnulf -> the closed<->reopened reversal stands.
    assert fact_reversal_gap(prev, card, entities=entities)["gap_count"] == 1


def test_same_entity_reversal_not_suppressed() -> None:
    """A present->absent reversal about the SAME entity is still a reversal."""
    prev = _card(resolved=["Arnulf arrived at the ridge"])
    card = _card(open_threads=["Arnulf is missing in the flood"])
    entities = {"arnulf"}
    # Same named entity on both sides -> not disjoint -> kept.
    assert fact_reversal_gap(prev, card, entities=entities)["gap_count"] == 1


def test_capitalized_common_noun_absent_from_lexicon_not_an_entity() -> None:
    """The new boundary: a capitalized common noun NOT in the lexicon is no entity."""
    prev = _card(resolved=["Floodwater secured the ledge supply"])
    card = _card(open_threads=["Floodwater left the ledge supply unclaimed"])
    # 'floodwater' is not a proper-noun entity -> named() empty on both -> a genuine
    # same-subject reversal about it is still flagged, not suppressed.
    entities = {"reinmar", "arnulf"}
    assert fact_reversal_gap(prev, card, entities=entities)["gap_count"] == 1


# ── FR-547: the corpus proper-noun lexicon builder ───────────────────────────


def _story_with_prose(
    cards_in_order: list[dict], texts: list[str], roster_names: dict[str, str]
) -> dict:
    """A story doc whose chapter cards carry committed prose and a roster."""
    doc = _story(cards_in_order)
    for cid, text in zip(doc["chapters"]["order"], texts, strict=True):
        doc["chapters"]["cards"][cid]["text"] = text
    doc["characters"] = {
        "roster": list(roster_names),
        "cards": {cid: {"name": name} for cid, name in roster_names.items()},
    }
    return doc


def test_proper_noun_lexicon_includes_offroster_excludes_locative() -> None:
    """The lexicon recovers an off-roster name (cap mid-sentence >=2) but no locative."""
    doc = _story_with_prose(
        [_card(), _card()],
        [
            "The clan fled. Then Arnulf reached the flood zone and Arnulf called out.",
            "Later Arnulf was gone, and the flood rose over the salt road.",
        ],
        {"c1": "Reinmar"},
    )
    lexicon = _proper_noun_entities(doc)
    # Off-roster Arnulf (capitalized mid-sentence 3x) is recovered ...
    assert "arnulf" in lexicon
    # ... the roster name is unioned in ...
    assert "reinmar" in lexicon
    # ... and no locative (always lowercase mid-sentence) poisons the lexicon.
    assert "flood" not in lexicon
    assert "zone" not in lexicon
    assert "road" not in lexicon


def test_summary_suppresses_offroster_locative_collision() -> None:
    """End-to-end (D4): an OFF-roster name in prose anchors the suppression.

    This pins the live 10032-BC AC: Arnulf is absent from the roster yet named in
    the prose, so the entity set recovers him and the flood-zone collision is no
    longer a false reversal -- proven by a committed synthetic fixture (outputs/ is
    gitignored).
    """
    doc = _story_with_prose(
        [
            _card(resolved=["Reinmar arrived at the flood zone by the salt road."]),
            _card(
                open_threads=[
                    "Arnulf is still missing in the flood zone and unconfirmed dead."
                ]
            ),
        ],
        [
            "Reinmar pressed on while Arnulf lagged. Arnulf would not reach the ford.",
            "No one found Arnulf. Even Arnulf's pack was gone from the ledge.",
        ],
        {"c1": "Reinmar"},  # Arnulf deliberately NOT in the roster.
    )
    assert fact_reversal_summary(doc)["gap_count"] == 0


def test_summary_without_entities_still_flags_collision() -> None:
    """Absent prose/characters (empty lexicon) the witness keeps today's behavior."""
    doc = _story(
        [
            _card(resolved=["Reinmar arrived at the flood zone by the salt road."]),
            _card(
                open_threads=[
                    "Arnulf is still missing in the flood zone and unconfirmed dead."
                ]
            ),
        ]
    )
    assert fact_reversal_summary(doc)["gap_count"] == 1
