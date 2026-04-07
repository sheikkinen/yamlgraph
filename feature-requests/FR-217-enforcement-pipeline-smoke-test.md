# Feature Request: FR-217 Enforcement Pipeline Smoke Test

**Priority:** LOW
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0 days
**Requested:** 2026-04-07

## Summary

A no-op feature request that triggers the full Chaplain enforcement pipeline (inbox → draft → judge → **enforce**) to validate the end-to-end flow including the enforcement stage. Unlike FR-216 (which was Rejected and therefore skipped by enforcement), this FR is intentionally Approved with zero scope so enforcement runs but produces no code changes.

## Value Statement

Infrastructure maintainers confirm the entire Chaplain pipeline — including the enforcement stage — operates correctly, catching routing, worktree, or enforcement regressions before real feature requests enter the queue.

## Problem

FR-216 tested the pipeline up to the Judge stage: it was Rejected, so `watch.sh` skipped enforcement (line 37–38). The enforcement stage (`scripts/enforce_worktree.sh`) has never been smoke-tested with a deliberate no-op payload. If enforcement has a regression (worktree setup, pre-commit hooks, branch creation), it will only surface when a real feature request fails — wasting time and polluting the git history.

A controlled test that enters and exits the enforcement pipeline without producing changes validates the full path.

## Proposed Solution

No code changes required. This FR is the test payload itself.

**⚠️ ENFORCEMENT INSTRUCTION: NO ACTION REQUIRED.**

This FR is a pipeline smoke test. The enforcer should:

1. Pick up this FR as an Approved, non-Bug feature request
2. Enter the enforcement pipeline (`scripts/enforce_worktree.sh`)
3. Observe that no code changes are specified
4. Exit cleanly with no commits, no branch, no PR

**There are zero implementation tasks.** The acceptance criteria are satisfied by the pipeline processing this FR without error.

## Acceptance Criteria

- [x] Inbox file consumed and deleted by `watch.sh`
- [x] Draft FR generated in `.chaplain/drafts/`
- [x] Judge approves (pipeline test with explicit no-op scope)
- [x] Enforcement pipeline triggered (not skipped)
- [x] Enforcement exits cleanly — no commits, no branch, no PR
- [x] No code changes produced

## Alternatives Considered

1. **FR-216 (Rejected pipeline test)** — Only tested inbox → draft → judge. Enforcement was skipped because Rejected FRs are filtered out in `watch.sh`. Does not validate the enforce stage.
2. **FR-099 (smoke-test.sh)** — Validates graph compilation and linting offline. Does not exercise the enforcement pipeline or worktree machinery.
3. **Automated integration test** — A pytest-based test that mocks the enforcement pipeline. More robust but higher effort; out of scope for a quick validation.

## Related

- `FR-216-pipeline-test.md` — Previous pipeline test (Rejected, enforcement skipped)
- `FR-099-chaplain-inbox-smoke-test.md` — Offline graph validation
- `.chaplain/watch.sh` — Daemon that routes FRs to enforcement
- `scripts/enforce_worktree.sh` — Enforcement pipeline under test
