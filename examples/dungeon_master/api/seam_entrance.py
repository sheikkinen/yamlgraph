"""Seam-entrance continuity witness for DM v2 (FR-538).

The mirror of :func:`gap_detectors.seam_precondition_gap`'s exit edge. That witness
catches an actor *removed* across a seam with no bridge; this one catches an actor
*introduced* across a seam with no arrival: a character who ACTS in a chapter's
final-cut prose but was neither on-page in the previous chapter nor staged arriving
in this one — the 10028-BC "Arnulf appears in Ch3, never present in Ch2" defect that
FR-537's clean cast-scoping exposed.

The gating signal is PROSE establishment — an arrival/reposition token-run near the
entrant in the chapter's own ``text`` — never a manifest lookup (FR-538 Judgement
B1): a name FR-539 lists in ``cast_entrances`` but does not narrate still counts as
a gap. A recorded turn intent only separates *acted* from merely *mentioned* among
the names already present in the prose (R1); it is not an independent membership
test.

A leaf over :mod:`chapter_nav`, :mod:`turn_state`, and :mod:`lifecycle_resolver`;
pure — no LLM, no ``turn_ops``. The word-bounded name matcher mirrors
``chapter_open._name_tokens`` (FR-537) rather than importing it, so this witness
stays below the chapter-open gate layer instead of depending up into it.
"""

from __future__ import annotations

import re

from examples.dungeon_master.api import chapter_nav
from examples.dungeon_master.api.lifecycle_resolver import _norm_name
from examples.dungeon_master.api.turn_state import chapter_turns

# Arrival tokens that stage an entrant's on-page appearance — the prose bridge an
# introduced character needs. When one occurs near the entrant's name in the
# chapter's own text, the entrance is ESTABLISHED (not a gap).
#
# LEXICON HYGIENE (FR-543): this set must contain ONLY unambiguous ARRIVAL verbs.
# It must NEVER re-borrow gap_detectors._REPOSITION_TOKENS — the EXIT-edge,
# movement-toward-hazard vocabulary (slips, loses footing, into the water, down the
# bank, goes back, back for). Those describe an actor moving toward death/departure;
# enlisting them as arrival signals let a later death-fall sentence ("Arnulf slid
# off the ledge and dropped into the water") clear an unbridged entrance (10030-BC
# Ch3 false negative). A fall/exit is not an arrival.
_ESTABLISH_TOKENS = (
    "arrives",
    "arrived",
    "arriving",
    "appears",
    "appeared",
    "appearing",
    "enters",
    "entered",
    "entering",
    "strode",
    "strides",
    "stepped",
    "steps",
    "comes",
    "came",
    "rode in",
    "rides in",
    "rode into",
    "rides into",
    "rejoins",
    "rejoined",
    "returns",
    "returned",
    "emerges",
    "emerged",
    "approaches",
    "approached",
    "reaches",
    "reached",
    "joins",
    "joined",
    "climbs",
    "climbed",
    "rushes in",
    "marches in",
    "marched",
    "walked in",
    "came up",
    "made his way",
    "made her way",
)

_NAME_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _name_tokens(text: str) -> list[str]:
    """Lowercased alphanumeric word tokens of ``text`` (for word-bounded matching).

    Mirrors ``chapter_open._name_tokens`` (FR-537); duplicated rather than imported
    to keep this witness below the chapter-open gate layer (no upward dependency).
    """
    return _NAME_TOKEN_RE.findall(str(text or "").lower())


def _contains_token_run(haystack: list[str], needle: list[str]) -> bool:
    """True when ``needle`` appears as a contiguous run of tokens in ``haystack``.

    Word-bounded: a roster name matches only as whole words (``Ron`` does not match
    inside ``around``); a multi-word name matches an exact contiguous run.
    """
    if not needle or len(needle) > len(haystack):
        return False
    span = len(needle)
    return any(
        haystack[i : i + span] == needle for i in range(len(haystack) - span + 1)
    )


