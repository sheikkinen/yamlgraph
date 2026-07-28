"""Load an existing prompt file into a list, one prompt per nonblank line.

FR-764 (R-1, binding input contract): reads ``state["input_file"]`` as UTF-8
text, treats each nonblank line as one prompt, strips only a leading decimal
enumerator of the form ``N. `` (a run of digits, a dot, then whitespace),
preserves all other prompt text verbatim, and raises ``ValueError`` when the
file is missing or yields zero prompts. It never writes to the input file.

Out of scope (frozen by judgement): blank-line paragraph parsing, multi-line
prompts, and named-style lookup tables.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Leading decimal enumerator: optional indent, digits, a dot, then whitespace.
# Only a "N. " prefix (with trailing whitespace/content) is stripped; a bare
# "19." with nothing after it is preserved as-is.
_ENUMERATOR = re.compile(r"^\s*\d+\.\s+")


def _parse_prompts(text: str) -> list[str]:
    prompts: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = _ENUMERATOR.sub("", line, count=1).strip()
        if line:
            prompts.append(line)
    return prompts


def load_prompts_node(state: dict) -> dict:
    """Read input_file into a prompts list (one prompt per nonblank line).

    Args:
        state: Graph state with 'input_file' path.

    Returns:
        State update ``{"source_prompts": [...]}``.

    Raises:
        ValueError: If 'input_file' is missing, the file does not exist, or the
            file yields zero prompts.
    """
    input_file = state.get("input_file")
    if not input_file:
        raise ValueError("load_prompts: 'input_file' is required")

    path = Path(input_file)
    if not path.is_file():
        raise ValueError(f"load_prompts: input file not found: {input_file}")

    prompts = _parse_prompts(path.read_text(encoding="utf-8"))
    if not prompts:
        raise ValueError(f"load_prompts: no prompts found in {input_file}")

    logger.info("📝 Loaded %d prompts from %s", len(prompts), input_file)
    return {"source_prompts": prompts}
