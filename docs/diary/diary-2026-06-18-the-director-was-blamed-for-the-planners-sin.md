# The Director Was Blamed for the Planner's Sin

**FR-523 — DM v2 state-aware chapter re-outline**

## What happened

A reviewer scored chapter 3 of the Floodmark book Continuity 1/5: Arnulf, left
"safe on the higher bank" at the close of chapter 2, was "swept away by the flood"
in chapter 3 with no transition. The reflex diagnosis — and the whole FR-519/520/521
arc before it — read this as the play layer failing: a character acting where the
carried state forbids, curable by *option removal* (roster-drop, forward-fed
continuity warnings to the director).

I built a deterministic witness (`seam_precondition_gap`) and a fixture to condemn
the bug before touching a fix. The witness fired exactly on the seam — but tracing
it backward through `story.json` showed the death itself was *planned* (the synopsis
genuinely loses Arnulf to the flood and returns him changed). The contradiction was
not the actor acting wrongly; it was that the **beat demanded a position the carried
state forbade, with nothing in between.** And the beat was written by
`outline_chapters` — which receives only the synopsis, outlines all chapters up
front, and never sees a single line of committed `world_state`. The planner authored
an impossible instruction; the generator teleported the actor to obey it; the
director was blamed at play time for a defect that entered three layers upstream at
planning time.

## The trap

**`downstream_fix` wearing the costume of a known cure.** The previous three FRs in
this arc all cured *unplanned re-animation* by removing options. This bug is the
exact inverse — a *planned transition that is physically discontinuous* — and it
looks identical from the play layer (an actor in an impossible place). Pattern-match
on the symptom and you reach for option removal again, which here would delete an
intended arc beat. The two failures share a surface ("raising the dead") and have
opposite cures: one *removes* an option, the other *adds* a bridge.

## The insight

The cheapest place to kill the contradiction is the boundary where it is authored,
not where it manifests. `outline_chapters` is state-blind by construction, so every
beat it writes is a hypothesis about a world it cannot see. The fix feeds the prior
chapter's committed `world_state`/`seam_packet` back into a *re-outline* of the next
unplayed chapter, so the planner authors the bridging reposition beat the death
requires. The up-front outline becomes a draft; the just-in-time re-outline is
authoritative. This is `the_one_law` applied to *planning*: normalize at the seam
where data enters the spec, not downstream in the director or the prose.

The deeper structural read: **memory flows forward (the ledger carries state into the
next chapter) but intent flows backward (the synopsis pre-commits every chapter's
events).** When the two are derived independently, they drift, and the drift surfaces
as a continuity break. The cure is to make the backward-flowing intent *see* the
forward-flowing memory at the moment it is finalized — to close the loop the
state-blind outliner left open.

## The method that paid off

Condemn before fix. The witness + fixture (committed RED, f368a770) made the
hypothesis falsifiable and turned the live `10023-BC` artifact into corroborating
evidence rather than the gate. When the GREEN test arrived it needed a *negative
control* — a re-outline returning beats without a bridge must leave the gap — because
without it the assertion could pass on plumbing alone. The witness that proves the
bug is also the witness that proves the fix; the negative control proves the witness.

**Seed:** Memory forward, intent backward — where else in the system does a
backward-derived plan ignore forward-carried state? The synopsis itself is authored
once from the draft and never re-consulted against what actually played. Should the
*synopsis* re-weave from the played chapters' committed memory the way the chapter
beats now do — a second loop closed one level up?
