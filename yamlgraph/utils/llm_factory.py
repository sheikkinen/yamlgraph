"""LLM Factory - Multi-provider abstraction for language models.

This module provides a simple factory pattern for creating LLM instances
across different providers (Anthropic, Azure, Mistral, OpenAI, Replicate, etc.).

Provider-specific creation functions live in ``llm_providers.py``.
"""

import logging
import os
import threading
from typing import Literal

from langchain_core.language_models.chat_models import BaseChatModel

from yamlgraph.config import DEFAULT_MODELS
from yamlgraph.utils.llm_providers import dispatch_provider

logger = logging.getLogger(__name__)

# Type alias for supported providers
ProviderType = Literal[
    "anthropic",
    "azure",
    "deepseek",
    "google",
    "inception",
    "lmstudio",
    "mistral",
    "openai",
    "replicate",
    "vertex",
    "xai",
]

# Providers that support thinking_budget natively
THINKING_PROVIDERS = {"anthropic", "google", "vertex"}

# OpenAI reasoning models that reject the temperature parameter (FR-455)
REASONING_MODEL_PREFIXES = ("o1", "o3", "o4")


_llm_cache: dict[tuple, BaseChatModel] = {}
_cache_lock = threading.Lock()


def create_llm(
    provider: ProviderType | None = None,
    model: str | None = None,
    temperature: float | None = 0.7,
    max_tokens: int | None = None,
    thinking_budget: int | None = None,
) -> BaseChatModel:
    """Create an LLM instance with multi-provider support.

    Supports Anthropic (default), Azure, DeepSeek, Google, Mistral, OpenAI, Replicate, and xAI providers.
    Provider can be specified via parameter or PROVIDER environment variable.
    Model can be specified via parameter or {PROVIDER}_MODEL environment variable.

    LLM instances are cached by (provider, model, temperature, max_tokens, thinking_budget)
    to improve performance.

    Args:
        provider: LLM provider ("anthropic", "deepseek", "mistral", "openai", "replicate", "xai").
                 Defaults to PROVIDER env var or "anthropic".
        model: Model name. Defaults to {PROVIDER}_MODEL env var or provider default.
        temperature: Temperature for generation (0.0-1.0).
        max_tokens: Maximum output tokens. None means provider default.
        thinking_budget: Extended thinking budget tokens. Supported by anthropic, google, and
                        vertex providers (FR-071, FR-230). For Anthropic: 0 or ≥1024, forces
                        temperature=1. For Google/Vertex: any non-negative integer or -1 for
                        automatic mode; temperature is not overridden.

    Returns:
        Configured LLM instance.

    Raises:
        ValueError: If provider is invalid or thinking_budget used with non-Anthropic.

    Examples:
        >>> # Use default Anthropic
        >>> llm = create_llm(temperature=0.7)

        >>> # Override provider
        >>> llm = create_llm(provider="mistral", temperature=0.8)

        >>> # Custom model
        >>> llm = create_llm(provider="openai", model="gpt-4o-mini")

        >>> # Use xAI Grok
        >>> llm = create_llm(provider="xai", model="grok-beta")

        >>> # Enable extended thinking
        >>> llm = create_llm(provider="anthropic", thinking_budget=8000)
    """
    # Determine provider (parameter > env var > default)
    selected_provider = provider or os.getenv("PROVIDER") or "anthropic"

    # Validate provider
    if selected_provider not in DEFAULT_MODELS:
        raise ValueError(
            f"Invalid provider: {selected_provider}. "
            f"Must be one of: {', '.join(DEFAULT_MODELS.keys())}"
        )

    # Validate thinking_budget is only used with supported providers
    if (
        thinking_budget is not None
        and thinking_budget >= 1024
        and selected_provider not in THINKING_PROVIDERS
    ):
        raise ValueError(
            f"thinking_budget is only supported for providers: {', '.join(sorted(THINKING_PROVIDERS))}, "
            f"got provider='{selected_provider}'"
        )

    # Ensure temperature has a value (some providers reject None)
    if temperature is None:
        temperature = 0.7

    # Track if we override temperature for warning
    temperature_overridden = False
    original_temperature = temperature

    # Override temperature to 1 if thinking is enabled (Anthropic requirement)
    if (
        thinking_budget is not None
        and thinking_budget >= 1024
        and selected_provider == "anthropic"
        and temperature != 1
    ):
        temperature_overridden = True
        original_temperature = temperature
        temperature = 1

    # Determine model (parameter > env var > default)
    # Note: DEFAULT_MODELS already handles env var via config.py
    selected_model = model or DEFAULT_MODELS[selected_provider]

    # Omit temperature for OpenAI reasoning models (FR-455)
    if (
        selected_provider == "openai"
        and any(selected_model.startswith(p) for p in REASONING_MODEL_PREFIXES)
        and temperature is not None
    ):
        logger.info(f"Omitting temperature for reasoning model: {selected_model}")
        temperature = None

    # Create cache key (includes thinking_budget, uses overridden temperature)
    cache_key = (
        selected_provider,
        selected_model,
        temperature,
        max_tokens,
        thinking_budget,
    )

    # Thread-safe cache access
    with _cache_lock:
        # Return cached instance if available
        if cache_key in _llm_cache:
            logger.debug(
                f"Using cached LLM: {selected_provider}/{selected_model} (temp={temperature})"
            )
            return _llm_cache[cache_key]

        # Create new LLM instance
        logger.info(
            f"Creating LLM: {selected_provider}/{selected_model} (temp={temperature})"
        )

        # Build optional kwargs (only include max_tokens if set)
        optional_kwargs: dict[str, object] = {}
        if max_tokens is not None:
            optional_kwargs["max_tokens"] = max_tokens

        # Dispatch to provider-specific creation
        llm = dispatch_provider(
            selected_provider,
            selected_model,
            temperature,
            thinking_budget,
            **optional_kwargs,
        )

        # Cache the instance
        _llm_cache[cache_key] = llm

        # Emit warning after caching if temperature was overridden
        if temperature_overridden:
            logger.warning(
                f"Temperature overridden from {original_temperature} to 1.0 "
                f"(required for extended thinking with budget={thinking_budget})"
            )

        return llm


def clear_cache() -> None:
    """Clear the LLM instance cache.

    Useful for testing or when you want to force recreation of LLM instances.
    """
    with _cache_lock:
        _llm_cache.clear()
    logger.debug("LLM cache cleared")
