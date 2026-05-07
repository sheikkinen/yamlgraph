"""Skill CLI commands for portable skill export (FR-348)."""

from __future__ import annotations

import argparse
import sys

from yamlgraph.skill_export import export_skill


def cmd_skill_export(args: argparse.Namespace) -> None:
    """Export a graph as a portable skill package."""
    try:
        package = export_skill(
            graph_path_or_dir=args.graph_path_or_dir,
            format=args.format,
            output_dir=args.output_dir,
        )
        target = package.target_file or package.target_dir
        print(f"✓ Skill exported: {target}")
    except Exception as exc:
        print(f"❌ Error exporting skill: {exc}")
        sys.exit(1)


def cmd_skill_dispatch(args: argparse.Namespace) -> None:
    """Dispatch skill subcommands."""
    if args.skill_command == "export":
        cmd_skill_export(args)
    else:
        print(f"Unknown skill command: {args.skill_command}")
        sys.exit(1)
