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

# Flaw codes grow per milestone, one per emitting check (FR-560 J4b: no code without an emitter).
# M1: monotonic-lifecycle + ungrounded-reveal. M2 (FR-561) adds open_condition -- the pure
# antecedent pre-check. M3 (FR-562) adds unclosed_affect -- the affect-closure debt check. The
# design S2 six-code set then lacks only unreachable/causal_threat, which stay planner-owned.
FlawCode = Literal[
    "open_condition",
    "lifecycle_violation",
    "ungrounded_reveal",
    "unclosed_affect",
]


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
    """Open or close one affect unit (Lehnert Plot Units). Closure is the M3 check (FR-562)."""

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
    # Global plan-length bound (sum of beat ``cost_turns``). ``None`` = unbounded, so the canonical
    # floodmark plan is untouched; set it to make capped reachability biteable (FR-561 check 5, J2).
    turn_budget: int | None = None
    # Affect units the author deliberately leaves open (tragic / unresolved endings). Default empty,
    # so a fully-resolved plan like floodmark is unaffected. Per-(char, kind), not a global flag: a
    # single boolean would exempt every open affect and gut the check (FR-562 M3, J1).
    intentional_open: list[tuple[CharacterId, AffectKind]] = Field(default_factory=list)


class PlanFlaw(BaseModel):
    """One narrative-invariant violation. ``code`` is the closed set (open_condition/lifecycle/ungrounded/unclosed_affect)."""

    code: FlawCode
    function_id: str
    detail: str


class ValidationResult(BaseModel):
    ok: bool
    flaws: list[PlanFlaw] = Field(default_factory=list)
