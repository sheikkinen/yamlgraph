# The Query That Matched Everything

**Date:** 2026-09-05
**FR:** FR-1004 retire the outsider ledger — the posted comment is the record
**Session:** enforcement, Windows host; the plan and judgement came from PR #598

## What happened

The plan replaced a committed file with a question: "how many distinct PRs
has the outsider read?" becomes one `gh search` over PR comments. The judge
insisted on a transition-safe search phrase and on a gate — the enforcing PR
must come back from that search exactly once, or the replacement is not
demonstrated. Good gate. It fired before I wrote a line of code.

The documented command returned 444 pull requests. Every PR in the
repository. I tried the phrase in four spellings; 444 each time. A nonsense
phrase — `zzqqxxnonsense` — also returned 444. The `in:comments "…"`
qualifier, written inline in the positional query, is silently dropped by
`gh` 2.98; the search degrades to "every PR" and reports success. The same
qualifier passed through the `--match comments` flag returns seven PRs, and
each of the seven carries exactly one marker comment.

The FR's measurement instrument would have counted the whole repository as
outsider-read on day one, and its documentation would have told the next
person to run exactly that command.

## The trap

A command in a plan is a *claim*, not a *witness*. The judge asked the FR to
"prove the transition query" and the FR answered with the command's text.
Text is what a plan can hold. But a search that returns everything looks,
from its exit code and its non-empty output, exactly like a search that
works — the failure mode is silent inflation, the worst kind for an
instrument whose job is to say "not yet twenty."

The nonsense-phrase probe is the whole cure and it costs one second: before
trusting any filter, ask it for something that cannot exist. If it says yes,
the filter is not a filter. Commandment 6 in query form — *when a filter
yields nothing, raise; never substitute everything* — and here the substitution
happened inside a tool I did not write and could not see.

## Two smaller ones

**Fakes that run under a different shell.** The wrapper tests drive
`scripts/outsider.sh` through `subprocess.run(["bash", …])`. On this host,
`bash` resolves to the Windows Subsystem for Linux relay, which is broken,
regardless of what Git Bash is on PATH. Seven tests cannot be witnessed here
and are owed to CI. I exercised every one of their behaviours by hand with the
same fakes from a Git Bash session — posted body byte-identical to the report,
placeholders, no ledger, non-zero on comment failure — which is evidence, but
not the test. Recorded as such.

**The self-test is a nagger's self-test.** `--selftest` expects NO/NO/NO/YES
from four fixtures. Today it produced rejected/NO/NO/NO: the model dropped
the quotes from a section-3 item once (fail-closed, as designed) and read the
positive fixture as five unclear items where FR-995's own record shows it
alternating between five and zero on the same text. The marker I came to
check was present and correct on every validated report. The instrument
varies; the record of it does not.

## Heuristic

Before documenting a search, filter, or count as an instrument, feed it an
impossible input. A filter that cannot say "nothing" cannot say "not yet."

**Seed:** the outsider's derived verdict on identical text flips between
runs; FR-995 recorded it, this self-test reproduced it. Twenty distinct PRs
is the threshold before a gate may be *proposed* — but a threshold on a
coin-flip is a threshold on nothing. Should the count be of *stable* reads
(two runs, same verdict) rather than of PRs, and is that a measurement this
comment-marker design can even express?
