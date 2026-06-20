"""Derived operations over the in-memory story ``doc`` for DM v2 (FR-493).

The sibling of ``story_doc`` (raw ``story.json`` I/O): this module owns the
*derived* operations over the loaded doc — the per-stage entry accessors, the
single stage-graph invocation, and the side-effecting expansions the adapter
performs around ``accept``/``navigate``. Lifted out of ``session`` so the adapter
stays under the size gate (FR-493 J1/J2), mirroring ``turn_ops`` / ``chapter_ops``.

Every function is a module-level ``(doc, …)`` operation — **no ``self``** (J1):
``session`` imports these; they import nothing from ``session`` (acyclic). The
doc accessors (``entry``/``characters``/``chapters``) and ``invoke_stage`` are the
shared core the expansions reuse; the expansions (``expand_roster``,
``expand_chapters``, ``apply_chapter_close``, ``compose_stage``, ``autodraft``)
are the side-effecting cluster navigation deliberately stays out of (FR-489 J1).
"""

from __future__ import annotations

import logging
from pathlib import Path

from examples.dungeon_master.api import (
    chapter_ops,
    outline_ops,
    story_doc,
    turn_ops,
    turn_state,
)
from examples.dungeon_master.api.graph_app import clean_text, get_app
from examples.dungeon_master.api.lifecycle_resolver import _norm_name
from examples.dungeon_master.api.tree import (
    CHAPTER_PREFIX,
    CHAR_PREFIX,
    STAGE_BY_NAME,
    TURN_PREFIX,
    Stage,
    parse_turn,
    resolve_stage,
    split_roster,
    unique_slug,
)

# ── doc accessors (the shared core) ─────────────────────────────────────────

_LOG = logging.getLogger(__name__)


def _empty_chapter_memory() -> dict:
    """Canonical empty chapter memory payload (FR-508 migration-safe default)."""
    return {
        "resolved_events": [],
        "irreversible_facts": [],
        "character_state_deltas": [],
        "open_threads": [],
        "forbidden_regressions": [],
    }


def _normalize_chapter_cast(doc: dict, authored: object) -> list[str]:
    """Map authored chapter cast names to roster display names; drop unknowns (FR-537).

    The boundary normalization (``the_one_law``): the outline names a chapter's
    focal cast in free text, but the play loop scopes the animated roster by roster
    identity. Keep only names that match a roster character (case-insensitive), emit
    the roster's canonical display name, and warn on every dropped unknown so a
    typo'd cast name is visible — never silently widened back to the full roster.
    """
    names = [str(c).strip() for c in (authored or []) if str(c).strip()]
    if not names:
        return []
    chars = doc.get("characters") or {}
    cards = chars.get("cards") or {}
    by_norm: dict[str, str] = {}
    for char_id in chars.get("roster") or []:
        display = str((cards.get(char_id) or {}).get("name") or char_id).strip()
        if display:
            by_norm.setdefault(_norm_name(display), display)
    out: list[str] = []
    seen: set[str] = set()
    for name in names:
        key = _norm_name(name)
        display = by_norm.get(key)
        if display is None:
            _LOG.warning("expand_chapters: dropping unknown chapter cast name %r", name)
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(display)
    return out


def _ensure_live_synopsis(doc: dict) -> dict:
    """Get or create deterministic rolling synopsis container."""
    syn = doc.setdefault("live_synopsis", {})
    syn.setdefault("summary", "")
    syn.setdefault("immutable_ledger", [])
    syn.setdefault("character_states", {})
    syn.setdefault("last_chapter_id", "")
    return syn


def _update_live_synopsis(doc: dict, cid: str, chapter_memory: dict) -> None:
    """Update rolling synopsis deterministically from chapter memory."""
    syn = _ensure_live_synopsis(doc)
    ledger = [str(x).strip() for x in list(syn.get("immutable_ledger") or [])]
    existing = {x.lower() for x in ledger if x}
    for fact in list(chapter_memory.get("irreversible_facts") or []):
        text = str(fact).strip()
        if not text:
            continue
        key = text.lower()
        if key in existing:
            continue
        existing.add(key)
        ledger.append(text)

    highlights = list(chapter_memory.get("resolved_events") or [])
    if not highlights:
        highlights = list(chapter_memory.get("open_threads") or [])
    snippet = "; ".join(str(x).strip() for x in highlights if str(x).strip())
    snippet = snippet[:480].rstrip()

    syn["immutable_ledger"] = ledger
    states = dict(syn.get("character_states") or {})
    for item in list(chapter_memory.get("character_state_deltas") or []):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        to_state = str(item.get("to_state") or "").strip()
        if name and to_state:
            states[name] = to_state
    syn["character_states"] = states
    syn["summary"] = (
        f"After chapter {cid}: {snippet}" if snippet else f"After chapter {cid}."
    )
    syn["last_chapter_id"] = str(cid)


