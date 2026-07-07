"""Persist derived story artifacts and prefetch prior threads (FR-691).

Story artifacts are regenerable derived data, not canon — they live under
``story/`` beside ``canon/``. Gates run persist-then-fail: artifacts are written
before the verdict so a failing run still leaves reviewable evidence on disk.

Atomic writes (tempfile + os.replace); ``yaml.safe_dump(sort_keys=False)`` to
keep field order legible.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import yaml

_STORY_DIR = Path(__file__).parent.parent / "story"


def _dump(item: Any) -> dict[str, Any]:
    return item.model_dump() if hasattr(item, "model_dump") else dict(item)


def _extract(value: Any, key: str) -> list[Any]:
    """Lift an inner list out of an LLM wrapper object, model, or dict."""
    if value is None:
        return []
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    if isinstance(value, dict):
        return value.get(key, [])
    return value


def _atomic_write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as fh:
            yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def prefetch_prior_threads(state: dict[str, Any]) -> dict[str, Any]:
    """Read ids of any previously persisted threads for id-stability checking.

    Empty on the first run (no ``story/thread/`` dir yet), which makes the
    id-stability gate a no-op — exactly as the Judgement specified.
    """
    thread_dir = _STORY_DIR / "thread"
    prior_ids: list[str] = []
    if thread_dir.is_dir():
        for f in sorted(thread_dir.glob("*.yaml")):
            data = yaml.safe_load(f.read_text())
            if isinstance(data, dict) and "id" in data:
                prior_ids.append(data["id"])
    return {"prior_thread_ids": prior_ids}


def persist_threads_1a(state: dict[str, Any]) -> dict[str, Any]:
    """Write the synopsis-only threads (the diff's left side) to story/."""
    threads = [_dump(t) for t in _extract(state.get("threads_1a_raw"), "threads")]
    path = _STORY_DIR / "threads_1a.yaml"
    _atomic_write(path, {"threads": threads})
    return {"threads_1a": threads, "threads_1a_path": str(path)}


def persist_threads(state: dict[str, Any]) -> dict[str, Any]:
    """Write each reconciled final-union thread to story/thread/<id>.yaml.

    Unpacks the reconcile LLM wrapper ({threads, dropped}) into the canonical
    state keys the thread gates read.
    """
    result = state.get("reconcile_result")
    threads = [_dump(t) for t in _extract(result, "threads")]
    dropped = [_dump(d) for d in _extract(result, "dropped")]
    written: list[str] = []
    for data in threads:
        tid = data.get("id", f"thread_{len(written)}")
        path = _STORY_DIR / "thread" / f"{tid}.yaml"
        _atomic_write(path, data)
        written.append(str(path))
    return {
        "threads": threads,
        "dropped_threads": dropped,
        "thread_paths": written,
    }


def persist_throughlines(state: dict[str, Any]) -> dict[str, Any]:
    """Write each throughline to story/throughline/<character>.yaml."""
    throughlines = [
        _dump(tl) for tl in _extract(state.get("throughlines_raw"), "throughlines")
    ]
    written: list[str] = []
    for data in throughlines:
        char = data.get("character", f"char_{len(written)}")
        path = _STORY_DIR / "throughline" / f"{char}.yaml"
        _atomic_write(path, data)
        written.append(str(path))
    return {"throughlines": throughlines, "throughline_paths": written}
