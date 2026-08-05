"""Shared page renderer — PDF page → PNG via pdftoppm (FR-776, CAP-219).

`render_page()` renders exactly one page of a PDF to a PNG file and
returns `{"page": int, "image": str}`. It raises on every failure —
missing PDF, missing poppler binary, invalid page, nonzero exit, or
absent output — and never returns a partial payload; the tool_call
node owns the error envelope (FR-776 R-5).

Rendered PNGs are working artifacts: the default output directory is
`tmp/pages/` and outputs must never be committed (FR-776 C-7).

Requirements: poppler (`brew install poppler` / `apt install poppler-utils`).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

DEFAULT_DPI = 150


def render_page(
    path: str | Path,
    page: int,
    out_dir: str | Path = "tmp/pages",
    dpi: int = DEFAULT_DPI,
) -> dict:
    """Render a single PDF page to PNG with pdftoppm.

    Args:
        path: PDF file path.
        page: 1-indexed page number to render.
        out_dir: Directory for the PNG (default tmp/pages, never committed).
        dpi: Render resolution (default 150 — sufficient for transcription).

    Returns:
        {"page": page, "image": "<out_dir>/p<page>-<n>.png"}

    Raises:
        ValueError: page < 1, pdftoppm nonzero exit, or no PNG produced.
        FileNotFoundError: missing PDF or missing pdftoppm binary.
    """
    page = int(page)
    if page < 1:
        raise ValueError(f"Page must be >= 1, got {page}")

    pdf = Path(path)
    if not pdf.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf}")

    if shutil.which("pdftoppm") is None:
        raise FileNotFoundError(
            "pdftoppm not found — install poppler (brew install poppler)"
        )

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    prefix = out / f"p{page}"

    cmd = [
        "pdftoppm",
        "-png",
        "-r",
        str(dpi),
        "-f",
        str(page),
        "-l",
        str(page),
        str(pdf),
        str(prefix),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise ValueError(
            f"pdftoppm failed for page {page} of {pdf} "
            f"(exit {result.returncode}): {result.stderr.strip()}"
        )

    matches = sorted(out.glob(f"{prefix.name}-*.png"), key=lambda p: p.stat().st_mtime)
    if not matches:
        raise ValueError(f"pdftoppm produced no PNG output for page {page} of {pdf}")

    return {"page": page, "image": str(matches[-1])}