def characters(doc: dict) -> dict:
    """The characters sub-document ``{reviewed, roster, cards}`` (created if absent)."""
    chars = doc.setdefault("characters", {"reviewed": False, "roster": [], "cards": {}})
    chars.setdefault("roster", [])
    chars.setdefault("cards", {})
    return chars


def chapters(doc: dict) -> dict:
    """The chapters sub-document ``{reviewed, order, cards}`` (created if absent).

    A fixed ordered set of book chapters (FR-488): ``order`` is the 1-based string
    ids in story sequence, ``cards`` maps each id to
    ``{title, summary, text, world_state, seam_packet, reviewed}``. Independent
    of the characters roster and of the preplan/play gate (J3).
    """
    chs = doc.setdefault("chapters", {"reviewed": False, "order": [], "cards": {}})
    chs.setdefault("order", [])
    chs.setdefault("cards", {})
    return chs


def entry(doc: dict, name: str) -> dict:
    """The per-stage sub-document ``{"text", "reviewed"}`` (created if absent).

    Static stages live at the top level; ``char:<id>`` stages are nested under
    ``characters.cards`` (A2); ``turn:<cid>:<n>`` stages reuse the chapter's
    turn ``recap`` entry so weave/edit/accept operate on it unchanged (FR-491 C).
    """
    if name.startswith(CHAR_PREFIX):
        cid = name[len(CHAR_PREFIX) :]
        cards = characters(doc)["cards"]
        return cards.setdefault(cid, {"name": cid, "text": "", "reviewed": False})
    if name.startswith(CHAPTER_PREFIX):
        cid = name[len(CHAPTER_PREFIX) :]
        cards = chapters(doc)["cards"]
        return cards.setdefault(
            cid,
            {
                "title": f"Chapter {cid}",
                "summary": "",
                "text": "",
                "world_state": "",
                "seam_packet": {
                    "resolved_events": [],
                    "open_threads": [],
                    "must_carry_facts": [],
                    "opening_constraints": [],
                    "character_lifecycle": [],
                },
                "chapter_memory": _empty_chapter_memory(),
                "reviewed": False,
            },
        )
    if name.startswith(TURN_PREFIX):
        cid, n = parse_turn(name)
        return turn_state.turn_record(doc, cid, n)["recap"]
    return doc.setdefault(name, {"text": "", "reviewed": False})


async def invoke_stage(doc: dict, stage: Stage, draft: str, instruction: str) -> str:
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
    errors = result.get("errors") or []
    if errors:
        # The graph swallowed a node failure into its errors list (e.g. a provider
        # content-policy block on an explicit scene). Surface the real reason
        # instead of returning the empty output it left behind (Commandment 6:
        # expose the fault, never hide it behind a blank card).
        last = errors[-1]
        reason = getattr(last, "message", None) or str(last)
        raise RuntimeError(reason)
    return clean_text(result.get(stage.output_key or stage.name))


# ── side-effecting expansions (navigation stays pure; FR-489 J1) ────────────


async def expand_roster(doc: dict, story_dir: Path) -> None:
    """Derive the cast from the synopsis and spawn one card per new name (A4)."""
    chars = characters(doc)
    roster_stage = STAGE_BY_NAME["characters"]
    raw = await invoke_stage(doc, roster_stage, "", roster_stage.seed)
    seen = set(chars["cards"].keys())
    for name in split_roster(raw):
        cid = unique_slug(name, seen)
        seen.add(cid)
        if cid not in chars["cards"]:
            chars["cards"][cid] = {"name": name, "text": "", "reviewed": False}
            chars["roster"].append(cid)
    story_doc.write(story_dir, doc)


async def expand_chapters(doc: dict, story_dir: Path) -> None:
    """Split the synopsis into a fixed chapter set, one card per chapter (FR-488).

    Idempotent (J6): the chapter set is FIXED at derivation — numeric ids cannot
    idempotently append like character slugs — so once ``order`` is populated this
    is a no-op. Otherwise it outlines the synopsis into ``{title, summary}`` chunks
    and spawns ``cards["1"]…["N"]`` with empty ``text``/``world_state`` for later
    per-chapter expansion.
    """
    chs = chapters(doc)
    if chs["order"]:
        return  # already derived; the set is fixed
    outline = await outline_ops.outline_chapters(doc)
    for i, chunk in enumerate(outline, start=1):
        cid = str(i)
        chs["cards"][cid] = {
            "title": chunk.get("title") or f"Chapter {cid}",
            "summary": chunk.get("summary", ""),
            "beats": list(chunk.get("beats") or []),
            "cast": _normalize_chapter_cast(doc, chunk.get("cast")),
            "entry_state": chunk.get("entry_state", ""),
            "exit_state": chunk.get("exit_state", ""),
            "text": "",
            "world_state": "",
            "seam_packet": {
                "resolved_events": [],
                "open_threads": [],
                "must_carry_facts": [],
                "opening_constraints": [],
                "character_lifecycle": [],
            },
            "chapter_memory": _empty_chapter_memory(),
            "reviewed": False,
        }
        chs["order"].append(cid)
    story_doc.write(story_dir, doc)


