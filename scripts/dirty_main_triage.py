#!/usr/bin/env python3
"""FR-1047 — read-only provenance triage for a dirty main checkout.

`git status` cannot tell debris from work: a partial `git pull` against the
FR-889 OS lock leaves already-merged content presenting as local
modifications, and a session that wrote into the shared checkout leaves the
only copy of real work in the same shape. This classifies each dirty path by
where its BYTES come from, and marks exactly one class safe.

Read-only by construction: no chmod (the FR-889 lock-mutator fence would deny
it anyway), no checkout, no clean. Mutation belongs to
`scripts/worktree.sh unlock-main|lock-main` plus explicit-pathspec git,
invoked by a human or agent after reading this report.

REQ-YG-678.
"""

from __future__ import annotations

import argparse
import json
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

GIT = shutil.which("git") or "/usr/bin/git"

TARGET_IDENTICAL = "TARGET_IDENTICAL"
KNOWN_BLOB = "KNOWN_BLOB"
UNSEEN_BLOB = "UNSEEN_BLOB"
UNSUPPORTED = "UNSUPPORTED"
ERROR = "ERROR"

SAFE = "SAFE"
PRESERVE = "PRESERVE"

#: Only these two status codes carry readable working-file bytes at a path
#: whose index entry is clean. Everything else preserves.
SUPPORTED_CODES = {" M", "??"}

#: A status record git did not shape as `XY <path>`. Deliberately outside
#: SUPPORTED_CODES so it can never be promoted to an untracked file.
MALFORMED = "!!"

#: Tree modes whose blob is an ordinary file. A symlink is also stored as a
#: blob, so matching bytes do not make a symlink and a regular file the same
#: thing — mode is part of the identity.
REGULAR_MODES = {b"100644", b"100755"}


class Refused(Exception):
    """A precondition failed; nothing is classified."""


@dataclass
class Verdict:
    code: str
    path: str
    klass: str
    disposition: str
    detail: str


def git_out(repo: Path, *args: str) -> str:
    """Run git, raising CalledProcessError on failure (never swallowed)."""
    return subprocess.run(  # noqa: S603  # CONF-487
        [GIT, *args],
        cwd=repo,
        check=True,
        capture_output=True,
    ).stdout.decode("utf-8", "surrogateescape")


def git_bytes(repo: Path, *args: str) -> bytes:
    return subprocess.run(  # noqa: S603  # CONF-488
        [GIT, *args],
        cwd=repo,
        check=True,
        capture_output=True,
    ).stdout


def check_preconditions(repo: Path) -> tuple[str, str, str]:
    """Return (root, head_oid, origin_main_oid) or raise Refused."""
    try:
        root = git_out(repo, "rev-parse", "--show-toplevel").strip()
        git_dir = git_out(repo, "rev-parse", "--absolute-git-dir").strip()
        common = git_out(
            repo, "rev-parse", "--path-format=absolute", "--git-common-dir"
        ).strip()
    except (subprocess.CalledProcessError, OSError) as exc:
        raise Refused(f"REFUSED: not a usable git checkout ({exc})") from exc
    if Path(git_dir) != Path(common):
        raise Refused("REFUSED: linked worktree — run against the main checkout")
    try:
        branch = git_out(repo, "rev-parse", "--abbrev-ref", "HEAD").strip()
    except subprocess.CalledProcessError as exc:
        raise Refused("REFUSED: HEAD does not resolve") from exc
    if branch != "main":
        raise Refused(f"REFUSED: not on main (HEAD is {branch!r})")
    try:
        head = git_out(repo, "rev-parse", "HEAD").strip()
        origin = git_out(repo, "rev-parse", "origin/main").strip()
    except subprocess.CalledProcessError as exc:
        raise Refused("REFUSED: origin/main does not resolve") from exc
    return root, head, origin


def parse_status(raw: bytes) -> list[tuple[str, str]]:
    """Parse `--porcelain=v1 -z` into (code, path) pairs.

    Rename/copy entries carry a second NUL-terminated origin path, which is
    consumed and discarded — those entries are unsupported anyway.
    """
    fields = raw.split(b"\0")
    entries: list[tuple[str, str]] = []
    i = 0
    while i < len(fields):
        field = fields[i]
        i += 1
        if not field:
            continue
        if len(field) < 4 or field[2:3] != b" ":
            entries.append((MALFORMED, field.decode("utf-8", "surrogateescape")))
            continue
        code = field[:2].decode("ascii", "replace")
        path = field[3:].decode("utf-8", "surrogateescape")
        if code[0] in "RC":
            i += 1  # discard the origin path
        entries.append((code, path))
    return entries


