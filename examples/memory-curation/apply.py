#!/usr/bin/env python3
"""FR-875 apply stage: execute human-approved selective amnesia.

Refuses without a sign-off line binding the manifest and disposition
hashes; refuses ALL mutation when any live file drifted from the frozen
manifest (validate-all-then-apply-all); idempotent on re-run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SIGN_OFF_RE = re.compile(
    r"^SIGN-OFF:.*manifest=([0-9a-f]{64}).*disposition=([0-9a-f]{64})", re.MULTILINE
)


class ApplyError(Exception):
    """Fatal apply refusal; message is the user-facing diagnostic."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_signoff(review: Path, manifest: Path, disposition: Path) -> None:
    match = SIGN_OFF_RE.search(review.read_text(encoding="utf-8"))
    if not match:
        raise ApplyError("no SIGN-OFF line in review file — human approval required")
    signed_manifest, signed_disposition = match.groups()
    if signed_manifest != sha256_file(manifest):
        raise ApplyError("SIGN-OFF manifest hash does not match manifest.json")
    if signed_disposition != sha256_file(disposition):
        raise ApplyError("SIGN-OFF disposition hash does not match disposition.json")


def plan_actions(
    disposition: dict, manifest: dict, memory_root: Path
) -> list[tuple[str, Path, str | None]]:
    """Validate every target against the frozen manifest; return actions.

    Refuses everything on any drift — no partial apply.
    """
    actions: list[tuple[str, Path, str | None]] = []
    for key, note in sorted(disposition["notes"].items()):
        frozen_sha = manifest["notes"][key]["sha256"]
        target = (memory_root / key).resolve()
        if not target.is_relative_to(memory_root.resolve()):
            raise ApplyError(f"path escapes memory root: {key}")
        verdict = note["verdict"]
        if verdict == "keep":
            continue
        if verdict == "forget":
            if not target.exists():
                continue  # already applied
            if sha256_file(target) != frozen_sha:
                raise ApplyError(f"drift: {key} changed after collection")
            actions.append(("forget", target, None))
        elif verdict == "redact":
            draft = note["redacted_draft"]
            if target.exists():
                live_sha = sha256_file(target)
                if live_sha == hashlib.sha256(draft.encode()).hexdigest():
                    continue  # already applied
                if live_sha != frozen_sha:
                    raise ApplyError(f"drift: {key} changed after collection")
            actions.append(("redact", target, draft))
    return actions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--disposition", required=True)
    parser.add_argument("--review", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--memory-root", required=True)
    args = parser.parse_args(argv)

    disposition_path = Path(args.disposition)
    manifest_path = Path(args.manifest)
    try:
        verify_signoff(Path(args.review), manifest_path, disposition_path)
        disposition = json.loads(disposition_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if disposition["manifest_sha256"] != sha256_file(manifest_path):
            raise ApplyError("disposition.json manifest hash does not match manifest")
        actions = plan_actions(disposition, manifest, Path(args.memory_root))
    except (ApplyError, OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"apply: refused: {exc}", file=sys.stderr)
        return 2

    forgotten = redacted = 0
    for verdict, target, draft in actions:
        if verdict == "forget":
            target.unlink()
            forgotten += 1
        else:
            target.write_text(draft, encoding="utf-8")
            redacted += 1
    kept = len(disposition["notes"]) - forgotten - redacted
    print(f"applied: {forgotten} forgotten, {redacted} redacted, {kept} kept/unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
