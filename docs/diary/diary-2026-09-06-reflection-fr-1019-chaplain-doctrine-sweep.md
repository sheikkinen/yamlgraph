# Reflection: the acceptance criterion that was already red

**Date:** 2026-09-06
**FR:** FR-1019 doctrine and reference sweep after Chaplain removal (Phase 3 of FR-1010)
**Session:** Claude Code on the Windows host; two judge rounds, one critique of the judge, then the port

## What happened

FR-1019 was the forty-four-line re-file of FR-1013, written to be short after
FR-1013 had grown to four hundred lines and four judgement rounds. The judge
rejected it in round 1 and approved it with four revisions in round 2. The
operator then asked for something the FR-1013 loop never got: a critical
review of the judgement itself before granting authority. Four of nine
revisions had caught real defects; three were legibility asks for the
reviewer; one label (REJECTED) was forced by a doctrine clause for a missing
link to research that already existed. The operator read that and said
enforce. The FR ended at 108 lines, with no census, no baseline, no new test
and no new requirement.

Two details are worth keeping.

**The FR's own residual check was red before the change.** AC-5 asserted that
no tracked file outside a short allowlist contains `.chaplain/inbox`,
`.chaplain/scripts` or `start-system.sh`. Running that grep on `main` took two
seconds and returned about forty files: capability records, old plans, census
artifacts, a demo script, two tests. The FR had re-created, in one line, the
inventory that killed FR-1013, and nobody had run the line. The judge caught
it by traceability reasoning (the test could not be tagged); the grep would
have caught it at authoring time for free.

**Folding came before weighing.** I folded round 1's five revisions into the
FR and re-ran the judge in the same breath, exactly as the FR-1013 sessions
did. The cost assessment — does this revision move the artifact toward the
Ideal Result or toward the reviewer? — happened only because the operator
asked for it after round 2. Done first, it would have produced the same
folds, but it would also have named the two trims (the six-row outcome table,
the struck "one round" sentence) at the moment they were cheap to refuse.

## The trap

**`acceptance_criterion_untested_on_base`.** An acceptance criterion is a
command whose exit code the author has never observed. It is written from
the picture of the finished change, so it encodes what the author believes
the repository looks like, not what it looks like. When the belief is wrong
the criterion is either impossible (AC-2 forbade `.chaplain/` in a file made
of `.chaplain/` paths) or it silently widens the scope to whatever the grep
happens to find (AC-5). Both were in a forty-four-line FR written by a
session that had just spent a day in these files.

## Heuristic

Run every fenced acceptance command against the current tree before the FR
is judged, and record which ones are already red. A criterion that fails on
`main` before the change is not an acceptance criterion for this change; it
is either a spec error or a different FR. The judge's measurability rubric
asks whether the command *can* run; this asks what it *says* — the same move
as `read_raw_output_first`, applied to the gate instead of the output.

Corollary: weigh a judge's revision before folding it, in one line each, and
put the refusals in the FR as sentences. The round-2 critique took ten
minutes and changed nothing in the enforcement — but it is the step whose
absence let FR-1013 run to four rounds.

**Seed:** should `scripts/judge.sh` extract the FR's fenced `bash` acceptance
blocks and run them against `BASE` before the model reads the FR, so that the
judgement opens with "these criteria are already red on the baseline" — a
mechanical pre-read that would have flagged AC-2 and AC-5 in round 1 without
spending a model turn on them?
