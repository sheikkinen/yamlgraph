# Feature Request: FR-739 VS Code Introspection Suite — situational awareness and the compaction altimeter

**Priority:** MEDIUM
**Type:** Enhancement (agent-facing tooling, `scripts/vscode/`)
**Status:** Completed
**Effort:** 1–2 days across independently shippable rungs
**Requested:** 2026-07-16
**Judged:** 2026-07-16 — the FR's own exhibit was mis-attributed: the
merged tap stream shows 11 "compactions" where per-session truth is 1;
session attribution promoted to AC-00, the load-bearing prerequisite
**Completed:** 2026-07-16 — all six rungs; witnesses below
**Spawned by:** the 2026-07-14→16 introspection arc ("a metacognitive
journey into 'self'"): four spikes (`now.py`, `ledger.py`, `stores.py`,
`portrait.py`), the OTel tap (`otel-tap-on.sh` / `tap.py`, commit
b012086f), and the tap's verification witnessing the authoring agent's
own compaction (747,955 → 68,861 tokens between two user messages).
Diaries: `diary-2026-07-16-two-rulers-disagreed.md`,
`diary-2026-07-16-the-guillotine-leaves-a-mark.md`,
`diary-2026-07-16-the-reception-hierarchy.md`.

**Prior art:** FR-737/FR-738 (reception hierarchy: emission ≠ reception;
any tap-derived signal must be delivered on rung 1–2, not left in a
file); FR-438/FR-439 (reasoning sentinel — the arm-then-deny bridge
pattern this FR reuses for delivery); FR-723 (route decision log — the
precedent for opt-in env-gated telemetry with a file sink); Scripture
`one_session_one_repo` + `.github/skills/session-introspection/SKILL.md`
(the existing rung-1 surface these improvements extend). Disposition:
this FR documents and extends the shipped spikes; no rejected FR
occupies this territory (FR-070 concerned browser UI, not introspection).

## North star

**The agent needs to know what's ongoing — and when the guillotine is
coming.** Two blindnesses, one suite:

1. *Concurrency blindness:* parallel sessions share git index, working
   tree, and environment (`one_session_one_repo`, three strikes
   2026-07-14). `now.py` approximates "who is live" from chatSessions
   mtimes; the tap has ground truth (`session.id` on live inference
   events).
2. *Compaction blindness:* context accretes ~1–3K/turn toward a ~750K
   ceiling, then is lossily summarized — invisibly from the inside.
   The tap records the trajectory; nobody reads it in-flow. Verified
   live: the tap's own verification session was compacted mid-arc and
   the agent learned it only from the file.

## Current state (shipped, spike-grade)

| Tool | Does | Blind spot |
|------|------|-----------|
| `now.py` | Situation board: live sessions (mtime), git state incl. nested repos, FRs in motion, interleave-hazard flag | mtime ≈ liveness; workspace-level not repo-level |
| `ledger.py` | Credits/USD by period and model from chatSessions | promptTokens = last round only → rounds× approximation |
| `stores.py` / `portrait.py` | Habitat map; memory/concurrency portrait | forensic only (past tense) |
| `otel-tap-on/off.sh` + `tap.py` | Exact per-call tokens, every inference call, all sessions, one file | rung 4 — no in-flow reader; no growth rule; no quota/cache split (strike 1, trace-level escalation on file) |

## Identified improvements (ranked by north star)

### AC-01 Compaction altimeter (the guillotine warning)
`tap.py --altimeter [session_id]`: per-session context trajectory from
`gen_ai.client.inference.operation.details`, current level, slope,
estimated turns-to-ceiling (ceiling calibrated from witnessed
compactions; first data point: ~748K). Exit code / one-line output
suitable for hook consumption.

### AC-02 Rung-1/2 delivery of the altimeter
Deliver, don't emit (FR-737 U-1): a PreToolUse hook (or session-start
tool result via the skill) that injects "context ~NNN K, compaction
estimated ≤N turns — flush session memory now" when past threshold.
The sentinel arm-then-deny shape: watcher on the passive rung, delivery
on the rung an agent cannot not-read.

