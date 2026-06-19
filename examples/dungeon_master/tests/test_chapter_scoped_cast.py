"""FR-537: chapter-scoped cast — narrow the animated roster to a chapter's focal cast.

A chapter declares a focal ``cast`` (authored in the outline) and names roster
characters in its ``beats``. The union of those two is the chapter's resolved
cast: the only characters that should be animated while the chapter plays. This
SCOPE narrowing is distinct from the lifecycle STATUS gates (a present, alive,
reviewed character can still be off-stage for a chapter). It must apply at BOTH
roster-narrowing sites — the prose-control cast (``build_allowed_scene_cast``)
AND the per-turn intents roster built inline in ``invoke_turn`` (the measured
defect: that path never called the cast resolver, so off-chapter characters were
animated every turn). An empty resolved cast falls back to the full reviewed
roster, so a cast-less story reproduces today's behavior (additive feature).
"""

from __future__ import annotations

import asyncio
from unittest.mock import patch

from examples.dungeon_master.api import doc_ops, outline_ops, turn_ops
from examples.dungeon_master.api.chapter_open import (
    build_allowed_scene_cast,
    resolve_chapter_cast,
    scope_roster_to_chapter_cast,
)
from examples.dungeon_master.api.lifecycle_resolver import _norm_name


def _run(coro):
    return asyncio.run(coro)


def _three_char_chars() -> dict:
    return {
        "roster": ["hilde", "gunnar", "arnulf"],
        "cards": {
            "hilde": {"name": "Hilde", "text": "h", "reviewed": True},
            "gunnar": {"name": "Gunnar", "text": "g", "reviewed": True},
            "arnulf": {"name": "Arnulf", "text": "a", "reviewed": True},
        },
    }


def _doc_with_chapter(card: dict) -> dict:
    return {
        "characters": _three_char_chars(),
        "chapters": {"order": ["1", "2"], "cards": {"1": {}, "2": card}},
    }


# ── resolve_chapter_cast: the single source of "who is in this chapter" ────────


def test_resolve_chapter_cast_unions_authored_cast_and_beat_named_roster():
    # Authored cast names Gunnar; the beats name Hilde. The resolved cast is the
    # union (normalized), and Arnulf — neither authored nor beat-named — is out.
    doc = _doc_with_chapter(
        {
            "cast": ["Gunnar"],
            "beats": ["Hilde musters the band", "the floodwaters rise"],
        }
    )
    assert resolve_chapter_cast(doc, "2") == {_norm_name("Gunnar"), _norm_name("Hilde")}


def test_resolve_chapter_cast_empty_when_no_cast_and_no_beat_names():
    # No authored cast and no roster name appears in the beats → empty (the callers
    # then fall back to the full reviewed roster).
    doc = _doc_with_chapter({"cast": [], "beats": ["the floodwaters rise"]})
    assert resolve_chapter_cast(doc, "2") == set()


def test_resolve_chapter_cast_drops_authored_names_absent_from_roster():
    # An authored cast name that matches no roster character is dropped (the
    # resolver restricts to the roster; the boundary already warns on unknowns).
    doc = _doc_with_chapter({"cast": ["Gunnar", "Nobody"], "beats": ["a beat"]})
    assert resolve_chapter_cast(doc, "2") == {_norm_name("Gunnar")}


def test_resolve_chapter_cast_beat_name_match_is_word_bounded():
    # Beat-name matching is token/word-bounded, not naive substring: a roster name
    # that only appears inside a larger word must NOT be admitted.
    chars = {
        "roster": ["ron"],
        "cards": {"ron": {"name": "Ron", "text": "r", "reviewed": True}},
    }
    doc = {
        "characters": chars,
        "chapters": {
            "order": ["1"],
            "cards": {"1": {"cast": [], "beats": ["they gathered around the fire"]}},
        },
    }
    assert resolve_chapter_cast(doc, "1") == set()


# ── build_allowed_scene_cast: reviewed ∩ chapter_cast − lifecycle ─────────────


def test_build_allowed_scene_cast_scopes_to_chapter_cast():
    doc = _doc_with_chapter({"cast": ["Gunnar"], "beats": ["a beat"]})
    assert build_allowed_scene_cast(doc, "2") == ["Gunnar"]


def test_build_allowed_scene_cast_empty_cast_falls_back_to_full_reviewed_roster():
    # A cast-less chapter reproduces the pre-FR-537 behavior: the full reviewed
    # roster in roster order.
    doc = _doc_with_chapter({"cast": [], "beats": ["the floodwaters rise"]})
    assert build_allowed_scene_cast(doc, "2") == ["Hilde", "Gunnar", "Arnulf"]


def test_build_allowed_scene_cast_scope_then_lifecycle_exclusion():
    # Chapter cast admits Hilde and Arnulf; the inherited seam packet marks Arnulf
    # confirmed dead → the scope narrows, then the lifecycle gate excludes Arnulf.
    doc = {
        "characters": _three_char_chars(),
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "seam_packet": {
                        "character_lifecycle": [
                            {
                                "name": "Arnulf",
                                "existence_state": "confirmed_dead",
                                "visibility_mode": "absent",
                                "allowed_reappearance_from_chapter": None,
                                "source_chapter": 1,
                            }
                        ]
                    }
                },
                "2": {"cast": ["Hilde", "Arnulf"], "beats": ["a beat"]},
            },
        },
    }
    assert build_allowed_scene_cast(doc, "2") == ["Hilde"]


# ── scope_roster_to_chapter_cast: the id-shape narrowing for the intents path ──


