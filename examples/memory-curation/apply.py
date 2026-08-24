#!/usr/bin/env python3
"""FR-875/FR-878 apply stage: execute approved selective amnesia.

Reversible by construction (FR-878): forget archives, redact stashes its
original, restore is conflict-safe. Approval is tiered from disposition
content; hash-binding and validate-all-then-apply-all are unchanged.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
from pathlib import Path

SIGN_OFF_RE = re.compile(
    r"^SIGN-OFF:.*manifest=([0-9a-f]{64}).*disposition=([0-9a-f]{64})", re.MULTILINE
)
DELEGATION_TOKEN = "DELEGATION: FR-878 tier-1 standing"
TOMBSTONE_NAME = "_tombstones.md"
DEFAULT_AUDIT_LOG = ".github/hooks/logs/memory-curation-audit.jsonl"


class ApplyError(Exception):
    """Fatal apply refusal; message is the user-facing diagnostic."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute_tier(disposition: dict) -> int:
    if disposition.get("premise_kind") != "hygiene":
        return 3  # export_publication, missing, or unknown: fail closed
    verdicts = {note["verdict"] for note in disposition["notes"].values()}
    if "forget" in verdicts:
        return 2
    if "redact" in verdicts:
        return 1
    return 0


def verify_signoff(review: Path, manifest: Path, disposition: Path, tier: int) -> None:
    match = SIGN_OFF_RE.search(review.read_text(encoding="utf-8"))
    if not match:
        raise ApplyError("no SIGN-OFF line in review file — approval required")
    if match.group(1) != sha256_file(manifest):
        raise ApplyError("SIGN-OFF manifest hash does not match manifest.json")
    if match.group(2) != sha256_file(disposition):
        raise ApplyError("SIGN-OFF disposition hash does not match disposition.json")
    line = match.group(0)
    has_human = "HUMAN=" in line
    if tier == 3 and not (has_human and "EXPORT_PUBLICATION_APPROVED" in line):
        raise ApplyError(
            "tier 3 (export/publication or unknown premise) requires a"
            " non-delegable human sign-off with EXPORT_PUBLICATION_APPROVED"
        )
    if tier == 2 and not has_human:
        raise ApplyError("tier 2 (forget verdicts) requires HUMAN=<name> sign-off")
    if tier == 1 and not (has_human or DELEGATION_TOKEN in line):
        raise ApplyError(
            "tier 1 requires HUMAN=<name> or the recorded standing"
            f" delegation line ({DELEGATION_TOKEN!r})"
        )


def plan_actions(
    disposition: dict, manifest: dict, memory_root: Path
) -> list[tuple[str, str, Path, str | None]]:
    """Validate every target against the frozen manifest; return actions.

    Refuses everything on any drift or protected-file hit — no partial apply.
    """
    actions: list[tuple[str, str, Path, str | None]] = []
    for key, note in sorted(disposition["notes"].items()):
        verdict = note["verdict"]
        if Path(key).name == TOMBSTONE_NAME and verdict != "keep":
            raise ApplyError(f"tombstone index is protected: {key} cannot be {verdict}")
        if verdict == "keep":
            continue
        frozen_sha = manifest["notes"][key]["sha256"]
        target = (memory_root / key).resolve()
        if not target.is_relative_to(memory_root.resolve()):
            raise ApplyError(f"path escapes memory root: {key}")
        if verdict == "forget":
            if not target.exists():
                continue  # already applied
            if sha256_file(target) != frozen_sha:
                raise ApplyError(f"drift: {key} changed after collection")
            actions.append(("forget", key, target, None))
        elif verdict == "redact":
            draft = note["redacted_draft"]
            if target.exists():
                live_sha = sha256_file(target)
                if live_sha == hashlib.sha256(draft.encode()).hexdigest():
                    continue  # already applied
                if live_sha != frozen_sha:
                    raise ApplyError(f"drift: {key} changed after collection")
            actions.append(("redact", key, target, draft))
    return actions


def append_tombstones(memory_root: Path, rows: list[str]) -> None:
    tomb = memory_root / "repo" / TOMBSTONE_NAME
    tomb.parent.mkdir(parents=True, exist_ok=True)
    with tomb.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(row + "\n")


def execute(
    actions: list[tuple[str, str, Path, str | None]],
    disposition: dict,
    memory_root: Path,
    hashes: tuple[str, str],
) -> tuple[int, int]:
    op_id = (
        datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + hashes[0][:8]
    )
    rows: list[str] = []
    forgotten = redacted = 0
    for verdict, key, target, draft in actions:
        pre_sha = sha256_file(target)
        archive_path = memory_root / ".archive" / op_id / key
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        archive_path.write_bytes(target.read_bytes())
        reason = disposition["notes"][key]["rationale"].replace("|", "/")
        if verdict == "forget":
            target.unlink()
            forgotten += 1
            post_sha = "-"
            row_verdict = "forget"
        else:
            target.write_text(draft, encoding="utf-8")
            redacted += 1
            post_sha = hashlib.sha256(draft.encode()).hexdigest()
            row_verdict = "redact-backup"
        rows.append(
            f"{op_id} | {key} | {row_verdict} | {reason} | .archive/{op_id}/{key}"
            f" | {pre_sha} | {post_sha} | {hashes[0]} | {hashes[1]} | archived"
        )
    if rows:
        append_tombstones(memory_root, rows)
    return forgotten, redacted


