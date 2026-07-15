"""FR-733 catalog loader — view-699 category clusters (REQ-YG-558)."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import yaml

DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / "data" / "cwe_catalog.yaml"


def load_cwe_clusters(state: dict) -> dict:
    """Load the generated catalog; return the merged state dict
    ``{cwe_clusters, usage_index}`` (FR-734 F4).

    Multi-membership rows appear in every member cluster (judged pin;
    the reducer's per-code dedup keeps the best-ranked occurrence).
    Prohibited rows carry no memberships — stripped at build time (F3),
    they never reach a brief. ``usage_index`` covers ALL catalog rows
    (including Prohibited non-members) so the reducer can distinguish
    off-population citations from fabrications. A missing catalog names
    the build step.
    """
    path = Path(state.get("catalog_path") or DEFAULT_CATALOG)
    if not path.exists():
        raise FileNotFoundError(
            f"Catalog not found: {path}. Generate it first: "
            "python examples/cwe-classifier/nodes/build_catalog.py "
            "(downloads cwec_v4.20 — MITRE CWE, free with attribution)"
        )
    payload = yaml.safe_load(path.read_text())
    names = payload.get("categories") or {}

    clusters: dict[str, list[dict]] = defaultdict(list)
    for row in payload["rows"]:
        for cluster_id in row["cluster_ids"]:
            clusters[cluster_id].append(row)

    return {
        "cwe_clusters": [
            {
                "cluster_id": cluster_id,
                "name": names.get(cluster_id, ""),
                "catalog_version": payload["catalog_version"],
                "coverage": payload["coverage"],
                "codes": rows,
                "brief": _brief(rows),
            }
            for cluster_id, rows in sorted(clusters.items())
        ],
        "usage_index": {row["code"]: row["mapping_usage"] for row in payload["rows"]},
    }


def _brief(rows: list[dict]) -> str:
    """Description-only briefs (F4) — usage and abstraction are
    code-side disciplines, never the model's job."""
    return "\n".join(
        f"{row['code']} — {row['title']} | {row['description']}" for row in rows
    )
