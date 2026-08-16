"""Graph commands for universal graph runner.

Implements:
- graph run <path> --var key=value --var-file vars.yaml
- graph info <path>
- graph lint <path>
- graph validate <path>
- graph codegen <path> [--output FILE] [--include-base]
"""

import sys
from argparse import Namespace
from pathlib import Path

from yamlgraph.cli import graph_run_helpers as _graph_run_helpers
from yamlgraph.cli.graph_validate import cmd_graph_lint, cmd_graph_validate
from yamlgraph.cli.helpers import (
    GraphLoadError,
    load_graph_config,
    load_imported_state,
    load_var_file,
    parse_vars,
    require_graph_config,
)
from yamlgraph.executor_async import run_graph_streaming_native
from yamlgraph.models.state_codegen import generate_typeddict_code

_setup_timeout = _graph_run_helpers._setup_timeout
_teardown_timeout = _graph_run_helpers._teardown_timeout
_display_result = _graph_run_helpers._display_result
_print_json_result = _graph_run_helpers._print_json_result
_get_interrupt_message = _graph_run_helpers._get_interrupt_message
_handle_export = _graph_run_helpers._handle_export
_print_trace_url = _graph_run_helpers._print_trace_url
_build_run_config = _graph_run_helpers._build_run_config
_invoke_graph = _graph_run_helpers._invoke_graph
_run_graph_until_complete = _graph_run_helpers._run_graph_until_complete
_emit_success_output = _graph_run_helpers._emit_success_output
_handle_optional_exports = _graph_run_helpers._handle_optional_exports


def _run_streaming(graph_path: str, initial_state: dict, config: dict) -> None:
    """Execute graph in streaming mode, printing tokens to stdout (FR-633)."""
    import asyncio

    from yamlgraph.models.streaming import StreamEvent

    async def _stream():
        async for item in run_graph_streaming_native(
            graph_path, initial_state, config=config
        ):
            if isinstance(item, StreamEvent):
                if item.type == "error":
                    print(f"\n❌ {item.error}", file=sys.stderr)
            else:
                print(item, end="", flush=True)
        print()  # Final newline

    asyncio.run(_stream())


def _run_lint_gate(graph_path: Path, *, json_mode: bool) -> None:
    """FR-677: lint the graph and refuse to run on any error-level finding.

    Error-level findings block execution with a non-zero exit; warning-level
    findings are reported but do not block. In ``--json`` mode the lint report
    is emitted as JSON to stdout with no decorative text; otherwise a
    human-readable report is printed.
    """
    from yamlgraph.config import WORKING_DIR
    from yamlgraph.linter import lint_graph

    try:
        result = lint_graph(graph_path, WORKING_DIR)
    except Exception as e:
        print(f"❌ Error linting {graph_path}: {e}", file=sys.stderr)
        sys.exit(1)

    errors = [issue for issue in result.issues if issue.severity == "error"]

    if json_mode:
        # Machine-readable: only emit decorative text when blocking.
        if errors:
            print(result.model_dump_json())
            sys.exit(1)
        return

    for issue in result.issues:
        icon = "❌" if issue.severity == "error" else "⚠"
        print(f"   {icon} [{issue.code}] {issue.message}", file=sys.stderr)
        if issue.fix:
            print(f"      Fix: {issue.fix}", file=sys.stderr)

    if errors:
        print(
            f"❌ Gate blocked: {len(errors)} error-level lint finding(s) in "
            f"{graph_path.name}; run aborted.",
            file=sys.stderr,
        )
        sys.exit(1)


