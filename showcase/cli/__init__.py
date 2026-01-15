"""Showcase CLI - Command-line interface for the showcase app.

This package provides the CLI entry point and command implementations.

Usage:
    showcase run --topic "machine learning" --style casual
    showcase list-runs
    showcase resume --thread-id abc123
    showcase route "I love this product!"
    showcase refine --topic "climate change"
    showcase trace --run-id <run-id>
"""

import argparse

# Import submodules for package access
from showcase.cli import commands, validators

# Re-export validators for backward compatibility
from showcase.cli.validators import (
    validate_refine_args,
    validate_route_args,
    validate_run_args,
)

# Re-export commands for backward compatibility
from showcase.cli.commands import (
    cmd_export,
    cmd_git_report,
    cmd_graph,
    cmd_list_runs,
    cmd_memory_demo,
    cmd_refine,
    cmd_resume,
    cmd_route,
    cmd_run,
    cmd_trace,
)

__all__ = [
    # Submodules
    "commands",
    "validators",
    # Validators
    "validate_run_args",
    "validate_route_args",
    "validate_refine_args",
    # Commands
    "cmd_run",
    "cmd_route",
    "cmd_refine",
    "cmd_memory_demo",
    "cmd_git_report",
    "cmd_list_runs",
    "cmd_resume",
    "cmd_trace",
    "cmd_export",
    "cmd_graph",
    # Entry points
    "main",
    "create_parser",
]


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the CLI argument parser.

    Returns:
        Configured ArgumentParser for testing and main().
    """
    parser = argparse.ArgumentParser(
        description="Showcase App - LangGraph Pipeline Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run the pipeline")
    run_parser.add_argument(
        "--topic", "-t", required=True, help="Topic to generate content about"
    )
    run_parser.add_argument(
        "--style",
        "-s",
        default="informative",
        choices=["informative", "casual", "technical"],
        help="Writing style",
    )
    run_parser.add_argument(
        "--word-count", "-w", type=int, default=300, help="Target word count"
    )
    run_parser.add_argument(
        "--export", "-e", action="store_true", help="Export result to JSON"
    )
    run_parser.add_argument(
        "--thread",
        type=str,
        default=None,
        help="Thread ID for conversation persistence",
    )
    run_parser.set_defaults(func=cmd_run)

    # List runs command
    list_parser = subparsers.add_parser("list-runs", help="List recent runs")
    list_parser.add_argument(
        "--limit", "-l", type=int, default=10, help="Maximum runs to show"
    )
    list_parser.set_defaults(func=cmd_list_runs)

    # Route command (router demo)
    route_parser = subparsers.add_parser(
        "route", help="Run router demo (tone classification)"
    )
    route_parser.add_argument("message", help="Message to classify and route")
    route_parser.set_defaults(func=cmd_route)

    # Refine command (reflexion demo)
    refine_parser = subparsers.add_parser(
        "refine", help="Run reflexion demo (self-refinement loop)"
    )
    refine_parser.add_argument(
        "--topic", "-t", required=True, help="Topic to write about"
    )
    refine_parser.set_defaults(func=cmd_refine)

    # Git-report command (agent demo)
    git_parser = subparsers.add_parser(
        "git-report", help="Analyze git repo with AI agent"
    )
    git_parser.add_argument(
        "--query",
        "-q",
        required=True,
        help="What to analyze (e.g., 'recent changes', 'test activity')",
    )
    git_parser.add_argument(
        "--repo", "-r", default=".", help="Repository path (default: current directory)"
    )
    git_parser.set_defaults(func=cmd_git_report)

    # Memory-demo command (multi-turn agent with memory)
    memory_parser = subparsers.add_parser(
        "memory-demo", help="Multi-turn code review with memory"
    )
    memory_parser.add_argument(
        "--input", "-i", required=True, help="Query or follow-up question"
    )
    memory_parser.add_argument(
        "--thread",
        "-t",
        type=str,
        default=None,
        help="Thread ID to continue conversation",
    )
    memory_parser.add_argument(
        "--repo", "-r", default=".", help="Repository path (default: current directory)"
    )
    memory_parser.add_argument(
        "--export", "-e", action="store_true", help="Export results to files"
    )
    memory_parser.set_defaults(func=cmd_memory_demo)

    # Resume command
    resume_parser = subparsers.add_parser("resume", help="Resume a pipeline")
    resume_parser.add_argument(
        "--thread-id", "-i", required=True, help="Thread ID to resume"
    )
    resume_parser.set_defaults(func=cmd_resume)

    # Trace command
    trace_parser = subparsers.add_parser("trace", help="Show execution trace")
    trace_parser.add_argument(
        "--run-id", "-r", help="Run ID (uses latest if not provided)"
    )
    trace_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Include timing details"
    )
    trace_parser.set_defaults(func=cmd_trace)

    # Export command
    export_parser = subparsers.add_parser("export", help="Export a run to JSON")
    export_parser.add_argument(
        "--thread-id", "-i", required=True, help="Thread ID to export"
    )
    export_parser.set_defaults(func=cmd_export)

    # Graph command
    graph_parser = subparsers.add_parser("graph", help="Show pipeline graph (Mermaid)")
    graph_parser.add_argument(
        "--type",
        "-t",
        default="main",
        choices=["main", "resume-analyze", "resume-summarize"],
        help="Graph type to show",
    )
    graph_parser.set_defaults(func=cmd_graph)

    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
