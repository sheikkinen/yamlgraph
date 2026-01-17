"""Replicate image generation tool for storyboard workflow.

Uses the Z-Image Turbo model to generate images from prompts.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

# Check if replicate is available
try:
    import replicate

    REPLICATE_AVAILABLE = True
except ImportError:
    REPLICATE_AVAILABLE = False
    logger.warning("replicate package not installed. Run: pip install replicate")


@dataclass
class ImageResult:
    """Result from image generation."""

    success: bool
    path: str | None = None
    error: str | None = None


def generate_image(
    prompt: str,
    output_path: str | Path,
    width: int = 1344,
    height: int = 768,
    model: str = "prunaai/z-image-turbo",
) -> ImageResult:
    """Generate an image using Replicate API.

    Args:
        prompt: Text prompt for image generation
        output_path: Path to save the generated image
        width: Image width (default 1344 for 16:9)
        height: Image height (default 768 for 16:9)
        model: Replicate model identifier

    Returns:
        ImageResult with success status and path or error
    """
    if not REPLICATE_AVAILABLE:
        return ImageResult(success=False, error="replicate package not installed")

    api_token = os.environ.get("REPLICATE_API_TOKEN")
    if not api_token:
        return ImageResult(
            success=False, error="REPLICATE_API_TOKEN not set in environment"
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        logger.info(f"🎨 Generating image: {prompt[:50]}...")

        # Run the model
        client = replicate.Client(api_token=api_token)
        output = client.run(
            model,
            input={
                "prompt": prompt,
                "width": width,
                "height": height,
                "output_format": "png",
                "guidance_scale": 0,
                "output_quality": 80,
                "num_inference_steps": 8,
            },
        )

        # output is typically a URL or file-like object
        image_url = output if isinstance(output, str) else str(output)

        # Download the image
        logger.info(f"📥 Downloading image to {output_path}")
        response = httpx.get(image_url, timeout=60.0)
        response.raise_for_status()

        output_path.write_bytes(response.content)
        logger.info(f"✓ Image saved: {output_path}")

        return ImageResult(success=True, path=str(output_path))

    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return ImageResult(success=False, error=str(e))


def generate_storyboard_images(
    panel_prompts: list[str],
    output_dir: str | Path,
    prefix: str = "panel",
) -> list[ImageResult]:
    """Generate multiple images for a storyboard.

    Args:
        panel_prompts: List of prompts for each panel
        output_dir: Directory to save images
        prefix: Filename prefix

    Returns:
        List of ImageResult for each panel
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for i, prompt in enumerate(panel_prompts, 1):
        output_path = output_dir / f"{prefix}_{i}.png"
        result = generate_image(prompt, output_path)
        results.append(result)

    return results
