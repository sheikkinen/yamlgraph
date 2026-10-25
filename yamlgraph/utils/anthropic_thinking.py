"""Anthropic's thinking setting: the off rule and the Anthropic factory that applies it.

The rule (``thinking_budget: 0`` in the form each model takes) is FR-1148's; FR-1150 moved it here with the
factory, its only caller, from ``llm_providers.py`` to keep that module under the size gate. ``llm_providers``
imports the factory into its registry and re-exports the rule's names. ``langchain_anthropic`` is imported inside
the factory, as before.
"""

from langchain_core.language_models.chat_models import BaseChatModel

from yamlgraph.utils.llm_bounds import _bounded

# Models whose thinking cannot be turned off (effort is their only control).
_ANTHROPIC_THINKING_ALWAYS_ON = ("claude-opus-5-5", "claude-fable-5")


def _anthropic_thinking_off(model: str) -> dict:
    """The ``thinking`` field that turns thinking off on ``model``.

    Claude Sonnet 5.5 refuses ``disabled`` and takes ``between_tools`` (its
    lowest setting: no thinking before the answer); Opus 5.5 and Fable 5.x
    cannot turn thinking off, so asking is an error here rather than a 400
    from the API; every other model takes ``disabled``.
    """
    if any(model.startswith(prefix) for prefix in _ANTHROPIC_THINKING_ALWAYS_ON):
        raise ValueError(
            f"thinking_budget=0: thinking cannot be turned off on {model}; "
            "omit thinking_budget for this model"
        )
    if model.startswith("claude-sonnet-5-5"):
        return {"type": "between_tools"}
    return {"type": "disabled"}


def _create_anthropic_llm(
    model: str,
    temperature: float | None,
    thinking_budget: int | None = None,
    **kwargs: object,
) -> BaseChatModel:
    """Create Anthropic Claude LLM.

    ``thinking_budget``: ``None`` leaves the request as it is (the model's own
    default); ``0`` turns thinking off in the form the model takes
    (``_anthropic_thinking_off``), so a model that thinks by default (Sonnet
    5.5) spends its ``max_tokens`` on the answer; ``>= 1024`` enables thinking
    with that budget.
    """
    from langchain_anthropic import ChatAnthropic

    anthropic_kwargs = dict(kwargs)
    if thinking_budget == 0:
        anthropic_kwargs["thinking"] = _anthropic_thinking_off(model)
    elif thinking_budget is not None and thinking_budget >= 1024:
        anthropic_kwargs["thinking"] = {
            "type": "enabled",
            "budget_tokens": thinking_budget,
        }

    return ChatAnthropic(
        model=model, temperature=temperature, **_bounded(anthropic_kwargs)
    )
