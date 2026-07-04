"""Pydantic schemas for guard, verification, and cache configuration.

Extracted from graph_schema.py (FR-674) to keep modules under the 450-line ceiling.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

VALID_ON_FAIL = {"warn", "halt", "retry"}


class CacheConfig(BaseModel):
    """Configuration for per-node result caching (FR-032).

    Maps to LangGraph CachePolicy on graph.add_node().
    """

    ttl: int | None = Field(
        default=None,
        ge=1,
        description="Time-to-live in seconds (None = cache forever)",
    )


class VerificationConfig(BaseModel):
    """Configuration for a node's verification gate (FR-164)."""

    question: str = Field(
        ..., description="Falsifiable prediction about the node's output"
    )
    on_fail: str = Field(
        default="warn",
        description="Action when prediction is violated: warn | halt | retry",
    )
    max_retries: int = Field(
        default=1,
        ge=1,
        description="Max retry attempts when on_fail: retry",
    )

    @field_validator("on_fail")
    @classmethod
    def validate_on_fail(cls, v: str) -> str:
        """Validate on_fail is a known action."""
        if v not in VALID_ON_FAIL:
            valid = ", ".join(sorted(VALID_ON_FAIL))
            raise ValueError(f"Invalid on_fail '{v}'. Valid: {valid}")
        return v


class GuardRuleBase(BaseModel):
    """Base schema for deterministic guard rules (FR-344)."""

    check: str = Field(..., description="Deterministic guard expression")
    message: str | None = Field(
        default=None,
        description="Optional human-readable failure message",
    )

    model_config = {"extra": "forbid"}


class PreGuardRule(GuardRuleBase):
    """Pre-execution guard rule."""

    on_fail: Literal["warn", "halt", "skip"] = Field(
        ..., description="Pre-guard action: warn | halt | skip"
    )


class PostGuardRule(GuardRuleBase):
    """Post-execution guard rule."""

    on_fail: Literal["warn", "halt", "retry"] = Field(
        ..., description="Post-guard action: warn | halt | retry"
    )
    max_retries: int | None = Field(
        default=None,
        ge=1,
        description="Retry budget for post guards with on_fail=retry (default 1)",
    )

    @model_validator(mode="after")
    def validate_retry_fields(self) -> "PostGuardRule":
        """Allow max_retries only with on_fail=retry, defaulting to 1."""
        if self.on_fail == "retry":
            if self.max_retries is None:
                self.max_retries = 1
            return self
        if self.max_retries is not None:
            raise ValueError(
                "max_retries is only valid for post guards with on_fail=retry"
            )
        return self


class GuardConfig(BaseModel):
    """Per-node deterministic guard configuration."""

    pre: list[PreGuardRule] = Field(
        default_factory=list,
        description="Pre-execution deterministic guards",
    )
    post: list[PostGuardRule] = Field(
        default_factory=list,
        description="Post-execution deterministic guards",
    )

    model_config = {"extra": "forbid"}


class GraphVerifyRule(GuardRuleBase):
    """Graph-level terminal verification rule (FR-677).

    Evaluated once against final state after the graph reaches its terminal
    node, before END. Unlike post guards there is no retry — a graph run is
    already complete, so the only meaningful actions are warn (record and
    continue) or halt (raise).
    """

    on_fail: Literal["warn", "halt"] = Field(
        ..., description="Graph verify action: warn | halt"
    )
