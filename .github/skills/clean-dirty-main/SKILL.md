---
name: clean-dirty-main
description: "Triage and clean a dirty main checkout by content provenance. Use when: the operator says check dirty main, clean dirty main, main is dirty, or asks whether dirty files on main are a regression; before discarding any modified or untracked file on the shared main checkout."
argument-hint: "none — operates on the main checkout"
---

# Clean Dirty Main

`git status` cannot tell debris from work. Both look like ` M` and `??`.
Classify by **where the bytes come from**, never by status output alone.

## Step 1 — triage first, always

```bash
python scripts/dirty_main_triage.py --repo /path/to/main/checkout
```

Read-only. Prints repo root, `HEAD`, `origin/main`, then per path an evidence
class and disposition, then:

```
safe=<n> preserve=<n> unsupported=<n> errors=<n>
```

**Its output is the input to every later step. No discard without it.**

| Class | Meaning | Disposition |
|-------|---------|-------------|
| `TARGET_IDENTICAL` | Working bytes equal the blob at the same path in `origin/main` | **The only safe class** |
| `KNOWN_BLOB` | Bytes occur in another reachable commit | Preserve; the source revision is reported |
| `UNSEEN_BLOB` | Bytes occur in no examined reachable ref | Preserve — this may be the only copy |
| `UNSUPPORTED` | Staged entry, deletion, rename, conflict, type change, symlink, submodule, non-regular file | Preserve |
| `ERROR` | A git, filesystem, or decode probe failed | Preserve |

## Step 2 — stop unless everything is safe

**Exit code non-zero, or any non-zero `preserve` / `unsupported` / `errors`
count → stop here.** Do not unlock. Do not mutate anything, *including the
paths marked safe*. Report the path, its class and its content hash, and hand
the decision to the operator.

The classifier is advisory: it cannot prevent a later git command from
discarding a path. Its force comes from failing closed, which only works if
you honour the exit code.

Never claim to move preserved content somewhere safe. `scripts/worktree.sh new`
creates a lane; it does not transport dirty files. There is no lossless
one-command rescue — say so and let the operator choose.

## Step 3 — all-safe cleanup, explicit paths only

Only when `safe=n` and every other count is `0`:

```bash
scripts/worktree.sh unlock-main
git checkout -- <path> [<path>...]        # tracked residue, named explicitly
rm -- <path>                              # untracked residue, named explicitly
scripts/worktree.sh sync                  # unlock -> pull --ff-only -> relock
```

Never a repository-wide discard: no whole-tree `checkout`, no whole-tree
`restore`, no recursive force-clean. Name every path the classifier cleared,
and nothing else.

`sync` relocks on both success and failure. If you unlock outside `sync`,
restore the FR-889 lock with `scripts/worktree.sh lock-main` on **every** exit
path, including error paths.

**Re-run the triage immediately before cleanup, and after any tree or ref
change.** A changed snapshot aborts the procedure — reclassify from scratch.

## The trap: `partial_pull_against_lock`

A `git pull` against the locked main checkout writes the unlocked paths (root
docs, `examples/`, `changelog/`, `reference/`), then aborts `Permission denied`
on the locked roots. HEAD never moves. The result is a tree that is
part-`origin/main`, part-`HEAD`, with git reporting already-merged content as
local modifications.

Two counter-diagnostics, both learned the expensive way:

- **Dirty + byte-identical to `origin/main` is an interrupted sync, not a
  regression.** Content identity is the diagnostic; status output is not.
- **It is not a parallel writer.** On 2026-09-03 and again on 2026-09-10 the
  reappearing dirt was blamed on a live sibling session; both times the writer
  was the investigation's own failed pull. Check
  `python3 scripts/vscode/now.py` before believing the parallel-session story.

Known causes, none of which the classifier can prove — it reports evidence,
not history:

| | Cause | Evidence left |
|---|---|---|
| A | Partial pull against the FR-889 lock | `TARGET_IDENTICAL` |
| B | A session wrote directly into main instead of a worktree | `UNSEEN_BLOB` |
| C | An editor flushed a stale buffer from a sibling session | `KNOWN_BLOB` |
| D | Worktree teardown residue (CAP-102 self-heal) | `TARGET_IDENTICAL` |

A and D are indistinguishable by evidence. Treat the letters as explanations
for a human, never as an output the tool can justify.

## Related

- `scripts/worktree.sh` — `lock-main`, `unlock-main`, `sync` (FR-889, FR-698)
- [FR-1047](../../../feature-requests/FR-1047-clean-dirty-main-skill.md) and its judgement
- [docs/diary/diary-2026-09-03-the-lock-writes-half-a-pull.md](../../../docs/diary/diary-2026-09-03-the-lock-writes-half-a-pull.md)
