# 2026-08-23: The Worktree Is the Airlock

## Context

Operator pointed me at the sibling session's notes: a worktree-based
process for regenerating docs/fr-board.md under parallel-session
contention (hook-lessons "FIFTH SHAPE", verified on FR-859, executed
live for FR-860: `git worktree add /tmp/fr860-view HEAD`, overlay the
pathspec files, regen the board inside, copy the artifact out, remove
the worktree, commit path-limited).

## What the Two Sessions Did Differently

Same hazard, two lineages of cure. My session fought the shared tree
*in place*: `--only` pathspecs, `git show --stat` audits, soft reset
after a foreign-file sweep. Each incident produced another ritual step
— the interleave taxonomy grew to six named "shapes", each with its own
counter-choreography. The sibling session stopped adding steps and
changed the substrate: compute against an **immutable snapshot** (a
throwaway worktree of HEAD plus explicitly overlaid inputs) instead of
the shared mutable working tree.

That is `the_one_law` applied to concurrency. The hook-time tree is a
boundary where another session's state enters my computation; the
in-place rituals are all `downstream_fix` — guards added where the
symptom manifests (stash conflicts, drift loops, swept files). The
worktree normalizes at entry: the sibling's staged/unstaged/untracked
state simply cannot reach the computation, so five of the six shapes
become unreachable rather than individually parried.

## The Trap I Was In

`working_system_inertia`, ritual variant: my counter-choreography
*worked* (every incident was caught and repaired), which hid that the
ritual list was growing linearly with incident shapes. A cure whose
size tracks the taxonomy is a symptom catalogue, not a cure. The
signal I missed: when the third "shape" got a number, the numbering
itself was the diagnosis — same as `audit_as_ritual` (3+ without a
structural fix → ritual).

## The Sharper Point: Subtraction Still Beats the Airlock

The worktree process is elegant, but it hermetically seals a
computation that FR-858 proposes to delete outright (retire the
committed fr-board). If 858 lands, the best version of this ritual is
the one nobody runs. Rank of cures, best first: **remove the shared
artifact** (858) > **compute in an airlock** (worktree) > **choreograph
around the contention** (my six-shape ritual). I was operating at rank
three while the sibling found rank two and the FR pipeline already
holds rank one. `growth_as_default` in process form: my default was to
grow the ritual, not to prune the artifact that necessitated it.

## Heuristic

When a shared-mutable-state hazard produces its second named "shape",
stop writing counter-choreography. Move the computation into an
immutable snapshot (worktree, `git archive`, clone) — or better, ask
whether the contended artifact should exist at all.

**Seed:** The worktree-simulation pattern generalizes past fr-board:
*any* pre-commit hook that regenerates from the working tree
(aggregate_capabilities, changelog aggregation, future generators) has
the same hook-input-divergence class. Should the repo grow a single
`scripts/hermetic.sh <cmd>` that runs any generator inside a
HEAD-worktree overlay — so the airlock is a primitive, not a per-hook
recipe rediscovered in memory notes? Or does FR-858's precedent say
the answer is always: retire the committed generated artifact instead?
