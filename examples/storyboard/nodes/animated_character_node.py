"""Animated character storyboard node.

Generates:
1. Character base image
2. 3 images per panel (first_frame, original, last_frame) using img2img from character
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .replicate_tool import edit_image, generate_image

logger = logging.getLogger(__name__)

GraphState = dict[str, Any]


def generate_animated_character_images(state: GraphState) -> dict:
    """Generate animated character-consistent storyboard images.

    Step 0: Generate base character image
    For each panel: Generate first_frame, original, last_frame via img2img

    Args:
        state: Graph state with 'story' and 'animated_panels'

    Returns:
        State update with 'images' and 'character_image'
    """
    story = state.get("story")
    animated_panels = state.get("animated_panels", [])

    if not story:
        logger.error("No story in state")
        return {
            "current_step": "generate_animated_character_images",
            "images": [],
            "error": "No story in state",
        }

    # Handle Pydantic model or dict
    if hasattr(story, "model_dump"):
        story_dict = story.model_dump()
    elif isinstance(story, dict):
        story_dict = story
    else:
        story_dict = {}

    character_prompt = story_dict.get("character_prompt", "")
    if not character_prompt:
        logger.error("No character_prompt in story")
        return {
            "current_step": "generate_animated_character_images",
            "images": [],
            "error": "No character_prompt provided",
        }

    if not animated_panels:
        logger.error("No animated_panels in state")
        return {
            "current_step": "generate_animated_character_images",
            "images": [],
            "error": "No animated panels to generate",
        }

    # Sort by _map_index if present
    if animated_panels and isinstance(animated_panels[0], dict):
        animated_panels = sorted(
            animated_panels,
            key=lambda x: x.get("_map_index", 0) if isinstance(x, dict) else 0,
        )

    # Create output directory
    thread_id = state.get("thread_id", datetime.now().strftime("%Y%m%d_%H%M%S"))
    output_dir = Path("outputs/storyboard") / thread_id / "animated"
    output_dir.mkdir(parents=True, exist_ok=True)

    model_name = state.get("model", "z-image")
    logger.info(f"🎬 Generating animated character storyboard in {output_dir}")
    logger.info(f"🖼️  Using model: {model_name}")

    # Step 0: Generate base character image
    character_path = output_dir / "character.png"
    logger.info(f"👤 Creating character: {character_prompt[:60]}...")

    character_result = generate_image(
        prompt=character_prompt,
        output_path=character_path,
        model_name=model_name,
    )

    if not character_result.success:
        logger.error(f"Character generation failed: {character_result.error}")
        return {
            "current_step": "generate_animated_character_images",
            "images": [],
            "error": f"Character generation failed: {character_result.error}",
        }

    logger.info(f"✓ Character created: {character_path}")

    # Generate frames for each panel
    total_images = len(animated_panels) * 3
    logger.info(
        f"🎞️  Generating {total_images} frames ({len(animated_panels)} panels × 3)"
    )

    all_results: list[dict] = []
    frame_keys = ["first_frame", "original", "last_frame"]

    for panel_idx, panel in enumerate(animated_panels, 1):
        if hasattr(panel, "model_dump"):
            panel_dict = panel.model_dump()
        elif isinstance(panel, dict):
            panel_dict = panel
        else:
            logger.warning(f"Panel {panel_idx} has unexpected type: {type(panel)}")
            continue

        panel_result = {"panel": panel_idx, "frames": {}}

        for frame_key in frame_keys:
            prompt = panel_dict.get(frame_key, "")
            if not prompt:
                logger.warning(f"Panel {panel_idx} missing {frame_key}")
                continue

            output_path = output_dir / f"panel_{panel_idx}_{frame_key}.png"
            logger.info(f"📸 Panel {panel_idx} {frame_key}: {prompt[:50]}...")

            # Use img2img from character
            result = edit_image(
                input_image=character_path,
                prompt=prompt,
                output_path=output_path,
                aspect_ratio="16:9",
            )

            if result.success and result.path:
                panel_result["frames"][frame_key] = result.path
            else:
                logger.error(f"Panel {panel_idx} {frame_key} failed: {result.error}")
                panel_result["frames"][frame_key] = None

        all_results.append(panel_result)

    # Save metadata
    metadata_path = output_dir / "animated_character_story.json"
    metadata = {
        "concept": state.get("concept", ""),
        "title": story_dict.get("title", ""),
        "narrative": story_dict.get("narrative", ""),
        "character_prompt": character_prompt,
        "character_image": str(character_path),
        "panels": [
            {
                "index": r["panel"],
                "frames": r["frames"],
                "prompts": {
                    k: animated_panels[r["panel"] - 1].get(k, "")
                    if isinstance(animated_panels[r["panel"] - 1], dict)
                    else ""
                    for k in frame_keys
                },
            }
            for r in all_results
        ],
        "generated_at": datetime.now().isoformat(),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2))
    logger.info(f"📝 Metadata saved: {metadata_path}")

    success_count = sum(1 for r in all_results for path in r["frames"].values() if path)
    logger.info(f"✅ Generated {success_count}/{total_images} images + 1 character")

    return {
        "current_step": "generate_animated_character_images",
        "character_image": str(character_path),
        "images": all_results,
        "output_dir": str(output_dir),
    }
