# Watcher2 Sanity Check — FR-402 Prompt Theme Analyzer Demo

**Date:** 2026-05-16
**FR:** FR-402

## Trap

`gate_checks_shape_not_substance` — a sanity reviewer could confirm files exist and
tests are green without verifying that assertions test *behavior* rather than presence.

## What Happened

Post-validate review of FR-402 (`examples/demos/prompt_theme_analyzer/`). The
implementation adds 15 files / 922 insertions, all within the scope prescribed by the
FR. All ten acceptance criteria (AC-01 through AC-10) are covered with unit tests, and
all 12 tests pass. The graph lints clean. Capability and requirement rows are in both
`capabilities/CAP-149-prompt-theme-analyzer-demo.yaml` and `ARCHITECTURE.md`.
`demo-output.log` contains the required execution command and success sentinel.
Changelog fragment carries correct `req: REQ-YG-359` front-matter.

## Root Cause (why a WARN was not needed)

The implementation followed the corrected FR shape faithfully. Boundary normalization
lives in `list_prompts` (truncation, empty/noise filtering, `source_dir` guard).
Deterministic aggregation is an explicit Python node before the second LLM call.
The `group_themes` prompt consumes only `theme_counts`, not raw per-item payloads.
Tests assert on behavioral outcomes (exact count values, specific markdown headers,
exception messages), not on trivial presence checks.

## What Worked

Encoding the FR judge's four amendment issues (RED test file, manual ARCHITECTURE.md
rows, AC-10 coverage, AC-07 integration qualification) as explicit acceptance gates
forced implementation completeness before merge. The `test_ac10_diary_entry_exists`
test asserting `"Seed:"` in the diary entry is a lightweight substance gate that
prevents empty placeholder files from satisfying the diary-gate CI check.

## Seed

Seed: Should the watcher2 stage add a machine-readable confidence score (0–1) per
acceptance criterion to its diary so that FSM routing thresholds can be tuned
automatically over time, rather than relying solely on binary PASS/WARN judgment?
