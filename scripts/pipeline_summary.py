"""Pipeline Summary — Daily aggregation of pipeline timing metrics (FR-256).

Reads JSON metric files from tmp/pipeline-metrics/ and prints a daily summary.
Uses Python stdlib only (json, pathlib, datetime). No external dependencies.

Usage:
    python scripts/pipeline_summary.py [--date YYYY-MM-DD] [--dir PATH]
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from pydantic import BaseModel, Field, computed_field

logger = logging.getLogger(__name__)

DEFAULT_METRICS_DIR = Path("tmp/pipeline-metrics")


class PipelineSummaryResult(BaseModel):
    """Aggregated pipeline summary (Commandment 5: Pydantic for all outputs)."""

    date: str = Field(description="Date filter applied (or 'all')")
    total_runs: int = Field(default=0, description="Total pipeline runs")
    success_count: int = Field(default=0, description="Successful runs")
    failure_count: int = Field(default=0, description="Failed runs")
    total_seconds: int = Field(default=0, description="Total wall time in seconds")
    avg_seconds: int = Field(default=0, description="Average duration per run")
    longest_fr: str | None = Field(default=None, description="FR with longest duration")
    longest_seconds: int = Field(default=0, description="Longest run duration")
    shortest_fr: str | None = Field(
        default=None, description="FR with shortest duration"
    )
    shortest_seconds: int = Field(default=0, description="Shortest run duration")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def success_rate(self) -> str:
        """Human-readable success rate percentage."""
        if self.total_runs == 0:
            return "N/A"
        pct = (self.success_count * 100) // self.total_runs
        return f"{pct}%"


def _format_duration(seconds: int) -> str:
    """Format seconds as human-readable duration."""
    if seconds < 60:
        return f"{seconds}s"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def aggregate_metrics(
    metrics_dir: Path,
    date_filter: str | None = None,
) -> PipelineSummaryResult:
    """Aggregate pipeline metrics from JSON files.

    Args:
        metrics_dir: Directory containing JSON metric files.
        date_filter: Optional YYYY-MM-DD to filter by started_at date.

    Returns:
        PipelineSummaryResult with aggregated data.
    """
    runs: list[dict] = []

    if not metrics_dir.exists():
        return PipelineSummaryResult(date=date_filter or "all")

    for f in sorted(metrics_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            logger.warning("Skipping malformed file: %s", f.name)
            continue

        # Only count enforce/bugfix pipeline runs (not chaplain-cycle)
        pipeline = data.get("pipeline", "")
        if pipeline not in ("enforce", "bugfix"):
            continue

        # Date filter
        if date_filter:
            started_at = data.get("started_at", "")
            if not started_at.startswith(date_filter):
                continue

        runs.append(data)

    if not runs:
        return PipelineSummaryResult(date=date_filter or "all")

    total_seconds = sum(r.get("duration_seconds", 0) for r in runs)
    success_runs = [r for r in runs if r.get("outcome") == "success"]
    failure_runs = [r for r in runs if r.get("outcome") != "success"]

    # Find longest and shortest
    sorted_by_duration = sorted(runs, key=lambda r: r.get("duration_seconds", 0))
    shortest = sorted_by_duration[0]
    longest = sorted_by_duration[-1]

    return PipelineSummaryResult(
        date=date_filter or "all",
        total_runs=len(runs),
        success_count=len(success_runs),
        failure_count=len(failure_runs),
        total_seconds=total_seconds,
        avg_seconds=total_seconds // len(runs),
        longest_fr=longest.get("fr", "unknown"),
        longest_seconds=longest.get("duration_seconds", 0),
        shortest_fr=shortest.get("fr", "unknown"),
        shortest_seconds=shortest.get("duration_seconds", 0),
    )


def format_summary(result: PipelineSummaryResult) -> str:
    """Format summary result as human-readable text."""
    lines = [
        f"Pipeline Summary ({result.date}):",
        f"  FRs processed: {result.total_runs}",
        f"  Total wall time: {_format_duration(result.total_seconds)}",
        f"  Avg per FR: {_format_duration(result.avg_seconds)}",
        f"  Success rate: {result.success_rate} ({result.success_count}/{result.total_runs})",
    ]
    if result.longest_fr:
        lines.append(
            f"  Longest: {result.longest_fr} ({_format_duration(result.longest_seconds)})"
        )
    if result.shortest_fr:
        lines.append(
            f"  Shortest: {result.shortest_fr} ({_format_duration(result.shortest_seconds)})"
        )
    return "\n".join(lines)


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Pipeline timing metrics summary")
    parser.add_argument(
        "--date",
        default=None,
        help="Filter by date (YYYY-MM-DD). Default: all dates.",
    )
    parser.add_argument(
        "--dir",
        default=str(DEFAULT_METRICS_DIR),
        help="Metrics directory (default: tmp/pipeline-metrics/)",
    )
    args = parser.parse_args()

    metrics_dir = Path(args.dir)
    if not metrics_dir.exists():
        print(f"No metrics directory found: {metrics_dir}")
        sys.exit(0)

    result = aggregate_metrics(metrics_dir, date_filter=args.date)
    print(format_summary(result))


if __name__ == "__main__":
    main()
