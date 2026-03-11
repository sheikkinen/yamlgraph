#!/usr/bin/env python3
"""Migrate monolithic CHANGELOG.md into fragment files under changelog/.

Usage:
    python scripts/migrate_changelog.py [changelog_md_path] [output_dir]

Parses each versioned section and individual entries from CHANGELOG.md,
writes fragment files to changelog/{version}/ and changelog/unreleased/.

FR-179: Append-Only Changelog Fragments
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Section heading → fragment type
SECTION_TYPE_MAP: dict[str, str] = {
    "Added": "feat",
    "Fixed": "fix",
    "Removed": "removal",
    "Changed": "feat",
    "Security": "feat",
}


def _slugify(text: str) -> str:
    """Convert text to kebab-case slug."""
    result = re.sub(r"[^a-zA-Z0-9]+", "-", text)
    result = re.sub(r"-+", "-", result)
    return result.strip("-").lower()


def _extract_fr_num(line: str) -> str | None:
    """Extract FR-XXX from an entry line."""
    match = re.search(r"FR-(\d+)", line)
    return f"FR-{match.group(1)}" if match else None


def _extract_req(line: str) -> str | None:
    """Extract REQ-YG-XXX from an entry line."""
    match = re.search(r"REQ-YG-(\d+)", line)
    return f"REQ-YG-{match.group(1)}" if match else None


def _extract_scope(line: str) -> str:
    """Best-effort scope extraction from entry text."""
    # Try to find scope from the FR title pattern: **FR-XXX Scope Thing**
    match = re.search(r"\*\*(?:FR-\d+\s+)?([^*:]+)", line)
    if match:
        title = match.group(1).strip()
        # First word as scope (lowercase), strip non-alphanumeric
        first_word = title.split()[0].lower() if title.split() else ""
        first_word = re.sub(r"[^a-z0-9-]", "", first_word)
        return first_word
    return ""


def _make_fragment(
    entry_type: str, scope: str, req: str | None, body: str
) -> str:
    """Build fragment file content with YAML front matter."""
    lines = ["---"]
    lines.append(f"type: {entry_type}")
    lines.append(f"scope: {scope}")
    if req:
        lines.append(f"req: {req}")
    lines.append("---")
    lines.append(body)
    lines.append("")
    return "\n".join(lines)


def _parse_entries(
    changelog_text: str,
) -> list[tuple[str, str, str]]:
    """Parse CHANGELOG.md into (version, section_type, entry_line) tuples.

    version is 'unreleased' or a semver string.
    section_type is 'feat', 'fix', 'removal', etc.
    entry_line is the raw markdown line.
    """
    entries: list[tuple[str, str, str]] = []
    current_version: str | None = None
    current_section_type: str | None = None

    for line in changelog_text.splitlines():
        # Version headers: ## [Unreleased] or ## [0.4.61] — 2026-03-08
        version_match = re.match(r"^## \[([^\]]+)\]", line)
        if version_match:
            ver = version_match.group(1)
            current_version = "unreleased" if ver.lower() == "unreleased" else ver
            current_section_type = None
            continue

        # Section headers: ### Added, ### Fixed, ### Removed, etc.
        section_match = re.match(r"^### (\w+)", line)
        if section_match:
            section_name = section_match.group(1)
            current_section_type = SECTION_TYPE_MAP.get(section_name)
            continue

        # Entry lines: start with "- "
        if (
            line.startswith("- ")
            and current_version is not None
            and current_section_type is not None
        ):
            entries.append((current_version, current_section_type, line))
        # Continuation lines (indented, part of multi-line entries)
        elif (
            line.startswith("  ")
            and entries
            and entries[-1][0] == current_version
        ):
            # Append to previous entry
            prev_ver, prev_type, prev_line = entries[-1]
            entries[-1] = (prev_ver, prev_type, prev_line + "\n" + line)

    return entries


def migrate(changelog_path: Path, output_dir: Path) -> int:
    """Migrate CHANGELOG.md into fragment files.

    Returns the number of fragments written.
    """
    text = changelog_path.read_text()
    entries = _parse_entries(text)

    # Track used filenames to avoid collisions
    used_names: set[str] = set()
    count = 0

    for version, entry_type, entry_line in entries:
        version_dir = output_dir / version
        version_dir.mkdir(parents=True, exist_ok=True)

        fr_num = _extract_fr_num(entry_line)
        req = _extract_req(entry_line)
        scope = _extract_scope(entry_line)

        # Determine filename
        if fr_num:
            # Extract title slug from entry
            title_match = re.search(r"\*\*(?:FR-\d+\s+)?([^*:]+)", entry_line)
            title = title_match.group(1).strip() if title_match else ""
            slug = _slugify(title)[:40]
            base_name = f"{fr_num}-{slug}" if slug else fr_num
        else:
            # No FR number — use first few words as slug
            clean = re.sub(r"\*\*([^*]+)\*\*", r"\1", entry_line)
            clean = clean.lstrip("- ").strip()
            slug = _slugify(clean[:60])
            base_name = slug or "entry"

        # De-duplicate filenames
        filename = f"{base_name}.md"
        if filename in used_names:
            i = 2
            while f"{base_name}-{i}.md" in used_names:
                i += 1
            filename = f"{base_name}-{i}.md"
        used_names.add(filename)

        fragment_content = _make_fragment(entry_type, scope, req, entry_line)
        (version_dir / filename).write_text(fragment_content)
        count += 1

    # Ensure unreleased directory always exists
    (output_dir / "unreleased").mkdir(parents=True, exist_ok=True)

    return count


def main() -> int:
    """Main entry point."""
    changelog_path = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "CHANGELOG.md"
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO_ROOT / "changelog"

    if not changelog_path.exists():
        print(f"❌ CHANGELOG.md not found: {changelog_path}", file=sys.stderr)
        return 1

    count = migrate(changelog_path, output_dir)
    print(f"✅ Migrated {count} entries to {output_dir}/")

    # Create .gitkeep in unreleased
    gitkeep = output_dir / "unreleased" / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()
        print(f"   Created {gitkeep}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
