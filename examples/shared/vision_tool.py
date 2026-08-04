"""Shared vision tool — image → structured text (FR-769, CAP-217).

`describe_image()` sends a local image or URL plus an instruction through
a `create_llm()` chat model and returns a validated `ImageDescription`.

Provider allowlist (google, anthropic) is enforced BEFORE any LLM
invocation: multimodal content parts require a vision-capable chat model,
and the factory's other providers dispatch to text-only wrappers.

Usage:
    from examples.shared.vision_tool import describe_image

    result = describe_image(
        "outputs/images/concept_3.png",
        "Title, 2-sentence description, and 8 DeviantArt tags.",
    )

Requirements: GOOGLE_API_KEY (default provider) or ANTHROPIC_API_KEY.
"""

from __future__ import annotations

import base64
import mimetypes
import os
from pathlib import Path

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from yamlgraph.utils.llm_factory import create_llm

# Initial support matrix (FR-769 R-1): provider -> (model env var, default).
SUPPORTED_PROVIDERS: dict[str, tuple[str, str]] = {
    "google": ("GOOGLE_MODEL", "gemini-2.0-flash"),
    "anthropic": ("ANTHROPIC_MODEL", "claude-haiku-4-5"),
}


class ImageDescription(BaseModel):
    """Structured description of an image."""

    title: str = Field(description="Short evocative title")
    description: str = Field(description="1-3 sentence description")
    tags: list[str] = Field(description="Keyword tags for the image")
    matches_prompt: bool | None = Field(
        default=None,
        description="QA verdict: does the image match the generation prompt?",
    )
    notes: str | None = Field(
        default=None, description="QA notes when matches_prompt is set"
    )


def _image_content_part(image: str | Path) -> dict:
    """Build the image content part: URL passthrough or base64 data URL."""
    ref = str(image)
    if ref.startswith(("http://", "https://")):
        return {"type": "image_url", "image_url": {"url": ref}}

    path = Path(image)
    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {path}")
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    data = base64.b64encode(path.read_bytes()).decode()
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{mime};base64,{data}"},
    }


def describe_image(
    image: str | Path,
    instruction: str,
    *,
    provider: str | None = None,
    model: str | None = None,
) -> ImageDescription:
    """Describe an image with a vision-capable LLM.

    Args:
        image: Local image path or http(s) URL.
        instruction: What to produce (e.g. title/description/tags, QA check).
        provider: LLM provider; defaults to PROVIDER env var or "google".
            Must be in SUPPORTED_PROVIDERS.
        model: Model override; defaults to the provider's model env var or
            its vision-capable default.

    Returns:
        Validated ImageDescription.

    Raises:
        ValueError: Unsupported provider (raised before any LLM call), or
            model output that cannot be validated.
        FileNotFoundError: Local image path does not exist.
    """
    selected = provider or os.getenv("PROVIDER") or "google"
    if selected not in SUPPORTED_PROVIDERS:
        supported = ", ".join(sorted(SUPPORTED_PROVIDERS))
        raise ValueError(
            f"Provider '{selected}' does not support vision here. "
            f"Supported providers: {supported}"
        )

    image_part = _image_content_part(image)

    model_env, default_model = SUPPORTED_PROVIDERS[selected]
    selected_model = model or os.getenv(model_env) or default_model

    llm = create_llm(provider=selected, model=selected_model, temperature=0.2)
    structured = llm.with_structured_output(ImageDescription)
    message = HumanMessage(content=[{"type": "text", "text": instruction}, image_part])
    result = structured.invoke([message])

    if isinstance(result, ImageDescription):
        return result
    if result is None:
        raise ValueError(
            f"Vision model '{selected}/{selected_model}' returned no structured output"
        )
    return ImageDescription.model_validate(result)
