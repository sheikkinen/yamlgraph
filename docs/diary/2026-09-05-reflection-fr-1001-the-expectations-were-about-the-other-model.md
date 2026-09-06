# Reflection — FR-1001: the expectations were about the other model

**Date:** 2026-09-05
**FR:** FR-1001 (`yamlgraph-outsider` standalone repository)
**Arc:** FR-990 census → FR-995 outsider reader → FR-1001 demo repo (this), with FR-1004 (ledger retirement) landing beside it from a parallel session.

## What happened

Four fixtures, expectations written before any run, as doctrine requires:
NO/NO/NO/YES. Eight runs on the sample configuration. Result:
REJECTED/REJECTED, NO/NO, **YES/YES**, **NO/NO**. Two of four inverted, one
never produced a report. Both passes agreed on every fixture — the instrument
was steady; the forecast was wrong.

Reading the raw readings before touching anything (the Scripture's
`read_raw_output_first`) showed why. The expectations had been written against
**sonnet's** failure mode from spike 2: it flagged every path and identifier and
quoted inline explanations as unknowns. The "positive" fixture was built to pass
*that* reader once a reducer set those aside. Haiku does not have that failure
mode — across eight runs the reducer set aside exactly one item (`FR-990`). Its
items were phrases the text genuinely leaves undefined: "mercury-2" is named but
never called a model; "cross-cutting" is used without saying in what sense. The
reducer, designed for sonnet's disease, was correct and nearly idle; the
fixtures encoded a prediction about a model that was not the one under test.

## The trap

`threshold_encodes_forecast`, in a new costume. The Scripture entry is about
aggregate acceptance gates; here the gate was a per-fixture verdict sequence.
Same mechanism: the acceptance criterion tested the author's *forecast* of what
the model would flag, not the property the FR was actually about (does the
reducer set aside paths/identifiers/glosses and nothing else? — yes, proven by
typed tests and by the eight runs). When the sequence failed, the reflex offered
three moves: switch to the model the forecast was written for, edit the fixture
until it passes, or record. The operator chose record. The first two are the
same move — bend the evidence toward the expectation — and both would have
looked like diligence.

A second, smaller trap: the live test originally asserted `rc == 0` *before*
capturing the raw reading. A rejected reading therefore left no evidence at all —
the fail-closed design, correct for production, erased the very artifact the
investigation needed. The fix was to capture the claim before validating it
(`OUTSIDER_DUMP_READING`), which is the same boundary principle as the parser
itself: the raw record must exist independently of whether it passes.

## The heuristic

**Expectations name their model.** A pre-written expectation for an LLM stage is
a forecast *about a specific configuration*; it does not transfer when the
configuration changes, and a fixture set tuned to one model's failure mode will
read a better model as a regression. Before reusing fixtures across a model
change, ask: what did the previous model get wrong, and did I build the positive
case to pass *that* wrongness? If yes, the fixture is a test of the old model,
not of the pipeline.

Corollary for evidence: **capture before you validate.** Any fail-closed
boundary needs a raw-record hook upstream of the rejection, or the failures that
matter most are the ones with no trace.

## Also seen

- Batch string replacement failed silently for all seven edits while the same
  edits succeeded one at a time. I did not diagnose; I routed around. Noting it
  so the next session does not lose ten minutes re-discovering it.
- PR #597 auto-merged while I was still amending its branch; two commits landed
  on an orphaned remote branch and main carried the stale plan for an hour. Arm
  auto-merge *after* the last push, or expect the merge to outrun the author.

**Seed:** the outsider now exists in two bodies — the Copilot route here and the
provider-API route in its own repository — and they disagree in kind (one
flickers and discriminates, the other is steady and literal). Could the two be
run as a pair on the same PR, with agreement as the signal and disagreement as
the interesting case, instead of choosing one?