def _name_has_arrival_signal(text: str, name: str, window: int = 60) -> bool:
    """Whether an establish-token sits within ``window`` chars of ``name`` in ``text``.

    Proximity, not whole-text: a single arrival line for the entrant resolves the
    gap, but an arrival word elsewhere about another character must not. ``name`` is
    already known present as a word-bounded token-run (membership is gated upstream),
    so a substring scan here is a safe proximity probe.
    """
    low = (text or "").lower()
    needle = name.lower()
    start = 0
    while True:
        i = low.find(needle, start)
        if i == -1:
            return False
        ctx = low[max(0, i - window) : i + len(needle) + window]
        if any(tok in ctx for tok in _ESTABLISH_TOKENS):
            return True
        start = i + len(needle)


def seam_entrance_gap(story_doc: dict, cid: str) -> dict:
    """Detect characters who act in chapter ``cid`` with no on-page arrival (FR-538).

    Returns ``{chapter, acting_count, gap_count, gaps:[{name, kind,
    last_on_page_chapter, established}]}`` where ``established`` is the prose arrival
    signal (the gating term, NOT a manifest lookup — B1). ``kind`` is derived from
    prior on-page history and the inherited ``character_lifecycle``:

    - **new** — never on-page in any prior chapter (a genuine newcomer).
    - **returning** — has an inherited ``character_lifecycle`` record (an absence
      the seam packet tracked).
    - **continuing** — on-page in some earlier chapter, scoped out of the immediate
      prior chapter, back now.

    Pure: reads final-cut ``text`` + turn intents + inherited seam packet; no LLM,
    no ``turn_ops``.
    """
    chapters = story_doc.get("chapters") or {}
    order = list(chapters.get("order") or [])
    chars = story_doc.get("characters") or {}
    cards = chars.get("cards") or {}

    # roster as (char_id, display_name, normalized_name, name_tokens)
    roster: list[tuple[str, str, str, list[str]]] = []
    for char_id in chars.get("roster") or []:
        name = str((cards.get(char_id) or {}).get("name") or char_id).strip()
        if name:
            roster.append((char_id, name, _norm_name(name), _name_tokens(name)))

    cid_text = str(chapter_nav.chapter_card(story_doc, cid).get("text") or "")
    cid_tokens = _name_tokens(cid_text)

    # char_ids that recorded an intent in cid — the "acted" gate (R1): only an
    # acting name (not a merely-mentioned one) can cross a seam.
    acted_ids: set[str] = set()
    for turn in chapter_turns(story_doc, cid):
        acted_ids.update((turn.get("intents") or {}).keys())

    acting = [
        (name, norm)
        for (char_id, name, norm, ntok) in roster
        if char_id in acted_ids and _contains_token_run(cid_tokens, ntok)
    ]

    prev = chapter_nav.previous_chapter_id(story_doc, cid)
    if prev is None:  # first chapter: no prior, no entrances
        return {
            "chapter": str(cid),
            "acting_count": len(acting),
            "gap_count": 0,
            "gaps": [],
        }

    # last prior chapter each roster name was on-page (token-run in that text).
    try:
        cid_index = order.index(cid)
    except ValueError:
        cid_index = len(order)
    last_on_page: dict[str, str] = {}
    for pcid in order[:cid_index]:
        ptokens = _name_tokens(
            str(chapter_nav.chapter_card(story_doc, pcid).get("text") or "")
        )
        for _char_id, _name, norm, ntok in roster:
            if _contains_token_run(ptokens, ntok):
                last_on_page[norm] = str(pcid)

    on_page_prev = {norm for norm, c in last_on_page.items() if c == str(prev)}

    lifecycle = chapter_nav.inherited_seam_packet(story_doc, cid).get(
        "character_lifecycle"
    )
    lifecycle_names = {
        _norm_name(str(e.get("name") or ""))
        for e in (lifecycle or [])
        if isinstance(e, dict) and e.get("name")
    }

    gaps: list[dict] = []
    for name, norm in acting:
        if norm in on_page_prev:  # continuation, not an entrance
            continue
        if _name_has_arrival_signal(cid_text, name):  # arrival staged in prose (B1)
            continue
        if norm not in last_on_page:
            kind = "new"
        elif norm in lifecycle_names:
            kind = "returning"
        else:
            kind = "continuing"
        gaps.append(
            {
                "name": name,
                "kind": kind,
                "last_on_page_chapter": last_on_page.get(norm),
                "established": False,
            }
        )

    return {
        "chapter": str(cid),
        "acting_count": len(acting),
        "gap_count": len(gaps),
        "gaps": gaps,
    }
