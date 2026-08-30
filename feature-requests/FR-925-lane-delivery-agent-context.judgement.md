# Judgement: FR-925 Lane Delivery Must Reach Agent Context

**Prior art:** `FR-925-lane-delivery-agent-context.md` is the FR under judgement, not precedent — this file is its verdict artifact. Genuine precedent (FR-902, FR-888, commit `b8fbd24d`) is dispositioned in the FR's own Prior art line and weighed throughout this judgement.

**Verdict:** APPROVED WITH REVISIONS — the problem is real and the seam-focused fix is directionally sound, but authority activates only after the FR corrects its identity/evidence path, makes the fallback satisfy "before first command," and disambiguates hook failure policy.

**Reviewed against:** `feature-requests/FR-925-lane-delivery-agent-context.md`; `feature-requests/FR-925.research.md`; `feature-requests/research-briefs/fr-925-lane-delivery-problem-brief.md`; `feature-requests/FR-902-session-worktree-lifecycle.md`; `feature-requests/FR-902-session-worktree-lifecycle.judgement.md`; `docs/diary/diary-2026-08-30-the-binding-that-passed-every-test.md`; commit `b8fbd24d`; `.github/copilot-instructions.md`; `.github/hooks/scripts/session-worktree.sh`; `.github/hooks/scripts/session-briefing.sh`; `.github/hooks/scripts/pre-command-guard.sh`; `.github/hooks/tests/test_fr902_session_worktree.py`; `.github/hooks/tests/test_fr902_lane_guard.py`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `feature-requests/TEMPLATE.md`.

## What is sound

The FR identifies a real delivery seam, not a hypothetical improvement. It records that SessionStart created the lane and wrote the record, while turn 1's LLM request had zero occurrences of the lane text and the agent remained in the main checkout (`feature-requests/FR-925-lane-delivery-agent-context.md:29-37`). The cited problem brief states the same observed failure and explains why read-only work and cwd can remain silently outside the lane until a write-shaped command trips the guard (`feature-requests/research-briefs/fr-925-lane-delivery-problem-brief.md:10-21`, `feature-requests/research-briefs/fr-925-lane-delivery-problem-brief.md:47-51`).

The scope is small and properly focused on delivery rather than rebuilding the lane system. FR-902 already owns lane creation and write guarding (`feature-requests/FR-902-session-worktree-lifecycle.md:52-60`), and the current hook script shows the exact dead surface: after writing the lane record it emits two plain `echo` lines (`.github/hooks/scripts/session-worktree.sh:49-55`). The repo instruction already documents that hook stdout does not reach agent context and gives advisory discovery instructions (`.github/copilot-instructions.md:37-38`), so this FR is correctly positioned as making that discovery mechanical rather than expanding guard semantics broadly.

Research is substantive enough for planning authority once the revisions below are folded. It preserves multiple solution classes and disagreement: PreToolUse schema delivery, SessionStart JSON delivery, pure subtraction, and external-method evidence (`feature-requests/FR-925.research.md:7-13`). It also answers `is_this_a_graph` as no/none across the candidates (`feature-requests/FR-925.research.md:9-13`), matching the repo doctrine that graphs are for graph-shaped orchestration, not hook output plumbing.

The acceptance criteria mostly target the right witness: AC-01 requires grepping the first `llm_request` rather than accepting hook stdout or exit code (`feature-requests/FR-925-lane-delivery-agent-context.md:85-88`). That is aligned with the cited diary cure: run the seam, not merely the surface, because green component checks can miss whether the contract crossed the boundary (`docs/diary/diary-2026-08-30-the-binding-that-passed-every-test.md:63-93`).

## Required revisions

### R-1: Correct the FR identity and evidence path

Change the heading from `FR-902` to `FR-925`. The file name, research file, and user-facing task identify this as FR-925, but the title line currently says `# Feature Request: FR-902 Lane Delivery Must Reach Agent Context` (`feature-requests/FR-925-lane-delivery-agent-context.md:1`). Also make the research brief path unambiguous from the repository root: `feature-requests/research-briefs/fr-925-lane-delivery-problem-brief.md`. The current inline path is written as `research-briefs/fr-925-lane-delivery-problem-brief.md` (`feature-requests/FR-925-lane-delivery-agent-context.md:9`), while the committed file lives under `feature-requests/research-briefs/`. This is a fold-only metadata correction, but it matters because the judge doctrine denies authority for absent or dangling research records (`.github/skills/judge-fr/doctrine.md:118-128`; `feature-requests/TEMPLATE.md:11-20`).

