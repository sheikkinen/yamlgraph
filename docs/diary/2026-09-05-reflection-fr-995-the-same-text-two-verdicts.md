# The Same Text, Two Verdicts, Two Minutes Apart

**Date:** 2026-09-05
**FR:** FR-995 outsider reader — enforce
**Trigger:** the positive fixture derived NO (5 items) at 06:24Z and YES (0
items) at 06:26Z from the identical input, on the identical prompt and model.
Operator, on being told: "gpt-5.6-sol is a nagger. almost impossible to
please. thats why the results are advisory — and number of runs limited."

## What happened

The judge's R-1 required a real positive: an actual model output that
satisfies the derived-verdict rule, with the expectation written before the
run and the threshold not loosened. I spent four glossing passes on the
#591 body. Each pass removed the phrases the previous run had flagged; each
run flagged a *different* set — 4, 3, 2, 5 items with almost no overlap.
Pass 3 met the count and tripped the hedge clause on a genuine omission (who
decides). Pass 4 added that and got five new items. Then the production
self-test ran the same pass-4 text and got "nothing".

I was, for four passes, treating the reader as a fixed function of the
text. It is not. At the borderline it is a distribution, and I was sampling
it once per pass and adjusting the input to the sample.

## The trap

`plausible_wrong_answer`'s cousin: **a single run is an opinion poll with
n = 1.** The derived rule is deterministic; the thing it derives *from* is
not. Chasing a moving item set by glossing is `two_strike_split`'s exact
symptom — reword, relocate, reword — one level up: I wasn't rewording the
prompt (that was forbidden), I was rewording the *input* to satisfy the
prompt. Same loop, different lever.

The operator's line ends the loop by naming what the instrument *is*: a
nagger. You do not calibrate a nagger until it stops nagging; you record
what it nags about, once, and let a human read it. That is what "advisory"
and "runs limited" mean operationally — not modesty, but a statement about
the variance of the source.

## What held

- The rule was never loosened. Four passes, one selftest, one judge
  revision, and ≤ 2 / no-hedge is still ≤ 2 / no-hedge.
- Every expectation was written before its run, including the stop rule
  that stopped me at pass 3 in the spike.
- Both reports for the same text are committed and both are asserted in
  tests — one NO, one YES. The record shows the variance instead of hiding
  the losing run.
- The wrapper smoke caught what unit tests missed: the renderer did not
  round-trip through its own parser. Unit tests loaded the module by spec;
  the graph loads it by path; Pydantic's forward refs differ between the two.
  The authoring route's smoke found it, again — third time this arc that
  the end-to-end run found what the unit did not.

## Heuristics

`sample_once_is_a_poll`: when an LLM output feeds a deterministic rule at a
threshold, one run per input is n = 1. Before glossing the input again, run
the same input twice. If the verdict flips, stop glossing — the variance is
the finding.

`nagger_is_not_calibrated_by_appeasement`: an adversarial reader that is
hard to please is doing its job. Its output is read, not satisfied. Limit
runs; record; hand to a human. Any later gate must measure repeat-run
variance, not single verdicts.

## Seed

**Seed:** The twenty-PR ledger will accumulate single runs. Should each ledger row
carry two runs — or should the wrapper refuse to write a verdict at all
and write only the item list, leaving YES/NO to the reader of the ledger?
A verdict that flips on a re-roll may be a column that should not exist.
