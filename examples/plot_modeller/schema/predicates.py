"""FR-571 — World-state predicates and beliefs with typed ``held``."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Fluent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pred: str
    args: list[str]
    value: bool | str = True


class Belief(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observer: str
    fluent: Fluent
    held: bool | str
