"""Book-chapter operations for DM v2 (FR-488 / FR-491).

The synopsis is the whole book in outline. This module owns the two chapter
graph invocations, kept apart from the stage adapter (mirroring ``turn_ops`` for
the play loop) so the structured outline parse and the forward-carried
``world_state`` plumbing live in one place and ``session`` stays under the size
gate.

Both functions are PURE reads of the story ``doc`` — they invoke a graph and
return its normalized output, never mutating ``doc``. The adapter owns the writes
(spawning cards, recording text). The load-bearing seam is the forward-carry
(J7): each chapter is PLAYED turn by turn (FR-491), and when its scene completes
:func:`close_chapter` derives the end-of-chapter ``world_state`` from the
inherited ledger + this chapter's played recaps so the NEXT chapter is played
from where this one left off.
"""

from __future__ import annotations

import logging
import re

from examples.dungeon_master.api import (
    chapter_nav,
    chapter_open,
    final_cut,
    turn_state,
)
from examples.dungeon_master.api.graph_app import get_app
from examples.dungeon_master.api.ledger_reconcile import reconcile_ledger_exits
from examples.dungeon_master.api.prose_continuity import (
    FinalCutReviseError,
    build_source_pointer,
    collect_dead_character_prose_violations,
    log_intra_chapter_continuity,
    post_revise_invariant_failures,
    revise_final_cut_once,
)
from examples.dungeon_master.api.seam_packet import parse_seam_packet
from examples.dungeon_master.api.tree import CHAPTER_CLOSE_GRAPH
from examples.dungeon_master.api.world_state import (
    apply_lane_floor,
    apply_ledger_delta,
    format_world_state,
)

_LOG = logging.getLogger(__name__)

# FR-495: the LLM-authored chapter title tends to self-assert its own ordinal
# ("Chapter 1 — …", "Chapter 2:", "Ch. 3 -"). The composer's positional ``n`` is
# the authority, so strip a single leading "Chapter <ordinal><separator>" prefix
# before the title enters the heading — otherwise the ordinal doubles. The
# ``\s+`` after the label is the safety guard: a real title that merely begins
# with "Ch…" / "Chapter <word>" without a separator is left untouched (e.g.
# "Children of the Thaw", "Chapter Endings").
_LEADING_CHAPTER_LABEL = re.compile(
    r"^\s*ch(?:apter|\.)?\s+[\w-]+\s*[—–:\-.]\s*",
    re.IGNORECASE,
)
_RETURN_SIGNAL = re.compile(r"\b(return|returns|returned|reappear|reappears)\b")
_MEMORY_MAX_ITEMS = 12


def _empty_chapter_memory() -> dict:
    """Canonical empty chapter memory payload (FR-508 A1)."""
    return {
        "resolved_events": [],
        "irreversible_facts": [],
        "character_state_deltas": [],
        "open_threads": [],
        "forbidden_regressions": [],
    }


