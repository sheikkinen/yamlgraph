"""Generate images via Replicate z-image from prompts."""

from __future__ import annotations

import logging
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from examples.shared.replicate_tool import generate_image

logger = logging.getLogger(__name__)


@dataclass
class PromptMetadata:
    """Full metadata for a prompt."""

    prompt_text: str
    concept: str = ""
    scene_brief: str = ""


def _embed_exif(image_path: Path, metadata: PromptMetadata) -> bool:
    """Embed prompt metadata in image EXIF fields.

    Uses exiftool to write metadata into the image's EXIF:
    - Description: Full prompt text
    - Title: Concept
    - Subject: Scene brief
    - Keywords: "ai-generated, concept:{concept}"

    Args:
        image_path: Path to the image file
        metadata: PromptMetadata with prompt_text, concept, scene_brief

    Returns:
        True if metadata was written successfully, False otherwise
    """
    try:
        args = [
            "exiftool",
            "-overwrite_original",
            f"-Description={metadata.prompt_text}",
        ]
        if metadata.concept:
            args.append(f"-Title={metadata.concept}")
            args.append(f"-Keywords=ai-generated, concept:{metadata.concept}")
        if metadata.scene_brief:
            args.append(f"-Subject={metadata.scene_brief}")
        args.append(str(image_path))

        subprocess.run(args, capture_output=True, timeout=30, check=True)
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


def _extract_prompt_metadata(prompts: list) -> list[PromptMetadata]:
    """Recursively extract full prompt metadata from nested structures.

    Handles:
    - list[str] → PromptMetadata with prompt_text only
    - list[dict with prompt_text/concept/scene_brief] → full PromptMetadata
    - list[dict with nested prompts] → flattens and extracts (map over subgraphs)
    """
    results: list[PromptMetadata] = []
    for p in prompts:
        if isinstance(p, str):
            results.append(PromptMetadata(prompt_text=p))
        elif isinstance(p, dict):
            # Check for nested prompts (from map over subgraphs)
            if "prompts" in p and isinstance(p["prompts"], list):
                results.extend(_extract_prompt_metadata(p["prompts"]))
            # Check for direct prompt_text
            elif "prompt_text" in p:
                results.append(
                    PromptMetadata(
                        prompt_text=p["prompt_text"],
                        concept=p.get("concept", ""),
                        scene_brief=p.get("scene_brief", ""),
                    )
                )
            else:
                results.append(PromptMetadata(prompt_text=str(p)))
    return results


def _generate_single_image(
    index: int, metadata: PromptMetadata, output_dir: Path, total: int
) -> tuple[int, str | None, PromptMetadata]:
    """Generate a single image (worker function for parallel execution).

    Returns:
        Tuple of (index, image_path_or_none, metadata)
    """
    timestamp = int(time.time() * 1000)
    image_path = output_dir / f"zimage_{index:02d}_{timestamp}.png"
    logger.info(f"🎨 [{index}/{total}] Generating: {metadata.prompt_text[:60]}...")

    result = generate_image(metadata.prompt_text, image_path, model_name="z-image")

    if result.success and result.path:
        return (index, str(image_path), metadata)
    else:
        logger.warning(f"⚠ Image {index} failed: {result.error}")
        return (index, None, metadata)


def generate_images_node(state: dict) -> dict:
    """Generate images via Replicate from prompts (parallel execution).

    Uses ThreadPoolExecutor to generate multiple images concurrently.
    EXIF metadata embedding happens after all images are generated.

    EXIF fields embedded:
    - Description: Full prompt text
    - Title: Concept theme
    - Subject: Scene brief
    - Keywords: ai-generated, concept tag

    Args:
        state: Graph state with 'prompts' list and 'output_dir' path

    Returns:
        State update with 'images' list of generated image paths
    """
    output_dir = Path(state.get("output_dir", "outputs/image_pipeline"))
    output_dir.mkdir(parents=True, exist_ok=True)

    # Extract full prompt metadata (concept, scene_brief, prompt_text)
    prompts = state.get("prompts", [])
    prompt_metadata = _extract_prompt_metadata(prompts)

    total = len(prompt_metadata)
    logger.info(f"🚀 Starting parallel generation of {total} images...")

    # Parallel image generation
    results: list[tuple[int, str | None, PromptMetadata]] = []
    with ThreadPoolExecutor(max_workers=min(10, total)) as executor:
        futures = {
            executor.submit(_generate_single_image, i, meta, output_dir, total): i
            for i, meta in enumerate(prompt_metadata, 1)
        }
        for future in as_completed(futures):
            results.append(future.result())

    # Sort by index to maintain order
    results.sort(key=lambda x: x[0])

    # Post-process: embed EXIF metadata (sequential — fast, local operation)
    image_paths: list[str] = []
    for _index, path, metadata in results:
        if path:
            image_paths.append(path)
            exif_ok = _embed_exif(Path(path), metadata)
            if not exif_ok:
                # Fallback: write sidecar with full metadata
                sidecar = Path(path).with_suffix(".txt")
                lines = [metadata.prompt_text]
                if metadata.concept:
                    lines.insert(0, f"Concept: {metadata.concept}")
                if metadata.scene_brief:
                    lines.insert(
                        1 if metadata.concept else 0, f"Brief: {metadata.scene_brief}"
                    )
                sidecar.write_text("\n".join(lines), encoding="utf-8")
                logger.info(f"📄 Fallback sidecar written: {sidecar.name}")

    logger.info(f"✅ Generated {len(image_paths)}/{total} images")

    return {"images": image_paths}
