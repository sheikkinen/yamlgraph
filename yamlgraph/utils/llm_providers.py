"""LLM provider-specific creation functions.

Extracted from llm_factory.py (FR-263) to keep module sizes within the
450-line gate.  Each ``_create_<provider>_llm`` function lazily imports its
SDK dependency so that only the active provider's package is required at
runtime.  Request bounds (FR-708/710) live in ``llm_bounds.py``; provider
identity and capability classification (FR-998) live at the bottom of this
module, behind the same lazy-import discipline.
"""

import logging
import os

from langchain_core.language_models.chat_models import BaseChatModel

from yamlgraph.utils.llm_bounds import (
    _VERTEX_CONSTRUCT_LOCK,
    _bounded,
    _masked_env,
    _vertex_transport,
)

logger = logging.getLogger(__name__)

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

    return ChatAnthropic(
        model=model, temperature=temperature, **_bounded(anthropic_kwargs)
    )


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
        **_bounded(dict(kwargs)),
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
        **_bounded(dict(kwargs)),
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
        **_vertex_transport(_bounded(google_kwargs, provider="google")),
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
        **_bounded(dict(kwargs)),
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
        **_bounded(dict(kwargs)),
    )


def _create_mistral_llm(
    model: str, temperature: float, **kwargs: object
) -> BaseChatModel:
    """Create Mistral AI LLM."""
    from langchain_mistralai import ChatMistralAI

    return ChatMistralAI(model=model, temperature=temperature, **_bounded(dict(kwargs)))


def _create_openai_llm(
    model: str, temperature: float | None, **kwargs: object
) -> BaseChatModel:
    """Create OpenAI LLM."""
    from langchain_openai import ChatOpenAI

    params: dict[str, object] = {"model": model, **_bounded(dict(kwargs))}
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
        **_bounded(dict(kwargs), timeout_param="request_timeout"),
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
    vertex_kwargs = _vertex_transport(_bounded(vertex_kwargs, provider="vertex"))

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
        **_bounded(dict(kwargs)),
    )


def _create_runpod_llm(
    model: str, temperature: float, **kwargs: object
) -> BaseChatModel:
    """Create RunPod LLM via its OpenAI-compatible endpoint (FR-766).

    RUNPOD_ENDPOINT is the full base URL (Public API model slug or
    serverless vLLM id); all three env inputs fail fast here (R-1).
    """
    from langchain_openai import ChatOpenAI

    base_url = os.getenv("RUNPOD_ENDPOINT")
    if not base_url:
        raise ValueError("RUNPOD_ENDPOINT is required for provider 'runpod'")
    api_key = os.getenv("RUNPOD_API_KEY")
    if not api_key:
        raise ValueError("RUNPOD_API_KEY is required for provider 'runpod'")
    if not model:
        raise ValueError("RUNPOD_MODEL is required for provider 'runpod'")
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        base_url=base_url,
        api_key=api_key,
        **_bounded(dict(kwargs)),
    )


# Providers whose factory accepts a `thinking_budget` argument (FR-680).
_THINKING_PROVIDERS = frozenset({"anthropic", "google", "vertex"})

# Data-driven provider registry (FR-680). Adding a provider is one entry here
# plus its `_create_*_llm` factory — no edit to `dispatch_provider`.
_PROVIDER_FACTORIES = {
    "anthropic": _create_anthropic_llm,
    "azure": _create_azure_llm,
    "deepseek": _create_deepseek_llm,
    "google": _create_google_llm,
    "inception": _create_inception_llm,
    "lmstudio": _create_lmstudio_llm,
    "mistral": _create_mistral_llm,
    "openai": _create_openai_llm,
    "replicate": _create_replicate_llm,
    "runpod": _create_runpod_llm,
    "vertex": _create_vertex_llm,
    "xai": _create_xai_llm,
}


def dispatch_provider(
    provider: str,
    model: str,
    temperature: float | None,
    thinking_budget: int | None,
    **kwargs: object,
) -> BaseChatModel:
    """Dispatch to the appropriate provider-specific creation function.

    FR-680: registry lookup replaces the former 11-branch if/elif chain.
    Unknown providers raise loudly here — there is no silent Anthropic
    substitution at this boundary (`create_llm` owns unset-provider defaulting).
    """
    factory = _PROVIDER_FACTORIES.get(provider)
    if factory is None:
        raise ValueError(
            f"Unknown provider '{provider}'. "
            f"Valid: {', '.join(sorted(_PROVIDER_FACTORIES))}"
        )
    if provider in _THINKING_PROVIDERS:
        return factory(model, temperature, thinking_budget, **kwargs)
    return factory(model, temperature, **kwargs)


# --- Provider identity and capability classification (FR-998) ---

# Anthropic's wording when a *model* lacks a capability. The structured error
# message must name the capability, say it is unsupported, and blame the model;
# a 400 that points into the schema (``output_config.format.schema``, "JSON
# Schema keyword ... unsupported") is a schema defect, not a capability gap,
# and must propagate (review #599 P2).
_CAPABILITY_TERMS = ("output_config", "structured output")
_UNSUPPORTED_TERMS = ("not support", "unsupported", "not available", "unavailable")
_SCHEMA_DEFECT_TERMS = (".schema", "json schema", "keyword", "invalid schema")


def is_anthropic_chat_model(llm: object) -> bool:
    """True when *llm* is a ``ChatAnthropic`` instance (subclasses included).

    ``isinstance`` against the lazily imported class — never
    ``type(llm).__name__``. Without ``langchain-anthropic`` installed nothing
    can be an Anthropic chat model. Generic modules (executor, race, agent)
    call this; they never import the provider class themselves.
    """
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        return False
    return isinstance(llm, ChatAnthropic)


def _structured_error_message(err: object) -> str:
    """The ``error.message`` of an Anthropic error body, or ``""`` without one."""
    body = getattr(err, "body", None)
    if not isinstance(body, dict):
        return ""
    error = body.get("error")
    if not isinstance(error, dict):
        return ""
    return str(error.get("message", ""))


def is_anthropic_unsupported_structured_output(llm: object, err: BaseException) -> bool:
    """The one error that earns a second, forced-tool-call attempt (FR-998).

    All four must hold: (1) *llm* is an Anthropic chat model; (2) *err* is
    Anthropic's typed ``BadRequestError``; (3) its status is HTTP 400; (4) the
    structured error body — not ``str(err)`` — says ``output_config`` /
    structured output is unsupported *for the model* and does not point into
    the schema. A Pydantic
    ``ValidationError``, auth, permission, rate-limit, timeout, network and
    server errors, an unrelated 400, and binding errors all answer False and
    propagate to the caller unchanged.
    """
    if not is_anthropic_chat_model(llm):
        return False
    from anthropic import BadRequestError

    if not isinstance(err, BadRequestError) or err.status_code != 400:
        return False
    message = _structured_error_message(err).lower()
    if any(term in message for term in _SCHEMA_DEFECT_TERMS):
        return False
    return (
        "model" in message
        and any(term in message for term in _CAPABILITY_TERMS)
        and any(term in message for term in _UNSUPPORTED_TERMS)
    )