async def apply_chapter_close(doc: dict, story_dir: Path, cid: str) -> None:
    """Record played chapter ``cid``'s end-of-chapter ledger (FR-491 B; J7).

    The forward-carry write: when a chapter's scene completes,
    ``chapter_ops.close_chapter`` (a pure read) derives its end-of-chapter
    ``world_state`` from the inherited ledger + the played recaps; this records it
    onto the card so the NEXT chapter inherits it, and marks the chapter reviewed.
    Named ``apply_chapter_close`` to stay distinct from the pure
    ``chapter_ops.close_chapter`` it wraps (FR-493 J3). Idempotent enough to re-run
    on a re-accept.
    """
    closed = await chapter_ops.close_chapter(doc, cid)
    card = chapters(doc)["cards"].get(cid)
    if card is not None:
        card["text"] = closed["text"]
        card["world_state"] = closed["world_state"]
        card["seam_packet"] = closed["seam_packet"]
        card["chapter_memory"] = closed.get("chapter_memory") or _empty_chapter_memory()
        card["reviewed"] = True
        _update_live_synopsis(doc, cid, card["chapter_memory"])
        story_doc.write(story_dir, doc)
    await reoutline_next_chapter(doc, story_dir, cid)


async def reoutline_next_chapter(doc: dict, story_dir: Path, cid: str) -> None:
    """Re-author the NEXT chapter's beats from chapter ``cid``'s committed state (FR-523).

    The state-aware re-outline write (J3): once ``cid`` has closed and committed its
    ``world_state``/``seam_packet``, the chapter that inherits that state has its
    beats re-derived (``outline_ops.reoutline_chapter_beats``, a pure read) so a
    lethal/exit beat is physically continuous with where the story left each actor —
    closing the seam-teleport :func:`gap_detectors.seam_precondition_gap` measures.

    Guarded (J7): a no-op unless a next chapter exists AND it has not been played
    (no committed turns) AND it is not ``reviewed`` — a partially-played chapter must
    not have its beats yanked out from under it. Only ``beats`` is rewritten; title
    and summary stay frozen (J4). The up-front ``expand_chapters`` draft is untouched.
    """
    chs = chapters(doc)
    order = chs.get("order", [])
    if cid not in order:
        return
    i = order.index(cid)
    if i + 1 >= len(order):
        return  # no next chapter
    next_cid = order[i + 1]
    next_card = chs["cards"].get(next_cid)
    if next_card is None:
        return
    if next_card.get("reviewed") or next_card.get("turns"):
        return  # already played / reviewed — do not disturb
    next_card["beats"] = await outline_ops.reoutline_chapter_beats(doc, next_cid)
    story_doc.write(story_dir, doc)


async def compose_stage(
    doc: dict, stage_entry: dict, stage: Stage, *, instruction: str
) -> bool:
    """Draft a composed multi-layer stage (currently only a turn).

    A turn is not a single ``invoke_stage`` call: it re-rolls its intents + recap
    together (FR-477 J2). The finishes are no longer navigable stages (FR-492):
    each chapter's final text is composed by ``close_chapter``. ``weave`` and
    ``autodraft`` share this exact dispatch — the only difference is whether a
    writer's ``instruction`` steers the composition (weave) or it is a fresh draft
    (auto-draft, empty arg). Mutates ``stage_entry`` in place; returns whether the
    stage was a composed stage, so the caller can fall back to ``invoke_stage`` for
    an ordinary card when it was not.
    """
    if stage.kind == "turn":
        cid, n = parse_turn(stage.name)
        stage_entry["text"] = await turn_ops.invoke_turn(
            doc, characters(doc), cid, n, instruction=instruction
        )
    else:
        return False
    return True


async def autodraft(doc: dict, story_dir: Path, target: str) -> None:
    """Auto-draft ``target`` on entry: land on a populated card, not a blank one."""
    stage = resolve_stage(doc, target)
    rec = entry(doc, target)
    if stage.seed and not rec.get("text", "").strip():
        if not await compose_stage(doc, rec, stage, instruction=""):
            rec["text"] = await invoke_stage(doc, stage, "", stage.seed)
        rec["reviewed"] = False
        story_doc.write(story_dir, doc)
