"""Executor Base - Shared utilities for sync and async prompt execution.

Provides common functions for prompt loading, formatting, and message building.
"""

import logging
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from yamlgraph.utils.prompts import load_prompt
from yamlgraph.utils.template import validate_variables

logger = logging.getLogger(__name__)

# Exceptions that are retryable
RETRYABLE_EXCEPTIONS = (
    "RateLimitError",
    "APIConnectionError",
    "APITimeoutError",
    "InternalServerError",
    "ServiceUnavailableError",
)


def is_retryable(exception: Exception) -> bool:
    """Check if an exception is retryable.

    Args:
        exception: The exception to check

    Returns:
        True if the exception should be retried
    """
    exc_name = type(exception).__name__
    return exc_name in RETRYABLE_EXCEPTIONS or "rate" in exc_name.lower()


def format_prompt(
    template: str,
    variables: dict,
    state: dict | None = None,
) -> str:
    """Format a prompt template with variables.

    Supports both simple {variable} placeholders and Jinja2 templates.
    If the template contains Jinja2 syntax ({%, {{), uses Jinja2 rendering.

    Args:
        template: Template string with {variable} or Jinja2 placeholders
        variables: Dictionary of variable values
        state: Optional state dict for Jinja2 templates (accessible as {{ state.field }})

    Returns:
        Formatted string

    Examples:
        Simple format:
            format_prompt("Hello {name}", {"name": "World"})

        Jinja2 with variables:
            format_prompt("{% for item in items %}{{ item }}{% endfor %}", {"items": [1, 2]})

        Jinja2 with state:
            format_prompt("Topic: {{ state.topic }}", {}, state={"topic": "AI"})
    """
    # Check for Jinja2 syntax
    if "{%" in template or "{{" in template:
        from jinja2 import Template

        jinja_template = Template(template)
        # Pass both variables and state to Jinja2
        context = {"state": state or {}, **variables}
        return jinja_template.render(**context)

    # Fall back to simple format - stringify lists for compatibility
    safe_vars = {
        k: (", ".join(map(str, v)) if isinstance(v, list) else v)
        for k, v in variables.items()
    }
    return template.format(**safe_vars)


def prepare_messages(  # noqa: C901
    prompt_name: str,
    variables: dict | None = None,
    provider: str | None = None,
    model: str | None = None,
    graph_path: Path | None = None,
    prompts_dir: Path | None = None,
    prompts_relative: bool = False,
    state: dict | None = None,
) -> tuple[list, str | None, str | None]:
    """Load prompt, validate, format, and build messages.

    Shared logic for sync and async executors.

    Args:
        prompt_name: Name of the prompt file (without .yaml)
        variables: Variables to substitute in the template
        provider: LLM provider override (None to use YAML/env default)
        model: LLM model override (None to use YAML/env default)
        graph_path: Path to graph file for relative prompt resolution
        prompts_dir: Explicit prompts directory override
        prompts_relative: If True, resolve prompts relative to graph_path
        state: Optional state dict for Jinja2 templates (accessible as {{ state.field }})

    Returns:
        Tuple of (messages list, resolved provider, resolved model)

    Raises:
        ValueError: If required template variables are missing
    """
    variables = variables or {}

    prompt_config = load_prompt(
        prompt_name,
        prompts_dir=prompts_dir,
        graph_path=graph_path,
        prompts_relative=prompts_relative,
    )

    # Handle system field conflicts - both system and system_segments not allowed
    has_system = "system" in prompt_config and prompt_config["system"]
    has_system_segments = "system_segments" in prompt_config

    if has_system and has_system_segments:
        raise ValueError(
            f"Cannot specify both 'system' and 'system_segments' fields in prompt '{prompt_name}'"
        )

    # Build full template for variable validation
    system_template = ""
    if has_system_segments:
        # Extract content from all segments for validation
        segments = prompt_config["system_segments"]
        for segment in segments:
            system_template += segment.get("content", "")
    elif has_system:
        system_field = prompt_config["system"]
        # Handle both scalar string and list format for system field
        if isinstance(system_field, list):
            # List format: [{"content": "text", "cache": bool}, ...]
            for item in system_field:
                if isinstance(item, dict):
                    system_template += item.get("content", "")
                else:
                    system_template += str(item)
        else:
            system_template = system_field

    full_template = system_template + prompt_config.get("user", "")
    validate_variables(full_template, variables, prompt_name)

    # Extract provider and model from YAML if not provided via parameter
    resolved_provider = provider
    if resolved_provider is None:
        resolved_provider = prompt_config.get("provider")
        if resolved_provider:
            logger.debug(f"Using provider from YAML: {resolved_provider}")

    resolved_model = model
    if resolved_model is None:
        resolved_model = prompt_config.get("model")
        if resolved_model:
            logger.debug(f"Using model from YAML: {resolved_model}")

    # Build system message
    user_text = format_prompt(prompt_config["user"], variables, state=state)

    messages = []

    # Handle system_segments (takes precedence over system)
    if has_system_segments:
        segments = prompt_config["system_segments"]

        # Check for empty segments
        if not segments:
            # Create empty SystemMessage for consistency
            messages.append(SystemMessage(content=""))
        else:
            system_msg = _build_system_message_from_segments(
                segments, variables, state, resolved_provider
            )
            if system_msg:
                messages.append(system_msg)

    # Handle scalar or list system field
    elif has_system:
        system_field = prompt_config["system"]

        if isinstance(system_field, list):
            # Treat list format as segments
            segments = []
            for item in system_field:
                if isinstance(item, dict):
                    segments.append(item)
                else:
                    # Convert bare string to segment
                    segments.append({"content": str(item), "cache": False})

            system_msg = _build_system_message_from_segments(
                segments, variables, state, resolved_provider
            )
            if system_msg:
                messages.append(system_msg)
        else:
            # Traditional scalar system prompt
            system_text = format_prompt(system_field, variables, state=state)
            if system_text:
                messages.append(SystemMessage(content=system_text))

    messages.append(HumanMessage(content=user_text))

    return messages, resolved_provider, resolved_model


def _build_system_message_from_segments(
    segments: list[dict],
    variables: dict,
    state: dict | None,
    provider: str | None,
) -> SystemMessage | None:
    """Build SystemMessage from system_segments.

    For Anthropic provider: create message with cache_control blocks
    For other providers: flatten to single content string

    Args:
        segments: List of segment dicts with 'content' and optional 'cache'
        variables: Template variables
        state: Optional state for Jinja2 templates
        provider: LLM provider name

    Returns:
        SystemMessage or None if all segments are empty
    """
    if not segments:
        return None

    # Process all segment content with variable substitution
    processed_segments = []
    for segment in segments:
        content = segment.get("content", "")
        cache = segment.get("cache", False)  # Default cache to False

        if content:
            formatted_content = format_prompt(content, variables, state=state)
            processed_segments.append({"content": formatted_content, "cache": cache})

    if not processed_segments:
        return None

    # For Anthropic provider, use content blocks with cache_control
    if provider == "anthropic":
        content_blocks = []
        for segment in processed_segments:
            block = {
                "type": "text",
                "text": segment["content"]
            }
            if segment["cache"]:
                block["cache_control"] = {"type": "ephemeral"}
            content_blocks.append(block)

        # Create SystemMessage with content blocks in additional_kwargs
        return SystemMessage(
            content="",  # Empty content, actual content in additional_kwargs
            additional_kwargs={"content": content_blocks}
        )

    # For non-Anthropic providers, flatten to single string
    combined_content = "\n".join(segment["content"] for segment in processed_segments)
    return SystemMessage(content=combined_content)
