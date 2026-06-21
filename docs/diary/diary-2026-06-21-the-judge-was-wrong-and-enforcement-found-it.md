# The Judge Was Wrong, and Enforcement Found It

**Date:** 2026-06-21
**FR:** FR-561 (DM v3 M2 -- causal trio hardened)

## What happened

I judged FR-561 myself, folded the judgement into the FR, and then sat down to enforce it. One of my
own judgement notes -- J5 -- claimed the new pure antecedent check would "also flag
`early_reveal_variant.Fonstage` as `open_condition`, subsuming the engine proof." I had even written
an acceptance-criterion bullet asserting it.

It was false. When I re-read the floodmark fixture against the check I was about to write, the
contradiction surfaced: `Fonstage`'s precondition is `believes(Clan, alive(Arnulf))=True`, and that
belief **is in `initial_belief`** (held=True). An existence-based check -- "is this atom in `I` or
produced by an earlier beat?" -- finds it grounded and does *not* flag it. The early-reveal is
unsolvable for a *temporal* reason (F1 flips the belief False before Ch3), which is precisely the
planner's job, not a missing-antecedent flaw. To make the pure check catch it, I would have had to
track latest-value-along-the-order -- re-implementing causal coherence and duplicating the engine,
violating the design's own split (check 1 = engine; checks 2/3/4 = hand-written).

So I corrected J5 in the FR before writing a single line of the check, kept the check existence-based,
and replaced the false AC bullet with its honest inverse: `validate_plan(early_reveal_variant)` yields
**no** `open_condition`; early-reveal stays an engine proof.

The rest landed cleanly: RED (phantom + overbudget fail, the other five pass -- including `threat`,
which confirmed J1's claim that the *current* encoding already proves a forced-window unsolvable with
no `build_problem` change), then GREEN: `open_condition` added to `FlawCode`, the pure
`_check_causal_antecedent`, a unary-counter `turn_budget` (the classical engine rejects `Int`
fluents, so a chain of `rem_<k>` markers is the only viable budget encoding), and a report
causal-health line. 444 DM tests green.

## Trap

**judge_as_infallible_authority.** I treated my own judgement as frozen authority and started to
implement a test asserting something I had asserted but never checked against the fixture. The
judgement is *not* the proof -- it is a plausible plan that can hide a subtle error exactly the way
plausible code does. J5 was a `plausible_wrong_answer` wearing a judge's robe: it had the shape of a
sharp insight ("the pure check subsumes the engine!") and was simply wrong about where the data lived.

## Cure

**enforce_reconciles_spec.** Enforcement is not stenography of the judgement; it is the first place
the judgement meets the actual fixtures and types. When the code contradicts a judgement note,
*correct the spec* -- it is the cheapest bug to kill, cheaper than a wrong test that would have to be
unwound later. Read the fixture thrice before trusting the note. The honest AC ("yields no flaw") is
worth more than the impressive one ("subsumes the engine").

## Seed

If a judge's note can be falsified by reading one fixture, should the Judge step *require* citing the
specific fixture/line that witnesses each claimed behavior -- turning every judgement assertion into a
pre-registered, mechanically-checkable prediction before enforcement begins?
