"""FR-722 catalog loader — clusters for the map fan-out (REQ-YG-549)."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import yaml

DEFAULT_CATALOG = (
    Path(__file__).resolve().parents[1] / "data" / "icpc2_rfe_catalog.yaml"
)


def load_rfe_catalog(state: dict) -> list[dict]:
    """Load the catalog and group rows into chapter×component clusters.

    Provisional rows are excluded unless ``include_provisional`` is set
    (Judgement F6: production mode defaults to verified-only). A missing
    catalog names the build step (A1: the example is usable only after
    the user-run generation).
    """
    path = Path(state.get("catalog_path") or DEFAULT_CATALOG)
    if not path.exists():
        raise FileNotFoundError(
            f"Catalog not found: {path}. Generate it first: "
            "python examples/icpc-2-rfe/nodes/build_catalog.py "
            "(downloads ICPC-2e-v7.0 under YOUR acceptance of Wonca terms)"
        )
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    include_provisional = bool(state.get("include_provisional"))

    clusters: dict[str, list[dict]] = defaultdict(list)
    for row in payload["rows"]:
        if row["provenance_status"] != "verified" and not include_provisional:
            continue
        clusters[row["cluster_id"]].append(row)

    return [
        {
            "cluster_id": cluster_id,
            "catalog_version": payload["catalog_version"],
            "codes": rows,
            "brief": _brief(rows),
        }
        for cluster_id, rows in sorted(clusters.items())
    ]


def _brief(rows: list[dict]) -> str:
    """Render a cluster's code list for the prompt — formatting is
    mechanizable, so it lives in code, not in the model's job."""
    lines = []
    for row in rows:
        parts = [f"{row['code']} — {row['title']}"]
        if row.get("inclusion_terms"):
            parts.append(f"includes: {'; '.join(row['inclusion_terms'])}")
        if row.get("exclusion_terms"):
            parts.append(f"excludes: {'; '.join(row['exclusion_terms'])}")
        if row.get("official_definition_or_note"):
            parts.append(row["official_definition_or_note"])
        lines.append(" | ".join(parts))
    return "\n".join(lines)
