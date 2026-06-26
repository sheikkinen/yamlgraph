"""FR-571 — 6 affect kinds with relational ``toward``."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict


class AffectKind(str, Enum):
    loss = "loss"
    guilt = "guilt"
    betrayal = "betrayal"
    retaliation = "retaliation"
    hidden_blessing = "hidden_blessing"
    hope = "hope"


class AffectDelta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    op: Literal["open", "close"]
    char: str
    kind: AffectKind
    toward: str | None = None
    # FR-607: the goal (a motivation.goal/threatens.goal name) this feeling is an
    # appraisal of. Optional — present on enriched ground truth and goal-anchored
    # predictions, absent on the frozen-gate two-pass path.
    referent: str | None = None
