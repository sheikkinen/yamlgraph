"""Request bounds shared by every provider constructor (FR-708 / FR-710).

Extracted from ``llm_providers.py`` (FR-998 review #599 P2) so that module
stays under the 450-line gate. Nothing here imports a provider SDK.
"""

import os
import threading
from contextlib import contextmanager

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
