# The Guard That Caught Its First Thief on Day One

**Date:** 2026-08-30
**FR:** FR-930 (code-owned FR-reference reconciliation in the recap demo)

## What happened

FR-922 closed with the recap's live anti-hallucination test in a "gray zone":
slow, vendor-bound, evaluation-shaped. The idiomatic answer was already in the
graph's own history — FR-702/703/704 each moved a "the model must not X"
instruction into code that makes X impossible. FR-930 applied the same eviction
to the last surviving prompt-only clause: model-authored FR/NC refs are now
claims, reconciled in `finalize_recap` against the model-visible deterministic
universe, stripped and recorded when unverified.

Then the demo-gate run turned the design note into a field report. Two
Anthropic runs timed out at `synthesize`; the operator said "run with
provider=inception". Mercury returned a recap with **five invented FR
references** (`FR-861`–`FR-864`, `FR-914`) on its first attempt — and the
hour-old reconciler stripped and recorded all five. The PR's own witness log
contains the exact defect class the retired test existed to sample, caught by
construction, on run one.

## The insight

The old test asserted a *vendor's* behavior: `skipif(not ANTHROPIC_API_KEY)`,
one sampled output, one model's hallucination rate. The moment the provider
changed, the behavioral premise silently changed with it — Mercury hallucinates
where Haiku (mostly) doesn't. A sampled witness is not just expensive; it is
*scoped to the model it sampled*. Enforcement at the boundary is
provider-invariant, which is the only invariance a multi-provider framework can
honestly claim. Provider swap is not noise to control for — it is the
strongest argument for construction over sampling.

## The trap avoided (narrowly)

My first universe design included `fr_statuses` — every FR at HEAD. The judge
caught it (R-2): the model never sees `fr_statuses`, so a real-but-invisible id
would have survived reconciliation and collected a `[Status: …]` tag —
credibility laundering for a hallucination. I had defined "source of truth" as
*what the repo knows* instead of *what the model was shown*. The universe for
reconciling a claim is the evidence the claimant could legitimately cite, not
everything the verifier happens to know. `never judge in the author's session`
earned its keep in one review cycle.

## Heuristic

**witness_scope_equals_vendor_scope** — any live-model test silently asserts
the sampled vendor's behavior distribution. If the guarded property must hold
across providers, it cannot be witnessed by sampling one; it must be enforced
at the boundary. Check every live LLM test: is it witnessing our code, or one
vendor's temperament?

**Seed:** the reconciler records `unverified_refs` but nothing reads them yet
(`who_reads_this_when`). Mercury's five-ref field run suggests a cheap eval
lane: run the recap demo across all configured providers and diff their
`unverified_refs` counts — a per-provider hallucination scoreboard from an
artifact we already emit. Is that the first consumer, or is the log line
enough?
