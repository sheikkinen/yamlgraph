"""Stateless, tree-driven session adapter for DM v2 (FR-474 → FR-475).

The preplan is a tree (FR-475), not a linear chain. The synopsis is the root; it
gates a Characters roster that spawns one ``char:<id>`` card per character, and a
Chapters branch derived once the cast is complete. Every visitable node — synopsis,
each character, each chapter — is the same card with one generation mode:

    weave (generate / iterate) → edit (autosave) → accept

``weave`` runs the current stage's graph with the current draft (possibly empty)
plus a writer's instruction. An empty draft means the instruction is the premise
(first generation); a non-empty draft means it is a change to apply. ``accept``
freezes the current stage and lands on the next sensible node, auto-drafting it.
Navigation between nodes is the breadcrumb (``navigate``), not a linear cursor.

The stage tree, breadcrumb model, and ``char:<id>`` resolution live in ``tree``.
The per-session ``story.json`` is the single source of truth::

    {
      "tagline": "...",
      "stage": "char:elara",                 # static name or char:<id>
      "synopsis":  {"text": "...", "reviewed": true},
      "characters": {
        "reviewed": false,
        "roster": ["elara", "coil"],
        "cards": {"elara": {"name": "Elara", "text": "...", "reviewed": true}, ...}
      }
    }
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from examples.dungeon_master.api import (
    chapter_ops,
    doc_ops,
    navigation,
    story_doc,
    turn_state,
)
from examples.dungeon_master.api.graph_app import (
    reset_caches as _reset_caches,
)
from examples.dungeon_master.api.tree import (
    CHAPTER_PREFIX,
    CHAR_PREFIX,
    FIRST_STAGE,
    TURN_PREFIX,
    Stage,
    breadcrumb,
    cast_complete,
    parse_turn,
    resolve_stage,
)
from examples.dungeon_master.api.world_state import format_world_state

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path("examples/dungeon_master/prompts")

# Base directory for per-session story files. Tests monkeypatch this.
STORY_ROOT = Path("outputs/dungeon-master")

# A sensible default so the first card lands seeded, not empty (FR-474 J1).
DEFAULT_TAGLINE = (
    "Themes of Romance, Adventure, Erotica."
    "10,000 BC, the great thaw — The Floodmark Saga. The glaciers are bleeding "
    "into the lowlands and three loosed rivers are drowning the valley; every "
    "clan must climb or die. Hilde, war-leader of the Aschenwulf band, raids the "
    "rival Bärenschädel clan at dawn just as the river breaks its banks, and is "
    "stranded on a shrinking ledge beside Gunnar, the man she came to kill — the "
    "survival truce between them hardening, against both clans' will, into "
    "something closer and far more dangerous, while in the same surge her "
    "brother Arnulf is swept downriver and mourned as drowned. A mature, "
    "explicit story of what people will break to stay alive — old laws, old "
    "loyalties, the line between enemy and lover — as a salt-road stranger named "
    "Reinmar steers the survivors toward the one high valley still standing by "
    "autumn, and the keeper of the old rites reads the truce itself as the "
    "judgment that called the flood. Romance, blood-feud, faith, and a returning "
    "ghost all converge on the same too-small patch of dry ground."
)

# Shown when a generation comes back empty with no recorded error — the shape a
# provider content-policy block usually takes (an empty completion, not a raise).
# Surfacing it keeps the DM from mistaking a decline for a blank-card bug, and the
# blank is never persisted over the existing draft (Commandment 6: no silent
# fallback).
DECLINED_MESSAGE = (
    "The model returned nothing — the request was most likely declined. "
    "Try rephrasing the scene or softening the explicit details, then Iterate again."
)

# Re-exported so tests can reset the shared graph cache via this module.
__all__ = ["DMSession", "StageView", "_reset_caches"]


def _story_dir(session_id: str) -> Path:
    return STORY_ROOT / session_id


@dataclass
class StageView:
    """View model for the current stage's card."""

    stage: str
    label: str
    text: str = ""
    reviewed: bool = False
    tagline: str = DEFAULT_TAGLINE
    # The breadcrumb control model (Story / Synopsis / branch + member peers).
    crumbs: list[dict] = field(default_factory=list)
    error: str | None = None
    # "" for an ordinary card, "turn" for a play turn (selects the two-column view).
    kind: str = ""
    # Read-only per-character performance for a turn: each card is
    # ``{name, thinking, intent, dialogue, expression}`` (FR-486).
    intents: list[dict] = field(default_factory=list)
    # The director's full structured judgement for a turn (FR-479/FR-481): one
    # dict (``phase, establishing, beats_satisfied, scene_complete, steer,
    # continuity``) so the always-visible Director card owns its presentation and
    # a new director field needs no dataclass change.
    direction: dict = field(default_factory=dict)
    # Book-chapter presentation (FR-490). On a ``chapter:<n>`` card, ``summary``
    # (what this chapter is) and ``world_state`` (what it inherited — the FR-488
    # J7 forward-carry) are shown above the prose. On the ``chapters`` overview,
    # ``chapters`` is the ordered ``[{id, title, summary, reviewed}]`` table of
    # contents. Empty for every other stage (additive).
    summary: str = ""
    world_state: str = ""
    chapters: list[dict] = field(default_factory=list)


