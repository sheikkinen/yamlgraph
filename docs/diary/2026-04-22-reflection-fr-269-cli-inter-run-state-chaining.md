# Reflection: FR-269 CLI Inter-Run State Chaining

**Date:** 2026-04-22
**FR:** FR-269
**Branch:** feat/fr-269-cli-inter-run-state-chaining

## What Was Done

Added `--import-state` and `--export-state` flags to `yamlgraph graph run`, enabling external orchestrators (shell scripts, CI pipelines) to chain graph invocations across shell boundaries while preserving state — including `CopilotResult.session_id` for copilot session resume.

Implementation: `export_state_to_path()` in `storage/export.py`, `load_imported_state()` and `handle_state_export()` in `cli/helpers.py`, parser arguments in `cli/__init__.py`, and wiring in `cmd_graph_run()`. Merge precedence: `graph_config.data < imported < var-file < var`.

## Cognitive Trap: Infrastructure Self-Exempt

The enforcement infrastructure itself (pre-commit hooks, capability registry, confession tracking, file-size gates) consumed more implementation effort than the actual feature. The feature was ~30 lines of logic; the compliance artifacts (CAP-120, CONF-005 line shift, REQ-YG-267/268 tags, changelog fragment) required ~5 separate iterations to satisfy all gates.

This isn't a complaint — it's the **infrastructure_self_exempt** trap in reverse: the gates work exactly because they're strict. But the cognitive risk is losing sight of the feature while chasing hook compliance. The cure is to treat gate satisfaction as a predictable post-implementation checklist, not a discovery process.

## Heuristic

**Gate compliance is a checklist, not a debugging session**: After implementing any `feat` change, mechanically walk the gate list before the first commit attempt: (1) capability YAML, (2) req tags on tests, (3) changelog fragment with valid `req:` front-matter, (4) ARCHITECTURE.md entries, (5) confession updates for shifted noqa lines, (6) file-size check. Running `pre-commit run --all-files` first (before `git commit`) surfaces all failures in one pass rather than iteratively through failed commit attempts.

## Seed

Could the acceptance test writer (`.chaplain/graphs/copilot/prompts/write-acceptance-tests.yaml`) be extended to also generate a gate-compliance skeleton — the CAP YAML, changelog fragment, and ARCHITECTURE.md entries — as part of the RED commit? This would shift gate compliance left, making it part of the test contract rather than a post-implementation discovery.
