"""Cast-entrance manifest for DM v2 Final Cut (FR-539 S0).

The CANDIDATE half of the seam-entrance pair. FR-538's ``seam_entrance_gap``
measures the prose OUTCOME — who actually arrived on the page. This derives the
planning INPUT the Final Cut narrator needs: who *should* be staged this chapter,
computed as the FR-537 scoped-cast delta against the prior chapter's on-page
presence — ``resolve_chapter_cast(cid) − on_page(prev)``.

The two lenses are deliberately different (FR-539 Judgement, paired B1): a scoped
entrant may never surface in prose, and a prose name may be out of scope. This
manifest **feeds** the narrator; it must **never** subtract from FR-538's gap set.
Listing a name is not bridging a seam.

Each entrant carries ``last_status`` / ``last_location`` read from the entrant's
OWN row in the inherited ledger only (char-bounded, R2) — the material the narrator
writes the arrival *from* ("Arnulf, last seen wounded at the ford…") rather than
inventing it.

A deriver leaf above :mod:`chapter_open` (it reuses the single cast resolver
``resolve_chapter_cast`` and that module's word-bounded name matcher — no parallel
cast notion, ``false_duplicate`` avoided) and over :mod:`chapter_nav`,
:mod:`world_state`, and :mod:`lifecycle_resolver`. Pure — no LLM, no ``turn_ops``.
"""

from __future__ import annotations

from examples.dungeon_master.api import chapter_nav
from examples.dungeon_master.api.chapter_open import (
    _contains_token_run,
    _name_tokens,
    resolve_chapter_cast,
)
from examples.dungeon_master.api.lifecycle_resolver import _norm_name
from examples.dungeon_master.api.world_state import parse_world_state


def derive_cast_entrances(doc: dict, cid: str) -> list[dict]:
    """Characters entering chapter ``cid`` vs the prior chapter's scoped cast (FR-539).

    ``entering = resolve_chapter_cast(cid) − on_page(prev)`` — the CANDIDATE set the
    Final Cut narrator should establish, in roster order. Returns
    ``[{name, kind, last_seen_chapter, last_status, last_location}]`` where:

    - **kind** ∈ {``new``, ``returning``, ``continuing``}: never on-page in any prior
      chapter → ``new``; has an inherited ``character_lifecycle`` record → ``returning``;
      else (on-page earlier, scoped out of the immediate prior chapter) → ``continuing``.
    - **last_seen_chapter**: the latest prior chapter the entrant was on-page (``None``
      for a genuine newcomer).
    - **last_status** / **last_location**: the entrant's OWN row in the inherited ledger
      (char-bounded, R2); empty strings when no row exists.

    The first chapter (no prior) and a chapter with no resolvable cast both return
    ``[]`` — additive, never a manufactured entrance. This is a planning lens: it is
    narrator INPUT and must never suppress FR-538's prose-outcome gap (paired B1).
    """
    prev = chapter_nav.previous_chapter_id(doc, cid)
    if prev is None:
        return []

    cast = resolve_chapter_cast(doc, cid)
    if not cast:
        return []

    chars = doc.get("characters") or {}
    cards = chars.get("cards") or {}
    roster = [
        (char_id, name, _norm_name(name), _name_tokens(name))
        for char_id in (chars.get("roster") or [])
        for name in [str((cards.get(char_id) or {}).get("name") or char_id).strip()]
        if name
    ]

    order = chapter_nav.chapter_order(doc)
    try:
        cid_index = order.index(cid)
    except ValueError:
        cid_index = len(order)
    last_on_page: dict[str, str] = {}
    for pcid in order[:cid_index]:
        ptokens = _name_tokens(
            str(chapter_nav.chapter_card(doc, pcid).get("text") or "")
        )
        for _char_id, _name, norm, ntok in roster:
            if _contains_token_run(ptokens, ntok):
                last_on_page[norm] = str(pcid)
    on_page_prev = {norm for norm, c in last_on_page.items() if c == str(prev)}

    lifecycle = chapter_nav.inherited_seam_packet(doc, cid).get("character_lifecycle")
    lifecycle_names = {
        _norm_name(str(e.get("name") or ""))
        for e in (lifecycle or [])
        if isinstance(e, dict) and e.get("name")
    }

    ledger = parse_world_state(chapter_nav.inherited_world_state(doc, cid))
    row_by_norm = {
        _norm_name(str(c.get("name") or "")): c
        for c in (ledger.get("characters") or [])
        if isinstance(c, dict) and c.get("name")
    }

    entrances: list[dict] = []
    for _char_id, name, norm, _ntok in roster:
        if norm not in cast or norm in on_page_prev:
            continue
        if norm not in last_on_page:
            kind = "new"
        elif norm in lifecycle_names:
            kind = "returning"
        else:
            kind = "continuing"
        row = row_by_norm.get(norm) or {}
        entrances.append(
            {
                "name": name,
                "kind": kind,
                "last_seen_chapter": last_on_page.get(norm),
                "last_status": str(row.get("status") or ""),
                "last_location": str(row.get("location") or ""),
            }
        )
    return entrances