class DMSession:
    """Stateless, tree-driven adapter — all state in the story document."""

    def __init__(self, session_id: str):
        self._session_id = session_id

    # ── document helpers ────────────────────────────────────────────────────

    def _load(self, story_dir: Path) -> dict:
        """Read the story doc, or a seeded empty doc before the first write."""
        try:
            return story_doc.read(story_dir)
        except FileNotFoundError:
            return {"tagline": DEFAULT_TAGLINE, "stage": FIRST_STAGE.name}

    def _stage(self, doc: dict) -> Stage:
        return resolve_stage(doc, doc.get("stage", FIRST_STAGE.name))

    def _view(self, doc: dict, *, error: str | None = None) -> StageView:
        stage = self._stage(doc)
        entry = doc_ops.entry(doc, stage.name)
        intents: list[dict] = []
        direction: dict = {}
        summary = ""
        world_state = ""
        chapters: list[dict] = []
        text = entry.get("text", "")
        if stage.kind == "turn":
            cid, n = parse_turn(stage.name)
            intents = turn_state.turn_intents(doc, doc_ops.characters(doc), cid, n)
            direction = turn_state.turn_direction(doc, cid, n)
        elif stage.kind == "chapter":
            # Surface the card's planning context above its prose (FR-490). The
            # forward-carry ledger is structured (FR-499A) — render it to text.
            summary = entry.get("summary", "")
            world_state = format_world_state(entry.get("world_state", {}))
        elif stage.kind == "chapters":
            # Project the ordered chapter set as a read-only table of contents.
            ch = doc_ops.chapters(doc)
            cards = ch["cards"]
            chapters = [
                {
                    "id": cid,
                    "title": cards.get(cid, {}).get("title") or f"Chapter {cid}",
                    "summary": cards.get(cid, {}).get("summary", ""),
                    "reviewed": bool(cards.get(cid, {}).get("reviewed")),
                }
                for cid in ch["order"]
            ]
        elif stage.kind == "book":
            # The terminal manuscript (FR-492 Phase 3): a deterministic compose
            # over the played chapters' final texts — no graph, no LLM. Reachable
            # only when every chapter is played, so the compose never raises here.
            text = chapter_ops.compose_book_deterministic(doc)
        return StageView(
            stage=stage.name,
            label=stage.label,
            text=text,
            reviewed=bool(entry.get("reviewed")),
            tagline=doc.get("tagline", DEFAULT_TAGLINE),
            crumbs=breadcrumb(doc),
            error=error,
            kind=stage.kind,
            intents=intents,
            direction=direction,
            summary=summary,
            world_state=world_state,
            chapters=chapters,
        )

    def view(self) -> StageView:
        """The current stage's view (no LLM); used by the landing page."""
        return self._view(self._load(_story_dir(self._session_id)))

    # ── actions (operate on the current stage) ──────────────────────────────

    async def weave(self, text: str, prompt: str) -> StageView:
        """The single generation mode for the current stage.

        - Empty draft + premise instruction → first generation.
        - Non-empty draft + change instruction → iteration.
        - Empty instruction → pure save of ``text`` (no LLM call).
        """
        story_dir = _story_dir(self._session_id)
        try:
            doc = self._load(story_dir)
            stage = self._stage(doc)
            entry = doc_ops.entry(doc, stage.name)
            if not prompt.strip():
                entry["text"] = text
                entry["reviewed"] = False
                story_doc.write(story_dir, doc)
                return self._view(doc)

            # On the first stage, the empty-draft premise IS the tagline.
            if stage is FIRST_STAGE and not text.strip():
                doc["tagline"] = prompt

            if not await doc_ops.compose_stage(doc, entry, stage, instruction=prompt):
                entry["text"] = await doc_ops.invoke_stage(doc, stage, text, prompt)
            if not entry.get("text", "").strip():
                # An empty generation with no recorded error is the silent shape of
                # a content-policy decline. Raise so the DM sees feedback and the
                # blank is never written over the draft (Commandment 6).
                raise RuntimeError(DECLINED_MESSAGE)
            entry["reviewed"] = False
            story_doc.write(story_dir, doc)
            return self._view(doc)
        except Exception as e:
            logger.exception("weave failed for session %s", self._session_id)
            doc = self._load(story_dir)
            doc_ops.entry(doc, self._stage(doc).name)["text"] = text
            return self._view(doc, error=str(e))

    def edit(self, text: str) -> StageView:
        """Persist the edited prose for the current stage (autosave)."""
        story_dir = _story_dir(self._session_id)
        try:
            doc = self._load(story_dir)
            doc_ops.entry(doc, self._stage(doc).name)["text"] = text
            story_doc.write(story_dir, doc)
            return self._view(doc)
        except Exception as e:
            logger.exception("edit failed for session %s", self._session_id)
            return self._view(self._load(story_dir), error=str(e))

    async def accept(self, text: str = "") -> StageView:
        """Freeze the current stage and land on the next sensible node (FR-475).

        Acceptance is persisted first. Then the landing target is chosen by the
        tree, not a linear cursor: accepting the synopsis derives the character
        roster (A4) and lands on the first character; accepting a character lands
        on the next unreviewed character, and accepting the last character derives
        the chapter outline and lands on the Chapters overview. The landing node
        auto-drafts on entry (FR-474).
        """
        story_dir = _story_dir(self._session_id)
        try:
            doc = self._load(story_dir)
            stage = self._stage(doc)
            entry = doc_ops.entry(doc, stage.name)
            if text.strip():
                entry["text"] = text
            entry["reviewed"] = True
            story_doc.write(story_dir, doc)  # persist acceptance before drafting

            # The synopsis-accept derives the cast before we ask where to land
            # (FR-489 J1): navigation is pure, so this side-effect lives here.
            # The chapter outline derives only once the cast is complete (FR-491
            # J1) — accepting the last character — so the outline can reference the
            # reviewed cast it will be played by.
            if stage.name == "synopsis":
                await doc_ops.expand_roster(doc, story_dir)
            elif stage.name.startswith(CHAR_PREFIX) and cast_complete(doc):
                await doc_ops.expand_chapters(doc, story_dir)
            elif stage.kind == "turn":
                # Accepting a turn whose director reported the chapter's scene
                # complete — or whose chapter exhausted its per-chapter turn budget
                # (FR-501) — closes the chapter (FR-491 B): derive its
                # end-of-chapter world_state from the inherited ledger + the played
                # recaps, so the NEXT chapter is played from where this one left off
                # (J7). The budget backstop stops a director that never resolves
                # from running the chapter away with the whole book turn_cap.
                cid, n = parse_turn(stage.name)
                if turn_state.chapter_should_close(doc, cid, n):
                    await doc_ops.apply_chapter_close(doc, story_dir, cid)
            target = navigation.accept_target(doc, stage)
            if target is not None:
                doc["stage"] = target
                doc_ops.entry(doc, target)  # ensure the target sub-document exists
                story_doc.write(story_dir, doc)
                await doc_ops.autodraft(doc, story_dir, target)
            return self._view(doc)
        except Exception as e:
            logger.exception("accept failed for session %s", self._session_id)
            return self._view(self._load(story_dir), error=str(e))

    async def navigate(self, target: str) -> StageView:
        """Set the current stage to ``target`` if reachable, else reject (FR-475).

        Guards: the synopsis is always reachable; a static child needs its parent
        reviewed; a character card needs the synopsis reviewed and the id present
        in the roster. The Characters group itself is non-visitable. The landing
        node auto-drafts on entry.
        """
        story_dir = _story_dir(self._session_id)
        try:
            doc = self._load(story_dir)
            if not navigation.can_visit(doc, target):
                return self._view(doc, error="That part of the story isn't ready yet.")
            if target.startswith(CHAPTER_PREFIX):
                # A chapter is PLAYED (FR-491): visiting it opens its first turn so
                # the play loop begins; its turns are reachable from the breadcrumb.
                cid = target[len(CHAPTER_PREFIX) :]
                target = f"{TURN_PREFIX}{cid}:1"
            doc["stage"] = target
            doc_ops.entry(doc, target)
            story_doc.write(story_dir, doc)
            await doc_ops.autodraft(doc, story_dir, target)
            return self._view(doc)
        except Exception as e:
            logger.exception("navigate failed for session %s", self._session_id)
            return self._view(self._load(story_dir), error=str(e))
