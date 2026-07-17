# FR-743: SessionStart Briefing Hook — the situation board becomes structural

**Status:** Proposed
**Type:** Enhancement (agent-facing enforcement, `.github/hooks/`)
**Effort:** 0.5–1 day (including the platform-contract probe)
**Requested:** 2026-07-17
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
