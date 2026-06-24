"""FR-571 — PlotPlan: the top-level plan model."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .functions import Function
from .predicates import Belief, Fluent


class AffectPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    unclosed_is_error: bool = True
    partial_goal_failure: bool = False


class PlanMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = ""
    genre: str = ""
    synopsis: str = ""


class PlotPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meta: PlanMeta = PlanMeta()
    agents: list[str] = []
    initial_world: list[Fluent] = []
    initial_belief: list[Belief] = []
    goals: list[Fluent] = []
    functions: list[Function] = []
    affect_policy: AffectPolicy = AffectPolicy()
