# Feature Request: Deny gh pr merge --admin outside break-glass

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-08-30
**First consumer / first event:** the first agent session after FR-934's
merge queue is live that reflexively types `gh pr merge --squash
--admin` — the guard denies it and points at the queue verb. Witnessed
frequency: at least four distinct sessions used `--admin` as the routine
merge verb on 2026-08-30 alone (PRs #519, #520 among them), including
after the deadlock that justified it was already cured.
**Research:** [docs/plan-research-merge-queue.md](../docs/plan-research-merge-queue.md)
(committed 2026-08-30, PR #520; equivalent committed record per FR-890
R-6 — §"The `--admin` habit is the real enemy" is this FR's problem
record). Sole-route provenance note: shared with FR-934 — the brief
`feature-requests/research-briefs/fr934-merge-integration-toll-brief.md`
covers both FRs' problem (its Witnessed incidents section records the
bypass culture); two sole-route runs on 2026-08-30 failed at the
artifact contract (librarian_structure 400-char cap, exit 65, defect in
FR-932's in-flight territory) and the failure is recorded rather than
routed around.
**Prior art:** the PreToolUse guard
(`.github/hooks/scripts/pre-command-guard.sh`) already denies
`--no-verify`, Co-authored-by trailers, multiline `git commit -m`, and
unpiped pytest — this FR conforms to that existing pattern (Commandment
4) rather than inventing a new enforcement surface.
`reference/break-glass.md` owns the documented exception path and is not
modified. FR-438 polices vendor-default thoughtcrimes at the same
boundary. No prior or REJECTED FR governs the merge verb.

## Summary

Add a PreToolUse guard rule denying `gh pr merge` invocations that carry
`--admin`, unless a break-glass escape variable is set. The denial
message names the compliant verb (`gh pr merge --squash`, which
auto-enqueues under FR-934's queue) and the break-glass procedure.

## Value Statement

The merge queue (FR-934) only serializes what passes through it; this
guard makes the bypass exceptional and audited instead of the default
verb, so the required checks gate reality again.

## Problem

`enforce_admins` is disabled on `main`, so `gh pr merge --admin`
bypasses every required context unconditionally. The habit was
rational while docs-only PRs deadlocked (FR-889 §4d), but the cure is
live — witnessed green on docs-only PR #520 — and the habit outlived
its justification the same day: sessions kept admin-merging PRs whose
checks would have passed. A queue that everyone bypasses serializes
nothing; detection without enforcement is advisory
(`detection_without_enforcement`), and the enforcement belongs at the
boundary where the command enters (`the_one_law`), which for agent
sessions is the PreToolUse guard.

## Proposed Solution

In `.github/hooks/scripts/pre-command-guard.sh`, following the existing
denial-rule pattern:

- Deny commands matching `gh pr merge` with an `--admin` flag.
- Escape hatch: `BREAK_GLASS=1` environment prefix allows the command;
  the guard logs the allowance to `.github/hooks/logs/audit.jsonl`
  (existing audit stream) so every bypass is enumerable afterwards.
- Denial message: one line naming `gh pr merge --squash` as the queue
  verb plus the `reference/break-glass.md` pointer.

Witness test in the existing hook-test pattern
(`tests/unit/test_*guard*.py` family): denied without the variable,
allowed with it, audit line written on allowance.

Non-goals: no change to `enforce_admins` (admin overrides remain the
operator's documented single-dev flow at the GitHub settings level;
this FR governs the agent command boundary, not the human's browser),
no change to `break-glass.md`, no server-side enforcement.

## Acceptance Criteria

- [ ] AC-01: `gh pr merge --squash --admin` (any flag order) is denied
      by the PreToolUse guard with a message naming the queue verb and
      break-glass pointer — witnessed by unit test.
- [ ] AC-02: `BREAK_GLASS=1 gh pr merge --squash --admin` is allowed
      and appends an audit line to `.github/hooks/logs/audit.jsonl` —
      witnessed by unit test.
- [ ] AC-03: plain `gh pr merge --squash` is unaffected — witnessed by
      unit test.
- [ ] AC-04: RED commit (failing witness) precedes GREEN commit
      (guard rule) in the PR's history.
- [ ] AC-05: changelog fragment (`type: feat`) in
      `changelog/unreleased/`.

## Alternatives Considered

| alternative | disposition |
|---|---|
| Enable `enforce_admins` server-side | REJECTED — removes the operator's own documented single-dev override and the break-glass path with it; server setting can't distinguish agent from human |
| Advisory doctrine line ("don't use --admin") | REJECTED — the doctrine already implies it and four sessions used it in one day; `detection_without_enforcement` names this failure |
| Delete gh CLI access for agents | REJECTED — destroys the entire PR flow to police one flag |
| PreToolUse guard denial with audited break-glass (this FR) | PURSUED — conforms to the existing guard pattern, keeps the exception enumerable, costs one rule plus one test |

## Related

- FR-934 (companion — the queue this guard protects; this FR is sequenced after FR-934 lands)
- FR-889 §4d (the deadlock whose cure removed the bypass's justification)
- `.github/hooks/README.md` (guard architecture), `reference/break-glass.md` (exception path)
- docs/plan-research-merge-queue.md §"The `--admin` habit is the real enemy"
