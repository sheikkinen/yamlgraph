"""Baseline manifest models and validation for FR-277 Watcher2 Baseline Checkpointing.

This module provides Pydantic models for baseline manifest schema validation
and helper functions for manifest validation.
"""

from typing import Literal

from pydantic import BaseModel, Field


class BaselineSource(BaseModel):
    """Source pattern specification for baseline manifest."""

    pattern: str = Field(description="Glob pattern for source files")
    mode: Literal["verbatim", "summarized"] = Field(
        description="Content processing mode"
    )


class BaselineManifest(BaseModel):
    """Baseline manifest schema validation."""

    manifest_version: int = Field(description="Manifest schema version")
    sources: list[BaselineSource] = Field(description="List of source patterns")
    exclude: list[str] | None = Field(
        default_factory=list, description="List of exclusion patterns"
    )


def validate_manifest_schema(manifest_data: dict) -> BaselineManifest:
    """Validate manifest data against schema.

    Args:
        manifest_data: Raw manifest dictionary

    Returns:
        Validated BaselineManifest instance

    Raises:
        ValidationError: If manifest data is invalid
    """
    return BaselineManifest(**manifest_data)
