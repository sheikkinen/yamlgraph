"""FR-733 catalog builder — generates the CWE catalog locally.

The catalog is a GENERATED artifact: this script parses the Tier-1
cwec_v4.20.xml (MITRE CWE, free with attribution) and emits
examples/cwe-classifier/data/cwe_catalog.yaml, which is gitignored.
The pin is the VERSIONED zip — cwec_latest.xml.zip is a moving pointer
and violates the refusal contract.

Usage:
    python examples/cwe-classifier/nodes/build_catalog.py [path/to/cwec_v4.20.xml.zip]

Without an argument the script expects tmp/cwec_v4.20.xml.zip (download
it from SOURCE_URL first).
"""

from __future__ import annotations

import hashlib
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import yaml

SOURCE_URL = "https://cwe.mitre.org/data/xml/cwec_v4.20.xml.zip"
SOURCE_SHA256 = "3976f599e5e5200219a3108bb896d06e2a88fbb293369e1883cb423a5e9d7d50"
SOURCE_VERSION = "cwec_v4.20"
XML_MEMBER = "cwec_v4.20.xml"
VIEW_ID = "699"  # Software Development — the judged clustering facet

_NS = {"c": "http://cwe.mitre.org/cwe-7"}

CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "cwe_catalog.yaml"

# F5 two-level pins, verified against cwec_v4.20.xml at enforce
# (judgement correction: catalog-wide Prohibited is 58 LIVE rows — the
# proposal's 83 counted the 25 Deprecated rows the builder skips).
CATALOG_USAGE_PINS = {"Prohibited": 58, "Discouraged": 44, "Allowed-with-Review": 93}
POPULATION_USAGE_PINS = {"Prohibited": 54, "Discouraged": 5, "Allowed-with-Review": 13}


def verify_source(zip_path: Path) -> None:
    """Refuse a source zip whose sha256 differs from the versioned pin."""
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    if digest != SOURCE_SHA256:
        raise ValueError(
            f"sha256 mismatch for {zip_path}: got {digest}, expected "
            f"{SOURCE_SHA256}. Download {SOURCE_VERSION} from {SOURCE_URL}"
        )


def _text(el: ET.Element | None) -> str:
    return "".join(el.itertext()).strip() if el is not None else ""


def parse_cwec(xml_text: str) -> dict:
    """Parse cwec XML into the catalog payload (REQ-YG-557).

    Deprecated weaknesses are skipped. cluster_ids come from view-699
    Has_Member rows (multi-membership duplicates the code into every
    member cluster; other views never count). Prohibited codes keep
    their catalog row but receive NO cluster membership — candidacy is
    stripped at build time (F3), the model never sees them.
    """
    root = ET.fromstring(xml_text)  # noqa: S314 — CONF-387
    live: dict[str, dict] = {}
    for weakness in root.findall(".//c:Weakness", _NS):
        if weakness.get("Status") == "Deprecated":
            continue
        wid = weakness.get("ID") or ""
        usage = _text(weakness.find(".//c:Mapping_Notes/c:Usage", _NS)) or "Allowed"
        parents = sorted(
            {
                f"CWE-{rel.get('CWE_ID')}"
                for rel in weakness.findall(".//c:Related_Weakness", _NS)
                if rel.get("Nature") == "ChildOf"
            }
        )
        live[wid] = {
            "code": f"CWE-{wid}",
            "title": weakness.get("Name") or "",
            "abstraction": weakness.get("Abstraction") or "",
            "mapping_usage": usage,
            "description": _text(weakness.find("c:Description", _NS)),
            "parents": parents,
            "cluster_ids": [],
            "source_tier": 1,
            "source_reference": f"{SOURCE_VERSION}/CWE-{wid}",
        }

    categories: dict[str, str] = {}
    excluded_prohibited: set[str] = set()
    members: set[str] = set()
    for category in root.findall(".//c:Category", _NS):
        if category.get("Status") == "Deprecated":
            continue
        cat_id = category.get("ID") or ""
        for member in category.findall(".//c:Has_Member", _NS):
            if member.get("View_ID") != VIEW_ID:
                continue
            row = live.get(member.get("CWE_ID") or "")
            if row is None:
                continue  # Deprecated member
            members.add(row["code"])
            if row["mapping_usage"] == "Prohibited":
                excluded_prohibited.add(row["code"])
                continue
            categories[cat_id] = category.get("Name") or ""
            row["cluster_ids"].append(f"CAT-{cat_id}")

    return {
        "catalog_version": SOURCE_VERSION,
        "coverage": {
            "view": int(VIEW_ID),
            "candidates": len(members) - len(excluded_prohibited),
            "excluded_prohibited": len(excluded_prohibited),
            "catalog_total": len(live),
        },
        "categories": {f"CAT-{cid}": name for cid, name in sorted(categories.items())},
        "rows": list(live.values()),
    }


def check_pins(payload: dict) -> None:
    """F5: assert two-level usage counts — a catalog bump that shifts
    MITRE's curation must be loud, never a silent drift."""
    rows = payload["rows"]
    clustered = [r for r in rows if r["cluster_ids"]]
    for level, pins, pool in (
        ("catalog-wide", CATALOG_USAGE_PINS, rows),
        ("in-population", POPULATION_USAGE_PINS, clustered),
    ):
        counts = {
            usage: sum(1 for r in pool if r["mapping_usage"] == usage) for usage in pins
        }
        if level == "in-population":
            # Prohibited members were stripped at build — the count
            # survives only in the coverage block.
            counts["Prohibited"] = payload["coverage"]["excluded_prohibited"]
        if counts != pins:
            raise ValueError(
                f"usage pin mismatch ({level}): got {counts}, expected {pins} "
                f"— MITRE curation shifted; re-judge the caps before bumping"
            )


def build_catalog(zip_path: Path, out_path: Path = CATALOG_PATH) -> Path:
    """Verify, parse, pin-check, and emit the catalog YAML (gitignored)."""
    verify_source(zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        xml_text = zf.read(XML_MEMBER).decode("utf-8")
    payload = parse_cwec(xml_text)
    check_pins(payload)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
    cov = payload["coverage"]
    print(
        f"✓ {cov['catalog_total']} weaknesses, {cov['candidates']} candidates "
        f"in {len(payload['categories'])} view-{cov['view']} clusters "
        f"({cov['excluded_prohibited']} Prohibited stripped) → {out_path}"
    )
    return out_path


def main() -> None:
    zip_path = (
        Path(sys.argv[1]) if len(sys.argv) > 1 else Path("tmp/cwec_v4.20.xml.zip")
    )
    if not zip_path.exists():
        raise SystemExit(
            f"Source not found: {zip_path}\n"
            f"Download {SOURCE_VERSION} (MITRE CWE, free with attribution) from:\n"
            f"  {SOURCE_URL}"
        )
    build_catalog(zip_path)


if __name__ == "__main__":
    main()