### R-2: Make the fallback satisfy "before first command"

Replace the current fallback wording with a first-command-safe fallback. If SessionStart `hookSpecificOutput.additionalContext` is not proven to appear in turn 1 before the model chooses its first tool call, the fallback must not be "approve and inform later." The current guard's clean path emits only `{"decision":"approve"}` at the end of inspection (`.github/hooks/scripts/pre-command-guard.sh:712-714`), and the existing lane guard explicitly allows read-only commands outside the lane (`.github/hooks/tests/test_fr902_lane_guard.py:131-137`). Merely adding context to an approve response would still allow the first already-chosen main-checkout command to execute, leaving the read/cwd hole the FR says it is closing (`feature-requests/FR-925-lane-delivery-agent-context.md:43-47`).

The FR must state this fallback mechanically: if the SessionStart channel fails the witness, PreToolUse must prevent the first repo-scoped tool invocation outside the owning lane from executing and return the lane instruction in structured output; the next invocation from inside the lane is allowed. That is the minimal fallback consistent with the stated first consumer/event (`feature-requests/FR-925-lane-delivery-agent-context.md:8`) and the "agents start working in their lane at turn 1" value statement (`feature-requests/FR-925-lane-delivery-agent-context.md:21-25`).

### R-3: Disambiguate fail-open policy by hook and by error class

Rewrite AC-03 so it does not conflict with existing FR-902 behavior. The FR says "hook remains fail-open on its own errors" and that malformed lane records produce no envelope and no session-blocking failure (`feature-requests/FR-925-lane-delivery-agent-context.md:91-93`). That is valid for an unreadable/malformed lane record in the PreToolUse fallback path: the existing guard already exits without denial when the record cannot be read or the lane is missing (`.github/hooks/scripts/pre-command-guard.sh:520-525`). It is not valid as a blanket statement about SessionStart, because the current SessionStart hook rejects invalid session IDs and lane creation failures (`.github/hooks/scripts/session-worktree.sh:37-46`), and FR-902 tests require invalid IDs to return nonzero and be audited (`.github/hooks/tests/test_fr902_session_worktree.py:162-177`).

The FR must define the policy explicitly:

- SessionStart delivery changes must preserve FR-902's invalid-session and lane-creation refusal behavior.
- PreToolUse fallback delivery must fail open on unreadable/malformed/missing lane records by emitting no lane envelope and not blocking solely because delivery metadata could not be read.
- All new timeout behavior must remain bounded and tested without weakening existing guard denials.

### R-4: Add the human arming gate explicitly

