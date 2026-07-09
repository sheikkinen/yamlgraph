# The Regex Repeats the Model's Sin (FR-702)

**Date:** 2026-07-09
**Context:** FR-702 enforce — disposition axis + mechanized orphan detection for the recap demo.

## What happened

FR-702 existed because the model mis-flagged referenced commits as orphans
(mid-subject refs, 2/6 false positives). The cure was mechanization: a regex
pre-pass so the failure class becomes "impossible by construction."

The first GREEN demo run put `a9a8bdec docs(fr-691): …` in orphans. The
mechanical cure had the same disease: the frozen pattern
`(FR|NC)-[0-9]+|#[0-9]+` was case-sensitive, and conventional-commit scopes
lowercase the ref. The Judge verified the pattern's *mechanism* (Jinja2 has no
regex → python pre-pass) but not its *coverage* against real data.

## The trap

Mechanization moves a judgement from model to code but does not validate it.
"Impossible by construction" is only as true as the construction's test corpus.
The regex was frozen at Judgement against three imagined variants (FR-, NC-,
#N) — none drawn from an actual `git log` of the repos it would run on, where
`docs(fr-691):` sits in plain sight. Spec-time examples are generated;
field data is sampled. Only one of these finds the lowercase scope.

## What saved it

`read_raw_output_first`, twice over. The FR itself was born from reading a raw
recap; the deviation was caught by reading the raw output of the *fix's own
first run* — before commit, cost: one read. The condemning test
(`test_lowercase_scoped_ref_is_referenced`) now carries the real commit line
verbatim as its fixture. Same-day symmetry: the FR that mechanized a
read-raw-output finding was itself corrected by a read-raw-output finding.

## Heuristic

When a Judgement freezes a *pattern* (regex, glob, grep expression), the
freeze must cite matches against sampled field data, not invented examples —
the same evidence standard the Scripture already demands for metric FRs
(N cited samples with a detail a generated dump could not produce). A regex
judged against imagined inputs is a spec-time `plausible_wrong_answer`.

**Seed:** Should W-lint or the Judge checklist gain a "pattern freeze requires
field-data citations" rule — mechanically: any FR fencing a regex must include
at least one fixture line marked as copied verbatim from a real corpus?
