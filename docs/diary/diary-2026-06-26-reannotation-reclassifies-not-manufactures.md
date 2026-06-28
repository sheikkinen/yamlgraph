# Diary — 2026-06-26 — Re-annotation reclassifies misses, it does not manufacture hits

## Context

FR-600 enforced the GT-re-annotation lever that FR-599's miss-decomposition probe routed:
12 L7 affect deltas the licensing pass flagged as UNLICENSED (bucket (e), tied at 39% of
the recall floor). The Judge granted authority with three corrections — fix the inverted
7/5 split, freeze the verdict as a committed fixture before editing, and report recall on
both the pre- and post-drop denominators.

## The cognitive trap I almost walked into

The seductive story was: "(e) is GT error → fix the GT → the model's 'misses' become hits →
recall jumps." It is a satisfying narrative because it makes the model look better and the
fix look powerful. The both-denominator decomposition the Judge demanded (correction #3)
killed that story with one number: re-anchoring 7 deltas converted exactly **one** miss to
a hit. Recall on the **fixed** denominator moved 0.061 → 0.091; the rest of the rise to
0.107 was the denominator shrinking by the 5 drops. Had I reported only the post-drop
0.061 → 0.107 (+75% relative), I would have sold a denominator trick as model skill.

The deeper insight: **re-annotation reclassifies misses to their true lever; it does not
manufacture hits.** The former (e)=12 re-partitioned to 1 HIT, 5 (a) ABSENT, 1 (c)
KIND-WRONG, 0 (e). The annotation error was real — but correcting it *revealed* the model's
remaining failures (it predicts nothing at the experiential beat) rather than erasing them.
A boundary fix exposes the next boundary; it does not collapse the whole stack.

## The deviation that honored the spirit over the letter

Frozen step 4 said "re-run the FR-599 probe." Taken literally, that was a trap: the probe's
fixture-pins are keyed to the OLD miss-set (detective F1 loss, now re-anchored; F7
hidden_blessing, now dropped), so a verbatim re-run would fail its own calibration AND
re-introduce the non-determinism that correction #2 (freeze the verdict) exists to
eliminate. The faithful move was to re-bucket deterministically from the frozen fixture
using the probe's own `_classify_licensed` — no LLM. The letter said "re-run the probe";
the spirit said "be reproducible." When they conflict, the frozen scope's *intent* wins,
and the deviation gets recorded in the Enforcement Outcome, not hidden.

## Heuristic

**A boundary correction reclassifies error to its true source; it rarely erases it. When a
data fix is claimed to lift a metric, hold the denominator fixed and show the hit count
move on its own — the part that survives a fixed denominator is the only real gain.**

## Seed

The 5 dropped opens orphaned 3 closes elsewhere in GT (close-without-open). The closure
validator only flags the opposite. Should a corpus-integrity gate assert open/close affect
pairing on the *ground truth* itself — so an annotation edit that breaks a thread is caught
at commit, the way a dangling pointer is caught at compile?
