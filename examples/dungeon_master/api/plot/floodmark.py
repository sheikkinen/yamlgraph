"""The floodmark ``PlotPlan`` literal + falsification variants -- the belief-lane fixtures (FR-560).

Mirrors design-v3-plot-model-implementation.md S4. Four plans:

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


__all__ = [
    "early_reveal_variant",
    "floodmark",
    "ungrounded_reveal_variant",
    "world_revival_variant",
]
