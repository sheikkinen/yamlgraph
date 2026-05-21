# Reflection: FR-441 Watcher2 Sanity Check

**Date:** 2026-05-21
**FR:** FR-441 — Pre-commit files patterns for scoped hook execution
**Reviewer:** watcher2 (post-validate sanity reviewer)

## Trap

`infrastructure_self_exempt` — enforcement tooling (pre-commit hooks) marked `always_run: true` was exempted from the "run only what's relevant" discipline applied everywhere else in the codebase.

## What Happened

All 17 targeted local hooks previously ran on every commit regardless of staged content. A docs-only commit triggered vulture, jscpd, radon, import-linter, and pytest — none of which can be affected by markdown-only changes. Issue #429 surfaced this as a real contributor pain point.

The implementation is configuration-only (`.pre-commit-config.yaml`): `always_run: true` removed from 17 hooks, each replaced with a precise `files:` regex derived from the hook's actual inspection scope. Four cross-cutting hooks (`diary-rotate`, `final-summary`, `demo-proof-check`, `gitignore-boundary-guard`) are explicitly preserved in their current state — either retaining `always_run: true` or having neither `files:` nor `always_run:`.

## Root Cause

The pattern of using `always_run: true` as a safe default was appropriate at initial hook introduction but was never revisited as the hook set grew. Prior art (`dependency-rationale`) already proved `files:`-scoped local hooks work correctly — the pattern was available but not propagated.

## What Worked

- **TDD discipline held**: 5 acceptance tests cover all AC points with behavioral assertions (pattern equality, key absence/presence), not implementation trivia.
- **Scope was minimal and config-only**: No script logic changed. No enforcement was removed — only invocation scoping changed.
- **Judge caught factual errors before implementation**: The FR went through AMEND before APPROVE, correcting a wrong claim about `demo-proof-check`/`gitignore-boundary-guard` having `always_run: true`. This kept AC03 deterministic.
- **5/5 tests PASS** after the single commit. Diff proportionality is tight: 34 lines changed in config, 102-line test file, 6-line changelog fragment, 118-line FR.

## Pipeline Log Note

No FR-441-specific pipeline log was found. The latest logs relate to prior FR work. This review is based on direct diff and test execution evidence.

Seed: Should the pre-commit `files:` patterns be validated for correctness (i.e., do they actually match what the hook inspects) via a second-order test that cross-references hook entry scripts against the declared `files:` regex — catching cases where the pattern scope drifts from what the script actually scans?
