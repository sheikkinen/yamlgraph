# Diary — A commit's blast radius is the index, not your edits

**2026-06-25 · FR-594 enforcement, post-implementation**

## What happened

FR-594 was done: graph wired, eleven tests green, acceptance run recorded, spike
retired, diary and changelog fragment written. The only step left was the commit.
I ran `git status --short` before staging — not out of suspicion, just habit — and
a line I did not expect was sitting in the working tree:

```
 M feature-requests/FR-593-story-level-vocabulary-pre-analysis-stage.md
```

I had not touched FR-593 this session. The diff was worse than a typo: it reverted
FR-593's status from `Kept (2026-06-25)` back to a stale `Enforcing — Authority
GRANTED` and **deleted the entire 47-line "Corpus Gate Result" section** — the
recorded two-run empirical findings (recall 0.46/0.49 straddling the 0.47 gate,
the KILL/KILL evaluator verdict) that were the whole reason FR-594 existed. A
destructive reversion of recorded work, authored by no step I had taken, riding
quietly in the same tree I was about to commit.

Had I run `git add -A` — the reflex move when "everything I did is good" — that
deletion would have been squashed into a `feat(plot_modeller)` commit with a
message that says nothing about FR-593. The findings would have vanished under a
commit about a different feature, discoverable only by someone later asking "where
did the FR-593 gate result go?" and bisecting to a commit that never mentions it.

I left it unstaged, surfaced it to the user, and staged the ten FR-594 files by
explicit path. The user chose to discard the stray reversion (`git checkout --`),
restoring FR-593's findings. The commit went in clean.

## The cognitive trap

**`commit_scope_equals_my_edits`.** I think of a commit as "the work I did." Git
thinks of a commit as "whatever is in the index." Those two sets are equal only if
nothing else moved the working tree — and something always can: a formatter, a
crashed tool, an editor autosave, a half-finished edit from a prior session, a
stray reversion from who-knows-where. The gap between *what I intended to commit*
and *what is stageable* is exactly where unrelated, sometimes destructive, changes
slip in. `git add -A` closes my eyes and trusts that gap is empty.

This is the same shape as the Scripture's `workspace_is_not_boundary`: the editor
shows me one coherent story (I built FR-594), but the filesystem holds state I did
not author and do not own. The cure there is `find . -name .git` before destructive
ops; the cure here is `git diff --cached` before *every* commit, and explicit-path
staging instead of `-A` whenever the tree holds more than one concern.

## What made it catch instead of slip

Nothing clever — just reading `git status` and then `git diff` on the one
surprising line before staging. The cheapest audit in version control is the one
you run on your own index a second before you seal it. The reversion was a
boundary violation (FR-593's recorded findings are not mine to delete inside an
FR-594 commit), and boundary violations are caught by *looking at the boundary*,
which for a commit is the staged diff.

## Heuristic

Before sealing a commit, diff the index, not your memory. `git add -A` is a bet
that the working tree contains only your work; on a real repo with formatters,
background tools, and multi-session branches, that bet is wrong often enough to
cost recorded findings. Stage by explicit path when more than one concern is in
flight, and read `git diff --cached` as the last gate — it is the only view that
shows what the commit will actually *be*, as opposed to what you *think* you did.

## Seed

The stray FR-593 reversion had no author I could name — it was just *there*. Could
a pre-commit hook flag when the staged set spans files unrelated to the commit's
declared FR (e.g. a `feat(...): FR-594` commit staging edits to a *different*
`FR-593-*.md`), the way the changelog-req gate cross-validates REQ IDs? A mechanical
"this commit touches an FR it doesn't claim" warning would turn the discipline I
applied by hand into a gate — catching the next reversion that rides in when no one
happens to read the diff.
