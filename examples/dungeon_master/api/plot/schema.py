"""Typed plot-model contract for DM v3 -- the graduated belief lane (FR-560 M1).

Graduated from the FR-559 floodmark spike. This is now **THE contract** the projection,
grounding, and live exclusion seam import (design-v3-plot-model-implementation.md S2), not a
throwaway subset. The schema grows per milestone: M1 carries only the fields and flaw codes the
belief lane needs (lifecycle + ungrounded-reveal). Affect-closure, capped reachability, and the
full six-code ``PlanFlaw`` Literal are M3/M4.

A1 architecture note (FR-560 J4): this package is a **leaf**. It may be imported *by* the v2
chapter-open seam (``chapter_open -> api.plot``), but must never import ``chapter_open``,
``turn_ops``, or ``seam_entrance`` -- that reverse edge would couple the typed contract to v2 and
break the island. ``api/plot/`` is outside import-linter's ``root_package = yamlgraph`` scope, so
the leaf direction is doctrine enforced by review + the file-size and ``ruff`` gates, not by
``lint-imports``.
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

# M1 carries only the flaw codes its checks emit (FR-560 J4b): the monotonic-lifecycle invariant
# and the ungrounded-reveal grounding check. The full design S2 six-code Literal grows per milestone.
FlawCode = Literal["lifecycle_violation", "ungrounded_reveal"]


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
    """Open or close one affect unit (Lehnert Plot Units). Carried; closure is an M3 check."""

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
    """One narrative-invariant violation. ``code`` is the M1 closed set (lifecycle/ungrounded)."""

    code: FlawCode
    function_id: str
    detail: str


class ValidationResult(BaseModel):
    ok: bool
    flaws: list[PlanFlaw] = Field(default_factory=list)
