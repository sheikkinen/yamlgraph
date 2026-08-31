"""YAML Prompt Executor - Unified interface for LLM calls.

This module provides a simple, reusable executor for YAML-defined prompts
with support for structured outputs via Pydantic models.
"""

import logging
import threading
import time
from pathlib import Path
from typing import TypeVar

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from yamlgraph.config import (
    DEFAULT_TEMPERATURE,
    MAX_RETRIES,
    RETRY_BASE_DELAY,
    RETRY_MAX_DELAY,
)
from yamlgraph.executor_base import (
    PromptRequest,
    attempt_structured_invoke,
    format_prompt,
    is_retryable,
    prepare_messages,
)
from yamlgraph.utils.llm_factory import create_llm

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

__all__ = [
    "execute_prompt",
    "format_prompt",
    "get_executor",
    "PromptExecutor",
    "PromptRequest",
]


def execute_prompt(
    prompt_name: str,
    variables: dict | None = None,
    output_model: type[T] | None = None,
    temperature: float = DEFAULT_TEMPERATURE,
    provider: str | None = None,
    model: str | None = None,
    graph_path: "Path | None" = None,
    prompts_dir: "Path | None" = None,
    prompts_relative: bool = False,
    state: dict | None = None,
    max_tokens: int | None = None,
    thinking_budget: int | None = None,
    retry_feedback: str | None = None,
) -> T | str:
    """Execute a YAML prompt with optional structured output.

    Public front door — thin constructor over PromptRequest (FR-715);
    the parameter contract is documented ONCE on the dataclass and
    signature parity is witnessed by tests. Uses the singleton
    PromptExecutor for LLM caching.

    Example:
        >>> result = execute_prompt(
        ...     "greet",
        ...     variables={"name": "World", "style": "formal"},
        ...     output_model=GenericReport,
        ... )
        >>> print(result.summary)
    """
    return get_executor().execute(
        PromptRequest(
            prompt_name=prompt_name,
            variables=variables,
            output_model=output_model,
            temperature=temperature,
            provider=provider,
            model=model,
            graph_path=graph_path,
            prompts_dir=prompts_dir,
            prompts_relative=prompts_relative,
            state=state,
            max_tokens=max_tokens,
            thinking_budget=thinking_budget,
            retry_feedback=retry_feedback,
        )
    )


# Default executor instance for LLM caching
# Use get_executor() to access, or set_executor() for dependency injection
_executor: "PromptExecutor | None" = None
_executor_lock = threading.Lock()


def get_executor() -> "PromptExecutor":
    """Get the executor instance (thread-safe).

    Returns the default singleton or a custom instance set via set_executor().

    Returns:
        PromptExecutor instance with LLM caching
    """
    global _executor
    if _executor is None:
        with _executor_lock:
            # Double-check after acquiring lock
            if _executor is None:
                _executor = PromptExecutor()
    return _executor


class PromptExecutor:
    """Reusable executor with LLM caching and retry logic."""

    def __init__(self, max_retries: int = MAX_RETRIES):
        self._max_retries = max_retries

    def _get_llm(
        self,
        temperature: float = DEFAULT_TEMPERATURE,
        provider: str | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        thinking_budget: int | None = None,
    ) -> BaseChatModel:
        """Get or create cached LLM instance.

        Uses llm_factory which handles caching internally.
        """
        return create_llm(
            temperature=temperature,
            provider=provider,
            model=model,
            max_tokens=max_tokens,
            thinking_budget=thinking_budget,
        )

    def _invoke_with_retry(
        self, llm, messages, output_model: type[T] | None = None
    ) -> T | str:
        """Invoke LLM with exponential backoff retry.

        Args:
            llm: The LLM instance to use
            messages: Messages to send
            output_model: Optional Pydantic model for structured output

        Returns:
            LLM response (parsed model or string)

        Raises:
            Last exception if all retries fail
        """
        last_exception = None

        for attempt in range(self._max_retries):
            try:
                return attempt_structured_invoke(llm, messages, output_model)
            except Exception as e:
                last_exception = e

                if not is_retryable(e) or attempt == self._max_retries - 1:
                    raise

                # Exponential backoff with jitter
                delay = min(RETRY_BASE_DELAY * (2**attempt), RETRY_MAX_DELAY)
                logger.warning(
                    f"LLM call failed (attempt {attempt + 1}/{self._max_retries}): {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)

        raise last_exception

    def execute(self, request: PromptRequest) -> T | str:
        """Execute a PromptRequest using cached LLM with retry logic.

        The parameter contract lives on PromptRequest (FR-715).
        Model/provider priority: request > prompt YAML metadata > env
        var > default.

        Raises:
            ValueError: If required template variables are missing
        """
        messages, resolved_provider, resolved_model = prepare_messages(
            prompt_name=request.prompt_name,
            variables=request.variables,
            provider=request.provider,
            model=request.model,
            graph_path=request.graph_path,
            prompts_dir=request.prompts_dir,
            prompts_relative=request.prompts_relative,
            state=request.state,
        )

        if request.retry_feedback:
            messages.append(HumanMessage(content=request.retry_feedback))

        llm = self._get_llm(
            temperature=request.temperature,
            provider=resolved_provider,
            model=resolved_model,
            max_tokens=request.max_tokens,
            thinking_budget=request.thinking_budget,
        )

        return self._invoke_with_retry(llm, messages, request.output_model)
