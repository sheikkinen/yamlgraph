"""Stateless, tree-driven session adapter for DM v2 (FR-474 → FR-475).

The preplan is a tree (FR-475), not a linear chain. The synopsis is the root; it
gates a Key Scene leaf and a Characters roster that spawns one ``char:<id>`` card
per character. Every visitable node — synopsis, key scene, each character — is the
same card with one generation mode:

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
      "key_scene": {"text": "...", "reviewed": false},
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

from examples.dungeon_master.api import chapter_ops, navigation, story_doc, turn_ops
from examples.dungeon_master.api.graph_app import (
    clean_text,
    get_app,
)
from examples.dungeon_master.api.graph_app import (
    reset_caches as _reset_caches,
)
from examples.dungeon_master.api.tree import (
    CHAPTER_PREFIX,
    CHAR_PREFIX,
    FINAL_CUT,
    FINAL_CUT_TURNS,
    FIRST_STAGE,
    STAGE_BY_NAME,
    TURN_PREFIX,
    WALKTHROUGH,
    Stage,
    breadcrumb,
    resolve_stage,
    split_roster,
    unique_slug,
)

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

    def _characters(self, doc: dict) -> dict:
        """The characters sub-document ``{reviewed, roster, cards}`` (created if absent)."""
        chars = doc.setdefault(
            "characters", {"reviewed": False, "roster": [], "cards": {}}
        )
        chars.setdefault("roster", [])
        chars.setdefault("cards", {})
        return chars

    def _chapters(self, doc: dict) -> dict:
        """The chapters sub-document ``{reviewed, order, cards}`` (created if absent).

        A fixed ordered set of book chapters (FR-488): ``order`` is the 1-based
        string ids in story sequence, ``cards`` maps each id to
        ``{title, summary, text, world_state, reviewed}``. Independent of the
        characters roster and of the preplan/play gate (J3).
        """
        chapters = doc.setdefault(
            "chapters", {"reviewed": False, "order": [], "cards": {}}
        )
        chapters.setdefault("order", [])
        chapters.setdefault("cards", {})
        return chapters

    def _entry(self, doc: dict, name: str) -> dict:
        """The per-stage sub-document ``{"text", "reviewed"}`` (created if absent).

        Static stages live at the top level; ``char:<id>`` stages are nested under
        ``characters.cards`` (A2); ``turn:<n>`` stages reuse the turn's ``recap``
        entry so weave/edit/accept operate on it unchanged (FR-477 J3).
        """
        if name.startswith(CHAR_PREFIX):
            cid = name[len(CHAR_PREFIX) :]
            cards = self._characters(doc)["cards"]
            return cards.setdefault(cid, {"name": cid, "text": "", "reviewed": False})
        if name.startswith(CHAPTER_PREFIX):
            cid = name[len(CHAPTER_PREFIX) :]
            cards = self._chapters(doc)["cards"]
            return cards.setdefault(
                cid,
                {
                    "title": f"Chapter {cid}",
                    "summary": "",
                    "text": "",
                    "world_state": "",
                    "reviewed": False,
                },
            )
        if name.startswith(TURN_PREFIX):
            return turn_ops.turn_record(doc, int(name[len(TURN_PREFIX) :]))["recap"]
        return doc.setdefault(name, {"text": "", "reviewed": False})

    def _view(self, doc: dict, *, error: str | None = None) -> StageView:
        stage = self._stage(doc)
        entry = self._entry(doc, stage.name)
        intents: list[dict] = []
        direction: dict = {}
        if stage.kind == "turn":
            n = int(stage.name[len(TURN_PREFIX) :])
            intents = turn_ops.turn_intents(doc, self._characters(doc), n)
            direction = turn_ops.turn_direction(doc, n)
        return StageView(
            stage=stage.name,
            label=stage.label,
            text=entry.get("text", ""),
            reviewed=bool(entry.get("reviewed")),
            tagline=doc.get("tagline", DEFAULT_TAGLINE),
            crumbs=breadcrumb(doc),
            error=error,
            kind=stage.kind,
            intents=intents,
            direction=direction,
        )

    def view(self) -> StageView:
        """The current stage's view (no LLM); used by the landing page."""
        return self._view(self._load(_story_dir(self._session_id)))

    # ── graph invocation ────────────────────────────────────────────────────

    async def _invoke_stage(
        self, doc: dict, stage: Stage, draft: str, instruction: str
    ) -> str:
        """Run a stage's graph and return its cleaned output text.

        Builds the graph variables from the draft, the writer's instruction, each
        upstream context stage's accepted text, and — for character cards — the
        character's ``name`` (A3). Shared by ``weave``, roster expansion, and
        auto-draft on entry.
        """
        variables = {"draft": draft, "instruction": instruction}
        for ctx in stage.context:
            variables[ctx] = doc.get(ctx, {}).get("text", "")
        if stage.var_name:
            variables["name"] = stage.var_name
        if stage.include_roster:
            # Bind generation to the cast: the rostered display names are the
            # authoritative character names (FR-480), so the scene cannot mint a
            # name the roster never sanctioned.
            chars = doc.get("characters", {})
            cards = chars.get("cards", {})
            names = [
                cards.get(cid, {}).get("name") or cid for cid in chars.get("roster", [])
            ]
            variables["roster"] = "\n".join(names)
        result = await get_app(stage.graph).ainvoke(variables)
        errors = result.get("errors") or []
        if errors:
            # The graph swallowed a node failure into its errors list (e.g. a
            # provider content-policy block on an explicit scene). Surface the real
            # reason instead of returning the empty output it left behind
            # (Commandment 6: expose the fault, never hide it behind a blank card).
            last = errors[-1]
            reason = getattr(last, "message", None) or str(last)
            raise RuntimeError(reason)
        return clean_text(result.get(stage.output_key or stage.name))

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
            entry = self._entry(doc, stage.name)
            if not prompt.strip():
                entry["text"] = text
                entry["reviewed"] = False
                story_doc.write(story_dir, doc)
                return self._view(doc)

            # On the first stage, the empty-draft premise IS the tagline.
            if stage is FIRST_STAGE and not text.strip():
                doc["tagline"] = prompt

            if not await self._compose_special(
                doc, entry, stage, instruction=prompt, draft=text
            ):
                entry["text"] = await self._invoke_stage(doc, stage, text, prompt)
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
            self._entry(doc, self._stage(doc).name)["text"] = text
            return self._view(doc, error=str(e))

    def edit(self, text: str) -> StageView:
        """Persist the edited prose for the current stage (autosave)."""
        story_dir = _story_dir(self._session_id)
        try:
            doc = self._load(story_dir)
            self._entry(doc, self._stage(doc).name)["text"] = text
            story_doc.write(story_dir, doc)
            return self._view(doc)
        except Exception as e:
            logger.exception("edit failed for session %s", self._session_id)
            return self._view(self._load(story_dir), error=str(e))

    async def accept(self, text: str = "") -> StageView:
        """Freeze the current stage and land on the next sensible node (FR-475).

        Acceptance is persisted first. Then the landing target is chosen by the
        tree, not a linear cursor: accepting the synopsis derives the character
        roster (A4) and lands on the Key Scene; accepting the Key Scene or a
        character lands on the next unreviewed character, or stays read-only when
        the cast is complete. The landing node auto-drafts on entry (FR-474).
        """
        story_dir = _story_dir(self._session_id)
        try:
            doc = self._load(story_dir)
            stage = self._stage(doc)
            entry = self._entry(doc, stage.name)
            if text.strip():
                entry["text"] = text
            entry["reviewed"] = True
            story_doc.write(story_dir, doc)  # persist acceptance before drafting

            # The synopsis-accept derives the cast before we ask where to land
            # (FR-489 J1): navigation is pure, so this side-effect lives here.
            if stage.name == "synopsis":
                await self._expand_roster(doc, story_dir)
                await self._expand_chapters(doc, story_dir)
            target = navigation.accept_target(doc, stage)
            if target is not None:
                doc["stage"] = target
                self._entry(doc, target)  # ensure the target sub-document exists
                story_doc.write(story_dir, doc)
                await self._autodraft(doc, story_dir, target)
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
            doc["stage"] = target
            self._entry(doc, target)
            story_doc.write(story_dir, doc)
            await self._autodraft(doc, story_dir, target)
            return self._view(doc)
        except Exception as e:
            logger.exception("navigate failed for session %s", self._session_id)
            return self._view(self._load(story_dir), error=str(e))

    # ── roster expansion (side-effecting; navigation stays pure) ─────────────

    async def _expand_roster(self, doc: dict, story_dir: Path) -> None:
        """Derive the cast from the synopsis and spawn one card per new name (A4)."""
        chars = self._characters(doc)
        roster_stage = STAGE_BY_NAME["characters"]
        raw = await self._invoke_stage(doc, roster_stage, "", roster_stage.seed)
        seen = set(chars["cards"].keys())
        for name in split_roster(raw):
            cid = unique_slug(name, seen)
            seen.add(cid)
            if cid not in chars["cards"]:
                chars["cards"][cid] = {"name": name, "text": "", "reviewed": False}
                chars["roster"].append(cid)
        story_doc.write(story_dir, doc)

    async def _expand_chapters(self, doc: dict, story_dir: Path) -> None:
        """Split the synopsis into a fixed chapter set, one card per chapter (FR-488).

        Idempotent (J6): the chapter set is FIXED at derivation — numeric ids
        cannot idempotently append like character slugs — so once ``order`` is
        populated this is a no-op. Otherwise it outlines the synopsis into
        ``{title, summary}`` chunks and spawns ``cards["1"]…["N"]`` with empty
        ``text``/``world_state`` for later per-chapter expansion.
        """
        chapters = self._chapters(doc)
        if chapters["order"]:
            return  # already derived; the set is fixed
        outline = await chapter_ops.outline_chapters(doc)
        for i, chunk in enumerate(outline, start=1):
            cid = str(i)
            chapters["cards"][cid] = {
                "title": chunk.get("title") or f"Chapter {cid}",
                "summary": chunk.get("summary", ""),
                "text": "",
                "world_state": "",
                "reviewed": False,
            }
            chapters["order"].append(cid)
        story_doc.write(story_dir, doc)

    async def _compose_special(
        self, doc: dict, entry: dict, stage: Stage, *, instruction: str, draft: str
    ) -> bool:
        """Draft a composed multi-layer stage (a turn or one of the three finishes).

        These stages are not a single ``_invoke_stage`` call: a turn re-rolls its
        intents + recap together (FR-477 J2); the two Final Cuts and the
        Walkthrough compose from the whole played arc and carry a structured track
        (``turns`` / ``setting``) beside the rendered ``text``. ``weave`` and
        ``_autodraft`` share this exact dispatch — the only difference is whether a
        writer's ``instruction``/``draft`` steers the composition (weave) or it is
        a fresh draft (auto-draft, empty args). Mutates ``entry`` in place; returns
        whether the stage was one of these composed stages, so the caller can fall
        back to ``_invoke_stage`` for an ordinary card when it was not.
        """
        if stage.kind == "turn":
            n = int(stage.name[len(TURN_PREFIX) :])
            entry["text"] = await turn_ops.invoke_turn(
                doc, self._characters(doc), n, instruction=instruction
            )
        elif stage.kind == "chapter":
            # A book chapter (FR-488): composed because it needs the previous
            # chapter's world_state threaded in (J7), which a bare _invoke_stage
            # cannot supply. invoke_chapter is pure; the world_state ledger is
            # recorded beside the rendered text for the next chapter to carry.
            n = int(stage.name[len(CHAPTER_PREFIX) :])
            chapter = await chapter_ops.invoke_chapter(
                doc, n, instruction=instruction, draft=draft
            )
            entry["text"] = chapter["text"]
            entry["world_state"] = chapter["world_state"]
        elif stage.name == FINAL_CUT:
            entry["text"] = await turn_ops.invoke_final_cut(
                doc, instruction=instruction, draft=draft
            )
        elif stage.name == FINAL_CUT_TURNS:
            segments = await turn_ops.invoke_final_cut_turns(
                doc, instruction=instruction, draft=draft
            )
            entry["turns"] = segments
            entry["text"] = turn_ops.render_cut_turns(segments)
        elif stage.name == WALKTHROUGH:
            wt = await turn_ops.invoke_walkthrough(
                doc, self._characters(doc), instruction=instruction, draft=draft
            )
            entry["setting"] = wt["setting"]
            entry["turns"] = wt["turns"]
            entry["text"] = turn_ops.render_walkthrough(wt["setting"], wt["turns"])
        else:
            return False
        return True

    async def _autodraft(self, doc: dict, story_dir: Path, target: str) -> None:
        """Auto-draft ``target`` on entry: land on a populated card, not a blank one."""
        stage = resolve_stage(doc, target)
        entry = self._entry(doc, target)
        if stage.seed and not entry.get("text", "").strip():
            if not await self._compose_special(
                doc, entry, stage, instruction="", draft=""
            ):
                entry["text"] = await self._invoke_stage(doc, stage, "", stage.seed)
            entry["reviewed"] = False
            story_doc.write(story_dir, doc)
