"""Save persona and scenario results as interlinked markdown files."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

OUTPUT_BASE = Path("outputs/persona_scenarios")


def _slugify(text: str) -> str:
    """Convert text to a URL/filename-safe slug."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40]


def _extract_field(item: object, field: str, fallback: str = "") -> str:
    """Extract a field from a dict or Pydantic model."""
    if hasattr(item, field):
        return getattr(item, field)
    if isinstance(item, dict):
        return item.get(field, fallback)
    return fallback


def _write_scenario_files(
    out: Path,
    persona_idx: int,
    scenarios: list[str],
) -> list[str]:
    """Write individual scenario markdown files.

    Args:
        out: Output directory
        persona_idx: 1-based persona index
        scenarios: List of scenario markdown strings

    Returns:
        List of written filenames
    """
    filenames = []
    for j, scenario_text in enumerate(scenarios, 1):
        # Extract title from scenario markdown
        title = _extract_scenario_title(str(scenario_text))
        slug = _slugify(title)
        fname = f"scenario-{persona_idx:02d}-{j:02d}-{slug}.md"
        (out / fname).write_text(str(scenario_text) + "\n")
        filenames.append(fname)
    return filenames


def _extract_scenario_title(text: str) -> str:
    """Extract a meaningful title from scenario markdown.

    Handles patterns like:
    - "# Morning Medication Check"
    - "# Title: Morning Medication Check"
    - "# Title\\nMorning Medication Check"
    - "**Title:** Morning Medication Check"
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for i, line in enumerate(lines):
        stripped = line.lstrip("#").strip()
        # Skip generic "Title" heading — use next line
        if stripped.lower() in ("title", "title:"):
            if i + 1 < len(lines):
                return lines[i + 1].lstrip("#").strip()
            continue
        # Handle "Title: Actual Title" or "**Title:** Actual Title"
        for prefix in ("title:", "**title:**", "**title**:"):
            if stripped.lower().startswith(prefix):
                return stripped[len(prefix) :].strip()
        # First real heading content
        if stripped:
            return stripped
    return "scenario"


def save_results(state: dict) -> dict:
    """Save personas and scenarios as interlinked markdown files.

    Creates a timestamped output directory with:
    - index.md linking to all personas
    - persona-NN-name.md linking to index and its scenarios
    - scenario-NN-MM-title.md linking back to parent persona

    Args:
        state: Graph state with 'personas', 'all_scenarios', 'product_analysis'

    Returns:
        State update with 'output_dir' path

    Raises:
        ValueError: If no personas are provided
    """
    personas = state.get("personas") or []
    all_scenarios = state.get("all_scenarios") or []
    product = state.get("product_analysis") or {}

    if not personas:
        raise ValueError("No personas to save")

    summary = _extract_field(product, "product_summary", "")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = OUTPUT_BASE / timestamp
    out.mkdir(parents=True, exist_ok=True)

    # Build persona file metadata
    persona_entries = []
    for i, persona in enumerate(personas, 1):
        name = _extract_field(persona, "name", f"persona-{i}")
        segment = _extract_field(persona, "segment", "")
        profile = _extract_field(persona, "profile", str(persona))
        slug = _slugify(name)
        fname = f"persona-{i:02d}-{slug}.md"
        persona_entries.append(
            {
                "idx": i,
                "name": name,
                "segment": segment,
                "profile": profile,
                "fname": fname,
            }
        )

    # Write index.md
    index_lines = [
        "# Personas & Scenarios\n",
        f"{summary}\n",
        "## Personas\n",
    ]
    for entry in persona_entries:
        index_lines.append(
            f"- [{entry['name']}]({entry['fname']}) — {entry['segment']}"
        )
    (out / "index.md").write_text("\n".join(index_lines) + "\n")

    # Write each persona + its scenarios
    for entry in persona_entries:
        i = entry["idx"]

        # Find matching scenario set by persona_name
        scenarios_list: list[str] = []
        for sc_set in all_scenarios:
            sc_persona = _extract_field(sc_set, "persona_name", "")
            if sc_persona == entry["name"]:
                raw = _extract_field(sc_set, "scenarios", [])
                scenarios_list = [str(s) for s in raw] if raw else []
                break
        # Fallback: positional alignment
        if not scenarios_list and i - 1 < len(all_scenarios):
            sc_set = all_scenarios[i - 1]
            raw = _extract_field(sc_set, "scenarios", [])
            scenarios_list = [str(s) for s in raw] if raw else []

        # Write scenario files
        scenario_fnames = _write_scenario_files(out, i, scenarios_list)

        # Persona file with forward links
        scenario_links = "\n".join(f"- [{sf}]({sf})" for sf in scenario_fnames)
        persona_content = (
            f"[← index](index.md)\n\n"
            f"# {entry['name']}\n\n"
            f"**Segment:** {entry['segment']}\n\n"
            f"{entry['profile']}\n\n"
            f"## Scenarios\n\n{scenario_links}\n"
        )
        (out / entry["fname"]).write_text(persona_content)

        # Add back-link header to each scenario file
        for sf in scenario_fnames:
            path = out / sf
            old = path.read_text()
            header = (
                f"[← {entry['name']}]({entry['fname']}) · " f"[← index](index.md)\n\n"
            )
            path.write_text(header + old)

    file_count = (
        1
        + len(persona_entries)
        + sum(len(_extract_field(sc, "scenarios", [])) for sc in all_scenarios)
    )
    logger.info(f"📝 Saved {file_count} files to {out}")

    return {"output_dir": str(out)}
