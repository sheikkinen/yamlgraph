# Feature Request: Shared-Repo Write Discipline — Skill Doctrine + Hermetic Adapter + Guard

**Status:** Proposed
**Date:** 2026-08-23
**Author:** agent session (operator-directed reflection)

**Prior art:** `.github/skills/session-introspection/SKILL.md` (read-side situation awareness; names `one_session_one_repo` but prescribes no write rituals — this FR adds its write-side doctrine rather than a rival skill); `.github/skills/judge-fr/` + `.github/skills/review-pr/` (the doctrine + adapter + mechanical-guard pattern this FR instantiates); Scripture `one_session_one_repo` process entry (names the ritual but at summary altitude); FR-784 (fourth interleave shape cure), FR-852 (sixth shape), FR-859/FR-860 (worktree-airlock regen, verified twice); FR-767 (sentinel-armed PreToolUse guard precedent); FR-858 (Proposed — retires the committed fr-board, deleting the most contended generated artifact; this FR is complementary: it governs the *class* of shared-tree writes, not one artifact, and its doctrine must not assume the board survives); diary 2026-08-23-the-worktree-is-the-airlock.md (the reflection that motivated this FR). Disposition: no existing artifact provides repo-visible, enforceable write discipline for parallel sessions — the six-shape taxonomy lives only in per-machine agent memory, invisible to the chaplain, CI, other machines, and non-Copilot agents.

## Ideal Result

Any agent (human-driven session, chaplain, watcher2, a fresh machine with zero
local memory) that writes to this shared repo discovers the parallel-session
write rituals from the repo itself, runs hook-input-divergent generators
through one hermetic route, and is mechanically denied the operations that
caused all six recorded interleave incidents.

## Problem

Six named interleave shapes (foreign staged sweep, stash-pop clobber,
hook-input divergence, branch switch underfoot, mid-cycle sweep + phantom
drift, pathspec-vs-staged board drift) were diagnosed and cured across
FR-784/852/859/860 — but the cures live in `/memories/repo/hook-lessons.md`,
which is **local agent memory**: per-machine, per-tool, uncommitted. The
chaplain, CI, sibling projects, and any agent without that memory file will
re-derive each shape by incident. Repo-scoped operating knowledge stored
outside the repo violates the boundary the Scripture itself names
(`workspace_is_not_boundary` corollary: memory visibility ≠ repo truth).

## Proposed Solution

Instantiate the judge/review pattern for shared-repo writes, homed in the
existing skill (Commandment 4 — conform before extending):

1. **Doctrine** — `.github/skills/session-introspection/doctrine.md`:
   the write-side contract. Contents graduated from local memory:
   - Commit ritual: `git branch --show-current` before every commit;
     pathspec commits only (`git commit --only <paths> -F <unique-msg-file>`);
     unique message files (`/tmp/msg-<topic>.txt`, never shared `./tmp/msg.txt`);
     `git show --stat` audit after; `git fetch` before every push.
   - Stash prohibition: never bare `git stash pop` in a shared tree; push
     with a unique token, pop by exact `stash@{n}` ref after `git stash list`
     verification; never stash-diagnose — simulate in a worktree.
   - The airlock procedure: any generator whose pre-commit hook regenerates
     from the working tree runs inside `git worktree add /tmp/<view> HEAD`
     + explicit overlay of the commit's pathspec files (the verified
     FR-859/860 recipe).
   - The six-shape taxonomy as an incident appendix (condensed, one
     paragraph per shape, cure cross-referenced to the rules above).
   - SKILL.md description updated so the trigger list includes write
     rituals, not just introspection.
2. **Adapter** — `scripts/hermetic.sh <cmd...>`: creates a HEAD worktree,
   overlays currently-staged + explicitly listed files, runs `<cmd>` inside
   with the main repo's venv python, copies declared output artifacts back,
   removes the worktree. The sole sanctioned route for hook-input-divergent
   generators (`fr_board.py`, `aggregate_capabilities.py`, changelog
   aggregation), mirroring how `judge.sh`/`review.sh` are sole routes.
   ~60 lines of bash; failure leaves the main tree untouched.
3. **Guard** — extend `.github/hooks/scripts/pre-command-guard.sh` with
   deny rules for the mechanically detectable ritual violations:
   - bare `git stash pop` / `git stash apply` without an explicit
     `stash@{n}` ref;
   - `git add -A`, `git add .`, `git add --all`, `git commit -a[m]`
     (index sweeps — the root mechanism of shapes 1 and 6);
   - denial messages point at the doctrine file (teach, not just block).
4. **Memory disposition (subtraction)** — after the doctrine lands, the
   interleave content of local `hook-lessons.md` is superseded; the memory
   file shrinks to a one-line pointer at the doctrine. Repo is truth,
   memory is cache.

## Non-Goals / Out of Scope

- Retiring the fr-board (FR-858 owns that; this FR's doctrine and adapter
  must work whether or not the board survives).
- Session-locking or preventing parallel sessions (the operator runs them
  deliberately; the goal is safe interleaving, not exclusion).
- Guarding `git push`/`git fetch` ordering (advisory in doctrine only —
  too many legitimate shapes to deny mechanically).

## Deliverables

- D-1: `doctrine.md` under session-introspection + SKILL.md description update
- D-2: `scripts/hermetic.sh` + witness test (worktree created, output copied,
  main tree bit-identical before/after on failure injection)
- D-3: pre-command-guard deny rules + guard tests (existing guard test
  pattern), audit-logged like all guard decisions
- D-4: local memory note slimmed to pointer (recorded in FR implementation
  status, not a repo artifact)

## Acceptance Criteria

- AC-1: A grep for `stash pop`, `add -A`, `commit -a` in the guard shows
  deny rules; each denial message names the doctrine path.
- AC-2: `scripts/hermetic.sh 'python scripts/fr_board.py'` regenerates
  docs/fr-board.md (or its FR-858 successor) with a dirty sibling working
  tree present, and the main tree's non-output files are untouched.
- AC-3: Doctrine file contains all six shapes with cures; SKILL.md
  description advertises write rituals.
- AC-4: Guard tests cover at least one allowed and one denied form per rule
  (e.g. `git stash pop stash@{0}` allowed, `git stash pop` denied).
- AC-5: No new required CI checks (operator git-flow constraint: single-dev
  push-to-main remains the default; guard is local PreToolUse only).

## Risks

- Guard false positives on chaplain/watcher automation that legitimately
  uses swept adds — mitigation: audit automation scripts for the denied
  forms before enabling; convert findings to pathspec form first.
- Doctrine drift vs Scripture summary — mitigation: Scripture
  `one_session_one_repo` entry gains a pointer to the doctrine as its
  canonical expansion (one-line edit, within scope).
