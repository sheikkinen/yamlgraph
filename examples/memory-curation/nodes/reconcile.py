#!/usr/bin/env python3
"""FR-875 reconcile stage: validate dispositions and render review artifacts.

Proves count-in == count-out over the frozen manifest (each path exactly
once, zero unknown verdicts), enforces cross-field invariants, and stamps
outputs with the manifest hash for the hash-bound apply gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, field_validator, model_validator


class Verdict(StrEnum):
    KEEP = "keep"
    REDACT = "redact"
    FORGET = "forget"


class Audience(StrEnum):
    PUBLIC = "public"
    PEER = "peer"
    CUSTOMER_PRIVATE = "customer_private"
    MACHINE_LOCAL = "machine_local"


class Staleness(StrEnum):
    FRESH = "fresh"
    DATED = "dated"
    EXPIRED = "expired"


class NoteDisposition(BaseModel):
    path: str
    verdict: Verdict
    audience: Audience
    rationale: str
    redacted_draft: str | None = None
    staleness: Staleness
    staleness_evidence: str | None = None

    @field_validator("rationale")
    @classmethod
    def rationale_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("rationale must be non-empty")
        return value

    @model_validator(mode="after")
    def cross_field_invariants(self) -> NoteDisposition:
        if self.verdict is Verdict.REDACT:
            if not (self.redacted_draft or "").strip():
                raise ValueError("redacted_draft required iff verdict=redact")
        elif self.redacted_draft:
            raise ValueError("redacted_draft only allowed for verdict=redact")
        if (
            self.staleness in (Staleness.DATED, Staleness.EXPIRED)
            and not (self.staleness_evidence or "").strip()
        ):
            raise ValueError("staleness_evidence required for dated/expired")
        return self


def reconcile(
    manifest_path: Path,
    dispositions_path: Path,
    out_dir: Path,
    premise_kind: str | None = None,
) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = json.loads(dispositions_path.read_text(encoding="utf-8"))
    validated: dict[str, NoteDisposition] = {}
    for row in rows:
        note = NoteDisposition.model_validate(row)
        if note.path in validated:
            raise ValueError(f"duplicate disposition for {note.path}")
        if note.path not in manifest["notes"]:
            raise ValueError(f"disposition for unknown path {note.path}")
        validated[note.path] = note
    missing = set(manifest["notes"]) - set(validated)
    if missing:
        raise ValueError(f"notes without disposition: {sorted(missing)}")

    manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    disposition = {
        "version": 1,
        "manifest_sha256": manifest_sha,
        "notes": {
            key: validated[key].model_dump(mode="json", exclude={"path"})
            for key in sorted(validated)
        },
    }
    if premise_kind is not None:
        if premise_kind not in ("hygiene", "export_publication"):
            raise ValueError(f"invalid premise_kind: {premise_kind!r}")
        disposition["premise_kind"] = premise_kind
    (out_dir / "disposition.json").write_text(
        json.dumps(disposition, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "disposition.md").write_text(
        render_review(disposition), encoding="utf-8"
    )
    return disposition


def render_review(disposition: dict) -> str:
    lines = [
        "# Memory-corpus disposition (FR-875) — HUMAN REVIEW REQUIRED",
        "",
        f"Manifest: `{disposition['manifest_sha256']}`",
        "",
        "| note | verdict | audience | staleness | rationale |",
        "|---|---|---|---|---|",
    ]
    for key, note in disposition["notes"].items():
        lines.append(
            f"| {key} | {note['verdict']} | {note['audience']} |"
            f" {note['staleness']} | {note['rationale']} |"
        )
    lines += [
        "",
        "To approve, append a line (hashes from manifest.json/disposition.json):",
        "",
        "    SIGN-OFF: approved by <name> manifest=<sha256> disposition=<sha256>",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--dispositions", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument(
        "--premise-kind", choices=["hygiene", "export_publication"], default=None
    )
    args = parser.parse_args(argv)
    try:
        disposition = reconcile(
            Path(args.manifest),
            Path(args.dispositions),
            Path(args.out_dir),
            premise_kind=args.premise_kind,
        )
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"reconcile: {exc}", file=sys.stderr)
        return 1
    counts: dict[str, int] = {}
    for note in disposition["notes"].values():
        counts[note["verdict"]] = counts.get(note["verdict"], 0) + 1
    print(f"reconciled {len(disposition['notes'])} notes: {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
