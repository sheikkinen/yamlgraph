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

# FR-708: default request timeout (seconds) for every provider client.
# A hung endpoint must FAIL within this bound instead of hanging forever
# and accumulating transport channels (Fly freeze RCA 2026-07-10).
_DEFAULT_REQUEST_TIMEOUT = 30.0
_DEFAULT_MAX_RETRIES = 2

# FR-710: provider-enforced client deadline floors, validated at construction
# so a below-floor knob fails loudly ONCE instead of a confusing 400 per
# request (which silently drops the candidate from every race).
_PROVIDER_TIMEOUT_FLOORS: dict[str, float] = {
    # Field-verified (FR-709 run 2, verbatim): 400 INVALID_ARGUMENT
    # "Manually set deadline 5s is too short. Minimum allowed deadline is 10s."
    "google": 10.0,
    # Backend-inferred (FR-710 Judgement F2): same google-genai client
    # enforces the deadline; not independently field-verified for vertex —
    # one line to fix if a field run ever contradicts it.
    "vertex": 10.0,
}


def _request_timeout() -> float:
    """Resolve the client request timeout at the env boundary (FR-708).

    Garbage or non-positive values raise — never silently substituted with the
    default (Commandment 6).
    """
    raw = os.getenv("LLM_REQUEST_TIMEOUT")
    if raw is None or not raw.strip():
        return _DEFAULT_REQUEST_TIMEOUT
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(
            f"LLM_REQUEST_TIMEOUT must be a positive number of seconds, got {raw!r}"
        ) from exc
    if value <= 0:
        raise ValueError(
            f"LLM_REQUEST_TIMEOUT must be a positive number of seconds, got {raw!r}"
        )
    return value


def _bounded(
    kwargs: dict, timeout_param: str = "timeout", provider: str | None = None
) -> dict:
    """Inject the FR-708 work bounds unless the caller supplied their own.

    FR-710: for providers with a known deadline floor, the EFFECTIVE timeout
    (whatever its source) is validated at construction — floor, value, and
    source named in the error. The source is resolved BEFORE setdefault
    (Judgement F1), since afterwards kwarg/env/default are indistinguishable.
    """
    if timeout_param in kwargs:
        source = f"caller kwarg {timeout_param}="
    elif (os.getenv("LLM_REQUEST_TIMEOUT") or "").strip():
        source = "LLM_REQUEST_TIMEOUT"
    else:
        source = "the default"
    kwargs.setdefault(timeout_param, _request_timeout())
    kwargs.setdefault("max_retries", _DEFAULT_MAX_RETRIES)

    floor = _PROVIDER_TIMEOUT_FLOORS.get(provider or "")
    if floor is not None:
        value = kwargs[timeout_param]
        # F3: None (or garbage) would TypeError the comparison and silently
        # defeat the FR-708 bound — raise the same shaped error.
        if not isinstance(value, int | float) or value < floor:
            raise ValueError(
                f"{provider} requires a request timeout >= {floor:g}s "
                f"(provider-enforced deadline floor); got {value!r} via {source}"
            )
    return kwargs


def _vertex_transport(kwargs: dict) -> dict:
    """Apply VERTEX_TRANSPORT=rest|grpc to google/vertex constructors (FR-708).

    Unset leaves the SDK default untouched; anything else raises at the
    boundary. REST rides httpx and honors timeouts reliably; gRPC-from-Fly
    is the suspected hanging layer in the freeze RCA.
    """
    raw = os.getenv("VERTEX_TRANSPORT")
    if raw is None or not raw.strip():
        return kwargs
    value = raw.strip().lower()
    if value not in ("rest", "grpc"):
        raise ValueError(f"VERTEX_TRANSPORT must be 'rest' or 'grpc', got {raw!r}")
    kwargs.setdefault("transport", value)
    return kwargs


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
