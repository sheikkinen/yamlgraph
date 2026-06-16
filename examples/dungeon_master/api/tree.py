"""Stage tree + breadcrumb model for DM v2 (FR-475).

The preplan is a tree, not a linear chain:

    Synopsis (root, gates children)
    ├── Characters         (roster — non-visitable; spawns one card per name)
    │   ├── char:elara     (dynamic leaf)
    │   └── char:coil      (dynamic leaf)
    └── Chapters           (derived once the cast is complete)

Static stages live in ``STAGES``. Per-character cards are *not* in ``STAGES``:
they are addressed by id (``char:<slug>``) and resolved at runtime from the
roster the synopsis-accept derives. ``resolve_stage`` returns a synthetic
``Stage`` for those (A1), carrying the character's display name so the shared
``character.yaml`` graph can be parameterised by it (A3).

All functions here are pure operations on the story ``doc`` — no I/O, no LLM.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

GRAPH_DIR = "examples/dungeon_master"
CHARACTER_GRAPH = f"{GRAPH_DIR}/character.yaml"
CHARACTER_SEED = "Draft this one character from the synopsis."
CHAR_PREFIX = "char:"

# Book-scope chapters (FR-488 / FR-491): an INDEPENDENT branch off the synopsis
# (a peer of Characters, NOT part of the cast gate — J3). The synopsis is the
# whole book in outline; ``chapter_outline.yaml`` splits it into a fixed ordered
# set of one-paragraph chapter summaries, and each ``chapter:<n>`` is PLAYED turn
# by turn (FR-491). When a chapter's scene completes, ``chapter_close.yaml``
# derives its end-of-chapter world_state from the inherited ledger + the played
# recaps, carrying it forward (J7). Numeric 1-based string ids — the set is FIXED
# at derivation (no idempotent slug-append; J6).
CHAPTER_OUTLINE_GRAPH = f"{GRAPH_DIR}/chapter_outline.yaml"
CHAPTER_CLOSE_GRAPH = f"{GRAPH_DIR}/chapter_close.yaml"
CHAPTER_PREFIX = "chapter:"

# Play loop (FR-477 / FR-491 C): turns are dynamic stages scoped to a chapter and
# addressed by ``turn:<cid>:<n>``, run by the shared turn graph, stored under
# ``chapters.cards[<cid>].turns``, and resolved at runtime like character cards.
TURN_GRAPH = f"{GRAPH_DIR}/turn.yaml"
TURN_PREFIX = "turn:"
TURN_SEED = "Play this turn."

# Final Cut (FR-484): a terminal leaf that composes one continuous scene from the
# whole played arc once the director reports the scene complete. A single static
# stage (not a per-item prefix), gated on ``scene_is_complete`` rather than a
# parent being reviewed.
FINAL_CUT = "final_cut"
FINAL_CUT_GRAPH = f"{GRAPH_DIR}/final_cut.yaml"
FINAL_CUT_SEED = "Compose the final cut of the whole played scene."

# Turn-structured Final Cut (FR-485): a sibling terminal leaf that, instead of
# dissolving the turns into one flowing scene (FR-484), keeps the turn skeleton —
# one polished segment per played turn, aligned 1:1 to the play-by-play, with the
# whole-arc knowledge spent on de-repetition and climax emphasis. A separate
# ``doc["final_cut_turns"]`` artifact, gated identically on ``scene_is_complete``.
FINAL_CUT_TURNS = "final_cut_turns"
FINAL_CUT_TURNS_GRAPH = f"{GRAPH_DIR}/final_cut_turns.yaml"
FINAL_CUT_TURNS_SEED = (
    "Compose the turn-structured final cut of the whole played scene."
)

# Full-text walkthrough (FR-487): the rendered finish. Where the two Final Cuts
# are *summaries* (tight prose over the recaps), the walkthrough renders the full
# text of each played turn from three already-authored layers — the FR-485 cut
# spine, the FR-486 per-character performance, and a new whole-arc director-
# staging pass — validated 1:1 by the reused ``validate_cut_turns``. A separate
# ``doc["walkthrough"]`` artifact, gated on the scene being complete AND the
# FR-485 cut being present (its spine).
WALKTHROUGH = "walkthrough"
WALKTHROUGH_GRAPH = f"{GRAPH_DIR}/walkthrough.yaml"
STAGING_GRAPH = f"{GRAPH_DIR}/staging.yaml"
WALKTHROUGH_SEED = "Render the full-text walkthrough of the whole played scene."


@dataclass(frozen=True)
class Stage:
    """One story stage: its graph, label, and the prior stages it reads as context."""

    name: str
    label: str
    graph: str
    # Names of earlier stages whose accepted text is passed in as graph variables.
    context: tuple[str, ...] = ()
    # Default instruction used to auto-draft this stage the moment it is entered,
    # so the DM never lands on a blank card. Empty seed => wait for a manual prompt.
    seed: str = ""
    # The parent stage that must be reviewed before this one unlocks (None = root).
    parent: str | None = None
    # "" for an ordinary stage, "roster" for the non-visitable Characters group.
    kind: str = ""
    # Character display name injected as the ``name`` graph variable (char stages).
    var_name: str = ""
    # The graph's output state_key, when it differs from ``name`` (e.g. roster, char).
    output_key: str = ""


# The static stage tree. Adding a static stage extends the app; per-character
# cards are built at runtime (see ``resolve_stage``).
STAGES: tuple[Stage, ...] = (
    Stage("synopsis", "Synopsis", f"{GRAPH_DIR}/synopsis.yaml"),
    Stage(
        "characters",
        "Characters",
        f"{GRAPH_DIR}/character_roster.yaml",
        context=("synopsis",),
        parent="synopsis",
        kind="roster",
        seed="Name the characters the synopsis requires (names only).",
        output_key="roster",
    ),
    Stage(
        # The Chapters overview (FR-490): a visitable, read-only table of contents
        # the group crumb lands on. NOT a roster (which is non-visitable) and NOT
        # auto-drafted (no seed) — the chapter set is derived by _expand_chapters
        # via chapter_ops directly, never through this stage. ``kind="chapters"``
        # routes app_body.html to the overview template, not the weave card.
        "chapters",
        "Chapters",
        CHAPTER_OUTLINE_GRAPH,
        context=("synopsis",),
        parent="synopsis",
        kind="chapters",
        output_key="outline",
    ),
    Stage(
        FINAL_CUT,
        "Final Cut",
        FINAL_CUT_GRAPH,
        seed=FINAL_CUT_SEED,
        output_key="final_cut",
    ),
    Stage(
        FINAL_CUT_TURNS,
        "Final Cut (Turns)",
        FINAL_CUT_TURNS_GRAPH,
        seed=FINAL_CUT_TURNS_SEED,
        output_key="cut",
    ),
    Stage(
        WALKTHROUGH,
        "Walkthrough",
        WALKTHROUGH_GRAPH,
        seed=WALKTHROUGH_SEED,
        output_key="walkthrough",
    ),
)
STAGE_BY_NAME = {s.name: s for s in STAGES}
FIRST_STAGE = STAGES[0]


def _slug(name: str) -> str:
    """Slugify a character name to an id (lowercase, alnum + hyphens)."""
    s = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return s or "character"


def unique_slug(name: str, seen: set[str]) -> str:
    """A slug for ``name`` not already in ``seen`` (suffix -2, -3… on collision)."""
    base = _slug(name)
    cid = base
    n = 2
    while cid in seen:
        cid = f"{base}-{n}"
        n += 1
    return cid


def split_roster(raw: str) -> list[str]:
    """Split a plain-text roster (names on lines or commas) into proper names."""
    names: list[str] = []
    for part in re.split(r"[\n,]+", raw or ""):
        # Strip bullets, numbering, and surrounding punctuation/space.
        name = part.strip().lstrip("-*•").strip()
        name = re.sub(r"^\d+[.)]\s*", "", name).strip()
        if name:
            names.append(name)
    return names


def resolve_stage(doc: dict, name: str) -> Stage:
    """The ``Stage`` for ``name`` — a static one, or a synthetic char/turn stage."""
    if name.startswith(CHAR_PREFIX):
        cid = name[len(CHAR_PREFIX) :]
        card = doc.get("characters", {}).get("cards", {}).get(cid, {})
        label = card.get("name") or cid
        return Stage(
            name=name,
            label=label,
            graph=CHARACTER_GRAPH,
            context=("synopsis",),
            seed=CHARACTER_SEED,
            parent="characters",
            var_name=label,
            output_key="character",
        )
    if name.startswith(CHAPTER_PREFIX):
        # A book chapter (FR-491). No longer a composed prose card — it is the
        # landing for a chapter that is PLAYED turn by turn. Not auto-drafted (no
        # seed); _view shows its summary + inherited world_state + played turns.
        cid = name[len(CHAPTER_PREFIX) :]
        card = doc.get("chapters", {}).get("cards", {}).get(cid, {})
        label = card.get("title") or f"Chapter {cid}"
        return Stage(
            name=name,
            label=label,
            graph=CHAPTER_CLOSE_GRAPH,
            context=("synopsis",),
            parent="chapters",
            kind="chapter",
            output_key="chapter_close",
        )
    if name.startswith(TURN_PREFIX):
        # A play turn (FR-477 / FR-491 C): scoped to a chapter, addressed
        # ``turn:<cid>:<n>``. The synthetic stage exists so _view/_entry/breadcrumb
        # can address it; the turn graph is run through _compose_special.
        cid, n = parse_turn(name)
        chapter = doc.get("chapters", {}).get("cards", {}).get(cid, {})
        chapter_label = chapter.get("title") or f"Chapter {cid}"
        return Stage(
            name=name,
            label=f"{chapter_label} · Turn {n}",
            graph=TURN_GRAPH,
            context=(),
            seed=TURN_SEED,
            parent="play",
            kind="turn",
            output_key="recap",
        )
    return STAGE_BY_NAME.get(name, FIRST_STAGE)


def parse_turn(name: str) -> tuple[str, int]:
    """Split a ``turn:<cid>:<n>`` stage name into its chapter id and 1-based index.

    Falls back to ``("", 0)`` for a malformed name so callers can reject it rather
    than raise mid-render (FR-491 C).
    """
    if not name.startswith(TURN_PREFIX):
        return "", 0
    rest = name[len(TURN_PREFIX) :]
    cid, _, suffix = rest.rpartition(":")
    if not cid or not suffix.isdigit():
        return "", 0
    return cid, int(suffix)


def cast_complete(doc: dict) -> bool:
    """Whether the cast is fully reviewed (synopsis ✓ + every character ✓; FR-491).

    The gate that derives the chapter outline and (FR-477) unlocks play: the cast
    must exist before the chapters can reference it (J1). The key scene is retired,
    so it is no longer part of the gate.
    """
    if not doc.get("synopsis", {}).get("reviewed"):
        return False
    chars = doc.get("characters", {})
    roster = chars.get("roster", [])
    cards = chars.get("cards", {})
    return bool(roster) and all(cards.get(cid, {}).get("reviewed") for cid in roster)


def scene_is_complete(doc: dict) -> bool:
    """Whether any played turn's director reported the scene complete (FR-484).

    The unlock gate for the terminal Final Cut leaf, mirroring ``preplan_complete``
    for the Play branch: once the director declares the scene's END reached on any
    turn (FR-479 J5), the whole arc exists and can be composed into one cut. Pure
    dict access — no turn_ops import, so ``tree`` stays free of cycles.
    """
    return any(
        (t.get("direction") or {}).get("scene_complete") for t in doc.get("turns", [])
    )


def cut_present(doc: dict) -> bool:
    """Whether the FR-485 turn-structured cut spine exists yet (FR-487 OQ1).

    The walkthrough renders that cut as its structural spine, so it stays locked
    until the cut is *present* (its ``turns`` segments exist) — not necessarily
    reviewed. Pure dict access, mirroring :func:`scene_is_complete`.
    """
    return bool((doc.get("final_cut_turns") or {}).get("turns"))


def breadcrumb(doc: dict) -> list[dict]:
    """The breadcrumb control model (FR-475): Story / Synopsis / branch peers.

    Each crumb is ``{label, stage, current, reviewed, group?, member?}``. ``stage``
    is the nav target (``None`` => not clickable). Branch peers (Chapters,
    Characters) appear only once the synopsis is reviewed; inside the Characters
    branch the cast is listed inline as member peers.
    """
    current = doc.get("stage", FIRST_STAGE.name)
    syn = doc.get("synopsis", {})
    crumbs: list[dict] = [
        {"label": "Story", "stage": None, "current": False, "reviewed": False},
        {
            "label": "Synopsis",
            "stage": "synopsis",
            "current": current == "synopsis",
            "reviewed": bool(syn.get("reviewed")),
        },
    ]
    if not syn.get("reviewed"):
        return crumbs

    # Chapters (FR-488 / FR-491): an independent branch off the synopsis, peer of
    # Characters. A fixed ordered set of chapters; each is PLAYED turn by turn, so
    # inside a chapter its turns are listed as deeper member peers. Not part of the
    # cast gate (J3).
    chapters = doc.get("chapters", {})
    ch_order = chapters.get("order", [])
    ch_cards = chapters.get("cards", {})
    in_chapters = current.startswith(CHAPTER_PREFIX)
    playing_cid, _playing_n = parse_turn(current)
    # The group crumb lands on the overview (FR-490), and the member peers are
    # visible both from inside a chapter AND while playing one of its turns, so the
    # chapter set stays discoverable while a chapter is being played.
    on_chapters = in_chapters or current == "chapters" or bool(playing_cid)
    ch_all_reviewed = bool(ch_order) and all(
        ch_cards.get(cid, {}).get("reviewed") for cid in ch_order
    )
    crumbs.append(
        {
            "label": "Chapters",
            "stage": "chapters" if ch_order else None,
            "current": current == "chapters",
            "reviewed": ch_all_reviewed,
            "group": True,
        }
    )
    if on_chapters:
        for cid in ch_order:
            card = ch_cards.get(cid, {})
            crumbs.append(
                {
                    "label": card.get("title") or f"Chapter {cid}",
                    "stage": CHAPTER_PREFIX + cid,
                    "current": current == CHAPTER_PREFIX + cid or cid == playing_cid,
                    "reviewed": bool(card.get("reviewed")),
                    "member": True,
                }
            )
            # The chapter being played lists its turns as deeper member peers
            # (FR-491 C): play is scoped to the chapter, not a flat global loop.
            if cid == playing_cid:
                for t in card.get("turns") or []:
                    n = t.get("n")
                    crumbs.append(
                        {
                            "label": f"Turn {n}",
                            "stage": f"{TURN_PREFIX}{cid}:{n}",
                            "current": current == f"{TURN_PREFIX}{cid}:{n}",
                            "reviewed": bool(t.get("recap", {}).get("reviewed")),
                            "member": True,
                            "deep": True,
                        }
                    )

    chars = doc.get("characters", {})
    cards = chars.get("cards", {})
    roster = chars.get("roster", [])
    in_chars = current.startswith(CHAR_PREFIX)
    all_reviewed = bool(roster) and all(
        cards.get(cid, {}).get("reviewed") for cid in roster
    )
    crumbs.append(
        {
            "label": "Characters",
            "stage": (CHAR_PREFIX + roster[0]) if roster else None,
            "current": False,
            "reviewed": all_reviewed,
            "group": True,
        }
    )
    if in_chars:
        for cid in roster:
            card = cards.get(cid, {})
            crumbs.append(
                {
                    "label": card.get("name") or cid,
                    "stage": CHAR_PREFIX + cid,
                    "current": current == CHAR_PREFIX + cid,
                    "reviewed": bool(card.get("reviewed")),
                    "member": True,
                }
            )

    # Play is no longer a flat global branch (FR-491): each chapter is played in
    # place, its turns listed under the chapter crumb above.
    # Final Cut (FR-484): a terminal peer once the director has reported the scene
    if scene_is_complete(doc):
        fc = doc.get("final_cut", {})
        crumbs.append(
            {
                "label": "Final Cut",
                "stage": FINAL_CUT,
                "current": current == FINAL_CUT,
                "reviewed": bool(fc.get("reviewed")),
            }
        )
        fct = doc.get("final_cut_turns", {})
        crumbs.append(
            {
                "label": "Final Cut (Turns)",
                "stage": FINAL_CUT_TURNS,
                "current": current == FINAL_CUT_TURNS,
                "reviewed": bool(fct.get("reviewed")),
            }
        )
        # Walkthrough (FR-487): the rendered finish, a peer after the two cuts.
        # It renders the FR-485 cut as its spine, so it appears only once that
        # cut is present (its segments exist) — not merely once the scene ends.
        if cut_present(doc):
            wt = doc.get("walkthrough", {})
            crumbs.append(
                {
                    "label": "Walkthrough",
                    "stage": WALKTHROUGH,
                    "current": current == WALKTHROUGH,
                    "reviewed": bool(wt.get("reviewed")),
                }
            )
    return crumbs
