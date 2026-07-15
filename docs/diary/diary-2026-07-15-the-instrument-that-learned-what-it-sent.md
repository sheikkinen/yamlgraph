# 2026-07-15 — The instrument that had to learn what it sent

**Context:** FR-736 enforce: trace capture for the WebLLM spike page —
the third instrument FR in two days for a protocol that has executed
exactly one real run.

**The core insight arrived via a user's five words.** "We would need to
see more. i.e. outgoing prompt" — and the whole flood investigation
re-read itself: I had diagnosed the missing JSON directive by reading
*compiler source*, not evidence, because the evidence never contained
the request. `read_raw_output_first` has a dual I had not named:
**record_raw_input_first**. The artifact that ends an investigation
must carry the stimulus, not only the response. A trace is just the
pair. LangSmith knows this; our zero-key page had to learn it locally
— and the product decision to stay standalone (LangSmith purged, even
the local uploader killed) made the lesson cleaner: observability is a
property of the artifact, not a service subscription.

**The judgement's best move was making a ruling buy its own witness.**
The no-restart ruling ("trace capture is semantics-neutral") could have
been a free assertion. Instead F1 priced it: the evidence header must
print the system prompt *from the same object the request uses*, so any
tally run self-proves it ran the amended artifact. A ruling that grants
convenience should attach the mechanism that would catch its own error.

**Recurrence, third strike in this arc:** the instrument-improvement
loop is seductive — each FR was genuinely justified by a real defect in
the previous session's evidence, and yet the protocol the instrument
serves has still not run. The judgement's freeze ("no further
instrument FRs before the tally") is `audit_as_ritual` applied
prophylactically: a tool improved three times without being used is a
ritual forming. Named in the FR so the freeze survives me.

**Seed:** the trace object is one `graph export --overlay` away from
being replayable — same shape as a route.jsonl line, one level down
(message-level instead of edge-level). If the skill-export rung ever
funds a WebLLM runtime, the trace format defined here becomes its
regression fixture format for free. Was that worth designing for
explicitly, or is it the speculative-extensibility trap wearing the
foresight costume?
