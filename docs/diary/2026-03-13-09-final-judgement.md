# Diary: 09 Final Judgement — The Cure Introduced the Disease

**Date:** 2026-03-13
**Document:** 09-full-scale-architecture.md
**Phase:** Final Judgement (4th verification pass)

## Cognitive Process

Three verification passes found and fixed 12 issues. The fourth pass found
that the third pass's amendment (R-5 hold audio) introduced a blocking defect
worse than the original problem it solved.

## Trap: Symptom Patch (R-5 amendment)

The R-5 observation was: "User hears silence for 6-18s during Ninchat relay."
The amendment's cure: add hold audio ("Odota hetki...") to `delegating_turn`.

The cure assumed Telephony could accept a new `speak` while already speaking.
This assumption was never verified against the engine. The Telephony FSM has
no `from: speaking, event: speak` transition. Any `speak` arriving during
speech is silently dropped (engine DEBUG log only).

For the Ninchat relay (6-18s): no problem — hold audio finishes (~2s) before
the graph completes. Telephony is idle when the response arrives.

For questionnaire turns (<1s): **catastrophic** — graph completes DURING hold
audio, response speak is dropped, Orchestrator desyncs (thinks response was
spoken because it receives speech_complete from the hold audio).

The R-5 amendment solved the slow-graph case but broke the fast-graph case —
which is the PRIMARY use case for Phase 1.

## The One Law (violated)

The amendment added hold audio at `delegating_turn` (downstream) instead of
asking: "Does the Telephony FSM support speak-during-speak?" (boundary check).
The correct normalization point is the Telephony FSM's transition table —
if it doesn't support the operation, adding the operation upstream is a bug,
not a feature.

## Insight: Self-transition guard persistence

Engine verification revealed that J-1 guards persist on self-transitions.
Guard key `_event_sent_{state}` is not cleared when the state self-loops
because the stale-key cleanup only removes guards from OTHER states. This
means even adding `from: speaking, to: speaking, event: speak` wouldn't fix
the problem — the voice_speak action's guard would prevent re-execution.

A proper fix requires either per-action guard keys or guard-clearing on
self-transition — both engine changes beyond the current FRs.

## Trap: Quick Confidence (the amendment comment)

The amendment's YAML comment stated: "Short graphs complete before hold
finishes playing — the next speak overwrites it. No harm." This was written
with quick confidence and never mechanically verified. The comment is false:
there is no overwrite mechanism. The event is dropped.

The Scripture's cure: "When I feel certain, let that be the sign to Judge."
The amendment was judged — and the false assumption was caught.

## Heuristic

**Every cure must be simulated against the same engine it targets.** An
amendment that adds a new action to a state must verify that all downstream
FSMs can receive the events that action produces, in all timing scenarios
(fast and slow). A 2s hold audio means there's a 2s window where the
Telephony FSM is in `speaking` and cannot accept new `speak` events. Any
graph completing within that window hits the race.

## Seed

The engine's fire-and-forget pattern (action returns None, no process_event)
combined with the 50ms polling loop creates a class of timing issues that
only manifest under specific graph execution speeds. Should the engine
support an "event queue" for events arriving during action execution, rather
than the current drop-on-no-match behavior? Or is the simplicity of
drop-on-no-match the right design, with FSM configs responsible for handling
all reachable (from, event) pairs?
