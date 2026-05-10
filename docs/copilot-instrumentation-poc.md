# Copilot Instrumentation POC (FR-362)

This proof-of-concept captures a two-phase Copilot execution (`plan` then resumed `implement`) and converts local artifacts into normalized process-mining events.

## Captured Artifacts

Artifacts are written to:

`outputs/copilot-instrumentation/<run-id>/<phase>/`

Per phase (`plan`, `implement`) the run records:

- `prompt.txt`
- `command.txt`
- `stdout.jsonl`
- `stderr.log`
- `share.md`
- `otel.jsonl`
- `copilot-debug.log`
- `git-status.txt`
- `git-diff.patch`

The run root also contains `run-metadata.json` with run ID, base ref, disposable worktree path, and extracted plan session ID.

## Observed Event Sequence

The extractor (`scripts/extract_copilot_events.py`) emits JSONL events with:

- `case_id`
- `phase`
- `event_type`
- `timestamp`
- `summary`

Initial event classes:

1. `otel_span` from `otel.jsonl` (`resourceSpans -> scopeSpans -> spans`)
2. `git_diff` from `git-diff.patch` snapshots

This event stream is sufficient for first-pass sequence analysis:

1. Identify deterministic boundaries (phase transitions, stable tool invocations).
2. Detect repetition across resumed runs.
3. Quantify output-side changes (`git_diff`) versus execution semantics (`otel_span`).

## Candidate Node Types

The observed shape maps to future YAMLGraph codification candidates:

- `copilot` (session-aware invocation boundary)
- `agent` (phase-level delegated reasoning)
- `python` (artifact parsing and normalization)
- `tool` (shell-level capture and git snapshots)
- `router` (branching by event signatures)
- `map` (phase fan-out aggregation)
- `llm` (semantic clustering of event summaries)

## Next FR

Follow-up scope should define a deterministic YAMLGraph process-mining pipeline that:

1. Computes conformance metrics from extracted events.
2. Flags unstable steps that should stay outside YAMLGraph orchestration.
3. Proposes node-level migration candidates with explicit acceptance thresholds.
