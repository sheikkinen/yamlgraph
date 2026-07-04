"""Async LLM Factory - Async versions of LLM creation.

This module provides async-compatible LLM creation with support for
non-blocking I/O operations in async contexts.

Note: This module is a foundation for future async support. Currently,
LangChain's LLM implementations use sync HTTP clients internally, so
this wraps them for use in async contexts via run_in_executor.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import TypeVar

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from pydantic import BaseModel

from yamlgraph.config import MAX_RETRIES, RETRY_BASE_DELAY, RETRY_MAX_DELAY
from yamlgraph.executor_base import attempt_structured_invoke, is_retryable
from yamlgraph.utils.llm_factory import ProviderType, create_llm

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Shared executor for running sync LLM calls
_executor: ThreadPoolExecutor | None = None


def get_executor() -> ThreadPoolExecutor:
    """Get or create the shared thread pool executor."""
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=4)
    return _executor


async def create_llm_async(
    provider: ProviderType | None = None,
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int | None = None,
) -> BaseChatModel:
    """Create an LLM instance asynchronously.

    Currently wraps the sync create_llm. Future versions may use
    native async LLM implementations.

    Args:
        provider: LLM provider ("anthropic", "mistral", "openai")
        model: Model name
        temperature: Temperature for generation
        max_tokens: Maximum output tokens. None means provider default.

    Returns:
        Configured LLM instance
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        get_executor(),
        partial(
            create_llm,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        ),
    )


async def invoke_async(
    llm: BaseChatModel,
    messages: list[BaseMessage],
    output_model: type[T] | None = None,
    max_retries: int = MAX_RETRIES,
) -> T | str:
    """Invoke LLM asynchronously with retry and structured-output fallback.

    Runs the sync invoke in a thread pool to avoid blocking.
    Mirrors sync executor retry semantics (FR-676):
    - Exponential backoff on retryable errors (asyncio.sleep between attempts)
    - FR-464 structured-output fallback when provider rejects response_format

    Args:
        llm: The LLM instance
        messages: Messages to send
        output_model: Optional Pydantic model for structured output
        max_retries: Maximum retry attempts (default from config)

    Returns:
        LLM response (parsed model or string)
    """
    loop = asyncio.get_running_loop()
    last_exception = None

    for attempt in range(max_retries):
        try:

            def sync_invoke() -> T | str:
                return attempt_structured_invoke(llm, messages, output_model)

            return await loop.run_in_executor(get_executor(), sync_invoke)

        except Exception as e:
            last_exception = e

            if not is_retryable(e) or attempt == max_retries - 1:
                raise

            delay = min(RETRY_BASE_DELAY * (2**attempt), RETRY_MAX_DELAY)
            logger.warning(
                f"Async LLM call failed (attempt {attempt + 1}/{max_retries}): {e}. "
                f"Retrying in {delay:.1f}s..."
            )
            await asyncio.sleep(delay)

    raise last_exception


def shutdown_executor() -> None:
    """Shutdown the thread pool executor.

    Call this during application shutdown to clean up resources.
    """
    global _executor
    if _executor is not None:
        _executor.shutdown(wait=True)
        _executor = None


__all__ = ["create_llm_async", "invoke_async", "shutdown_executor"]
