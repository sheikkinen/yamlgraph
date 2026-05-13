"""YamlGraph CLI - Command-line interface for yamlgraph.

This package provides the CLI entry point and command implementations.

Usage:
    yamlgraph graph run examples/demos/yamlgraph/graph.yaml --var topic="AI"
    yamlgraph graph info examples/npc/npc-creation.yaml
"""

import argparse

from yamlgraph.cli.a2a_commands import cmd_a2a_dispatch
from yamlgraph.cli.diary_commands import cmd_diary_dispatch
from yamlgraph.cli.graph_commands import cmd_graph_dispatch
from yamlgraph.cli.schema_commands import cmd_schema_dispatch
from yamlgraph.cli.skill_commands import cmd_skill_dispatch

__all__ = [
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

    # === Skill commands (FR-348) ===
    skill_parser = subparsers.add_parser(
        "skill", help="Portable skill packaging and export"
    )
    skill_subparsers = skill_parser.add_subparsers(
        dest="skill_command", help="Skill subcommands"
    )

    # skill export
    skill_export_parser = skill_subparsers.add_parser(
        "export", help="Export graph as portable skill package"
    )
    skill_export_parser.add_argument(
        "graph_path_or_dir",
        help="Path to graph YAML file or a directory containing graph.yaml",
    )
    skill_export_parser.add_argument(
        "--format",
        choices=["skill-md", "copilot", "cursor", "agent-md"],
        default="skill-md",
        help="Target format layout (default: skill-md)",
    )
    skill_export_parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        dest="output_dir",
        help="Base output directory (default: output)",
    )

    skill_parser.set_defaults(func=cmd_skill_dispatch)

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

    # === A2A commands (FR-208) ===
    a2a_parser = subparsers.add_parser("a2a", help="A2A protocol server commands")
    a2a_subparsers = a2a_parser.add_subparsers(
        dest="a2a_command", help="A2A subcommands"
    )

    # a2a serve
    a2a_serve_parser = a2a_subparsers.add_parser(
        "serve", help="Start A2A HTTP server exposing graphs as agents"
    )
    a2a_serve_parser.add_argument(
        "graph_path",
        nargs="?",
        default=None,
        help="Path to graph YAML file or directory (default: auto-discover)",
    )
    a2a_serve_parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",  # noqa: S104
        help="Server host (default: 0.0.0.0)",
    )
    a2a_serve_parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8080,
        help="Server port (default: 8080)",
    )

    # a2a card
    a2a_card_parser = a2a_subparsers.add_parser(
        "card", help="Print Agent Card JSON for a graph"
    )
    a2a_card_parser.add_argument(
        "graph_path",
        nargs="?",
        default=None,
        help="Path to graph YAML file or directory",
    )
    a2a_card_parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Hostname for Agent Card URL (default: localhost)",
    )
    a2a_card_parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8080,
        help="Port for Agent Card URL (default: 8080)",
    )

    a2a_parser.set_defaults(func=cmd_a2a_dispatch)

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
