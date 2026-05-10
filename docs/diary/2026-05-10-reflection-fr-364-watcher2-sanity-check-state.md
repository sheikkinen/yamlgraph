# Diary: FR-364 Watcher2 Sanity-Check Reflection

**Date:** 2026-05-10
**FR:** FR-364 — Copilot Instrumentation Gap Closure
**Reviewer:** watcher2 post-validate sanity check

## Trap

`plausible_wrong_answer` — terminal ANSI escape codes in a `git diff` display can make a correct variable reference (`$phase_dir/share.md`) appear malformed (with a spurious space). Treating diff output as ground truth without verifying the actual source file would produce a false WARN.

## What Happened

FR-364 closed six FR-362 follow-up gaps in one pass:

1. Runner (`copilot_instrument.sh`) now passes `--output-format json`, `--log-dir <phase>/logs`, `--log-level debug` and exports `COPILOT_OTEL_EXPORTER_TYPE=file` and `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true`.
2. Before/after git snapshots (`git-status-before.txt`, `git-diff-before.patch`, `git-status-after.txt`, `git-diff-after.patch`) are captured per phase.
3. Event schema expanded with `source`, `success`, `details`.
4. Semantic event extraction (`phase_marker`, `test_run`, `lint_run`, `file_create`, `file_edit`, `failure`, `retry`) extracted via a new library module (`extract_copilot_events_lib.py`).
5. Deterministic conformance-table output via `--conformance-table`.
6. Documentation (`docs/copilot-instrumentation-poc.md`) now explicitly separates Raw Telemetry Artifacts from Normalized Semantic Events.

All 8 acceptance tests passed. CAP-145 registered all 7 REQ-YG-340..346 requirements; `req_coverage.py` reports `7/7 reqs, 8 tests`.

## Root Cause (of original gaps)

FR-362 was explicitly scoped as a POC. The extractor deliberately emitted coarse events (`otel_span`, `git_diff`) to prove the concept without over-engineering. FR-364 formalised the follow-up contract that was already described informally in `docs/copilot-instrumentation-poc.md`. The root cause of the gap was correct-but-intentional scope limitation, not oversight.

## What Worked

- **Scope boundary enforcement:** changes stayed within the five files listed in the FR constraints. No `yamlgraph/` changes. No new runtime dependencies.
- **Synthetic fixture strategy:** all eight tests run deterministically without live Copilot. The fixture constructs known OTel span JSON and exercises every semantic event path.
- **Library extraction pattern:** moving logic from the CLI wrapper into `extract_copilot_events_lib.py` makes the extractor independently testable without subprocess overhead for most assertions.
- **Conformance-table determinism test:** running the formatter twice on the same fixture and asserting `stdout == stdout` is a minimal but correct test for the determinism contract.

## Seed

If semantic event extraction logic grows (more tool names, more pattern matchers), at what complexity threshold should `extract_copilot_events_lib.py` be promoted from a script-adjacent library to a first-class `yamlgraph/` module — and what would that promotion require in terms of import-linter rules and capability registry updates?
