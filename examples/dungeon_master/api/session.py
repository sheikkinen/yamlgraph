"""Stateless, stage-driven session adapter for DM v2 (FR-474, Phases 1–2).

The app is a chain of identical loops, one per story stage:

    weave (generate / iterate) → edit (autosave) → accept → next stage

There is exactly one generation mode per stage: ``weave`` runs that stage's graph
with the current draft (possibly empty) plus a writer's instruction. An empty
draft means the instruction is the premise (first generation); a non-empty draft
means it is a change to apply. ``accept`` freezes the current stage and advances
the cursor to the next one. There is no outline, chapter, or beat path — those
live in ``purgatory/``.

The per-session ``story.json`` is the single source of truth::

    {
      "tagline": "...",
      "stage": "plot",
      "synopsis": {"text": "...", "reviewed": true},
      "plot":     {"text": "...", "reviewed": false}
    }
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from examples.dungeon_master.api import story_doc

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path("examples/dungeon_master/prompts")

# Base directory for per-session story files. Tests monkeypatch this.
STORY_ROOT = Path("outputs/dungeon-master")

# A sensible default so the first card lands seeded, not empty (FR-474 J1).
DEFAULT_TAGLINE = "A clockmaker discovers her city is a machine winding down"


@dataclass(frozen=True)
class Stage:
    """One story stage: its graph, label, and the prior stage it reads as context."""

    name: str
    label: str
    graph: str
    # Names of earlier stages whose accepted text is passed in as graph variables
    # (e.g. plot reads the synopsis). Each becomes a variable of the same name.
    context: tuple[str, ...] = ()
    # Default instruction used to auto-draft this stage the moment it is entered
    # (on accept of the prior stage), so the DM never lands on a blank card. A
    # stage with no seed waits for a manual prompt (the first stage never auto-
    # drafts because it is never advanced to).
    seed: str = ""


# The ordered chain of stages. Adding a stage here extends the app; no per-stage
# generate/edit/accept code is needed (Phase 2 added "plot" with this one line).
STAGES: tuple[Stage, ...] = (
    Stage("synopsis", "Synopsis", "examples/dungeon_master/synopsis.yaml"),
    Stage(
        "plot",
        "Plot",
        "examples/dungeon_master/plot.yaml",
        context=("synopsis",),
        seed="Draft the three-act plot from the accepted synopsis.",
    ),
)
STAGE_BY_NAME = {s.name: s for s in STAGES}
FIRST_STAGE = STAGES[0]

_app_cache: dict[str, object] = {}


def _reset_caches() -> None:
    """Reset the compiled-graph cache (for testing)."""
    _app_cache.clear()


def _get_app(graph: str):
    """Compile + cache a stage graph (no checkpointer)."""
    if graph not in _app_cache:
        from yamlgraph.graph_loader import compile_graph, load_graph_config

        config = load_graph_config(graph)
        _app_cache[graph] = compile_graph(config).compile()
    return _app_cache[graph]


def _story_dir(session_id: str) -> Path:
    return STORY_ROOT / session_id


def _clean_text(value: object) -> str:
    """Normalize a raw model result to plain string, stripping a stray fence."""
    text = str(value or "").strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def _next_stage(name: str) -> Stage | None:
    """The stage after ``name``, or None if ``name`` is the last stage."""
    idx = next((i for i, s in enumerate(STAGES) if s.name == name), -1)
    if idx < 0 or idx + 1 >= len(STAGES):
        return None
    return STAGES[idx + 1]


@dataclass
class StageView:
    """View model for the current stage's card."""

    stage: str
    label: str
    text: str = ""
    reviewed: bool = False
    tagline: str = DEFAULT_TAGLINE
    # Accepted prior stages, oldest first, for the breadcrumb trail.
    trail: list[tuple[str, str]] = field(default_factory=list)
    error: str | None = None


class DMSession:
    """Stateless, stage-driven adapter — all state in the story document."""

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
        return STAGE_BY_NAME.get(doc.get("stage", FIRST_STAGE.name), FIRST_STAGE)

    def _entry(self, doc: dict, name: str) -> dict:
        """The per-stage sub-document ``{"text", "reviewed"}`` (created if absent)."""
        return doc.setdefault(name, {"text": "", "reviewed": False})

    def _trail(self, doc: dict, current: str) -> list[tuple[str, str]]:
        """Labels of stages up to (not including) ``current``, for breadcrumbs."""
        trail: list[tuple[str, str]] = []
        for s in STAGES:
            if s.name == current:
                break
            trail.append((s.name, s.label))
        return trail

    def _view(self, doc: dict, *, error: str | None = None) -> StageView:
        stage = self._stage(doc)
        entry = self._entry(doc, stage.name)
        return StageView(
            stage=stage.name,
            label=stage.label,
            text=entry.get("text", ""),
            reviewed=bool(entry.get("reviewed")),
            tagline=doc.get("tagline", DEFAULT_TAGLINE),
            trail=self._trail(doc, stage.name),
            error=error,
        )

    # ── actions (operate on the current stage) ──────────────────────────────

    async def _invoke_stage(
        self, doc: dict, stage: Stage, draft: str, instruction: str
    ) -> str:
        """Run a stage's graph and return its cleaned text.

        Builds the graph variables from the draft, the writer's instruction, and
        each upstream context stage's accepted text. Shared by ``weave`` (manual)
        and ``accept`` (auto-draft on entry).
        """
        variables = {"draft": draft, "instruction": instruction}
        for ctx in stage.context:
            variables[ctx] = doc.get(ctx, {}).get("text", "")
        result = await _get_app(stage.graph).ainvoke(variables)
        return _clean_text(result.get(stage.name))

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
        """Freeze the current stage, advance the cursor, and auto-draft the next.

        The acceptance is persisted first; then, if the next stage declares a
        ``seed`` and has no draft yet, its graph is run so the DM lands on a
        populated card instead of a blank one (purgatory-style continuity). If
        the current stage is the last one, it stays selected as read-only.
        """
        story_dir = _story_dir(self._session_id)
        try:
            doc = self._load(story_dir)
            stage = self._stage(doc)
            entry = self._entry(doc, stage.name)
            if text.strip():
                entry["text"] = text
            entry["reviewed"] = True
            nxt = _next_stage(stage.name)
            if nxt is not None:
                doc["stage"] = nxt.name
                self._entry(doc, nxt.name)  # ensure the next sub-document exists
            story_doc.write(story_dir, doc)  # persist acceptance before drafting

            # Auto-draft on entry: land on a populated card, not an empty one.
            if nxt is not None and nxt.seed:
                nxt_entry = self._entry(doc, nxt.name)
                if not nxt_entry.get("text", "").strip():
                    nxt_entry["text"] = await self._invoke_stage(doc, nxt, "", nxt.seed)
                    nxt_entry["reviewed"] = False
                    story_doc.write(story_dir, doc)
            return self._view(doc)
        except Exception as e:
            logger.exception("accept failed for session %s", self._session_id)
            return self._view(self._load(story_dir), error=str(e))
