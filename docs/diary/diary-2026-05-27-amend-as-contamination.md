# Diary: Amend as Contamination — Mixed Commit Trap

**Date:** 2026-05-27
**FRs:** FR-461
**Context:** Persona & scenario pipeline demo, commit phase

## Summary

After multiple pre-commit failures (ruff E741, ruff-format, end-of-file,
missing README entry), I used `git commit --amend --no-edit` to add the
final fix. The amend silently merged FR-461 files into an existing FR-460
commit, producing a mixed-concern commit with the wrong message.

## The Trap: `--amend --no-edit` on a Foreign Commit

The branch `feat/FR-461-persona-scenario-pipeline` was created from `main`,
which already had an FR-460 commit at HEAD. None of my initial `git commit`
attempts succeeded (hooks rejected them). When I finally ran
`git commit --amend --no-edit`, it amended the FR-460 commit — not "my"
commit, because mine never landed.

The result: 17 files changed under the message
`feat(ci): FR-460 cap-architecture-sync pre-commit hook` — a commit that
contained FR-461's persona pipeline, FR-460's architecture sync, and the
wrong commit message.

## The Cure: `git reset --soft` and Re-commit

Fix was clean: `git reset --soft main` to unstage everything, then
`git checkout` the FR-460 files back to main's versions, then
`git commit -F tmp/msg.txt` with only FR-461 files staged. Result:
a single-concern commit `cf327a94` with the correct message.

## Heuristic

**Never `--amend` without verifying HEAD is yours.** Before any amend,
run `git log --oneline -1` and confirm the message matches the current
work. If it doesn't, you're about to contaminate someone else's commit.

More broadly: when multiple commit attempts fail in sequence, the mental
model drifts — you start assuming "my commit is at HEAD" when it never
landed. Each hook failure resets you to the pre-commit state, but the
cognitive state doesn't reset with it.

## Traps Encountered

- **continuation_bias**: After multiple retries, assumed progress had been
  made (commit existed) when it hadn't
- **mixed_commits_erode_auditability**: The amend violated one-concern-per-
  commit principle, mixing FR-460 and FR-461

## Seed

Could a pre-amend hook verify that HEAD's commit message matches the
current branch's FR pattern (e.g., branch `feat/FR-461-*` but HEAD says
`FR-460`)? A simple mismatch warning would catch this class of error
before it happens.
