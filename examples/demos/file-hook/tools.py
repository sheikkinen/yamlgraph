"""File-hook demo tools (FR-781) — pairing scan, safe publish, confidence gate.

The `.md` twin IS the ledger: a PNG is unprocessed iff no `<base>.md`
exists beside it. Publication is fail-safe: only confidence == "high"
writes/renames; unsafe titles and collisions never overwrite or escape
the watched directory (judgement C-3, C-7).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import yaml

from examples.shared.vision_tool import describe_image

logger = logging.getLogger(__name__)

_PROMPT_FILE = Path(__file__).parent / "prompts" / "describe_artwork.yaml"


def _load_instruction() -> str:
    """Load the julkaisuohje-derived instruction from the prompt YAML."""
    data = yaml.safe_load(_PROMPT_FILE.read_text())
    return data["template"]


def find_unpaired(dir: str) -> list[str]:
    """Return PNGs in dir lacking an `.md` twin — the pairing ledger."""
    directory = Path(dir)
    unpaired = [
        str(png)
        for png in sorted(directory.glob("*.png"))
        if not png.with_suffix(".md").exists()
    ]
    logger.info("find_unpaired: %d unpaired PNG(s) in %s", len(unpaired), directory)
    return unpaired


def safe_basename(title: str) -> str | None:
    """Deterministic title -> basename; None when no safe name exists.

    Strips control characters, converts path separators to '-',
    collapses whitespace, and rejects empty/dot-only results so writes
    cannot escape the watched directory.
    """
    cleaned = re.sub(r"[\x00-\x1f\x7f]", "", title)
    cleaned = cleaned.replace("/", "-").replace("\\", "-")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = cleaned.strip(".")  # kills '.', '..', and hidden-file prefixes
    if not cleaned:
        return None
    return cleaned


def _dedupe(directory: Path, base: str, source: Path) -> str:
    """Numeric-suffix collision policy: never overwrite unrelated files."""
    candidate = base
    n = 1
    while True:
        md = directory / f"{candidate}.md"
        png = directory / f"{candidate}.png"
        if not md.exists() and (not png.exists() or png == source):
            return candidate
        n += 1
        candidate = f"{base}-{n}"


def _render_post(desc) -> str:
    tags = " ".join(f"#{t}" for t in desc.tags)
    parts = [f"# {desc.title}", "", desc.description, ""]
    if desc.quote:
        parts += [f"> {desc.quote}", ""]
    if tags:
        parts += [tags, ""]
    return "\n".join(parts)


def process_artwork(
    file: str,
    instruction: str | None = None,
    max_dim: int = 512,
    provider: str | None = None,
    model: str | None = None,
) -> dict:
    """Describe one PNG; publish `<safe-title>.md` + rename iff confidence high.

    Returns a typed result dict; blocked/error results leave the source
    PNG unmodified and write nothing (fail-safe boundary).
    """
    src = Path(file)
    desc = describe_image(
        src,
        instruction or _load_instruction(),
        provider=provider,
        model=model,
        max_dim=max_dim,
    )
    if desc.confidence != "high":
        logger.warning(
            "blocked: %s confidence=%s (only 'high' publishes)", src, desc.confidence
        )
        return {
            "file": str(src),
            "status": "blocked",
            "reason": f"confidence={desc.confidence}",
            "title": desc.title,
        }

    base = safe_basename(desc.title)
    if base is None:
        logger.error(
            "unsafe title for %s: %r — source left unmodified", src, desc.title
        )
        return {
            "file": str(src),
            "status": "error",
            "reason": f"unsafe title: {desc.title!r}",
        }

    directory = src.parent
    base = _dedupe(directory, base, source=src)
    md_path = directory / f"{base}.md"
    png_path = directory / f"{base}.png"

    md_path.write_text(_render_post(desc))
    if src != png_path:
        src.rename(png_path)
    logger.info("published: %s -> %s + %s", src.name, png_path.name, md_path.name)
    return {
        "file": str(src),
        "status": "published",
        "title": desc.title,
        "md": str(md_path),
        "png": str(png_path),
    }
