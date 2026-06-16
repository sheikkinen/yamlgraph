"""Prototype tests for DM v2 book-scope chapters (FR-488).

A *visibility* harness, not a governance gate (FR-474 J3/J4): no
``@pytest.mark.req``. These pin the book-scope planning layer added after the
synopsis — the chapter outline (synopsis split into one-paragraph chapter
summaries) and the per-chapter expansion that carries an explicit ``world_state``
forward from the previous chapter.

The load-bearing test is the **forward-carry seam** (J7), preserved through play
(FR-491): closing played ``chapter:2`` must thread ``chapter:1``'s ``world_state``
into the chapter-close graph variables, and a chapter's play (``running_scene``)
must see the previous chapter's world_state — never its turns. That is a
deterministic-plumbing assertion — the mock supplies the world-state content; the
test proves the wiring delivers it.

Run directly:
    pytest examples/dungeon_master/tests/test_chapters.py --no-cov
"""

from __future__ import annotations

import asyncio
import copy
from unittest.mock import patch

from examples.dungeon_master.api import chapter_ops

SYNOPSIS_TEXT = "Kara leads the band against a rival raider as the floodwaters rise."

# A structured two-chapter outline (J1): {chapters: [{title, summary}]} — the
# shape split_roster cannot carry, so the outline is parsed as JSON, not lines.
OUTLINE = {
    "chapters": [
        {"title": "Chapter 1 — The Water Rises", "summary": "Kara musters the band."},
        {"title": "Chapter 2 — The Last Ledge", "summary": "Kara corners the raider."},
    ]
}


def _capturing_mock(captured: list[dict]):
    """A mock execute_prompt that records the chapter-close graph's variables (J7)."""

    def _mock(prompt_name, variables=None, **kwargs):
        variables = variables or {}
        if prompt_name == "chapter_outline":
            return OUTLINE
        if prompt_name == "chapter_close":
            captured.append(dict(variables))
            return {
                "world_state": (
                    f"WS@{variables.get('index', '?')} "
                    f"(prev={variables.get('previous_world_state') or 'none'})"
                ),
            }
        if prompt_name == "final_cut":
            # The per-chapter finish (FR-492): compose the chapter's final text
            # from its played arc. The mock echoes the assembled arc so a test can
            # see the recaps flowed into the composed prose.
            return f"FINAL CUT: {variables.get('arc', '')}"
        raise AssertionError(f"unexpected prompt {prompt_name!r}")

    return _mock


def _patched(mock):
    return patch.multiple(
        "yamlgraph.node_factory.llm_nodes",
        execute_prompt=mock,
    ), patch.multiple(
        "yamlgraph.executor",
        execute_prompt=mock,
    )


def _run(coro):
    return asyncio.run(coro)


def _doc_with_chapters() -> dict:
    """A doc whose synopsis is reviewed and whose chapter outline is already derived."""
    return {
        "synopsis": {"text": SYNOPSIS_TEXT, "reviewed": True},
        "chapters": {
            "reviewed": False,
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "title": "Chapter 1 — The Water Rises",
                    "summary": "Kara musters the band.",
                    "text": "Chapter 1 full text.",
                    "world_state": "WS1-CARRIED-FORWARD",
                    "reviewed": True,
                },
                "2": {
                    "title": "Chapter 2 — The Last Ledge",
                    "summary": "Kara corners the raider.",
                    "text": "",
                    "world_state": "",
                    "reviewed": False,
                },
            },
        },
    }


# ── J7: the forward-carry seam ───────────────────────────────────────────────


