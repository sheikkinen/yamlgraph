"""Prototype tests for DM v2 full-story Markdown render (FR-494 Part 1).

A *visibility* harness, not a governance gate (FR-474 J3): no ``@pytest.mark.req``.
These pin the **deterministic** full-story render — a pure function over the whole
story doc, **no LLM, no I/O**. The Book body is reused verbatim from
``chapter_ops.compose_book_deterministic`` (J3); the renderer only frames it with
the tagline lead, the synopsis, and the cast.

The load-bearing assertions:
- no invented title (the tagline is a paragraph; there is no title field — J1);
  the tagline appears as a blockquote lead and every section sits at H1;
- synopsis and (optional) cast precede the chapter body, in that order;
- a character with empty card text is dropped; an empty roster drops the whole
  ``# Cast`` section (J2);
- the world-state ledger never reaches the manuscript; and
- an empty book (no chapter played) raises rather than returning "" — the front
  matter alone is not a story (J3, inherited from the Book compose).

Run directly:
    pytest examples/dungeon_master/tests/test_render.py --no-cov
"""

from __future__ import annotations

import pytest

from examples.dungeon_master.api import render


def _full_story() -> dict:
    """A complete doc: tagline + synopsis + reviewed cast + two played chapters."""
    return {
        "tagline": "A drowned valley, a survival truce, and the flood as judgment.",
        "synopsis": {
            "text": "Hilde and Gunnar are stranded together as the rivers rise.",
            "reviewed": True,
        },
        "characters": {
            "reviewed": True,
            "roster": ["hilde", "gunnar"],
            "cards": {
                "hilde": {
                    "name": "Hilde",
                    "text": "War-leader of the Aschenwulf band.\n\nFierce, loyal.",
                    "reviewed": True,
                },
                "gunnar": {
                    "name": "Gunnar",
                    "text": "The man she came to kill.",
                    "reviewed": True,
                },
            },
        },
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "title": "The Water Rises",
                    "text": "Hilde musters the band at the failing dam.",
                    "world_state": "WS1: the dam holds, for now.",
                },
                "2": {
                    "title": "The Last Ledge",
                    "text": "Hilde and Gunnar are stranded on the shrinking ledge.",
                    "world_state": "WS2: the truce hardens.",
                },
            },
        },
    }


def test_render_opens_with_tagline_lead_and_no_invented_title():
    doc = _full_story()
    md = render.render_story_markdown(doc)
    # The tagline is the blockquote lead — not a heading (J1: no title field).
    assert md.startswith("> A drowned valley")
    # No invented top-level title line precedes the tagline.
    assert "# Untitled" not in md
    # Every section header is H1, never H2 (flat hierarchy so the Book body — also
    # H1 — is reused verbatim).
    assert "## " not in md


def test_render_orders_tagline_synopsis_cast_then_chapters():
    doc = _full_story()
    md = render.render_story_markdown(doc)
    assert (
        md.index("> A drowned valley")
        < md.index("# Synopsis")
        < md.index("# Cast")
        < md.index("# Chapter 1: The Water Rises")
        < md.index("# Chapter 2: The Last Ledge")
    )
    assert "Hilde and Gunnar are stranded together as the rivers rise." in md


def test_render_cast_uses_first_paragraph_only():
    doc = _full_story()
    md = render.render_story_markdown(doc)
    assert "**Hilde** — War-leader of the Aschenwulf band." in md
    # Only the first \n\n-split paragraph of the card; the rest is dropped.
    assert "Fierce, loyal." not in md
    assert "**Gunnar** — The man she came to kill." in md


def test_render_cast_extracts_summary_value_from_labeled_sheet():
    # FR-496: the character card is a labeled SHEET (SUMMARY:/ROLE:/ORIGIN:…)
    # joined by single newlines, so split("\n\n")[0] would leak the WHOLE sheet.
    # The cast gloss must be the SUMMARY value alone — none of the other labels.
    doc = _full_story()
    doc["characters"]["cards"]["hilde"]["text"] = (
        "SUMMARY: A war-leader who came to kill and stayed to survive.\n"
        "ROLE: Band leader of the Aschenwulf.\n"
        "ORIGIN: The drowned northern valleys.\n"
        "APPEARANCE: Scarred, river-soaked, unbowed.\n"
        "PERSONALITY: Fierce, loyal, unyielding.\n"
        "DRIVE: Vengeance, then mercy.\n"
        "BOND: Gunnar.\n"
        "FLAW: Cannot forgive herself."
    )
    md = render.render_story_markdown(doc)
    assert "**Hilde** — A war-leader who came to kill and stayed to survive." in md
    # None of the sheet scaffolding leaks into the cast line.
    assert "SUMMARY:" not in md
    assert "ROLE:" not in md
    assert "ORIGIN:" not in md
    assert "APPEARANCE:" not in md
    assert "FLAW:" not in md


def test_render_cast_summary_match_is_case_and_whitespace_tolerant():
    # J3: match only SUMMARY:, but tolerate leading whitespace and any case.
    doc = _full_story()
    doc["characters"]["cards"]["gunnar"]["text"] = (
        "  summary:   The man she came to kill.\nROLE: The hunted."
    )
    md = render.render_story_markdown(doc)
    assert "**Gunnar** — The man she came to kill." in md
    assert "ROLE:" not in md


def test_render_cast_plain_prose_without_summary_falls_back():
    # J4: a card with no SUMMARY: label keeps the FR-494 first-paragraph behaviour.
    doc = _full_story()
    doc["characters"]["cards"]["hilde"]["text"] = (
        "War-leader of the Aschenwulf band.\n\nFierce, loyal."
    )
    md = render.render_story_markdown(doc)
    assert "**Hilde** — War-leader of the Aschenwulf band." in md
    assert "Fierce, loyal." not in md


def test_render_drops_empty_character_cards():
    doc = _full_story()
    doc["characters"]["cards"]["gunnar"]["text"] = "   "
    md = render.render_story_markdown(doc)
    assert "**Hilde**" in md
    assert "**Gunnar**" not in md


def test_render_omits_cast_section_when_roster_empty():
    doc = _full_story()
    doc["characters"] = {"reviewed": False, "roster": [], "cards": {}}
    md = render.render_story_markdown(doc)
    assert "# Cast" not in md
    # The story still renders its synopsis and chapters.
    assert "# Synopsis" in md
    assert "# Chapter 1: The Water Rises" in md


def test_render_suppresses_world_state_ledger():
    doc = _full_story()
    md = render.render_story_markdown(doc)
    assert "WS1" not in md
    assert "WS2" not in md


def test_render_reuses_book_body_verbatim():
    from examples.dungeon_master.api import chapter_ops

    doc = _full_story()
    md = render.render_story_markdown(doc)
    body = chapter_ops.compose_book_deterministic(doc)
    # The Book body appears unchanged inside the manuscript (J3 — reuse, not
    # reimplement; the renderer only prepends front matter).
    assert body in md


def test_render_raises_when_no_chapter_played():
    doc = _full_story()
    doc["chapters"]["cards"]["1"]["text"] = ""
    doc["chapters"]["cards"]["2"]["text"] = ""
    # Inherits the Book compose's raise — the front matter alone is not a story.
    with pytest.raises(ValueError):
        render.render_story_markdown(doc)
