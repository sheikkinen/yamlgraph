# Reflection: FR-256 Pipeline Timing Metrics

**Date:** 2026-04-20
**FR:** FR-256
**Branch:** feat/fr-256-pipeline-timing-metrics

## What Was Done

Added lightweight timing and outcome instrumentation to the three core pipeline scripts (`enforce_worktree.sh`, `bugfix_worktree.sh`, `watch.sh`). Each pipeline run now appends a JSON record to `.chaplain/metrics/YYYY-MM.jsonl` with phase durations, exit codes, and FR references. A read-only aggregation script (`scripts/pipeline_metrics.py`) produces daily summaries: mean/p95 duration, success rate, and per-FR breakdowns.

## Cognitive Trap: Operational Truth Without Instruments

The Chaplain pipeline had been running for months with no visibility into duration or success rates — the 9th Commandment ("establish measurable service objectives; instrument and trace execution") applied but was not enforced at the meta-tooling layer. The pipeline that enforces instrumentation on user graphs was itself uninstrumented. This is the **infrastructure_self_exempt** trap: meta-tooling exempted from the gates it enforces.

The fix is mechanical (shell `date +%s%N` bookends + `jq` JSON append), but the insight is architectural: the enforcement pipeline is a production system and should be treated as one.

## Heuristic

**Instrument the instrumenter**: Any tool that enforces observability on downstream systems must itself be observable. Apply the same instrumentation standards to CI, pre-commit hooks, and enforcement pipelines as to user-facing production code. If you can't answer "what's the p95 enforcement duration?", the pipeline is a black box.

## Seed

The metrics JSONL files are local — visible only to the machine running the daemon. Could the aggregation script push a daily summary to a GitHub Issue (or PR comment) automatically, making pipeline health visible to all contributors without requiring local access? Combined with FR-243's remote inbox, this would complete a full observability loop: propose via Issues, observe pipeline health via Issues.
