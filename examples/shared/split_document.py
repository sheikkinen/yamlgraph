"""Shared document splitter (FR-773, REQ-YG-577).

Splits a PDF into per-page text chunks via poppler (pdfinfo/pdftotext),
shaped for map-node fan-out: ``{"chunks": [{"index", "text"}], "total"}``.

Failure contract (judgement C-3): every failure raises ValueError naming
the failing condition — never a silent fallback to all pages.
"""

import shutil
import subprocess
from pathlib import Path


def split_document(
    path: str,
    mode: str = "page",
    start: int | None = None,
    end: int | None = None,
) -> dict:
    """Split a PDF into text chunks, one per selected page.

    Args:
        path: PDF file path.
        mode: Only "page" is supported.
        start: First page, 1-indexed (default 1).
        end: Last page, 1-indexed inclusive (default: last page).

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
    for offset, page in enumerate(range(first, last + 1)):
        text = subprocess.run(
            ["pdftotext", "-layout", "-f", str(page), "-l", str(page), path, "-"],
            capture_output=True,
            text=True,
            check=False,
        )
        if text.returncode != 0:
            raise ValueError(
                f"pdftotext failed for page {page} of {path}: " f"{text.stderr.strip()}"
            )
        chunks.append({"index": offset, "text": text.stdout})
    return {"chunks": chunks, "total": total}


def _parse_page_count(pdfinfo_output: str, path: str) -> int:
    for line in pdfinfo_output.splitlines():
        if line.startswith("Pages:"):
            try:
                return int(line.split(":", 1)[1].strip())
            except ValueError:
                break
    raise ValueError(f"could not parse page count from pdfinfo output for {path}")
