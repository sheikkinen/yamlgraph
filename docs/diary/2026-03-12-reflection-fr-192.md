# Diary Reflection — FR-192 Draconian Changelog Release Gate

**Date:** 2026-03-12
**FR:** FR-192
**Author:** Copilot

## Context

The v0.4.63 release demonstrated changelog release drift: version was bumped, committed, and tagged while 21 changelog fragments remained orphaned in `changelog/unreleased/`. The existing documentation described the correct process, but documentation is advisory — not enforcement.

## Trap: `audit_as_ritual`

The release checklist existed and described every step. But a checklist without a gate is a ritual, not a process. The presence of documentation created false confidence that the release process was controlled. From the Knowledge Graph: *"3+ audits without fix → ritual, not process."*

The deeper trap is `infrastructure_self_exempt`: the release process enforced changelog discipline for developers (via `changelog-gate` CI job for PRs) but exempted itself — the release commit that *moves* fragments had no enforcement. The gate guarded the entry but not the exit.

## Heuristic: Gate the Transition, Not Just the Entry

When a process has multiple ordered steps where skipping one creates drift, gate the *transitions* between steps — not just the first step. FR-149's `changelog-gate` checked that PRs included fragments (entry gate). FR-192 adds the exit gate: you can't bump version without freezing first. Defense-in-depth: local pre-commit → atomic script → CI validation.

## Seed

**If the release script itself becomes the new unguarded ritual, what prevents drift in the release script's own behavior?** Could a "release integration test" run `release.sh` in a disposable git repo and assert the exact sequence of commits/tags/file movements? Would such a test be worth the maintenance cost, or would it become another infrastructure_self_exempt case?
