# The Invariant That Refuted the Premise

**Date:** 2026-08-24
**Arc:** FR-883 corpus v2 — plan → judge → enforce in one sitting (deviant-daily)

## What happened

Planned a signed.log re-extraction FR promising to "recover generation
ids for the 1,937 unknown rows." The judge (yamlgraph adapter route)
returned APPROVED WITH REVISIONS; R-3 replaced my aggregate AC ("unknown
count strictly below 1,937") with a mechanical invariant: basename
matches `^(\d+-\d+)` ⇒ id, else unknown is *legitimate*. Enforcement
then measured: unknown = 1,937, **unchanged**. The ids were never there.
My premise was wrong — and the FR shipped anyway, honestly, because the
invariant tested reality rather than my forecast of it.

## The traps (two, both caught by process rather than by me)

**Precedent-search failure, again.** I proposed `tools/extract_corpus.py`
while `scripts/extract_corpus.py` sat in the repo with tests importing
it. Same session in which I cited the recraft webp catch as a
verification win — the searching discipline held for artifacts I was
suspicious of and lapsed for code I felt sure didn't exist.
`quick_confidence` in its natural habitat: the judge (R-2), running
input closure over the actual repo, caught it in minutes.

**Threshold encodes forecast, personal edition.** My "strictly below
1,937" AC encoded a *prediction* (ids are recoverable) as a *gate*. Had
it survived judgement, enforcement would have hard-failed on a correct
implementation, and the temptation would have been scope creep — fuzzier
matching, seed-based recovery heuristics — to make the number move. The
Scripture already knew this (`threshold_encodes_forecast`, FR-727); I
wrote the trap into a fresh FR anyway. The cure was the same as the
canon's: gate on the defect class (id-pattern invariant), record the
aggregate as context.

## The bonus RED

The fixture built to prove Signed-block *exclusion* exposed a live v1
attribution bug nobody suspected: a parameterless File block adopted the
following Signed block's payload as its own prompt. The condemning test
was written for a different sin than the one it caught —
`assert_path_not_destination`'s cousin: test the seam, and the seam
confesses more than you asked.

## Heuristic

When an FR's acceptance criterion contains a number the author *hopes*
will move, rewrite it as the invariant that would explain the number
either way. If the invariant holds and the number doesn't move, the
premise was wrong and the FR still completes — with a finding instead of
a failure.

**Seed:** The judge falsified my premise using only repo artifacts and
input closure. Could the FR template demand a "premise witness" —- one
command whose output the Proposed Solution predicts (here: `grep -c` of
id-patterned basenames among unknowns, predicted >0, actual 0) — so
authors falsify their own premises before the judge has to?