### AC-03 Ground-truth liveness in now.py
`now.py --tap`: live sessions from tap `session.id` recency (inference
events in last N minutes) instead of/alongside mtimes; interleave
hazard becomes "session X ran a tool call 40s ago on this repo", not
"a file changed recently".

### AC-04 Ledger exact-mode with provenance seam
Post-tap data uses exact per-call tokens; pre-tap history stays
rounds×-estimated; the seam date is stamped in output so the spliced
series is never mistaken for uniform (`artifact_carries_code_identity`
applied to a time series).

### AC-05 Tap lifecycle rule
Decide meter-vs-experiment before it becomes infrastructure
(`infrastructure_self_exempt`): rotation/size cap for the JSONL
(tap.py already warns >100 MB; enforcement missing), documented
disarm criterion, and quality-signal surfacing (`finish_reasons`
= `length`, `success=false`) in the situation board.

## Non-goals

- No CAPTURE_CONTENT escalation without explicit user decision
  (privacy; two-strike rule holds).
- No always-on daemon; readers are invoked, not resident.
- No claim of invoice-grade cost until quota/cache fields are captured
  or GitHub billing export is reconciled (calibration stands at 98%
  cache, two anchors).

## Acceptance criteria

- AC-01: altimeter output witnessed against a real compaction event
  (predicted ceiling within 10% of observed).
- AC-02: injection witnessed in an agent transcript (rung-2 receipt,
  not audit-log emission) — the FR-738 standard of proof.
- AC-03: `now.py --tap` shows a session as live that mtime-mode misses
  or vice versa, documented in one comparative run.
- AC-04: ledger output carries the seam date; pre/post-tap subtotals
  reconcile with tap.py totals for the overlap window.
- AC-05: growth rule enforced in code; disarm criterion written in
  `scripts/vscode/README.md`.

## Open questions for Judgement

1. Is the compaction ceiling stable per model/plan, or dynamic? (One
   witnessed value; need 2–3 compactions before hardcoding.)
2. Should AC-02 live in `.github/hooks/` (repo-scoped) when the tap is
   machine-global? A yamlgraph hook warns only yamlgraph sessions.
3. Does the summarizer-loss study (diary seed: diff pre-compaction
   transcript vs post-compaction summary) belong here or in its own
   investigation FR (`investigation_before_fix`)?

## Judgement (2026-07-16)

