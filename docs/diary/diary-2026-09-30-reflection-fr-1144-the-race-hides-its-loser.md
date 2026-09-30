# Reflection: FR-1144 — the race hides its loser

**Date:** 2026-09-30
**FR:** FR-1144 (race nodes honour `thinking_budget`), live A/B test bed

## What happened

The operator asked whether any example had raced with and without thinking.
None had: FR-1144 was witnessed only by unit tests that stop at the provider
factory. We built two arms of `image-that-speaks` through the authoring
adapter and ran them live.

Three findings, each visible only from a real run:

1. **The demo's providers were dead.** The google candidate failed with
   `API_KEY_INVALID` in both arms. The first smoke exited 0 because the race
   tolerates a failed candidate: gpt-4o-mini won alone, and the "A/B" compared
   nothing. Exit 0 from a race says one candidate lived, not that the
   comparison happened.
2. **The model name was not the whole address.** `gemini-3.5-flash` is the
   `.env` default, and it returns 404 at the `.env` default location
   `europe-north1`; it answers only at `global`. Two defaults that each look
   right are wrong together.
3. **The race cannot measure what it hedges.** With vertex/azure live, azure
   won all six runs. The race node's duration is the winner's latency, so the
   arms differed only by azure noise. Gemini, the one candidate the budget
   changes, is cancelled as the loser, and its latency is recorded nowhere
   unless tracing is on.

## Trap

`winner_only_observation`: a race is a measurement instrument that discards
the losers' readings by design. Any A/B whose treatment changes a candidate
that loses measures the winner twice. The node's success, its winner and its
duration are all blind to the losing candidate.

## Heuristic

Before comparing race configurations, name which candidate the change
affects and confirm that candidate's own latency is recorded (tracing, or a
direct per-candidate probe). If it never wins, the race output says nothing
about it.

**Seed:** Should the race node log each cancelled candidate's elapsed time at
cancellation? One log line per loser would turn every production race into a
free per-provider latency sample, the evidence FR-1144's first consumer needs.
