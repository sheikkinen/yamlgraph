"""LangGraph State Definitions.

Defines typed state schemas for different graph types.
Uses generic Any types for demo-specific outputs, allowing
any Pydantic model from inline YAML schemas.
"""

from datetime import datetime
from operator import add
from typing import Annotated, Any, TypedDict

from showcase.models.schemas import PipelineError


# =============================================================================
# Base State - Common fields for all graphs
# =============================================================================


class BaseState(TypedDict, total=False):
    """Common fields for all graphs.

    Provides shared functionality like error tracking and timestamps.
    """

    thread_id: str
    current_step: str
    error: PipelineError | None
    errors: list[PipelineError]
    started_at: datetime | None
    completed_at: datetime | None


# =============================================================================
# Specialized States
# =============================================================================


class ContentState(BaseState, total=False):
    """State for content generation pipeline.

    Used by: graphs/showcase.yaml

    Fields:
        generated: Output from generate node (typically has title, content, word_count, tags)
        analysis: Output from analyze node (typically has summary, key_points, sentiment, confidence)
    """

    topic: str
    style: str
    word_count: int
    generated: Any  # Dynamic Pydantic model from inline schema
    analysis: Any  # Dynamic Pydantic model from inline schema
    final_summary: str | None


class RouterState(BaseState, total=False):
    """State for router demo.

    Used by: graphs/router-demo.yaml

    Fields:
        classification: Output from classify node (typically has tone, confidence, reasoning)
    """

    message: str
    classification: Any  # Dynamic Pydantic model from inline schema
    response: str | None
    _route: str | None


class ReflexionState(BaseState, total=False):
    """State for self-correction loops.

    Used by: graphs/reflexion-demo.yaml

    Fields:
        current_draft: Output from draft/refine nodes (typically has content, version)
        critique: Output from critique node (typically has score, feedback, should_refine)
    """

    topic: str
    current_draft: Any  # Dynamic Pydantic model from inline schema
    critique: Any  # Dynamic Pydantic model from inline schema
    _loop_counts: dict[str, int]
    _loop_limit_reached: bool


class AgentState(BaseState, total=False):
    """State for agent with tool use.

    Used by: graphs/git-report.yaml, graphs/memory-demo.yaml

    Note: messages uses Annotated with add reducer for accumulation.
    """

    input: str
    messages: Annotated[list, add]  # Accumulates across iterations
    response: str | None  # Agent's final response (state_key target)
    analysis: str | None
    report: Any  # Dynamic Pydantic model from inline schema
    _tool_results: list[dict] | None  # Raw tool outputs
    _agent_iterations: int
    _agent_limit_reached: bool


# =============================================================================
# Backward Compatibility
# =============================================================================


# Alias for backward compatibility - existing code uses ShowcaseState
ShowcaseState = ContentState


def create_initial_state(
    topic: str,
    style: str = "informative",
    word_count: int = 300,
    thread_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Create an initial state for a new pipeline run.

    Args:
        topic: The topic to generate content about
        style: Writing style (default: informative)
        word_count: Target word count (default: 300)
        thread_id: Optional thread ID (auto-generated if not provided)
        **kwargs: Additional state fields

    Returns:
        Initialized state dictionary
    """
    import uuid

    return {
        "thread_id": thread_id or uuid.uuid4().hex[:16],
        "topic": topic,
        "style": style,
        "word_count": word_count,
        "current_step": "init",
        "error": None,
        "errors": [],
        "started_at": datetime.now(),
        "completed_at": None,
        **kwargs,
    }
