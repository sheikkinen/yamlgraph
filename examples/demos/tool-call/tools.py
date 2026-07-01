"""Tool-call demo: prepare task dict and tool implementations."""


def prepare_task(state: dict) -> dict:
    """Build a task dict dispatching word_count on the given text."""
    text = state.get("text", "")
    return {"task": {"tool": "word_count", "args": {"text": text}}}


def word_count(text: str = "") -> str:
    """Count words in text."""
    return str(len(text.split()))


def char_count(text: str = "") -> str:
    """Count characters in text."""
    return str(len(text))
