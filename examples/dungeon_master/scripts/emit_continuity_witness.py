"""FR-530 Stage 1 -- post-generation continuity witness (visibility, not a gate).

The independent ``book_reviewer`` is the only component that reads *across* seams and
computes a pairwise chapter-seam continuity score. Today it runs after generation as a
separate example, so its verdict never travels with the run that produced the book. This
witness reads the just-written ``review.md`` and emits the continuity score in a small
machine-readable JSON alongside the book artifacts, so every run carries its own score
and FR-531's deterministic report can later join it.

**Posture (FR-522):** visibility only. A low score NEVER fails the run or CI -- the caller
wires this as a non-blocking step. An LLM continuity score is not a deterministic
guarantee, so it is reported, never gated.

The per-seam corrective re-roll (Stage 2) is explicitly OUT of scope (FR-530 J2): it is
gated behind this Stage 1 proving useful and FR-532's calibration of the axis.

Run::

    python -m examples.dungeon_master.scripts.emit_continuity_witness --out <book-dir>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from examples.dungeon_master.api.allegiance_ledger import allegiance_transitions
from examples.dungeon_master.api.character_overlay import derive_overlay
from examples.dungeon_master.api.fact_reversal import fact_reversal_gap, name_tokens
from examples.dungeon_master.api.prompt_salience import (
    format_prompt_salience_report,
    presence_correlation,
    prompt_mass_summary,
)
from examples.dungeon_master.api.seam_entrance import seam_entrance_gap
from examples.dungeon_master.scripts.calibrate_continuity_axis import (
    parse_continuity_breaks,
)

__all__ = [
    "build_witness",
    "seam_entrance_summary",
    "fact_reversal_summary",
    "overlay_trail_summary",
    "write_witness",
    "main",
]

WITNESS_FILENAME = "continuity_witness.json"


def build_witness(book: str, review_md: str) -> dict:
    """Project the reviewer's continuity axis into a small machine-readable record."""
    score, breaks = parse_continuity_breaks(review_md)
    return {
        "book": book,
        "continuity_score": score,
        "break_count": len(breaks),
        "posture": "visibility-not-gate",
    }


def seam_entrance_summary(story_doc: dict) -> dict:
    """Aggregate the deterministic seam-entrance witness over a story doc (FR-538).

    Walks ``chapters.order`` and runs :func:`seam_entrance_gap` per chapter, summing
    the roster-lens entrance gaps and tallying them by ``kind``. Roster lens only:
    non-roster named NPCs are out of scope (see FR-538 Scope). Purely additive to
    the witness; never gates the run.
    """
    order = list((story_doc.get("chapters") or {}).get("order") or [])
    total = 0
    by_kind: dict[str, int] = {}
    by_chapter: list[dict] = []
    for cid in order:
        result = seam_entrance_gap(story_doc, cid)
        gap_count = result["gap_count"]
        if not gap_count:
            continue
        total += gap_count
        by_chapter.append(
            {
                "chapter": result["chapter"],
                "gap_count": gap_count,
                "gaps": [
                    {"name": g["name"], "kind": g["kind"]} for g in result["gaps"]
                ],
            }
        )
        for gap in result["gaps"]:
            by_kind[gap["kind"]] = by_kind.get(gap["kind"], 0) + 1
    return {"gap_count": total, "by_kind": by_kind, "by_chapter": by_chapter}


# FR-547: a token is treated as a proper noun (named entity) only if it appears
# capitalized in a NON-sentence-initial position at least this many times across the
# committed prose. >=2 drops one-off dialogue-capitalized common words (the 10032-BC
# residual was {keep:3, this:2, mark:1, here:1}; the threshold drops mark/here, and
# `_subject_tokens` reuse drops `this`). Tunable; the irreducible residual escalates
# to the deferred Phase-2 LLM same-fact-identity tier (visibility-not-gate posture).
_PROPER_NOUN_MIN_CAPS = 2

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*")


