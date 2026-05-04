# Reflection: FR-325 Demo-gate Log Content Validation

**Date:** 2026-05-04
**FR:** FR-325 Demo-gate validates demo-output.log content
**Reviewer:** watcher2 (post-validate)

## Trap

`detection_without_enforcement` — The demo-gate enforced artifact *shape* (file
presence) but not artifact *truth* (successful execution). A log file containing
`Node greet failed` passed the gate because CI never inspected the content.

## What Happened

FR-323 produced a `demo-output.log` that recorded a fatal ERROR but still
satisfied the gate. This FR closes that gap by adding semantic validation:

- CI (`demo-gate` in `.github/workflows/commitlint.yml`) now runs
  `scripts/demo_log_semantics.sh` for each changed log.
- Pre-commit (`scripts/check_demo_proof.sh`) delegates to the same shared
  helper, preserving CI/local parity.
- The shared script enforces three rules:
  1. Log must not be empty.
  2. Log must not contain fatal execution markers (`Node .* failed`, `❌ Error:`, etc.).
  3. Log must contain a success evidence marker.

## Root Cause

The original gate design optimised for "was the demo run?" rather than "did the
demo succeed?". Presence-only checking is a classic `detection_without_enforcement`
trap: a lint check that cannot block is advisory, not enforcement.

## What Worked

- Shared semantics helper (`scripts/demo_log_semantics.sh`) as single source of
  truth — CI and pre-commit both delegate to it, preventing drift.
- Unit tests (`test_fr325_demo_gate_log_content_validation.py`) exercise each
  failure mode independently with fixture-level isolation.
- Scope stayed tight: only gate surfaces and directly coupled tests/docs touched.

## Heuristic

*The gate must validate the claim the artifact makes, not merely that the
artifact exists.*  A demo log is a claim of successful execution; treat its
absence of success evidence as a gate failure, not a formatting quirk.

## Seed

Could the semantics helper evolve into a configurable "log contract" file per
demo directory (`demo-output.contract.yaml`) that specifies which success and
failure patterns to expect, allowing demos with intentional error cases to still
pass with appropriate proof?
