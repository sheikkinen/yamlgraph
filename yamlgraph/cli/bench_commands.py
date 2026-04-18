"""Bench command for multi-model comparison (FR-231 Phase 2, REQ-YG-232).

Runs a graph against multiple provider/model combinations and displays
a side-by-side comparison of execution time, token usage, and output.

Usage::

    yamlgraph graph bench examples/demos/hello/graph.yaml \\
        --models anthropic/claude-sonnet-4-20250514 openai/gpt-4o \\
        --var name=World --runs 1
"""

from __future__ import annotations

import json
import logging
import sys
import time
from argparse import Namespace
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Pydantic models
# =============================================================================


class BenchResult(BaseModel):
    """Result of a single model benchmark run."""

    provider: str
    model: str
    duration_s: float
    tokens_in: int = 0
    tokens_out: int = 0
    status: str  # "success" or "error"
    output: dict = Field(default_factory=dict)
    error: str | None = None


# =============================================================================
# Model spec parsing
# =============================================================================


def parse_model_spec(spec: str) -> tuple[str, str]:
    """Parse a 'provider/model' spec into (provider, model) tuple.

    Args:
        spec: Model specification in 'provider/model' format.
              Models with slashes (e.g. replicate/owner/model) are supported.

    Returns:
        Tuple of (provider, model).

    Raises:
        ValueError: If spec doesn't contain '/'.
    """
    if "/" not in spec:
        raise ValueError(
            f"Invalid model spec '{spec}': expected 'provider/model' format "
            f"(e.g. 'anthropic/claude-sonnet-4-20250514')"
        )
    provider, model = spec.split("/", 1)
    return provider, model


# =============================================================================
# Table formatting
# =============================================================================


def format_bench_table(results: list[BenchResult], full: bool = False) -> str:
    """Format benchmark results as a comparison table.

    Args:
        results: List of BenchResult objects.
        full: If True, include full output per model.

    Returns:
        Formatted table string.
    """
    # Column widths
    model_col = max(len(f"{r.provider}/{r.model}") for r in results)
    model_col = max(model_col, len("Model"))

    header = (
        f"{'Model':<{model_col}}  "
        f"{'Duration':>10}  "
        f"{'Tokens In':>10}  "
        f"{'Tokens Out':>10}  "
        f"{'Status':>8}"
    )
    sep = "-" * len(header)

    lines = [sep, header, sep]

    for r in results:
        model_name = f"{r.provider}/{r.model}"
        status = "✓" if r.status == "success" else "✗"
        duration = f"{r.duration_s:.2f}s" if r.status == "success" else "—"
        tokens_in = str(r.tokens_in) if r.tokens_in > 0 else "—"
        tokens_out = str(r.tokens_out) if r.tokens_out > 0 else "—"

        lines.append(
            f"{model_name:<{model_col}}  "
            f"{duration:>10}  "
            f"{tokens_in:>10}  "
            f"{tokens_out:>10}  "
            f"{status:>8}"
        )

        if r.status == "error" and r.error:
            lines.append(f"  ↳ {r.error}")

        if full and r.status == "success" and r.output:
            for key, value in r.output.items():
                if key.startswith("_") or key in {"messages", "errors", "_loop_counts"}:
                    continue
                if value is not None:
                    val_str = str(value)
                    if len(val_str) > 200:
                        val_str = val_str[:200] + "..."
                    lines.append(f"  {key}: {val_str}")

    lines.append(sep)
    return "\n".join(lines)


# =============================================================================
# JSON export
# =============================================================================


def export_bench_results(
    results: list[BenchResult],
    graph_path: str,
    variables: dict,
    output_path: str,
) -> None:
    """Export benchmark results to a JSON file.

    Args:
        results: List of BenchResult objects.
        graph_path: Path to the graph YAML file.
        variables: Variables used for the run.
        output_path: Path to write JSON output.
    """
    data = {
        "graph": graph_path,
        "variables": variables,
        "timestamp": datetime.now(UTC).isoformat(),
        "results": [r.model_dump() for r in results],
    }
    Path(output_path).write_text(json.dumps(data, indent=2, default=str))


# =============================================================================
# Benchmark runner
# =============================================================================


