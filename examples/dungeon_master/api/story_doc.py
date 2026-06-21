"""Per-session story document store for the DM v2 synopsis prototype (FR-474).

A tiny JSON file per session is the single source of truth for the synopsis
loop. The v2 overlay is intentionally small: ``tagline``, ``synopsis``,
``reviewed``. No graph or LLM touches this file — reads and writes are plain
document operations.

FR-556 (Contract A) adds the typed structural backbone of the chapter sub-tree.
The models are deliberately PERMISSIVE (``extra='allow'``, every field optional):
they type only the structural spine the 14 reach-in modules read so a malformed
write is caught at the seam, while the legacy and derived fields a real card
carries (``world_state`` as the empty-string placeholder OR a typed ledger dict,
``seam_packet``, free ``text``, ``chapter_memory``) ride along untouched. The
in-memory doc stays a plain ``dict`` -- :func:`parse` and
:func:`validate_chapter_card` validate at the WRITE boundary (the typed setter,
:func:`chapter_nav.write_chapter_card`), NOT at read time, so loading a legacy or
partial book that degrades gracefully today never raises mid-run (FR-556 J2).
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError


class InvalidChapterCard(ValueError):
    """A chapter card failed structural validation at the write boundary (FR-556).

    Raised by :func:`validate_chapter_card` (and thus the typed setter) when a card
    is not a mapping or its typed backbone is the wrong shape -- e.g. ``beats`` or
    ``turns`` is not a list. Distinct from the gate battery's content rejection
    (:class:`gap_detectors.ChapterGateError`, FR-558): this is shape, not playability.
    """


class ChapterCard(BaseModel):
    """The typed structural backbone of one chapter card (FR-556 Contract A).

    Only the spine the reach-in sites read is typed; derived/legacy fields ride
    along via ``extra='allow'``. A card with ``beats`` or ``turns`` of the wrong
    container type is rejected; everything the codebase actually persists validates.
    """

    model_config = ConfigDict(extra="allow")

    title: str = ""
    summary: str = ""
    beats: list[str] = []
    cast: list[str] = []
    entry_state: str = ""
    exit_state: str = ""
    turns: list[dict] = []
    reviewed: bool = False


class Chapters(BaseModel):
    """The ``chapters`` sub-tree: ordered ids plus the id -> card mapping (FR-556)."""

    model_config = ConfigDict(extra="allow")

    order: list[str] = []
    cards: dict[str, ChapterCard] = {}


class StoryDoc(BaseModel):
    """The typed boundary view of a story document (FR-556 Contract A).

    Permissive at every level so a live book -- with its session overlay
    (``tagline``, ``synopsis``, ``reviewed``), characters, and derived fields --
    validates; only the chapter spine is typed.
    """

    model_config = ConfigDict(extra="allow")

    chapters: Chapters = Chapters()


def parse(doc: dict) -> StoryDoc:
    """Validate a story document against the typed boundary view (FR-556).

    The boundary parse: proves a doc matches the structural contract. Callers keep
    using the plain ``dict`` for in-memory mutation; this is a validation gate, not
    a representation swap (FR-556 J2).
    """
    return StoryDoc.model_validate(doc)


def validate_chapter_card(card: object) -> ChapterCard:
    """Validate one chapter card's structure, raising :class:`InvalidChapterCard`.

    The write-boundary check the typed setter funnels every card through (FR-556 J4):
    a structurally-broken card is rejected here instead of being committed and
    surfacing later as a degraded instrument read.
    """
    try:
        return ChapterCard.model_validate(card)
    except ValidationError as exc:
        raise InvalidChapterCard(str(exc)) from exc


def doc_path(story_dir: Path | str) -> Path:
    """Path to the per-session ``story.json``."""
    return Path(story_dir) / "story.json"


def read(story_dir: Path | str) -> dict:
    """Read the story document. Raises if it does not exist (boundary)."""
    return json.loads(doc_path(story_dir).read_text())


def write(story_dir: Path | str, doc: dict) -> None:
    """Persist the story document for a single-writer UI."""
    Path(story_dir).mkdir(parents=True, exist_ok=True)
    doc_path(story_dir).write_text(json.dumps(doc, indent=2, ensure_ascii=False))
