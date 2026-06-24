"""FR-571 — Function model (one authored beat)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .affects import AffectDelta
from .kinds import FunctionKind
from .predicates import Belief, Fluent


class Motivation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent: str
    goal: str


class Function(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    kind: FunctionKind
    gloss: str = ""
    subject: str = ""
    roles: dict[str, str] = {}
    chapter: int = 1
    observers: list[str] = []
    motivation: Motivation | None = None
    threatens: Motivation | None = None
    enables: list[str] = []
    pre_world: list[Fluent] = []
    eff_world: list[Fluent] = []
    pre_belief: list[Belief] = []
    eff_belief: list[Belief] = []
    eff_affect: list[AffectDelta] = []
