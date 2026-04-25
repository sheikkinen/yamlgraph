"""Schema definitions for baseline state."""

from typing import Any

from pydantic import BaseModel, Field


class BaselineSourceInfo(BaseModel):
    """Information about a baseline source file."""
    path: str = Field(description="Relative path to source file")
    hash: str = Field(description="SHA256 hash of file content")


class BaselineSummaryMeta(BaseModel):
    """Metadata for summarized content."""
    model: str = Field(description="Model used for summarization")
    prompt_version: str = Field(description="Version of summary prompt")
    summary_key: str = Field(description="Cache key for summary")


class BaselineState(BaseModel):
    """Complete baseline state schema."""
    baseline_id: str = Field(description="Unique baseline identifier")
    baseline_manifest_version: str = Field(description="Manifest version used")
    baseline_built_at: str = Field(description="ISO8601 timestamp of build")
    baseline_sources: list[BaselineSourceInfo] = Field(description="Source files information")
    baseline_context_verbatim: dict[str, str] = Field(description="Verbatim content by path")
    baseline_context_summaries: dict[str, str] = Field(description="Summarized content by path")
    baseline_summary_meta: dict[str, dict[str, Any]] = Field(description="Summary metadata by path")
    baseline_warnings: list[str] = Field(description="Warnings during baseline build")
