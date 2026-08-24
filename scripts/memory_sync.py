#!/usr/bin/env python3
"""FR-874: cross-device agent memory sync via the git-tracked note store.

The memory tool's "repo" and "user" scopes live under machine-local VS Code
storage; this script mirrors them through ``docs/agent-memory/`` so git
carries agent intel across devices, peers, and subrepos.

Commands:
    export   memory-tool -> store (repo scope + explicitly promoted user notes)
    import   store -> memory-tool (manifest base-hash conflict contract)
    promote  mark one user-scope note as shareable (adds to manifest promoted list)

Store resolution: --store > $YAMLGRAPH_AGENT_MEMORY_ROOT (read-only, subrepo
mode) > <this repo>/docs/agent-memory. An env-var store refuses export/promote.
Conflict contract (judgement R-2): never mtime — a local note is overwritten
only when it still matches the base hash recorded at last import; divergence
on both sides is a reported conflict unless --force.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STORE = REPO_ROOT / "docs" / "agent-memory"
ENV_STORE = "YAMLGRAPH_AGENT_MEMORY_ROOT"
NOTE_KEY_RE = re.compile(r"^(repo|shared)/[A-Za-z0-9._-]+\.md$")
NOTE_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+\.md$")
BASE_STATE_FILE = ".import-base.json"


class SyncError(Exception):
    """Fatal sync failure; message is the user-facing diagnostic."""


@dataclass
class Store:
    root: Path
    read_only: bool

    @property
    def manifest_path(self) -> Path:
        return self.root / "manifest.json"

    def load_manifest(self) -> dict:
        if self.manifest_path.exists():
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        return {"version": 1, "notes": {}, "promoted": []}

    def save_manifest(self, manifest: dict) -> None:
        self.manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_store(store_arg: str | None, need_write: bool) -> Store:
    import os

    if store_arg:
        return Store(root=Path(store_arg), read_only=False)
    env_value = os.environ.get(ENV_STORE, "").strip()
    if env_value:
        root = Path(env_value)
        if not (root / "manifest.json").exists():
            raise SyncError(
                f"{ENV_STORE} points to an invalid store (no manifest.json): {root}"
            )
        if need_write:
            raise SyncError(
                f"store resolved via {ENV_STORE} is read-only (subrepo mode); "
                "export/promote must run in the master clone"
            )
        return Store(root=root, read_only=True)
    return Store(root=DEFAULT_STORE, read_only=False)


def discover_memory_root() -> Path:
    """Locate this workspace's live memory-tool root (macOS VS Code layout)."""
    base = (
        Path.home()
        / "Library"
        / "Application Support"
        / "Code"
        / "User"
        / "workspaceStorage"
    )
    for ws in sorted(base.glob("*/workspace.json")):
        try:
            folder = json.loads(ws.read_text(encoding="utf-8")).get("folder", "")
        except (OSError, json.JSONDecodeError):
            continue
        if folder.rstrip("/").endswith(
            REPO_ROOT.name
        ) and REPO_ROOT.as_uri() == folder.rstrip("/"):
            root = ws.parent / "GitHub.copilot-chat" / "memory-tool" / "memories"
            if root.is_dir():
                return root
    raise SyncError(
        "could not discover the memory-tool root for this workspace; "
        "pass --memory-root explicitly"
    )


def resolve_memory_root(arg: str | None) -> Path:
    if arg:
        root = Path(arg)
        if not root.is_dir():
            raise SyncError(f"--memory-root does not exist: {root}")
        return root
    return discover_memory_root()


def validate_note_key(key: str) -> None:
    if not NOTE_KEY_RE.match(key):
        raise SyncError(f"manifest note key fails sanitization: {key!r}")


def safe_child(root: Path, relative: str) -> Path:
    """Resolve relative under root, refusing escape via traversal or symlink."""
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise SyncError(f"path escapes target root: {relative!r}")
    return candidate


def local_path_for(memory_root: Path, key: str) -> Path:
    # shared/ notes live at the user scope's top level locally
    relative = key if key.startswith("repo/") else key.split("/", 1)[1]
    return safe_child(memory_root, relative)