**Verdict: APPROVED — with the FR's central exhibit corrected by
measurement before a line of code exists** (`read_raw_output_first`
applied to the altimeter's own input: the tap stream was re-read
per-session before granting authority).

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | **The merged stream manufactures phantom guillotines.** `copilot_chat.agent.turn` events carry NO `session.id`; read naively, the tap shows **11 collapses** where per-session truth is **1**. Ten of eleven "compactions" are session switches. An altimeter built on the merged stream is worse than none: phantom alarms = alarm fatigue = FR-737-F2 at the altimeter's first heartbeat | **AC-00 (new, prerequisite to all):** session attribution via the measured join — `session.start.traceId → session.id`, then `agent.turn` events keyed by `spanContext.traceId`. Verified clean on the live file: a904c468 = 39 turns, peak 750,382, exactly one compaction (750,382 → 61,205); c0f1927c and 854c6a35 = zero. No per-session claim ships without this join |
| F2 | **Ceiling is n=1 and must not be hardcoded.** Witnessed: one compaction at 750,382. Counter-evidence in the same file: sessions alive at 652,563 and 692,282 *uncompacted* — the ceiling is only bounded to (692K, 750K] by this sample, and may be dynamic per model/plan (open question 1 confirmed real) | The altimeter reports **level, slope, and highest-witnessed-peak** — never a hardcoded ceiling. Each witnessed compaction is **recorded** (session, peak, post-level, timestamp) to a calibration file in `scripts/vscode/`; turns-to-ceiling estimates unlock at ≥3 witnesses. AC-01 reworded: the calibration record IS the deliverable; prediction accuracy is the follow-up, not the gate |
| F3 | **AC-02's delivery rung was under-specified and the hook answer is premature.** A PreToolUse hook reads a growing machine-global JSONL on *every tool call* of *only yamlgraph sessions* — cost without coverage (open question 2 resolved) | Rung-2 first: altimeter output lands in `now.py` (the session-start situation board the skill already mandates) and `tap.py --altimeter`. PreToolUse injection is the **recorded escalation** if rung-2 receipt fails twice (`two_strike_split`); receipt witnessed per the FR-738 standard — in a transcript, not an audit log |
| F4 | AC-04 seam is sound; one correction: the overlap window must exclude sessions from other machines/pre-restart turns absent from the tap by construction — reconcile per-session, not per-total, or the seam "discrepancy" is guaranteed noise | AC-04 reconciles per-session over sessions present in both stores |
| F5 | AC-05's "growth rule enforced in code" — a warning is not enforcement (`detection_without_enforcement`) | `tap.py` rotates on read past the cap (archive with date stamp, start fresh); disarm criterion in README. Current file 0.2 MB/day-of-use: cap 100 MB stands, generous by ~2 orders |
| F6 | Open question 3: the summarizer-loss study is an investigation, not an enhancement — different deliverable (a causal-chain harness), different rhythm | **Out of scope.** Separate investigation FR when pursued (`investigation_before_fix`); this FR only guarantees the raw material survives (F2's calibration records + tap archives) |

**Purge list:** resident daemon; CAPTURE_CONTENT or trace-level
escalation (stays user-decision, outside this FR); hardcoded ceiling;
semantic/embedding anything; summarizer-loss study (F6); per-tool-call
hook delivery before rung-2 receipt fails twice (F3).

**Scope frozen:** AC-00 (attribution join) → AC-01 (altimeter +
calibration record) → AC-02 (rung-2 delivery via now.py/skill) →
AC-03 (ground-truth liveness) → AC-04 (ledger seam, per-session
reconciliation) → AC-05 (rotation + disarm criterion). Each rung
independently shippable; AC-00 blocks all.

## Implementation (2026-07-16)

RED 82ba08a0 (10 failing witnesses, fixture mirrors real exporter
shape) → GREEN in the same day. `tap.py` restructured into judged
functions (`load_events`, `join_sessions`, `detect_compactions`,
`record_compactions`, `altimeter_lines`, `live_session_ids`,
`reconcile`, `rotate_if_big`); `now.py --tap`; `ledger.py --tap`.
Tests: `pytest scripts/vscode/tests/ -q` — 10/10.

**AC witnesses (all live, same day):**
- AC-00/01: first real run recorded the witnessed compaction to
  `compactions.jsonl` (peak 750,382 → post 61,205, session a904c468);
  three live sessions ranked: 715K and 679K climbing, 158K
  post-compaction.
- AC-02: `now.py --tap` output — including the authoring session's own
  altimeter line — arrived in the authoring agent's tool result:
  rung-2 receipt witnessed per the FR-738 standard, not emitted to a
  log. (F3's per-tool-call hook remains the unspent escalation.)
- AC-03: tap showed 3 LIVE sessions with turn counts vs mtime-mode's
  title-only view; ground truth includes turns and models.
- AC-04: seam 2026-07-16 11:54; neighbor session ratio 1.01 —
  the rounds× estimator validated against exact within 1% on a
  complete session; own in-flight session 0.27 because chatSessions
  lags the active turn (expected; documented in README).
- AC-05: rotation archive+truncate under test with a tiny cap;
  truncation chosen over rename to keep the exporter's append fd
  valid. Disarm criterion written in README (meter, not experiment).

**Deviations:** none of scope; one implementation note — slope uses
the last ≤4 turns' consecutive deltas (a zip-tail bug caught by the
RED suite's ETA witness before it shipped).
