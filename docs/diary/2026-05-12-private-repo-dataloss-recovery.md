# Reflection: Private Repository Data Loss and Recovery

**Date:** 2026-05-12
**FR:** none — incident reflection (history rewrite crossed repository boundaries)
**Reviewer:** human + agent recovery session

## What Happened

Private application repositories were present under the YAMLGraph workspace as
nested projects. During cleanup/recovery work, they were treated as ordinary
workspace contents instead of independent repositories with their own ownership,
history, and risk profile.

The private repositories were then deleted forcefully. This caused real data
loss: tracked files could be recovered from git, and some unstaged tracked edits
could be recovered from a pre-commit patch, but any untracked local-only files
were exposed to permanent loss.

Recovery succeeded for the visible tracked work:

- tracked deletions were restored from git;
- the pre-commit stash patch was found under `~/.cache/pre-commit/`;
- recoverable unstaged tracked diffs were reapplied;
- suspicious deletions were reset before committing;
- remaining changes were split into focused commits and pushed.

The damage was not theoretical. The system survived because git and pre-commit
left enough breadcrumbs, not because the deletion operation was safe.

## Damage

- Private repositories were accidentally included in the YAMLGraph working tree
  context.
- A forceful deletion path crossed repository boundaries.
- Tracked files were recoverable from git.
- Unstaged tracked edits were partly recoverable from pre-commit stash patches.
- Untracked files had no guaranteed recovery path.
- The recovery process consumed time that should have gone into the actual
  runtime/deploy fix.

## Trap

`monorepo_identity_confusion`: a workspace folder is not a repository boundary.
The editor can show several projects as one visible tree, but git safety,
ownership, privacy, and recovery semantics remain per-repository.

`quick_confidence`: cleanup felt like a local filesystem operation. It was
actually a cross-repository destructive action with different blast radii in
each nested repo.

`untracked_blindness`: git restore can rebuild tracked state, but it cannot
resurrect files git never knew existed. Any destructive operation that runs
before enumerating untracked files is already gambling with data loss.

## What Worked

- Running `git status --short` and `git diff --name-status` after recovery made
  the remaining state legible.
- Restoring suspicious deletions before committing prevented accidental
  codification of the recovery damage.
- Splitting commits by concern preserved auditability: supervisor runtime,
  deploy diagnostics, and ruff formatting landed separately.
- Pre-commit stash patches provided a second recovery channel for unstaged
  tracked edits.

## What Failed

- The repository boundary was not named before destructive cleanup.
- No inventory of untracked files was captured before deletion.
- Private application repositories were allowed to sit inside the framework
  workspace without a strong enough warning that they are separate assets.
- The recovery depended on luck: tracked state and pre-commit patches existed;
  untracked state might not have.

## Heuristic

Before any destructive filesystem operation in a workspace that may contain
nested repositories, run a boundary inventory first:

```bash
find . -name .git -type d -prune
git status --short --untracked-files=all
```

For each nested repository, repeat the status check inside that repository. If
any untracked file or unstaged change exists, stop and make an explicit backup
or commit plan before deletion.

Treat private application repositories inside a framework workspace as external
systems mounted into the editor, not as disposable subdirectories.

## Metacognitive Reflection

The agent performed the `git filter-repo` operation correctly — the tool ran,
the history was rewritten, the force push succeeded. Every individual step was
technically valid. The failure was not in execution but in **framing**: the task
"remove all traces from yamlgraph repo" was interpreted as a filesystem cleanup
scoped to a single repository, when the workspace actually contained multiple
independent repositories sharing a visible tree.

The confirmation flow asked about scope (simple rm vs. history rewrite, which
dirs to include) but never asked the critical boundary question: "Are any of
these directories independent git repositories with their own untracked state?"
The `find . -name .git -type d` inventory that the heuristic now prescribes
would have surfaced this in seconds.

This is `quick_confidence` at the architectural level — the operation felt
contained because the tool (`filter-repo`) is well-understood, the flags were
correct, and the output was clean. Confidence in the tool substituted for
confidence in the problem definition. The Scripture's "When I feel certain, let
that be the sign to Judge" applies not just to code, but to destructive
operations: the more certain the plan feels, the more likely a boundary
assumption is hiding.

**Graduated heuristic candidate:** `workspace_is_not_boundary` — editor
visibility does not imply ownership. Before any destructive operation that
touches directories, enumerate `.git` boundaries. Each boundary is a separate
blast radius. This is the filesystem analogue of the `instruction_boundary`
trap: just as agent instructions must be treated as external input, nested
repositories must be treated as external systems.

## Seed

Should YAMLGraph provide a `scripts/workspace_boundary_report.py` guard that
enumerates nested git repositories, untracked files, dirty worktrees, and private
project markers before any Chaplain or agent cleanup workflow is allowed to run?
