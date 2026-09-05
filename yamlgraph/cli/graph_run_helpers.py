"""Helpers for graph run command execution."""

from __future__ import annotations

import json
import logging
import sys
from argparse import Namespace
from pathlib import Path

import yaml

from yamlgraph.cli.helpers import handle_state_export

logger = logging.getLogger(__name__)


def _setup_timeout(timeout: int | None) -> dict | None:
    """Set up execution timeout using signal.alarm on Unix."""
    if timeout is None:
        return None

    import platform

    if platform.system() == "Windows":
        logger.warning(
            "Execution timeout is not supported on Windows — ignoring --timeout %d",
            timeout,
        )
        return None

    import signal

    def _timeout_handler(_signum, _frame):
        raise TimeoutError(f"Execution timed out after {timeout}s")

    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(timeout)

    return {"old_handler": old_handler}


def _teardown_timeout(ctx: dict | None) -> None:
    """Cancel timeout alarm and restore previous signal handler."""
    if ctx is None:
        return

    import signal

    signal.alarm(0)
    signal.signal(signal.SIGALRM, ctx["old_handler"])


def _display_result(result: dict, truncate: bool = True) -> None:
    """Display result summary to console."""
    print("=" * 60)
    print("RESULT")
    print("=" * 60)

    skip_keys = {"messages", "errors", "_loop_counts"}
    for key, value in result.items():
        if key.startswith("_") or key in skip_keys:
            continue
        if value is not None:
            value_str = str(value)
            if truncate and len(value_str) > 200:
                value_str = value_str[:200] + "..."
            print(f"  {key}: {value_str}")


def _print_json_result(result: dict) -> None:
    """Print final state as machine-readable JSON to stdout."""
    from yamlgraph.storage.export import _serialize_state

    print(json.dumps(_serialize_state(result), default=str))


def _get_interrupt_message(result: dict) -> str:
    """Extract human-readable message from interrupt."""
    interrupt = result.get("__interrupt__", ())
    if interrupt and len(interrupt) > 0:
        interrupt_obj = interrupt[0]
        if hasattr(interrupt_obj, "value"):
            value = interrupt_obj.value
            if isinstance(value, str):
                return value
            if isinstance(value, dict):
                return value.get("message", value.get("question", str(value)))
    return result.get("response", "Please provide input:")


def _handle_export(graph_path: Path, result: dict, *, quiet: bool = False) -> None:
    """Handle optional result export."""
    from yamlgraph.storage.export import export_result

    with open(graph_path, encoding="utf-8") as f:
        graph_config = yaml.safe_load(f)

    export_config = graph_config.get("exports", {})
    if export_config:
        paths = export_result(result, export_config)
        if paths and not quiet:
            print("\n📁 Exported:")
            for p in paths:
                print(f"   {p}")


def _print_trace_url(tracer: object | None, share: bool = False) -> None:
    """Print LangSmith trace URL after an invoke (FR-022)."""
    if tracer is None:
        return

    from yamlgraph.utils.tracing import get_trace_url, share_trace

    if share:
        url = share_trace(tracer)
        if url:
            print(f"🔗 Trace (public): {url}")
    else:
        url = get_trace_url(tracer)
        if url:
            print(f"🔗 Trace: {url}")


