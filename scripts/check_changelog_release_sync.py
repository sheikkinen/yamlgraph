"""Fail commit if version bumped with orphaned changelog fragments.

Pre-commit gate (FR-192): Blocks commit when BOTH conditions are true:
  1. pyproject.toml version field changed in staged files
  2. changelog/unreleased/ contains *.md files (excluding .gitkeep)

This forces changelog freeze before version bump commits.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def check(
    diff_output: str | None = None,
    unreleased_dir: Path | None = None,
) -> int:
    """Check changelog release sync.

    Args:
        diff_output: Staged diff of pyproject.toml. If None, runs git diff.
        unreleased_dir: Path to changelog/unreleased/. If None, uses repo default.

    Returns:
        0 if commit is allowed, 1 if blocked.
    """
    if diff_output is None:
        result = subprocess.run(
            ["git", "diff", "--cached", "--", "pyproject.toml"],
            capture_output=True,
            text=True,
        )
        diff_output = result.stdout

    if 'version = "' not in diff_output:
        return 0  # No version change — nothing to gate

    if unreleased_dir is None:
        unreleased_dir = Path("changelog/unreleased")

    fragments = [f for f in unreleased_dir.glob("*.md") if f.name != ".gitkeep"]
    if fragments:
        print("❌ Version bump detected but changelog/unreleased/ has fragments:")
        for f in sorted(fragments):
            print(f"   • {f.name}")
        print()
        print("Freeze first:")
        print('  VERSION="X.Y.Z"')
        print('  mkdir -p "changelog/${VERSION}"')
        print('  mv changelog/unreleased/*.md "changelog/${VERSION}/"')
        print("  python scripts/aggregate_changelog.py > CHANGELOG.md")
        print()
        print("Or use: scripts/release.sh <VERSION>")
        return 1

    return 0


def main() -> int:
    """Entry point for pre-commit hook."""
    return check()


if __name__ == "__main__":
    sys.exit(main())
