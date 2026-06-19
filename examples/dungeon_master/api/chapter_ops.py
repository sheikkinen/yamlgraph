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

import hashlib
import json
import logging
import re

from examples.dungeon_master.api import chapter_nav, turn_ops
from examples.dungeon_master.api.graph_app import field, get_app
from examples.dungeon_master.api.seam_packet import (
    format_seam_packet,
    parse_seam_packet,
)
from examples.dungeon_master.api.tree import (
    CHAPTER_CLOSE_GRAPH,
    CHAPTER_OUTLINE_GRAPH,
    CHAPTER_REOUTLINE_GRAPH,
)
from examples.dungeon_master.api.witness_metrics import (
    reversal_pack_gap,
    unplayable_beat_gap,
)
from examples.dungeon_master.api.world_state import (
    apply_lane_floor,
    apply_ledger_delta,
    format_world_state,
    parse_world_state,
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

# FR-510: active-role detection for confirmed-dead character prose validation.
# Match: name immediately followed by an active verb within 8 word-tokens.
# Exclude: possessives (<name>'s) and locative-past patterns.
_DEAD_CHAR_ACTIVE_VERB = re.compile(
    r"\b(?:came|drove|thrust|jabbed|lifted|demanded|called|stepped|moved"
    r"|said|planted|struck|pressed|held|answered|snapped|ordered|pushed"
    r"|walked|turned|stood|kept|raised|reached|pointed|pulled|shoved"
    r"|forced|took|told|placed|stayed|brought|led|used|barred|pinned|seized|set)\b"
)
_DEAD_CHAR_LOCATIVE = re.compile(
    r"\b(?:where|when|as)\b",
    re.IGNORECASE,
)

# FR-519: warn-only object-possession continuity heuristic. A "loss" cue near a
# tracked object (a drop/throw/kick, or being driven into the ground) followed by
# a later "use" cue on the same object is a use-after-loss contradiction. Both
# verb sets are enumerated and the check is warn-only (no raise): the lane floor
# can manufacture false positives, so block is forbidden until the rate is
# measured (FR-519 B4); the prompt injection is the real enforcement.
_OBJECT_LOSS_CUE = re.compile(
    r"\b(?:dropped|lost|flung|threw|hurled|kicked|knocked|released|tossed"
    r"|abandoned|relinquished)\b"
    r"|let\s+go\s+of"
    r"|(?:wrenched|torn|knocked)\s+from"
    r"|into\s+the\s+(?:mud|ground|water|river|dirt|snow|flood|earth)",
    re.IGNORECASE,
)
_OBJECT_USE_CUE = re.compile(
    r"\b(?:raised|lifted|thrust|jabbed|swung|drove|used|struck|leveled"
    r"|levelled|pointed|aimed|wielded|pressed|planted|brought|hefted)\b",
    re.IGNORECASE,
)


class FinalCutReviseError(RuntimeError):
    """Typed chapter-close failure when one-pass revise cannot produce safe prose."""

    def __init__(self, payload: dict):
        self.payload = payload
        super().__init__(f"FINAL_CUT_REVISE_FAILED: {payload}")


def detect_dead_character_prose_violations(name: str, text: str) -> list[dict]:
    """Detect active-role appearances of a confirmed-dead character in prose.

    Returns typed violation dicts with keys ``type``, ``name``, ``excerpt``.
    Passive/possessive/locative patterns are excluded (FR-510 A6).
    An empty name always returns no violations.
    """
    name = (name or "").strip()
    if not name:
        return []

    pattern = re.compile(r"\b" + re.escape(name) + r"\b", re.IGNORECASE)
    violations: list[dict] = []

    for m in pattern.finditer(text):
        start = m.start()
        # Exclude possessives: name immediately followed by '
        if text[m.end() : m.end() + 2] in ("'s", "\u2019s"):
            continue
        # Exclude locative-past: preceded by where/when/as within 4 tokens
        prefix = text[max(0, start - 30) : start]
        if _DEAD_CHAR_LOCATIVE.search(prefix.split()[-1] if prefix.split() else ""):
            continue
        # Check for active verb within 8 word-tokens after the name
        suffix = text[m.end() : m.end() + 60]
        words_after = suffix.split()
        window = " ".join(words_after[:8])
        if _DEAD_CHAR_ACTIVE_VERB.search(window):
            excerpt_end = m.end() + min(60, len(suffix))
            excerpt = text[max(0, start - 5) : excerpt_end].strip()
            violations.append(
                {
                    "type": "active_presence",
                    "name": name,
                    "excerpt": excerpt[:120],
                }
            )
    return violations


def detect_object_use_after_loss(obj_name: str, holder: str, text: str) -> list[dict]:
    """Detect a tracked object being used after the prose showed it lost (FR-519).

    Walks occurrences of ``obj_name`` in order. The first occurrence whose
    surrounding window carries a loss cue (drop/throw/kick/driven-into-the-ground)
    marks the object as lost; any later occurrence preceded by a use cue
    (raised/thrust/swung …) is a use-after-loss contradiction. Warn-only by design
    (the caller never raises): an enumerated, conservative heuristic, returning
    typed hit dicts with keys ``object``, ``holder``, ``excerpt``. An empty object
    name returns no hits.
    """
    obj_name = (obj_name or "").strip()
    text = text or ""
    if not obj_name:
        return []
    pattern = re.compile(r"\b" + re.escape(obj_name) + r"\b", re.IGNORECASE)
    lost = False
    hits: list[dict] = []
    for m in pattern.finditer(text):
        start, end = m.start(), m.end()
        before = text[max(0, start - 48) : start]
        after = text[end : end + 48]
        if lost and _OBJECT_USE_CUE.search(before):
            excerpt = text[max(0, start - 30) : min(len(text), end + 40)].strip()
            hits.append(
                {"object": obj_name, "holder": holder, "excerpt": excerpt[:160]}
            )
        if _OBJECT_LOSS_CUE.search(before + " " + after):
            lost = True
    return hits


def _log_intra_chapter_continuity(
    doc: dict, cid: str, text: str, closed: dict | None
) -> None:
    """Warn-only intra-chapter physical-continuity diagnostics (FR-519).

    The enforcement is the final-cut prompt injection (the dead/possession blocks);
    this only *measures* the residual the prompt did not prevent — never raises.
    Two typed signals feed the FR-520 Phase-2 gate decision:

    - ``DEAD_CHARACTER_ACTS_POST_DEATH``: a within-chapter-dead character in an
      active role. A coarse upper bound — the death point cannot be located in
      prose mechanically, so legitimate pre-death action is also counted; a turn
      grained death point is exactly the FR-520 working memory this gates.
    - ``OBJECT_USED_AFTER_LOSS``: a tracked object used after the prose showed it
      lost (the lane floor can manufacture false positives, so warn-only per B4).
    """
    _, within_dead = turn_ops.dead_character_names(doc, cid, closed)
    for name in within_dead:
        for v in detect_dead_character_prose_violations(name, text):
            _LOG.warning(
                "Intra-chapter dead character prose: %s",
                {
                    "code": "DEAD_CHARACTER_ACTS_POST_DEATH",
                    "chapter_id": str(cid),
                    "name": v["name"],
                    "excerpt": v["excerpt"],
                },
            )

    tracked: dict[str, str] = {}
    sources = [parse_world_state(chapter_nav.inherited_world_state(doc, cid))]
    if isinstance(closed, dict):
        sources.append(parse_world_state(closed.get("world_state")))
    for ws in sources:
        for o in ws.get("objects", []):
            name = str(o.get("name") or "").strip()
            if name:
                tracked[name] = str(o.get("holder") or "").strip()
    for obj_name, holder in tracked.items():
        for hit in detect_object_use_after_loss(obj_name, holder, text):
            _LOG.warning(
                "Object used after loss: %s",
                {"code": "OBJECT_USED_AFTER_LOSS", "chapter_id": str(cid), **hit},
            )


def _collect_dead_character_prose_violations(
    dead_names: list[str], text: str, cid: str
) -> list[dict]:
    """Collect typed dead-character prose violations for all forbidden names."""
    out: list[dict] = []
    for dead_name in dead_names:
        for v in detect_dead_character_prose_violations(dead_name, text):
            out.append(
                {
                    "code": "DEAD_CHARACTER_PROSE_VIOLATION",
                    "chapter_id": str(cid),
                    "name": v["name"],
                    "pattern": v["type"],
                    "excerpt": v["excerpt"],
                }
            )
    return out


def _build_source_pointer(doc: dict, cid: str) -> dict:
    """Build deterministic seam source pointer for chapter-close diagnostics."""
    order = list((doc.get("chapters") or {}).get("order") or [])
    prev = ""
    if cid in order:
        idx = order.index(cid)
        if idx > 0:
            prev = str(order[idx - 1])
    seam = parse_seam_packet(chapter_nav.inherited_seam_packet(doc, cid))
    seam_hash = hashlib.sha256(
        json.dumps(seam, sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()[:16]
    return {"chapter_id": prev, "seam_hash": seam_hash}


def _norm_name(name: str) -> str:
    return " ".join(str(name or "").lower().split())


def _mentioned_non_possessive(name: str, text: str) -> bool:
    pattern = re.compile(r"\b" + re.escape(name) + r"\b(?!['\u2019]s)", re.IGNORECASE)
    return bool(pattern.search(text or ""))


def _safe_lines_preserved_ratio(
    original: str, revised: str, violations: list[dict]
) -> float:
    markers: list[str] = []
    for v in violations:
        name = str(v.get("name") or "").strip()
        if name:
            markers.append(name)
        excerpt = str(v.get("excerpt") or "").strip()
        for part in excerpt.splitlines():
            part = part.strip()
            if len(part) >= 12:
                markers.append(part)
    safe = []
    for line in (original or "").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        lowered = line.lower()
        if any(marker.lower() in lowered for marker in markers if marker):
            continue
        safe.append(line)
    if not safe:
        return 1.0
    kept = sum(1 for line in safe if line in (revised or ""))
    return kept / max(1, len(safe))


def _post_revise_invariant_failures(
    doc: dict,
    cid: str,
    original: str,
    revised: str,
    allowed_cast: list[str],
    violations: list[dict],
) -> list[str]:
    """Return invariant failures for one-pass revise acceptance."""
    failures: list[str] = []

    # Invariant 1: preserve beats as substrings when they were present in original.
    for beat in turn_ops.chapter_beats(doc, cid):
        beat_text = str(beat or "").strip()
        if not beat_text:
            continue
        if (
            beat_text.lower() in (original or "").lower()
            and beat_text.lower() not in (revised or "").lower()
        ):
            failures.append(f"beat_lost:{beat_text}")

    # Invariant 2: no newly introduced disallowed known character names.
    chars = dict(doc.get("characters") or {})
    cards = dict(chars.get("cards") or {})
    roster = list(chars.get("roster") or [])
    known_names = {
        _norm_name(
            str(dict(cards.get(char_id) or {}).get("name") or char_id).strip()
        ): str(dict(cards.get(char_id) or {}).get("name") or char_id).strip()
        for char_id in roster
    }
    allowed_norm = {_norm_name(n) for n in allowed_cast if str(n).strip()}
    for norm, display in known_names.items():
        if not display or norm in allowed_norm:
            continue
        if _mentioned_non_possessive(
            display, revised
        ) and not _mentioned_non_possessive(display, original):
            failures.append(f"new_disallowed_name:{display}")

    # Invariant 3: bounded length delta (<= 20%).
    original_len = max(1, len(original or ""))
    delta = abs(len(revised or "") - len(original or "")) / original_len
    if delta > 0.20:
        failures.append(f"length_delta_exceeds_20pct:{delta:.3f}")

    # Invariant 4: safe-line preservation ratio >= 0.90.
    ratio = _safe_lines_preserved_ratio(original, revised, violations)
    if ratio < 0.90:
        failures.append(f"safe_line_ratio_below_threshold:{ratio:.3f}")

    return failures


async def _revise_final_cut_once(
    doc: dict,
    cid: str,
    original_text: str,
    violations: list[dict],
    allowed_cast: list[str],
    dead_names: list[str],
    closed: dict | None = None,
) -> str:
    """Run exactly one constrained revise pass over final cut prose."""
    violation_lines = "\n".join(
        f"- {v.get('name')}: {v.get('excerpt')}" for v in violations
    )
    instruction = (
        "Revise ONLY the violating lines below. Keep all non-violating text unchanged. "
        "Do not add new characters, beats, or outcomes. Keep chronology and tone. "
        "Allowed cast: "
        + ", ".join(allowed_cast)
        + ". Forbidden dead characters: "
        + ", ".join(dead_names)
        + ". Violations:\n"
        + violation_lines
    )
    return await turn_ops.invoke_final_cut(
        doc,
        cid,
        instruction=instruction,
        draft=original_text,
        closed=closed,
    )


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


def _beat_list(item: object) -> list[str]:
    """The ordered key-event beats from an outline entry (FR-503; ``[]`` if absent).

    The director selects satisfied beats by number from this finite list, so the
    phrases are kept verbatim (not coerced through ``field``, which flattens to a
    single string). Blank entries are dropped; a missing/non-list ``beats`` yields
    an empty list, which :func:`_require_beats` then rejects at the boundary.
    """
    raw = item.get("beats") if isinstance(item, dict) else getattr(item, "beats", None)
    if not isinstance(raw, list):
        return []
    return [str(b).strip() for b in raw if str(b).strip()]


def _require_beats(chapters: list[dict]) -> list[dict]:
    """Reject any chapter that carries no enumerated ``beats`` (FR-504 contract).

    FR-503 replaced the director's unbounded free-text beat judgement with a
    finite, enumerated beat ledger but kept the FR-491 free-text path alive as the
    ``N == 0`` fallback. FR-504 retires that fallback: a non-empty ``beats`` list
    is now a validated boundary contract, normalized where the outline enters
    (``the_one_law``), so there is exactly one beat-judgement regime downstream and
    no chapter can silently fall back. Returns ``chapters`` unchanged when every
    one carries beats; raises otherwise (Commandment 6: no silent fallback).
    """
    for i, ch in enumerate(chapters, start=1):
        if not ch.get("beats"):
            raise ValueError(
                f"chapter {i} ({ch.get('title') or '?'!r}) outline carries no beats; "
                "every chapter must enumerate its key-event beats (FR-504)"
            )
    return chapters


# FR-525: how many times the outliner re-rolls when a chapter packs a removal AND
# return for one actor before raising (Commandment 6: no silent fallback). Three
# attempts = the first roll plus two corrected re-rolls.
_OUTLINE_MAX_ATTEMPTS = 3


def _packed_chapters(chapters: list[dict]) -> list[dict]:
    """Chapters that pack a same-actor removal-and-return (FR-525 over-pack).

    Pure: applies :func:`witness_metrics.reversal_pack_gap` to each authored chapter
    card and returns ``[{index, title, actors}]`` for every chapter that packs at
    least one actor's loss and return — the un-playable reversals the 16-turn cap
    (FR-501) would force-close mid-arc.
    """
    out: list[dict] = []
    for i, ch in enumerate(chapters, start=1):
        gap = reversal_pack_gap(ch)
        if gap["gap_count"]:
            out.append(
                {
                    "index": i,
                    "title": str(ch.get("title") or ""),
                    "actors": gap["packed_actors"],
                }
            )
    return out


def _reversal_feedback(packed: list[dict]) -> str:
    """The correction block appended to the synopsis on an outline re-roll (FR-525).

    Names each offending chapter and the actor(s) it both removes and returns, and
    restates the hard rule, so the re-invoked outliner moves the return to a later
    chapter rather than repeating the pack.
    """
    lines = [
        f'- Chapter {p["index"]} ("{p["title"]}") removes AND returns: '
        f"{', '.join(p['actors'])}"
        for p in packed
    ]
    return (
        "\n\nCORRECTION — your previous outline VIOLATED a hard rule: a character "
        "removed within a chapter must not also return within that same chapter. "
        "A chapter is played under a fixed turn budget and cannot portray both a "
        "loss and the return that reverses it. Re-author so each of these losses "
        "and its return are in DIFFERENT chapters (author the return as a beat of a "
        "LATER chapter):\n" + "\n".join(lines)
    )


def _unplayable_chapters(chapters: list[dict]) -> list[dict]:
    """Chapters whose FINAL beat is an unplayable time-skip epilogue (FR-528).

    Pure: applies :func:`witness_metrics.unplayable_beat_gap` to each authored
    chapter card and returns ``[{index, title, beat, marker}]`` for every chapter
    whose last beat LEADS with a future-time-skip ("By autumn, …"). A bounded scene
    (FR-501) can never enact such a beat, so ``scene_complete = (k == n)`` never fires
    and the chapter rides the cap (the no-progress tail FR-527 mis-treated as a play
    symptom). The cure normalizes at the partitioner boundary (``the_one_law``).
    """
    out: list[dict] = []
    for i, ch in enumerate(chapters, start=1):
        gap = unplayable_beat_gap(ch)
        if gap["gap_count"]:
            g = gap["gaps"][0]
            out.append(
                {
                    "index": i,
                    "title": str(ch.get("title") or ""),
                    "beat": g["beat"],
                    "marker": g["marker"],
                }
            )
    return out


def _unplayable_feedback(unplayable: list[dict]) -> str:
    """The correction block appended to the synopsis on an outline re-roll (FR-528).

    Names each offending chapter and its time-skip final beat, and restates the hard
    rule, so the re-invoked outliner either re-authors the final beat as a
    present-tense in-scene resolution OR folds the epilogue into the chapter
    ``summary`` (narration), never leaving it as a beat the bounded scene cannot
    enact.
    """
    lines = [
        f'- Chapter {p["index"]} ("{p["title"]}") final beat leads with '
        f'"{p["marker"]}": {p["beat"]}'
        for p in unplayable
    ]
    return (
        "\n\nCORRECTION — your previous outline VIOLATED a hard rule: a chapter's "
        "FINAL beat must be a present-tense event the scene can enact within its "
        "turn budget. A beat that resolves only after a time-skip ('By autumn, …', "
        "'Years later, …') can never be played, so the chapter never completes. "
        "Re-author each of these final beats as an in-scene, present-tense "
        "resolution, OR move the time-skip aftermath into that chapter's SUMMARY "
        "as closing narration (not a beat):\n" + "\n".join(lines)
    )


async def outline_chapters(doc: dict) -> list[dict]:
    """Split the accepted synopsis into an ordered list of ``{title, summary, beats}``.

    Runs ``chapter_outline.yaml`` once over the synopsis and returns the structured
    chapter list (J1: a titled paragraph per chapter — a shape a plain line-split
    cannot hold). Raises rather than substituting an empty book when the model
    returns no chapters, and rejects any chapter without enumerated ``beats``
    (:func:`_require_beats`, FR-504 contract) — both per Commandment 6: no silent
    fallback.

    FR-525 — split-gate: the partitioner can pack a death-and-return *reversal* into
    one chapter, but the play loop closes a chapter at ``CHAPTER_TURN_CAP`` turns
    (FR-501) and cannot portray both a loss and its reversing return. A chapter that
    removes AND returns the same actor therefore force-closes mid-reversal, leaving
    the return a phantom (``witness_metrics.beat_coverage_gap``). The cure normalizes
    at the partitioner boundary (``the_one_law``): after each outline the
    deterministic :func:`witness_metrics.reversal_pack_gap` checks every chapter; on a
    pack the outline is re-invoked with the violation fed back (bounded retry), then
    raises (no silent fallback) — never emitting a packed outline downstream.

    FR-528 — epilogue-gate: the partitioner can also author a chapter's FINAL beat as
    a time-skip epilogue ("By autumn, … a settlement that ends the feud"). A chapter
    resolves only when its director computes ``scene_complete = (k == n)`` over
    ``n = len(beats)``; a beat that resolves only after a season passes can never be
    enacted in the 16-turn cap, so ``scene_complete`` never fires and the chapter
    rides the cap (the no-progress tail FR-527 mis-treated downstream). The same
    boundary cure: :func:`witness_metrics.unplayable_beat_gap` checks every chapter;
    on a hit the outline is re-invoked instructing an in-scene resolution or a summary
    fold (bounded retry), then raises — never emitting a cap-riding chapter.
    """
    synopsis = doc.get("synopsis", {}).get("text", "")
    feedback = ""
    packed: list[dict] = []
    unplayable: list[dict] = []
    for _ in range(_OUTLINE_MAX_ATTEMPTS):
        result = await get_app(CHAPTER_OUTLINE_GRAPH).ainvoke(
            {"synopsis": synopsis + feedback, "outline": {}}
        )
        outline = result.get("outline") or {}
        raw = outline.get("chapters") if isinstance(outline, dict) else None
        chapters = [
            {
                "title": field(item, "title"),
                "summary": field(item, "summary"),
                "beats": _beat_list(item),
            }
            for item in (raw or [])
        ]
        if not chapters:
            raise ValueError("chapter outline returned no chapters")
        chapters = _require_beats(chapters)
        packed = _packed_chapters(chapters)
        unplayable = _unplayable_chapters(chapters)
        if not packed and not unplayable:
            return chapters
        feedback = ""
        if packed:
            feedback += _reversal_feedback(packed)
        if unplayable:
            feedback += _unplayable_feedback(unplayable)
    if packed:
        raise ValueError(
            "chapter outline packs a removal-and-return reversal into one chapter "
            f"after {_OUTLINE_MAX_ATTEMPTS} attempts (FR-525); a character lost within "
            f"a chapter must return in a LATER chapter: {packed}"
        )
    raise ValueError(
        "chapter outline authors an unplayable time-skip epilogue as a chapter's "
        f"final beat after {_OUTLINE_MAX_ATTEMPTS} attempts (FR-528); a final beat "
        "must be an in-scene present-tense resolution, not a post-time-skip aftermath: "
        f"{unplayable}"
    )


async def reoutline_chapter_beats(doc: dict, cid: str) -> list[str]:
    """Re-author chapter ``cid``'s beats from the prior chapter's carried state (FR-523).

    The chapter outliner is state-blind: it writes every chapter's beats from the
    synopsis alone (``outline_chapters``), so a lethal/exit beat can land on an actor
    the prior chapter left safe, with no beat bridging the two — the seam-teleport
    condemned by :func:`witness_metrics.seam_precondition_gap`. This re-derives the
    BEATS of one not-yet-played chapter from the synopsis + this chapter's FROZEN
    title/summary + the PRIOR chapter's committed ``world_state``/``seam_packet``, so
    the planner can author the bridging reposition beat the death requires — killing
    the contradiction in the spec (``the_one_law``: normalize at the outliner
    boundary, not downstream in the director/prose).

    Pure (J2): invokes ``CHAPTER_REOUTLINE_GRAPH`` and returns the parsed,
    ``_require_beats``-validated list; NEVER mutates ``doc`` and NEVER re-authors the
    title or summary (J4). Raises rather than substituting an empty beat list
    (Commandment 6: no silent fallback).
    """
    card = doc.get("chapters", {}).get("cards", {}).get(cid, {})
    result = await get_app(CHAPTER_REOUTLINE_GRAPH).ainvoke(
        {
            "synopsis": doc.get("synopsis", {}).get("text", ""),
            "chapter_title": card.get("title", ""),
            "chapter_summary": card.get("summary", ""),
            "prior_world_state": format_world_state(
                chapter_nav.inherited_world_state(doc, cid)
            ),
            "prior_seam_packet": format_seam_packet(
                chapter_nav.inherited_seam_packet(doc, cid)
            ),
            "reoutline": {},
        }
    )
    beats = _beat_list(result.get("reoutline") or {})
    if not beats:
        raise ValueError(
            f"chapter {cid} re-outline returned no beats (FR-523); every chapter "
            "must enumerate its key-event beats"
        )
    return beats


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
    over the whole played arc (:func:`turn_ops.invoke_final_cut`) rather than the
    raw recaps. A pure read: the adapter records the result onto the card.
    """
    card = doc.get("chapters", {}).get("cards", {}).get(cid, {})
    recaps = turn_ops.chapter_recaps_text(doc, cid)
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
    text = await turn_ops.invoke_final_cut(doc, cid, closed=closed)
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
    violations = _collect_dead_character_prose_violations(dead_names, text, cid)
    for payload in violations:
        _LOG.warning("Dead character prose violation: %s", payload)

    revised = False
    attempt_count = 0
    if violations:
        attempt_count = 1
        revised = True
        allowed_cast = turn_ops.build_allowed_scene_cast(doc, cid)
        revised_text = await _revise_final_cut_once(
            doc,
            cid,
            original_text=text,
            violations=violations,
            allowed_cast=allowed_cast,
            dead_names=dead_names,
            closed=closed,
        )
        invariant_failures = _post_revise_invariant_failures(
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
                "source_pointer": _build_source_pointer(doc, cid),
            }
            _LOG.error("Final cut revise failed: %s", payload)
            raise FinalCutReviseError(payload)

        text = revised_text
        violations = _collect_dead_character_prose_violations(dead_names, text, cid)
        if violations:
            payload = {
                "code": "FINAL_CUT_REVISE_FAILED",
                "chapter_id": str(cid),
                "attempt_count": attempt_count,
                "violations": violations,
                "invariant_failures": [],
                "revised": revised,
                "source_pointer": _build_source_pointer(doc, cid),
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

    _log_intra_chapter_continuity(doc, cid, text, closed)

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
