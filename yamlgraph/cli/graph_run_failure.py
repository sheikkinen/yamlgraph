"""FR-1163: what `graph run` reports when graph execution fails.

A failed run still names what it produced and what it spent: an unmet map
join lists its failures and collected count, and enabled usage trackers
print even with zero recorded calls. Under ``--json`` the report is one
stdout object; human text goes to stderr.
"""

import json
import sys
from argparse import Namespace

from yamlgraph.models.map_results import MapCompletenessError

MESSAGE_CUT = 200


def format_token_line(s: dict) -> str:
    """The token usage line, as printed after a run."""
    return (
        f"\U0001f4ca Token usage: "
        f"{s['total_input_tokens']} in / "
        f"{s['total_output_tokens']} out "
        f"({s['total_calls']} call{'s' if s['total_calls'] != 1 else ''})"
        + (
            f", {s['total_reasoning_tokens']} thinking"
            if s["total_reasoning_tokens"]
            else ""
        )
        + (
            f", {s['total_cache_read_tokens']} cache read"
            if s["total_cache_read_tokens"]
            else ""
        )
        + (
            f", {s['total_cache_write_tokens']} cache write"
            if s["total_cache_write_tokens"]
            else ""
        )
    )


def format_timing_line(ts: dict) -> str:
    """The LLM timing line, as printed after a run."""
    return (
        f"⏱ Timing: {ts['total_duration_s']}s total "
        f"({ts['call_count']} call{'s' if ts['call_count'] != 1 else ''}, "
        f"{ts['mean_duration_s']}s mean)"
    )


def print_usage(tracker, timing_tracker, *, on_failure: bool, file=None) -> None:
    """Print enabled usage lines; on success only trackers with calls print."""
    if tracker is not None and (on_failure or tracker.total_calls > 0):
        print(f"\n{format_token_line(tracker.summary())}", file=file)
    if timing_tracker is not None and (on_failure or timing_tracker.total_calls > 0):
        print(f"\n{format_timing_line(timing_tracker.summary())}", file=file)


def map_failure_lines(exc: MapCompletenessError) -> list[str]:
    """One line per failed branch, then the collected count."""
    lines = []
    for f in exc.failures:
        message = f.message
        if len(message) > MESSAGE_CUT:
            message = message[:MESSAGE_CUT] + "..."
        lines.append(f"   #{f.index} {f.error_type}: {message}")
    lines.append(
        f"   {len(exc.collected)} collected results in '{exc.collect_key}' "
        f"({exc.verdict.succeeded} succeeded in failing dispatch)"
    )
    return lines


def _json_payload(exc: Exception, tracker, timing_tracker) -> dict:
    from yamlgraph.storage.export import _serialize_object

    payload: dict = {"status": "failed", "error": str(exc)}
    if isinstance(exc, MapCompletenessError):
        payload["map"] = {
            "name": exc.map_name,
            "collect_key": exc.collect_key,
            "verdict": exc.verdict.model_dump(),
            "collected": _serialize_object(exc.collected),
            "failures": [f.model_dump() for f in exc.failures],
        }
    if tracker is not None:
        payload["token_usage"] = tracker.summary()
    if timing_tracker is not None:
        payload["timing"] = timing_tracker.summary()
    return payload


def report_execution_failure(
    exc: Exception,
    args: Namespace,
    tracker,
    timing_tracker,
    *,
    json_mode: bool,
) -> None:
    """Report a failed graph execution once: headline, map evidence, usage."""
    stream = sys.stderr if json_mode else sys.stdout
    headline = f"❌ {exc}" if isinstance(exc, TimeoutError) else f"❌ Error: {exc}"
    print(headline, file=stream)
    if json_mode:
        print(json.dumps(_json_payload(exc, tracker, timing_tracker), default=str))
        return
    if isinstance(exc, MapCompletenessError):
        for line in map_failure_lines(exc):
            print(line)
        if getattr(args, "full", False):
            from yamlgraph.cli.graph_run_helpers import _display_result

            _display_result({exc.collect_key: exc.collected}, truncate=False)
    print_usage(tracker, timing_tracker, on_failure=True)
