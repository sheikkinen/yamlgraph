"""Provider identity and capability classification at the provider boundary.

FR-998. Lives beside ``llm_providers.py`` (which sits at the 450-line gate)
and follows its discipline: every provider SDK is imported lazily, inside the
function that needs it. Generic modules — ``executor_base``, ``race_node``,
``tools/agent`` — call these predicates and never import a provider class or
SDK, and never compare class names.
"""

from __future__ import annotations

# Anthropic's wording when a model lacks a capability. Both a capability term
# and an unsupported term must appear in the *structured* error message; a 400
# that names ``output_config`` for another reason (an invalid schema inside
# it) is not a capability gap and must propagate.
_CAPABILITY_TERMS = ("output_config", "structured output")
_UNSUPPORTED_TERMS = ("not support", "unsupported", "not available", "unavailable")


def is_anthropic_chat_model(llm: object) -> bool:
    """True when *llm* is a ``ChatAnthropic`` instance (subclasses included).

    ``isinstance`` against the lazily imported class — never
    ``type(llm).__name__``. Without ``langchain-anthropic`` installed nothing
    can be an Anthropic chat model.
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
    structured output is unsupported for the model. A Pydantic
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
    return any(term in message for term in _CAPABILITY_TERMS) and any(
        term in message for term in _UNSUPPORTED_TERMS
    )
