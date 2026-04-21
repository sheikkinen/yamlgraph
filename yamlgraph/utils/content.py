"""Shared content normalization utilities.

LLM providers return different content types for response.content:
- OpenAI: str
- Anthropic Claude: list[dict] (content blocks)

This module provides a single normalization function to ensure
consistent string output regardless of provider (FR-059, FR-264).
"""

from typing import Any

__all__ = ["normalize_content"]


def normalize_content(content: Any) -> str:
    """Normalize LLM response content to string.

    Anthropic Claude returns content as a list of blocks:
    [{"type": "text", "text": "..."}]. This function extracts
    text from all known formats.

    Args:
        content: LLM response content (str, list, or None)

    Returns:
        Normalized string content
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )
    return str(content) if content else ""
