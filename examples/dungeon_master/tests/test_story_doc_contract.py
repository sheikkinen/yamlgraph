"""Condemn the untyped story-doc boundary that FR-556 (Contract A) closes.

THE DEFECT (structural, from the v2 refactoring plan): the chapter sub-tree
(``doc["chapters"]["cards"][<cid>]``) is a raw nested dict that 14 of 32 api
modules reach into directly. Nothing types the card shape, so a malformed write
(``beats`` a string, ``turns`` a dict) is committed silently and only manifests
downstream as a degraded instrument read. Contract A introduces the ONE typed
accessor: a :class:`StoryDoc` model that a live book validates against (the
boundary parse) and a structural SETTER (:func:`chapter_nav.write_chapter_card`)
that REJECTS a structurally-invalid card at the write seam -- the seam Contract C
(FR-558) later binds the gate battery to.

These tests prove (a) a representative, real-shaped doc -- including legacy and
derived card fields (``world_state`` as the empty-string placeholder, a
``seam_packet`` dict, free ``text``) -- validates via ``story_doc.parse``; (b) the
typed setter persists a well-formed card readable back through the accessor; and
(c) the setter raises ``InvalidChapterCard`` on a structurally-broken card rather
than committing it. (b)+(c) are the new capability; (a) is the characterization
net proving the parse does not reject the shape the codebase actually writes.

Example tests are requirement-exempt (FR-474 J3): no ``@pytest.mark.req``.
"""

from __future__ import annotations

import pytest

from examples.dungeon_master.api import chapter_nav, story_doc

# A representative two-chapter book mirroring the real persisted shape: the
# structural backbone (order, cards, beats, turns) plus the legacy/derived fields
# the boundary must tolerate -- ``world_state`` written as the ``""`` placeholder by
# ``expand_chapters`` AND a typed ledger dict on the closed chapter, a ``seam_packet``
# mapping, free ``text``, and a played ``turns`` list.
_REPRESENTATIVE_DOC = {
    "tagline": "An age of flood and feud",
    "chapters": {
        "order": ["1", "2"],
        "cards": {
            "1": {
                "title": "The Flood Rises",
                "summary": "The river breaks its banks and the band flees to high ground.",
                "beats": [
                    "The river breaks its banks at dawn",
                    "The band abandons the lowland steading",
                    "They reach the high ridge by dusk",
                ],
                "cast": ["Arnulf", "Sela"],
                "entry_state": "",
                "exit_state": "the band holds the high ridge",
                "text": "The water came before the light did...",
                "world_state": {"location": "high ridge", "morale": "shaken"},
                "seam_packet": {"carried": ["the feud is unresolved"]},
                "reviewed": True,
                "turns": [
                    {"n": 1, "direction": {"cast_exits": []}},
                    {"n": 2, "direction": {"cast_exits": []}},
                ],
            },
            "2": {
                "title": "The Ridge Holds",
                "summary": "Refugees gather and the old feud reopens.",
                "beats": ["Refugees arrive", "The feud reopens"],
                "cast": ["Arnulf"],
                "entry_state": "the band holds the high ridge",
                "exit_state": "",
                "text": "",
                "world_state": "",
                "seam_packet": {},
                "reviewed": False,
            },
        },
    },
}


def test_representative_doc_validates_at_boundary():
    """A real-shaped book -- legacy ``world_state=''`` and typed-ledger cards alike
    -- parses cleanly; the boundary type tolerates what the codebase actually writes."""
    parsed = story_doc.parse(_REPRESENTATIVE_DOC)
    assert parsed.chapters.order == ["1", "2"]
    assert set(parsed.chapters.cards) == {"1", "2"}
    # Backbone is typed; derived/legacy fields ride along untouched (extra='allow').
    assert parsed.chapters.cards["1"].beats[0].startswith("The river breaks")
    assert len(parsed.chapters.cards["1"].turns) == 2


def test_write_chapter_card_persists_valid_card():
    """The typed setter is the write seam: a well-formed card it accepts is readable
    back through the accessor, byte-for-byte."""
    doc: dict = {"chapters": {"order": ["1"], "cards": {}}}
    card = {
        "title": "A New Chapter",
        "summary": "Something happens.",
        "beats": ["It begins", "It ends"],
        "cast": ["Sela"],
        "entry_state": "",
        "exit_state": "",
    }
    chapter_nav.write_chapter_card(doc, "1", card)
    assert chapter_nav.chapter_card(doc, "1") == card
    assert chapter_nav.chapter_turns(doc, "1") == []


def test_write_chapter_card_rejects_structurally_invalid_card():
    """The setter REJECTS a structurally-broken card (``beats`` a string, not a list)
    at the write boundary instead of committing it -- the seam FR-558 binds gates to."""
    doc: dict = {"chapters": {"order": ["1"], "cards": {}}}
    broken = {"title": "Broken", "summary": "x", "beats": "not-a-list"}
    with pytest.raises(story_doc.InvalidChapterCard):
        chapter_nav.write_chapter_card(doc, "1", broken)
    # The malformed card was not committed.
    assert chapter_nav.chapter_card(doc, "1") == {}
