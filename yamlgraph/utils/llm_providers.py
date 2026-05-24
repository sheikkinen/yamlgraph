"""LLM provider-specific creation functions.

Extracted from llm_factory.py (FR-263) to keep module sizes within the
450-line gate.  Each ``_create_<provider>_llm`` function lazily imports its
SDK dependency so that only the active provider's package is required at
runtime.
"""

import logging
import os
import threading
from contextlib import contextmanager

from langchain_core.language_models.chat_models import BaseChatModel

logger = logging.getLogger(__name__)

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


def _create_azure_llm(
    model: str, temperature: float, **kwargs: object
) -> BaseChatModel:
    """Create Azure AI LLM via langchain-azure-ai.

    Uses AzureAIOpenAIApiChatModel which covers both Azure OpenAI deployments
    and Azure AI Foundry model catalog (GPT-4o, Llama, Mistral, Cohere).

    Args:
        model: Deployment/model name (e.g., "gpt-4o")
        temperature: Temperature for generation

    Returns:
        LangChain-compatible chat model

    Raises:
        ValueError: If AZURE_AI_ENDPOINT or AZURE_AI_API_KEY is not set
    """
    from langchain_azure_ai.chat_models import AzureAIOpenAIApiChatModel

    endpoint = os.getenv("AZURE_AI_ENDPOINT", "")
    api_key = os.getenv("AZURE_AI_API_KEY", "")

    if not endpoint:
        raise ValueError(
            "AZURE_AI_ENDPOINT environment variable is required. "
            "Set it to your Azure AI Foundry endpoint URL "
            "(e.g. https://my-resource.services.ai.azure.com/openai/v1)"
        )
    if not api_key:
        raise ValueError(
            "AZURE_AI_API_KEY environment variable is required. "
            "Get your key from the Azure Portal under your resource's Keys section."
        )

    return AzureAIOpenAIApiChatModel(
        endpoint=endpoint,
        credential=api_key,
        model=model,
        temperature=temperature,
        **kwargs,
    )


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


def _create_mistral_llm(
    model: str, temperature: float, **kwargs: object
) -> BaseChatModel:
    """Create Mistral AI LLM."""
    from langchain_mistralai import ChatMistralAI

    return ChatMistralAI(model=model, temperature=temperature, **kwargs)


def _create_openai_llm(
    model: str, temperature: float | None, **kwargs: object
) -> BaseChatModel:
    """Create OpenAI LLM."""
    from langchain_openai import ChatOpenAI

    params: dict[str, object] = {"model": model, **kwargs}
    if temperature is not None:
        params["temperature"] = temperature
    return ChatOpenAI(**params)


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


def dispatch_provider(
    provider: str,
    model: str,
    temperature: float | None,
    thinking_budget: int | None,
    **kwargs: object,
) -> BaseChatModel:
    """Dispatch to appropriate provider-specific creation function."""
    if provider == "azure":
        return _create_azure_llm(model, temperature, **kwargs)
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
