"""The floodmark ``PlotPlan`` literal + falsification variants -- the belief-lane fixtures (FR-560).

Mirrors design-v3-plot-model-implementation.md S4. Belief-lane plans (FR-560):

* ``floodmark`` -- the canonical presumed-dead arc. World-truth ``alive(Arnulf)`` stays True; only
  the clan's *belief* flips to dead at F1 and is corrected at the Ch6 reveal. Solvable; grounded.
* ``early_reveal_variant`` -- adds a Ch3 beat that needs the clan to already believe Arnulf alive.
  The reveal that establishes that belief is at Ch6, so the Ch3 beat can never fire -> with the
  mandatory-step encoding the goal is unreachable -> provably unsolvable.
* ``world_revival_variant`` -- the 'death that un-happens' bug: F1 kills Arnulf in *world-truth*
  and the reveal revives him in *world-truth* (instead of correcting belief). The planner cannot
  see the contradiction; the monotonic-lifecycle check flags one ``lifecycle_violation``.
* ``ungrounded_reveal_variant`` -- F1 no longer opens the secret (its ``eff_belief`` is empty), yet
  Fr still reveals the clan's belief to alive. There is nothing to un-tell -> the grounding check
  flags one ``ungrounded_reveal``.

Both ``api/plot`` (report) and the test tree import these fixtures from here, so the canonical plan
has a single typed home (FR-560).

The causal-trio variants (FR-561 M2) live beside the canon: ``phantom_return_variant``
(open_condition, pure), ``overbudget_variant`` / ``budget_ok_variant`` (capped reachability via the
unary-counter), and ``threat_variant`` (forced-window threat, proven against the current encoding).
"""

from __future__ import annotations

from .schema import AffectDelta, Belief, Fluent, Function, PlotPlan

ARNULF, CLAN, HILDE = "Arnulf", "Clan", "Hilde"


def _alive(value: bool = True) -> Fluent:
    return Fluent(pred="alive", args=(ARNULF,), value=value)


def _clan_believes_alive(held: bool) -> Belief:
    return Belief(observer=CLAN, fluent=Fluent(pred="alive", args=(ARNULF,)), held=held)


# --- the canonical presumed-dead arc (solvable, grounded) ----------------------------------
floodmark = PlotPlan(
    agents=[ARNULF, HILDE],
    initial_world=[_alive(True)],
    initial_belief=[_clan_believes_alive(True)],
    goals=[_alive(True)],  # G: world-truth alive holds through the finale
    functions=[
        Function(
            id="F1",
            kind="villainy",
            subject=ARNULF,
            chapter=1,
            grain="turn",
            # WORLD-TRUTH STAYS ALIVE -- only belief flips. (The floodmark distinction.)
            eff_world=[],
            eff_belief=[_clan_believes_alive(False)],
            eff_affect=[AffectDelta(op="open", char=HILDE, kind="loss")],
        ),
        Function(
            id="Fr",
            kind="reveal",
            subject=ARNULF,
            chapter=6,
            observers=[CLAN],
            pre_belief=[_clan_believes_alive(False)],
            eff_belief=[_clan_believes_alive(True)],
            eff_affect=[
                AffectDelta(op="close", char=HILDE, kind="loss"),
                AffectDelta(op="open", char=HILDE, kind="guilt"),
            ],
        ),
        Function(
            id="Ff",
            kind="reconciliation",
            subject=HILDE,
            chapter=6,
            pre_belief=[_clan_believes_alive(True)],
            eff_affect=[AffectDelta(op="close", char=HILDE, kind="guilt")],
        ),
    ],
    order=[("F1", "Fr"), ("Fr", "Ff")],
)


# --- early-reveal variant (provably unsolvable) --------------------------------------------
# An "Arnulf onstage before the clan at Ch3" beat needs the clan to believe him alive -- a belief
# only established by Fr at Ch6. Mandatory-step encoding makes the goal unreachable.
early_reveal_variant = floodmark.model_copy(deep=True)
early_reveal_variant.functions.insert(
    2,
    Function(
        id="Fonstage",
        kind="return",
        subject=ARNULF,
        chapter=3,
        observers=[CLAN],
        pre_belief=[_clan_believes_alive(True)],
    ),
)
early_reveal_variant.order = [("F1", "Fonstage"), ("Fonstage", "Fr"), ("Fr", "Ff")]


# --- world-revival variant (one lifecycle_violation) ---------------------------------------
# F1 kills Arnulf in world-truth; Fr revives him in world-truth instead of correcting belief.
# Fr's belief effect is cleared so this stays a pure lifecycle case (no reveal to ground).
world_revival_variant = floodmark.model_copy(deep=True)
world_revival_variant.functions[0].eff_world = [_alive(False)]
world_revival_variant.functions[0].eff_belief = []
world_revival_variant.functions[1].eff_world = [_alive(True)]
world_revival_variant.functions[1].eff_belief = []