def _build_run_config(args: Namespace, graph_config, initial_state: dict) -> tuple:
    """Build LangGraph run configuration from CLI args and graph config."""
    from yamlgraph.utils.tracing import create_tracer, inject_tracer_config

    yaml_variables = graph_config.raw_config.get("variables") or {}
    if yaml_variables:
        initial_state = {**yaml_variables, **initial_state}
    if graph_config.data:
        initial_state = {**graph_config.data, **initial_state}

    config: dict = {}
    if args.thread:
        config["configurable"] = {"thread_id": args.thread}
        initial_state["thread_id"] = args.thread

    recursion_limit = getattr(args, "recursion_limit", None)
    if recursion_limit is None:
        recursion_limit = graph_config.recursion_limit
    config["recursion_limit"] = recursion_limit

    # FR-984: CLI over YAML; no key at all when neither supplies one
    max_concurrency = getattr(args, "max_concurrency", None)
    if max_concurrency is None:
        max_concurrency = getattr(graph_config, "max_concurrency", None)
    if max_concurrency is not None:
        config["max_concurrency"] = max_concurrency

    timeout = getattr(args, "timeout", None)
    if timeout is None:
        timeout = graph_config.timeout

    tracer = create_tracer()
    inject_tracer_config(config, tracer)
    share_flag = getattr(args, "share_trace", False)

    tracker = None
    if getattr(args, "token_usage", False):
        from yamlgraph.utils.token_tracker import create_token_tracker

        tracker = create_token_tracker()
        config.setdefault("callbacks", []).append(tracker)

    timing_tracker = None
    if getattr(args, "timing", False):
        from yamlgraph.utils.timing_tracker import create_timing_tracker

        timing_tracker = create_timing_tracker()
        config.setdefault("callbacks", []).append(timing_tracker)

    return initial_state, config, tracker, timeout, tracer, share_flag, timing_tracker


def _invoke_graph(app, input_data, config: dict, use_async: bool):
    """Invoke a compiled graph synchronously or asynchronously.

    Sets the route-log thread_id contextvar around invocation (FR-723 R-1):
    routing seams receive state only, so the invoking thread id travels by
    contextvar — null when the run has no thread, never fabricated.
    """
    from yamlgraph.utils.route_log import route_thread_id_from_config

    with route_thread_id_from_config(config):
        if use_async:
            import asyncio

            return asyncio.run(app.ainvoke(input_data, config=config))
        return app.invoke(input_data, config=config)


def _run_graph_until_complete(
    app,
    initial_state: dict,
    config: dict,
    use_async: bool,
    tracer: object | None,
    share_flag: bool,
    *,
    json_mode: bool,
    error_stream,
) -> dict:
    """Run graph and handle optional interrupt resume loop."""
    result = _invoke_graph(app, initial_state, config, use_async)
    if not json_mode:
        _print_trace_url(tracer, share_flag)

    while "__interrupt__" in result:
        if json_mode:
            message = _get_interrupt_message(result)
            print(
                f"❌ --json mode does not support interactive interrupts: {message}",
                file=error_stream,
            )
            sys.exit(1)

        message = _get_interrupt_message(result)
        print(f"\n💬 {message}")
        user_input = input("\n> ").strip()

        if not user_input:
            print("❌ Empty input. Exiting.")
            sys.exit(0)

        from langgraph.types import Command

        result = _invoke_graph(app, Command(resume=user_input), config, use_async)
        _print_trace_url(tracer, share_flag)

    return result


def _emit_success_output(
    args: Namespace,
    result: dict,
    tracker,
    timing_tracker,
    *,
    json_mode: bool,
) -> None:
    """Emit command output for successful execution."""
    if json_mode:
        _print_json_result(result)
        return

    _display_result(result, truncate=not getattr(args, "full", False))

    if tracker is not None and tracker.total_calls > 0:
        s = tracker.summary()
        print(
            f"\n\U0001f4ca Token usage: "
            f"{s['total_input_tokens']} in / "
            f"{s['total_output_tokens']} out "
            f"({s['total_calls']} call{'s' if s['total_calls'] != 1 else ''})"
        )

    if timing_tracker is not None and timing_tracker.total_calls > 0:
        ts = timing_tracker.summary()
        print(
            f"\n⏱ Timing: {ts['total_duration_s']}s total "
            f"({ts['call_count']} call{'s' if ts['call_count'] != 1 else ''}, "
            f"{ts['mean_duration_s']}s mean)"
        )


def _handle_optional_exports(
    args: Namespace,
    graph_path: Path,
    result: dict,
    *,
    json_mode: bool,
    error_stream,
) -> None:
    """Handle optional --export and --export-state behavior."""
    if args.export:
        if json_mode:
            _handle_export(graph_path, result, quiet=True)
        else:
            _handle_export(graph_path, result)

    if getattr(args, "export_state", None):
        handle_state_export(
            result,
            args.export_state,
            quiet=json_mode,
            error_stream=error_stream,
        )
