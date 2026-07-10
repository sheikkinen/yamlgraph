# The Field Corrected the Judge Within the Hour (FR-709)

**Date:** 2026-07-10
**Context:** FR-709 enforce — the first live-transport witness of the NC-361 arc; passed, with the judgement's own fixture corrected by reality.

## What happened

The judgement's F2 pinned `LLM_REQUEST_TIMEOUT=5` for the test. Google's
API rejected it: `400: "Manually set deadline 5s is too short. Minimum
allowed deadline is 10s."` A provider-side floor on client deadlines —
a fact that exists in no SDK docstring we read, no mock we wrote, and no
judgement finding. One real request surfaced it. (Also: the draft's model
id `claude-3-5-haiku-latest` 404'd — ids rot; the repo's own usage census
is the reliable source, 83 hits for `claude-haiku-4-5`.)

This is `mock_escape_hatch` completing its own argument: the FR existed
because mocks can't exercise real transports, and its very first run
against a real transport invalidated a judged constant. The Judge verified
the fixture against OUR stack's layers (F2 was a genuine catch — client
timeout vs drain grace); it could not verify it against the provider's
unpublished contract. Field floors beat frozen constants.

## The verdict data

Three races, all `winner=anthropic loser=google` (bias held), verdicts
0.74/1.22/1.95 s, zero abandon-WARNINGs, threads to baseline after every
race, zero net growth. Two conclusions:

1. **The teardown contract holds on live transport** — cancelled gemini
   tasks acknowledged cancellation within CLEANUP_GRACE; the abandon path
   stayed cold, as designed for healthy endpoints.
2. **First rate-layer datapoint**: no accumulation over repeated races
   post-707/708. The `bounded_is_not_small` question from this morning's
   reflection has its first answer: locally, the rate is fine. FR-710
   remains gated on the Fly probe (the deployed environment is where the
   original accumulation lived).

## Heuristic

A judged constant that crosses an external boundary (provider API, OS,
SDK) is a hypothesis until one real request confirms it. For any FR whose
fixtures encode provider-facing values, the first enforce step should be
the cheapest possible live probe of those values — before building the
test around them. Corollary for consumers: FR-708's `LLM_REQUEST_TIMEOUT`
has a provider-dependent floor (google: 10 s); document floors where the
knob is documented, or the knob invites a loud-but-confusing 400.

**Seed:** should FR-708's `_request_timeout()` validate against known
provider floors (google ≥ 10) and raise with a floor-naming message at
construction instead of a 400 at request time — normalize the provider's
constraint at our boundary?
