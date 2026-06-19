"""Condemn the missing entrance-manifest with a deterministic fixture (FR-539 S0).

``derive_cast_entrances`` is the CANDIDATE half of the seam-entrance pair. Where
FR-538's ``seam_entrance_gap`` measures the prose OUTCOME (who actually arrived on
the page), this derives the planning INPUT: who the Final Cut narrator *should*
stage this chapter, computed as the FR-537 scoped-cast delta against the prior
chapter's on-page presence — ``resolve_chapter_cast(cid) − on_page(prev)``.

The two lenses are deliberately different (FR-539 Judgement, paired B1): a scoped
entrant may never surface in prose (still a candidate here), and the manifest must
NEVER suppress FR-538's gap. ``test_candidate_includes_entrant_with_no_prose`` pins
that distinction — a cast member absent from the chapter's own prose is still a
candidate entrance, because this is the manifest the narrator is handed, not a
measurement of what it wrote.

Each entrant carries its ``kind`` (new/returning/continuing) plus ``last_status`` /
``last_location`` read from the entrant's OWN row in the inherited ledger only
(char-bounded, R2) — the material the narrator writes the arrival *from*.

Example tests are requirement-exempt (FR-474 J3): no ``@pytest.mark.req``.
"""

from __future__ import annotations

from examples.dungeon_master.api.cast_entrances import derive_cast_entrances


def _doc(chapters: list[dict]) -> dict:
    """Build a DM v2 doc from per-chapter specs (the single changed variable).

    Each ``chapters`` entry is ``{text, cast, [world_state], [seam_lifecycle]}``:
    - ``text``: the chapter's final-cut prose (drives on-page presence).
    - ``cast``: display names the chapter's authored ``cast`` field scopes in
      (the FR-537 ``resolve_chapter_cast`` source).
    - ``world_state`` (optional): the chapter's typed ledger ``characters`` rows,
      inherited by the NEXT chapter (drives ``last_status`` / ``last_location``).
    - ``seam_lifecycle`` (optional): ``character_lifecycle`` rows inherited by the
      NEXT chapter (drives the ``returning`` taxonomy).
    """
    order = [str(i + 1) for i in range(len(chapters))]
    cards: dict = {}
    for i, ch in enumerate(chapters):
        cid = str(i + 1)
        card: dict = {
            "title": f"Chapter {cid}",
            "reviewed": True,
            "text": ch["text"],
            "cast": ch.get("cast", []),
            "turns": [],
        }
        if "world_state" in ch:
            card["world_state"] = {"characters": ch["world_state"]}
        if "seam_lifecycle" in ch:
            card["seam_packet"] = {"character_lifecycle": ch["seam_lifecycle"]}
        cards[cid] = card
    return {
        "chapters": {"order": order, "cards": cards},
        "characters": {
            "reviewed": True,
            "roster": ["hilde", "arnulf", "reinmar"],
            "cards": {
                "hilde": {"name": "Hilde", "reviewed": True},
                "arnulf": {"name": "Arnulf", "reviewed": True},
                "reinmar": {"name": "Reinmar", "reviewed": True},
            },
        },
    }


def _by_name(entrances: list[dict]) -> dict[str, dict]:
    return {e["name"]: e for e in entrances}


# ── the candidate set: who the narrator must establish ───────────────────────


def test_entrant_absent_from_prev_prose_is_listed_new():
    """Arnulf is scoped into Ch2 but never on-page in Ch1 → a 'new' entrance.

    Hilde is on-page in Ch1 and scoped into Ch2 — the negative control, not an
    entrance. last_seen_chapter is None for a genuine newcomer.
    """
    doc = _doc(
        [
            {
                "text": "Hilde held the ridge while the clan retreated.",
                "cast": ["Hilde"],
            },
            {
                "text": "Hilde and Arnulf pressed the assault at dawn.",
                "cast": ["Hilde", "Arnulf"],
            },
        ]
    )
    entrances = _by_name(derive_cast_entrances(doc, "2"))
    assert "Hilde" not in entrances
    assert entrances["Arnulf"]["kind"] == "new"
    assert entrances["Arnulf"]["last_seen_chapter"] is None