def load_base_state(memory_root: Path) -> dict:
    path = memory_root / BASE_STATE_FILE
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_base_state(memory_root: Path, state: dict) -> None:
    (memory_root / BASE_STATE_FILE).write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def cmd_export(memory_root: Path, store: Store, quiet: bool) -> int:
    manifest = store.load_manifest()
    changes: list[str] = []

    def put(source: Path, key: str, scope: str, promoted_from: str | None) -> None:
        validate_note_key(key)
        target = safe_child(store.root, key)
        target.parent.mkdir(parents=True, exist_ok=True)
        digest = sha256_of(source)
        previous = manifest["notes"].get(key)
        if previous and previous["sha256"] == digest:
            return
        target.write_bytes(source.read_bytes())
        manifest["notes"][key] = {
            "scope": scope,
            "sha256": digest,
            "promoted_from": promoted_from,
        }
        changes.append(f"{'update' if previous else 'add'} {key}")

    repo_dir = memory_root / "repo"
    if repo_dir.is_dir():
        for note in sorted(repo_dir.glob("*.md")):
            put(note, f"repo/{note.name}", "repo", None)
    for name in manifest["promoted"]:
        if not NOTE_NAME_RE.match(name):
            raise SyncError(f"promoted entry fails sanitization: {name!r}")
        source = safe_child(memory_root, name)
        if not source.exists():
            raise SyncError(f"promoted note missing from user scope: {name}")
        put(source, f"shared/{name}", "user", name)

    store.save_manifest(manifest)
    if not quiet:
        for line in changes or ["up to date"]:
            print(line)
    return 0


def cmd_import(memory_root: Path, store: Store, force: bool, quiet: bool) -> int:
    if not store.manifest_path.exists():
        raise SyncError(f"store has no manifest.json: {store.root}")
    manifest = store.load_manifest()
    base_state = load_base_state(memory_root)
    conflicts: list[str] = []
    applied: list[str] = []

    for key in sorted(manifest["notes"]):
        validate_note_key(key)
        source = safe_child(store.root, key)
        if source.is_symlink() or not source.is_file():
            raise SyncError(f"store note missing or symlinked: {key}")
        repo_hash = sha256_of(source)
        target = local_path_for(memory_root, key)
        base = base_state.get(key)

        if target.exists():
            local_hash = sha256_of(target)
            if local_hash == repo_hash:
                base_state[key] = repo_hash
                continue
            if local_hash != base and repo_hash != base and not force:
                conflicts.append(key)
                continue
            if local_hash != base and repo_hash == base:
                continue  # local is ahead; repo unchanged since last import
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        base_state[key] = repo_hash
        applied.append(key)

    save_base_state(memory_root, base_state)
    if not quiet:
        for key in applied:
            print(f"import {key}")
    if conflicts:
        for key in conflicts:
            print(
                f"conflict (local and store diverged; use --force): {key}",
                file=sys.stderr,
            )
        return 3
    return 0


def cmd_promote(memory_root: Path, store: Store, name: str, quiet: bool) -> int:
    if not NOTE_NAME_RE.match(name):
        raise SyncError(f"note name fails sanitization: {name!r}")
    source = safe_child(memory_root, name)
    if not source.is_file():
        raise SyncError(f"user-scope note not found: {source}")
    manifest = store.load_manifest()
    if name not in manifest["promoted"]:
        manifest["promoted"].append(name)
        manifest["promoted"].sort()
        store.root.mkdir(parents=True, exist_ok=True)
        store.save_manifest(manifest)
    if not quiet:
        print(f"promoted {name} (export to publish)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["export", "import", "promote"])
    parser.add_argument("note", nargs="?", help="user-scope note name (promote)")
    parser.add_argument("--memory-root", help="memory-tool root override (tests)")
    parser.add_argument("--store", help="store directory override (tests)")
    parser.add_argument(
        "--force", action="store_true", help="overwrite conflicts on import"
    )
    parser.add_argument("--quiet", action="store_true", help="suppress info output")
    args = parser.parse_args(argv)

    try:
        need_write = args.command in ("export", "promote")
        store = resolve_store(args.store, need_write=need_write)
        memory_root = resolve_memory_root(args.memory_root)
        if args.command == "export":
            return cmd_export(memory_root, store, args.quiet)
        if args.command == "import":
            return cmd_import(memory_root, store, args.force, args.quiet)
        if not args.note:
            raise SyncError("promote requires a note name")
        return cmd_promote(memory_root, store, args.note, args.quiet)
    except SyncError as exc:
        print(f"memory_sync: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
