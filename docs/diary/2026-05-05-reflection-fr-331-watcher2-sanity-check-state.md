# Reflection: FR-331 Watcher2 Sanity Check

**Date:** 2026-05-05
**FR:** FR-331 — Static Module Map for Tier-2 Codebase Context
**Role:** watcher2 post-validate independent reviewer

## What Happened

FR-331 adds a deterministic AST-based module map generator (`scripts/generate_module_map.py`)
that writes `reference/module-map.md` and wires it into `CLAUDE.md`. All 7 acceptance criteria
are implemented and all 6 acceptance tests pass (0.34s, no slow tests needed).

Pipeline evidence: `validate_fix → sanity_check` transition at 07:52:02 with exit=0 and
3706 unit tests green. The diary artifact was initially missing from the enforce commit — caught
and fixed within the validate_fix phase before reaching this check.

## Trap

**Trap: Treating a generated artifact as documentation.**
A generated file (`reference/module-map.md`) committed to the repo can lull reviewers into
thinking it is a static document to be read and approved, rather than a contract whose source
of truth is the generator. The correct review target is the generator contract (inputs →
deterministic output shape), not the artifact's content at any given commit.

## Root Cause

The enforce phase validated behavior correctly: AC-02 runs the generator and verifies its
output shape; AC-04 checks that the `test_map` section contains the word "deterministic" (the
documented mapping rule). The artifact committed to HEAD is simply the generated read-replica.

## What Worked

- **Scope containment:** All out-of-scope items (LLM classifier, pre-commit auto-regen gate,
  cross-language indexing) are cleanly excluded. Zero runtime/graph code changed.
- **Stdlib-only constraint:** Honored in both implementation and test (AC-06 verifies `ast`
  usage; no new install-time dependencies).
- **TDD discipline:** Tests check behavior (script execution, section presence, determinism
  documentation) rather than implementation trivia.
- **Pipeline log clarity:** `validate_fix → sanity_check` state transition is logged with
  precise timestamps and exit codes, giving reviewers full reproducibility context.

## Minor Observation

AC-06 proves `ast` is used but does not assert the _absence_ of disallowed parsers. For a
stdlib-only constraint this is sufficient (the constraint is economically enforced by the
`pip-audit` security check and the lack of any new imports), but a future tightening could
assert `tree_sitter` and `lark` are absent from the script's import list.

## Seed

If `reference/module-map.md` is regenerated on every enforce run, stale entries will drift
silently in proportion to the PR diff size. **Could the module-map generator be run in
`--diff` mode — emitting only the slice of the map covering files changed in the current
branch — so reviewers receive focused structural context rather than the full 1500-line tree?**
That would be the smallest step toward PR-scoped Tier-2 context without requiring an LLM
classifier.
