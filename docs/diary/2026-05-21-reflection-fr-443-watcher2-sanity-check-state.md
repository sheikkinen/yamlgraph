# Reflection: FR-443 Document Copilot Hooks in copilot-instructions.md — Watcher2 Sanity Check

**Date:** 2026-05-21
**FR:** FR-443 — Add `### Copilot Hooks (.github/hooks/)` subsection to `.github/copilot-instructions.md`
**Reviewer:** watcher2 post-validate sanity check

## Trap

`gate_checks_shape_not_substance` risk: documentation-only FRs invite superficial compliance — a subsection can exist and contain all required tokens while still being incoherent or misleading. The acceptance tests check presence and token membership; they cannot verify that the operational map is accurate against the live hook scripts.

## What Happened

`.github/copilot-instructions.md` had one generic hook line that named no scripts, no blocked patterns, and no audit path. Agents hitting a denial had nowhere to self-diagnose; the full contract lived only in `.github/hooks/README.md`, which is not surfaced at point-of-failure. FR-443 inserted a 6-line operational map under `### Conventions` covering PreToolUse, PostToolUse, reasoning sentinel, lockdown channel, audit trail, and a link to the full README.

## Root Cause

Documentation was added iteratively to `README.md` as hooks evolved (FR-414, FR-434, FR-442), but the primary instruction file was never updated in parallel. There was no gate requiring `.github/copilot-instructions.md` to reflect new hook capabilities — the gap accumulated silently across three FRs.

## What Worked

- **Minimal, bounded scope:** the entire change is 8 lines in one documentation file; no behavior changes.
- **Redundancy-avoidance by design:** content links to `README.md` rather than duplicating it, preventing drift risk.
- **Acceptance tests check substance:** AC-02 asserts all nine operational tokens are present; AC-03 enforces the conciseness constraint (≤15 non-empty lines). Tests pass against the live file (3/3 GREEN).
- **TDD rite observed:** test file created alongside documentation, not after.

## Evidence

- 3 FR acceptance tests: all 3 pass.
- Diff: 8 net lines in `.github/copilot-instructions.md`, 67 lines of acceptance tests, FR (112 lines), changelog fragment (5 lines). Scope is proportional.
- FR acceptance criteria: all 8 items checked off; implementation matches proposed solution text verbatim.

## Seed

**Seed:** Each new hook FR touches `.github/hooks/README.md` but no gate checks whether `.github/copilot-instructions.md` references the changed scripts — could a lightweight doc-sync lint rule (e.g., verify that every script name mentioned in README.md also appears in the instructions hooks subsection) close this gap without requiring manual review?
