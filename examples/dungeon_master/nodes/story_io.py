"""Side-effect tools for the dungeon-master narrative example.

FR-466: Turn-based book / dungeon master.

Layer 3 (side effects + state transforms) only — no LLM orchestration here.

Tools
-----
- ``save_story_tool``    : Phase 1 — persist the preplanned skeleton to story.json
                           plus per-chapter outline files.
- ``parse_dm_tool``      : Phase 3 — parse raw DM input into a structured
                           ``dm_action`` + ``dm_payload`` (DM CLI grammar).
- ``commit_beat_tool``   : Phase 3 — apply an edit, append the final beat to the
                           current chapter file, and advance turn/history.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# DM action keywords (no payload).
_DM_KEYWORDS = {"accept", "retry", "next-chapter", "end"}

# Actions that commit the current beat and advance the turn.
COMMITTING_ACTIONS = {"accept", "edit", "nudge", "next-chapter"}


def _slugify(text: str) -> str:
    """Filesystem-safe lowercase slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")
    return slug or "chapter"


def _to_plain(value: object) -> object:
    """Normalize an LLM result into plain JSON-serializable data.

    LLM nodes may return Pydantic models (structured output) or dicts
    (``parse_json``). Normalize both to plain dict/list at this boundary.
    """
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return {k: _to_plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_plain(v) for v in value]
    return value


def _unwrap_list(value: object, key: str) -> list:
    """Normalize an LLM object output into a plain list.

    List-producing prompts return ``{key: [...]}``. Unwrap that single boundary
    shape into the bare list, normalizing any nested models en route.
    """
    plain = _to_plain(value)
    if isinstance(plain, dict):
        inner = plain.get(key)
        if isinstance(inner, list):
            return inner
    if isinstance(plain, list):
        return plain
    return []


def save_story_tool(state: dict) -> dict:
    """Persist the preplanned story skeleton to disk (Phase 1).

    Writes ``story.json`` containing synopsis, plot, chapters and cast, plus one
    outline file per chapter (``chapter-NN-<slug>.md``).

    Args:
        state: Graph state containing ``output_dir``, ``synopsis``, ``plot``,
            ``chapters`` (list) and ``cast`` (list).

    Returns:
        dict with ``story_path`` (path to story.json) and ``chapter_outlines``
        (list of written outline file paths).
    """
    output_dir = Path(state.get("output_dir", "outputs/dungeon-master"))
    output_dir.mkdir(parents=True, exist_ok=True)

    chapters = _unwrap_list(state.get("chapters"), "chapters")
    cast = _unwrap_list(state.get("cast"), "cast")

    story = {
        "synopsis": _to_plain(state.get("synopsis")),
        "plot": _to_plain(state.get("plot")),
        "chapters": chapters,
        "cast": cast,
    }

    story_path = output_dir / "story.json"
    story_path.write_text(json.dumps(story, indent=2, ensure_ascii=False))
    logger.info("Wrote story skeleton to %s", story_path)

    chapter_outlines: list[str] = []
    for index, chapter in enumerate(chapters):
        title = chapter.get("title") if isinstance(chapter, dict) else str(chapter)
        summary = chapter.get("summary", "") if isinstance(chapter, dict) else ""
        filename = f"chapter-{index:02d}-{_slugify(title)}.md"
        filepath = output_dir / filename
        filepath.write_text(f"# {title}\n\n{summary}\n")
        chapter_outlines.append(str(filepath))
        logger.info("Wrote chapter outline %s", filepath)

    return {
        "story_path": str(story_path),
        "chapter_outlines": chapter_outlines,
        # Normalize wrapped LLM outputs back into plain lists for downstream use.
        "chapters": chapters,
        "cast": cast,
    }


def load_story_tool(state: dict) -> dict:
    """Load a persisted story skeleton from disk (Phase 3 turn-loop entry).

    Reads ``<output_dir>/story.json`` and seeds the turn-loop state with the
    chapters, cast, synopsis and plot, plus fresh turn counters.

    Returns:
        dict of state updates. ``turn_number``/``chapter_index``/``history``/
        ``steer`` are initialised only when absent so resumes are preserved.
    """
    output_dir = Path(state.get("output_dir", "outputs/dungeon-master"))
    story_path = output_dir / "story.json"
    story = json.loads(story_path.read_text())

    updates: dict = {
        "synopsis": story.get("synopsis"),
        "plot": story.get("plot"),
        "chapters": story.get("chapters") or [],
        "cast": story.get("cast") or [],
    }
    # Initialise turn state only on a fresh run.
    updates["turn_number"] = int(state.get("turn_number") or 0)
    updates["chapter_index"] = int(state.get("chapter_index") or 0)
    updates["history"] = list(state.get("history") or [])
    updates["steer"] = state.get("steer") or ""
    return updates