def test_close_chapter_threads_previous_chapter_world_state():
    doc = _doc_with_chapters()
    # Chapter 2 has been played: closing it derives its end-of-chapter world_state
    # from the inherited ledger + the played recaps (FR-491 B).
    doc["chapters"]["cards"]["2"]["turns"] = [
        {"n": 1, "recap": {"text": "Kara corners the raider on the ledge."}}
    ]
    captured: list[dict] = []
    mock = _capturing_mock(captured)
    m1, m2 = _patched(mock)
    with m1, m2:
        result = _run(chapter_ops.close_chapter(doc, "2"))
    assert len(captured) == 1
    # The plumbing delivered chapter 1's world_state to chapter 2's close.
    assert "WS1-CARRIED-FORWARD" in captured[0]["previous_world_state"]
    # And chapter 2 read its own summary, not chapter 1's.
    assert "corners the raider" in captured[0]["summary"]
    # The played recaps are delivered to the close graph for the world_state.
    assert "on the ledge" in captured[0]["recaps"]
    # The chapter's final text is the per-chapter Final Cut composed over its arc
    # (FR-492), so the played recap flows through into the prose.
    assert "on the ledge" in result["text"]
    # The close returns the new world-state ledger the next chapter inherits.
    assert result["world_state"]


def test_close_chapter_one_has_no_previous_world_state():
    doc = _doc_with_chapters()
    doc["chapters"]["cards"]["1"]["turns"] = [
        {"n": 1, "recap": {"text": "Kara musters the band at dawn."}}
    ]
    captured: list[dict] = []
    mock = _capturing_mock(captured)
    m1, m2 = _patched(mock)
    with m1, m2:
        _run(chapter_ops.close_chapter(doc, "1"))
    # Chapter 1 is the first: there is no prior world state to carry.
    assert captured[0]["previous_world_state"] == ""


def test_chapter_two_play_sees_chapter_one_world_state_not_its_turns():
    """A chapter's play reads the PREVIOUS chapter's world_state, never its turns.

    The slice-3 load-bearing seam (FR-491): each chapter is played from where the
    last left off. ``running_scene`` for chapter 2 must inherit chapter 1's
    end-of-chapter ``world_state`` (the established START) and read chapter 2's own
    summary — but it must NOT see chapter 1's played turns, which are private to
    chapter 1's loop.
    """
    from examples.dungeon_master.api import turn_ops

    doc = {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "title": "Chapter 1 — The Water Rises",
                    "summary": "Kara musters the band.",
                    "world_state": "WS1-AFTER-CHAPTER-ONE",
                    "turns": [
                        {"n": 1, "recap": {"text": "CH1-TURN-RECAP private to ch 1."}}
                    ],
                },
                "2": {
                    "title": "Chapter 2 — The Last Ledge",
                    "summary": "Kara corners the raider.",
                    "world_state": "",
                    "turns": [],
                },
            },
        },
    }
    scene = turn_ops.running_scene(doc, "2", 1)
    # Chapter 2's play inherits chapter 1's end-of-chapter world_state (the carry)…
    assert "WS1-AFTER-CHAPTER-ONE" in scene
    # …and reads its own summary…
    assert "Kara corners the raider" in scene
    # …but NOT chapter 1's played turns (private to chapter 1's loop).
    assert "CH1-TURN-RECAP" not in scene


# ── J1: the outline is a structured parse, not a split_roster mirror ─────────


def test_outline_chapters_parses_structured_title_summary():
    doc = {"synopsis": {"text": SYNOPSIS_TEXT, "reviewed": True}}
    mock = _capturing_mock([])
    m1, m2 = _patched(mock)
    with m1, m2:
        chapters = _run(chapter_ops.outline_chapters(doc))
    assert [c["title"] for c in chapters] == [
        "Chapter 1 — The Water Rises",
        "Chapter 2 — The Last Ledge",
    ]
    assert all(c["summary"] for c in chapters)


# ── purity: chapter_ops must not mutate the doc it reads ──────────────────────


