#!/usr/bin/env python3
"""Ramp installer — FR-865.

Mechanical, idempotent, reversible copier of curated governance assets
from ramp/assets/ into a target repository, driven by ramp/manifest.yaml.
No LLM, no network, no judgement about the target. The only git
invocation is rev-parse inside this repository to stamp the source SHA
(artifact_carries_code_identity); no git command ever runs against the
target (FR-865 R-5: filesystem inspection only).
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
RAMP_DIR = REPO_ROOT / "ramp"
DEFAULT_MANIFEST = RAMP_DIR / "manifest.yaml"
DEFAULT_CONSUMERS = RAMP_DIR / "consumers.md"
CONSUMERS_ENV = "RAMP_CONSUMERS_FILE"
TARGET_DOC = Path("docs") / "ramp-manifest.md"
BACKUP_DIR = Path("docs") / "ramp-backups"
OVERWRITE_POLICIES = ("never", "force-backup")
PROVENANCE_FIELDS = ("authored", "mirror_exact", "curation_diff")
GENERATED_PARTS = {"__pycache__", "logs"}
GENERATED_SUFFIXES = (".pyc", ".log", ".jsonl")
SLUG_RE = re.compile(r"^[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+$")


class ManifestError(ValueError):
    """ramp/manifest.yaml violates its schema."""


class Refusal(RuntimeError):
    """Target or arguments refused; nothing was written."""


@dataclass
class Entry:
    source: str
    destination: str
    tier: int
    overwrite: str
    provenance: str
    executable: bool = False
    allow_symlink: bool = False
    mirror_exact: str | None = None
    curation_diff: str | None = None


def _check_relpath(kind: str, value: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value:
        errors.append(f"{kind} must be a non-empty string: {value!r}")
        return
    p = Path(value)
    if p.is_absolute():
        errors.append(f"absolute {kind} forbidden: {value}")
    if ".." in p.parts:
        errors.append(f"'..' traversal in {kind} forbidden: {value}")
    if value != os.path.normpath(value):
        errors.append(f"{kind} not normalized: {value}")
    if GENERATED_PARTS & set(p.parts) or p.name.endswith(GENERATED_SUFFIXES):
        errors.append(f"generated/cache/log path forbidden in {kind}: {value}")


def _parse_entry(raw: dict, ramp_dir: Path, errors: list[str]) -> Entry | None:
    source = raw.get("source", "")
    destination = raw.get("destination", "")
    _check_relpath("source", source, errors)
    _check_relpath("destination", destination, errors)
    tier = raw.get("tier")
    if tier not in (1, 2, 3):
        errors.append(f"tier must be 1, 2 or 3: {tier!r} ({source})")
    overwrite = raw.get("overwrite", "")
    if overwrite not in OVERWRITE_POLICIES:
        errors.append(f"overwrite must be one of {OVERWRITE_POLICIES}: {overwrite!r}")
    provenance = [f for f in PROVENANCE_FIELDS if raw.get(f)]
    if len(provenance) != 1:
        errors.append(f"exactly one provenance field required ({source}): {provenance}")
    src_path = ramp_dir / source if isinstance(source, str) and source else None
    allow_symlink = bool(raw.get("allow_symlink", False))
    if src_path is not None and not errors:
        if src_path.is_symlink() and not allow_symlink:
            errors.append(f"symlink source without allow_symlink: {source}")
        elif src_path.is_dir():
            errors.append(f"directory source forbidden: {source}")
        elif not src_path.is_file():
            errors.append(f"missing source: {source}")
    if errors:
        return None
    return Entry(
        source=source,
        destination=destination,
        tier=tier,
        overwrite=overwrite,
        provenance=provenance[0],
        executable=bool(raw.get("executable", False)),
        allow_symlink=allow_symlink,
        mirror_exact=raw.get("mirror_exact") or None,
        curation_diff=raw.get("curation_diff") or None,
    )


def load_manifest(
    path: Path = DEFAULT_MANIFEST, ramp_dir: Path | None = None
) -> list[Entry]:
    """Load and validate the ramp manifest; raise ManifestError on any defect."""
    ramp_dir = ramp_dir or Path(path).parent
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        raise ManifestError("manifest must be a mapping with an 'entries' list")
    entries: list[Entry] = []
    errors: list[str] = []
    for raw in data["entries"]:
        entry_errors: list[str] = []
        entry = _parse_entry(raw, ramp_dir, entry_errors)
        errors.extend(entry_errors)
        if entry is not None:
            entries.append(entry)
    dests = [e.destination for e in entries]
    for dup in {d for d in dests if dests.count(d) > 1}:
        errors.append(f"duplicate destination: {dup}")
    if errors:
        raise ManifestError("; ".join(errors))
    return entries


def select_tier(entries: list[Entry], tier: int) -> list[Entry]:
    """Monotonic tier expansion: tier N ships every entry with tier <= N."""
    return [e for e in entries if e.tier <= tier]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_sha() -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def check_target(target: Path) -> Path:
    """Refuse anything outside the supported Tier-1 contract (FR-865 R-3/R-5)."""
    target = Path(target)
    if not target.is_dir():
        raise Refusal(f"refused — not a directory: {target}")
    git = target / ".git"
    if git.is_file():
        raise Refusal(
            "refused — linked worktree (.git is a file); documented "
            "limitation, run against the main working tree"
        )
    if not git.is_dir():
        raise Refusal(f"refused — not a git repository root (no .git/): {target}")
    if target.resolve() == REPO_ROOT.resolve():
        raise Refusal("refused — target is this repository itself")
    if not (target / "pyproject.toml").is_file():
        raise Refusal("refused — unsupported target shape: no pyproject.toml")
    if not (target / "tests").is_dir():
        raise Refusal("refused — unsupported target shape: no tests/ suite")
    ruff_configured = (
        "[tool.ruff" in (target / "pyproject.toml").read_text(encoding="utf-8")
        or (target / "ruff.toml").is_file()
        or (target / ".ruff.toml").is_file()
    )
    if not ruff_configured:
        raise Refusal("refused — unsupported target shape: ruff not configured")
    return target


def plan(
    entries: list[Entry], tier: int, target: Path, force: bool
) -> list[tuple[Entry, str]]:
    """Compute (entry, action) pairs; actions: created/skipped_exists/overwritten."""
    resolved_target = target.resolve()
    actions: list[tuple[Entry, str]] = []
    for e in select_tier(entries, tier):
        dest = (target / e.destination).resolve()
        if not dest.is_relative_to(resolved_target):
            raise Refusal(f"refused — destination escapes target root: {e.destination}")
        if dest.exists():
            if force and e.overwrite == "force-backup":
                actions.append((e, "overwritten"))
            else:
                actions.append((e, "skipped_exists"))
        else:
            actions.append((e, "created"))
    return actions


ACTION_WORDS = {
    "created": "create",
    "skipped_exists": "skip exists",
    "overwritten": "overwrite",
}


def render_target_doc(sha: str, tier: int, rows: list[dict]) -> str:
    lines = [
        "# Ramp Install Manifest",
        "",
        "Written by scripts/ramp.sh (FR-865). Sufficient for rollback:",
        "`scripts/ramp.sh <this-repo> --rollback` deletes only `created`",
        "rows (hash-verified) and restores `overwritten` rows from backup.",
        "",
        f"- source_sha: {sha}",
        "- reviewed_source_sha: pending-human-review",
        f"- tier: {tier}",
        "",
        "| destination | source | action | source_sha256 | installed_sha256 "
        "| backup |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            "| {destination} | {source} | {action} | {source_sha256} "
            "| {installed_sha256} | {backup} |".format(**r)
        )
    return "\n".join(lines) + "\n"


def parse_target_manifest(path: Path) -> dict:
    """Parse docs/ramp-manifest.md back into a dict (tests + rollback)."""
    text = Path(path).read_text(encoding="utf-8")
    doc: dict = {"rows": {}}
    for line in text.splitlines():
        if line.startswith("- source_sha: "):
            doc["source_sha"] = line.split(": ", 1)[1]
        elif line.startswith("- tier: "):
            doc["tier"] = int(line.split(": ", 1)[1])
        elif line.startswith("|") and "---" not in line and "destination" not in line:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) == 6:
                doc["rows"][cells[0]] = {
                    "source": cells[1],
                    "action": cells[2],
                    "source_sha256": cells[3],
                    "installed_sha256": cells[4],
                    "backup": cells[5],
                }
    return doc


def _consumer_row(slug: str, tier: int, manifest_path: Path) -> tuple[str, str]:
    mhash = hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest()[:12]
    ssha = source_sha()[:12]
    from datetime import date

    row = f"| {slug} | {date.today().isoformat()} | {tier} | {ssha} | {mhash} | - |"
    identity = f"{slug}::{tier}::{mhash}"
    return row, identity


CONSUMERS_HEADER = """# Ramp Consumers