def prep_turn_tool(state: dict) -> dict:
    """Derive per-turn context for the planning + weave nodes (Phase 3).

    Computes the current ``chapter_goal`` from the active chapter and a
    ``recent_history`` string from the last few committed beats. Done in Python
    to avoid fragile variable-indexed expression access into nested state.
    """
    chapters = state.get("chapters") or []
    chapter_index = int(state.get("chapter_index") or 0)

    if 0 <= chapter_index < len(chapters):
        chapter = chapters[chapter_index]
        if isinstance(chapter, dict):
            chapter_goal = chapter.get("summary") or chapter.get("title") or ""
        else:
            chapter_goal = str(chapter)
    else:
        chapter_goal = "Bring the story to a close."

    history = state.get("history") or []
    recent = history[-3:]
    recent_history = "\n\n".join(str(beat) for beat in recent)

    return {"chapter_goal": chapter_goal, "recent_history": recent_history}


def parse_dm_tool(state: dict) -> dict:
    """Parse raw DM input into a structured action + payload (Phase 3).

    DM CLI grammar (case-insensitive action keywords):

    ===================  =======================================================
    ``dm_input``         result
    ===================  =======================================================
    ``""`` / ``accept``  ``dm_action=accept``
    ``edit: <text>``     ``dm_action=edit``,  ``dm_payload=<text>``
    ``nudge: <text>``    ``dm_action=nudge``, ``dm_payload=<text>``
    ``retry``            ``dm_action=retry``
    ``next-chapter``     ``dm_action=next-chapter``
    ``end``              ``dm_action=end``
    ===================  =======================================================

    Unrecognised non-empty input is treated as ``accept`` (the default path) so
    an Enter-through run never stalls.
    """
    raw = (state.get("dm_input") or "").strip()

    if not raw:
        return {"dm_action": "accept", "dm_payload": ""}

    prefix, _, payload = raw.partition(":")
    prefix_lc = prefix.strip().lower()

    if prefix_lc in {"edit", "nudge"} and payload.strip():
        return {"dm_action": prefix_lc, "dm_payload": payload.strip()}

    lowered = raw.lower()
    if lowered in _DM_KEYWORDS:
        return {"dm_action": lowered, "dm_payload": ""}

    # Unknown input → accept (autonomous default).
    return {"dm_action": "accept", "dm_payload": ""}


def commit_beat_tool(state: dict) -> dict:
    """Commit the current beat and advance the turn (Phase 3).

    Applies an edit when ``dm_action == 'edit'`` (replacing the woven beat with
    ``dm_payload``), appends the final beat to the current chapter file, advances
    ``turn_number``, appends to ``history``, and threads a Nudge into ``steer``
    for exactly the next turn.

    This tool is only reached on committing actions
    (accept/edit/nudge/next-chapter); retry never commits.

    Returns:
        dict of state updates: ``beat``, ``turn_number``, ``history``, ``steer``,
        and ``chapter_index`` (advanced on ``next-chapter``).
    """
    action = state.get("dm_action", "accept")
    payload = state.get("dm_payload", "")

    beat = payload if action == "edit" and payload else state.get("draft_beat", "")

    output_dir = Path(state.get("output_dir", "outputs/dungeon-master"))
    output_dir.mkdir(parents=True, exist_ok=True)

    chapter_index = int(state.get("chapter_index", 0))
    chapters = state.get("chapters") or []
    if 0 <= chapter_index < len(chapters):
        chapter = chapters[chapter_index]
        title = chapter.get("title") if isinstance(chapter, dict) else str(chapter)
    else:
        title = f"chapter-{chapter_index}"

    chapter_file = output_dir / f"chapter-{chapter_index:02d}-{_slugify(title)}.md"
    with chapter_file.open("a") as handle:
        handle.write(f"\n{beat}\n")
    logger.info("Committed beat to %s", chapter_file)

    history = list(state.get("history") or [])
    history.append(beat)

    updates: dict = {
        "beat": beat,
        "turn_number": int(state.get("turn_number", 0)) + 1,
        "history": history,
        # Nudge steers exactly the next turn; all other actions clear it.
        "steer": payload if action == "nudge" else "",
    }

    if action == "next-chapter":
        updates["chapter_index"] = chapter_index + 1

    return updates
