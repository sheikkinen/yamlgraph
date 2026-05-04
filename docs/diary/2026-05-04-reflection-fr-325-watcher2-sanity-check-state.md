# Watcher2 Sanity Check — FR-325 Demo-gate Log Content Validation

**Date:** 2026-05-04
**FR:** FR-325 Demo-gate validates demo-output.log content
**Reviewer:** watcher2 (post-validate sanity check)
**Status:** PASS

## Trap

`detection_without_enforcement` — the demo-gate was a shape check masquerading
as a proof check. A log file containing `[ERROR] Node greet failed` satisfied
the gate because presence was the only criterion. Artifact shape ≠ artifact
truth.

## What Happened

The implementation correctly identifies the enforcement boundary (log content
at ingest, not log existence at merge) and adds a shared semantics helper
(`scripts/demo_log_semantics.sh`) used identically by CI and pre-commit.
Three failure modes are enforced: empty log, fatal execution markers, and
absence of success evidence. All six acceptance tests pass with behavioral
fixture-level isolation (real temp git repos, not mocks).

## Root Cause

The original gate was designed to answer "was the demo run?" rather than "did
the demo succeed?" The presence-only check was a classic incomplete boundary:
it normalised artifact existence but not artifact semantics.

## What Worked

- **Single source of truth** for semantic rules: `demo_log_semantics.sh` is
  sourced by both CI and pre-commit, making drift structurally impossible.
- **Behavioral tests**: each fixture constructs an actual git repository and
  runs the real script; no mocks, no stub logic.
- **Tight scope**: only gate surfaces and directly-coupled tests/docs changed.
  No speculative extensibility introduced.
- **All AC-01..AC-06 covered**: presence check preserved, content rules added,
  CI/local parity enforced, docs updated.

## Proportionality Verdict

10 files, 487 insertions. The test file (201 lines) and the shared semantics
script (36 lines) account for most of the additions. No bloat; no unrelated
changes. Proportional to a 0.5-day bug fix.

## Seed

Could `demo_log_semantics.sh` be extended with a per-demo contract file
(`demo-output.contract.yaml`) that lets individual demos declare their own
success and failure patterns — enabling demos whose output intentionally
contains error-like strings (e.g., error-handling demos) to still pass with
appropriate proof?
