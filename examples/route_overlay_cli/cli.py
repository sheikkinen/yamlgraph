#!/usr/bin/env python3
"""Route overlay example CLI using Mermaid CLI (mmdc).

This example is intentionally separate from the core YAMLGraph CLI.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from yamlgraph.compile.graph_loader import load_graph_config
from yamlgraph.mermaid_export import parse_route_lines, render_mermaid, render_overlay


class CliError(Exception):
    """Error carrying an explicit process exit code."""

    def __init__(self, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render authored + route-overlay Mermaid outputs with mmdc"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    render = sub.add_parser("render", help="Render authored and overlay diagrams")
    render.add_argument("--graph", required=True, help="Path to graph YAML file")
    render.add_argument("--route", required=True, help="Path to route JSONL file")
    render.add_argument(
        "--out-dir",
        default="examples/route_overlay_cli/outputs",
        help="Output directory for .mmd and rendered images",
    )
    render.add_argument(
        "--format",
        choices=["svg", "png"],
        default="svg",
        help="Rendered image format",
    )
    return parser


def _ensure_file(path: Path, label: str) -> None:
    if not path.exists() or not path.is_file():
        raise CliError(f"{label} file not found: {path}", 2)


def _load_graph_dict(graph_path: Path) -> dict:
    try:
        config = load_graph_config(graph_path)
    except Exception as exc:
        raise CliError(f"Failed to load graph '{graph_path}': {exc}", 2) from exc
    return config.raw_config


def _load_route_events(route_path: Path) -> list[dict]:
    lines = route_path.read_text(encoding="utf-8").splitlines()
    route = parse_route_lines(lines)
    if len(route) < 1:
        raise CliError(
            f"Route file '{route_path}' contains no valid route events.",
            2,
        )
    return route


def _discover_mmdc() -> str:
    mmdc = shutil.which("mmdc")
    if not mmdc:
        raise CliError(
            "mmdc not found. Install with: npm i -g @mermaid-js/mermaid-cli",
            2,
        )
    return mmdc


def _run_mmdc(mmdc: str, input_path: Path, output_path: Path) -> None:
    try:
        subprocess.run(
            [mmdc, "-i", str(input_path), "-o", str(output_path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise CliError(
            f"mmdc failed for '{input_path}' -> '{output_path}': {detail}",
            1,
        ) from exc


def _cmd_render(args: argparse.Namespace) -> int:
    graph_path = Path(args.graph)
    route_path = Path(args.route)
    out_dir = Path(args.out_dir)

    _ensure_file(graph_path, "Graph")
    _ensure_file(route_path, "Route")

    graph_dict = _load_graph_dict(graph_path)
    route = _load_route_events(route_path)
    mmdc = _discover_mmdc()

    out_dir.mkdir(parents=True, exist_ok=True)

    authored_mmd = out_dir / "graph.authored.mmd"
    overlay_mmd = out_dir / "graph.overlay.mmd"
    authored_img = out_dir / f"graph.authored.{args.format}"
    overlay_img = out_dir / f"graph.overlay.{args.format}"

    authored_mmd.write_text(render_mermaid(graph_dict), encoding="utf-8")
    overlay_mmd.write_text(render_overlay(graph_dict, route), encoding="utf-8")

    _run_mmdc(mmdc, authored_mmd, authored_img)
    _run_mmdc(mmdc, overlay_mmd, overlay_img)

    print(f"authored_mmd={authored_mmd}")
    print(f"overlay_mmd={overlay_mmd}")
    print(f"authored_image={authored_img}")
    print(f"overlay_image={overlay_img}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "render":
            return _cmd_render(args)
        parser.print_help()
        return 2
    except CliError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
