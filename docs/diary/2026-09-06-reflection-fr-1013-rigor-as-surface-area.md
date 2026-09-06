# Reflection: rigor as surface area — the FR-1013 theatre

**Arc.** FR-1013 was a documentation sweep: rename one heading, drop one
clause, fix a dozen pointers, move one file. It consumed four judgement
rounds, three review rounds, two PRs, sixteen commits, a new requirement, a
261-row sha256 baseline and a 421-line test — and was closed unmerged by the
operator with "now stop and reflect. what's happening here". Re-filed as
FR-1019, about forty lines.

## What the raw record says

Round 1: APPROVED WITH REVISIONS, 5 revisions. Round 2: SPLIT (a closure
script had crept in). Review 1: 7 blocking findings. Round 3: APPROVED WITH
REVISIONS, 4 revisions. Review 2: 6 findings. Round 4: APPROVED WITH
REVISIONS, 3 revisions. Review 3: 1 finding. Every verdict was "almost"; every
fold made the FR longer; every longer FR produced a new list. The FR went from
~150 lines to 413. The test went from 20 assertions to a per-file hash of
every Chaplain-matching line in 261 files, pinned to a single commit forever —
a tripwire that would have sent the next session that wrote "watcher" in a
reference doc back to *this* FR's judgement.

Of the fourteen review findings after round 1, about half were defects I
introduced while fixing the previous round: SHAs churned by my own rebases, a
merge-order sentence I wrote backwards, a link one directory short, a
`git cat-file` design that cannot run in a depth-1 CI checkout. The other half
were the reviewer reading a bigger document and finding more in it.

## Two traps

**`rigor_as_surface_area`.** The judge and reviewer are models. They read the
whole artifact and return findings roughly proportional to what there is to
read. Folding findings adds text; text invites findings. There is no fixed
point inside the loop — it terminates only when a human says stop. The command
book already encodes this (`merge` is the human's word), and I treated each
verdict as a gate to clear instead of input for the human to weigh. The FR
grew because I never asked whether the *finding* was worth its cost, only
whether I could satisfy it.

**`own_churn_as_findings`.** Rebase-then-record produced stale SHAs; fix a
sentence, get its ordering wrong; add a check, break it in CI. Each round's
verification was "the target test passes here", never "what did I just
change that the previous round did not ask for". Half the queue was my own
tail.

Both wear the costume of `working_system_inertia` inverted: not "it works so
don't look", but "it was asked for so don't weigh". The Scripture's
`forced_opposite` — state the strongest case *against* before granting — never
fired on a judge's revision, because `plan-judge is never challenged` had
quietly become `the agent never challenges`. The one finding I did refuse
(the closure script) I refused only because a judge had already refused it.

## Heuristic

Before folding any revision, cost it against the Ideal Result in one line:
*does this bring the artifact closer to the ideal, or closer to the reviewer?*
A revision that adds a table, a baseline, a requirement, or a permanent gate
to a one-time cleanup is the second kind; answer it with a sentence in the FR
("refused: X would outlive the change it guards") and let the human decide.
Round count is a signal: a third judgement round on a docs FR means the FR is
being written *for* the judge.

Corollary for the fix loop: after every fold, diff the whole PR against the
previous head and read the diff as the reviewer will, before running the
route again. The cheapest finding is the one I catch in my own diff.

**Seed:** should `scripts/judge.sh` and `scripts/review.sh` print, next to
the verdict, the round number and the artifact's growth since the previous
round (lines of FR, lines of test) — so that "round 3, +180 lines" is visible
to the human at the moment the human can still say stop, rather than after
the fourth?