def test_close_chapter_does_not_mutate_doc():
    doc = _doc_with_chapters()
    doc["chapters"]["cards"]["2"]["turns"] = [
        {"n": 1, "recap": {"text": "Kara corners the raider on the ledge."}}
    ]
    before = copy.deepcopy(doc)
    mock = _capturing_mock([])
    m1, m2 = _patched(mock)
    with m1, m2:
        _run(chapter_ops.close_chapter(doc, "2"))
    assert doc == before


# ── J3: chapters are independent of the preplan/play gate ────────────────────


def test_chapters_do_not_affect_preplan_complete():
    from examples.dungeon_master.api import tree

    # A doc with a fully derived chapter set but NO cast: the cast gate must stay
    # closed — chapters are a separate branch (J3).
    doc = {
        "synopsis": {"text": SYNOPSIS_TEXT, "reviewed": True},
        "chapters": {
            "reviewed": True,
            "order": ["1", "2"],
            "cards": {
                "1": {"reviewed": True},
                "2": {"reviewed": True},
            },
        },
    }
    assert tree.cast_complete(doc) is False
    # And a complete cast stays complete regardless of chapter state.
    doc["characters"] = {
        "roster": ["kara"],
        "cards": {"kara": {"reviewed": True}},
    }
    assert tree.cast_complete(doc) is True


def test_chapters_appear_as_breadcrumb_peer_of_characters():
    from examples.dungeon_master.api import tree

    doc = {
        "synopsis": {"text": SYNOPSIS_TEXT, "reviewed": True},
        "chapters": {"order": ["1"], "cards": {"1": {"title": "One"}}},
        "characters": {"roster": ["kara"], "cards": {"kara": {"name": "Kara"}}},
        "stage": "chapters",
    }
    labels = [c["label"] for c in tree.breadcrumb(doc)]
    assert "Chapters" in labels
    # Chapters sits after Synopsis and before Characters (independent branch).
    assert labels.index("Synopsis") < labels.index("Chapters")
    assert labels.index("Chapters") < labels.index("Characters")


# ── J6: the chapter set is FIXED at derivation (idempotent expansion) ─────────


def test_expand_chapters_is_idempotent(tmp_path, monkeypatch):
    from examples.dungeon_master.api import session as session_mod

    monkeypatch.setattr(session_mod, "STORY_ROOT", tmp_path)
    session_mod._reset_caches()

    calls = {"outline": 0}

    def _counting_mock(prompt_name, variables=None, **kwargs):
        variables = variables or {}
        if prompt_name == "chapter_outline":
            calls["outline"] += 1
            return OUTLINE
        raise AssertionError(f"unexpected prompt {prompt_name!r}")

    m1, m2 = _patched(_counting_mock)
    sess = session_mod.DMSession("ch-idem")
    doc = {"synopsis": {"text": SYNOPSIS_TEXT, "reviewed": True}}
    story_dir = tmp_path / "ch-idem"
    story_dir.mkdir(parents=True, exist_ok=True)
    with m1, m2:
        _run(sess._expand_chapters(doc, story_dir))
        order_first = list(doc["chapters"]["order"])
        # A second derivation must be a no-op: numeric ids cannot append like
        # slugs, so the set is fixed (J6) and the outline graph is not re-run.
        _run(sess._expand_chapters(doc, story_dir))
    assert calls["outline"] == 1
    assert doc["chapters"]["order"] == order_first == ["1", "2"]


# ── FR-490: the chapter outline needs a face (overview card + navigation) ─────
#
# The outline is the load-bearing view of book scope, yet FR-488 gave it no
# surface (J1). These pin the presentation/navigation seam: the repurposed
# (formerly dead) ``chapters`` stage is a read-only overview the group crumb
# lands on; ``StageView`` carries the outline projection and per-chapter
# ``summary``/``world_state``; member peers are discoverable from the overview.


