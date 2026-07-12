"""A2A message parsing, error mapping, and Agent Card generation.

FR-208 / CAP-81: A2A Protocol Server
(REQ-YG-208, REQ-YG-209, REQ-YG-213)

Extracted from a2a_server.py to keep module sizes under 450 lines.
"""

from __future__ import annotations

import json
import shlex
from typing import Any

try:
    from a2a.types import (
        AgentCapabilities,
        AgentCard,
        AgentSkill,
        InternalError,
        InvalidParamsError,
        Part,
    )
except ImportError as exc:
    raise ImportError(
        "A2A SDK not installed. Install with: pip install yamlgraph[a2a]"
    ) from exc

from yamlgraph.models import ErrorType, PipelineError

# ---------------------------------------------------------------------------
# REQ-YG-209: Message parsing strategy
# ---------------------------------------------------------------------------


def extract_text_from_parts(parts: list[Part]) -> str:
    """Extract and concatenate text from A2A message parts.

    Multiple TextPart entries are joined with newlines.
    If no TextPart is found, raises ValueError.

    Args:
        parts: List of A2A Part objects.

    Returns:
        Concatenated text content.

    Raises:
        ValueError: If no text parts found (unsupported_content_type).
    """
    texts: list[str] = []
    for part in parts:
        if part.WhichOneof("content") == "text":
            texts.append(part.text)

    if not texts:
        raise ValueError("unsupported_content_type: message contains no text parts")

    return "\n".join(texts)


def parse_a2a_message(
    text: str,
    required_vars: list[str],
) -> dict[str, str]:
    """Parse A2A message text into graph input variables.

    Resolution order:
    1. JSON object → parse as dict
    2. Contains '=' → key_value mode (shlex.split)
    3. Exactly one required var → single_input mode
    4. Fallback → assign to 'input' key

    Args:
        text: Raw text from A2A message.
        required_vars: List of required variable names from graph state.

    Returns:
        Dict of variable name → value.

    Raises:
        ValueError: If required variables are missing (missing_variables).
    """
    variables: dict[str, str] = {}

    # 1. Try JSON
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            variables = {
                k: str(v) if not isinstance(v, str) else v for k, v in parsed.items()
            }
            _validate_required_vars(variables, required_vars)
            return variables
    except (json.JSONDecodeError, ValueError):
        pass

    # 2. Try key=value (if text contains '=')
    if "=" in text:
        try:
            tokens = shlex.split(text)
            kv_pairs: dict[str, str] = {}
            for token in tokens:
                if "=" in token:
                    key, _, value = token.partition("=")
                    if key:
                        kv_pairs[key] = value
            if kv_pairs:
                variables = kv_pairs
                _validate_required_vars(variables, required_vars)
                return variables
        except ValueError:
            pass

    # 3. Single required var → assign entire text
    if len(required_vars) == 1:
        variables = {required_vars[0]: text}
        return variables

    # 4. Fallback → assign to 'input'
    variables = {"input": text}
    _validate_required_vars(variables, required_vars)
    return variables


def _validate_required_vars(
    variables: dict[str, str],
    required_vars: list[str],
) -> None:
    """Validate all required variables are present.

    Raises:
        ValueError: With code 'missing_variables' listing missing keys.
    """
    missing = [v for v in required_vars if v not in variables]
    if missing:
        raise ValueError(f"missing_variables: {', '.join(missing)}")


# ---------------------------------------------------------------------------
# REQ-YG-209: PipelineError → A2A error mapping
# ---------------------------------------------------------------------------

# Maps PipelineError.type to A2A error class
_ERROR_TYPE_MAP: dict[ErrorType, type] = {
    ErrorType.LLM_ERROR: InternalError,
    ErrorType.STATE_ERROR: InternalError,
    ErrorType.UNKNOWN_ERROR: InternalError,
    ErrorType.VALIDATION_ERROR: InvalidParamsError,
    ErrorType.PROMPT_ERROR: InvalidParamsError,
    ErrorType.VERIFICATION_ERROR: InvalidParamsError,
}


def map_pipeline_error(err: PipelineError) -> InternalError | InvalidParamsError:
    """Map a PipelineError to an A2A error type.

    Args:
        err: YAMLGraph PipelineError instance.

    Returns:
        A2A error instance (InternalError or InvalidParamsError).
    """
    error_cls = _ERROR_TYPE_MAP.get(err.type, InternalError)
    return error_cls(
        message=err.message,
        data={
            "node": err.node,
            "retryable": err.retryable,
            "error_type": err.type.value,
            **err.details,
        },
    )


# ---------------------------------------------------------------------------
# REQ-YG-208: Agent Card generation
# ---------------------------------------------------------------------------


def build_agent_card(
    graphs: list[dict[str, Any]],
    host: str = "localhost",
    port: int = 8080,
    version: str = "0.4.63",
) -> AgentCard:
    """Build an A2A Agent Card from discovered graphs.

    Each graph becomes a skill in the Agent Card.

    Args:
        graphs: List of discovered graph info dicts.
        host: Server hostname.
        port: Server port.
        version: Agent version string.

    Returns:
        A2A AgentCard instance.
    """
    skills = [
        AgentSkill(
            id=g["name"],
            name=g["name"],
            description=g.get("description", ""),
            tags=["yamlgraph"],
        )
        for g in graphs
    ]

    return AgentCard(
        name="YAMLGraph A2A Server",
        description="YAMLGraph graphs exposed as A2A agents",
        version=version,
        skills=skills,
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
    )


# ---------------------------------------------------------------------------
# REQ-YG-213: Interrupt detection
# ---------------------------------------------------------------------------


def _detect_interrupt(result: dict[str, Any]) -> bool:
    """Detect if graph result indicates an interrupt (input-required).

    LangGraph sets ``__interrupt__`` in state when a node with
    ``interrupt_before`` / ``interrupt_after`` triggers.

    Args:
        result: Graph invocation result dict.

    Returns:
        True if the result contains an interrupt marker.
    """
    return "__interrupt__" in result


def _extract_interrupt_payload(result: dict[str, Any]) -> str | None:
    """Extract the interrupt payload from a graph result.

    FR-250 / REQ-YG-213: Forward the interrupt value (the question/prompt)
    to the A2A client so it knows *what* to answer.

    Args:
        result: Graph invocation result dict containing ``__interrupt__``.

    Returns:
        String representation of the interrupt payload, or None if
        no interrupt or no payload.
    """
    interrupts = result.get("__interrupt__")
    if not interrupts:
        return None
    first = interrupts[0]
    # LangGraph Interrupt objects have a .value attribute
    value = getattr(first, "value", None)
    if value is None and isinstance(first, dict):
        value = first.get("value")
    return str(value) if value is not None else None
