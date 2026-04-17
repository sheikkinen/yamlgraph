"""LLM Factory - Multi-provider abstraction for language models.

This module provides a simple factory pattern for creating LLM instances
across different providers (Anthropic, Mistral, OpenAI, Replicate).
"""

import logging
import os
import threading
from contextlib import contextmanager
from typing import Literal

from langchain_core.language_models.chat_models import BaseChatModel

from yamlgraph.config import DEFAULT_MODELS

logger = logging.getLogger(__name__)

# Type alias for supported providers
ProviderType = Literal[
    "anthropic",
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


_llm_cache: dict[tuple, BaseChatModel] = {}
_cache_lock = threading.Lock()

# Serialises Vertex Express construction so env-var masking is race-free
_VERTEX_CONSTRUCT_LOCK = threading.Lock()


@contextmanager
def _masked_env(*keys: str):  # type: ignore[return]
    """Temporarily remove *keys* from os.environ, restoring them on exit."""
    saved = {k: os.environ.pop(k) for k in keys if k in os.environ}
    try:
        yield
    finally:
        os.environ.update(saved)


# --- Provider-specific helper functions ---


def _create_deepseek_llm(
    model: str, temperature: float, **kwargs: object
) -> BaseChatModel:
    """Create DeepSeek LLM (OpenAI-compatible API)."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        base_url="https://api.deepseek.com/v1",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        **kwargs,
    )


def _create_google_llm(
    model: str, temperature: float, thinking_budget: int | None = None, **kwargs: object
) -> BaseChatModel:
    """Create Google Generative AI LLM."""
    from langchain_google_genai import ChatGoogleGenerativeAI

    google_kwargs = dict(kwargs)
    if thinking_budget is not None:
        google_kwargs["thinking_budget"] = thinking_budget
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        **google_kwargs,
    )


def _create_inception_llm(
    model: str, temperature: float, **kwargs: object
) -> BaseChatModel:
    """Create Inception Labs Mercury LLM."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        base_url="https://api.inceptionlabs.ai/v1",
        api_key=os.getenv("INCEPTION_API_KEY"),
        **kwargs,
    )


def _create_mistral_llm(
    model: str, temperature: float, **kwargs: object
) -> BaseChatModel:
    """Create Mistral AI LLM."""
    from langchain_mistralai import ChatMistralAI

    return ChatMistralAI(model=model, temperature=temperature, **kwargs)


def _create_openai_llm(
    model: str, temperature: float, **kwargs: object
) -> BaseChatModel:
    """Create OpenAI LLM."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=model, temperature=temperature, **kwargs)


def _create_xai_llm(model: str, temperature: float, **kwargs: object) -> BaseChatModel:
    """Create xAI Grok LLM."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        base_url="https://api.x.ai/v1",
        api_key=os.getenv("XAI_API_KEY"),
        **kwargs,
    )


def _create_lmstudio_llm(
    model: str, temperature: float, **kwargs: object
) -> BaseChatModel:
    """Create LM Studio local LLM."""
    from langchain_openai import ChatOpenAI

    base_url = os.getenv("LMSTUDIO_BASE_URL") or "http://localhost:1234/v1"
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        base_url=base_url,
        api_key="not-needed",
        **kwargs,
    )


def _create_anthropic_llm(
    model: str, temperature: float, thinking_budget: int | None = None, **kwargs: object
) -> BaseChatModel:
    """Create Anthropic Claude LLM."""
    from langchain_anthropic import ChatAnthropic

    anthropic_kwargs = dict(kwargs)
    if thinking_budget is not None and thinking_budget >= 1024:
        anthropic_kwargs["thinking"] = {
            "type": "enabled",
            "budget_tokens": thinking_budget,
        }

    return ChatAnthropic(model=model, temperature=temperature, **anthropic_kwargs)