def append_audit(tier: int, hashes: tuple[str, str]) -> None:
    log = Path(os.environ.get("MEMORY_CURATION_AUDIT_LOG", DEFAULT_AUDIT_LOG))
    log.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.datetime.now(datetime.UTC).isoformat(),
        "event": "memory_curation_apply",
        "tier": tier,
        "manifest_sha256": hashes[0],
        "disposition_sha256": hashes[1],
    }
    with log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def write_curation_state(memory_root: Path, hashes: tuple[str, str]) -> None:
    """FR-877: record the post-apply live baseline for the staleness advisory."""
    notes = {}
    repo_dir = memory_root / "repo"
    for path in sorted(repo_dir.glob("*.md")):
        if path.is_symlink() or not path.is_file():
            continue
        notes[f"repo/{path.name}"] = sha256_file(path)
    marker = {
        "version": 1,
        "applied_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "manifest_sha256": hashes[0],
        "disposition_sha256": hashes[1],
        "notes": notes,
    }
    (memory_root / ".curation-state.json").write_text(
        json.dumps(marker, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def run_apply(args: argparse.Namespace) -> int:
    memory_root = Path(args.memory_root)
    disposition_path = Path(args.disposition)
    manifest_path = Path(args.manifest)
    try:
        disposition = json.loads(disposition_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        tier = compute_tier(disposition)
        if tier > 0:
            verify_signoff(Path(args.review), manifest_path, disposition_path, tier)
            if disposition["manifest_sha256"] != sha256_file(manifest_path):
                raise ApplyError(
                    "disposition.json manifest hash does not match manifest"
                )
        actions = plan_actions(disposition, manifest, memory_root)
    except (ApplyError, OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"apply: refused: {exc}", file=sys.stderr)
        return 2
    hashes = (sha256_file(manifest_path), sha256_file(disposition_path))
    forgotten, redacted = execute(actions, disposition, memory_root, hashes)
    if tier > 0:
        append_audit(tier, hashes)
    write_curation_state(memory_root, hashes)
    kept = len(disposition["notes"]) - forgotten - redacted
    print(
        f"applied (tier {tier}): {forgotten} forgotten (archived),"
        f" {redacted} redacted (original stashed), {kept} kept/unchanged"
    )
    return 0


def run_restore(args: argparse.Namespace) -> int:
    memory_root = Path(args.memory_root)
    ref = args.ref.strip("/")
    archive_file = memory_root / ".archive" / ref
    try:
        if not archive_file.is_file():
            raise ApplyError(f"no archived note at .archive/{ref}")
        op_id, key = ref.split("/", 1)
        live = (memory_root / key).resolve()
        if not live.is_relative_to(memory_root.resolve()):
            raise ApplyError(f"path escapes memory root: {key}")
        archived_bytes = archive_file.read_bytes()
        tomb = memory_root / "repo" / TOMBSTONE_NAME
        tomb_text = tomb.read_text(encoding="utf-8") if tomb.exists() else ""
        already_recorded = f".archive/{ref} " in tomb_text and "| restored" in tomb_text
        if live.exists():
            if live.read_bytes() != archived_bytes:
                raise ApplyError(
                    f"conflict: live {key} diverged from archive — human action required"
                )
            if already_recorded:
                print(f"restore: already restored: {key}")
                return 0
        else:
            live.parent.mkdir(parents=True, exist_ok=True)
            live.write_bytes(archived_bytes)
        sha = hashlib.sha256(archived_bytes).hexdigest()
        append_tombstones(
            memory_root,
            [
                f"{op_id} | {key} | restore | restored from archive |"
                f" .archive/{ref} | {sha} | - | - | - | restored"
            ],
        )
        print(f"restored {key} from .archive/{ref}")
        return 0
    except (ApplyError, OSError) as exc:
        print(f"restore: refused: {exc}", file=sys.stderr)
        return 2


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "restore":
        parser = argparse.ArgumentParser(description="Restore an archived note.")
        parser.add_argument("mode")
        parser.add_argument("ref", help="<op_id>/<original-relative-path>")
        parser.add_argument("--memory-root", required=True)
        return run_restore(parser.parse_args(argv))
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--disposition", required=True)
    parser.add_argument("--review", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--memory-root", required=True)
    return run_apply(parser.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
