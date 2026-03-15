"""Generate images via Replicate z-image from prompts."""

from __future__ import annotations

import contextlib
import logging
import subprocess
from pathlib import Path

from examples.shared.replicate_tool import generate_image

logger = logging.getLogger(__name__)


def _embed_exif(image_path: Path, prompt: str) -> None:
    """Best-effort EXIF embedding. Requires exiftool on PATH."""
    with contextlib.suppress(FileNotFoundError, subprocess.CalledProcessError):
        subprocess.run(
            [
                "exiftool",
                "-overwrite_original",
                f"-Description={prompt}",
                str(image_path),
            ],
            capture_output=True,
            timeout=10,
            check=True,
        )


def generate_images_node(state: dict) -> dict:
    """Generate images via Replicate from prompts.

    Iterates over prompts, generates images via z-image model,
    saves PNGs and sidecar .txt files to the output directory.

    Args:
        state: Graph state with 'prompts' list and 'output_dir' path

    Returns:
        State update with 'images' list of generated image paths
    """
    prompts = state.get("prompts", [])
    output_dir = Path(state.get("output_dir", "outputs/image_pipeline"))
    output_dir.mkdir(parents=True, exist_ok=True)

    image_paths: list[str] = []

    for i, prompt in enumerate(prompts, 1):
        image_path = output_dir / f"image_{i:02d}.png"
        logger.info(f"🎨 [{i}/{len(prompts)}] Generating: {prompt[:60]}...")

        result = generate_image(prompt, image_path, model_name="z-image")

        if result.success and result.path:
            image_paths.append(str(image_path))
            # Sidecar file (always written)
            sidecar = image_path.with_suffix(".txt")
            sidecar.write_text(prompt)
            # EXIF embedding (optional, best-effort)
            _embed_exif(image_path, prompt)
        else:
            logger.warning(f"⚠ Image {i} failed: {result.error}")

    logger.info(f"✅ Generated {len(image_paths)}/{len(prompts)} images")

    return {"images": image_paths}