def _dispatch_provider(
    provider: str,
    model: str,
    temperature: float,
    thinking_budget: int | None,
    **kwargs: object,
) -> BaseChatModel:
    """Dispatch to appropriate provider-specific creation function."""
    if provider == "deepseek":
        return _create_deepseek_llm(model, temperature, **kwargs)
    if provider == "google":
        return _create_google_llm(model, temperature, thinking_budget, **kwargs)
    if provider == "inception":
        return _create_inception_llm(model, temperature, **kwargs)
    if provider == "mistral":
        return _create_mistral_llm(model, temperature, **kwargs)
    if provider == "openai":
        return _create_openai_llm(model, temperature, **kwargs)
    if provider == "replicate":
        return _create_replicate_llm(model, temperature, **kwargs)
    if provider == "vertex":
        return _create_vertex_llm(model, temperature, thinking_budget, **kwargs)
    if provider == "xai":
        return _create_xai_llm(model, temperature, **kwargs)
    if provider == "lmstudio":
        return _create_lmstudio_llm(model, temperature, **kwargs)
    # Default: anthropic
    return _create_anthropic_llm(model, temperature, thinking_budget, **kwargs)


def create_llm(
    provider: ProviderType | None = None,
    model: str | None = None,
    temperature: float | None = 0.7,
    max_tokens: int | None = None,
    thinking_budget: int | None = None,
) -> BaseChatModel:
    """Create an LLM instance with multi-provider support.

    Supports Anthropic (default), DeepSeek, Google, Mistral, OpenAI, Replicate, and xAI providers.
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
        llm = _dispatch_provider(
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


def _create_replicate_llm(
    model: str, temperature: float, **kwargs: object
) -> BaseChatModel:
    """Create a Replicate-hosted model via LangChain wrapper.

    Uses langchain-litellm for unified interface. Requires REPLICATE_API_TOKEN
    environment variable (loaded from .env via config.py).

    Note: Replicate doesn't support structured output (response_format).
    Use parse_json: true in node config instead of output_schema in prompts.

    Args:
        model: Model name (e.g., "ibm-granite/granite-4.0-h-small")
        temperature: Temperature for generation

    Returns:
        LangChain-compatible chat model

    Raises:
        ValueError: If REPLICATE_API_TOKEN is not set
    """
    import warnings

    import litellm
    from langchain_litellm import ChatLiteLLM

    # Suppress Pydantic serialization warnings from langchain-litellm
    # (type mismatch between LiteLLM and LangChain response types - harmless)
    warnings.filterwarnings("ignore", message="Pydantic serializer warnings")

    # Validate API token is set
    if not os.getenv("REPLICATE_API_TOKEN"):
        raise ValueError(
            "REPLICATE_API_TOKEN environment variable is required. "
            "Get your token at https://replicate.com/account/api-tokens"
        )

    # Drop unsupported params (like response_format) for Replicate
    litellm.drop_params = True

    # LiteLLM format: replicate/owner/model
    litellm_model = f"replicate/{model}"

    return ChatLiteLLM(
        model=litellm_model,
        temperature=temperature,
        **kwargs,
    )


def _create_vertex_llm(
    model: str, temperature: float, thinking_budget: int | None = None, **kwargs: object
) -> BaseChatModel:
    """Create Google Vertex AI LLM.

    Express mode (VERTEX_API_KEY set): passes google_api_key only — no project/location.
    ADC mode (VERTEX_API_KEY absent): passes project + location via GCP ADC credentials.
    The two branches are mutually exclusive to satisfy the google-genai SDK constraint.
    """
    from langchain_google_genai import ChatGoogleGenerativeAI

    vertex_kwargs = dict(kwargs)
    if thinking_budget is not None:
        vertex_kwargs["thinking_budget"] = thinking_budget

    api_key = os.getenv("VERTEX_API_KEY")
    if api_key:
        with (
            _VERTEX_CONSTRUCT_LOCK,
            _masked_env(
                "GOOGLE_CLOUD_PROJECT",
                "GOOGLE_CLOUD_LOCATION",
                "VERTEXAI_PROJECT",
                "GOOGLE_API_KEY",
            ),
        ):
            return ChatGoogleGenerativeAI(
                model=model,
                temperature=temperature,
                vertexai=True,
                google_api_key=api_key,
                **vertex_kwargs,
            )

    project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("VERTEXAI_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        vertexai=True,
        project=project,
        location=location,
        **vertex_kwargs,
    )


def clear_cache() -> None:
    """Clear the LLM instance cache.

    Useful for testing or when you want to force recreation of LLM instances.
    """
    with _cache_lock:
        _llm_cache.clear()
    logger.debug("LLM cache cleared")
