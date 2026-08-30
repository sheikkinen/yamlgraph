# The Counterfactual I Almost Didn't Run

*2026-08-30 — FR-932 enforcement*

## What happened

FR-932 gives the research route's personas the feature-request corpus they
had never been shown. Enforcement went cleanly through two RED/GREEN pairs.
Then the live run failed on a 400-character schema overflow. I re-ran it.
Same failure. Re-ran again. Same failure, same persona, same field, same
truncated input preview.

I had a theory ready before the third run finished. My change adds a
prior-art block to the persona context. The brief is *about* prior art. The
overflowing text quoted my own block — "corpus the personas saw". Obviously
the added context made the personas verbose. I measured the delta to
quantify my own culpability: 388 characters on 12,000, a 3.2% increase.

I was three sentences into writing "my change caused this" in the FR when
the number stopped me. 3.2% context growth causing 4-of-4 failures across
three different personas is not a proportionate effect. So I checked out
`examples/demos/research-route/` at the pre-FR-932 commit and ran it again.

It failed too. Different persona, different field, same 400-character class.

## The trap

**Causal narrative arrives before causal evidence, and it arrives wearing
the evidence's clothes.** Every element of my story was true: my change did
add context, the brief was self-referential, the failing text did quote my
block. The story was coherent, specific, and grounded in real observations.
It was also wrong, and it was *more* persuasive for being detailed.

What made it dangerous was that it was self-incriminating. I had internalised
"a red suite belongs to the current change author" as *assume you broke it*,
and the guilty explanation felt like the humble one. The reasoning sentinel
fired at me later for the opposite reflex — disclaiming ownership — which is
the correct thing to police. But ownership means *find the cause*, not
*assume you are it*. Confessing to an unproven cause is as much a failure of
evidence as denying a proven one, and it is harder to catch because it looks
like integrity.

The counterfactual cost one command and two minutes. I nearly skipped it
because I already had an explanation that fit.

## The other one

The same discipline paid twice in one session. The FR's headline measurement
— "15 of 60 precedent cells cite nothing" — came from a regex I wrote
myself. Re-running the count through the repo's own `_classify_precedent`
showed all 14 untraceable rows sat in artifacts that predate the validator
which now raises on them. A closed hole. I had sold the judge a defect that
no longer existed, and the judge granted authority partly on that number.

Both errors share a shape: **I measured with an instrument I built for the
occasion instead of the one the repo already trusts.** My regex, my causal
story. The repo's validator and the repo's own prior code were both one
command away.

## The finding I'd have missed

Owning the red suite instead of routing around it produced the session's most
valuable artifact. Three FR-737 tests were failing before I touched anything.
Doctrine forbids the phrase that would have let me move on, so I traced them:
`prior_art.py` imports `yaml` at module scope, `fr-checks.sh` invokes it with
bare system `python3`, and swallows stderr with `2>/dev/null || true`. The
prior-art notification hook had been silently dead. `yaml-checks.sh` shells
out the same way and is dead the same way.

A hook that fails loudly gets fixed in a day. This one was engineered to fail
quietly, and the tests that knew were red long enough to become scenery.

## Heuristic

**Run the counterfactual before writing the causal sentence.** When a failure
appears during your change, the cost of reverting your change and re-running
is almost always smaller than the cost of a wrong root cause entering the
record. Guilt is not evidence. Neither is innocence.

Corollary: when you find yourself measuring the *magnitude* of your own
culpability, you have already skipped the question of whether it exists.

## Seed

The reasoning sentinel catches "not introduced by this change" — the
disclaiming direction. Nothing catches "introduced by this change" asserted
without a counterfactual. Both are unfalsified causal claims about a red
suite; only one is policed. Should attributing a failure to your own diff
require the same evidence as attributing it elsewhere — and what would the
witness look like?
