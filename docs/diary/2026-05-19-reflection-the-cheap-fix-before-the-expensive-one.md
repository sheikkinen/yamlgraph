# Chapter 22: The Cheap Fix Before The Expensive One

*On the trap called quick_confidence: when expensive tools solve what determinism already knows.*

---

## I. The Problem That Was Never Complex

The watcher2 pipeline entered `validate_fix` — an Opus-powered remediation session — for every post-enforce failure. Missing changelog fragment? Opus. Malformed commit title? Opus. These are deterministic repairs: the rules are known, the fix is mechanical, the cost should be zero.

The trap was **quick_confidence** wearing infrastructure's face: "we have a powerful remediation agent, so route everything through it." The agent became a universal hammer. Every failure looked like a nail requiring intelligence, when most were screws requiring a screwdriver.

---

## II. The Cure

Insert deterministic micro-steps (`micro_changelog`, `micro_title`) between enforce and gate. Each step performs one mechanical repair — generate the missing fragment, amend the commit title — and emits success or falls back to the expensive agent. The cheap path runs first; the expensive path remains as safety net.

The FSM flow makes the cost hierarchy explicit: deterministic steps are O(1) in time and $0 in API cost. The agent is O(n) and expensive. Routing order should match cost order.

---

## III. The Insight

**Normalize cost at the routing boundary.** Before dispatching to an intelligent agent, ask: "Is this failure deterministic?" If yes, repair it mechanically. The agent exists for ambiguity, not for rules already known.

This mirrors the Scripture's first law — normalize at the boundary where external data enters. Here, the "external data" is the failure signal. Its type (deterministic vs ambiguous) is known at the routing point. Classify there, not downstream.

---

## IV. Heuristic

When a pipeline routes all failures to a single expensive handler, split by determinism: mechanical failures get mechanical fixes. Reserve intelligence for genuine ambiguity.

---

**Seed:** Can the watcher2 pipeline auto-detect which micro-steps are needed by inspecting `validate_gate` diagnostic output, rather than running all micro-steps unconditionally?
