# Feature Request: FR-902 Lane Delivery Must Reach Agent Context

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-08-30
**First consumer / first event:** any agent session at turn 1 while `fr902.live` is armed — the moment it decides where to run its first terminal command
**Research:** [FR-925.research.md](FR-925.research.md) (brief: `research-briefs/fr-925-lane-delivery-problem-brief.md`, run 2026-08-30, 5 personas, unanimous pursue)
**Prior art:** gate hits are filename-noun noise ("problem, brief"): `census-human-readable-tail.md`, `corpus-census-skeleton-reuse.md`, `corpus-map-reduce-reference-contract.md`, `diary-trap-recurrence-census.md` share no subject matter with lane delivery — not applicable. `fr-888-problem-brief.md` is genuine adjacent precedent: FR-888 guards main-checkout writes, FR-902 built the lane substrate this FR delivers; distinguished in Problem/Related — this FR changes delivery only, no guard semantics.

## Summary

FR-902 creates a session lane and guards it, but the lane announcement is
plain SessionStart stdout, which VS Code captures into hook telemetry and
discards. The agent never learns its lane exists until a write trips the
guard. Deliver the lane through the structured `hookSpecificOutput` JSON
channel — the one channel proven to reach agent context — and delete the
dead stdout announcement.

## Value Statement

Agents start working in their lane at turn 1 instead of squatting in the
shared main checkout until first denial, closing the read/cwd hole that
`one_session_one_repo` still leaks through.

## Problem

Witnessed in session 9acc40e0 (2026-08-30):

- SessionStart hook ran ok (audit `approve / lane ready`, lane record
  written) — yet turn 1's LLM request contains **zero** occurrences of
  "session lane" / "Work there" (verified in the session debug log).
- The hook's comment promises "(briefing orders after this hook)" but
  `session-briefing.sh` carries no lane information at all.
- The agent ran its entire first turn in the main checkout; the operator
  had to ask "are we in worktree".

Every component is green; the seam between hook output and agent context
is unexercised — the same trap class recorded twice that morning in the
diary ("the binding that passed every test and delivered nothing").

Current mitigation is fail-closed only: the first out-of-lane *write* is
denied with lane instructions. Reads, analysis, and terminal cwd stay
silently out-of-lane. An advisory instruction exists in
copilot-instructions.md (`b8fbd24d`) — the discovery ring — but nothing
mechanical delivers the lane.

## Proposed Solution

Research convergence (5/5 pursue; two personas convergent on
schema-data, one external-method with VS Code docs citation):

1. **SessionStart emits structured JSON, not stdout.**
   `session-worktree.sh` replaces its two `echo` lines with a
   `hookSpecificOutput` envelope carrying `additionalContext` — the
   documented VS Code channel for injecting initialization state:

   ```json
   {
     "hookSpecificOutput": {
       "hookEventName": "SessionStart",
       "additionalContext": "FR-902 session lane: <lane>\nWork there: cd '<lane>'"
     }
   }
   ```

2. **Verify the channel before relying on it.** First enforcement step:
   a witness run proving `additionalContext` from SessionStart actually
   appears in turn 1's LLM request (debug-log witness, same method that
   proved the stdout gap). If VS Code does not honor it for
   SessionStart, fall back to emitting the same envelope from the
   PreToolUse guard's *approve* path (fires before the first tool call;
   proven channel — three personas' primary route).

3. **Delete the dead stdout announcement** (subtractionist): plain
   `echo` lines go; the lane record file and the advisory instruction
   remain the on-demand fallbacks.

4. **Ship dark, arm by operator** — same `fr902.live` discipline; no
   behavior change until the flag is reviewed.

## Acceptance Criteria

- [ ] AC-01 (the seam, not the component): in a fresh session with
      `fr902.live` armed, the lane path appears in the agent-visible
      context of turn 1 — witnessed by grep of the session debug log's
      first `llm_request`, not by hook stdout or exit code.
- [ ] AC-02: `session-worktree.sh` emits a valid `hookSpecificOutput`
      JSON envelope; the plain-stdout announcement lines are removed.
- [ ] AC-03: hook remains fail-open on its own errors and within its
      15s budget; a malformed lane record produces no envelope and no
      session-blocking failure.
- [ ] AC-04: lane guard behavior unchanged — existing FR-902 lane-guard
      tests pass unmodified.
- [ ] AC-05: the advisory instruction in copilot-instructions.md is
      updated only if the delivery mechanism contradicts it, not
      removed (instruction = discovery ring, hook = enforcement ring).
- [ ] AC-06: hook unit tests cover envelope shape, live-flag gating,
      and the missing-record path.
- [ ] Changelog fragment in `changelog/unreleased/`.
- [ ] Diary entry.

## Alternatives Considered

Dispositioned in [FR-925.research.md](FR-925.research.md):

- **PreToolUse-approve delivery** (os-infra, data-process, native
  planner): inject lane into the guard's approve-path JSON on every
  tool call. Held as the fallback if SessionStart `additionalContext`
  is not honored — per-call repetition is noisier than one-shot
  session-start delivery, but the channel is already proven.
- **Pure subtraction** (subtractionist): delete the stdout lines and
  rely solely on the lane record + copilot-instructions advisory.
  Folded partially (the deletion), rejected as the whole fix: advisory
  discovery failed silently once already; the mechanical ring is the
  point.
- **Briefing integration**: wire the lane into `session-briefing.sh` /
  `now.py --brief`. Rejected: the briefing rides the same undelivered
  stdout channel — same defect, one hop removed.

## Related

- FR-902 (`feature-requests/FR-902-session-worktree-lifecycle.md`) — the
  surface this closes the seam on; hook comment already promised
  "agent-visible lane delivery".
- Commit `b8fbd24d` — interim advisory instruction (discovery ring).
- Diary 2026-08-30 "the binding that passed every test and delivered
  nothing" — the trap class, third witness in one day.
- **Separate follow-up candidate (out of scope here):** the lane
  guard's write-target path model produced three false-positive classes
  in one session — git writes resolved to hook cwd ignoring in-command
  `cd`, `python3 -c` treated as a write at cwd, and shell-variable
  paths (`$D/...`) unresolvable hence root-resolved. Each forced the
  `FR902_ALLOW_OUTSIDE=1` escape for genuinely in-lane work, training
  an escape reflex that erodes the audit signal. Two-strike material
  (`two_strike_split`): the abstraction belongs in code, not in agent
  workarounds.
