# Diary 2026-09-26 — The verdict that was overwritten

**Context:** judgement folds into FR-1076, 1079, 1084–1088 (#704); FR-1083
split into FR-1097/FR-1098; FR-1076 simplified and re-judged; judgements
committed (#705).

The operator asked "check for overengineering" and got back a real list.
FR-1076 had a lease, a lease token, a crash claim broader than any witness,
and a 10,000-item bound. None of it had a consumer asking for it; each piece
came from answering a judgement revision by adding a mechanism. After the
simplification the store is two tables: loading it writes nothing, and saving
it is one `BEGIN IMMEDIATE` compare-and-set. The re-judge accepted all four
cuts. The revisions it added (a typed load plan, reconciliation by key,
exact `base_dir` resolution) are about correctness, not scope. A judgement
round tends to inflate an FR; asking "overengineered?" is what brings it
back down.

The second event mattered more. FR-1097 and FR-1098 were judged from my
worktree, and the drafts landed in its `tmp/`. About ten minutes later a
parallel session ran `judge.sh` on the same FRs in the same worktree.
FR-1097's first draft was replaced by a second verdict on identical input.
The two verdicts disagree: the first required a persistent SQLite
checkpointer witness across two CLI runs, the second asked the operator for
an exit-code decision. FR-1098's draft was deleted, and the rerun never
finished. Nothing warned me. The files had the right names and
well-formed headers.

Committing only the surviving verdict would have been judge-shopping
performed by a stranger. It would pass every gate, because the gate checks
that `.judgement.md` exists and has its sections, not that it is the only
verdict rendered. The cure was to say it: the commit message and the PR
body name the lost requirement. The copies in `/private/tmp` exist only
because the loss was noticed. Recovering the verdict was luck, not process.

Third: #704 merged between two turns, and the operator's "include in the
open pr" referred to a PR that was no longer open. I opened #705 and said
so. It is a small instance of `recorded_is_not_read`: my picture of the
world was one turn out of date.

**Heuristic:** a judge verdict is evidence only while it is the sole
verdict on its input. When two exist for the same FR content, both are the
record. Commit the survivor with the lost one's demands named, or re-judge
and commit both. Never let the survivor stand alone.

**Seed:** should `judge.sh` stamp each draft with the FR blob SHA and a run
id, and refuse to overwrite a draft for the same SHA, keeping `-2` instead?
Then disagreement between runs becomes a visible artifact rather than a
silent overwrite. That is `artifact_carries_code_identity` applied to
verdicts.
