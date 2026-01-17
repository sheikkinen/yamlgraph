"""Character-consistent storyboard node.

This node:
1. Generates a character image from description (step 0)
2. Uses image-to-image editing to place character in each panel scene
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .replicate_tool import ImageResult, edit_image, generate_image

logger = logging.getLogger(__name__)

# Type alias for state
GraphState = dict[str, Any]


def generate_character_storyboard(state: GraphState) -> dict:
    """Generate character-consistent storyboard images.

    Step 0: Generate base character image from character_prompt
    Panels 1-3: Use image-to-image to place character in each scene

    Args:
        state: Graph state with 'story' containing character and panel prompts

    Returns:
        State update with 'images' list and metadata
    """
    story = state.get("story")
    if not story:
        logger.error("No story in state")
        return {
            "current_step": "generate_character_storyboard",
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

    # Extract prompts
    character_prompt = story_dict.get("character_prompt", "")
    panels = story_dict.get("panels", [])

    if not character_prompt:
        logger.error("No character_prompt in story")
        return {
            "current_step": "generate_character_storyboard",
            "images": [],
            "error": "No character_prompt provided",
        }

    if not panels:
        logger.error("No panels in story")
        return {
            "current_step": "generate_character_storyboard",
            "images": [],
            "error": "No panel prompts provided",
        }

    # Create output directory
    thread_id = state.get("thread_id", datetime.now().strftime("%Y%m%d_%H%M%S"))
    output_dir = Path("outputs/storyboard") / thread_id
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"🎬 Generating character-consistent storyboard in {output_dir}")

    # Get model selection from state (default: z-image for character)
    model_name = state.get("model", "z-image")
    logger.info(f"🖼️  Using model for character: {model_name}")

    image_paths: list[str] = []
    results: list[ImageResult] = []

    # Step 0: Generate base character image
    character_path = output_dir / "character.png"
    logger.info(f"👤 Step 0 - Creating character: {character_prompt[:60]}...")

    character_result = generate_image(
        prompt=character_prompt,
        output_path=character_path,
        model_name=model_name,
    )
    results.append(character_result)

    if not character_result.success:
        logger.error(f"Character generation failed: {character_result.error}")
        return {
            "current_step": "generate_character_storyboard",
            "images": [],
            "error": f"Character generation failed: {character_result.error}",
        }

    image_paths.append(str(character_path))
    logger.info(f"✓ Character created: {character_path}")

    # Panels 1-3: Image-to-image editing with character as base
    for i, panel_prompt in enumerate(panels[:3], 1):  # Max 3 panels
        if not panel_prompt:
            logger.warning(f"Panel {i} has no prompt, skipping")
            continue

        panel_path = output_dir / f"panel_{i}.png"
        logger.info(f"📸 Panel {i}: {panel_prompt[:60]}...")

        panel_result = edit_image(
            input_image=character_path,
            prompt=panel_prompt,
            output_path=panel_path,
            aspect_ratio="16:9",
        )
        results.append(panel_result)

        if panel_result.success and panel_result.path:
            image_paths.append(panel_result.path)
            logger.info(f"✓ Panel {i} created")
        else:
            logger.error(f"Panel {i} failed: {panel_result.error}")

    # Save metadata
    metadata_path = output_dir / "story.json"
    metadata = {
        "concept": state.get("concept", ""),
        "title": story_dict.get("title", ""),
        "narrative": story_dict.get("narrative", ""),
        "character_prompt": character_prompt,
        "character_image": str(character_path),
        "panels": [
            {
                "prompt": panels[i] if i < len(panels) else "",
                "image": image_paths[i + 1] if i + 1 < len(image_paths) else None,
            }
            for i in range(len(panels[:3]))
        ],
        "generated_at": datetime.now().isoformat(),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2))
    logger.info(f"📝 Metadata saved: {metadata_path}")

    success_count = sum(1 for r in results if r.success)
    logger.info(
        f"✅ Generated {success_count}/{len(results)} images (1 character + {len(panels[:3])} panels)"
    )

    return {
        "current_step": "generate_character_storyboard",
        "images": image_paths,
        "character_image": str(character_path),
        "output_dir": str(output_dir),
    }
