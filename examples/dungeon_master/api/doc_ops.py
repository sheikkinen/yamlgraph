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

from pathlib import Path

from examples.dungeon_master.api import chapter_ops, story_doc, turn_ops
from examples.dungeon_master.api.graph_app import clean_text, get_app
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
    ``{title, summary, text, world_state, reviewed}``. Independent of the
    characters roster and of the preplan/play gate (J3).
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
                "reviewed": False,
            },
        )
    if name.startswith(TURN_PREFIX):
        cid, n = parse_turn(name)
        return turn_ops.turn_record(doc, cid, n)["recap"]
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
    outline = await chapter_ops.outline_chapters(doc)
    for i, chunk in enumerate(outline, start=1):
        cid = str(i)
        chs["cards"][cid] = {
            "title": chunk.get("title") or f"Chapter {cid}",
            "summary": chunk.get("summary", ""),
            "text": "",
            "world_state": "",
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
        card["reviewed"] = True
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
