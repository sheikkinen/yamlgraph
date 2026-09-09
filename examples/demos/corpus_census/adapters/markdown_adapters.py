"""FR-1033 bounded local-Markdown corpus adapters.

A separate module from ``corpus_adapters`` for the same reason
``diary_adapters`` is: adding these to the host module pushed it past the
450-line ceiling. Slot contract is unchanged — discover returns a list of
item refs, extract returns one item's text.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

MD_MAX_ITEMS = 200  # the graph's own map ceiling (graph.yaml max_map_items)
MD_MAX_CHARS = 65536  # covers the motivating corpus; larger files are rejected


def _require(state: dict[str, Any], key: str) -> str:
    value = state.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value


class MarkdownItemRef(BaseModel):
    """Byte identity of one Markdown file, frozen at discovery.

    The census slot contract passes items as strings, so this model is
    serialized to JSON and back. Extraction re-verifies both fields against
    the file on disk before decoding, so a ledger row is provably about the
    bytes that were judged rather than about a pathname.
    """

    model_config = ConfigDict(extra="forbid")

    path: str
    sha256: str
    bytes: int


def md_discover(state: dict[str, Any]) -> list[str]:
    """List every Markdown file in a bounded directory, with byte identity.

    Fails closed rather than returning a prefix: completeness is part of the
    census result, so an over-ceiling directory is the operator's problem to
    narrow, not ours to silently truncate (diary_discover sets the precedent).
    """
    folder = Path(_require(state, "source"))
    if not folder.is_dir():
        raise NotADirectoryError(f"md_discover: not a directory: {folder}")

    paths = [p for p in sorted(folder.glob("*.md")) if p.is_file()]
    if not paths:
        raise ValueError(f"md_discover: no markdown files in {folder}")
    if len(paths) > MD_MAX_ITEMS:
        raise ValueError(
            f"md_discover: {len(paths)} files exceeds the ceiling of "
            f"{MD_MAX_ITEMS}; narrow or shard the source ({folder}). "
            "Each shard is an independently complete run."
        )

    items = []
    for path in paths:
        raw = path.read_bytes()
        ref = MarkdownItemRef(
            path=str(path),
            sha256=hashlib.sha256(raw).hexdigest(),
            bytes=len(raw),
        )
        items.append(ref.model_dump_json())
    return items


def md_extract(state: dict[str, Any]) -> str:
    """Read one Markdown file, verifying it is the file discovery saw.

    Identity is checked on raw bytes before any decoding, so a mutated file
    raises rather than being judged. Oversize is rejected, never truncated: a
    truncated read yields a plausible ledger row describing a file's head while
    attributing the judgement to the whole file.
    """
    item = _require(state, "item")
    try:
        ref = MarkdownItemRef.model_validate_json(item)
    except ValidationError as exc:
        raise ValueError(f"md_extract: malformed item reference: {item!r}") from exc

    path = Path(ref.path)
    raw = path.read_bytes()  # FileNotFoundError propagates by design

    if len(raw) != ref.bytes:
        raise ValueError(
            f"md_extract: {path} changed since discovery: "
            f"bytes {len(raw)} != {ref.bytes}"
        )
    digest = hashlib.sha256(raw).hexdigest()
    if digest != ref.sha256:
        raise ValueError(
            f"md_extract: {path} changed since discovery: "
            f"sha256 {digest} != {ref.sha256}"
        )

    text = raw.decode("utf-8", errors="replace")
    if len(text) > MD_MAX_CHARS:
        raise ValueError(
            f"md_extract: {path} has {len(text)} characters, exceeding the "
            f"ceiling of {MD_MAX_CHARS}; this adapter does not cover it"
        )
    return text
