# Two artifacts agreeing is one observation copied

**FR-1055** — `system_segments` built perfect Anthropic cache blocks and then
posted them to an address nobody reads. Eight tests were green. A shipped demo
logged `✓ Cache hit!`. Both were wrong, and neither could have noticed.

## The trap: the producer's own output is not evidence

Every Anthropic assertion in `test_prompt_caching_fr276.py` read the blocks
back out of `additional_kwargs` — the same field the producer had just written.
The suite verified that yamlgraph wrote into a box. Nothing verified that the
consumer opens that box, because nothing in the repo ever called
`langchain_anthropic._format_messages`.

This is `unexercised_links_pass_every_test_of_the_chain`, and the tell is
specific: **a test whose assertion reads the field its own subject just
wrote.** That is not a round trip; it is a mirror. The fix for a mirror test is
not a better assertion, it is a second party.

The consequence was worse than the FR's title. The blocks were not merely
uncached — `content=""` meant the **entire system prompt was discarded** on
every Anthropic call using `system_segments` or the list form of `system:`.
Silently. Since FR-276. The feature named "caching" was in fact a prompt
deleter, and the word "caching" in its name is exactly why nobody looked: a
degraded cache is a cost problem, so the failure mode everyone imagined was
expensive-but-correct.

## The second copy: a log that narrates instead of reading

The demo's `✓ Cache hit! Shared system segment reused from analyze step` is a
`print` statement. It was true of the author's intent and never of the run.
Then I measured the prefix: ~300 tokens, against Anthropic's 1024/2048-token
minimum cacheable size. The demo was below the floor at which `cache_control`
does anything **at all** — so even a fully correct implementation would have
produced zero cache hits there. The log was doubly fictional, and it had been
sitting in the repo as the feature's proof.

FR-219 closed with its own Next Steps still reading "Verify cache hits in
Anthropic usage logs (if accessible)". The AC was ticked; the verification was
not done. The parenthetical `(if accessible)` is where the rot entered: an
acceptance criterion with an escape hatch is a wish.

## What the gates caught that I did not

The hedging gate blocked my commit over `executor_base.py:382` — a docstring I
never touched. Its FB001 allowlist is keyed by `file:line`, and deleting two
lines had slid a confessed entry out from under its key. Annoying, correct, and
a small proof of the same principle: a line-keyed claim about a file is only
true until someone edits the file. The confession had to move with the code.

## Heuristic

**When a test's assertion reads a field the subject under test just wrote,
there is no seam coverage — only a mirror.** Cross the boundary in the test or
admit the boundary is untested. And when an artifact *narrates* a success
(`✓ Cache hit!`), find the number it should have printed instead; if no number
exists, the success never happened.

Corollary earned here: before trusting any cache/quota/threshold feature, check
the provider's **minimum** for it to engage. A correct implementation below the
provider's floor is indistinguishable from a broken one — and both produce a
cheerful log.

**Seed:** The FB001 allowlist is keyed by `file:line` and silently rots on
every edit above it. Which other enforcement artifacts in this repo encode a
*position* rather than an *identity* — and could a gate detect a confession
whose line no longer contains the token it confesses, instead of waiting for an
unrelated commit to trip over it?
