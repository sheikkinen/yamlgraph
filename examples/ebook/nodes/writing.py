"""Chapter writing tools for eBook authoring pipeline.

FR-100: YAMLGraph Development Pipeline eBook.
REQ-YG-091: write_chapters_tool writes formatted chapter content to disk.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Chapter mapping: state key -> filename
CHAPTER_MAP = {
    "chapter_introduction": "00-introduction.md",
    "chapter_doctrine": "01-doctrine.md",
    "chapter_precommit": "02-precommit-gates.md",
    "chapter_chaplain": "03-chaplain-pipeline.md",
    "chapter_inquisitor": "04-inquisitor.md",
    "chapter_diary": "05-diary-system.md",
}


def write_chapters_tool(state: dict) -> dict:
    """Write all chapter content to the output directory.

    Reads chapter content from state variables (chapter_introduction,
    chapter_doctrine, etc.) and writes each to the appropriate file
    in output_dir.

    Args:
        state: Graph state containing:
            - output_dir: Target directory for chapter files
            - chapter_introduction: Content for 00-introduction.md
            - chapter_doctrine: Content for 01-doctrine.md
            - chapter_precommit: Content for 02-precommit-gates.md
            - chapter_chaplain: Content for 03-chaplain-pipeline.md
            - chapter_inquisitor: Content for 04-inquisitor.md
            - chapter_diary: Content for 05-diary-system.md

    Returns:
        dict with 'written' key containing list of written file paths
    """
    output_dir = Path(state.get("output_dir", "docs/ebook"))
    output_dir.mkdir(parents=True, exist_ok=True)

    written = []

    for state_key, filename in CHAPTER_MAP.items():
        content = state.get(state_key)

        # Skip empty or missing chapters
        if not content:
            logger.info("Skipping %s — no content", filename)
            continue

        filepath = output_dir / filename
        filepath.write_text(content)
        written.append(str(filepath))
        logger.info("Wrote %s", filepath)

    return {"written": written}


def persist_chapter(state: dict) -> dict:
    """Persist a single chapter to disk.

    FR-103: Per-chapter persistence for resumability.

    Args:
        state: Graph state containing:
            - content: Chapter content to write
            - filename: Target filename (e.g., "01-doctrine.md")
            - output_dir: Target directory (default: docs/ebook/)

    Returns:
        dict with 'persisted' key containing the filepath
    """
    content = state.get("content", "")
    filename = state.get("filename", "chapter.md")
    output_dir = Path(state.get("output_dir", "docs/ebook"))

    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / filename
    filepath.write_text(content)

    logger.info("Persisted %s", filepath)
    return {"persisted": str(filepath)}
