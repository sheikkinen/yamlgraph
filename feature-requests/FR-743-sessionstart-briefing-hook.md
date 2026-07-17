# FR-743: SessionStart Briefing Hook — the situation board becomes structural

**Status:** Enforced — probe verdict + receipt witness pend the first fresh session
**Type:** Enhancement (agent-facing enforcement, `.github/hooks/`)
**Effort:** 0.5–1 day (including the platform-contract probe)
**Requested:** 2026-07-17
**Judged:** 2026-07-17 — bundle probe: SessionStart present in the
runtime (76 refs); TWO undocumented events found (UserPromptSubmit,
SessionEnd — the diary-debt moment); probe widened, scope held
**Enforced:** 2026-07-17 — AC-01/03/04 witnessed; AC-00/02 armed,
awaiting a fresh session (see Implementation)
**Spawned by:** the events-to-agent seam research (2026-07-16, MAP.md
seam 4): three delivery seams proven or mapped; SessionStart is the
declared-but-unused one — the natural briefing moment. Every FR-741/742
delivery today depends on an agent *voluntarily* running `now.py`;
the reception hierarchy says voluntary reading is rung 3–4 behavior
wearing a rung-2 costume. A session that skips the ritual inherits
nothing: no orphans, no diary debts, no interleave flags, no
altimeter.

**Prior art:** FR-741/742 (the briefing content this FR delivers:
orphaned intentions, diary debts, claims-vs-facts section); FR-739
(altimeter + tap liveness); FR-737/738 + reception-hierarchy diary
(emission ≠ reception; name the rung, the reader, the moment — this FR
assigns the *moment* structurally); FR-438/439 (sentinel: the rung-1
sibling for critical events — explicitly NOT this FR's channel);
hooks README (SessionStart listed in the event table; FR-425's
daemon sketch names SessionStart auto-start as future work). The
session-introspection skill remains the pull path; this FR adds push.
Disposition: no rejected FR touches session-start injection; the
skill (FR-446 family) is complementary, not superseded.

## Problem

The situation board answers past/present/future in one command — but
only for agents that run the command. The `one_session_one_repo`
ritual, orphan triage, and diary-debt inheritance are all
*voluntary*: a fresh session starts blind and stays blind unless its
human or its habits invoke `now.py`. The measured failure mode is
this week's history: interleave incidents happen at session start,
precisely before any briefing has been read.

## Proposed Solution

1. **AC-00 Platform probe first** (`read_raw_output_first` applied to
   the hooks contract): SessionStart is *documented* in our README but
   exercised by nothing — verify the runtime actually fires it (a
   probe hook writing one line to `logs/audit.jsonl`), and record
   what stdin it receives and where stdout lands (context injection?
   systemMessage? swallowed?). **This FR's design freezes only after
   the probe**: if SessionStart output is not agent-visible, the
   verdict is recorded and the FR falls back to wiring the briefing
   into the *first* PreToolUse of a session (sentinel-style
   first-call detection — same courier, later moment).
2. **`session-briefing.json` + `session-briefing.sh`**: on
   SessionStart, run `now.py --window 2` in compact mode and deliver:
   interleave flags, orphaned intentions + diary debts (FR-741/742),
   altimeter levels, plan-state pointer. Hard timeout ≤5s (the hook
   budget); on any failure, deliver nothing and exit 0 — a briefing
   hook that blocks session start is worse than no briefing
   (`automation_inherits_doctrine`: same failure-isolation rules as
   every other hook).
3. **Compact mode** (`now.py --brief`): ≤15 lines, headline-only —
   the full board stays pull. A briefing nobody can skim is a wall
   (FR-737 F2: alarm fatigue).
4. **Receipt witness**: per the FR-738 standard — a real fresh
   session's transcript showing the briefing arrived and was acted on
   (e.g., the session references an inherited orphan or flag it was
   never told about by the human).

## Acceptance Criteria

- [ ] AC-00: probe results recorded in this FR (fires? stdin schema?
      stdout visibility?) — design frozen only after.
- [ ] AC-01 RED: briefing script unit-tested (compact output, ≤15
      lines, exit-0-on-any-failure, ≤5s timeout).
- [ ] AC-02: receipt witnessed in a fresh session's transcript.
- [ ] AC-03: failure isolation witnessed — briefing script killed /
      erroring produces a normal session start.
- [ ] AC-04: MAP.md seam 4 updated with the probe verdict (the
      SessionStart row moves from "declared, unused" to measured).

## Out of scope (purge list)

- Rung-1 sentinel envelope for critical events (compaction-imminent,
  collision forecast) — separate FR when the altimeter has ≥3
  witnesses; this FR is the informational channel only.
- The detector daemon (FR-425 territory).
- Any LLM in the briefing path.
- Blocking/deny semantics at session start.

## Questions for the human (as options, or 'none')

None — AC-00's probe answers the only open question (platform
behavior), and the fallback path is specified for both probe
outcomes.

