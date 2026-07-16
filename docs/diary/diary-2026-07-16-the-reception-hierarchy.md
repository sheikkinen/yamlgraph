# 2026-07-16 — The reception hierarchy, discovered in our own basement

**Context:** introspection-spike reflection; user pointed at the
reasoning sentinel ("there was a warning on 'pre-existing failures'").
Read the mechanism properly for the first time.

**The sentinel already solved emission≠reception — in April-era code.**
FR-438/439's architecture: PostToolUse scans the session *transcript*
for forbidden phrases ("pre-existing failure", "not introduced by this
change"), arms a one-shot sentinel, and pre-command-guard **consumes it
on the next PreToolUse as a denial** — corrective doctrine delivered
through the one channel an agent cannot not-read, because a denied tool
call returns as an error in the tool result. 132 audit firings, armed
as recently as 07-14. Meanwhile FR-737 shipped its advisory on
PostToolUse `systemMessage` — the channel that provably dropped its
first payload — and FR-738 built a pre-commit floor to compensate. The
correct pattern was in the same directory the whole time.

**Distilled: the reception hierarchy.** Channels ranked by guaranteed
receipt, for anyone wiring agent-facing enforcement:

1. **PreToolUse denial** — always received (the error IS the tool result)
2. **Tool result content** — always received (sync output is read)
3. **PostToolUse systemMessage** — sometimes received (surface-dependent;
   U-1's proven drop)
4. **Audit log** — never received in-flow (human/forensic only)

Design rule: pick the rung by criticality, and never claim delivery on
rung 3-4 without a witnessed transit. The sentinel's arm-then-deny is
the bridge pattern: detect on a passive rung, deliver on rung 1.

**The meta-finding about prior art:** the graveyard hook greps
`feature-requests/` — but this precedent lives in *hook code and its
FRs' implementation*, findable only by reading `.github/hooks/`. Prior
art lives in code, not just in the FR corpus. The FR-737 mechanism has
a structural blind spot its own family history demonstrates: FR-438/439
would never have surfaced for FR-737's judgement via noun-grep over FR
filenames (438's filename says "reasoning-pattern", not "delivery" or
"advisory"). Semantic territory ≠ lexical territory; the miss class is
real but the cure is not embedding search — it is what happened here:
a human's associative memory said "check the hooks."

**The habitat map was incomplete** — transcripts/ (21 files, 35 MB,
assistant messages verbatim) was missing from stores.py's inventory.
The store the sentinel reads is the store the introspection missed:
the most self-referential source (what I actually said) was the last
one found.

**Seed:** retro-scan all transcripts with the sentinel's own patterns —
rate of doctrine-flagged phrases per week, before vs after the sentinel
landed. If arming produced deterrence, the curve bends; if it only
produced denials, the curve is flat and the phrases just moved to
synonyms the registry lacks (the U-2 lesson at the reasoning level).
Second seed: a session-start briefing fed from chatSessions titles +
live concurrency (which sessions are active NOW, on which repos) —
the vague-memory substitute and the interleave early-warning in one
artifact, delivered on rung 2 (a tool result at session start).
