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

from unittest.mock import patch

import pytest

from examples.dungeon_master.api import chapter_ops


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
