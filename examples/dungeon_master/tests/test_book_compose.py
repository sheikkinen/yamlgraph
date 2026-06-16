"""Prototype tests for DM v2 deterministic book composition (FR-492 Phase 3).

A *visibility* harness, not a governance gate (FR-474 J3/J4): no
``@pytest.mark.req``. These pin the **deterministic** book assembly — a pure
function over the chapters' already-final texts, with **no LLM on the path**. The
model is off the road to a *first* book: composition is free, reproducible, and
never empty when a chapter has been played.

The load-bearing assertions:
- zero graph/LLM invocations (the function never reaches ``get_app``);
- chapters render in ``chapters.order``, each as ``# Chapter {n}: {title}`` +
  its beat-faithful final ``text``;
- the world-state ledger is suppressed from the reader manuscript; and
- an empty book (no chapter played) raises rather than returning "" (Commandment
  6: no silent fallback).

Run directly:
    pytest examples/dungeon_master/tests/test_book_compose.py --no-cov
"""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest

from examples.dungeon_master.api import chapter_ops, navigation, tree


def _played_book() -> dict:
    """A two-chapter doc whose chapters have both been played to a final text."""
    return {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "title": "The Water Rises",
                    "text": "Kara musters the band at the failing dam.",
                    "world_state": "WS1: the dam holds, for now.",
                },
                "2": {
                    "title": "The Last Ledge",
                    "text": "Kara corners the raider on the ledge.",
                    "world_state": "WS2: the raider is cornered.",
                },
            },
        }
    }


def _no_llm_guard():
    # compose is PURE: reaching the graph app is the failure we want to catch.
    def _boom(*_a, **_k):
        raise AssertionError("compose_book_deterministic must not invoke any graph/LLM")

    return patch.object(chapter_ops, "get_app", _boom)


def test_compose_orders_chapters_and_titles_them():
    doc = _played_book()
    with _no_llm_guard():
        book = chapter_ops.compose_book_deterministic(doc)
    # Chapter 1's heading + text precedes chapter 2's, in chapters.order.
    assert book.index("# Chapter 1: The Water Rises") < book.index(
        "# Chapter 2: The Last Ledge"
    )
    assert "Kara musters the band at the failing dam." in book
    assert "Kara corners the raider on the ledge." in book


def test_compose_suppresses_world_state_ledger():
    doc = _played_book()
    with _no_llm_guard():
        book = chapter_ops.compose_book_deterministic(doc)
    # The forward-carry ledger is plumbing, not manuscript: it never reaches the
    # reader's book.
    assert "WS1" not in book
    assert "WS2" not in book


def test_compose_skips_unplayed_chapters_but_keeps_played_order():
    doc = _played_book()
    # Chapter 2 has not been played to a final text yet.
    doc["chapters"]["cards"]["2"]["text"] = ""
    with _no_llm_guard():
        book = chapter_ops.compose_book_deterministic(doc)
    assert "# Chapter 1: The Water Rises" in book
    assert "The Last Ledge" not in book


def test_compose_raises_when_no_chapter_played():
    doc = _played_book()
    doc["chapters"]["cards"]["1"]["text"] = ""
    doc["chapters"]["cards"]["2"]["text"] = ""
    with _no_llm_guard(), pytest.raises(ValueError):
        chapter_ops.compose_book_deterministic(doc)


# ── FR-495: the composer owns the ordinal; a self-asserted "Chapter N —" prefix
# in the LLM-authored title must not double the heading. ──


def _titled_book(title_1: str, title_2: str = "The Last Ledge") -> dict:
    return {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {"title": title_1, "text": "Kara musters the band."},
                "2": {"title": title_2, "text": "Kara corners the raider."},
            },
        }
    }


def test_compose_strips_self_asserted_chapter_label():
    # The outline title self-asserts its own ordinal; the composer's n is the
    # authority, so the heading must read once — not "Chapter 1: Chapter 1 —".
    doc = _titled_book("Chapter 1 — The Frozen Crossing")
    with _no_llm_guard():
        book = chapter_ops.compose_book_deterministic(doc)
    assert "# Chapter 1: The Frozen Crossing" in book
    assert "Chapter 1: Chapter 1" not in book


def test_compose_keeps_clean_title_untouched():
    doc = _titled_book("The Frozen Crossing")
    with _no_llm_guard():
        book = chapter_ops.compose_book_deterministic(doc)
    assert "# Chapter 1: The Frozen Crossing" in book


