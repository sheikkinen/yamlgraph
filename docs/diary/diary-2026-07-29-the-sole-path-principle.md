# The Sole Path Principle

**Date:** 2026-07-29
**Context:** FR-765 round 2 shipped the third sole-route execution
surface (judge-fr → review-pr → graph-authoring), and the first
end-to-end smoke of `scripts/author.sh` ran the same day.

## What the principle actually buys

The Scripture says "one judge to rule them all" and forbids the prompt
adapter and sister-session routes. Today made the mechanism visible:
**a sole path is a deliberately constructed boundary — the one door
through which execution enters, built so there is a place to attach
enforcement.** The One Law says normalize at the boundary where
external data enters; the sole path is what you build when no natural
boundary exists yet. Lock, lineage sentinel, executor resolution, and
the artifact contract all live in the wrapper because the wrapper is
the only place execution is guaranteed to pass through. You cannot
gate what you cannot route.

Three corollaries surfaced during the smoke:

1. **One route makes one witness sufficient.** The commit_lint smoke
   proved the *entire* authoring route, because there is exactly one.
   With N permitted routes, a passing smoke witnesses 1/N and the
   drift hides in the other N−1. Sole path is what converts a demo
   from anecdote into coverage.

2. **The re-entry exception is not a loophole — it is the
   termination condition.** "To author, invoke the author route" told
   to the agent already inside the route is infinite regress. Sole
   path plus recursion guard is how a self-referential rule grounds
   out: everyone outside uses the door; whoever is inside IS the
   execution. The morning's R-1 lesson composes here: the guard must
   ban re-entering the door, not practicing the profession.

3. **Sole path without artifact proof is still trust.** The route
   guarantees where execution happens, not that it happened well. The
   wrapper's substance checks (five headings, an existing listed
   path) are the other half of the pair. Round 1 of FR-765 was
   doctrine an agent *may* follow; round 2 is a door that *emits
   evidence* when passed through. The principle's real product is
   witnessability, not restriction.

## The honest counterpoint

A sole path is a single point of failure with the same break-glass
economics as branch protection: when the route is down, the pressure
to "just do it manually this once" is exactly the drift the route
exists to prevent. The judge doctrine already handles this the right
way — the bypass must be rarer than the defect, and documented.

## Graduation pressure

Three routes now share the same skeleton: wrapper (lock + sentinel +
executor resolution + artifact contract) → thin adapter graph → copilot
node → doctrine pointer. Per the Scripture's own graduation rule, the
third recurrence is Scripture material: the pattern deserves a name —
*sole_route_with_artifact_proof* — before a fourth hand-copied wrapper
appears. Three near-identical bash wrappers is also the
`regex_fourth_exclusion` shape one strike early: the variance between
them is a small manifest (graph path, artifact path, required
headings, sentinel var, timeout), and everything else is duplicated
mechanism.

**Seed:** Should the route skeleton be data, not code — a
`route-manifest.yaml` per skill (graph, artifact, headings, sentinel,
timeout) consumed by one generic `scripts/route.sh`? And if routes
become data, can the FR-756-style gates then check *route coverage*
mechanically: every doctrine file must name exactly one manifest, every
manifest exactly one artifact contract?
