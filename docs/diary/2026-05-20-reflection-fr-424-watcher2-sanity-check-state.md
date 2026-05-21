# Reflection: FR-424 WIP Commit Subject Gate — Watcher2 Sanity Check

**Date:** 2026-05-20
**FR:** FR-424 — Block WIP commit subjects in main merge path
**Reviewer:** watcher2 post-validate sanity

## What Happened

FR-424 closed the structural gap flagged in inquisitor audits 239–243: commits with `wip`
in the subject line had no enforcement gate. The implementation added two coordinated layers:
a local commit-msg pre-commit hook (branch-guarded to `main`) and a CI `wip-gate` job in
`commitlint.yml` that scans `BASE_SHA..HEAD_SHA` subject lines on every PR. Seven acceptance
tests covering all eight ACs were written, pass in 2.57s, and assert behavior (exit codes +
output content) rather than implementation shape.

Pipeline evidence: FSM transitioned cleanly setup → plan → capture_fr → judge → enforce_session
→ micro_changelog → micro_title → sanity_check with no fallback arcs. Judge approved; enforce
completed in ~13 minutes.

## Trap

**`detection_without_enforcement`** — The audits had been flagging WIP commits for five
consecutive runs (239–243) without a blocking mechanism. Each audit correctly identified the
violation; none triggered a gate change. Audit-as-ritual: the detection existed but the
enforcement boundary was absent.

## Root Cause

The pre-commit and CI gate inventories had no WIP-subject entry. Conventional Commits,
changelog, diary, and trailer checks were all wired; WIP subjects were a visible gap that
survived because no audit output was structurally linked to a blocking change.

## What Worked

1. **Layered defense proportional to threat**: local hook (immediate feedback on `main`) + CI
   gate (PR merge boundary) covers both commit paths without overlap or redundancy.
2. **Word-boundary matching (`\bwip\b`)**: prevents false positives on `swipe`, `equip`, etc.
   — tested explicitly in AC-03 / test_ac03.
3. **Existing test patterns reused**: `test_fr410` and `test_fr385` provided ready templates for
   subprocess-executed shell-script tests, reducing invention and keeping consistency.
4. **Scope discipline**: direct-push bypass and duplicate-subject detection were explicitly
   deferred, preventing scope creep that would have added risk without adding value here.

## FR/Code Alignment

All 8 acceptance criteria are satisfied:

| AC | Evidence |
|----|---------|
| AC-01 | `block-wip-main-subject` hook in `.pre-commit-config.yaml`; test_ac01 passes |
| AC-02 | Hook branch-guards on `main` only; test_ac02 passes |
| AC-03 | `grep -Eiq "\bwip\b"` used; test_ac03 passes |
| AC-04 | `wip-gate` job present in `commitlint.yml`; test_ac04 passes |
| AC-05 | Job exits 1 on WIP subject; test_ac05 passes |
| AC-06 | Job exits 0 on clean range; test_ac06 passes |
| AC-07 | `CLAUDE.md` required-checks table updated; test_ac07 passes |
| AC-08 | `CAP-154`, `REQ-YG-411`, `ARCHITECTURE.md` updated; test_ac07 also asserts |

## Seed

**Seed:** When a CI gate is added at the PR merge boundary, the branch protection configuration must be
updated in the same commit to activate it. Could the gate-registration step be automated
— e.g., a script that reads all `jobs:` keys from `commitlint.yml` and diffs them against the
branch protection required-status-check list, failing if any job is unregistered?
