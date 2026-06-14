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

from examples.dungeon_master.api import story_doc, turn_ops
from examples.dungeon_master.api.graph_app import (
    clean_text,
    get_app,
)
from examples.dungeon_master.api.graph_app import (
    reset_caches as _reset_caches,
)
from examples.dungeon_master.api.tree import (
    CHAR_PREFIX,
    FIRST_STAGE,
    STAGE_BY_NAME,
    TURN_PREFIX,
    Stage,
    breadcrumb,
    preplan_complete,
    resolve_stage,
    split_roster,
    unique_slug,
)

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path("examples/dungeon_master/prompts")

# Base directory for per-session story files. Tests monkeypatch this.
STORY_ROOT = Path("outputs/dungeon-master")

# A sensible default so the first card lands seeded, not empty (FR-474 J1).
DEFAULT_TAGLINE = "10,000 B.C. in heat. Adult story."

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
    # Read-only per-character intents for a turn (``[{name, thinking, intent}]``).
    intents: list[dict] = field(default_factory=list)
    # The director's signals for a turn (FR-479): the scene has reached its END,
    # and any continuity flags (e.g. a non-roster name taking decisive action).
    scene_complete: bool = False
    continuity: list[str] = field(default_factory=list)


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
        if name.startswith(TURN_PREFIX):
            return turn_ops.turn_record(doc, int(name[len(TURN_PREFIX) :]))["recap"]
        return doc.setdefault(name, {"text": "", "reviewed": False})

    def _view(self, doc: dict, *, error: str | None = None) -> StageView:
        stage = self._stage(doc)
        entry = self._entry(doc, stage.name)
        intents: list[dict] = []
        scene_complete = False
        continuity: list[str] = []
        if stage.kind == "turn":
            n = int(stage.name[len(TURN_PREFIX) :])
            intents = turn_ops.turn_intents(doc, self._characters(doc), n)
            direction = turn_ops.turn_direction(doc, n)
            scene_complete = bool(direction.get("scene_complete"))
            continuity = list(direction.get("continuity") or [])
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
            scene_complete=scene_complete,
            continuity=continuity,
        )

    def _turn_intents(self, doc: dict, n: int) -> list[dict]:
        """The current turn's intents as ordered ``[{name, thinking, intent}]`` cards."""
        turns = doc.get("turns", [])
        if n < 1 or len(turns) < n:
            return []
        intents = turns[n - 1].get("intents", {})
        chars = self._characters(doc)
        out: list[dict] = []
        for cid in chars["roster"]:
            if cid in intents:
                out.append(
                    {
                        "name": chars["cards"].get(cid, {}).get("name") or cid,
                        "thinking": intents[cid].get("thinking", ""),
                        "intent": intents[cid].get("intent", ""),
                    }
                )
        return out

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
        result = await get_app(stage.graph).ainvoke(variables)
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

            if stage.kind == "turn":
                # Iterate re-rolls the whole turn (intents + recap together, J2);
                # the prompt steers the recap.
                n = int(stage.name[len(TURN_PREFIX) :])
                entry["text"] = await turn_ops.invoke_turn(
                    doc, self._characters(doc), n, instruction=prompt
                )
            else:
                entry["text"] = await self._invoke_stage(doc, stage, text, prompt)
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

            target = await self._accept_target(doc, story_dir, stage)
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
            if not self._can_visit(doc, target):
                return self._view(doc, error="That part of the story isn't ready yet.")
            doc["stage"] = target
            self._entry(doc, target)
            story_doc.write(story_dir, doc)
            await self._autodraft(doc, story_dir, target)
            return self._view(doc)
        except Exception as e:
            logger.exception("navigate failed for session %s", self._session_id)
            return self._view(self._load(story_dir), error=str(e))

    # ── tree navigation helpers ─────────────────────────────────────────────

    def _can_visit(self, doc: dict, target: str) -> bool:
        """Whether ``target`` is currently reachable (parent-reviewed / roster gates)."""
        if target == "synopsis":
            return True
        if target.startswith(CHAR_PREFIX):
            cid = target[len(CHAR_PREFIX) :]
            return bool(doc.get("synopsis", {}).get("reviewed")) and (
                cid in self._characters(doc)["cards"]
            )
        if target.startswith(TURN_PREFIX):
            # Play turns unlock only once the whole preplan is reviewed; a player
            # may revisit any existing turn or open the next one.
            if not preplan_complete(doc):
                return False
            suffix = target[len(TURN_PREFIX) :]
            if not suffix.isdigit():
                return False
            return 1 <= int(suffix) <= len(doc.get("turns", [])) + 1
        stage = STAGE_BY_NAME.get(target)
        if stage is None or stage.kind == "roster":
            # Unknown stage, or the non-visitable Characters group.
            return False
        if stage.parent:
            return bool(doc.get(stage.parent, {}).get("reviewed"))
        return True

    async def _accept_target(
        self, doc: dict, story_dir: Path, stage: Stage
    ) -> str | None:
        """The node to land on after accepting ``stage`` (FR-475 / FR-477)."""
        if stage.name == "synopsis":
            await self._expand_roster(doc, story_dir)
            return "key_scene"
        if stage.name == "key_scene":
            # Accepting the key scene may be the act that completes the preplan.
            if preplan_complete(doc):
                return f"{TURN_PREFIX}1"
            return self._next_unreviewed_char(doc)
        if stage.name.startswith(CHAR_PREFIX):
            nxt = self._next_unreviewed_char(doc, after=stage.name[len(CHAR_PREFIX) :])
            if nxt is not None:
                return nxt
            # Last character reviewed: open Play if the rest of the preplan is too.
            return f"{TURN_PREFIX}1" if preplan_complete(doc) else None
        if stage.name.startswith(TURN_PREFIX):
            n = int(stage.name[len(TURN_PREFIX) :])
            # Once the director reports the scene's END reached, stop offering a
            # plain next-turn advance — the scene is done, not replayed (FR-479 J5).
            if turn_ops.turn_direction(doc, n).get("scene_complete"):
                return None
            return f"{TURN_PREFIX}{n + 1}"
        return None

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

    def _next_unreviewed_char(self, doc: dict, after: str | None = None) -> str | None:
        """The next unreviewed character id (searching after ``after``, wrapping)."""
        chars = self._characters(doc)
        roster = chars["roster"]
        cards = chars["cards"]
        order = roster
        if after and after in roster:
            i = roster.index(after)
            order = roster[i + 1 :] + roster[: i + 1]
        for cid in order:
            if not cards.get(cid, {}).get("reviewed"):
                return CHAR_PREFIX + cid
        return None

    async def _autodraft(self, doc: dict, story_dir: Path, target: str) -> None:
        """Auto-draft ``target`` on entry: land on a populated card, not a blank one."""
        stage = resolve_stage(doc, target)
        entry = self._entry(doc, target)
        if stage.seed and not entry.get("text", "").strip():
            if stage.kind == "turn":
                entry["text"] = await turn_ops.invoke_turn(
                    doc, self._characters(doc), int(stage.name[len(TURN_PREFIX) :])
                )
            else:
                entry["text"] = await self._invoke_stage(doc, stage, "", stage.seed)
            entry["reviewed"] = False
            story_doc.write(story_dir, doc)