def _bounded_lines(raw: object) -> list[str]:
    """Normalize provider/authored list fields to stable bounded string lists."""
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        text = str(item or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
        if len(out) >= _MEMORY_MAX_ITEMS:
            break
    return out


def _derive_chapter_memory(packet: dict) -> dict:
    """Derive deterministic chapter memory from seam packet artifacts."""
    memory = _empty_chapter_memory()
    memory["resolved_events"] = _bounded_lines(packet.get("resolved_events"))
    memory["open_threads"] = _bounded_lines(packet.get("open_threads"))
    memory["irreversible_facts"] = _bounded_lines(packet.get("must_carry_facts"))
    memory["forbidden_regressions"] = _bounded_lines(packet.get("opening_constraints"))

    deltas: list[dict] = []
    for item in list(packet.get("character_lifecycle") or []):
        name = str(item.get("name") or "").strip()
        to_state = str(item.get("existence_state") or "").strip()
        if not name or not to_state:
            continue
        source_chapter = item.get("source_chapter")
        evidence = (
            f"seam_lifecycle(source_chapter={source_chapter})"
            if isinstance(source_chapter, int)
            else "seam_lifecycle"
        )
        deltas.append(
            {
                "name": name,
                "from_state": None,
                "to_state": to_state,
                "evidence": evidence,
            }
        )
        if len(deltas) >= _MEMORY_MAX_ITEMS:
            break
    memory["character_state_deltas"] = deltas
    return memory


def _clean_chapter_title(title: str) -> str:
    """Drop a self-asserted 'Chapter N —' prefix; the composer owns the ordinal."""
    return _LEADING_CHAPTER_LABEL.sub("", title or "").strip()


def _planned_reappearance_chapter(doc: dict, name: str) -> int | None:
    """Find first planned chapter index where ``name`` is marked as returning.

    Uses chapter metadata only (title/summary/beats) to keep this deterministic.
    Returns a 1-based chapter index over ``chapters.order`` when a return signal
    is present; otherwise ``None``.
    """
    if not name.strip():
        return None
    target = name.lower().strip()
    chapters = doc.get("chapters", {})
    order = chapters.get("order", [])
    cards = chapters.get("cards", {})
    for i, cid in enumerate(order, start=1):
        card = cards.get(cid, {})
        text_parts = [
            str(card.get("title") or ""),
            str(card.get("summary") or ""),
            " ".join(str(b or "") for b in (card.get("beats") or [])),
        ]
        hay = "\n".join(text_parts).lower()
        if target in hay and _RETURN_SIGNAL.search(hay):
            return i
    return None


def _clamp_lifecycle_reappearance_to_plan(doc: dict, packet: dict) -> dict:
    """Clamp lifecycle reappearance chapter to chapter-plan return metadata.

    If a lifecycle record proposes an earlier reappearance than the plan's first
    return signal for that character, raise it to the planned chapter index.
    """
    lifecycle = list(packet.get("character_lifecycle") or [])
    if not lifecycle:
        return packet
    out = dict(packet)
    out_lifecycle: list[dict] = []
    for item in lifecycle:
        rec = dict(item)
        name = str(rec.get("name") or "").strip()
        planned = _planned_reappearance_chapter(doc, name)
        allowed = rec.get("allowed_reappearance_from_chapter")
        if planned is not None and (not isinstance(allowed, int) or allowed < planned):
            rec["allowed_reappearance_from_chapter"] = planned
        out_lifecycle.append(rec)
    out["character_lifecycle"] = out_lifecycle
    return out


def _enforce_reappearance_state_coherence(packet: dict) -> dict:
    """Reconcile a lifecycle row that is *confirmed* dead yet *allowed* to return.

    FR-526 (behind FR-525) — a close seam committed records like Arnulf's in
    ``10024-BC`` Ch3: ``existence_state=confirmed_dead`` together with a non-null
    ``allowed_reappearance_from_chapter``. The two are contradictory — a character
    the plan intends to bring back is *presumed* dead, not *confirmed* dead. The
    close LLM derives the death from the loss; ``_clamp_lifecycle_reappearance_to_plan``
    sets the reappearance index from the plan but reconciles only the index, never
    the state, and nothing else rejects the pairing.

    This is a PURE, packet-only invariant (no ``doc`` — coherence depends on the row
    alone) normalized at the close seam where the record is committed
    (``the_one_law``): when a row carries a non-null reappearance allowance, soften
    ``confirmed_dead`` to ``missing_presumed_dead``, PRESERVING the allowance (the
    authored return intent — the opposite fix of clearing it, J4). Rows without a
    reappearance allowance are left untouched, so a genuine confirmed death stays
    confirmed (J4 negative control). Scope is ``existence_state`` only; the
    same-chapter index incoherence is FR-525's to prevent at the partitioner (J5).
    """
    lifecycle = list(packet.get("character_lifecycle") or [])
    out = dict(packet)
    out_lifecycle: list[dict] = []
    for item in lifecycle:
        rec = dict(item)
        allowed = rec.get("allowed_reappearance_from_chapter")
        if allowed is not None and rec.get("existence_state") == "confirmed_dead":
            rec["existence_state"] = "missing_presumed_dead"
        out_lifecycle.append(rec)
    out["character_lifecycle"] = out_lifecycle
    return out


async def close_chapter(doc: dict, cid: str) -> dict:
    """Close played chapter ``cid``: derive ``{text, world_state, seam_packet}``.

    The adapter-facing entry to the **Scene lifecycle** (FR-493 J5, hosted in
    :mod:`turn_ops`): the terminal step that derives ``world_state_out`` + final
    text once a chapter's scene completes. Invoked from
    :func:`doc_ops.apply_chapter_close`; stays here (not in ``turn_ops``) as the
    chapter-level seam, distinct from the write-wrapper that records its result.

    The forward-carry seam (FR-491 G2/B, preserving FR-488 J7 through play): a
    chapter is no longer expanded from its summary in one shot — it is PLAYED, and
    when its scene completes this derives continuity artifacts. ``world_state`` runs
    ``chapter_close.yaml`` once over the inherited ledger (where the previous
    chapter left off) + this chapter's played recaps, returning the end-of-chapter
    ledger the NEXT chapter inherits. ``seam_packet`` is the explicit chapter seam
    handoff contract for turn-1 of chapter N+1. ``text`` is the chapter's *final text*: the
    per-chapter Final Cut (FR-492), one continuous beat-faithful passage composed
    over the whole played arc (:func:`final_cut.invoke_final_cut`) rather than the
    raw recaps. A pure read: the adapter records the result onto the card.
    """
    card = doc.get("chapters", {}).get("cards", {}).get(cid, {})
    recaps = turn_state.chapter_recaps_text(doc, cid)
    result = await get_app(CHAPTER_CLOSE_GRAPH).ainvoke(
        {
            "synopsis": doc.get("synopsis", {}).get("text", ""),
            "summary": card.get("summary", ""),
            "index": cid,
            "previous_world_state": format_world_state(
                chapter_nav.inherited_world_state(doc, cid)
            ),
            "recaps": recaps,
            "chapter_close": {},
        }
    )
    closed = result.get("chapter_close") or {}
    # FR-519: thread the close-graph output into the final cut so the within-chapter
    # death + possession constraints reach the prompt. The chapter's own world_state
    # is not committed to the doc until this function returns, so it must be passed,
    # not read back (B1).
    text = await final_cut.invoke_final_cut(doc, cid, closed=closed)
    seam_packet = parse_seam_packet(closed.get("seam_packet"))
    seam_packet = _clamp_lifecycle_reappearance_to_plan(doc, seam_packet)
    seam_packet = _enforce_reappearance_state_coherence(seam_packet)
    # FR-510 + FR-511: validate final prose against confirmed-dead characters from
    # prior seam and run one constrained revise cycle if needed. Scope is the
    # before-open class only: a within-chapter-dead character acts legitimately up
    # to their death, so the blanket active-role detector must not raise on them
    # (FR-519 B3); their residual is measured warn-only below.
    prior_seam = parse_seam_packet(chapter_nav.inherited_seam_packet(doc, cid))
    dead_names = [
        str(item.get("name") or "").strip()
        for item in list(prior_seam.get("character_lifecycle") or [])
        if str(item.get("existence_state") or "").strip() == "confirmed_dead"
        and str(item.get("name") or "").strip()
    ]
    violations = collect_dead_character_prose_violations(dead_names, text, cid)
    for payload in violations:
        _LOG.warning("Dead character prose violation: %s", payload)

    revised = False
    attempt_count = 0
    if violations:
        attempt_count = 1
        revised = True
        allowed_cast = chapter_open.build_allowed_scene_cast(doc, cid)
        revised_text = await revise_final_cut_once(
            doc,
            cid,
            original_text=text,
            violations=violations,
            allowed_cast=allowed_cast,
            dead_names=dead_names,
            closed=closed,
        )
        invariant_failures = post_revise_invariant_failures(
            doc,
            cid,
            original=text,
            revised=revised_text,
            allowed_cast=allowed_cast,
            violations=violations,
        )
        if invariant_failures:
            payload = {
                "code": "FINAL_CUT_REVISE_FAILED",
                "chapter_id": str(cid),
                "attempt_count": attempt_count,
                "violations": violations,
                "invariant_failures": invariant_failures,
                "revised": revised,
                "source_pointer": build_source_pointer(doc, cid),
            }
            _LOG.error("Final cut revise failed: %s", payload)
            raise FinalCutReviseError(payload)

        text = revised_text
        violations = collect_dead_character_prose_violations(dead_names, text, cid)
        if violations:
            payload = {
                "code": "FINAL_CUT_REVISE_FAILED",
                "chapter_id": str(cid),
                "attempt_count": attempt_count,
                "violations": violations,
                "invariant_failures": [],
                "revised": revised,
                "source_pointer": build_source_pointer(doc, cid),
            }
            _LOG.error("Final cut revise failed: %s", payload)
            raise FinalCutReviseError(payload)
        _LOG.info(
            "Final cut revise applied: %s",
            {
                "chapter_id": str(cid),
                "attempt_count": attempt_count,
                "revised": revised,
            },
        )

    log_intra_chapter_continuity(doc, cid, text, closed)

    chapter_memory = _derive_chapter_memory(seam_packet)
    inherited_ledger = chapter_nav.inherited_world_state(doc, cid)
    order = doc.get("chapters", {}).get("order", [])
    current_index = order.index(cid) if cid in order else 0
    emitted = closed.get("world_state")
    operations = emitted.get("operations") if isinstance(emitted, dict) else None
    # FR-514 J4: the three non-relationship lanes keep full-ledger emission but are
    # floored (an emptied lane carries forward, never zeroes state); the
    # relationship lane is the update-delta path applied by code (FR-514/515/517),
    # so a forgetful close can no longer reset the bonds (10020-BC Ch5 dropout).
    world_ledger = apply_lane_floor(emitted, inherited_ledger)
    delta = apply_ledger_delta(inherited_ledger, operations, current_index)
    world_ledger["relationships"] = delta["relationships"]
    # FR-542 A: the close graph derives world_state from prose and can miss a
    # director-reported cast_exit, leaving a swept-away actor logged present (the
    # Arnulf resurrection). Reconcile the emitted ledger against this chapter's
    # reported exits at the boundary the contradiction enters, before the next
    # chapter inherits it. Interim fix (continuity-projection-plan.md step 2),
    # superseded by the write-once projected lifecycle ledger (step 3).
    world_ledger = reconcile_ledger_exits(
        world_ledger, turn_state.chapter_cast_exits(doc, cid)
    )
    return {
        "text": text,
        "world_state": world_ledger,
        "seam_packet": seam_packet,
        "chapter_memory": chapter_memory,
    }


def compose_book_deterministic(doc: dict) -> str:
    """Assemble the played chapters into one reader manuscript — pure, no LLM.

    The book seam (FR-492 Phase 3): a deterministic read over the chapters'
    already-final texts, so the model is off the path to a *first* book —
    composition is free, reproducible, and never empty when a chapter is played.
    Walks ``chapters.order`` and heads each PLAYED chapter (one whose per-chapter
    Final Cut produced a non-empty ``text``) as ``# Chapter {n}: {title}``
    followed by its beat-faithful prose; sections are joined by a blank line. The
    number ``n`` is the chapter's position in ``order`` so it stays stable when an
    earlier chapter is not yet played. The forward-carry ``world_state`` ledger is
    plumbing for the next chapter's play, not manuscript, so it never appears.
    Raises rather than returning "" when no chapter has been played (Commandment
    6: no silent fallback). LLM voice/continuity passes are a later revision seam
    (FR-492 Phase 4), not this first composition.
    """
    chapters = doc.get("chapters", {})
    cards = chapters.get("cards", {})
    sections: list[str] = []
    for n, cid in enumerate(chapters.get("order", []), start=1):
        card = cards.get(cid, {})
        text = (card.get("text") or "").strip()
        if not text:
            continue
        title = _clean_chapter_title(card.get("title", ""))
        heading = f"# Chapter {n}: {title}" if title else f"# Chapter {n}"
        sections.append(f"{heading}\n\n{text}")
    if not sections:
        raise ValueError("book composition has no played chapter")
    return "\n\n".join(sections)
