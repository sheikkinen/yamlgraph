"""Graph-local wrapper for the shared vision tool demo."""

from __future__ import annotations

from examples.shared.vision_tool import describe_image

INSTRUCTION = "Title, 2-sentence description, and 8 DeviantArt tags."


def describe_demo_image(state: dict) -> dict:
    """Describe the input image and return plain graph state."""
    result = describe_image(state["image"], INSTRUCTION, provider="google")
    return {"described": result.model_dump()}
