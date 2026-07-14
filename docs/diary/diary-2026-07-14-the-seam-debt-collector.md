# The Seam Debt Collector (FR-723 enforce)

**Date:** 2026-07-14
**FR:** FR-723 — execution path visualization (route hook + mermaid export + overlay + diff)

## What happened

The enforce itself was boring — the Judgement was good. The route hook
landed at `routing.py` exactly as ruled, the zero-overhead test led the
file, the reflexion demo routed refine→refine→END on a live run with the
thread_id carried, and the loop-exit line — the seam the ninchat
prototype could not see by construction — appeared in the first
route.jsonl ever captured.

Everything interesting happened at the *boundaries around* the enforce:

1. **The REQ allocation race fired again, mid-commit.** I checked for
   duplicate IDs after `git pull` per the standing memory note — clean —
   then allocated REQ-YG-551/552 from a `sort | tail` that silently
   misparsed and missed CAP-203's committed 551. The
   `validate-capabilities` gate caught it (the seed from the 2026-07-08
   diary entry became a real gate, and it paid for itself today).
   Renumbered per the landed-first rule.

2. **Filing R-3's migration NC in ninchat_voice collected someone
   else's seam debt.** The NC is a one-file docs commit — but the repo's
   pre-commit pytest was red at HEAD: NC-373's routing split had
   orphaned three test expectations (import, monkeypatch target, source
   probe) — `refactor_orphans_secondary`, verbatim. And *behind* that
   collection error hid a second failure: the venv's yamlgraph was one
   release stale and rejected a graph the current schema accepts. A
   collection error is a tarp over the rest of the suite — fixing it
   uncovers debts nobody has seen yet. The reasoning sentinel fired on
   my prose while I was fixing them; the doctrine and I agreed on the
   action (fix, don't bypass), but the flagged phrase was in my
   explanation. The guard reads language because language leaks intent.

## The insight

A cross-repo deliverable ("file an NC before merge") is priced as a
docs commit but costs whatever the target repo's gates have been
accruing since the last commit that exercised them. The five-line NC
cost: one import repair, two patch-target repairs, one expectation
table, one venv upgrade. None of it was waste — it was NC-373's
undelivered mail, and FR-723's R-3 was simply the next courier through
the door. Enforcement gates make debt land on the next visitor, not
the debtor; that is still strictly better than the debt compounding
invisibly.

**Heuristic:** before filing even a docs-only commit in a sibling repo,
run its unit gate first (`pytest -q` costs 1s); budget the repair into
the task instead of discovering it inside a failing commit loop. A
collection error is never one failure — count the suite only after it
collects.

## Seed

The stale-venv failure and the orphaned-import failure were both
*version skew between a repo and its own HEAD-adjacent state* — one in
site-packages, one in a test's mental model of the module tree. Could
the chaplain's post-merge finalization run sibling-project smoke gates
(collect-only pytest in `projects/*`) and file the repair NCs
automatically — making the debt land on the debtor's pipeline instead
of the next courier?