def cmd_graph_run(args: Namespace) -> None:
    """Run any graph with provided variables.

    Usage:
        yamlgraph graph run graphs/yamlgraph.yaml --var topic=AI --var style=casual
    """
    from yamlgraph.compile.graph_loader import (
        compile_graph,
        get_checkpointer_for_graph,
        load_graph_config,
    )

    graph_path = Path(args.graph_path)
    json_mode = getattr(args, "json", False)
    stream_mode = getattr(args, "stream", False)
    error_stream = sys.stderr if json_mode else sys.stdout

    if stream_mode and json_mode:
        print("❌ --stream and --json are mutually exclusive", file=sys.stderr)
        sys.exit(1)

    if not graph_path.exists():
        print(f"❌ Graph file not found: {graph_path}", file=error_stream)
        sys.exit(1)

    # FR-677: opt-in lint gate — refuse to run on error-level findings.
    if getattr(args, "gate", False):
        _run_lint_gate(graph_path, json_mode=json_mode)

    # Parse variables: --var-file provides base, --var overrides
    try:
        file_vars = load_var_file(getattr(args, "var_file", None))
        cli_vars = parse_vars(args.var)
    except (ValueError, FileNotFoundError) as e:
        print(f"❌ {e}", file=error_stream)
        sys.exit(1)

    # FR-269: Import state from prior run as base layer
    imported_state = load_imported_state(
        getattr(args, "import_state", None),
        error_stream=error_stream,
    )

    # Merge: imported < var-file < CLI vars
    initial_state = {**imported_state, **file_vars, **cli_vars}

    if not json_mode:
        print(f"\n🚀 Running graph: {graph_path.name}")
        if initial_state:
            print(f"   Variables: {initial_state}")
        print()

    try:
        # Load config and compile with checkpointer
        graph_config = load_graph_config(str(graph_path))
        graph = compile_graph(graph_config)
        checkpointer = get_checkpointer_for_graph(graph_config)
        app = graph.compile(checkpointer=checkpointer)

        # Build run configuration (data merge, thread, limits, tracing, tokens, timing)
        initial_state, config, tracker, timeout, tracer, share_flag, timing_tracker = (
            _build_run_config(args, graph_config, initial_state)
        )

        # FR-633: Streaming mode — bypass invoke, use native streaming
        if stream_mode:
            _run_streaming(str(graph_path), initial_state, config)
            return

        use_async = getattr(args, "use_async", False)

        # FR-027: Set up timeout guard (signal.alarm on Unix)
        timeout_ctx = _setup_timeout(timeout)

        from contextlib import nullcontext

        from yamlgraph.observability.otel import generate_run_id, graph_run_span
        from yamlgraph.utils.route_log import route_log_enabled, route_run_context

        thread_id = config.get("configurable", {}).get("thread_id")
        run_id = generate_run_id()
        route_context = (
            route_run_context(graph_path, thread_id=thread_id, run_id=run_id)
            if route_log_enabled() and graph_path.is_file()
            else nullcontext()
        )
        with (
            graph_run_span(
                graph_config.name, initial_state, thread_id=thread_id, run_id=run_id
            ) as run_ctx,
            route_context,
        ):
            try:
                result = _run_graph_until_complete(
                    app,
                    initial_state,
                    config,
                    use_async,
                    tracer,
                    share_flag,
                    json_mode=json_mode,
                    error_stream=error_stream,
                )
            except TimeoutError as te:
                print(f"❌ {te}", file=error_stream)
                sys.exit(1)
            finally:
                _teardown_timeout(timeout_ctx)

            if "__interrupt__" in result:
                run_ctx.outcome = "interrupted"

        _emit_success_output(
            args,
            result,
            tracker,
            timing_tracker,
            json_mode=json_mode,
        )
        _graph_run_helpers._handle_export = _handle_export
        _handle_optional_exports(
            args,
            graph_path,
            result,
            json_mode=json_mode,
            error_stream=error_stream,
        )

        if not json_mode:
            print()

    except Exception as e:
        print(f"❌ Error: {e}", file=error_stream)
        sys.exit(1)


def cmd_graph_info(args: Namespace) -> None:
    """Show information about a graph."""
    graph_path = Path(args.graph_path)

    try:
        config = require_graph_config(graph_path)

        name = config.get("name", graph_path.stem)
        description = config.get("description", "No description")
        nodes = config.get("nodes", {})
        edges = config.get("edges", [])

        print(f"\n📊 Graph: {name}")
        print(f"   {description}")

        # Show nodes
        print(f"\n   Nodes ({len(nodes)}):")
        for node_name, node_config in nodes.items():
            node_type = node_config.get("type", "prompt")
            print(f"     - {node_name} ({node_type})")

        # Show edges
        print(f"\n   Edges ({len(edges)}):")
        for edge in edges:
            from_node = edge.get("from", "?")
            to_node = edge.get("to", "?")
            condition = edge.get("condition", "")
            if condition:
                print(f"     {from_node} → {to_node} (conditional)")
            else:
                print(f"     {from_node} → {to_node}")

        # Show required inputs if defined
        inputs = config.get("inputs", {})
        if inputs:
            print(f"\n   Inputs ({len(inputs)}):")
            for input_name, input_config in inputs.items():
                required = input_config.get("required", False)
                default = input_config.get("default", None)
                req_str = " (required)" if required else f" (default: {default})"
                print(f"     --var {input_name}=<value>{req_str}")

        print()

    except GraphLoadError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading graph: {e}")
        sys.exit(1)


def cmd_graph_codegen(args: Namespace) -> None:
    """Generate TypedDict Python code for IDE support (FR-008).

    Reads graph YAML, generates TypedDict code with proper type hints,
    and writes to file or stdout.
    """
    try:
        config = load_graph_config(args.graph_path)
        source_path = str(args.graph_path)
        include_base = getattr(args, "include_base", False)

        code = generate_typeddict_code(config, source_path, include_base)

        output_path = getattr(args, "output", None)
        if output_path:
            Path(output_path).write_text(code)
            print(f"✓ Generated TypedDict code: {output_path}")
        else:
            print(code)

    except GraphLoadError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error generating TypedDict code: {e}")
        sys.exit(1)


def cmd_graph_dispatch(args: Namespace) -> None:
    """Dispatch to graph subcommands."""
    if args.graph_command == "run":
        cmd_graph_run(args)
    elif args.graph_command == "info":
        cmd_graph_info(args)
    elif args.graph_command == "validate":
        cmd_graph_validate(args)
    elif args.graph_command == "lint":
        cmd_graph_lint(args)
    elif args.graph_command == "codegen":
        cmd_graph_codegen(args)
    elif args.graph_command == "bench":
        from yamlgraph.cli.bench_commands import cmd_graph_bench

        cmd_graph_bench(args)
    elif args.graph_command == "export":
        from yamlgraph.cli.export_commands import cmd_graph_export

        cmd_graph_export(args)
    else:
        print(f"Unknown graph command: {args.graph_command}")
        sys.exit(1)
