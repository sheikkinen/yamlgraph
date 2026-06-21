"""FR-553: deterministic turn-director prompt-mass + presence witness (visibility, not a gate).

The investigation that corrected the FR-553 premise: the ~12.3k tokens a turn costs is the
*whole turn graph's* 5-call sum (dominated by the three ``_map_intents_sub`` calls), NOT the
director prompt. The director's actual ``{{ scene }}`` -- assembled by
:func:`turn_ops.running_scene` -- is compact (~0.5-1.6k tokens). This module measures that
true quantity deterministically and asks the decisive question the mass framing missed:

    Was the governing fact's subject present in the scene at the turn where the break occurred?

If absent, the fix is a bounded/re-ranked prompt (pin the fact). If present-but-the-break-
still-happened, the lever is prompt *wording* or the recap/narrator dropping the fact -- NOT
mass. Both signals are recomputed offline from the persisted story doc: no LLM, no LangSmith
dependency (tracing is optional and eventually-consistent), and a tiktoken-absent environment
degrades the mass block to omission -- never a char/4 proxy, never a gate (FR-553 C2).
"""

from __future__ import annotations

import re

from examples.dungeon_master.api.turn_ops import running_scene

_POSTURE = "visibility-not-gate"
_ENCODING = "cl100k_base"


def _encoder():
    """The ``cl100k_base`` tiktoken encoder, or ``None`` when tiktoken is unavailable.

    Returning ``None`` (not a fallback proxy) lets :func:`prompt_mass_summary` omit the
    block entirely, honoring both "no char/4 proxy" and "never break the run" (C2).
    """
    try:
        import tiktoken
    except Exception:
        return None
    try:
        return tiktoken.get_encoding(_ENCODING)
    except Exception:
        return None


def _count(enc, text: str) -> int:
    return len(enc.encode(text or ""))


def prompt_mass_summary(story_doc: dict) -> dict | None:
    """Per-turn director-scene token mass, recomputed offline (FR-553 quantity #3).

    Walks ``chapters.order`` and, for every turn of every chapter, recomputes
    :func:`running_scene` (which reads only the doc) and tiktoken-counts it. Reports the
    per-turn mass plus each chapter's peak/mean and the global peak. Returns ``None`` when
    tiktoken is absent or no chapter carries a turn, so the witness simply omits the block.
    This is the director's ACTUAL scene size -- never the 12k turn-graph total (the 5-call
    sum) the FR-553 premise mistook for it.
    """
    enc = _encoder()
    if enc is None:
        return None
    chapters = story_doc.get("chapters") or {}
    order = list(chapters.get("order") or [])
    cards = chapters.get("cards") or {}
    by_chapter: list[dict] = []
    peak = 0
    for cid in order:
        turns = list((cards.get(cid) or {}).get("turns") or [])
        if not turns:
            continue
        per_turn: list[dict] = []
        for n in range(1, len(turns) + 1):
            tokens = _count(enc, running_scene(story_doc, cid, n))
            per_turn.append({"turn": n, "scene_tokens": tokens})
            peak = max(peak, tokens)
        token_counts = [t["scene_tokens"] for t in per_turn]
        by_chapter.append(
            {
                "chapter": cid,
                "turn_count": len(turns),
                "peak_tokens": max(token_counts),
                "mean_tokens": round(sum(token_counts) / len(token_counts), 1),
                "per_turn": per_turn,
            }
        )
    if not by_chapter:
        return None
    return {
        "posture": _POSTURE,
        "encoding": _ENCODING,
        "peak_scene_tokens": peak,
        "by_chapter": by_chapter,
    }


def _subject_present_at_open(story_doc: dict, cid: str, subject: str) -> bool:
    """Whether ``subject`` is named in chapter ``cid``'s opening scene (turn 1).

    The governing cross-chapter facts (a prior chapter's ending, a character's lifecycle
    status) reach the director only via the turn-1 seam packet; subject-presence in the
    recomputed opening scene is the necessary condition for the fact to be salient there.
    A missing chapter id or empty subject is treated as absent.
    """
    if not subject or not cid:
        return False
    return subject.lower() in running_scene(story_doc, cid, 1).lower()


def presence_correlation(story_doc: dict, witness: dict) -> dict:
    """Cross-reference each continuity break against subject-presence at its failing turn (C3).

    For every ``fact_reversal`` gap (the break manifests at the ``to_chapter`` opening) and
    every ``seam_entrance`` gap (at that chapter's opening), recompute the opening scene and
    record whether the break's subject is present. ``presence_gap_count`` (subject ABSENT)
    points at a bounded/re-ranked prompt fix; ``present_but_ignored_count`` (subject present,
    yet the break occurred) points at prompt wording or the recap/narrator -- not mass. Pure:
    reads the doc and the already-assembled witness blocks, never the LLM.
    """
    checks: list[dict] = []
    for block in (witness.get("fact_reversal") or {}).get("by_chapter") or []:
        cid = block.get("to_chapter")
        for gap in block.get("gaps") or []:
            subject = str(gap.get("subject") or "")
            checks.append(
                {
                    "source": "fact_reversal",
                    "subject": subject,
                    "failing_chapter": cid,
                    "failing_turn": 1,
                    "governing_fact": str(gap.get("prior_fact") or ""),
                    "subject_present_at_failing_turn": _subject_present_at_open(
                        story_doc, cid, subject
                    ),
                }
            )
    for block in (witness.get("seam_entrance") or {}).get("by_chapter") or []:
        cid = block.get("chapter")
        for gap in block.get("gaps") or []:
            subject = str(gap.get("name") or "")
            checks.append(
                {
                    "source": "seam_entrance",
                    "subject": subject,
                    "failing_chapter": cid,
                    "failing_turn": 1,
                    "governing_fact": str(gap.get("kind") or ""),
                    "subject_present_at_failing_turn": _subject_present_at_open(
                        story_doc, cid, subject
                    ),
                }
            )
    gaps = sum(1 for c in checks if not c["subject_present_at_failing_turn"])
    ignored = sum(1 for c in checks if c["subject_present_at_failing_turn"])
    return {
        "posture": _POSTURE,
        "check_count": len(checks),
        "presence_gap_count": gaps,
        "present_but_ignored_count": ignored,
        "checks": checks,
    }


