"""Shared document splitter (FR-773/FR-774, REQ-YG-577).

Splits a PDF into text chunks via poppler (pdfinfo/pdftotext), shaped
for map-node fan-out: ``{"chunks": [{"index", "text"}], "total"}``.
Pages can be batched into multi-page chunks (``pages_per_chunk``) and
sub-threshold chunks dropped (``min_chars``).

Failure contract (FR-773 C-3, FR-774 C-3): every failure raises
ValueError naming the failing condition — never a silent fallback and
never a success-shaped empty chunk list.
"""

import shutil
import subprocess
from pathlib import Path


def split_document(
    path: str,
    mode: str = "page",
    start: int | None = None,
    end: int | None = None,
    pages_per_chunk: int = 1,
    min_chars: int = 0,
) -> dict:
    """Split a PDF into text chunks of consecutive pages.

    Args:
        path: PDF file path.
        mode: Only "page" is supported.
        start: First page, 1-indexed (default 1).
        end: Last page, 1-indexed inclusive (default: last page).
        pages_per_chunk: Consecutive pages joined per chunk (default 1).
        min_chars: Drop chunks whose stripped text is shorter (default 0).

    Returns:
        {"chunks": [{"index": int, "text": str}, ...], "total": int}
        where index is 0-based within the returned selection and total
        is the whole document's page count.
    """
    if mode != "page":
        raise ValueError(
            f"Unsupported mode {mode!r}: only 'page' is supported "
            "(chapter/paragraph splitting is not implemented)"
        )
    if pages_per_chunk < 1:
        raise ValueError(f"pages_per_chunk must be >= 1, got {pages_per_chunk}")
    if min_chars < 0:
        raise ValueError(f"min_chars must be >= 0, got {min_chars}")
    if shutil.which("pdfinfo") is None or shutil.which("pdftotext") is None:
        raise ValueError(
            "pdfinfo/pdftotext not found — install poppler (brew install poppler)"
        )
    if not Path(path).is_file():
        raise ValueError(f"document not found: {path}")

    info = subprocess.run(
        ["pdfinfo", path], capture_output=True, text=True, check=False
    )
    if info.returncode != 0:
        raise ValueError(f"pdfinfo failed for {path}: {info.stderr.strip()}")

    total = _parse_page_count(info.stdout, path)
    first = start if start is not None else 1
    last = end if end is not None else total
    if not 1 <= first <= last <= total:
        raise ValueError(
            f"page range {first}..{last} out of bounds for {total}-page document"
        )

    chunks = []
    for first_page in range(first, last + 1, pages_per_chunk):
        last_page = min(first_page + pages_per_chunk - 1, last)
        text = subprocess.run(
            [
                "pdftotext",
                "-layout",
                "-f",
                str(first_page),
                "-l",
                str(last_page),
                path,
                "-",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if text.returncode != 0:
            raise ValueError(
                f"pdftotext failed for pages {first_page}-{last_page} of {path}: "
                f"{text.stderr.strip()}"
            )
        chunks.append(text.stdout)

    if all(not text.strip() for text in chunks):
        raise ValueError(
            f"no extractable text in {path} — scanned/image-only PDF? "
            "vision fallback is not implemented (FR-774 non-goal)"
        )
    kept = [text for text in chunks if len(text.strip()) >= min_chars]
    if not kept:
        raise ValueError(
            f"min_chars={min_chars} filtered out every chunk of {path} — "
            "lower the threshold or inspect the document"
        )
    return {
        "chunks": [{"index": i, "text": text} for i, text in enumerate(kept)],
        "total": total,
    }


def _parse_page_count(pdfinfo_output: str, path: str) -> int:
    for line in pdfinfo_output.splitlines():
        if line.startswith("Pages:"):
            try:
                return int(line.split(":", 1)[1].strip())
            except ValueError:
                break
    raise ValueError(f"could not parse page count from pdfinfo output for {path}")
