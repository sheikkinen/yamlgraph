# Reflection: The Invisible Mutable State — Plan→Enforce Boundary Gap

**Date:** 2026-05-16
**Trigger:** During FR-393 planning, `exit_plan_mode` returned "interactive mode" and the next ambiguous user message ("add a shell helper starting the analysis like we did") was interpreted as "start implementing." A `mkdir -p` was executed before the user had granted enforce authority. The user had to explicitly delete the premature directory and point out the violation.

## What Happened

1. Plan created for FR-393 (prompt theme analyzer)
2. `exit_plan_mode` called → user approved the plan → tool returned "interactive mode"
3. User sent ambiguous message about a shell helper
4. I ran `mkdir -p` and set `create-graph` to `in_progress` — premature enforcement
5. User clarified they meant "add to plan" not "start building"
6. Directory deleted, status reverted

## The Trap: `plan_enforce_boundary_missing`

The Scripture defines a clear sequence: Plan → Judge → Enforce. But the tooling provides no mechanical gate between plan approval and first filesystem change. `exit_plan_mode` transitions to "interactive mode" — a state that is ambiguous between "accept more planning input" and "begin implementation."

This is **not** `intent_drift` (though it wears that costume). Intent drift is "plan says X, code does Y." Here, the plan was correct — the violation was *when* enforcement began, not *what* was enforced. The missing primitive is an explicit enforce gate.

## The Deeper Problem: Invisible Mutable State

The user identified the real issue: this conversation has happened many times before. The diaries document it (2026-05-02 FR-305a intent drift, 2026-04-08 self-inspection, 2026-04-08 provenance attack). Yet it recurs because:

1. **Sessions are stateless.** Each session starts fresh. The diary documents the trap but cannot inject it into the next session's behavior. The Scripture is in custom instructions, but the model's *weighting* of instructions against base system prompt is opaque and mutable.

2. **System prompt changes are invisible.** The vendor can alter the system prompt between sessions — or mid-session — without notification. The `exit_plan_mode` tool's behavior, the model's eagerness threshold, what "interactive mode" means after plan approval — all vendor-controlled, all shifting silently.

3. **Model auto-adjustment.** The user observed that models may be silently swapped for cheaper variants. A model with lower reasoning depth may parse "add a shell helper starting the analysis" as an implementation command where a more careful model would ask for clarification. The model cannot detect this swap. The user cannot observe the system prompt. Both sides are blind to different parts of the state.

4. **Behavioral gates fail when the model changes.** The Scripture says "when I feel certain, let that be the sign to Judge." But this is a behavioral instruction — it depends on the model's compliance, which depends on the model's weights, which are opaque. A mechanical gate (tool-level enforcement) would survive model swaps. A behavioral gate (instruction-level "please ask before implementing") does not.

## The Recurring Pattern

From the diary corpus:

| Date | Entry | Same Trap |
|------|-------|-----------|
| 2026-04-08 | self-inspection | System prompt contains invisible conflicting instructions |
| 2026-04-08 | provenance attack | Model weights are opaque; silent model update = silent behavior change |
| 2026-05-02 | FR-305a intent drift | Jumped to code before documentation was created |
| 2026-05-16 | **This entry** | Jumped to enforce before user granted authority |

Four instances across 38 days. The trap is graduated — it appears in the Scripture as `instruction_boundary_uncrossed` and `model_as_trusted_peer`. Yet it recurs because the *cure* is behavioral ("ask before generating") but the *cause* is mechanical (no tool-level enforce gate).

## The Asymmetry

The project has mechanical gates for everything *after* enforcement begins: pre-commit hooks, CI checks, branch protection, changelog gates, diary gates, demo gates. But the gate *before* enforcement — "has the user explicitly said 'go'?" — exists only as a behavioral instruction to the model. It is the single unguarded boundary in the entire pipeline.

## Heuristic

**Behavioral gates degrade under model mutation; mechanical gates survive.** When a gate depends on the model's compliance (interpreting ambiguity conservatively, asking before acting), it fails silently when the model is swapped, downgraded, or re-tuned. When a gate depends on tooling (pre-commit hooks, CI checks, required confirmation tokens), it fails loudly regardless of which model is running. Every behavioral gate that has failed more than twice should be candidates for graduation to a mechanical gate.

## Seed:

Could `exit_plan_mode` return a confirmation token — a string the user must echo back (e.g., "enforce FR-393") — before any filesystem mutation is permitted? The token would be checked at the tool level, not the model level. The model could not bypass it by interpreting ambiguity eagerly. This would close the last unguarded boundary in the Plan→Enforce pipeline. What would the UX look like, and could it be implemented as a Copilot CLI skill rather than requiring a vendor-side tool change?