def _proper_noun_entities(story_doc: dict) -> set[str]:
    """Corpus proper-noun lexicon for entity-disagreement suppression (FR-547).

    Reads committed chapter prose (``chapters.cards[*].text``) and collects tokens
    that appear capitalized in a non-sentence-initial position at least
    ``_PROPER_NOUN_MIN_CAPS`` times (length >= 4, lowercased). This recovers off-roster
    named characters (Arnulf, Aschenwulf) the roster omits, without depending on roster
    completeness, while locatives -- never capitalized mid-sentence -- stay out so the
    discriminator is not poisoned. The roster's own name-tokens are unioned in as a
    belt-and-suspenders for a rostered member rarely present in prose.
    """
    chapters = story_doc.get("chapters") or {}
    cards = chapters.get("cards") or {}
    counts: dict[str, int] = {}
    for cid in chapters.get("order") or []:
        text = (cards.get(cid) or {}).get("text") or ""
        for sentence in re.split(r"[.!?]+", str(text)):
            for index, match in enumerate(_WORD_RE.finditer(sentence)):
                token = match.group(0)
                if index > 0 and token[:1].isupper() and len(token) >= 4:
                    key = token.lower()
                    counts[key] = counts.get(key, 0) + 1
    entities = {t for t, n in counts.items() if n >= _PROPER_NOUN_MIN_CAPS}

    chars = story_doc.get("characters") or {}
    name_cards = chars.get("cards") or {}
    for char_id in chars.get("roster") or []:
        name = (name_cards.get(char_id) or {}).get("name") or char_id
        entities |= name_tokens(name)
    return entities


def fact_reversal_summary(story_doc: dict) -> dict:
    """Aggregate the deterministic fact-reversal witness over a story doc (FR-542 B).

    Walks adjacent chapter pairs in ``chapters.order`` and runs
    :func:`fact_reversal_gap` over each, summing resolved-fact reversals and
    forbidden-regression violations and tallying them by ``reason``. Purely additive
    to the witness, measurement-first (FR-538 posture): a reversal is reported, never
    gates the run in Phase 1 (gate promotion is the FR-542 Phase-2 follow-up).

    A corpus proper-noun entity set is built once from the prose and threaded into
    each pair, so a reversal whose two lines name DISJOINT entities -- sharing only an
    incidental locative token -- is suppressed (FR-547).
    """
    chapters = story_doc.get("chapters") or {}
    order = list(chapters.get("order") or [])
    cards = chapters.get("cards") or {}
    entities = _proper_noun_entities(story_doc)
    total = 0
    by_reason: dict[str, int] = {}
    by_chapter: list[dict] = []
    for prev_cid, cid in zip(order, order[1:], strict=False):
        result = fact_reversal_gap(
            cards.get(prev_cid) or {}, cards.get(cid) or {}, entities
        )
        gap_count = result["gap_count"]
        if not gap_count:
            continue
        total += gap_count
        by_chapter.append(
            {
                "from_chapter": prev_cid,
                "to_chapter": cid,
                "gap_count": gap_count,
                "gaps": [
                    {
                        "subject": g["subject"],
                        "reason": g["reason"],
                        "prior_fact": g["prior_fact"],
                        "reversed_fact": g["reversed_fact"],
                    }
                    for g in result["gaps"]
                ],
            }
        )
        for gap in result["gaps"]:
            by_reason[gap["reason"]] = by_reason.get(gap["reason"], 0) + 1
    return {
        "gap_count": total,
        "by_reason": by_reason,
        "by_chapter": by_chapter,
        "posture": "visibility-not-gate",
    }


