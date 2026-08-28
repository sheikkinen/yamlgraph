"""Read-only git metadata adapters for the pattern/model census demo."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

MAX_STAT_LINES = 40


def _require(state: dict[str, Any], key: str) -> str:
    value = state.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value.strip()


def _git(repo: str, *argv: str) -> str:
    result = subprocess.run(  # noqa: S603 - fixed git argv, no shell
        ["git", "-C", repo, *argv],  # noqa: S607
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    return result.stdout


def discover(state: dict[str, Any]) -> list[str]:
    """Return commit SHAs from the last twelve months, excluding merge commits."""
    source = _require(state, "source")
    if not Path(source).is_dir():
        raise NotADirectoryError(f"source is not a directory: {source}")
    shas = _git(
        source,
        "log",
        "--since=12 months ago",
        "--no-merges",
        "--pretty=format:%H",
    ).split()
    if not shas:
        raise ValueError(f"no commits found in {source}")
    return shas


def extract(state: dict[str, Any]) -> dict[str, str]:
    """Return bounded commit metadata only: repo, sha, date, subject, shortstat."""
    source = _require(state, "source")
    sha = _require(state, "item")
    if not Path(source).is_dir():
        raise NotADirectoryError(f"source is not a directory: {source}")
    output = _git(
        source,
        "show",
        "--stat",
        f"--stat-count={MAX_STAT_LINES}",
        "--format=%cI%n%s",
        sha,
    )
    lines = output.splitlines()
    if len(lines) < 2:
        raise ValueError(f"git show returned incomplete metadata for {sha}")
    shortstat = ""
    for line in reversed(lines[: MAX_STAT_LINES + 2]):
        stripped = line.strip()
        if stripped and (" changed" in stripped or "insertion" in stripped):
            shortstat = stripped
            break
    return {
        "repo": str(Path(source).resolve()),
        "sha": sha,
        "date": lines[0].strip(),
        "subject": lines[1].strip(),
        "shortstat": shortstat,
    }
