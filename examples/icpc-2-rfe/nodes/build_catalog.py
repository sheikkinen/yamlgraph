"""FR-722 catalog builder — generates the ICPC-2 RFE catalog locally.

The catalog is a GENERATED artifact (Judgement A1): this script parses
the Tier-1 ICPC-2e-v7.0 ClaML file and emits
examples/icpc-2-rfe/data/icpc2_rfe_catalog.yaml, which is gitignored.
The Wonca-copyrighted source is downloaded by the USER under their own
acceptance of the terms — the repository redistributes nothing.

Usage:
    python examples/icpc-2-rfe/nodes/build_catalog.py [path/to/ICPC-2e-v7.0.zip]

Without an argument the script expects tmp/ICPC-2e-v7.0.zip (download it
from SOURCE_URL first).
"""

from __future__ import annotations

import hashlib
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import yaml

SOURCE_URL = (
    "https://www.helsedirektoratet.no/digitalisering-og-e-helse/"
    "helsefaglige-kodeverk/icpc/icpc-2e--english-version/_/attachment/inline/"
    "7c5c8e7f-8c5a-4a0d-97a7-49bb144a162c:"
    "22fb4d59b1033d44af1da42cb84897cb363f7136/ICPC-2e-v7.0.zip"
)
SOURCE_SHA256 = "bbf96476cf97d572c2ce6e8a0652b3ae7460bfa9f3502e345a2d0c2f851e6c22"
SOURCE_VERSION = "ICPC-2e-v7.0"
CLAML_MEMBER = "ICPC-2e-v7.0.xml"

# Phase 1 (FR-722, Judgement F1): components 1 (symptoms/complaints) and
# 7 (diseases) per chapter. Phase 2 (FR-724): shared process rubrics
# (components 2-6, ClaML chapter "-") join as PROC-C<n> clusters.
RFE_COMPONENTS = (1, 7)
PROCESS_COMPONENTS = (2, 3, 4, 5, 6)

CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "icpc2_rfe_catalog.yaml"

_RUBRIC_LIST_KINDS = {"inclusion": "inclusion_terms", "exclusion": "exclusion_terms"}
_RUBRIC_TEXT_KINDS = {"criteria", "note"}


def verify_source(zip_path: Path) -> None:
    """Refuse a source zip whose sha256 differs from the pin (A1)."""
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    if digest != SOURCE_SHA256:
        raise ValueError(
            f"sha256 mismatch for {zip_path}: got {digest}, expected "
            f"{SOURCE_SHA256}. Download {SOURCE_VERSION} from {SOURCE_URL}"
        )


def _label_text(rubric: ET.Element) -> str:
    label = rubric.find("Label")
    return "".join(label.itertext()).strip() if label is not None else ""


def _split_terms(text: str) -> list[str]:
    return [part.strip() for part in text.split(";") if part.strip()]


def parse_claml(xml_text: str) -> list[dict]:
    """Parse ClaML into catalog rows (REQ-YG-548).

    Component is derived from the SuperClass code suffix
    (``<chapter>.<component>``). Chapter headers are excluded. Chapter
    codes keep components 1/7 (FR-722); process codes (chapter ``-``,
    components 2-6) become chapter-independent ``PROC-C<n>`` clusters
    (FR-724). Provenance fields are assigned mechanically: the row is
    derived from the Tier-1 file itself.
    """
    root = ET.fromstring(xml_text)  # noqa: S314 — CONF-386
    rows: list[dict] = []
    for cls in root.findall(".//Class"):
        code = cls.get("code") or ""
        if cls.get("kind") == "chapter":
            continue
        super_cls = cls.find("SuperClass")
        if super_cls is None:
            continue
        chapter, _, comp_str = (super_cls.get("code") or "").partition(".")
        if not comp_str.isdigit():
            continue
        component = int(comp_str)
        if chapter == "-":
            if component not in PROCESS_COMPONENTS:
                continue
            cluster_id = f"PROC-C{component}"
        else:
            if component not in RFE_COMPONENTS:
                continue
            cluster_id = f"{chapter}-C{component}"

        row: dict = {
            "code": code,
            "title": "",
            "chapter": chapter,
            "component": component,
            "cluster_id": cluster_id,
            "official_definition_or_note": "",
            "inclusion_terms": [],
            "exclusion_terms": [],
            "source_tier": 1,
            "source_reference": f"{SOURCE_VERSION}/{code}",
            "provenance_status": "verified",
        }
        notes: list[str] = []
        for rubric in cls.findall("Rubric"):
            kind = rubric.get("kind") or ""
            text = _label_text(rubric)
            if kind == "preferred":
                row["title"] = text
            elif kind in _RUBRIC_LIST_KINDS:
                row[_RUBRIC_LIST_KINDS[kind]] = _split_terms(text)
            elif kind in _RUBRIC_TEXT_KINDS:
                notes.append(f"{kind}: {text}")
            elif kind == "icd10":
                row["icd10"] = text
        row["official_definition_or_note"] = " | ".join(notes)
        rows.append(row)
    return rows


def build_catalog(zip_path: Path, out_path: Path = CATALOG_PATH) -> Path:
    """Verify, parse, and emit the catalog YAML (gitignored)."""
    verify_source(zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        xml_text = zf.read(CLAML_MEMBER).decode("utf-8")
    rows = parse_claml(xml_text)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"catalog_version": SOURCE_VERSION, "rows": rows}
    out_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
    print(f"✓ {len(rows)} rubrics → {out_path}")
    return out_path


def main() -> None:
    zip_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("tmp/ICPC-2e-v7.0.zip")
    if not zip_path.exists():
        raise SystemExit(
            f"Source not found: {zip_path}\n"
            f"Download {SOURCE_VERSION} (Wonca copyright — your acceptance "
            f"of the terms) from:\n  {SOURCE_URL}"
        )
    build_catalog(zip_path)


if __name__ == "__main__":
    main()