Generic source-repo registry (FR-865 A-2). One row per install; row
identity is `(target, tier, manifest hash)` and re-installs update the
row idempotently. The target is a repository slug (`owner/repo`) —
never an absolute local path or a credential-bearing URL.

| target | date | tier | source_sha | manifest_hash | reviewed_sha |
|---|---|---|---|---|---|
"""


def record_consumer(slug: str, tier: int, manifest_path: Path, path: Path) -> str:
    row, identity = _consumer_row(slug, tier, manifest_path)
    _, _, mhash = identity.split("::")
    text = path.read_text(encoding="utf-8") if path.exists() else CONSUMERS_HEADER
    lines = text.rstrip("\n").splitlines()
    kept = [
        ln
        for ln in lines
        if not (
            ln.startswith(f"| {slug} |")
            and f"| {tier} |" in ln
            and f"| {mhash} |" in ln
        )
    ]
    kept.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(kept) + "\n", encoding="utf-8")
    return row


def validate_slug(slug: str) -> str:
    if not SLUG_RE.match(slug) or "://" in slug or "@" in slug:
        raise Refusal(
            f"refused — consumer target must be a repository slug owner/repo, "
            f"got: {slug}"
        )
    return slug


def install(
    target: Path,
    tier: int,
    *,
    force: bool = False,
    dry_run: bool = False,
    consumer: str | None = None,
    manifest_path: Path = DEFAULT_MANIFEST,
    out=print,
) -> int:
    if consumer:
        validate_slug(consumer)
    entries = load_manifest(manifest_path)
    target = check_target(Path(target))
    actions = plan(entries, tier, target, force)
    if dry_run:
        out(f"dry-run: tier {tier} into {target} — nothing will be written")
    for e, action in actions:
        out(f"{ACTION_WORDS[action]} {e.destination}")
    if consumer:
        row, _ = _consumer_row(consumer, tier, manifest_path)
        if dry_run:
            out(f"would record consumer row: {row}")
    if dry_run:
        return 0

    rows = []
    changed = False
    for e, action in actions:
        dest = target / e.destination
        src = Path(manifest_path).parent / e.source
        backup = "-"
        if action == "overwritten":
            backup_path = target / BACKUP_DIR / e.destination
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            backup_path.write_bytes(dest.read_bytes())
            backup = (BACKUP_DIR / e.destination).as_posix()
        if action in ("created", "overwritten"):
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(src.read_bytes())
            if e.executable:
                dest.chmod(dest.stat().st_mode | 0o755)
            changed = True
        rows.append(
            {
                "destination": e.destination,
                "source": e.source,
                "action": action,
                "source_sha256": sha256_file(src),
                "installed_sha256": sha256_file(dest) if dest.exists() else "-",
                "backup": backup,
            }
        )
    doc_path = target / TARGET_DOC
    if changed or not doc_path.exists():
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text(render_target_doc(source_sha(), tier, rows), encoding="utf-8")
    if consumer:
        registry = Path(os.environ.get(CONSUMERS_ENV, DEFAULT_CONSUMERS))
        row = record_consumer(consumer, tier, manifest_path, registry)
        out(f"recorded consumer row: {row}")
    out(f"next step (operator): cd {target} && pre-commit install")
    out("(the installer never runs pre-commit install itself)")
    return 0


def rollback(target: Path, *, out=print) -> int:
    target = Path(target)
    doc_path = target / TARGET_DOC
    if not doc_path.is_file():
        raise Refusal(f"refused — no ramp manifest to roll back: {doc_path}")
    doc = parse_target_manifest(doc_path)
    for dest_rel, row in doc["rows"].items():
        dest = target / dest_rel
        if row["action"] == "created":
            if dest.is_file() and sha256_file(dest) == row["installed_sha256"]:
                dest.unlink()
                out(f"deleted {dest_rel}")
            elif dest.exists():
                out(f"kept {dest_rel} (modified since install)")
        elif row["action"] == "overwritten" and row["backup"] != "-":
            backup = target / row["backup"]
            if backup.is_file():
                dest.write_bytes(backup.read_bytes())
                backup.unlink()
                out(f"restored {dest_rel} from backup")
    doc_path.unlink()
    out("rollback complete")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ramp.sh",
        description="Copy curated governance assets into a target repo (FR-865).",
    )
    parser.add_argument("target", help="path to the target repository root")
    parser.add_argument("--tier", type=int, choices=(1, 2, 3))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--record-consumer", metavar="OWNER/REPO")
    parser.add_argument("--rollback", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.rollback:
            return rollback(Path(args.target))
        if args.tier is None:
            parser.error("--tier {1,2,3} is required unless --rollback")
        return install(
            Path(args.target),
            args.tier,
            force=args.force,
            dry_run=args.dry_run,
            consumer=args.record_consumer,
        )
    except (ManifestError, Refusal) as exc:
        print(f"ramp: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
