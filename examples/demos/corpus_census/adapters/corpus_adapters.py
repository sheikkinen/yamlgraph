"""Corpus adapters for the FR-892 proof configurations.

PDF library census (AC-08) and git history timeline census (AC-09).
Slot contract, matching the pipeline's python-node convention: functions
take the resolved state dict; discover returns a list of item refs,
extract returns one item's text content.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

MAX_ITEMS = 50
MAX_PAGES = 5
MAX_CHARS = 4000


def _require(state: dict[str, Any], key: str) -> str:
    value = state.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value


# --- PDF library (AC-08) -------------------------------------------------


def pdf_discover(state: dict[str, Any]) -> list[str]:
    """Enumerate PDF files in the source folder (bounded, sorted)."""
    folder = Path(_require(state, "source"))
    if not folder.is_dir():
        raise NotADirectoryError(f"pdf_discover: not a directory: {folder}")
    pdfs = [str(p) for p in sorted(folder.glob("*.pdf"))][:MAX_ITEMS]
    if not pdfs:
        raise ValueError(f"pdf_discover: no PDFs in {folder}")
    return pdfs


def pdf_extract(state: dict[str, Any]) -> str:
    """Extract text from the first MAX_PAGES pages of one PDF."""
    from pypdf import PdfReader

    item = _require(state, "item")
    reader = PdfReader(item)
    text = "\n".join(
        (page.extract_text() or "") for page in reader.pages[:MAX_PAGES]
    ).strip()[:MAX_CHARS]
    if not text:
        raise ValueError(f"pdf_extract: no extractable text in {item}")
    return text


# --- Git history timeline (AC-09) ----------------------------------------


def _git(repo: str, *argv: str) -> str:
    result = subprocess.run(  # noqa: S603 — fixed git argv, no shell
        ["git", "-C", repo, *argv],  # noqa: S607
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    return result.stdout


def git_discover(state: dict[str, Any]) -> list[str]:
    """Enumerate a bounded commit window. source format: '<repo>:<n>'."""
    source = _require(state, "source")
    repo, _, n = source.partition(":")
    window = min(int(n or "10"), MAX_ITEMS)
    shas = _git(repo, "log", f"-{window}", "--format=%H").split()
    if not shas:
        raise ValueError(f"git_discover: no commits in {repo}")
    # Item ref carries the repo so extract stays stateless: '<repo>@<sha>'
    return [f"{repo}@{sha}" for sha in shas]


def git_extract(state: dict[str, Any]) -> str:
    """One commit's subject, body, and diffstat."""
    item = _require(state, "item")
    repo, _, sha = item.partition("@")
    text = _git(repo, "show", "-s", "--format=%s%n%n%b", sha)
    stat = _git(repo, "show", "--stat", "--format=", sha)
    return (text + "\n" + stat).strip()[:MAX_CHARS]
