"""FR-545 -- allegiance-transition ledger-fidelity witness (deterministic, no LLM).

The relationship ledger (``world_state.relationships``) is the system of record for
allegiance over time: an edge's stance reversal is recorded bi-temporally (FR-515) by
CLOSING the old edge (``valid_to`` stamped at the closing ordinal K) and OPENING a new
edge (``valid_from == K``). This witness reads those stamps from the FINAL committed
ledger -- which carries the entire history, since closed edges are never dropped unless
ungrounded (``world_state.parse_world_state``) -- and reports each recorded stance
reversal between roster pairs.

**What it measures (C4 -- read this before trusting a low number):** *grounded
op-emission*, NOT break correctness. It cannot tell a correct recorded transition from a
hallucinated-but-grounded one, and it CANNOT see the *unrecorded* prose flips that are the
actual defect -- those leave the ledger static, so there is nothing to read. On a book the
LLM reviewer flags for many allegiance breaks, a near-zero ``transition_count`` is the
fidelity gap made visible (the writer is not recording the flips), never an all-clear.
The witness is a regression gauge for the chapter-close fidelity instruction and a
complement to the reviewer's localization, not a replacement.

**Scope:** named pairwise edges only. Character-grain authority/role resets (one
character's role, no edge to diff) and collective allegiance (a group is not a roster
name) are out of scope and remain the LLM reviewer's domain.

Posture (FR-522): visibility-not-gate. Nothing here ever fails a run or CI.
"""

from __future__ import annotations

from examples.dungeon_master.api.world_state import _norm_token, _rel_key

# Frozen stance buckets (no widening -- regex_fourth_exclusion): a relationship type
# maps to a stance pole, and a transition is a reversal only when the two poles are an
# OPPOSED pair. Buckets, not enumerated type pairs, so enmity->romantic_bond (negative
# -> positive) and romantic_bond->estranged (positive -> negative, a cooling) are both
# caught without listing every type combination.
_POSITIVE_STANCE = frozenset(
    {"alliance", "romantic_bond", "friendship", "ally", "bond", "loyalty"}
)
_NEGATIVE_STANCE = frozenset(
    {"enmity", "estranged", "rivalry", "feud", "enemy", "betrayal"}
)
_COMMAND_STANCE = frozenset({"command", "commands", "leads", "authority_over"})
_SUBORDINATE_STANCE = frozenset({"subordinate", "follows", "serves", "under"})

# The only stance-pole pairs that count as a reversal (frozen).
_OPPOSED_POLES = frozenset(
    {
        frozenset({"positive", "negative"}),
        frozenset({"command", "subordinate"}),
    }
)


def _stance(rel_type: object) -> str:
    """Map a relationship type to its frozen stance pole, or ``""`` if unclassified."""
    token = _norm_token(rel_type)
    if token in _POSITIVE_STANCE:
        return "positive"
    if token in _NEGATIVE_STANCE:
        return "negative"
    if token in _COMMAND_STANCE:
        return "command"
    if token in _SUBORDINATE_STANCE:
        return "subordinate"
    return ""


def _is_reversal(from_type: object, to_type: object) -> bool:
    """True when the two types cross an opposed stance-pole pair."""
    from_pole = _stance(from_type)
    to_pole = _stance(to_type)
    if not from_pole or not to_pole:
        return False
    return frozenset({from_pole, to_pole}) in _OPPOSED_POLES


def _roster_name_set(doc: dict) -> set[str]:
    """Normalized display names of the reviewed roster (the roster lens)."""
    chars = doc.get("characters") or {}
    cards = chars.get("cards") or {}
    names: set[str] = set()
    for char_id in chars.get("roster") or []:
        name = (cards.get(char_id) or {}).get("name") or char_id
        names.add(_norm_token(name))
    return names


def _is_grounded(edge: dict) -> bool:
    return bool([c for c in edge.get("recap_citations") or [] if str(c).strip()])


def allegiance_transitions(doc: dict) -> dict:
    """Recorded stance reversals between roster pairs, read from the final ledger.

    Reads the final chapter's committed ``world_state.relationships``, groups edges by
    the type-independent :func:`world_state._rel_key`, and reports each pair that has a
    CLOSED edge (``valid_to == K``) reconciled into a NEW edge (``valid_from == K``)
    whose type crosses a frozen opposed stance-pole pair. ``K`` (the closing ordinal)
    localizes the transition to a chapter.

    Returns ``{"transition_count", "ungrounded_count", "by_pair": [{"between", "from",
    "to", "at_chapter", "grounded"}], "posture"}``. ``transition_count`` counts only
    GROUNDED reversals (the trustworthy signal); ``ungrounded_count`` counts reversals
    whose new edge carries no recap citation. Pure; never mutates ``doc``.
    """
    chapters = doc.get("chapters") or {}
    order = list(chapters.get("order") or [])
    cards = chapters.get("cards") or {}
    roster = _roster_name_set(doc)

    by_pair: list[dict] = []
    grounded_count = 0
    ungrounded_count = 0

    if order:
        final = order[-1]
        rels = ((cards.get(final) or {}).get("world_state") or {}).get(
            "relationships"
        ) or []
        edges_by_key: dict[tuple[str, ...], list[dict]] = {}
        for rel in rels:
            edges_by_key.setdefault(_rel_key(rel), []).append(rel)

        for key, edges in edges_by_key.items():
            if not key or not all(name in roster for name in key):
                continue
            for closed in (e for e in edges if e.get("valid_to") is not None):
                ordinal = closed.get("valid_to")
                for new in edges:
                    if new is closed or new.get("valid_from") != ordinal:
                        continue
                    if not _is_reversal(closed.get("type"), new.get("type")):
                        continue
                    grounded = _is_grounded(new)
                    by_pair.append(
                        {
                            "between": list(key),
                            "from": str(closed.get("type") or "").strip(),
                            "to": str(new.get("type") or "").strip(),
                            "at_chapter": ordinal,
                            "grounded": grounded,
                        }
                    )
                    if grounded:
                        grounded_count += 1
                    else:
                        ungrounded_count += 1

    by_pair.sort(key=lambda p: (p["at_chapter"], p["between"]))
    return {
        "transition_count": grounded_count,
        "ungrounded_count": ungrounded_count,
        "by_pair": by_pair,
        "posture": "visibility-not-gate",
    }