def origin_blob(repo: Path, origin_oid: str, path: str) -> bytes | None:
    """Bytes of `origin/main:<path>`, or None when it is absent or not a file.

    A non-regular target mode (symlink, gitlink) returns None rather than its
    bytes: identical bytes do not make a symlink interchangeable with the
    regular file sitting in the working tree.
    """
    out = git_bytes(repo, "ls-tree", "-z", origin_oid, "--", path)
    if not out.strip(b"\0"):
        return None
    entry = out.split(b"\0")[0]
    meta = entry.split(b"\t", 1)[0].split(b" ")
    if len(meta) < 3 or meta[1] != b"blob" or meta[0] not in REGULAR_MODES:
        return None
    return git_bytes(repo, "cat-file", "blob", meta[2].decode("ascii"))


def tree_contains(repo: Path, rev: str, oid: str) -> bool:
    listing = git_out(repo, "ls-tree", "-r", rev)
    return f"{oid}\t" in listing


def find_source_revision(repo: Path, oid: str) -> str | None:
    """Short SHA of a reachable commit whose tree actually holds `oid`.

    `--find-object` also reports commits that DELETED the object; naming one
    of those as the source would be a false provenance claim, so each
    candidate is verified against its own tree.
    """
    candidates = git_out(
        repo, "log", "--all", "--find-object", oid, "--format=%H", "--max-count=20"
    ).split()
    for sha in candidates:
        if tree_contains(repo, sha, oid):
            return sha[:12]
    return None


def unreadable_reason(target: Path) -> tuple[str, str] | None:
    """Return (class, detail) when the path cannot yield trustworthy bytes."""
    try:
        mode = target.lstat().st_mode
    except OSError as exc:
        return ERROR, f"stat failed: {exc.strerror}"
    if stat.S_ISLNK(mode):
        return UNSUPPORTED, "symlink"
    if not stat.S_ISREG(mode):
        return UNSUPPORTED, "not a regular file"
    return None


def classify(repo: Path, origin_oid: str, code: str, path: str) -> Verdict:
    """Classify one status entry. Any doubt preserves."""
    if code not in SUPPORTED_CODES:
        reason = (
            "malformed status record"
            if code == MALFORMED
            else "unsupported status code"
        )
        return Verdict(code, path, UNSUPPORTED, PRESERVE, reason)
    unreadable = unreadable_reason(repo / path)
    if unreadable:
        klass, detail = unreadable
        return Verdict(code, path, klass, PRESERVE, detail)
    try:
        working = (repo / path).read_bytes()
        oid = git_out(repo, "hash-object", "--no-filters", "--", path).strip()
        blob = origin_blob(repo, origin_oid, path)
    except (OSError, subprocess.CalledProcessError) as exc:
        return Verdict(code, path, ERROR, PRESERVE, f"probe failed: {exc}")
    if blob is not None and blob == working:
        return Verdict(code, path, TARGET_IDENTICAL, SAFE, f"blob {oid[:12]}")
    try:
        source = find_source_revision(repo, oid)
    except (subprocess.CalledProcessError, OSError) as exc:
        return Verdict(code, path, ERROR, PRESERVE, f"reachability probe failed: {exc}")
    if source:
        return Verdict(
            code, path, KNOWN_BLOB, PRESERVE, f"blob {oid[:12]} from {source}"
        )
    return Verdict(code, path, UNSEEN_BLOB, PRESERVE, f"blob {oid[:12]} — only copy")


def report(root: str, head: str, origin: str, verdicts: list[Verdict]) -> int:
    print(f"repo:        {root}")
    print(f"HEAD:        {head}")
    print(f"origin/main: {origin}")
    print()
    for v in verdicts:
        print(f"  [{v.code}] {json.dumps(v.path)}")
        print(f"        {v.klass}  {v.disposition}  ({v.detail})")
    if verdicts:
        print()
    tally = {
        "safe": sum(v.disposition == SAFE for v in verdicts),
        "preserve": sum(
            v.disposition == PRESERVE and v.klass in (KNOWN_BLOB, UNSEEN_BLOB)
            for v in verdicts
        ),
        "unsupported": sum(v.klass == UNSUPPORTED for v in verdicts),
        "errors": sum(v.klass == ERROR for v in verdicts),
    }
    print(" ".join(f"{k}={v}" for k, v in tally.items()))
    unsafe = tally["preserve"] + tally["unsupported"] + tally["errors"]
    if unsafe:
        print(
            "\nNOT SAFE TO CLEAN: every path above must be dispositioned by a "
            "human before any mutation."
        )
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="path to the main checkout")
    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()
    try:
        root, head, origin = check_preconditions(repo)
    except Refused as exc:
        print(exc)
        return 2
    try:
        raw = git_bytes(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"REFUSED: status failed ({exc})")
        return 2
    verdicts = [classify(repo, origin, code, path) for code, path in parse_status(raw)]
    return report(root, head, origin, verdicts)


if __name__ == "__main__":
    sys.exit(main())
