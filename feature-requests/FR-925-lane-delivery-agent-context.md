# Feature Request: FR-925 Lane Delivery Must Reach Agent Context

**Priority:** HIGH
**Type:** Bug
**Status:** SUPERSEDED 2026-08-30 by [FR-927](FR-927-retire-fr902-lane-guard-hooks.md) — the hook-created lane this FR delivers no longer exists. Previously: Approved with revisions (folded 2026-08-30); that approval and the implementation record below are preserved as historical fact, not retroactively rejected.
**Effort:** 0.5 days
**Requested:** 2026-08-30
**First consumer / first event:** any agent session at turn 1 while `fr902.live` is armed — the moment it decides where to run its first terminal command
**Research:** [FR-925.research.md](FR-925.research.md) (brief: `feature-requests/research-briefs/fr-925-lane-delivery-problem-brief.md`, run 2026-08-30, 5 personas, unanimous pursue)
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
   SessionStart, the fallback must be **first-command-safe** (R-2):
   merely adding context to the guard's approve response would still
   let the first already-chosen main-checkout command execute. Instead,
   the PreToolUse fallback must *not execute* the first repo-scoped
   tool invocation outside the owning lane — it returns structured
   output carrying the lane instruction; the equivalent retry from
   inside the lane is approved. One interception, then normal guard
   semantics.

3. **Delete the dead stdout announcement** (subtractionist): plain
   `echo` lines go; the lane record file and the advisory instruction
   remain the on-demand fallbacks.

4. **Ship dark, arm by operator** — same `fr902.live` discipline; no
   behavior change until the flag is reviewed. Binding condition (R-4,
   judgement C-2): hook behavior remains dark until a human reviews
   the enforcement diff and arms `.github/hooks/fr902.live`; arming is
   never implied by merge.

### Fail-open policy by hook and error class (R-3)

- **SessionStart** preserves FR-902 refusal behavior: invalid session
  IDs and lane-creation failures exit non-zero and are audited — no
  success-shaped envelope for those cases.
- **PreToolUse fallback** (if used) fails open on unreadable, missing,
  malformed, or stale lane records: no lane envelope is emitted and the
  call is not blocked solely because delivery metadata could not be
  read.
- All new timeout behavior stays within the hook's 15s budget and must
  not weaken existing guard denials.

## Acceptance Criteria (revised per judgement)

- [ ] AC-01: with `.github/hooks/fr902.live` armed in a fresh session,
      the absolute lane path appears in the agent-visible context of
      turn 1 before the first tool command is selected; proof is a
      captured debug-log grep of the first `llm_request`, not hook
      stdout or a successful exit code.
- [ ] AC-02: on the successful live SessionStart path,
      `session-worktree.sh` emits exactly one valid JSON object with
      `hookSpecificOutput.hookEventName == "SessionStart"` and an
      `additionalContext` string containing both
      `FR-902 session lane: <absolute-lane>` and
      `Work there: cd '<absolute-lane>'`; the previous plain stdout
      announcement lines are removed.
- [ ] AC-03: when `.github/hooks/fr902.live` is absent, SessionStart
      remains a silent no-op: no lane, no record, no envelope.
- [ ] AC-04: SessionStart preserves existing FR-902 refusal behavior
      for invalid session IDs and lane-creation failure; these remain
      audited and produce no success-shaped envelope.
- [ ] AC-05: if the AC-01 SessionStart witness fails, enforcement
      implements the PreToolUse fallback: the first repo-scoped tool
      invocation outside the owning lane is not executed, returns
      structured lane context, and an equivalent retry from inside the
      lane is approved.
- [ ] AC-06: in the PreToolUse fallback path, an unreadable, missing,
      malformed, or stale lane record emits no delivery envelope and
      does not block solely because lane metadata could not be read.
- [ ] AC-07: existing FR-902 lane-guard behavior unchanged: out-of-lane
      writes denied with lane path, in-lane writes allowed, read-only
      commands allowed unless the AC-05 fallback is active for initial
      delivery, `FR902_ALLOW_OUTSIDE=1` bypasses only the FR-902 lane
      denial class.
- [ ] AC-08: the advisory instruction in copilot-instructions.md is
      retained unless contradicted by the final delivery mechanism; if
      changed, it still documents the lane record, session-id
      derivation, and escape hatch.
- [ ] AC-09: unit tests cover envelope shape, live-flag gating, stdout
      deletion, missing/malformed lane-record fail-open behavior, and
      the selected fallback path if used.
- [ ] AC-10: changelog fragment in `changelog/unreleased/`.
- [ ] AC-11: diary reflection under `docs/diary/`.

## Implementation Status (2026-08-30)

Enforced per judgement (`FR-925-lane-delivery-agent-context.judgement.md`):

- RED `fd1f200f`: failing envelope witness (JSON-parse of whole stdout);
  refusal/not-live paths asserted envelope-free.
- GREEN `c5d0a38b`: `session-worktree.sh` emits one
  `hookSpecificOutput.additionalContext` envelope (python3 heredoc for
  JSON-safe lane paths); plain stdout announcement deleted. 29 tests
  pass including the unmodified lane-guard suite (AC-07).
- AC-08: advisory instruction untouched — it states hook *stdout* does
  not reach context, which remains true; delivery now bypasses stdout.
- **AC-01 witness pending (C-3)**: requires a fresh VS Code session
  against the updated hook in the main checkout; verify via grep of the
  new session debug log's first `llm_request` for the lane path. If it
  fails, switch to the AC-05 PreToolUse fallback — do not ship
  SessionStart-only as proven.
- C-2 note: `fr902.live` was already armed before this change; the
  operator must review the hook diff (this is the arming review).
- Deviation: none from frozen scope. D-3/D-5 (fallback) not built —
  contingent on witness outcome per C-3.

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
