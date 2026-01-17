"""Animated storyboard node for generating frame images.

Generates 3 images per panel: first_frame, original, last_frame.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .replicate_tool import generate_image

logger = logging.getLogger(__name__)

GraphState = dict[str, Any]


def generate_animated_images_node(state: GraphState) -> dict:
    """Generate images for all animated panel frames.

    Reads animated_panels from state and generates 3 images per panel.
    Saves to outputs/storyboard/{thread_id}/animated/ directory.

    Args:
        state: Graph state with 'animated_panels' list of {first_frame, original, last_frame}

    Returns:
        State update with 'images' list organized by panel
    """
    animated_panels = state.get("animated_panels", [])
    if not animated_panels:
        logger.error("No animated_panels in state")
        return {
            "current_step": "generate_animated_images",
            "images": [],
            "error": "No animated panels to generate",
        }

    # Sort by _map_index if present to maintain order
    if animated_panels and isinstance(animated_panels[0], dict):
        animated_panels = sorted(
            animated_panels,
            key=lambda x: x.get("_map_index", 0) if isinstance(x, dict) else 0,
        )

    # Create output directory
    thread_id = state.get("thread_id", datetime.now().strftime("%Y%m%d_%H%M%S"))
    output_dir = Path("outputs/storyboard") / thread_id / "animated"
    output_dir.mkdir(parents=True, exist_ok=True)

    total_images = len(animated_panels) * 3
    logger.info(
        f"🎬 Generating {total_images} images ({len(animated_panels)} panels × 3 frames)"
    )

    # Get model selection from state (default: z-image)
    model_name = state.get("model", "z-image")
    logger.info(f"🖼️  Using model: {model_name}")

    # Generate images for each panel
    all_results: list[dict] = []
    frame_keys = ["first_frame", "original", "last_frame"]

    for panel_idx, panel in enumerate(animated_panels, 1):
        # Handle Pydantic model or dict
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

            result = generate_image(prompt, output_path, model_name=model_name)

            if result.success and result.path:
                panel_result["frames"][frame_key] = result.path
            else:
                logger.error(f"Panel {panel_idx} {frame_key} failed: {result.error}")
                panel_result["frames"][frame_key] = None

        all_results.append(panel_result)

    # Save metadata
    story = state.get("story", {})
    if hasattr(story, "model_dump"):
        story_dict = story.model_dump()
    elif isinstance(story, dict):
        story_dict = story
    else:
        story_dict = {}

    metadata_path = output_dir / "animated_story.json"
    metadata = {
        "concept": state.get("concept", ""),
        "title": story_dict.get("title", ""),
        "narrative": story_dict.get("narrative", ""),
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

    # Count successes
    success_count = sum(1 for r in all_results for path in r["frames"].values() if path)
    logger.info(f"✅ Generated {success_count}/{total_images} images")

    return {
        "current_step": "generate_animated_images",
        "images": all_results,
        "output_dir": str(output_dir),
    }
