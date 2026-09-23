# The knob that was never wired

**Date:** 2026-09-23
**FR:** FR-1056 — DeepSeek non-thinking mode

## The trap: a setting that validates, dispatches, caches — and evaporates

`thinking_budget: 0` on a DeepSeek node passed the Pydantic validator, was
resolved through node-over-defaults precedence, was folded into the LLM cache
key, and was handed to `dispatch_provider` — which then dropped it on the floor,
because `deepseek` was not in `_THINKING_PROVIDERS`. Four layers of machinery
handled the value correctly and the fifth silently discarded it.

This is `plausible_wrong_answer` in configuration form. A crash would have been
kinder: the author sees a field named exactly what they want, sees it accepted,
and gets billed for high-effort reasoning on every call forever. Nothing in the
system is wrong enough to notice. The linter even abstains — W071-2 fires only
for `thinking_budget > 0`, so zero passes quietly through the one check that
exists to catch provider mismatches.

The generalisable shape: **a dispatch allowlist is a silent filter.** Adding a
provider to the registry (FR-680) makes it constructible, but the thinking
knob's reachability is governed by a *second*, narrower set on the same line of
code. Every capability gated by a set membership test has a failure mode where
the capability is configured and the membership is absent, and that failure mode
is mute by construction. The cure is not more validation upstream — it is a test
that asserts the **request payload**, i.e. the last observable artifact before
the wire.

## The near-miss: two registries that look like a duplicate

`llm_factory.THINKING_PROVIDERS` and `llm_providers._THINKING_PROVIDERS` hold
the same three strings and have nearly the same name. Every instinct says
deduplicate. Doing so would have been a defect: DeepSeek belongs in exactly one
of them. It can be told to *stop* thinking, so it must be in the dispatch set;
it has no token budget at all, so it must stay out of the factory set where a
`>= 1024` request is rejected. `false_duplicate` — syntactic similarity is not
semantic equivalence — and the asymmetry only became visible because the
provider's actual API was read rather than assumed.

## The method that worked: read the vendor, then execute the SDK

Two probes, each about one command, settled what would otherwise have been
paragraphs of plausible reasoning:

1. The vendor docs: DeepSeek enables thinking **by default** at `high` effort,
   offers `none/low/high/max` and no token budget, and lists exactly two model
   names — neither of which is the `deepseek-chat` this repo still defaults to.
2. The installed SDK: `ChatOpenAI(reasoning_effort="none")._get_request_payload`
   emits the key verbatim. No `extra_body` workaround, no responses-API rewrite.

Probe 2 killed an entire alternative (A3) that a design discussion would have
argued about at length. `read_raw_output_first` applies to SDKs, not only to LLM
stages: the payload dict is the raw output of the construction boundary.

## Heuristic

> When a config value crosses a dispatch allowlist, the acceptance test must
> assert the outbound request, not the accepted input. Validation proves the
> value was *allowed*; only the payload proves it was *sent*.

**Seed:** every provider factory here takes `**kwargs` and every dispatch site
filters by set membership — so how many other node settings are accepted,
cached, and silently dropped for some provider? A generated matrix of
(setting × provider) → does it appear in the payload? would answer it once, and
turn a class of mute failures into a table anyone can read.
