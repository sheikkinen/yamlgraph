"""Close-boundary ledger exit reconciliation for DM v2 (FR-542 Part A).

The chapter-close graph derives the end-of-chapter ``world_state`` ledger from the
prose alone, so it can miss a director-reported ``cast_exit`` -- the 10029-BC
"Arnulf swept away yet logged alive at the bank" seam, where a swept-away actor is
committed present and surfaces as an unstaged resurrection chapters later. This
module normalizes at the boundary the bad row enters: it reconciles the emitted
ledger against the exits the director actually reported, before the next chapter
inherits it.

Interim fix (continuity-projection-plan.md step 2), superseded by the write-once
projected lifecycle ledger (step 3). Split out of ``chapter_ops`` (FR-536 concern
seam): the reconciliation is a pure, roster-bounded, no-LLM ledger transform with
no dependency on the close graph, so it lives as a leaf beside the other ledger
primitives. The generic, novel ``fact_reversal_gap`` (FR-542 Part B) is its
visibility-only sibling in ``fact_reversal``.
"""

from __future__ import annotations

import logging

from examples.dungeon_master.api.lifecycle_resolver import _norm_name

_LOG = logging.getLogger(__name__)

# Status substrings that already record a character's exit/loss (FR-542 A): a
# ledger row bearing one needs no reconciliation -- the close graph already caught
# the exit. Kept a closed, literal set (not free-text NLP); matched case-folded.
_ABSENCE_STATUS_TOKENS = (
    "dead",
    "died",
    "dies",
    "deceased",
    "killed",
    "slain",
    "perished",
    "drowned",
    "swept",
    "lost",
    "gone",
    "missing",
    "absent",
    "departed",
    "vanished",
)

# The canonical correction a reconciled exit writes when the close graph left an
# exited actor reading present. Truthful without fabricating a cause (the
# director's ``cast_exits`` carries only the name): the actor left the scene.
_RECONCILED_EXIT_STATUS = "absent -- exited the scene this chapter"


def _status_marks_absence(status: object) -> bool:
    """True when a ledger status already records an exit/loss (FR-542 A)."""
    low = str(status or "").lower()
    return any(token in low for token in _ABSENCE_STATUS_TOKENS)


def reconcile_ledger_exits(world_ledger: dict, exits: list[str]) -> dict:
    """Correct character rows the director benched that the close graph kept present.

    The close graph derives end-of-chapter ``world_state`` from the prose alone and
    can miss a director-reported ``cast_exit`` -- the 10029-BC "Arnulf swept away
    yet logged alive at the bank" seam, where the contradiction enters at the close
    boundary and surfaces as an unstaged resurrection chapters later. This
    normalizes at the boundary the bad row enters: any exited character whose status
    does not already read as absent/lost is marked absent. Pure, roster-bounded
    (only names the director benched), no LLM; returns a new ledger and never
    mutates the input (FR-542 A).
    """
    exit_keys = {_norm_name(name) for name in exits if str(name).strip()}
    if not exit_keys:
        return world_ledger
    out = dict(world_ledger)
    reconciled: list[dict] = []
    for character in world_ledger.get("characters") or []:
        record = dict(character)
        if _norm_name(record.get("name")) in exit_keys and not _status_marks_absence(
            record.get("status")
        ):
            _LOG.warning(
                "Reconciled ledger exit: %s",
                {
                    "name": record.get("name"),
                    "was": str(record.get("status") or "").strip(),
                    "now": _RECONCILED_EXIT_STATUS,
                },
            )
            record["status"] = _RECONCILED_EXIT_STATUS
        reconciled.append(record)
    out["characters"] = reconciled
    return out
