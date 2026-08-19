# 2026-08-19 — The Collision Cure That Recolonized the ID

**Context:** Status sweep of FR-818..822 and the GitHub-runner automations
(daily-digest, weekly-recap), requested as "check latest FRs, github runner
based automations. reflect."

## What the sweep found

The automations are healthy: daily-digest cron has fired successfully five
days straight (Fly.io endpoint route, pre-FR-819-PoC architecture), and
weekly-recap (FR-821) has its dispatch proof (PR #473 merged by recap-bot
via auto-merge) with the first true cron observation due Monday 2026-08-24.
The FR arc 814→818 (knowledge graph → judge context narrowing) and
819→820 (hosted runner → Stripe credits) are coherent, well-dispositioned
chains. FR-822 shipped a live DeviantArt publish in half a day.

## The trap: collision_cure_reallocates_from_stale_view

`FR-819-hosted-declarative-graph-runner.md` proudly documents its own
collision cure: "originally filed as FR-815; renamed to FR-819 on
2026-08-18 to resolve an ID collision." But `FR-819-github-native-digest-
poc-repo.md` — filed the same day, in a parallel session — already owned
FR-819. The rename resolved one collision by creating another. The cure
executed the same defective allocation procedure as the disease: pick the
next-free ID from a *local, stale* view of the corpus.

This is the `one_session_one_repo` shared-index race and the
`cap-req-id-allocation-race` (CAP/REQ IDs, same shape) recurring for a
third artifact class. Three strikes across ID families — this is now a
pattern of the *allocation mechanism*, not of any one session's care.

## The consequence is silent, which makes it worse

`docs/fr-board.md` renders exactly one FR-819 row. **Correction (same
day, during the repair):** the missing row was *terminal-status
filtering* (Completed FRs are excluded by default; `--all` includes
them), not ID-based dedup — I asserted the shadowing mechanism before
reading `fr_board.py`, a small `quick_confidence` instance inside the
very entry that preaches against it. The collision is still real and
still harmful — two FRs sharing one ID corrupts every cross-reference
(FR-820 cited "FR-819" fourteen times meaning Serve, while FR-821 cited
"FR-819" meaning the digest PoC), and the FR-814 knowledge graph would
merge the two into one node. Nothing checks "is the ID a unique key" at
the write boundary; the violation was found only because a routine sweep
counted files (`ls | grep -c "^FR-819"` → 3).

## Heuristic

An ID collision fix must not reuse the allocation procedure that caused
the collision. Renaming to "next free per my working tree" after a
parallel-session race is the same bet, re-placed. The cure is mechanical:
allocate against origin (`git ls-remote` + fetch, or a pre-commit
uniqueness check over `feature-requests/FR-*.md` stems) — normalize at
the boundary where the ID enters, not downstream where the board dedupes.

## Seed

**Seed:** The repo now has three ID families (FR, CAP/REQ, diary dates)
allocated by "look at the directory, increment." Should a single
`scripts/next_id.py --family fr` + pre-commit uniqueness gate own all
three — and would the weekly-recap automation PR pattern (FR-821) be the
right vehicle to let CI itself file the collision-repair PR when a
duplicate lands anyway?
