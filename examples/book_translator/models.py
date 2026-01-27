"""Shared models for book translator."""

from dataclasses import dataclass


@dataclass
class Chunk:
    """A text chunk with context for translation.

    Attributes:
        index: Position in the sequence of chunks
        title: Section/chapter title
        text: The actual text content
        context_before: Text from previous chunk for context
        context_after: Text from next chunk for context
        char_count: Character count of the text
    """

    index: int
    title: str
    text: str
    context_before: str
    context_after: str
    char_count: int

    def to_dict(self) -> dict:
        """Convert to dictionary for state serialization."""
        return {
            "index": self.index,
            "title": self.title,
            "text": self.text,
            "context_before": self.context_before,
            "context_after": self.context_after,
            "char_count": self.char_count,
        }
