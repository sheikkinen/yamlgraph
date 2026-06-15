"""Prototype tests for DM v2 book-scope chapters (FR-488).

A *visibility* harness, not a governance gate (FR-474 J3/J4): no
``@pytest.mark.req``. These pin the book-scope planning layer added after the
synopsis — the chapter outline (synopsis split into one-paragraph chapter
summaries) and the per-chapter expansion that carries an explicit ``world_state``
forward from the previous chapter.

The load-bearing test is the **forward-carry seam** (J7): expanding ``chapter:2``
must thread ``chapter:1``'s ``world_state`` into the chapter graph variables. That
is a deterministic-plumbing assertion — the mock supplies the world-state content;
the test proves the wiring delivers it.

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
    """A mock execute_prompt that records the chapter graph's variables (J7)."""

    def _mock(prompt_name, variables=None, **kwargs):
        variables = variables or {}
        if prompt_name == "chapter_outline":
            return OUTLINE
        if prompt_name == "chapter":
            captured.append(dict(variables))
            return {
                "text": f"Chapter {variables.get('index', '?')} full text.",
                "world_state": (
                    f"WS@{variables.get('index', '?')} "
                    f"(prev={variables.get('previous_world_state') or 'none'})"
                ),
            }
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


def test_chapter_two_expansion_threads_chapter_one_world_state():
    doc = _doc_with_chapters()
    captured: list[dict] = []
    mock = _capturing_mock(captured)
    m1, m2 = _patched(mock)
    with m1, m2:
        result = _run(chapter_ops.invoke_chapter(doc, 2))
    assert len(captured) == 1
    # The plumbing delivered chapter 1's world_state to chapter 2's expansion.
    assert "WS1-CARRIED-FORWARD" in captured[0]["previous_world_state"]
    # And chapter 2 read its own summary, not chapter 1's.
    assert "corners the raider" in captured[0]["summary"]
    # The expansion returns both the prose and the new world-state ledger.
    assert result["text"]
    assert result["world_state"]


def test_chapter_one_expansion_has_no_previous_world_state():
    doc = _doc_with_chapters()
    captured: list[dict] = []
    mock = _capturing_mock(captured)
    m1, m2 = _patched(mock)
    with m1, m2:
        _run(chapter_ops.invoke_chapter(doc, 1))
    # Chapter 1 is the first: there is no prior world state to carry.
    assert captured[0]["previous_world_state"] == ""


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


def test_invoke_chapter_does_not_mutate_doc():
    doc = _doc_with_chapters()
    before = copy.deepcopy(doc)
    mock = _capturing_mock([])
    m1, m2 = _patched(mock)
    with m1, m2:
        _run(chapter_ops.invoke_chapter(doc, 2))
    assert doc == before


# ── J3: chapters are independent of the preplan/play gate ────────────────────


def test_chapters_do_not_affect_preplan_complete():
    from examples.dungeon_master.api import tree

    # A doc with a fully derived chapter set but NO key scene and NO cast: the
    # preplan gate must stay closed — chapters are a separate branch (J3).
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
    assert tree.preplan_complete(doc) is False
    # And a complete preplan stays complete regardless of chapter state.
    doc["key_scene"] = {"reviewed": True}
    doc["characters"] = {
        "roster": ["kara"],
        "cards": {"kara": {"reviewed": True}},
    }
    assert tree.preplan_complete(doc) is True


def test_chapters_appear_as_breadcrumb_peer_of_key_scene():
    from examples.dungeon_master.api import tree

    doc = {
        "synopsis": {"text": SYNOPSIS_TEXT, "reviewed": True},
        "key_scene": {"reviewed": False},
        "chapters": {"order": ["1"], "cards": {"1": {"title": "One"}}},
        "stage": "key_scene",
    }
    labels = [c["label"] for c in tree.breadcrumb(doc)]
    assert "Chapters" in labels
    # Chapters sits after Key Scene and before Characters (independent branch).
    assert labels.index("Key Scene") < labels.index("Chapters")


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