def _revives_in_recap(text: str, name: str) -> bool:
    """Whether ``name`` appears in ``text`` other than as a possessive (FR-554 C1).

    The honest substring proxy: an exited name in a strictly-later recap is a revival
    UNLESS its only occurrences are possessive (``Name's`` / ``Name\u2019s`` -- e.g.
    "Arnulf's fallen body", "Arnulf's weapon arm": aftermath the narrator may legitimately
    describe). The single frozen exclusion is possessive-only -- no verb lexicon, no
    subject/actor-position parser (the ``regex_fourth_exclusion`` trap). It is a flag to
    look, not a verdict: it still fires on legitimate non-possessive mentions (grief:
    "they wept for Arnulf"), an over-count accepted under visibility-not-gate.
    """
    if not text or not name:
        return False
    for m in re.finditer(rf"\b{re.escape(name)}\b(['\u2019]s)?", text, re.IGNORECASE):
        if not m.group(1):  # this occurrence is not a possessive Name's
            return True
    return False


def revived_actors(story_doc: dict) -> dict:
    """Exited actors narrated on stage again in a strictly-later recap (FR-554, C1).

    For each chapter, the director's per-turn ``cast_exits`` names the roster members who
    have left the scene -- killed, drowned, swept away -- and must not act again. The exit
    is legitimate up to and including the turn it is first declared; a *revival* is the same
    name appearing (non-possessively, :func:`_revives_in_recap`) in the recap of a turn
    STRICTLY AFTER its first-exit turn. Returns ``{posture, count, incidents}`` where each
    incident is ``{chapter, name, exit_turn, revival_turn}``; empty when no exits are
    recorded. Pure (reads only the doc), deterministic, visibility-not-gate -- the
    regression gauge the recap-salience wording change must drive toward zero.
    """
    chapters = story_doc.get("chapters") or {}
    order = list(chapters.get("order") or [])
    cards = chapters.get("cards") or {}
    incidents: list[dict] = []
    for cid in order:
        turns = list((cards.get(cid) or {}).get("turns") or [])
        first_exit: dict[str, int] = {}
        for t in turns:
            n = t.get("n")
            if n is None:
                continue
            for raw in (t.get("direction") or {}).get("cast_exits") or []:
                name = str(raw).strip()
                if name:
                    first_exit.setdefault(name, n)
        if not first_exit:
            continue
        for t in turns:
            n = t.get("n")
            text = (t.get("recap") or {}).get("text") or ""
            for name, exit_turn in first_exit.items():
                if n is None or n <= exit_turn:
                    continue
                if _revives_in_recap(text, name):
                    incidents.append(
                        {
                            "chapter": cid,
                            "name": name,
                            "exit_turn": exit_turn,
                            "revival_turn": n,
                        }
                    )
    return {"posture": _POSTURE, "count": len(incidents), "incidents": incidents}


def format_prompt_salience_report(witness: dict) -> str:
    """A terse per-chapter mass + presence-verdict report (FR-553 deliverable 2).

    Joins the deterministic ``prompt_mass`` block with the ``presence_correlation`` verdict.
    The decisive per-call split (intents vs director vs recap) is corroborating LangSmith
    evidence cited in FR-553, not a data dependency here.
    """
    lines: list[str] = ["FR-553 turn-director prompt salience (visibility, not a gate)"]
    mass = witness.get("prompt_mass")
    if mass:
        lines.append(
            f"  peak director scene: {mass['peak_scene_tokens']} tok "
            f"({mass['encoding']})"
        )
        lines.append("  chapter  turns  peak_tok  mean_tok")
        for chapter in mass["by_chapter"]:
            lines.append(
                f"  {chapter['chapter']:>7}  {chapter['turn_count']:>5}  "
                f"{chapter['peak_tokens']:>8}  {chapter['mean_tokens']:>8}"
            )
    else:
        lines.append("  prompt_mass: omitted (tiktoken unavailable)")
    presence = witness.get("presence_correlation") or {}
    lines.append(
        "  presence: "
        f"{presence.get('check_count', 0)} breaks -- "
        f"{presence.get('presence_gap_count', 0)} presence-gap (subject absent), "
        f"{presence.get('present_but_ignored_count', 0)} present-but-ignored"
    )
    revived = witness.get("revived_actor") or {}
    if "count" in revived:
        lines.append(
            "  revived actors (exited, then on stage again -- FR-554): "
            f"{revived.get('count', 0)}"
        )
        for inc in revived.get("incidents") or []:
            lines.append(
                f"    ch{inc['chapter']} {inc['name']}: "
                f"exited t{inc['exit_turn']}, on stage again t{inc['revival_turn']}"
            )
    return "\n".join(lines)
