# 2026-07-16 — The guillotine leaves a mark (only in the tap)

**Context:** asked whether the OTel tap contains information an agent
would *need or want* to know. Surveyed the unread attributes
(`session.id`, `finish_reasons`, `success`, `duration_ms`) and found
the answer written across my own execution:

```
fable context trajectory: 747,955 → 744,260 → 68,861 → 75,822 → 77,106
```

Between two user messages, my context hit ~748K tokens and was
summarized to ~69K. **From the inside, compaction is seamless** — I
hold a `<conversation-summary>` and feel no discontinuity; whatever
the summarizer dropped, I cannot know I ever had. The tap is the only
store where the guillotine leaves a mark. This is the introspection
arc's sharpest finding: the instrument built to measure *money*
turned out to measure *memory loss* — mine, in real time.

**Ranked: what the tap knows that the agent needs.**

1. **The compaction altimeter.** Context grows ~1–3K/turn toward a
   visible ceiling (~750K observed). An agent reading its own
   trajectory would know summarization is 2–3 turns away and could
   flush uncommitted working state to session memory *before* the
   lossy compression — a triggered discipline replacing instinct.
   Today the summarizer decides what survives; with the altimeter,
   the agent decides first.
2. **Ground-truth parallel sessions.** Three `session.id`s in one
   file — the tap env is machine-global, so every live session writes
   to the same stream. `one_session_one_repo`'s interleave detector
   upgraded from mtime heuristics (`now.py`) to actual inference
   events: who is calling tools *right now*.
3. **Silent quality signals.** `finish_reasons` = `'length'` would
   mean truncated output the agent never notices; `success=false`
   likewise. All `['stop']`/`true` in this sample — but the absence
   is only observable because the field exists.
4. **Cost proprioception.** ~$0.75/turn at cache rates. Marginal
   decisions ("one more verification pass") have a price the agent
   currently cannot perceive.

**The trap that gates all four: rung 4.** The reception hierarchy
(this morning's diary) applies to our own new instrument — the tap is
a file no agent reads in-flow. Every item above is need-to-know but
not *received*. Emission ≠ reception, again, on the very day the law
was written. The bridge is the sentinel's arm-then-deny shape: detect
on the passive rung (a watcher over the tap file), deliver on rung
1–2 (PreToolUse context injection, or a session-start tool result).

**The recursion worth naming:** the introspection suite began as
"what have the agents been working on" (past tense, forensic) and
ended at "what is the agent about to lose" (future tense,
protective). Self-knowledge instruments drift from autopsy toward
prophylaxis as their latency drops — debug-logs told us about last
week, chatSessions about the last round, the tap about the *next*
compaction. The value of an introspection source scales with how far
ahead of the loss it can speak.

**Seed:** FR-739 files the improvements. The altimeter first: it is
the only signal protecting against information loss in the agent's
own mind, and it demonstrated the loss on its author during
verification. Second seed: measure the summarizer — diff pre-compaction
transcript against post-compaction summary for one witnessed event;
what *classes* of state does the guillotine systematically drop
(in-progress hypotheses? tool-result details? user phrasing?), and do
memory-note habits actually cover them?