def test_compose_label_only_title_collapses_without_dangling_separator():
    # J2: a title that cleans to empty (a label + trailing separator, or an empty
    # title) yields "# Chapter {n}" with NO trailing ": " — the ordinal appears
    # once, no dangling colon. (A bare "Chapter 1" with no separator is left to
    # the \s+ guard, J3, and is not this case.)
    doc = _titled_book("Chapter 1 —", title_2="")
    with _no_llm_guard():
        book = chapter_ops.compose_book_deterministic(doc)
    assert "# Chapter 1\n\n" in book
    assert "# Chapter 1:" not in book
    assert "# Chapter 2\n\n" in book
    assert "# Chapter 2:" not in book


def test_compose_real_title_beginning_with_ch_word_is_untouched():
    # J3: the required \s+ guard — a real title that merely begins with "Ch…" or
    # "Chapter <word>" with no separator must NOT be eaten.
    doc = _titled_book("Children of the Thaw", title_2="Chapter Endings")
    with _no_llm_guard():
        book = chapter_ops.compose_book_deterministic(doc)
    assert "# Chapter 1: Children of the Thaw" in book
    assert "# Chapter 2: Chapter Endings" in book


def test_compose_strips_varied_chapter_label_separators():
    # Colon, en-dash, and a spelled ordinal all count as the self-asserted prefix.
    for raw, want in (
        ("Chapter 2: The Fort Defended", "# Chapter 1: The Fort Defended"),
        ("Chapter Three – The Crossing", "# Chapter 1: The Crossing"),
        ("Ch. 4 - The Thaw", "# Chapter 1: The Thaw"),
    ):
        doc = _titled_book(raw)
        with _no_llm_guard():
            book = chapter_ops.compose_book_deterministic(doc)
        assert want in book


# ── The Book stage: the terminal leaf that renders the deterministic compose ──


def _played_reviewed_book() -> dict:
    """A whole story whose chapters are all PLAYED to a reviewed final text.

    ``all_chapters_played`` is the Book gate: the chapter order is non-empty and
    every chapter card is reviewed (played to its director-judged end).
    """
    return {
        "synopsis": {"text": "s", "reviewed": True},
        "characters": {
            "reviewed": True,
            "roster": ["kara"],
            "cards": {"kara": {"name": "Kara", "text": "c", "reviewed": True}},
        },
        "chapters": {
            "reviewed": False,
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "title": "The Water Rises",
                    "text": "Kara musters the band at the failing dam.",
                    "world_state": "WS1",
                    "reviewed": True,
                },
                "2": {
                    "title": "The Last Ledge",
                    "text": "Kara corners the raider on the ledge.",
                    "world_state": "WS2",
                    "reviewed": True,
                },
            },
        },
    }


def test_all_chapters_played_gate():
    doc = _played_reviewed_book()
    assert tree.all_chapters_played(doc) is True
    # An unplayed chapter closes the gate.
    doc["chapters"]["cards"]["2"]["reviewed"] = False
    assert tree.all_chapters_played(doc) is False
    # And an empty chapter set is not "all played".
    assert tree.all_chapters_played({"chapters": {"order": [], "cards": {}}}) is False


def test_book_reachable_only_when_all_chapters_played():
    doc = _played_reviewed_book()
    assert navigation.can_visit(doc, "book") is True
    doc["chapters"]["cards"]["2"]["reviewed"] = False
    assert navigation.can_visit(doc, "book") is False


def test_book_crumb_appears_only_when_all_chapters_played():
    doc = _played_reviewed_book()
    labels = [c["label"] for c in tree.breadcrumb(doc)]
    assert "The Book" in labels
    # The Book is the terminal leaf, after Characters.
    assert labels.index("Characters") < labels.index("The Book")
    # Close the gate: the crumb disappears.
    doc["chapters"]["cards"]["2"]["reviewed"] = False
    assert "The Book" not in [c["label"] for c in tree.breadcrumb(doc)]


def test_book_stage_first_render_composes_manuscript(tmp_path, monkeypatch):
    from examples.dungeon_master.api import session as session_mod
    from examples.dungeon_master.api import story_doc

    monkeypatch.setattr(session_mod, "STORY_ROOT", tmp_path)
    session_mod._reset_caches()

    story_dir = tmp_path / "book-render"
    story_dir.mkdir(parents=True, exist_ok=True)
    story_doc.write(story_dir, _played_reviewed_book())

    sess = session_mod.DMSession("book-render")
    # No LLM mock: the Book stage has no seed, so navigating to it must NOT invoke
    # any graph — its first render is the pure deterministic compose.
    view = asyncio.run(sess.navigate("book"))
    assert view.kind == "book"
    assert "# Chapter 1: The Water Rises" in view.text
    assert "# Chapter 2: The Last Ledge" in view.text
    assert "WS1" not in view.text  # the world_state ledger stays out of the book
