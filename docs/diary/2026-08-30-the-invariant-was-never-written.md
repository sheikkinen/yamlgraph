# The Invariant Was Never Written

**Date:** 2026-08-30
**Context:** FR-889 wording audit + FR-902 intent archaeology, ordered by
the operator after the docs-exception amendment merged (PR #505) and
FR-927 (lane-guard retirement) was judged with enforcement withheld.

## The question

Was FR-889's target unspecific? The operator's actual target, stated in
five words after the fact: straightforward protection of main, forcing
agents into worktrees for all changes. And separately: what did FR-902
actually want?

## Finding 1: FR-889 specified the mechanism's coverage, not the invariant

FR-889 is a remediation FR — its Summary is "stop predicting writes by
parsing shell; make the OS refuse them." That sentence names a mechanism
swap. The policy invariant — *no agent-originated write lands on the main
checkout outside runtime lanes* — appears nowhere in the document. The
Ideal Result section is an example scenario (`echo x > yamlgraph/f.py`
denied), and an example is not an invariant: it let the coverage set be
inherited from FR-888's "enforcement-class directories" concept, five
roots plus a docs exception that nobody re-derived from first principles.

The measurable consequence: every gap between mechanism coverage and the
operator's policy surfaced as an operator correction — the §4 scope
additions pre-enforcement, then the post-merge amendment removing the
docs exception ("agent should not have any business writing to main").
Two amendments, each one the invariant asserting itself against a
coverage list.

`ideal_result_backwards` was followed in form but not in kind: the ideal
was written as a *scene*, not a *law*. A scene can be satisfied by a
mechanism that covers the scene. A law forces the coverage set to be
derived, not inherited.

## Finding 2: the hook mechanism is wrong for enforcement, right for two things

FR-889's own tool-space table already renders this verdict, and the
amendment arc confirms it. Hooks that parse command text to predict
write targets are condemned — undecidable language, unbounded fuzz
surface. What legitimately remains in hooks after FR-889 is exactly:

1. **Cure delivery** — the edit-tool denial whose message carries the
   executable worktree instruction. The kernel says EACCES; the hook says
   *why* and *what to do instead*.
2. **Lock defense** — the narrow R-2 chmod/chflags/setfacl fence that
   keeps the audited unlock verb as the only door.

Anything beyond those two roles is the condemned class wearing a new
check number.

## Finding 3: FR-902 had three intents; the guard served half of one

Intent archaeology from the FR text: (1) inter-session collision
immunity — mechanize `one_session_one_repo` after its third strike;
(2) loss prevention — checkpoint commit per turn so a dying session
loses nothing; (3) cost/provenance join — Session-Id/Request-Index
trailers making the FR-898 ledger joinable to git history.

The lane guard (Check 8) was only the enforcement half of intent 1. And
it was a **new write-verb shell grammar committed four days after the
FR-888 post-mortem condemned exactly that pattern class** — while
FR-889, the FR deleting the original grammar, was already judged and in
flight. The condemnation was scoped to the artifact (Check 7 of one hook
file), not the pattern class, so the class re-entered through a sibling
FR and nobody's gate fired. FR-902's judge approved D-5 without citing
the post-mortem that condemned its shape.

## Finding 4: the OS lock does not subsume FR-902's first intent

Easy to believe, false: "main is locked, so sessions can't collide."
The lock protects main from *all* sessions; it does nothing between
sessions — every worktree is writable by the same user, so session A
can still sweep session B's staged files or delete its untracked WIP.
With FR-927 retiring the SessionStart/Stop hooks, intent 1 returns to
ritual plus `now.py` visibility, and intents 2 and 3 become unserved
(the join tooling survives, but nothing writes trailers anymore).
Retiring the mechanism was right; the intents are now open questions
again, and honesty requires saying so rather than letting the
retirement read as "problem solved."

## Trap (proposed): condemnation_scoped_to_artifact

A post-mortem condemns a pattern but names only the artifact bearing it
→ the pattern re-enters through the next FR that needs the same job
done, and every gate passes because no gate knows the *class*. Cure: a
condemnation names the class and plants a structural test for the class
(FR-889's R-6 did this — but only for the one hook file; FR-902 added
its grammar to the same file *behind* the R-6 test's blind spot, matched
by activation condition rather than parser shape). Second witness makes
this Scripture; this is the first recorded.

## Heuristic

When writing a protection FR, write the invariant first, as a single
sentence with a universal quantifier, and derive the coverage set from
it in the FR body. If the coverage set is a list someone inherited, the
amendments are already scheduled.

**Seed:** FR-902's three intents are orphaned, not refuted. Does
intent 1 (inter-session immunity) have an OS-shaped answer the way main
protection did — per-lane ownership, or a commit-time boundary check
(fsmonitor/index guard) instead of a write-time grammar? And is intent 3
(turn-level provenance) cheaper as a read-side join over the platform's
own session store than as write-side trailers? Both deserve one-page
dispositions before anyone writes another hook.
