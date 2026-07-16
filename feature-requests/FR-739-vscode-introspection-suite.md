# Feature Request: FR-739 VS Code Introspection Suite — situational awareness and the compaction altimeter

**Priority:** MEDIUM
**Type:** Enhancement (agent-facing tooling, `scripts/vscode/`)
**Status:** Proposed
**Effort:** 1–2 days across independently shippable rungs
**Requested:** 2026-07-16
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
