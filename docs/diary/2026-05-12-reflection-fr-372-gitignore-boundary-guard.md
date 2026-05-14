# Diary: FR-372 gitignore Boundary Guard

**Date:** 2026-05-12
**FR:** FR-372 — gitignore boundary guard for pre-commit
**Reviewer:** validate remediation pass

## What Happened

FR-372 adds a pre-commit shell script (`scripts/check_gitignore_boundary.sh`) that blocks staged `.gitignore` changes by default, requiring explicit `YAMLGRAPH_ALLOW_GITIGNORE_EDIT=1` and a traceable `YAMLGRAPH_GITIGNORE_REASON` to bypass. The hook is registered in `.pre-commit-config.yaml`, 7 acceptance tests are green, and bypass contract is documented in `reference/break-glass.md`.

Scope is minimal and proportional: 1 shell script, 1 hook registration, 1 test file (7 tests), 1 changelog fragment, 1 doc update.

## Trap

**gate_checks_shape_not_substance** was the primary risk here: it would have been easy to register the hook and write tests that confirm the script *exists* and the hook *is listed*, without testing that the logic inside the script actually blocks the right paths. The implementation avoided this by running the script directly in subprocess tests with synthetic git repos, asserting on exit codes and stderr content — substance, not just presence.

**workspace_is_not_boundary** was the upstream trigger for this entire FR. The incident diary (`docs/diary/2026-05-12-private-repo-dataloss-recovery.md`) documented how a `.gitignore` edit in a multi-repo workspace caused untracked-file loss. The guard normalizes at the boundary where `.gitignore` changes enter a commit — the earliest, cheapest interception point.

## Root Cause

No dedicated gate existed for `.gitignore` changes. The file is structurally indistinguishable from any other file to pre-commit's default hooks. A single targeted script closes the gap without touching runtime or graph logic.

## What Worked

- **Prior-art pattern (`check_demo_proof.sh`) reduced implementation risk**: the structure (read staged names, match regex, fail with message, check bypass env vars) was already established. The new script followed it exactly.
- **Bypass contract is tight**: both `YAMLGRAPH_ALLOW_GITIGNORE_EDIT=1` *and* a non-empty reason containing `FR-` or `gh-` are required. Either alone fails closed. This prevents silent bypasses.
- **TDD structure is clean**: 7 tests cover all 7 ACs; each test creates an isolated temp git repo, so there is no state leakage between cases.

## Seed

Should the bypass reason token (`FR-` or `gh-`) be validated against the live GitHub issue/FR registry at bypass time, so the trace is not just syntactically valid but referentially real? This would turn the bypass from a policy assertion into a verified audit trail entry.
