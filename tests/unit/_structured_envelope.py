"""LangChain ``include_raw=True`` structured-output envelope for test doubles (FR-1164)."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage


def envelope(
    parsed: Any, raw: Any = None, parsing_error: BaseException | None = None
) -> dict:
    """Return ``{"raw", "parsed", "parsing_error"}`` as ``with_structured_output`` does."""
    return {
        "raw": AIMessage(content="") if raw is None else raw,
        "parsed": parsed,
        "parsing_error": parsing_error,
    }
