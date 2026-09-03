# The Lock Writes Half a Pull — Damage Report

**Date:** 2026-09-03
**Trigger:** operator: "check dirty main - regression ?"

## What happened

Main showed 6 modified + 12 untracked files — all FR-959/FR-962
artifacts (corpus_census adapters, person_profile_census demo,
changelog fragments, reference docs). HEAD sat at `b09d1a7f` (#559),
4 commits behind origin/main (#562–#565 merged remotely).

Verdict: **no regression, no lost work**. Every dirty file was
byte-identical to origin/main. The dirt was the debris of a
`git pull` that half-executed against the FR-889 OS lock.

## Causal chain

1. `git pull --ff-only` starts the checkout phase and writes files
   in path order. Unlocked paths (root docs, `examples/`,
   `changelog/`, `reference/`) get their new content written.
2. The merge then hits FR-889-locked paths (`capabilities/`,
   `docs/`, `feature-requests/`, `tests/`, `yamlgraph/`) —
   `Permission denied`, merge aborts, **HEAD never moves**.
3. Result: a working tree that is part-origin/main, part-HEAD, with
   git reporting the already-merged content as local modifications.
4. It happened twice: an earlier session's pull created the original
   dirt; my own first recovery pull (06:51:28 bulk mtime) re-created
   it plus new files, which I initially misread as an active
   parallel writer. Operator corrected: no other sessions. The
   "writer" was my own failed pull.

## Recovery (verified)

`scripts/worktree.sh sync` alone could not recover — the prior
partial pull's residue made the next pull refuse to overwrite.
Working sequence:

1. Verify EVERY dirty file byte-matches origin/main
   (`git show origin/main:$f | diff -q - $f`). This is the
   safety proof that discarding loses nothing.
2. `scripts/worktree.sh unlock-main`
3. `git checkout --` the tracked dirt; `git clean -f` /
   `rm -r` the untracked duplicates.
4. `git pull --ff-only origin main`
5. `scripts/worktree.sh lock-main`

Final state: main clean at `de3023fa`, even with origin, lock
restored.

## Damage assessment

- Lost work: **none** (byte-match proof before every discard).
- Wrong turn: one — attributed the reappearing dirt to a parallel
  session (`now.py` showed a 3-min-old opus session that was in
  fact this investigation's own lineage). One operator correction
  ("no other active sessions") collapsed the hypothesis.
- Guard interaction: `.github/hooks/cmd status` was denied as a
  tool call yet still reported "Lockdown: no" — the lockdown
  channel is a different mechanism from the FR-889 chmod lock;
  `ls -lO` showing `r--r--r--` is the lock's real signature.

## Trap

`partial_pull_against_lock`: git's checkout phase is not atomic
under a path-scoped write barrier. A pull that dies on locked paths
leaves already-merged content as "local changes", wearing the
costume of a regression. The diagnostic that cuts through it is
content identity, not status output: dirty + byte-identical to
origin/main = interrupted sync, not divergence.

Scripture already holds the general form —
`changelog_first_diagnostic` (enumerate what moved before assuming
breakage) and hook-lessons line "diff main's dirt against origin/main
— if identical to the merged PR, restore + sync" (CAP-102 note,
2026-08-30). This is the second recurrence of that cure; recorded in
`/memories/repo/hook-lessons.md` as its own entry with the recovery
recipe.

## Insight

The FR-889 lock did its job — it stopped a write to governed paths —
but its failure mode is a half-written tree, which reads as
corruption to the next session. A barrier that aborts mid-operation
converts "blocked" into "suspicious". The cheap cure is diagnostic
(byte-match check); the structural cure would be making `sync` the
only sanctioned pull route and having it pre-clean verified-identical
residue itself.

**Seed:** should `scripts/worktree.sh sync` learn the recovery it
forced me to do by hand — detect pull-abort residue, verify each
blocking file byte-matches origin/main, auto-discard and retry —
so a half-pull heals in one command instead of five?