## Judgement (2026-07-17)

**Verdict: APPROVED — with the platform contract measured as far as a
bundle grep reaches, and the probe scope widened by what the grep
found.**

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | **The runtime knows SessionStart** — 76 occurrences in the built-in extension bundle (alongside PreToolUse 87 / PostToolUse 131). Existence ≠ wiring: whether our hook-config schema reaches it and where stdout lands remains unmeasured | AC-00 stands as the design gate; the bundle evidence upgrades the prior from "documented in our own README" to "present in the runtime". The fallback (first-PreToolUse detection) stays specified |
| F2 | **The probe found two undocumented events: `UserPromptSubmit` (43) and `SessionEnd` (28).** Our hooks README's event table is incomplete — prior art lives in the bundle, not our docs. SessionEnd is *the diary-debt moment*: FR-742 measured that sessions die exactly when reflection is due; a SessionEnd hook is the structural answer to that finding | AC-00 probes **all three events in one config** (marginal cost ≈ zero: one probe script, three registrations, one line each to audit.jsonl). Scope stays SessionStart-briefing; SessionEnd flush/diary-warning and UserPromptSubmit are RECORDED as territory in MAP.md and left to their own FRs — this judgement refuses the scope-creep its own measurement invites |
| F3 | ≤15-line budget is asserted, not derived | Keep as the F2-of-FR-737 default (silence over noise); the receipt witness (AC-02) is the empirical check — if the witnessed session skims past the briefing, the budget was still too fat |
| F4 | `now.py --brief` does not exist yet; the briefing script shelling into a 200-line board would blow the 5s/15-line budget | AC-01 includes `--brief` as a tested now.py mode (headline counts only: hazards, orphans+debts count, altimeter top line, board pointer). Fail-open pinned by test |
| F5 | Hook JSON files load at session start — a config error could break ALL hooks, not just this one | The probe config ships as a separate JSON file (isolation by file, matching pre-command-guard.json precedent); AC-03's kill-test covers script failure AND malformed-config rollback |

**Purge confirmations:** rung-1 sentinel envelope, detector daemon,
LLM, deny semantics — all stay out. SessionEnd/UserPromptSubmit
explicitly out (F2).

**Scope frozen:** AC-00 (three-event probe, verdict recorded here) →
AC-01 (`now.py --brief` + briefing script, RED-first, fail-open) →
AC-02 (fresh-session receipt witness) → AC-03 (failure isolation) →
AC-04 (MAP.md seam update).

### Questions for the human (as options, or 'none')

None — F2's discoveries are recorded, not adopted; no authority gaps.

## Implementation (2026-07-17)

RED (4 witnesses) → GREEN. `now.py --brief` (≤15 lines, per-seam
degradation — live run produced 8 lines incl. a real interleave
warning and the altimeter top); `session-briefing.sh` (fail-open:
exit 0 with sabotaged PATH, pinned by test); `session-probe.sh`
(stdin schema → audit.jsonl + stdout visibility marker; self-tested
with fixture stdin — log line and marker both correct);
`session-probe.json` registers SessionStart (probe + briefing),
UserPromptSubmit, SessionEnd — isolated file per judgement F5.

**Armed, not yet witnessed (requires a fresh session — human
action):**
- AC-00 verdict: which events fire, stdin schema per event, and
  whether the stdout marker/briefing is agent-visible. Read
  `.github/hooks/logs/audit.jsonl` for `"probe": "FR-743"` lines
  after opening a new session.
- AC-02 receipt: the fresh session's transcript referencing briefing
  content it wasn't told by the human.

On negative visibility verdict: fall back to first-PreToolUse
delivery per the judged design; the probe stays until all three
events have a recorded verdict, then unregisters (it is an
experiment, not a meter — AC-05 discipline from FR-739).

## Amendment A1 (2026-07-17): probe widened to six events

Second bundle grep (prompted by "is there a hook for compact?"):
**PreCompact** (10 refs), **PostCompact** (7), **PostToolUseFailure**
(17) also exist in the runtime — three more events our hooks README
never listed. Registered in the same probe config (the F2
marginal-cost argument, applied again). Consequences if they fire:
- **PreCompact** = the flush-before-guillotine moment — supersedes
  the altimeter's *predictive* protection (ceiling models, ETA) with
  an exact platform event; the ceiling-that-wasn't-one-thing problem
  (2026-07-17 diary) becomes moot for the protective use case.
- **PostCompact** = mechanical witness recording for
  compactions.jsonl (cures the poll-gated harvest).
- Distill-at-compaction (FR-742 seed) gains its mechanism.
Each is its own FR once the probe returns verdicts.
