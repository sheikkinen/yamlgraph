"""Diary CLI commands (FR-124).

Implements:
- diary import [--dry-run] [--source DIR]
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from yamlgraph.diary.importer import import_git_reports, import_scheduled_entries


def cmd_diary_import(args: Namespace) -> None:
    """Import pending scheduled insights into docs/diary/."""
    diary_dir = Path("docs/diary")
    source_dir = Path(args.source) if args.source else None
    dry_run = args.dry_run

    if source_dir and not source_dir.exists():
        print(f"⚠️  Source directory not found: {source_dir}")

    if dry_run:
        label = source_dir or "~/scheduled-yamlgraphs/outputs/"
        print(f"📋 Pending scheduled imports ({label}):")

    results = import_scheduled_entries(diary_dir, source_dir, dry_run=dry_run)
    results += import_git_reports(diary_dir, source_dir, dry_run=dry_run)

    if not results:
        print("Nothing to import.")
        return

    has_errors = False
    for r in results:
        if r.status == "error":
            print(f"✗ {r.filename}: {r.message}")
            has_errors = True
        elif r.status == "skipped":
            print(f"⏭️  {r.filename} ({r.message})")
        elif dry_run:
            print(f"  📝 {r.filename}  ({r.entry_type})")
        else:
            print(f"✓ Imported {r.filename} ({r.entry_type})")

    count = sum(1 for r in results if r.status == "imported")
    if dry_run:
        pending = sum(1 for r in results if r.status != "error")
        print(f"\n{pending} file(s) ready to import. Run without --dry-run to apply.")
    else:
        print(f"\n{count} file(s) imported into {diary_dir}/.")

    if has_errors:
        raise SystemExit(1)


def cmd_diary_dispatch(args: Namespace) -> None:
    """Dispatch to diary subcommands."""
    if args.diary_command == "import":
        cmd_diary_import(args)
    else:
        print("Unknown diary command. Use: yamlgraph diary import --help")
        raise SystemExit(1)
