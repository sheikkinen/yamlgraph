# The tests ran the script and never noticed it could not be run

**Date:** 2026-09-05 · **FR:** FR-995 (dogfood run on PR #593, fix PR #594) · **Trap:** `gate_checks_shape_not_substance`, inverted

## What happened

The first real run of `scripts/outsider.sh` after merge died with `permission denied`. Thirty-six tests had passed in the lane and in CI. Every one of them invoked the wrapper as `bash scripts/outsider.sh …` — the interpreter was named, so the file's own mode never mattered to the test. The committed mode was `100644`. The `git update-index --chmod=+x` I ran in the lane was real, but a later `git add` of the same file re-staged it from disk, where it was still `644` because `chmod` is denied by the pre-command guard and I had never had a reason to notice. Squash-merge faithfully preserved the wrong bit.

## The mechanism

The test harness and the user disagree about *what the artifact is*. To the tests, the artifact is the text of the script. To the user, it is a file they type as a command. A test that supplies the interpreter tests the text and silently exempts the mode. This is the inverse of the usual shape-not-substance trap: here the gate checked substance (behaviour) and skipped the shape (executability), and the shape was the thing that failed first in production.

There is a second, smaller mechanism: the FR-889 lock strips disk permissions on main to `r--`, so `os.access(X_OK)` would be wrong there too. The mode that matters is the one in the git index, not on any disk. The witness therefore reads `git ls-files -s scripts/outsider.sh` and asserts `100755` — the contract is the committed object, not the working tree.

## Heuristic

For any script a human is told to run directly, one test must exercise it *the way the human is told to* — or, where the environment makes that impossible, assert the committed mode from the index. "Runs under `bash`" is a witness for the text, not for the command.

Corollary for lanes in this repo: after `git update-index --chmod=+x`, never `git add` that path again in the same lane; commit the mode change without touching the working-tree copy, and verify with `git ls-files -s` before pushing.

**Seed:** the demo-proof gate checks that `demo-output.log` exists and carries the success stamp — does any gate check that the *command in the README* that produced it is the command a reader would copy, mode and shebang included? A "copy the README, run it, diff the log" gate would have caught this in CI before the first human did.
