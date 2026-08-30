# The Parallel Writers and the Serial Door

**Date:** 2026-08-30
**Context:** Three-day retrospective (08-27 → 08-30): ~78 commits on main, the
FR-889 → FR-902 → FR-925/926 → FR-927 pipeline arc, and the worktree census
that followed.

## What the record says

Three days, four pipeline mutations:

1. **FR-889** OS-locked the main checkout — `chmod -R u-w` on governed roots.
   The filesystem, not a command grammar, became the write barrier. All change
   now routes worktree → PR → squash. This one held.
2. **FR-902** built automatic session lanes — a worktree conjured per agent
   session, with a lane guard denying writes outside it.
3. **FR-925/926** patched lane *delivery* twice ("the binding that passed
   every test and delivered nothing").
4. **FR-927** retired the whole FR-902 lane apparatus. Built on the 28th,
   patched twice on the 29th, deleted on the 30th.

The census confirms the operator's one-line diagnosis. Twenty worktrees on
disk. The four `session/*` auto-lanes: **zero commits ahead of main** — pure
residue. Meanwhile ten agent-*named* lanes (`fr912-retire-skill-export`,
`fr927-retire-fr902-lane-guard`, `featfr931-judge-review-model-upgrade`…)
carry all the live and recently-merged work. Agents never needed lanes
provisioned *for* them; they provision lanes *deliberately*, named after the
FR they serve. The automation automated the cheap step.

## The trap: concurrency moved the bottleneck, it did not remove it

FR-889 made parallel *writing* safe — genuinely. Concurrent implementation
works now; that half of the operator's statement is a success report. But
branch protection says `Require up to date: Enabled (strict)` with squash-only
merges. So with N open PRs, every merge invalidates the base of the other
N−1. Integration is a serial door that every parallel writer must re-queue
for, paying a rebase + full CI re-run per pass. The merge cost is O(N) per
landing, and the operator's calibration already names merge acrobatics as
*the* handicap — time, tokens, money.

This is Amdahl in process form: we optimized the section that was already
parallelizable (implementation) and left the serial section (integration)
untouched. Worse — FR-902 spent three FRs of effort on the parallel section's
*provisioning*, the cheapest step in the entire pipeline.

## The question that should have fired

`does_the_platform_already_do_this` — GitHub **merge queues** exist precisely
for this failure shape: strict up-to-date + many concurrent PRs. The queue
serializes the rebase-and-revalidate mechanically; authors stop hand-cranking
`git rebase` + force-push per landing. Before any local auto-rebase bot or
watcher grows here (growth_as_default watches, salivating), one settings-page
visit answers whether the platform already sells the cure. That check costs
five minutes; FR-902's lifecycle cost three FRs and a retirement.

And `would_you_use_this` should have killed FR-902 at filing: the first
consumer of an auto-provisioned lane was never named, because the consumers
(agents) already had a habit — `scripts/worktree.sh new <fr-name>` — that the
automation displaced nothing from. A lane nobody asked for is a lane nobody
enters. The four empty `session/*` directories are the physical form of an
unanswered value_proposition.

## Small witness, same day

`worktree.sh new diary-worktree-era --prefix docs` produced branch
`docsdiary-worktree-era` — prefix concatenated without `/`. Same symptom
visible in `featfr931-…`, `featfr932-…`. Three occurrences; the graduation
threshold is met the moment someone files it.

## Heuristic

**Provisioning is never the bottleneck; integration is.** When parallelizing
agent work, measure where the serial section actually sits (for us: the
strict-up-to-date merge door) and spend there. An automation whose consumers
already had a cheaper habit is residue at birth.

**Seed:** Can the merge door itself be widened rather than queued — e.g. does
the FR-919 doc-only skip generalize to a *risk-tiered* required-context set,
so a diary PR and a `graph_loader.py` PR stop paying the same integration
toll? And: one settings-page check — is a GitHub merge queue available on
this repo's plan, and does it compose with squash-only + admin-bypass reality?
