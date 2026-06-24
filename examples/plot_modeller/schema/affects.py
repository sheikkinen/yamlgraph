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
