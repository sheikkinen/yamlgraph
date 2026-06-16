# The Chapter That Would Not End

*Diary — 2026-06-16 — FR-501, DM v2 play-loop runaway*

## What happened

A live Floodmark regeneration on the `inception`/`mercury` provider died with the
book gate still shut: `chapters played: [('1', True), ('2', False), …]`. Chapter 1
closed; chapter 2 ran **91 turns** and never did, starving chapters 3–5 of the
shared turn budget. The director's `phase` told the whole story: chapter 1 climbed
opening → rising → climax → resolved in six turns; chapter 2 logged one `opening`
and then **ninety** `rising` turns. It never escalated, so `scene_complete` never
fired, and the play loop — whose only chapter exit is `scene_complete` — kept
asking for one more turn until the book-level `turn_cap` ran out.

## The trap: blaming the provider for exposing the defect

The seductive conclusion was "mercury is too weak; use vertex." That is
`working_system_inertia` wearing a provider label. Vertex had *worked* — but
working is not the same as *bounded*. Vertex happened to resolve chapters quickly,
which hid a loop that delegates termination entirely to the model's judgement with
no deterministic floor. Mercury didn't introduce the runaway; it **revealed** one
that was always reachable. Any provider, on an unlucky chapter, could hang the same
way. The question was never "which model resolves?" but "what closes the chapter
when the model won't?" — and the honest answer was *nothing did*.

## The boundary: the loop must bound the chapter

`the_one_law` again: normalize at the boundary where the untrusted thing enters.
The director's `scene_complete` is an LLM judgement — an external, unreliable
signal — and the play loop consumed it as if it were a guaranteed eventual `True`.
The fix is a deterministic backstop at the loop boundary: a per-chapter turn budget
(`CHAPTER_TURN_CAP = 16`) that force-closes a chapter once it plays its full
allowance without resolving. The two gate sites that branched on
`scene_complete` — `navigation.accept_target` (where to land next) and
`session.accept` (whether to close the chapter) — now share one predicate,
`chapter_should_close(doc, cid, n)`, so the policy lives in exactly one place
instead of being duplicated and drifting. The cap is generous — ≈2.7× the six-turn
natural length — so a well-behaved director still closes on its own signal; the
budget only catches a runaway.

## Why it was cheap to fix and cheap to prove

`apply_chapter_close` already tolerated a non-`scene_complete` chapter: its
`climax_turn` falls back to the last played turn when no turn ever reached climax.
So forcing the close needed no new close path — only a new *reason* to close. And
the whole thing is pure: five dict-in/bool-out tests pin the predicate's truth
table and the navigation force-close, no TestClient, no LLM, no filesystem. The
runaway that cost 91 live turns to discover is now condemned by a 0.07-second test.

## Heuristic

When a loop's only exit is an LLM's "I'm done" signal, the loop is unbounded by
construction — the model's judgement is an external input, not a termination proof.
Put a deterministic budget at the loop boundary so the loop closes itself when the
signal never comes. A working provider that happens to terminate is not a bounded
loop; it is a runaway waiting for an unlucky input.

**Seed:** The cap force-closes a chapter, but the *content* of a chapter that ran
90 turns past its arc is still 90 turns of un-resolved drift. Should a force-close
also mark the chapter as degraded — a quality flag the book_reviewer reads — so
"the loop terminated" is not silently confused with "the chapter ended well"? What
is the cheapest signal that distinguishes a natural close from a budget cap?
