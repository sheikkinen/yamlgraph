#!/usr/bin/env python3
"""Query LangSmith traces from the command line.

Usage:
    python scripts/langsmith_traces.py                     # latest 5 runs
    python scripts/langsmith_traces.py --limit 20          # latest 20 runs
    python scripts/langsmith_traces.py --failed             # recent failures
    python scripts/langsmith_traces.py --run-id UUID        # single run detail
    python scripts/langsmith_traces.py --children UUID      # child runs of a root
    python scripts/langsmith_traces.py --project NAME       # override project
    python scripts/langsmith_traces.py --status              # check config status

Requires: LANGSMITH_API_KEY (or LANGCHAIN_API_KEY) in env or .env
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_env() -> None:
    """Load .env from repo root if available."""
    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    except ImportError:
        pass


def _get_client():
    """Create a LangSmith client."""
    from langsmith import Client

    return Client()


def _get_project(args) -> str:
    """Resolve project name from args or env."""
    if args.project:
        return args.project
    import os

    return os.environ.get(
        "LANGSMITH_PROJECT",
        os.environ.get("LANGCHAIN_PROJECT", "default"),
    )


def cmd_status(args) -> None:
    """Check LangSmith configuration status."""
    import os

    keys = [
        "LANGSMITH_TRACING",
        "LANGCHAIN_TRACING_V2",
        "LANGSMITH_API_KEY",
        "LANGCHAIN_API_KEY",
        "LANGSMITH_ENDPOINT",
        "LANGCHAIN_ENDPOINT",
        "LANGSMITH_PROJECT",
        "LANGCHAIN_PROJECT",
    ]
    print("=== LangSmith Configuration ===")
    for key in keys:
        val = os.environ.get(key)
        if val is None:
            print(f"  {key}: (not set)")
        elif "KEY" in key:
            print(f"  {key}: {val[:8]}...{val[-4:]}")
        else:
            print(f"  {key}: {val}")

    try:
        from langsmith.utils import tracing_is_enabled

        enabled = tracing_is_enabled()
    except Exception:
        enabled = False
    print(f"\n  Tracing active: {enabled}")

    if enabled:
        try:
            client = _get_client()
            project = _get_project(args)
            runs = list(client.list_runs(project_name=project, is_root=True, limit=1))
            print(f"  Project: {project}")
            print(f"  Runs found: {'yes' if runs else 'none'}")
            if runs:
                print(f"  Latest: {runs[0].start_time} ({runs[0].status})")
        except Exception as e:
            print(f"  Connection test: FAILED ({e})")


def cmd_list(args) -> None:
    """List recent runs."""
    client = _get_client()
    project = _get_project(args)

    kwargs = {
        "project_name": project,
        "is_root": True,
        "limit": args.limit,
    }
    if args.failed:
        kwargs["error"] = True

    runs = list(client.list_runs(**kwargs))
    if not runs:
        print("No runs found.")
        return

    label = "failed " if args.failed else ""
    print(f"=== {len(runs)} latest {label}runs (project: {project}) ===\n")
    for run in runs:
        status_icon = "✓" if run.status == "success" else "✗"
        latency = f"{run.latency:.2f}s" if run.latency else "?"
        tokens = run.total_tokens or 0
        print(
            f"  {status_icon} {run.id}  {run.name:<20} "
            f"{run.start_time:%Y-%m-%d %H:%M:%S}  "
            f"{latency:>8}  {tokens:>6} tok  "
            f"{run.status}"
        )
        if run.error:
            err_preview = run.error[:100].replace("\n", " ")
            print(f"    ↳ {err_preview}")


def cmd_detail(args) -> None:
    """Show detailed info for a single run."""
    client = _get_client()
    project = _get_project(args)

    if args.run_id == "latest":
        runs = list(client.list_runs(project_name=project, is_root=True, limit=1))
        if not runs:
            print("No runs found.")
            return
        run = runs[0]
    else:
        run = client.read_run(args.run_id)

    print("=== Run Detail ===")
    print(f"  ID:          {run.id}")
    print(f"  Name:        {run.name}")
    print(f"  Status:      {run.status}")
    print(f"  Start:       {run.start_time}")
    print(f"  End:         {run.end_time}")
    print(f"  Latency:     {run.latency}s" if run.latency else "")
    print(f"  Total tokens: {run.total_tokens}")
    print(f"  Prompt:      {run.prompt_tokens}")
    print(f"  Completion:  {run.completion_tokens}")
    if run.error:
        print(f"  Error:       {run.error}")
    print()

    print("--- Inputs ---")
    print(json.dumps(run.inputs, indent=2, default=str)[:3000])
    print()
    print("--- Outputs ---")
    print(json.dumps(run.outputs, indent=2, default=str)[:3000])


def cmd_children(args) -> None:
    """Show child runs (node executions) for a root run."""
    client = _get_client()
    project = _get_project(args)

    if args.run_id == "latest":
        runs = list(client.list_runs(project_name=project, is_root=True, limit=1))
        if not runs:
            print("No runs found.")
            return
        root_id = str(runs[0].id)
        print(f"Using latest run: {root_id}\n")
    else:
        root_id = args.run_id

    children = list(
        client.list_runs(
            project_name=project,
            filter=f'eq(parent_run_id, "{root_id}")',
        )
    )
    if not children:
        print("No child runs found.")
        return

    print(f"=== {len(children)} child runs ===\n")
    for child in sorted(children, key=lambda r: r.start_time or ""):
        status_icon = "✓" if child.status == "success" else "✗"
        latency = f"{child.latency:.2f}s" if child.latency else "?"
        tokens = child.total_tokens or 0
        print(
            f"  {status_icon} {child.name:<25} [{child.run_type:<5}] "
            f"{latency:>8}  {tokens:>6} tok  {child.status}"
        )
        if child.error:
            err_preview = child.error[:120].replace("\n", " ")
            print(f"    ↳ {err_preview}")


def main() -> None:
    _load_env()

    parser = argparse.ArgumentParser(
        description="Query LangSmith traces",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--project", type=str, default=None, help="LangSmith project name"
    )

    sub = parser.add_subparsers(dest="command")

    # status
    sub.add_parser("status", help="Check LangSmith configuration")

    # list
    list_p = sub.add_parser("list", help="List recent runs")
    list_p.add_argument(
        "--limit", type=int, default=5, help="Number of runs (default: 5)"
    )
    list_p.add_argument("--failed", action="store_true", help="Show only failed runs")

    # detail
    detail_p = sub.add_parser("detail", help="Show run details")
    detail_p.add_argument(
        "run_id", nargs="?", default="latest", help="Run UUID or 'latest'"
    )

    # children
    children_p = sub.add_parser("children", help="Show child runs")
    children_p.add_argument(
        "run_id", nargs="?", default="latest", help="Root run UUID or 'latest'"
    )

    args = parser.parse_args()

    if args.command is None:
        # Default: list recent runs
        args.limit = 5
        args.failed = False
        cmd_list(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "detail":
        cmd_detail(args)
    elif args.command == "children":
        cmd_children(args)


if __name__ == "__main__":
    main()
