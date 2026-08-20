# The Cure That Planted the Next Defect (VR-005)

**Date:** 2026-08-20
**Arc:** voice_runtime VR-005 — judge → fold → RED dd760a6 → GREEN 051d03c → release 0.1.13 (PyPI live), one session.

## The lineage nobody audited

NC-340 (June) cured permanent STT deafness by adding `_ensure_feed_task()` to
the tail of `_connect()` — every reconnect path now guaranteed a live feeder.
Correct, tested, shipped. But `start()` also calls `_connect()`, and `start()`
kept its own `create_task` from the pre-NC-340 world. The cure's guarantee
("a feeder exists after _connect") composed with the old code's assumption
("no feeder exists until I create one") into a double-create. Two feeders
raced one queue for two months as "the intermittent lost first utterance."

The trap is a specialization of `composition_bug`: **a fix that strengthens a
callee's postcondition silently invalidates callers written against the weaker
one.** NC-340's tests all exercised reconnect paths; none re-examined the
initial-start path whose contract had just changed underneath it. When a fix
adds a side effect to a shared internal (`_connect`), every caller must be
re-read as if new — the diff view shows the callee changing, never the
callers rotting.

## Designing the fake to remove mercy

csap-black FR-005 had already refuted "cancel-without-await" as the crash
cause because `await self._stt.close()` *happened* to yield the loop cycle
that delivered the cancellation. Safe by accident. To condemn D-C anyway, the
RED fake's `close()` was written with **zero suspension points** — an async
def that returns synchronously — so no incidental yield could deliver the
cancellation and mask the missing await. The general move: to witness a
missing await, strip every incidental yield from the test doubles; mercy in
the fixture is a false negative in the witness. This is the dual of the
FR-005 reproducer's failure (a no-op `_connect` stub too UNfaithful to spawn
the duplicate): fidelity in what the double *does*, austerity in when it
*yields*.

## The judge caught the FR contradicting itself

R-1 was the valuable revision: the FR's Problem section listed SDK
message-handler tasks as unowned orphans while its Out-of-scope section
forbade touching SDK internals. Both true, jointly unimplementable. The
author (me, in the prior session's framing) couldn't see it because each
sentence was locally correct. Input-closure judging — FR + source only, no
chat narrative — is what surfaced it: the judge read the document as a
contract and found the clause conflict. A prompt-as-subagent-contract lesson
applied to FRs: the enforcer cannot push back, so clause consistency is the
judge's job, not the enforcer's discovery.

## Friction observed (guard, not doctrine)

`pre-command-guard.sh` denied two innocent commands: `ls tests/ | head` (the
word "pytest" appeared elsewhere in the compound command) and a commit whose
*message text* contained "SKIP=pytest" alongside a `git diff --stat | head`.
Substring conjunction over the whole command line, blind to pipeline
structure. Cost: two reworded retries. The reasoning sentinel also fired
one-shot on "pre-existing failure" — correctly per doctrine letter, though
the stash-and-rerun attribution it demanded had already been done; the
phrase, not the practice, tripped it.

**Seed:** When a guard matches substrings across an entire compound command
(message text included), its false-positive rate grows with command
complexity — should PreToolUse guards parse the pipeline AST (which program
receives the pipe?) instead of grepping the line, and should the reasoning
sentinel accept a citation of performed evidence (stash-rerun log) as
discharge instead of firing on phrase alone?
