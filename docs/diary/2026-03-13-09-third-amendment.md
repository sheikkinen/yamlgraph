# Diary: 09 Third Amendment — Normalize at the Boundary

**Date:** 2026-03-13
**Document:** 09-full-scale-architecture.md
**Phase:** Amendment of Second Judgement issues R-1 through R-5

## Cognitive Process

The amendment was triggered by a single user word — "amend" — with a crucial
qualifier: "feature requests to both yamlgraph and statemachine_engine are
allowed." This permission changed the solution space entirely.

## Trap: Downstream Fix (avoided)

The Second Judgement proposed two options for R-1: (a) custom `send_event_to`
action returning `None`, or (b) engine FR adding `fire_and_forget` to the
built-in. Without the engine-FR permission, option (a) was the pragmatic
choice — a downstream fix for an upstream problem.

With the permission, the trap became visible: a custom action that reinvents
90% of an existing built-in is the **downstream fix** pattern. Two parameters
on the existing action (`fire_and_forget: true`, `guard: true`) eliminate the
custom action entirely, normalize the behavior at the engine boundary, and
benefit all future projects — not just this voicebot.

## Insight: The One Law in Practice

The Scripture's **One Law** — "Normalize at the boundary where external data
enters, not downstream where it manifests" — applied directly:

- **Boundary:** The engine's `SendEventAction` is where external commands
  enter the FSM event dispatch system.
- **Symptom:** Actions returning truthy values trigger unintended state
  transitions. Actions re-execute every 50ms tick.
- **Downstream fix:** Custom action wrapping the built-in.
- **Boundary fix:** Two parameters on the built-in itself.

The `guard` parameter is even more powerful at the engine level. Every
ninchat_voice action independently implements the J-1 pattern (~10 lines
each, different key prefixes, manual stale-key cleanup). A single `guard: true`
parameter on the built-in eliminates this boilerplate for all future actions.

## Trap: Working System Inertia (detected)

The Second Judgement rated R-2 as "MEDIUM — low probability, fixable in impl."
This is the **working_system_inertia** trap: "it'll probably work without the
guard, we'll fix it if it breaks." But voicebot calls are real-time — a
duplicate `speak` command means the caller hears garbled overlapping audio.
The cost of the guard (~5 lines at engine level) is negligible compared to the
debugging cost of a heisenbug that manifests only under load.

## R-5: Accepting the Trade-off

R-5 (user speech lost during long-running graphs) was the only issue requiring
a design decision rather than a technical fix. The temptation was to add
`delegating_hold` and `delegating_wait` states for full listen-during-graph
support. But that adds states, transitions, and edge cases (what happens when
user speech arrives mid-graph?) for a scenario that can be mitigated with one
line of hold audio.

The cheapest bug is the one in the spec. The cheapest feature is the one that
doesn't exist. Hold audio is the right trade-off for Phase 1.

## Heuristic

**Permission unlocks boundary fixes.** When constrained to one system, you
patch downstream. When given permission to change the boundary system, audit
which downstream patches become unnecessary. The "allowed" qualifier on FRs
is not just permission — it's an obligation to check.

## Seed

If `fire_and_forget` and `guard` become engine-level primitives, should ALL
engine actions support them? `voice_speak` and `voice_listen` currently
implement their own guards. Could they delegate to `guard: true` instead,
reducing every action to pure logic with no boilerplate?
