"""Output-token-limit check on a raw LLM reply (FR-1164).

One classifier for the three surfaces that first hold an LLM node's reply:
``executor_base.attempt_structured_invoke``, the structured policy helpers in
``structured_output`` and ``race_node._invoke_candidate_async``. A reply whose
provider reports a stop on the output-token limit raises
:class:`OutputTruncatedError` instead of being returned as a finished answer.

Stop values (offline package reads + live probe, FR-1164 research record):
Anthropic ``stop_reason="max_tokens"``, OpenAI ``finish_reason="length"``,
Google ``finish_reason="MAX_TOKENS"``. Absent or unrecognized metadata is not
proof of completeness; it only means no rejection here.
"""

from __future__ import annotations

from langchain_core.messages import BaseMessage

TRUNCATED = frozenset({"max_tokens", "length", "MAX_TOKENS"})
PREVIEW_CHARS = 200


def _render(count: int | None) -> str:
    return "unknown" if count is None else str(count)


class OutputTruncatedError(RuntimeError):
    """The provider stopped the reply at the output-token limit.

    Counts the provider does not report stay ``None`` (rendered ``unknown``).
    ``visible_chars`` and ``preview`` come from the normalized visible text
    only; thinking blocks never reach this error.
    """

    def __init__(
        self,
        stop_reason: str,
        output_tokens: int | None,
        reasoning_tokens: int | None,
        visible_chars: int,
        preview: str,
    ) -> None:
        self.stop_reason = stop_reason
        self.output_tokens = output_tokens
        self.reasoning_tokens = reasoning_tokens
        self.visible_chars = visible_chars
        self.preview = preview
        super().__init__(
            f"LLM reply stopped at the output-token limit "
            f"(stop_reason={stop_reason}): {_render(output_tokens)} output tokens, "
            f"{_render(reasoning_tokens)} of them thinking; {visible_chars} visible "
            f"characters. Raise max_tokens; where the model supports a thinking "
            f"budget, lowering it leaves more for the answer."
        )


def ensure_complete(message: BaseMessage) -> None:
    """Raise :class:`OutputTruncatedError` when *message* stopped on the limit."""
    return None
