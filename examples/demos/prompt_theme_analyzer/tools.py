"""FR-402 Prompt Theme Analyzer demo tools."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

MAX_PROMPT_CHARS = 2000
DEFAULT_REPORT_PATH = "outputs/prompt-theme-report.md"


def list_prompts(state: dict) -> dict:
    """Scan source_dir for prompts.txt files and normalize boundary input."""
    source_dir_value = state.get("source_dir")
    if not isinstance(source_dir_value, str) or not source_dir_value.strip():
        raise ValueError("source_dir is required")

    source_dir = Path(source_dir_value)
    if not source_dir.exists():
        raise FileNotFoundError(f"source_dir does not exist: {source_dir}")
    if not source_dir.is_dir():
        raise NotADirectoryError(f"source_dir is not a directory: {source_dir}")

    prompt_entries: list[dict[str, str]] = []
    for prompts_file in sorted(source_dir.glob("*/prompts.txt")):
        text = prompts_file.read_text(encoding="utf-8", errors="replace").strip()

        if not text or len(text) < 50:
            continue
        if text.startswith("{"):
            continue

        lowered = text.lower()
        if lowered.startswith("i'm sorry") or lowered.startswith("i am sorry"):
            continue

        prompt_entries.append(
            {
                "timestamp": prompts_file.parent.name,
                "text": text[:MAX_PROMPT_CHARS],
            }
        )

    return {"prompt_entries": prompt_entries}


def aggregate_themes(state: dict) -> dict:
    """Deterministically aggregate per-item themes into sorted counts."""
    classifications = state.get("classifications")
    if not isinstance(classifications, list):
        raise ValueError("classifications must be a list")

    counts: Counter[str] = Counter()
    for item in classifications:
        if not isinstance(item, dict):
            continue
        theme_raw = item.get("theme")
        if not isinstance(theme_raw, str):
            continue

        theme = " ".join(theme_raw.split()).strip()
        if not theme:
            continue

        counts[theme] += 1

    theme_counts = [
        {"theme": theme, "count": count}
        for theme, count in sorted(
            counts.items(), key=lambda it: (-it[1], it[0].lower())
        )
    ]
    return {"theme_counts": theme_counts}


def write_report(state: dict) -> dict:
    """Write deterministic theme counts and grouped clusters as markdown."""
    theme_counts = state.get("theme_counts")
    if not isinstance(theme_counts, list):
        raise ValueError("theme_counts must be a list")

    theme_groups = state.get("theme_groups")
    if hasattr(theme_groups, "model_dump"):
        theme_groups = theme_groups.model_dump()
    if not isinstance(theme_groups, dict):
        raise ValueError("theme_groups must be a dict")

    output_path_value = state.get("output_path", DEFAULT_REPORT_PATH)
    if not isinstance(output_path_value, str) or not output_path_value.strip():
        raise ValueError("output_path must be a non-empty string")

    lines = [
        "# Prompt Theme Analysis Report",
        "",
        "## Deterministic Theme Counts",
        "",
        "| Theme | Count |",
        "| --- | ---: |",
    ]

    if theme_counts:
        for item in theme_counts:
            if not isinstance(item, dict):
                continue
            theme = item.get("theme")
            count = item.get("count")
            if isinstance(theme, str) and isinstance(count, int):
                lines.append(f"| {theme} | {count} |")
    else:
        lines.append("| _No themes classified_ | 0 |")

    lines.extend(["", "## LLM Grouped Theme Clusters", ""])

    grouped_markdown = theme_groups.get("grouped_themes_markdown")
    if isinstance(grouped_markdown, str) and grouped_markdown.strip():
        lines.append(grouped_markdown.strip())
    else:
        lines.append("_No groups returned by the LLM._")

    total_classified = theme_groups.get("total_classified")
    if isinstance(total_classified, int):
        lines.extend(["", f"Total classified prompts: **{total_classified}**"])

    report = "\n".join(lines).rstrip() + "\n"
    output_path = Path(output_path_value)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    return {
        "report": report,
        "output_path": str(output_path),
    }