def test_scope_roster_to_chapter_cast_narrows_ids():
    doc = _doc_with_chapter({"cast": ["Gunnar"], "beats": ["a beat"]})
    chars = _three_char_chars()
    assert scope_roster_to_chapter_cast(
        doc, chars, "2", ["hilde", "gunnar", "arnulf"]
    ) == ["gunnar"]


def test_scope_roster_to_chapter_cast_empty_cast_keeps_full_roster():
    doc = _doc_with_chapter({"cast": [], "beats": ["the floodwaters rise"]})
    chars = _three_char_chars()
    assert scope_roster_to_chapter_cast(
        doc, chars, "2", ["hilde", "gunnar", "arnulf"]
    ) == ["hilde", "gunnar", "arnulf"]


# ── invoke_turn: the per-turn intents roster is the measured defect ───────────


class _GraphCapture:
    def __init__(self) -> None:
        self.payload: dict | None = None

    async def ainvoke(self, payload):
        self.payload = payload
        return {"intents": [], "direction": {}, "recap": "ok"}


def _doc_for_turn(card: dict) -> dict:
    return {
        "characters": _three_char_chars(),
        "chapters": {
            "order": ["1", "2", "3"],
            "cards": {"1": {}, "2": {}, "3": card},
        },
    }


def test_invoke_turn_intents_roster_scoped_to_chapter_cast(monkeypatch):
    # The defect: the intents roster is built inline in invoke_turn and never went
    # through the cast resolver, so Gunnar/Arnulf were animated in a Hilde-only
    # chapter. Assert the ACTUAL animated cast (the graph payload), not just the
    # prose-control helper.
    doc = _doc_for_turn({"cast": ["Hilde"], "beats": ["Hilde acts"], "turns": []})
    chars = _three_char_chars()
    capture = _GraphCapture()
    monkeypatch.setattr(turn_ops, "get_app", lambda name: capture)

    text = _run(turn_ops.invoke_turn(doc, chars, "3", 1))

    assert text == "ok"
    assert capture.payload is not None
    cast_names = [c.get("name") for c in (capture.payload.get("cast") or [])]
    assert cast_names == ["Hilde"]


def test_invoke_turn_full_roster_when_chapter_declares_no_cast(monkeypatch):
    doc = _doc_for_turn({"cast": [], "beats": ["the band marches"], "turns": []})
    chars = _three_char_chars()
    capture = _GraphCapture()
    monkeypatch.setattr(turn_ops, "get_app", lambda name: capture)

    _run(turn_ops.invoke_turn(doc, chars, "3", 1))

    cast_names = [c.get("name") for c in (capture.payload.get("cast") or [])]
    assert cast_names == ["Hilde", "Gunnar", "Arnulf"]


# ── boundary: expand_chapters stores roster-normalized cast ───────────────────


_OUTLINE_WITH_CAST = {
    "chapters": [
        {
            "title": "Chapter 1",
            "summary": "Kara musters the band.",
            "beats": ["Kara musters the band", "the floodwaters rise"],
            "cast": ["gunnar", "Nobody"],
        },
        {
            "title": "Chapter 2",
            "summary": "Kara corners the raider.",
            "beats": ["Kara reaches the ledge", "Kara corners the raider"],
            "cast": ["Hilde"],
        },
    ]
}


def _patched(mock):
    return patch.multiple(
        "yamlgraph.node_factory.llm_nodes",
        execute_prompt=mock,
    ), patch.multiple(
        "yamlgraph.executor",
        execute_prompt=mock,
    )


def test_expand_chapters_stores_roster_normalized_cast(tmp_path, monkeypatch):
    from examples.dungeon_master.api import session as session_mod

    monkeypatch.setattr(session_mod, "STORY_ROOT", tmp_path)
    session_mod._reset_caches()

    def _mock(prompt_name, variables=None, **kwargs):
        if prompt_name == "chapter_outline":
            return _OUTLINE_WITH_CAST
        raise AssertionError(f"unexpected prompt {prompt_name!r}")

    m1, m2 = _patched(_mock)
    doc = {
        "synopsis": {"text": "a synopsis", "reviewed": True},
        "characters": {
            "roster": ["gunnar", "hilde"],
            "cards": {
                "gunnar": {"name": "Gunnar", "text": "g", "reviewed": True},
                "hilde": {"name": "Hilde", "text": "h", "reviewed": True},
            },
        },
    }
    story_dir = tmp_path / "ch-cast"
    story_dir.mkdir(parents=True, exist_ok=True)
    with m1, m2:
        _run(doc_ops.expand_chapters(doc, story_dir))

    # Unknown authored names are dropped; matched names are stored as the roster's
    # canonical display name (case-insensitive match).
    assert doc["chapters"]["cards"]["1"]["cast"] == ["Gunnar"]
    assert doc["chapters"]["cards"]["2"]["cast"] == ["Hilde"]


def test_outline_chapters_parses_cast_field():
    def _mock(prompt_name, variables=None, **kwargs):
        if prompt_name == "chapter_outline":
            return _OUTLINE_WITH_CAST
        raise AssertionError(f"unexpected prompt {prompt_name!r}")

    m1, m2 = _patched(_mock)
    doc = {"synopsis": {"text": "a synopsis", "reviewed": True}}
    with m1, m2:
        chapters = _run(outline_ops.outline_chapters(doc))

    assert chapters[0]["cast"] == ["gunnar", "Nobody"]
    assert chapters[1]["cast"] == ["Hilde"]
