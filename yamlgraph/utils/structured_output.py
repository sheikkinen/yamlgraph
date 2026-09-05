"""Structured-output policy: how a provider is asked for a shape (FR-998).

The ONLY production caller of the library structured-output binder. Three surfaces —
``executor_base.attempt_structured_invoke`` (the sync executor and the threaded
async wrapper), ``race_node._invoke_candidate_async`` (native async) and both
agent finalisation tiers — route through here instead of repeating a library
default.

Policy:

- An explicit ``method`` is forwarded unchanged. The agent's recovery tier
  passes ``"function_calling"`` and can never be upgraded from here.
- With no override, Anthropic chat models get ``"json_schema"``: constrained
  decoding, so the decoder — not the model's goodwill — guarantees that a
  ``list[str]`` field arrives as a list. Every other provider keeps the
  library default (no ``method`` kwarg at all).
- Invocation makes exactly one forced-tool-call second attempt when, and only
  when, Anthropic answers a typed 400 saying the model does not support
  ``output_config`` (``llm_providers`` predicates). Every other error — including
  one raised by the second attempt — propagates unchanged.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from yamlgraph.utils.llm_providers import (
    is_anthropic_chat_model,
    is_anthropic_unsupported_structured_output,
)

logger = logging.getLogger(__name__)

CONSTRAINED_METHOD = "json_schema"
FORCED_TOOL_CALL_METHOD = "function_calling"


def bind_structured_output(
    llm: Any, output_model: type, *, method: str | None = None
) -> Any:
    """Return the structured-output runnable for *llm* under the FR-998 policy."""
    if method is None and is_anthropic_chat_model(llm):
        method = CONSTRAINED_METHOD
    kwargs = {} if method is None else {"method": method}
    return llm.with_structured_output(output_model, **kwargs)


def _model_name(llm: Any) -> str:
    return str(getattr(llm, "model", type(llm).__name__))


def _second_attempt_earned(llm: Any, err: BaseException) -> bool:
    """Classify *err* at the provider boundary; log once when it qualifies."""
    if not is_anthropic_unsupported_structured_output(llm, err):
        return False
    logger.info(
        "Anthropic constrained output unsupported on %s; "
        "one forced-tool-call attempt (FR-998)",
        _model_name(llm),
    )
    return True


def invoke_structured(
    llm: Any, output_model: type, messages: list, *, config: dict | None = None
) -> Any:
    """One structured invocation (sync) under the policy above."""
    call = {} if config is None else {"config": config}
    try:
        return bind_structured_output(llm, output_model).invoke(messages, **call)
    except Exception as err:
        if not _second_attempt_earned(llm, err):
            raise
        return bind_structured_output(
            llm, output_model, method=FORCED_TOOL_CALL_METHOD
        ).invoke(messages, **call)


async def ainvoke_structured(
    llm: Any,
    output_model: type,
    messages: list,
    *,
    config: dict | None = None,
    second_attempt_config: Callable[[], dict] | None = None,
) -> Any:
    """Native-async twin of :func:`invoke_structured` — ``ainvoke``, never a thread.

    ``second_attempt_config`` is called at most once, immediately before the
    second attempt, so a caller that traces per attempt (the race node,
    FR-720) can give that attempt its own run id. ``None`` reuses *config*.
    """
    call = {} if config is None else {"config": config}
    try:
        return await bind_structured_output(llm, output_model).ainvoke(messages, **call)
    except Exception as err:
        if not _second_attempt_earned(llm, err):
            raise
        if second_attempt_config is not None:
            call = {"config": second_attempt_config()}
        return await bind_structured_output(
            llm, output_model, method=FORCED_TOOL_CALL_METHOD
        ).ainvoke(messages, **call)