def run_benchmark(
    app: object,
    initial_state: dict,
    model_specs: list[tuple[str, str]],
    runs: int,
    config: dict,
) -> list[BenchResult]:
    """Run a compiled graph against multiple provider/model combinations.

    Each model is run ``runs`` times. Errors are captured per-model
    without aborting other models.

    Args:
        app: Compiled LangGraph application.
        initial_state: Initial state dict.
        model_specs: List of (provider, model) tuples.
        runs: Number of runs per model.
        config: Base LangGraph run configuration.

    Returns:
        List of BenchResult objects.
    """
    from yamlgraph.utils.timing_tracker import create_timing_tracker
    from yamlgraph.utils.token_tracker import create_token_tracker

    results: list[BenchResult] = []

    for provider, model in model_specs:
        durations: list[float] = []
        total_tokens_in = 0
        total_tokens_out = 0
        last_output: dict = {}
        error_msg: str | None = None
        status = "success"

        for _run_idx in range(runs):
            # Fresh callbacks per run
            timer = create_timing_tracker()
            token_tracker = create_token_tracker()

            run_config = dict(config)
            run_config["callbacks"] = list(config.get("callbacks", []))
            run_config["callbacks"].extend([timer, token_tracker])

            # Override provider/model via configurable
            run_config.setdefault("configurable", {})
            run_config["configurable"]["provider_override"] = provider
            run_config["configurable"]["model_override"] = model

            try:
                start = time.monotonic()
                result = app.invoke(dict(initial_state), config=run_config)
                elapsed = time.monotonic() - start

                durations.append(elapsed)
                ts = token_tracker.summary()
                total_tokens_in += ts["total_input_tokens"]
                total_tokens_out += ts["total_output_tokens"]
                last_output = result if isinstance(result, dict) else {}
            except Exception as e:
                status = "error"
                error_msg = str(e)
                break

        if status == "success" and durations:
            avg_duration = sum(durations) / len(durations)
        else:
            avg_duration = 0.0

        results.append(
            BenchResult(
                provider=provider,
                model=model,
                duration_s=round(avg_duration, 2),
                tokens_in=total_tokens_in,
                tokens_out=total_tokens_out,
                status=status,
                output=last_output,
                error=error_msg,
            )
        )

    return results


# =============================================================================
# CLI command
# =============================================================================


def cmd_graph_bench(args: Namespace) -> None:
    """Run graph benchmark across multiple provider/model combinations.

    Usage:
        yamlgraph graph bench graph.yaml --models anthropic/claude-sonnet-4-20250514 openai/gpt-4o
    """
    from yamlgraph.cli.helpers import load_var_file, parse_vars
    from yamlgraph.graph_loader import compile_graph, load_graph_config

    graph_path = Path(args.graph_path)

    if not graph_path.exists():
        print(f"❌ Graph file not found: {graph_path}")
        sys.exit(1)

    # Parse model specs
    try:
        model_specs = [parse_model_spec(spec) for spec in args.models]
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)

    # Parse variables
    try:
        file_vars = load_var_file(getattr(args, "var_file", None))
        cli_vars = parse_vars(args.var)
        initial_state = {**file_vars, **cli_vars}
    except (ValueError, FileNotFoundError) as e:
        print(f"❌ {e}")
        sys.exit(1)

    print(f"\n🏋 Benchmarking graph: {graph_path.name}")
    print(f"   Models: {', '.join(f'{p}/{m}' for p, m in model_specs)}")
    print(f"   Runs per model: {args.runs}")
    if initial_state:
        print(f"   Variables: {initial_state}")
    print()

    try:
        graph_config = load_graph_config(str(graph_path))

        # Merge data_files into initial state
        if graph_config.data:
            initial_state = {**graph_config.data, **initial_state}

        graph = compile_graph(graph_config)
        app = graph.compile()

        config: dict = {"recursion_limit": graph_config.recursion_limit or 50}

        results = run_benchmark(
            app=app,
            initial_state=initial_state,
            model_specs=model_specs,
            runs=args.runs,
            config=config,
        )

        # Display table
        show_full = getattr(args, "full", False)
        table = format_bench_table(results, full=show_full)
        print(table)

        # Export if requested
        export_path = getattr(args, "bench_export", None)
        if export_path:
            export_bench_results(
                results=results,
                graph_path=str(graph_path),
                variables=initial_state,
                output_path=export_path,
            )
            print(f"\n📁 Results exported to: {export_path}")

        print()

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
