#!/usr/bin/env python3
"""Generate ARCHITECTURE.md capability sections from YAML registry.

Usage:
    python scripts/aggregate_capabilities.py           # update ARCHITECTURE.md
    python scripts/aggregate_capabilities.py --dry-run  # preview to stdout

Reads all capabilities/CAP-*.yaml files, generates a summary table and
detailed requirement sections, and writes them between generation markers
in ARCHITECTURE.md.

FR-178: Append-Only Capability Registry
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CAPABILITIES_DIR = REPO_ROOT / "capabilities"
ARCHITECTURE_MD = REPO_ROOT / "ARCHITECTURE.md"

BEGIN_MARKER = "<!-- BEGIN GENERATED CAPABILITIES -->"
END_MARKER = "<!-- END GENERATED CAPABILITIES -->"


def load_capabilities() -> list[dict]:
    """Load all capability YAML files, sorted by numeric ID."""
    capabilities = []
    for filepath in sorted(CAPABILITIES_DIR.glob("CAP-*.yaml")):
        with open(filepath) as f:
            data = yaml.safe_load(f)
        # Add numeric sort key
        match = re.search(r"CAP-(\d+)", str(data["id"]))
        data["_num"] = int(match.group(1)) if match else 0
        capabilities.append(data)
    capabilities.sort(key=lambda c: c["_num"])
    return capabilities


def generate_sections(capabilities: list[dict]) -> str:
    """Generate markdown content from capabilities list."""
    lines: list[str] = []

    # Summary table
    lines.append("### Capability Summary")
    lines.append("")
    lines.append("| # | Capability | Primary Modules | Requirements |")
    lines.append("|---|-----------|----------------|--------------|")

    for cap in capabilities:
        num = cap["_num"]
        name = cap["name"]
        modules = ", ".join(f"`{m}`" for m in cap.get("modules", [])[:4])
        if len(cap.get("modules", [])) > 4:
            modules += ", …"
        reqs = [r["id"] for r in cap.get("requirements", [])]
        req_str = _compact_req_range(reqs) if reqs else "—"
        lines.append(f"| {num} | CAP-{num} {name} | {modules} | {req_str} |")

    lines.append("")
    lines.append(
        "> Capability numbers are stable identifiers. Gaps (e.g. 27, 29, 52, 58) indicate retired capabilities."
    )
    lines.append("")

    # Detailed sections
    for cap in capabilities:
        num = cap["_num"]
        name = cap["name"]
        desc = cap.get("description", "").strip()
        fr = cap.get("fr", "legacy")
        reqs = cap.get("requirements", [])

        lines.append(f"### {num}. CAP-{num} {name}")
        lines.append("")
        if desc:
            lines.append(desc)
            lines.append("")
        if fr != "legacy":
            lines.append(f"**Feature Request:** {fr}")
            lines.append("")

        if reqs:
            lines.append("| Requirement | Description | Key Modules |")
            lines.append("|------------|-------------|-------------|")
            for req in reqs:
                req_id = req["id"]
                req_desc = req.get("description", "").strip().replace("|", "\\|")
                req_mods = ", ".join(f"`{m}`" for m in req.get("modules", []))
                lines.append(f"| {req_id} | {req_desc} | {req_mods} |")
            lines.append("")

    return "\n".join(lines)


def _compact_req_range(reqs: list[str]) -> str:
    """Compact a list of REQ-YG-XXX into range notation where possible."""
    nums = sorted(
        int(re.search(r"(\d+)$", r).group(1)) for r in reqs if re.search(r"(\d+)$", r)
    )
    if not nums:
        return "—"

    if len(nums) == 1:
        return f"REQ-YG-{nums[0]:03d}"

    # Check if it's a contiguous range
    if nums == list(range(nums[0], nums[-1] + 1)):
        return f"REQ-YG-{nums[0]:03d} – {nums[-1]:03d}"

    # Mixed: show first-last with gaps noted
    parts = []
    i = 0
    while i < len(nums):
        start = nums[i]
        while i + 1 < len(nums) and nums[i + 1] == nums[i] + 1:
            i += 1
        end = nums[i]
        if start == end:
            parts.append(f"{start:03d}")
        else:
            parts.append(f"{start:03d} – {end:03d}")
        i += 1

    return "REQ-YG-" + ", ".join(parts)


def update_architecture(content: str, dry_run: bool = False) -> str:
    """Insert generated content between markers in ARCHITECTURE.md."""
    text = ARCHITECTURE_MD.read_text()

    begin_idx = text.find(BEGIN_MARKER)
    end_idx = text.find(END_MARKER)

    if begin_idx == -1 or end_idx == -1:
        print("❌ Generation markers not found in ARCHITECTURE.md")
        print(f"   Expected: {BEGIN_MARKER}")
        print(f"   And: {END_MARKER}")
        sys.exit(1)

    # Replace content between markers
    new_text = (
        text[: begin_idx + len(BEGIN_MARKER)] + "\n\n" + content + "\n" + text[end_idx:]
    )

    if dry_run:
        print(content)
        return new_text

    ARCHITECTURE_MD.write_text(new_text)
    print(f"✅ Updated ARCHITECTURE.md ({len(content)} chars generated)")
    return new_text


def main() -> int:
    """Main entry point."""
    dry_run = "--dry-run" in sys.argv

    capabilities = load_capabilities()
    if not capabilities:
        print("❌ No capability files found")
        return 1

    content = generate_sections(capabilities)
    update_architecture(content, dry_run=dry_run)

    return 0


if __name__ == "__main__":
    sys.exit(main())
