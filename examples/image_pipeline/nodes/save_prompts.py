"""Save generated prompts to a text file, one per line."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

OUTPUT_BASE = Path("outputs/image_pipeline")


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

    # Extract all prompt texts, handling nested structures
    prompt_texts = _extract_prompt_texts(prompts)

    if not prompt_texts:
        raise ValueError("No prompt texts found in prompts")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = OUTPUT_BASE / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    prompt_file = output_dir / "prompts.txt"
    prompt_file.write_text("\n".join(prompt_texts) + "\n", encoding="utf-8")

    logger.info(f"📝 Saved {len(prompt_texts)} prompts to {prompt_file}")

    return {
        "prompt_file": str(prompt_file),
        "output_dir": str(output_dir),
        "prompt_texts": prompt_texts,
    }
