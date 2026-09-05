"""YamlGraph CLI - Command-line interface for yamlgraph.

This package provides the CLI entry point and command implementations.

Usage:
    yamlgraph graph run examples/demos/yamlgraph/graph.yaml --var topic="AI"
    yamlgraph graph info examples/npc/npc-creation.yaml
"""

import argparse
import sys

from yamlgraph.cli.diary_commands import cmd_diary_dispatch
from yamlgraph.cli.graph_commands import cmd_graph_dispatch
from yamlgraph.cli.schema_commands import cmd_schema_dispatch

__all__ = [
    # Entry points
    "main",
    "create_parser",
]


def _positive_int(text: str) -> int:
    """argparse type: reject 0 and negatives before any graph is invoked."""
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {text}")
    return value


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the CLI argument parser.

    Returns:
        Configured ArgumentParser for testing and main().
    """
    parser = argparse.ArgumentParser(
        description="YAMLGraph - YAML-first LLM Pipeline Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Graph command group (universal runner)

    graph_parser = subparsers.add_parser(
        "graph", help="Universal graph runner and utilities"
    )
    graph_subparsers = graph_parser.add_subparsers(
        dest="graph_command", help="Graph commands"
    )

    # graph run
    graph_run_parser = graph_subparsers.add_parser("run", help="Run any graph")
    graph_run_parser.add_argument("graph_path", help="Path to graph YAML file")
    graph_run_parser.add_argument(
        "--var",
        "-v",
        action="append",
        default=[],
        help="Set state variable (key=value or key=@file.txt), can repeat",
    )
    graph_run_parser.add_argument(
        "--var-file",
        type=str,
        default=None,
        dest="var_file",
        help="Load variables from YAML/JSON file (--var overrides)",
    )
    graph_run_parser.add_argument(
        "--tool",
        action="append",
        default=[],
        dest="tool_bindings",
        help="Bind a tool slot to an FR-768 manifest (SLOT=manifest.yaml), can repeat",
    )
    graph_run_parser.add_argument(
        "--thread", "-t", type=str, default=None, help="Thread ID for persistence"
    )
    graph_run_parser.add_argument(
        "--export", "-e", action="store_true", help="Export results to files"
    )
    graph_run_parser.add_argument(
        "--full", "-f", action="store_true", help="Show full output without truncation"
    )
    graph_run_parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Emit final graph state as JSON to stdout (machine-readable mode)",
    )
    graph_run_parser.add_argument(
        "--async",
        "-a",
        action="store_true",
        dest="use_async",
        help="Use async execution for parallel map nodes (recommended for Mistral)",
    )
    graph_run_parser.add_argument(
        "--share-trace",
        action="store_true",
        dest="share_trace",
        help="Share LangSmith trace publicly and display the URL",
    )
    graph_run_parser.add_argument(
        "--recursion-limit",
        type=int,
        default=None,
        dest="recursion_limit",
        help="Override LangGraph recursion limit (default: from YAML config or 50)",
    )
    graph_run_parser.add_argument(
        "--max-concurrency",
        type=_positive_int,
        default=None,
        dest="max_concurrency",
        help=(
            "Cap parallel map branches for the whole run (LangGraph "
            "max_concurrency); overrides config.max_concurrency in the YAML"
        ),
    )
    graph_run_parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        dest="timeout",
        help="Global execution timeout in seconds (default: from YAML config or None)",
    )
    graph_run_parser.add_argument(
        "--token-usage",
        action="store_true",
        dest="token_usage",
        help="Track and display token usage summary after execution",
    )
    graph_run_parser.add_argument(
        "--timing",
        action="store_true",
        dest="timing",
        help="Track and display LLM call timing summary after execution",
    )
    graph_run_parser.add_argument(
        "--import-state",
        type=str,
        default=None,
        dest="import_state",
        help="Load initial state from JSON file exported by --export-state",
    )
    graph_run_parser.add_argument(
        "--export-state",
        type=str,
        default=None,
        dest="export_state",
        help="Write full state JSON to this path after run (for inter-run chaining)",
    )
    graph_run_parser.add_argument(
        "--stream",
        action="store_true",
        default=False,
        help="Stream LLM tokens to stdout in real-time (mutually exclusive with --json)",
    )
    graph_run_parser.add_argument(
        "--gate",
        action="store_true",
        default=False,
        help="Lint the graph first; refuse to run on any error-level finding (FR-677)",
    )

    # graph info
    graph_info_parser = graph_subparsers.add_parser(
        "info", help="Show graph information"
    )
    graph_info_parser.add_argument("graph_path", help="Path to graph YAML file")

    # graph validate
    graph_validate_parser = graph_subparsers.add_parser(
        "validate", help="Validate graph YAML schema"
    )
    graph_validate_parser.add_argument("graph_path", help="Path to graph YAML file")

    # graph lint
    graph_lint_parser = graph_subparsers.add_parser(
        "lint", help="Lint graph for issues (missing state, unused tools, etc.)"
    )
    graph_lint_parser.add_argument(
        "graph_path", nargs="+", help="Path(s) to graph YAML file(s)"
    )
    graph_lint_parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Emit per-file lint results as NDJSON to stdout (machine-readable mode)",
    )

    # graph codegen (FR-008)
    graph_codegen_parser = graph_subparsers.add_parser(
        "codegen", help="Generate TypedDict Python code for IDE support"
    )
    graph_codegen_parser.add_argument("graph_path", help="Path to graph YAML file")
    graph_codegen_parser.add_argument(
        "--output", "-o", type=str, help="Output file (default: stdout)"
    )
    graph_codegen_parser.add_argument(
        "--include-base",
        action="store_true",
        help="Include infrastructure fields (thread_id, errors, etc.)",
    )

    # graph bench (FR-231)
    graph_bench_parser = graph_subparsers.add_parser(
        "bench", help="Benchmark graph across multiple provider/model combinations"
    )
    graph_bench_parser.add_argument("graph_path", help="Path to graph YAML file")
    graph_bench_parser.add_argument(
        "--models",
        nargs="+",
        required=True,
        help="Provider/model specs (e.g. anthropic/claude-sonnet-4-20250514 openai/gpt-4o)",
    )
    graph_bench_parser.add_argument(
        "--var",
        "-v",
        action="append",
        default=[],
        help="Set state variable (key=value), can repeat",
    )
    graph_bench_parser.add_argument(
        "--var-file",
        type=str,
        default=None,
        dest="var_file",
        help="Load variables from YAML/JSON file (--var overrides)",
    )
    graph_bench_parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Number of times to run each model (default: 1)",
    )
    graph_bench_parser.add_argument(
        "--export",
        type=str,
        default=None,
        dest="bench_export",
        help="Export results to JSON file",
    )
    graph_bench_parser.add_argument(
        "--full",
        "-f",
        action="store_true",
        help="Show full output per model in display",
    )

    # graph export (FR-723)
    graph_export_parser = graph_subparsers.add_parser(
        "export", help="Export authored graph as Mermaid; overlay/diff routes"
    )
    graph_export_parser.add_argument(
        "graph_path", nargs="?", default=None, help="Path to graph YAML file"
    )
    graph_export_parser.add_argument(
        "--mermaid",
        action="store_true",
        default=False,
        help="Render the authored graph as a Mermaid flowchart",
    )
    graph_export_parser.add_argument(
        "--overlay",
        type=str,
        default=None,
        help="route.jsonl to overlay on the map (taken edges + decision ordinals)",
    )
    graph_export_parser.add_argument(
        "--diff",
        nargs=2,
        metavar=("A", "B"),
        default=None,
        help="Diff two route.jsonl files occurrence-aligned (exit 1 on divergence)",
    )
    graph_export_parser.add_argument(
        "--output", "-o", type=str, default=None, help="Output file (default: stdout)"
    )

    graph_parser.set_defaults(func=cmd_graph_dispatch)

    # === Schema commands (FR-009) ===
    schema_parser = subparsers.add_parser(
        "schema", help="JSON Schema export for IDE support"
    )
    schema_subparsers = schema_parser.add_subparsers(
        dest="schema_command", help="Schema subcommands"
    )

    # schema export
    schema_export_parser = schema_subparsers.add_parser(
        "export", help="Export graph schema as JSON Schema"
    )
    schema_export_parser.add_argument(
        "--output", "-o", type=str, help="Output file (default: stdout)"
    )

    # schema path
    schema_subparsers.add_parser("path", help="Print path to bundled JSON Schema")

    schema_parser.set_defaults(func=cmd_schema_dispatch)

    # === Diary commands (FR-124) ===
    diary_parser = subparsers.add_parser("diary", help="Diary management commands")
    diary_subparsers = diary_parser.add_subparsers(
        dest="diary_command", help="Diary subcommands"
    )

    # diary import
    diary_import_parser = diary_subparsers.add_parser(
        "import", help="Import pending scheduled insights into docs/diary/"
    )
    diary_import_parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Show pending imports without modifying diary",
    )
    diary_import_parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Override source base directory (default: ~/scheduled-yamlgraphs/outputs/)",
    )

    diary_parser.set_defaults(func=cmd_diary_dispatch)

    return parser


def main():
    """Main CLI entry point."""
    # FR-951: declare the codec of our own streams so status glyphs survive a
    # pipe on hosts whose preferred encoding is not UTF-8.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="backslashreplace")

    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