def _view_doc_with_chapters() -> dict:
    """A reviewed-synopsis doc with a derived two-chapter set (chapter 1 expanded)."""
    return {
        "synopsis": {"text": SYNOPSIS_TEXT, "reviewed": True},
        "chapters": {
            "reviewed": False,
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "title": "Chapter 1 — The Water Rises",
                    "summary": "Kara musters the band.",
                    "text": "Chapter 1 full text.",
                    "world_state": "WS1-CARRIED-FORWARD",
                    "reviewed": True,
                },
                "2": {
                    "title": "Chapter 2 — The Last Ledge",
                    "summary": "Kara corners the raider.",
                    "text": "",
                    "world_state": "",
                    "reviewed": False,
                },
            },
        },
    }


# ── J5: StageView carries the outline + per-chapter context ───────────────────


def test_view_populates_summary_and_world_state_for_chapter_card():
    from examples.dungeon_master.api import session as session_mod

    sess = session_mod.DMSession("v490")
    doc = _view_doc_with_chapters()
    doc["stage"] = "chapter:1"
    view = sess._view(doc)
    assert view.kind == "chapter"
    # The card's summary (what this chapter is) and inherited world_state (the
    # J7 forward-carry) are surfaced on the view, above the prose.
    assert view.summary == "Kara musters the band."
    assert view.world_state == "WS1-CARRIED-FORWARD"


def test_view_populates_chapters_list_for_overview():
    from examples.dungeon_master.api import session as session_mod

    sess = session_mod.DMSession("v490")
    doc = _view_doc_with_chapters()
    doc["stage"] = "chapters"
    view = sess._view(doc)
    assert view.kind == "chapters"
    # The overview projects the ordered set as {id, title, summary, reviewed}.
    assert [c["id"] for c in view.chapters] == ["1", "2"]
    assert [c["title"] for c in view.chapters] == [
        "Chapter 1 — The Water Rises",
        "Chapter 2 — The Last Ledge",
    ]
    assert [c["summary"] for c in view.chapters] == [
        "Kara musters the band.",
        "Kara corners the raider.",
    ]
    assert [c["reviewed"] for c in view.chapters] == [True, False]


def test_view_leaves_chapter_fields_empty_for_non_chapter_stage():
    from examples.dungeon_master.api import session as session_mod

    sess = session_mod.DMSession("v490")
    doc = _view_doc_with_chapters()
    doc["stage"] = "synopsis"
    view = sess._view(doc)
    # Additive: every non-chapter stage leaves the new fields at their defaults.
    assert view.summary == ""
    assert view.world_state == ""
    assert view.chapters == []


# ── J4: the overview reads the chapter group dict without mutating it ─────────


def test_view_on_overview_does_not_mutate_chapter_group():
    from examples.dungeon_master.api import session as session_mod

    sess = session_mod.DMSession("v490")
    doc = _view_doc_with_chapters()
    doc["stage"] = "chapters"
    before = copy.deepcopy(doc["chapters"])
    sess._view(doc)
    # ``_entry("chapters")`` aliases the {reviewed, order, cards} group dict; the
    # generic setdefault must be a harmless no-op (J4) — never corrupting it.
    assert doc["chapters"] == before


# ── J6: the group crumb lands on the overview; peers visible from it ──────────


def test_chapters_group_crumb_lands_on_overview():
    from examples.dungeon_master.api import tree

    doc = _view_doc_with_chapters()
    doc["stage"] = "synopsis"
    crumbs = tree.breadcrumb(doc)
    group = next(c for c in crumbs if c["label"] == "Chapters")
    # The group crumb opens the table of contents, not blind into chapter 1.
    assert group["stage"] == "chapters"


def test_chapter_member_peers_visible_from_overview():
    from examples.dungeon_master.api import tree

    doc = _view_doc_with_chapters()
    doc["stage"] = "chapters"
    labels = [c["label"] for c in tree.breadcrumb(doc)]
    # Standing on the overview, every chapter is a discoverable member peer.
    assert "Chapter 1 — The Water Rises" in labels
    assert "Chapter 2 — The Last Ledge" in labels
