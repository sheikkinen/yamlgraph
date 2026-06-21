"""Throwaway Pydantic subset of the v3 plot schema -- FR-559 spike ONLY.

THIS IS NOT THE PRODUCTION CONTRACT (J4). The real typed island is the eventual
``api/plot/schema.py`` (design-v3-plot-model-implementation.md S2). This module is a minimal
subset built to make the M0 falsification spike runnable; it is **not imported by DM v2** and
must not be treated as the API. Adding fields here proves nothing about the production schema.

Subset scope: just enough of ``PlotPlan`` / ``Function`` / ``Fluent`` / ``Belief`` /
``AffectDelta`` to (a) compile belief-as-fluent into a ``unified-planning`` problem and (b) run
the hand-written monotonic-lifecycle check. Affect / belief-grounding / capped-reachability are
production M1+ concerns, intentionally absent.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

CharacterId = str

# Closed Propp-like alphabet (subset of design S2 -- only the kinds the floodmark fixtures use).
FunctionKind = Literal[
    "villainy",
    "reveal",
    "reconciliation",
    "return",
]
WorldPred = Literal["alive", "at", "faction", "rel", "holds"]
AffectKind = Literal["loss", "guilt"]
Grain = Literal["book", "chapter", "turn"]


class Fluent(BaseModel):
    """One world-truth atom. ``value`` is bool for alive/holds, str for at/faction/rel."""

    pred: WorldPred
    args: tuple[str, ...]
    value: bool | str = True

    def key(self) -> tuple[WorldPred, tuple[str, ...]]:
        return (self.pred, self.args)


class Belief(BaseModel):
    """Per-observer belief about a Fluent. ``held=False`` means believes-NOT."""

    observer: CharacterId
    fluent: Fluent
    held: bool = True


class AffectDelta(BaseModel):
    """Open or close one affect unit (Lehnert Plot Units). Carried but not checked in M0."""

    op: Literal["open", "close"]
    char: CharacterId
    kind: AffectKind


class Function(BaseModel):
    """One authored beat. Finite alphabet; grounded roles; typed pre/effects."""

    id: str
    kind: FunctionKind
    subject: CharacterId
    target: str | None = None
    observers: list[CharacterId] = Field(default_factory=list)
    chapter: int
    grain: Grain = "chapter"
    cost_turns: int = 1

    pre_world: list[Fluent] = Field(default_factory=list)
    pre_belief: list[Belief] = Field(default_factory=list)

    eff_world: list[Fluent] = Field(default_factory=list)
    eff_belief: list[Belief] = Field(default_factory=list)
    eff_affect: list[AffectDelta] = Field(default_factory=list)


class PlotPlan(BaseModel):
    """<I, A, G, F, E> -- the whole authored plot."""

    initial_world: list[Fluent] = Field(default_factory=list)
    initial_belief: list[Belief] = Field(default_factory=list)
    agents: list[CharacterId] = Field(default_factory=list)
    goals: list[Fluent] = Field(default_factory=list)
    functions: list[Function] = Field(default_factory=list)
    order: list[tuple[str, str]] = Field(default_factory=list)


class PlanFlaw(BaseModel):
    code: Literal["lifecycle_violation"]
    function_id: str
    detail: str


class ValidationResult(BaseModel):
    ok: bool
    flaws: list[PlanFlaw] = Field(default_factory=list)
