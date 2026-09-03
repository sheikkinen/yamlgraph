"""Pydantic models for structured LLM outputs.

This module contains FRAMEWORK models only - models used by the framework itself.
Demo-specific output schemas are defined inline in graph YAML files.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# Error Types
# =============================================================================


class ErrorType(StrEnum):
    """Types of errors that can occur in the pipeline."""

    LLM_ERROR = "llm_error"  # LLM API errors (rate limit, timeout, etc.)
    VALIDATION_ERROR = "validation_error"  # Pydantic validation failures
    PROMPT_ERROR = "prompt_error"  # Missing prompt, template errors
    STATE_ERROR = "state_error"  # Missing required state data
    VERIFICATION_ERROR = "verification_error"  # Verification gate violations (FR-164)
    GUARD_ERROR = "guard_error"  # Deterministic node guard violations (FR-344)
    TIMEOUT_ERROR = "timeout_error"  # Per-node execution timeout (FR-069)
    UNKNOWN_ERROR = "unknown_error"  # Catch-all


class PipelineError(BaseModel):
    """Structured error information for pipeline failures."""

    type: ErrorType = Field(description="Category of error")
    message: str = Field(description="Human-readable error message")
    node: str = Field(description="Node where error occurred")
    timestamp: datetime = Field(default_factory=datetime.now)
    retryable: bool = Field(
        default=False, description="Whether this error can be retried"
    )
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional error context"
    )

    @classmethod
    def from_exception(
        cls, e: Exception, node: str, error_type: ErrorType | None = None
    ) -> "PipelineError":
        """Create a PipelineError from an exception.

        Args:
            e: The exception that occurred
            node: Name of the node where error occurred
            error_type: Optional explicit error type

        Returns:
            PipelineError instance
        """
        # Infer error type from exception
        if error_type is None:
            exc_name = type(e).__name__.lower()
            if "rate" in exc_name or "timeout" in exc_name or "api" in exc_name:
                error_type = ErrorType.LLM_ERROR
                retryable = True
            elif "validation" in exc_name:
                error_type = ErrorType.VALIDATION_ERROR
                retryable = False
            elif "file" in exc_name or "prompt" in exc_name:
                error_type = ErrorType.PROMPT_ERROR
                retryable = False
            else:
                error_type = ErrorType.UNKNOWN_ERROR
                retryable = False
        else:
            retryable = error_type == ErrorType.LLM_ERROR

        return cls(
            type=error_type,
            message=str(e),
            node=node,
            retryable=retryable,
            details={"exception_type": type(e).__name__},
        )


class VerificationViolation(PipelineError):
    """A node's output violated its stated verification question (FR-164)."""

    prediction: str = Field(description="The original verification question")
    actual: str = Field(description="String repr of actual output")
    check_type: str = Field(
        description="Evaluator pattern: count_range | non_empty | contains | annotation"
    )


class GuardViolation(PipelineError):
    """A deterministic node guard check failed (FR-344)."""

    phase: Literal["pre", "post", "verify"] = Field(description="Guard phase")
    check: str = Field(description="Guard expression that failed")
    actual: str = Field(description="Actual evaluated guard result")
    on_fail: str = Field(description="Configured guard failure action")


# =============================================================================
# Generic Report Model (Flexible for Any Use Case)
# =============================================================================


class GenericReport(BaseModel):
    """Flexible report structure for any use case.

    Use this when you don't need a custom schema - works for most
    analysis and summary tasks. The LLM can populate any combination
    of the optional fields as needed.

    Example usage in graph YAML:
        nodes:
          analyze:
            type: llm
            prompt: my_analysis
            output_model: yamlgraph.models.GenericReport

    Example prompts can request specific sections:
        "Analyze the repository and provide:
         - A summary of findings
         - Key findings as bullet points
         - Recommendations for improvement"
    """

    title: str = Field(description="Report title")
    summary: str = Field(description="Executive summary")
    sections: dict[str, Any] = Field(
        default_factory=dict,
        description="Named sections with any content (strings, dicts, lists)",
    )
    findings: list[str] = Field(
        default_factory=list, description="Key findings or bullet points"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Suggested actions or areas to focus on"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional key-value data (author, version, tags, etc.)",
    )


# =============================================================================
# Copilot Node Result (REQ-YG-087)
# =============================================================================


class CopilotResult(BaseModel):
    """Structured result from copilot node execution.

    Wraps the unstructured text output from Copilot CLI or MCP sampling
    in a structured envelope with execution metadata.
    """

    output: str = Field(description="Raw Copilot response text")
    exit_code: int = Field(
        default=0, description="Process exit code (cli backend only)"
    )
    model: str | None = Field(default=None, description="Model used (if reported)")
    backend: str = Field(description="Execution backend: 'cli', 'api', or 'sampling'")
    session_id: str | None = Field(
        default=None,
        description="Copilot session ID for resumption (FR-105)",
    )


# Closed copilot backend set (FR-959 REQ-YG-640). Order is the order named in
# error messages; anything outside it fails before any subprocess.
COPILOT_BACKENDS: tuple[str, ...] = ("cli", "api", "sampling", "claude")

# Keys that only the claude backend understands; an error on cli/api backends.
CLAUDE_ONLY_CLI_FLAGS: tuple[str, ...] = ("tools", "allowed_tools", "max_turns")


class ClaudeCliFlags(BaseModel):
    """Typed ``cli_flags`` for ``backend: claude`` (FR-959 judgement R-4).

    Strict: ``"40"`` is not an int, ``True`` is not an int, ``1`` is not a
    bool. ``extra="forbid"``: a misspelled key is an error, never a silently
    dropped flag. Applied only when the backend is ``claude``; the Copilot and
    API backends keep their untyped dict (REQ-YG-087/356 unchanged).
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    model: str | None = None
    resume: str | None = None
    continue_session: bool = False
    tools: list[str] | None = Field(
        default=None,
        description="Tool AVAILABILITY (`--tools`); [] means no tools at all",
    )
    allowed_tools: list[str] | None = Field(
        default=None,
        description="Tool APPROVAL (`--allowedTools`); never restricts availability",
    )
    allow_all_tools: bool = False
    allow_all_paths: bool = False
    max_turns: int | None = Field(default=None, gt=0)