# --- ungrounded-reveal variant (one ungrounded_reveal) -------------------------------------
# F1 never opens the secret (no belief flip), yet Fr still reveals the clan's belief to alive.
# Nothing was told, so nothing can be un-told -- the grounding check flags it.
ungrounded_reveal_variant = floodmark.model_copy(deep=True)
ungrounded_reveal_variant.functions[0].eff_belief = []


# --- phantom-return variant (one open_condition, FR-561 M2) --------------------------------
# A Ch3 "return" beat needs Hilde to believe Arnulf alive -- but nobody ever opens that belief
# (initial_belief carries only the clan; F1 flips only the clan). The precondition has no producer
# and is not in I, so the pure antecedent check flags one open_condition. (Distinct from
# early-reveal, whose precondition IS in I -- that stays a temporal engine proof, J5.)
phantom_return_variant = floodmark.model_copy(deep=True)
phantom_return_variant.functions.append(
    Function(
        id="Fphantom",
        kind="return",
        subject=ARNULF,
        chapter=3,
        observers=[HILDE],
        pre_belief=[
            Belief(
                observer=HILDE, fluent=Fluent(pred="alive", args=(ARNULF,)), held=True
            )
        ],
    )
)
phantom_return_variant.order = [
    ("F1", "Fphantom"),
    ("Fphantom", "Fr"),
    ("Fr", "Ff"),
]


# --- budget variants (FR-561 M2 check 5) ---------------------------------------------------
# floodmark's three beats cost 1 turn each (sum = 3). With turn_budget=2 the unary-counter runs
# out before the last beat -> the mandatory done_ goal is unreachable -> PROVEN_UNSOLVABLE. With a
# sufficient turn_budget=3 the same plan still solves -- the counter only bites when exceeded.
overbudget_variant = floodmark.model_copy(deep=True)
overbudget_variant.turn_budget = 2

budget_ok_variant = floodmark.model_copy(deep=True)
budget_ok_variant.turn_budget = 3


# --- threat variant (forced-window, FR-561 M2 check 6) -------------------------------------
# Producer A (Ch1) sets holds(Ledger); threat B (Ch2) clears it; consumer C (Ch3) needs it. The
# chapter chain forces A->B->C, so by Ch3 the precondition is gone with no later producer and C's
# done_ goal is mandatory -> PROVEN_UNSOLVABLE against the *current* encoding (no build_problem
# change, J1). The pure antecedent check does NOT flag C: A is a producer (existence holds); the
# later clearing is a temporal fact only the planner owns.
LEDGER = "Ledger"


def _holds_ledger(value: bool) -> Fluent:
    return Fluent(pred="holds", args=(LEDGER,), value=value)


threat_variant = PlotPlan(
    agents=[ARNULF],
    initial_world=[_holds_ledger(False)],
    initial_belief=[],
    goals=[],
    functions=[
        Function(
            id="A",
            kind="villainy",
            subject=ARNULF,
            chapter=1,
            eff_world=[_holds_ledger(True)],
        ),
        Function(
            id="B",
            kind="villainy",
            subject=ARNULF,
            chapter=2,
            eff_world=[_holds_ledger(False)],
        ),
        Function(
            id="C",
            kind="return",
            subject=ARNULF,
            chapter=3,
            pre_world=[_holds_ledger(True)],
        ),
    ],
    order=[("A", "B"), ("B", "C")],
)


# --- dropped-confrontation variant (one unclosed_affect, FR-562 M3) -------------------------
# The canonical floodmark with the reconciliation beat's guilt-close removed, so the guilt opened
# at the reveal (Fr) is never discharged -> one unclosed_affect localized to Fr.
dropped_confrontation_variant = floodmark.model_copy(deep=True)
dropped_confrontation_variant.functions[2].eff_affect = []


# --- reopened-affect variant (J3 witness: ordered pop-walk, not Counter balance) -----------
# An early beat CLOSES loss(Hilde) (a harmless unmatched close) and a later beat REOPENS it. A
# net-zero +1/-1 count would wrongly pass; the ordered walk leaves the late open as residual debt
# localized to the reopening beat (Yopen).
reopened_affect_variant = PlotPlan(
    agents=[HILDE],
    functions=[
        Function(
            id="Xclose",
            kind="reconciliation",
            subject=HILDE,
            chapter=1,
            eff_affect=[AffectDelta(op="close", char=HILDE, kind="loss")],
        ),
        Function(
            id="Yopen",
            kind="villainy",
            subject=HILDE,
            chapter=2,
            eff_affect=[AffectDelta(op="open", char=HILDE, kind="loss")],
        ),
    ],
    order=[("Xclose", "Yopen")],
)


__all__ = [
    "budget_ok_variant",
    "dropped_confrontation_variant",
    "early_reveal_variant",
    "floodmark",
    "overbudget_variant",
    "phantom_return_variant",
    "reopened_affect_variant",
    "threat_variant",
    "ungrounded_reveal_variant",
    "world_revival_variant",
]
