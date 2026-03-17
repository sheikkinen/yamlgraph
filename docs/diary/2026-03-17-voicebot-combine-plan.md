# Diary: Combined Voice Runtime — From Reckoning to Composition

**Date:** 2026-03-17

## Context

Two voicebot projects in the same monorepo: `ninchat_voice` (deployed, 1 FSM,
15 states, production on Fly.io) and `voicebot-fsm` (204 tests, 2-FSM
architecture that proved to be a `framework_costume` trap). The critical
crosscheck revealed voicebot-fsm's FSMs are message relays — the Python server
is the real controller. ninchat_voice's single coordinator pattern works.

## Cognitive Process

**Trap encountered: `working_system_inertia`** — The original plan (plan-forward
v1) recommended "fork ninchat_voice, surgically remove Ninchat coupling, replace
with questionnaire." This was the correct analysis of what's wrong (2 FSMs bad,
1 FSM good) but the wrong cure: mutilating a working production system.

**Cure applied: `callsite_fix`** — The user's revision was precise:
"copy ninchat_voice as-is but add the probe_recap from voicebot." This is the
callsite fix — don't change the working system, extend it at the specific point
where new behavior is needed.

**Design insight: Sequential phase composition.** The combined FSM adds 4 states
to a 15-state config. The probe_recap phase sits between greeting and Ninchat
dialogue. The Ninchat flow is completely untouched. This proves FSM configs
support phase composition without architectural changes — just new states and
transitions spliced into the existing flow.

**Subtlety spotted: `parse_targets` reinitialization.** The probe_recap graph's
`parse_targets` node resets `extracted` to `dict.fromkeys(field_ids)` (all None)
on every invocation. With LangGraph checkpointing, this could destroy accumulated
answers across turns. This is logged as an open question — verify before live test.

## Heuristic

**Phase composition over flow replacement.** When adding capability to a working
FSM, insert a bounded loop (new states) at the junction point and preserve the
existing flow downstream. The FSM config is the composition boundary — not the
execution engine, not the services, not the graph.

## Seed

If the FSM config is the composition spec — "phases: [greeting, probe_recap,
ninchat_dialogue, goodbye]" — should there be a meta-config that compiles
phase definitions into a coordinator YAML? Each phase would be a reusable
template: a set of states, transitions, events, and actions with defined
entry/exit contracts. The compiler stitches them together.