def test_on_page_in_prev_is_not_an_entrance():
    """A character on-page in the prior chapter is continuing, not entering."""
    doc = _doc(
        [
            {"text": "Hilde and Arnulf made camp.", "cast": ["Hilde", "Arnulf"]},
            {"text": "Hilde and Arnulf broke camp.", "cast": ["Hilde", "Arnulf"]},
        ]
    )
    assert derive_cast_entrances(doc, "2") == []


def test_first_chapter_has_no_entrances():
    """The first chapter has no prior, so nothing is an entrance."""
    doc = _doc(
        [
            {"text": "Hilde stood alone at the gate.", "cast": ["Hilde", "Arnulf"]},
        ]
    )
    assert derive_cast_entrances(doc, "1") == []


def test_returning_entrant_via_inherited_lifecycle():
    """On-page Ch1, scoped out Ch2 (with a lifecycle record), back in Ch3's cast.

    The inherited ``character_lifecycle`` absence marks the return: kind
    'returning', last_seen_chapter the latest prior on-page chapter ('1').
    """
    doc = _doc(
        [
            {"text": "Hilde and Arnulf held the pass.", "cast": ["Hilde", "Arnulf"]},
            {
                "text": "Hilde pressed on alone.",
                "cast": ["Hilde"],
                "seam_lifecycle": [{"name": "Arnulf", "existence_state": "absent"}],
            },
            {"text": "Hilde and Arnulf reunited.", "cast": ["Hilde", "Arnulf"]},
        ]
    )
    arnulf = _by_name(derive_cast_entrances(doc, "3"))["Arnulf"]
    assert arnulf["kind"] == "returning"
    assert arnulf["last_seen_chapter"] == "1"


def test_continuing_entrant_scoped_out_then_back():
    """Same shape without a lifecycle record → 'continuing' (off-page, not absent)."""
    doc = _doc(
        [
            {"text": "Hilde and Arnulf held the pass.", "cast": ["Hilde", "Arnulf"]},
            {"text": "Hilde pressed on alone.", "cast": ["Hilde"]},
            {"text": "Hilde and Arnulf reunited.", "cast": ["Hilde", "Arnulf"]},
        ]
    )
    arnulf = _by_name(derive_cast_entrances(doc, "3"))["Arnulf"]
    assert arnulf["kind"] == "continuing"
    assert arnulf["last_seen_chapter"] == "1"


def test_last_status_location_from_inherited_ledger_char_bounded():
    """last_status/last_location come from the entrant's OWN inherited row only (R2).

    Arnulf enters Ch2; his Ch1 ledger row is surfaced. Hilde's row must NOT leak
    into Arnulf's manifest entry — the slice is char-bounded.
    """
    doc = _doc(
        [
            {
                "text": "Hilde held the ridge.",
                "cast": ["Hilde"],
                "world_state": [
                    {"name": "Hilde", "status": "leading", "location": "the ridge"},
                    {"name": "Arnulf", "status": "wounded", "location": "the ford"},
                ],
            },
            {
                "text": "Hilde and Arnulf pressed the assault.",
                "cast": ["Hilde", "Arnulf"],
            },
        ]
    )
    arnulf = _by_name(derive_cast_entrances(doc, "2"))["Arnulf"]
    assert arnulf["last_status"] == "wounded"
    assert arnulf["last_location"] == "the ford"


def test_candidate_includes_entrant_with_no_prose():
    """A scoped entrant absent from THIS chapter's prose is still a candidate.

    The lens distinction from FR-538 (paired B1): the manifest is the narrator's
    INPUT (who should be staged), not a measurement of the prose. Arnulf is scoped
    into Ch2 but never named in Ch2's text — he is still listed, because the
    manifest must hand the narrator the entrant to establish; it never suppresses
    FR-538's gap, which separately measures whether the prose did so.
    """
    doc = _doc(
        [
            {"text": "Hilde held the ridge.", "cast": ["Hilde"]},
            {"text": "Hilde pressed the assault at dawn.", "cast": ["Hilde", "Arnulf"]},
        ]
    )
    assert "Arnulf" in _by_name(derive_cast_entrances(doc, "2"))
