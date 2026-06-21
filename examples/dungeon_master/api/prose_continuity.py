"""Final-cut prose continuity: dead-character / object-loss detection + revise.

Split out of ``chapter_ops`` (FR-536 Workstream C) so the final-cut prose
validation regime lives in one cohesive module, distinct from chapter
close/compose orchestration. Two pure detectors (``detect_*``) measure the
physical-continuity residual the final-cut prompt did not prevent; the
``*_final_cut`` / ``*_prose_violations`` helpers wrap them into the one-pass
constrained revise cycle :func:`chapter_ops.close_chapter` runs when a
confirmed-dead character surfaces in the authored prose (FR-510/FR-511/FR-519).

Warn-only by design where the lane floor can manufacture false positives
(FR-519 B4): the enforcement is the prompt injection; this only measures and,
for the before-open dead class, drives a single bounded revise.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re

from examples.dungeon_master.api import chapter_nav, final_cut, turn_state
from examples.dungeon_master.api.seam_packet import parse_seam_packet
from examples.dungeon_master.api.world_state import parse_world_state

_LOG = logging.getLogger(__name__)

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


def log_intra_chapter_continuity(
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
    _, within_dead = final_cut.dead_character_names(doc, cid, closed)
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


def collect_dead_character_prose_violations(
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


def build_source_pointer(doc: dict, cid: str) -> dict:
    """Build deterministic seam source pointer for chapter-close diagnostics."""
    prev = chapter_nav.previous_chapter_id(doc, cid) or ""
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


def post_revise_invariant_failures(
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
    for beat in turn_state.chapter_beats(doc, cid):
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


async def revise_final_cut_once(
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
    return await final_cut.invoke_final_cut(
        doc,
        cid,
        instruction=instruction,
        draft=original_text,
        closed=closed,
    )
