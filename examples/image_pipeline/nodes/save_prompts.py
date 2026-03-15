"""Save generated prompts to a text file, one per line."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

OUTPUT_BASE = Path("outputs/image_pipeline")


def save_prompts_node(state: dict) -> dict:
    """Save prompts to a text file, one per line.

    Creates a timestamped output directory under outputs/image_pipeline/
    and writes prompts.txt compatible with zimage-replicate.mjs format.

    Args:
        state: Graph state with 'prompts' list

    Returns:
        State update with 'prompt_file' path and 'output_dir' path

    Raises:
        ValueError: If no prompts are provided
    """
    prompts = state.get("prompts") or []
    if not prompts:
        raise ValueError("No prompts to save")

    # Handle both list[str] and list[dict] with 'prompt_text' key
    prompt_texts = []
    for p in prompts:
        if isinstance(p, dict):
            prompt_texts.append(p.get("prompt_text", str(p)))
        else:
            prompt_texts.append(str(p))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = OUTPUT_BASE / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    prompt_file = output_dir / "prompts.txt"
    prompt_file.write_text("\n".join(prompt_texts) + "\n")

    logger.info(f"📝 Saved {len(prompts)} prompts to {prompt_file}")

    return {"prompt_file": str(prompt_file), "output_dir": str(output_dir)}
