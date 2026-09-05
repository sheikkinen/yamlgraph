# The Edge That Had Already Gone

**Date:** 2026-09-05
**FR:** FR-998 Anthropic structured output must be constrained, not requested
**Session:** enforcement, Windows host; judgement and plan came from PR #596

## What happened

The plan was precise about its edge. Constrained decoding needs Sonnet 4.5 or
Opus 4.1; the graph inventory still names `claude-sonnet-4-20250514` seven
times and `claude-3-haiku-20240307` once; those two "are expected to return an
API error for `output_config`; the fix must fall back to today's behaviour
for them, on the provider's typed error, not a substring." The judgement
froze a four-condition predicate around that error and demanded sync and
async witnesses for it. I built the predicate, the second attempt, the log
line, and thirteen propagation cases before I asked the API a question.

Then I asked. Both edge models answer `404 not_found_error: model:
claude-sonnet-4-20250514`. They are not models that reject `output_config`.
They are not models. Every Anthropic model the API still serves accepts
constrained decoding. The typed 400 the whole second-attempt path exists for
has no live witness and, today, cannot have one; it is exercised only by
errors I construct in tests.

The design is still right — a model family that ships without the capability
will appear again, and the predicate is narrow enough to do no harm until
then. But the FR reasoned from a graph inventory (what our YAML files *name*)
as if it were a population (what the provider *serves*). Seven files naming a
retired model is a different defect from a model rejecting a parameter, and
the plan spent its edge-case budget on the second while the first sat in
`grep` output.

## The trap

Designing against an enumerated edge without first checking that the edge
still exists. The inventory was real, the reasoning was sound, and the
premise had expired. It is a cousin of `false_duplicate`: syntactic presence
(a model string in a YAML file) taken for semantic presence (a live model
with a known capability gap). The cure cost one API call and thirty seconds;
it should have been the first thing enforcement did, before the RED commit,
because it changes what the RED commit can honestly claim to condemn.

## Two smaller ones

**Line-keyed confessions.** The hedging allowlist and `docs/confessions.md`
key each confessed `fallback` token by `file:line`. Adding one import to
`agent.py` moved two confessions; adding one to `executor_base.py` moved a
third. The check caught it, which is the point, but a confession that dies
whenever anyone adds a line above it is a confession keyed on the wrong
thing. Content-hash the line, or key on the enclosing symbol.

**The 450-line wall at the boundary.** The judgement placed the two Anthropic
predicates in `llm_providers.py`, "whose provider constructors already use
lazy imports". That file was at exactly 450 lines, the size gate's ceiling.
I put them in a sibling module, ticked AC-04 anyway, and wrote it up as a
deviation. The review refused it: a deviation recorded by the deviator is
drift, not authority. The honest move was one step further — extract the
request-bound helpers that had nothing to do with providers, and put the
predicates where the plan said. Judges read code; they do not run `wc -l`.
A plan that names a file should name its line count, and an enforcer who
hits the ceiling should make room, not move the goalpost.

## Heuristic

Before building a path for a class of peer — a model, a provider, a client
version — ask the live system whether the class still has members. An
inventory of names in our own files is a floor on what we *reference*, never
evidence of what *exists*. One call; before RED.

**Seed:** The second-attempt path is now code with no reachable trigger in
production. Purge says: not required and not tested against a real peer, it
should not exist. Preserve says: the next model family to ship without the
capability will need it on day one, and the predicate is narrow. Which
doctrine wins when the witness is *constructed* but the design is *correct* —
and is there a lint that would tell us, months from now, that the path is
still unreachable?
