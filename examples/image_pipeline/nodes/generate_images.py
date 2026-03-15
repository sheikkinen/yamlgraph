"""Generate images via Replicate z-image from prompts."""

from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path

from examples.shared.replicate_tool import generate_image

logger = logging.getLogger(__name__)


def _embed_exif(image_path: Path, prompt: str) -> bool:
    """Embed prompt in image EXIF Description field.

    Uses exiftool to write the prompt into the image's EXIF metadata.
    This is the canonical storage for the prompt — sidecar files are optional.

    Args:
        image_path: Path to the image file
        prompt: The prompt text to embed

    Returns:
        True if metadata was written successfully, False otherwise
    """
    try:
        subprocess.run(
            [
                "exiftool",
                "-overwrite_original",
                f"-Description={prompt}",
                str(image_path),
            ],
            capture_output=True,
            timeout=30,
            check=True,
        )
        logger.debug(f"📝 EXIF written to {image_path.name}")
        return True
    except FileNotFoundError:
        logger.warning("⚠ exiftool not found — install with: brew install exiftool")
        return False
    except subprocess.CalledProcessError as e:
        logger.warning(
            f"⚠ exiftool failed: {e.stderr.decode() if e.stderr else 'unknown error'}"
        )
        return False
    except subprocess.TimeoutExpired:
        logger.warning(f"⚠ exiftool timed out for {image_path.name}")
        return False


def _extract_prompt_texts(prompts: list) -> list[str]:
    """Recursively extract prompt_text values from nested structures.

    Handles:
    - list[str] → returns as-is
    - list[dict with prompt_text] → extracts prompt_text
    - list[dict with nested prompts] → flattens and extracts (map over subgraphs)
    """
    texts = []
    for p in prompts:
        if isinstance(p, str):
            texts.append(p)
        elif isinstance(p, dict):
            # Check for nested prompts (from map over subgraphs)
            if "prompts" in p and isinstance(p["prompts"], list):
                texts.extend(_extract_prompt_texts(p["prompts"]))
            # Check for direct prompt_text
            elif "prompt_text" in p:
                texts.append(p["prompt_text"])
            else:
                texts.append(str(p))
    return texts


def generate_images_node(state: dict) -> dict:
    """Generate images via Replicate from prompts.

    Iterates over prompts, generates images via z-image model,
    saves PNGs and sidecar .txt files to the output directory.

    Args:
        state: Graph state with 'prompts' list and 'output_dir' path

    Returns:
        State update with 'images' list of generated image paths
    """
    output_dir = Path(state.get("output_dir", "outputs/image_pipeline"))
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use pre-extracted prompt_texts if available (from save_prompts), else extract
    prompt_texts = state.get("prompt_texts")
    if not prompt_texts:
        prompts = state.get("prompts", [])
        prompt_texts = _extract_prompt_texts(prompts)

    image_paths: list[str] = []

    for i, prompt in enumerate(prompt_texts, 1):
        # Include timestamp in filename (matches zimage-replicate.mjs pattern)
        timestamp = int(time.time() * 1000)  # milliseconds since epoch
        image_path = output_dir / f"zimage_{i:02d}_{timestamp}.png"
        logger.info(f"🎨 [{i}/{len(prompt_texts)}] Generating: {prompt[:60]}...")

        result = generate_image(prompt, image_path, model_name="z-image")

        if result.success and result.path:
            image_paths.append(str(image_path))
            # Embed prompt in EXIF metadata (canonical storage)
            exif_ok = _embed_exif(image_path, prompt)
            if not exif_ok:
                # Fallback: write sidecar .txt if EXIF failed
                sidecar = image_path.with_suffix(".txt")
                sidecar.write_text(prompt)
                logger.info(f"📄 Fallback sidecar written: {sidecar.name}")
        else:
            logger.warning(f"⚠ Image {i} failed: {result.error}")

    logger.info(f"✅ Generated {len(image_paths)}/{len(prompt_texts)} images")

    return {"images": image_paths}