def overlay_trail_summary(story_doc: dict) -> dict:
    """Aggregate the FR-541 derived character overlay into a review trail (FR-544).

    Walks ``chapters.order`` and, for each roster character, REUSES
    :func:`character_overlay.derive_overlay` to recompute the CURRENT STATE the
    intent node saw entering that chapter -- never re-deriving accrual logic. Pure:
    never mutates ``story_doc``. Characters whose overlay is ``{}`` (no prior
    committed delta) are omitted, so an empty trail reproduces today's silence.

    The trail is expected to be SPARSE (FR-544 J1, sparse-is-truth): it carries only
    characters with committed ``character_state_deltas``, so a thin trail is a true
    measurement of thin deltas, not a bug. Visibility-not-gate: never fails the run.
    """
    chars = story_doc.get("characters") or {}
    cards = chars.get("cards") or {}
    roster = list(chars.get("roster") or [])
    order = list((story_doc.get("chapters") or {}).get("order") or [])
    total = 0
    by_chapter: list[dict] = []
    for cid in order:
        characters: list[dict] = []
        for char_id in roster:
            name = str((cards.get(char_id) or {}).get("name") or char_id).strip()
            overlay = derive_overlay(story_doc, cid, name)
            if not overlay:
                continue
            characters.append(
                {
                    "name": name,
                    "status": overlay["status"],
                    "history": overlay["history"],
                }
            )
        if characters:
            total += len(characters)
            by_chapter.append({"chapter": cid, "characters": characters})
    return {
        "transition_count": total,
        "by_chapter": by_chapter,
        "posture": "visibility-not-gate",
    }


def _load_story_doc(out_dir: Path) -> dict | None:
    """Load the session source-of-truth story doc, or ``None`` if absent.

    Prefers ``<out>/story/story.json`` (the per-session committed state) over the
    top-level export ``<out>/story.json``; returns ``None`` when neither exists so
    the seam-entrance block is simply omitted (non-fatal).
    """
    for candidate in (out_dir / "story" / "story.json", out_dir / "story.json"):
        if candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8"))
    return None


def write_witness(out_dir: Path) -> dict | None:
    """Read ``<out_dir>/review.md`` and write ``<out_dir>/continuity_witness.json``.

    Returns the witness dict, or ``None`` if no review exists yet (the caller treats a
    missing review as a skipped, non-fatal step). When the session story doc is
    present, an additive ``seam_entrance`` block (FR-538) is included.
    """
    review = out_dir / "review.md"
    if not review.exists():
        return None
    witness = build_witness(out_dir.name, review.read_text(encoding="utf-8"))
    story_doc = _load_story_doc(out_dir)
    if story_doc is not None:
        witness["seam_entrance"] = seam_entrance_summary(story_doc)
        witness["fact_reversal"] = fact_reversal_summary(story_doc)
        witness["overlay_trail"] = overlay_trail_summary(story_doc)
        witness["allegiance_transitions"] = allegiance_transitions(story_doc)
        # FR-553: deterministic turn-director prompt mass (the director's ACTUAL
        # scene size, recomputed offline -- never the 12k turn-graph total) and the
        # presence-at-failing-turn cross-reference (was the break's subject in the
        # opening scene?). Mass is omitted when tiktoken is absent; both are pure
        # visibility (never gate). presence_correlation reads the blocks set above.
        mass = prompt_mass_summary(story_doc)
        if mass is not None:
            witness["prompt_mass"] = mass
        witness["presence_correlation"] = presence_correlation(story_doc, witness)
    (out_dir / WITNESS_FILENAME).write_text(
        json.dumps(witness, indent=2) + "\n", encoding="utf-8"
    )
    return witness


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="FR-530 Stage 1 post-generation continuity witness"
    )
    parser.add_argument("--out", required=True, help="book output directory")
    args = parser.parse_args(argv)

    witness = write_witness(Path(args.out))
    if witness is None:
        print("continuity witness: no review.md found (skipped, non-blocking)")
        return 0
    seam = witness.get("seam_entrance") or {}
    seam_note = (
        f" seam_entrance={seam.get('gap_count', 0)} gaps"
        if "seam_entrance" in witness
        else ""
    )
    print(
        f"continuity witness: {witness['book']} "
        f"continuity={witness['continuity_score']}/5 "
        f"({witness['break_count']} breaks){seam_note} [visibility, not a gate]"
    )
    if "presence_correlation" in witness:
        print(format_prompt_salience_report(witness))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
