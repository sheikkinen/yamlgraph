"""The floodmark ``PlotPlan`` literal + two falsification variants -- FR-559 spike fixtures.

Mirrors design-v3-plot-model-implementation.md S4. Three plans:

* ``floodmark`` -- the canonical presumed-dead arc. World-truth ``alive(Arnulf)`` stays True; only
  the clan's *belief* flips to dead at F1 and is corrected at the Ch6 reveal. Solvable.
* ``early_reveal_variant`` -- adds a Ch3 beat that needs the clan to already believe Arnulf alive.
  The reveal that establishes that belief is at Ch6, so the Ch3 beat can never fire -> with the
  mandatory-step encoding (J2) the goal is unreachable -> provably unsolvable.
* ``world_revival_variant`` -- the 'death that un-happens' bug: F1 kills Arnulf in *world-truth*
  and the reveal revives him in *world-truth* (instead of correcting belief). The planner cannot
  see the contradiction; the hand-written monotonic-lifecycle check flags one
  ``lifecycle_violation``.
"""

from __future__ import annotations

from .schema import AffectDelta, Belief, Fluent, Function, PlotPlan

ARNULF, CLAN, HILDE = "Arnulf", "Clan", "Hilde"


def _alive(value: bool = True) -> Fluent:
    return Fluent(pred="alive", args=(ARNULF,), value=value)


def _clan_believes_alive(held: bool) -> Belief:
    return Belief(observer=CLAN, fluent=Fluent(pred="alive", args=(ARNULF,)), held=held)


# --- the canonical presumed-dead arc (solvable) --------------------------------------------
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
world_revival_variant = floodmark.model_copy(deep=True)
world_revival_variant.functions[0].eff_world = [_alive(False)]
world_revival_variant.functions[0].eff_belief = []
world_revival_variant.functions[1].eff_world = [_alive(True)]


__all__ = ["early_reveal_variant", "floodmark", "world_revival_variant"]
