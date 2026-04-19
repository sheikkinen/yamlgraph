"""FR-254 Diary Index Graph — Python tools.

Three functions for the diary-index pipeline:
1. list_diary_files() — glob diary entries, return filename+content
2. aggregate_index() — deterministic cross-reference index from extractions
3. write_index() — persist index to YAML file
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

import yaml

DIARY_DIR = Path("docs/diary")


def list_diary_files(state: dict) -> dict:  # noqa: ARG001
    """List all diary .md files with their content.

    Args:
        state: Graph state (unused — no inputs needed)

    Returns:
        Dict with diary_files: list of {filename, content} dicts
    """
    files = sorted(DIARY_DIR.glob("*.md"))
    diary_files = [
        {"filename": f.name, "content": f.read_text(encoding="utf-8")} for f in files
    ]
    return {"diary_files": diary_files}


def aggregate_index(state: dict) -> dict:
    """Deterministically aggregate extractions into a cross-reference index.

    Args:
        state: Graph state with extractions list

    Returns:
        Dict with index containing entries, traps_index, seeds_index,
        fr_index, heuristics_candidates, and statistics
    """
    extractions: list[dict] = state["extractions"]

    # Per-entry metadata
    entries = [
        {
            "filename": e["filename"],
            "date": e.get("date", ""),
            "title": e.get("title", ""),
            "category": e.get("category", "other"),
            "traps": e.get("traps", []),
            "heuristics": e.get("heuristics", []),
            "seeds": e.get("seeds", []),
            "fr_references": e.get("fr_references", []),
        }
        for e in extractions
    ]

    # Traps index: trap → filenames, sorted by count desc
    trap_to_files: defaultdict[str, list[str]] = defaultdict(list)
    for e in extractions:
        for trap in e.get("traps", []):
            trap_to_files[trap].append(e["filename"])

    traps_index = sorted(
        [
            {"trap": trap, "count": len(fnames), "filenames": sorted(fnames)}
            for trap, fnames in trap_to_files.items()
        ],
        key=lambda x: (-x["count"], x["trap"]),
    )

    # Seeds index: seed → filenames, sorted by count desc
    seed_to_files: defaultdict[str, list[str]] = defaultdict(list)
    for e in extractions:
        for seed in e.get("seeds", []):
            seed_to_files[seed].append(e["filename"])

    seeds_index = sorted(
        [
            {"seed": seed, "count": len(fnames), "filenames": sorted(fnames)}
            for seed, fnames in seed_to_files.items()
        ],
        key=lambda x: (-x["count"], x["seed"]),
    )

    # FR reverse index: FR-XXX → filenames
    fr_to_files: defaultdict[str, list[str]] = defaultdict(list)
    for e in extractions:
        for fr in e.get("fr_references", []):
            fr_to_files[fr].append(e["filename"])

    fr_index = sorted(
        [
            {"fr": fr, "count": len(fnames), "filenames": sorted(fnames)}
            for fr, fnames in fr_to_files.items()
        ],
        key=lambda x: (-x["count"], x["fr"]),
    )

    # Heuristics candidates: appearing 2+ times
    heuristic_counts: Counter[str] = Counter()
    heuristic_to_files: defaultdict[str, list[str]] = defaultdict(list)
    for e in extractions:
        for h in e.get("heuristics", []):
            heuristic_counts[h] += 1
            heuristic_to_files[h].append(e["filename"])

    heuristics_candidates = sorted(
        [
            {
                "heuristic": h,
                "count": count,
                "filenames": sorted(heuristic_to_files[h]),
            }
            for h, count in heuristic_counts.items()
            if count >= 2
        ],
        key=lambda x: (-x["count"], x["heuristic"]),
    )

    # Statistics
    all_traps = {t for e in extractions for t in e.get("traps", [])}
    all_seeds = {s for e in extractions for s in e.get("seeds", [])}
    all_frs = {fr for e in extractions for fr in e.get("fr_references", [])}

    category_counts: Counter[str] = Counter()
    for e in extractions:
        category_counts[e.get("category", "other")] += 1

    statistics = {
        "total_entries": len(extractions),
        "total_unique_traps": len(all_traps),
        "total_unique_seeds": len(all_seeds),
        "total_unique_frs": len(all_frs),
        "entries_by_category": dict(sorted(category_counts.items())),
    }

    index = {
        "entries": entries,
        "traps_index": traps_index,
        "seeds_index": seeds_index,
        "fr_index": fr_index,
        "heuristics_candidates": heuristics_candidates,
        "statistics": statistics,
    }

    return {"index": index}


def write_index(state: dict) -> dict:
    """Write the final index to a YAML file.

    Args:
        state: Graph state with index dict and output_path

    Returns:
        Dict with output_path
    """
    index = state["index"]
    output_path = Path(state.get("output_path", "docs/diary-index.yaml"))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        yaml.dump(index, default_flow_style=False, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    return {"output_path": str(output_path)}
