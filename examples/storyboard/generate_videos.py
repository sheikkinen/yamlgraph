#!/usr/bin/env python3
"""Generate video clips from consecutive image pairs.

Takes a folder of images, sorts alphabetically, and generates
video clips for each consecutive pair (1→2, 2→3, 3→4, etc.)

Usage:
    python examples/storyboard/generate_videos.py outputs/storyboard/20260117_112419/animated

Options:
    --pattern GLOB     File pattern to match (default: *.png)
    --prompt TEXT      Prompt for video generation
    --fps INT          Frames per second (default: 16)
    --frames INT       Number of frames (default: 81)
    --resolution STR   Resolution: 480p, 720p (default: 480p)
    --dry-run          Show what would be generated without running
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Check if replicate is available
try:
    import replicate

    REPLICATE_AVAILABLE = True
except ImportError:
    REPLICATE_AVAILABLE = False


def generate_video_clip(
    first_image: Path,
    last_image: Path,
    output_path: Path,
    prompt: str = "",
    fps: int = 16,
    num_frames: int = 81,
    resolution: str = "480p",
) -> bool:
    """Generate a video clip between two images.

    Args:
        first_image: Starting frame
        last_image: Ending frame
        output_path: Where to save the video
        prompt: Optional prompt describing the motion
        fps: Frames per second
        num_frames: Total number of frames
        resolution: Output resolution (480p, 720p)

    Returns:
        True if successful
    """
    if not REPLICATE_AVAILABLE:
        logger.error("replicate package not installed. Run: pip install replicate")
        return False

    api_token = os.environ.get("REPLICATE_API_TOKEN")
    if not api_token:
        logger.error("REPLICATE_API_TOKEN not set")
        return False

    try:
        logger.info(f"🎬 Generating: {first_image.name} → {last_image.name}")

        client = replicate.Client(api_token=api_token)

        with open(first_image, "rb") as f1, open(last_image, "rb") as f2:
            output = client.run(
                "wan-video/wan-2.2-i2v-fast",
                input={
                    "image": f1,
                    "last_image": f2,
                    "prompt": prompt or "Smooth camera motion, cinematic transition",
                    "go_fast": True,
                    "num_frames": num_frames,
                    "resolution": resolution,
                    "sample_shift": 12,
                    "frames_per_second": fps,
                    "interpolate_output": False,
                    "lora_scale_transformer": 1,
                    "lora_scale_transformer_2": 1,
                },
            )

        # Save the video
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(output.read())

        logger.info(f"✓ Saved: {output_path}")
        return True

    except Exception as e:
        logger.error(f"✗ Failed: {e}")
        return False


def get_prompt_for_pair(
    metadata: dict | None,
    img1_name: str,
    img2_name: str,
) -> str:
    """Try to extract relevant prompt from metadata."""
    if not metadata:
        return ""

    # Parse panel number from filename
    # e.g., "panel_1_first_frame.png" → panel 1
    for panel in metadata.get("panels", []):
        prompts = panel.get("prompts", {})

        # If transitioning within same panel, use the prompts
        if f"panel_{panel['index']}" in img1_name:
            if "first_frame" in img1_name and "original" in img2_name:
                return prompts.get("original", "")
            if "original" in img1_name and "last_frame" in img2_name:
                return prompts.get("last_frame", "")
            if "first_frame" in img1_name and "last_frame" in img2_name:
                return prompts.get("last_frame", "")

    return ""


def main():
    parser = argparse.ArgumentParser(
        description="Generate video clips from consecutive image pairs"
    )
    parser.add_argument(
        "folder",
        type=Path,
        help="Folder containing images",
    )
    parser.add_argument(
        "--pattern",
        default="*.png",
        help="Glob pattern for images (default: *.png)",
    )
    parser.add_argument(
        "--prompt",
        default="",
        help="Prompt for all video generations",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=16,
        help="Frames per second (default: 16)",
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=81,
        help="Number of frames (default: 81)",
    )
    parser.add_argument(
        "--resolution",
        default="480p",
        choices=["480p", "720p"],
        help="Output resolution (default: 480p)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without running",
    )
    args = parser.parse_args()

    folder = args.folder
    if not folder.exists():
        logger.error(f"❌ Folder not found: {folder}")
        sys.exit(1)

    # Find images (alphabetically sorted)
    images = sorted(folder.glob(args.pattern))
    if not images:
        logger.error(f"❌ No images matching '{args.pattern}' in {folder}")
        sys.exit(1)

    # Filter out non-frame images
    images = [img for img in images if img.name not in ("character.png",)]

    logger.info(f"📁 Found {len(images)} images in {folder} (alphabetical order)")
    for img in images:
        logger.info(f"   {img.name}")

    # Load metadata if available
    metadata_path = folder / "animated_character_story.json"
    metadata = None
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text())
        logger.info(f"📝 Loaded metadata from {metadata_path.name}")

    # Create output folder
    videos_folder = folder / "videos"
    if not args.dry_run:
        videos_folder.mkdir(exist_ok=True)

    # Generate videos for consecutive pairs
    pairs = list(zip(images[:-1], images[1:]))
    logger.info(f"\n🎬 Generating {len(pairs)} video clips:")

    success_count = 0
    for i, (img1, img2) in enumerate(pairs, 1):
        output_name = f"clip_{i:02d}_{img1.stem}_to_{img2.stem}.mp4"
        output_path = videos_folder / output_name

        # Get prompt
        prompt = args.prompt or get_prompt_for_pair(metadata, img1.name, img2.name)

        logger.info(f"\n[{i}/{len(pairs)}] {img1.name} → {img2.name}")
        if prompt:
            logger.info(f"   Prompt: {prompt[:60]}...")

        if args.dry_run:
            logger.info(f"   Would save: {output_path}")
            continue

        if generate_video_clip(
            first_image=img1,
            last_image=img2,
            output_path=output_path,
            prompt=prompt,
            fps=args.fps,
            num_frames=args.frames,
            resolution=args.resolution,
        ):
            success_count += 1

    if not args.dry_run:
        logger.info(f"\n✅ Generated {success_count}/{len(pairs)} video clips")
        logger.info(f"📂 Output: {videos_folder}")


if __name__ == "__main__":
    main()