Add a judgement/enforcement condition to the FR that hook behavior remains dark until a human reviews the enforcement diff and arms `.github/hooks/fr902.live`. The proposed solution says "Ship dark, arm by operator" (`feature-requests/FR-925-lane-delivery-agent-context.md:80-81`), but enforcement-infrastructure changes are adversarial input under judge doctrine and require a human-review GATE (`.github/skills/judge-fr/doctrine.md:94-103`). This must be a binding condition, not prose.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-925-lane-delivery-agent-context.md`: fold R-1 through R-4, update acceptance criteria, and later record implementation status/decisions. |
| D-2 | `.github/hooks/scripts/session-worktree.sh`: replace the successful live-path plain stdout announcement with a valid SessionStart `hookSpecificOutput.additionalContext` JSON envelope, if the witness proves SessionStart delivery. |
| D-3 | `.github/hooks/scripts/pre-command-guard.sh`: only if the SessionStart witness fails, add the first-command-safe fallback described in R-2; preserve existing FR-902 write-denial and escape semantics. |
| D-4 | `.github/hooks/tests/test_fr902_session_worktree.py`: update/add unit coverage for live flag gating, successful envelope shape, stdout deletion, and SessionStart failure policy. |
| D-5 | `.github/hooks/tests/test_fr902_lane_guard.py`: only if fallback is used, add/update coverage for first repo-scoped out-of-lane tool interception, in-lane allow, missing/malformed record fail-open, and unchanged existing denials. |
| D-6 | `changelog/unreleased/*.md`: changelog fragment for this hook bugfix. |
| D-7 | `docs/diary/*.md`: reflection entry after implementation. |

Not authorized: changes to FR-902 lane creation semantics outside what is required for delivery; fixes for the separate guard false-positive classes listed as out of scope (`feature-requests/FR-925-lane-delivery-agent-context.md:130-138`); removing the advisory instruction from `.github/copilot-instructions.md` unless the new mechanism contradicts it (`feature-requests/FR-925-lane-delivery-agent-context.md:96-98`); routing through `session-briefing.sh` or `now.py --brief`, which the FR rejected (`feature-requests/FR-925-lane-delivery-agent-context.md:118-120`); broad hook framework refactors; changing judge/review doctrine; invoking another judge route.

## Revised acceptance criteria

- [ ] AC-01: With `.github/hooks/fr902.live` armed in a fresh session, the absolute lane path appears in the agent-visible context of turn 1 before the first tool command is selected; proof is a captured debug-log grep of the first `llm_request`, not hook stdout or a successful exit code.
- [ ] AC-02: On the successful live SessionStart path, `session-worktree.sh` emits exactly one valid JSON object containing `hookSpecificOutput.hookEventName == "SessionStart"` and an `additionalContext` string that contains both `FR-902 session lane: <absolute-lane>` and `Work there: cd '<absolute-lane>'`; the previous plain stdout announcement lines are removed.
- [ ] AC-03: When `.github/hooks/fr902.live` is absent, SessionStart remains a silent no-op: no lane is created, no lane record is written, and no delivery envelope is emitted.
- [ ] AC-04: SessionStart preserves existing FR-902 refusal behavior for invalid session IDs and lane-creation failure; these cases remain audited and do not produce a success-shaped lane envelope.
- [ ] AC-05: If the AC-01 SessionStart witness fails, enforcement implements the PreToolUse fallback: the first repo-scoped tool invocation outside the owning lane is not executed, returns structured lane context, and an equivalent retry from inside the lane is approved.
- [ ] AC-06: In the PreToolUse fallback path, an unreadable, missing, malformed, or stale lane record emits no delivery envelope and does not block solely because lane metadata could not be read.
- [ ] AC-07: Existing FR-902 lane-guard behavior is unchanged: out-of-lane writes are denied with the lane path, in-lane writes are allowed, read-only commands remain allowed unless the fallback from AC-05 is active for initial delivery, and `FR902_ALLOW_OUTSIDE=1` bypasses only the FR-902 lane denial class.
- [ ] AC-08: The advisory instruction in `.github/copilot-instructions.md` is retained unless contradicted by the final delivery mechanism; if changed, it still documents the lane record, session-id derivation, and escape hatch.
- [ ] AC-09: Unit tests cover envelope shape, live-flag gating, stdout deletion, missing/malformed lane-record fail-open behavior, and the selected fallback path if used.
- [ ] AC-10: A changelog fragment exists in `changelog/unreleased/`.
- [ ] AC-11: A diary reflection exists under `docs/diary/`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is not active until R-1 through R-4 are folded into the FR. | GATE |
| C-2 | Because this changes hook enforcement infrastructure, a human must review the hook diff before `.github/hooks/fr902.live` is armed for live sessions. | GATE |
| C-3 | The enforcer must first run the SessionStart `additionalContext` witness. If the witness fails, the implementation must switch to the R-2 PreToolUse fallback rather than shipping an unproven SessionStart-only mechanism. | GATE |
| C-4 | The implementation must not alter FR-902 lane guard denials, audited escape behavior, or branch/worktree lifecycle except where explicitly listed in the frozen scope. | GATE |
| C-5 | The false-positive guard classes named as follow-up material are parked for a separate FR and must not be fixed here. | GATE |

Authority granted: after the revisions are folded, build a live-gated hook-delivery fix that gets the FR-902 lane path into agent-visible context before any repo work proceeds, with SessionStart JSON as the preferred route and the first-command-safe PreToolUse fallback only if the preferred route fails its witness.
