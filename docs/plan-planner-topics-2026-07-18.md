# Planner Topics — 2026-07-18

**Status:** Point-in-time planner brief (statuses verified on disk + live /health 2026-07-18)
**Sources:** [projects/ninchat_voice/docs/plan-fr-queue-2026-07-15.md](../projects/ninchat_voice/docs/plan-fr-queue-2026-07-15.md) (rev 3 — lags, see §5), [docs/fr-board.md](fr-board.md), [docs/world-context.md](world-context.md) (fresh 07-17), csap `reports/weekly/hp-suite-2026-07-14.md`, `now.py` situation board.
**Rule of the file:** every topic names its first consumer and its gate. A topic with neither is `growth_as_default` and does not belong here.

## 1. The critical path: next full csap black-box run (ninchat_voice)

The single most valuable arc. The 07-14 run (56/58) found two defect
families; both are fixed on main; the fixes are **not yet measurable**.
Sequence is judged and frozen (2026-07-17):

| Step | What | Owner | Gate |
|---|---|---|---|
| 1 | ~~Clean deploy of HEAD~~ **DONE (verified 2026-07-18):** `/health` reports `e8e3c2b` = repo HEAD, non-dirty, past `47ca206` — all Finding-2 fixes live | voice enforcer | ✓ gate MET |
| 2 | NC-396 expected-block recalibration (HP-44/67 + flips family) | **csap** (handed off @ their 66d3e5c) | their commit |
| 3 | Flips-suite re-run, 7 cases, ~25 min (currently 1/7 — ruler lag, not defect wave) | voice enforcer | **≥6/7 with residue explained** — hard entry gate for step 5 |
| 4 | Ride-alongs on the same deploy: HP-47/61 pair (Finding-1 fix live-verified), HP-83 single call (NC-387 Exhibit A), partial NC-370 AC-03 signal | voice enforcer | cheap, parallel with 3 |
| 5 | Full 58-case run — new design × new ruler × upgraded harness (twin column NC-389, field gate NC-375, claim-fidelity NC-388) | csap + voice | step 3 gate passed |

Planner note: steps 1–2 are parallel; 3 is meaningless before both; the
expensive run fires exactly once, when it can *falsify the fix wave*
rather than rediscover the pre-fix world.

## 2. ninchat_voice — judgement & filing lane

| Topic | State | Planner action |
|---|---|---|
| **NC-378** schema proposal emitter | Proposed; **gate now MET** (7 synthetic rows ≥ 2 suite runs in `data/schema-signal.jsonl`) | Judge next. First production row will arrive via NC-379's weekly export (ENFORCED 07-17; first window empty) |
| **NC-381** record exporter → ESB | Reserved, unfiled; gate cleared (NC-395 enforced, P8 answered: fly volume, 30-day retention) | File with the message contract (NC-368 fields) + P8 volume/retention as its own AC |
| **P8 follow-up** fly volume tier + 30-day retention for call records | Sanctioned, no FR | Small FR; prerequisite for NC-379's record-source swap (R-4 ship-then-swap) and for NC-381 durability |
| **NC-370** fly sizing | Proposed, stale (resize already live) | Re-scope at judgement; AC-03 validation flood is the oldest open AC on live infra — fold into §1 step 4/5 or run standalone |
| **NC-361** midcall silence | Proposed | Re-scope at judgement — partially superseded by NC-383 findings; do not enforce as written |
| **NC-385 Half B** (HP-76 required-field-never-probed) | Filed, unblocked | Investigation FR; any session |
| **NC-387** additive topic loading | Proposed, Exhibit A provisional | Judge after the HP-83 re-run (§1 step 4) resolves the exhibit |
| **NC-368/382** Digialusta | Externally gated (anonymization + API contract + test env) | Park; poke externally |
| NC-353–356 stress rig | Tier-5 parked (Phase-0 external gates) + headers lag the 07-08 judgement | Sync headers when touched; premises need re-judgement (pool=3 known, N>5 pointless pre-370) |

## 3. yamlgraph — framework lane

| Topic | State | Planner action |
|---|---|---|
| **FR-745** FR triage graph | Judged; **enforcement in flight** (parallel session, RED committed 2026-07-18) | Taken — no second pickup (`one_session_one_repo`) |
| **FR-747** loader error UX | Judged | Enforce lane pickup |
| **FR-746** ideal-result slot (TEMPLATE + Sermon) | Completed 07-18 | Done — new FRs must state Ideal Result before Proposed Solution |
| **Scripture graduation: the assumed-sensor pattern** | 4 recorded strikes (NC-383 "no bash port", NC-389 "run-test lock", NC-377 "asked count", NC-379 "derived species") | Graduate to traps/cures: *"verify the sensor exists before designing the measurement; an empty verification result is a claim requiring a positive control."* Two-strike rule long since met — file the graduation proposal to `.chaplain/inbox/` |
| **Seeds awaiting owners** (Scripture seeds block) | `artifact_carries_code_identity`, `diary_graduation_pipeline`, `inquisitor_auto_escalation`, `req_coverage_as_universal_gate`, `verification_checkpoint_primitive` | Each needs a first consumer named before filing (would_you_use_this); `artifact_carries_code_identity` has one — NC-379's export stamps + shared-repo measurement runs |

## 4. World-context intake (fresh 2026-07-17 — first planner read)

> **Re-distilled 2026-07-18 (world now):** all three questions stand;
> none gains a consumer. Deltas: (1) sandboxing is STRENGTHENED — the
> "Agent Security Is a Systems Problem" paper argues system-level
> design over prompt-level defenses, our `two_strike_split` at
> industry scale; still research-first, chaplain worktrees remain the
> first named consumer. (2) New watch-tier signal: benchmark
> governance / evaluation-reproducibility scrutiny (Kaggle AGI-comp
> inconsistencies) — resonates with the measurement spine and the
> `artifact_carries_code_identity` seed, no FR trigger. (3) Output-
> quality meta-tooling (cliché highlighter) — the ecosystem arriving
> at `read_raw_output_first`; watch only.

Three open questions from [world-context.md](world-context.md) with a
local seam each; file only where a consumer exists:

- **Sandboxing / tool permissions in YAML** — ecosystem incidents
  (grok-build directory upload, web_fetch exfiltration) are the
  `instruction`-boundary trap at industry scale. Local seam:
  `tools/shell.py` sanitization exists; a *declarative* per-tool
  permission surface does not. Research-first (Commandment 1) — no FR
  until a named consumer (chaplain worktrees are the likely first).
- **Routing/eval primitives across model tiers** — lands next to
  FR-723's route hook + `Model Routing Is Simple. Until It Isn't.`
  Watch, don't build: no current graph needs multi-tier routing.
- **Security regressions as first-class eval cases** — fits the
  witness-suite pattern; candidate ride-along whenever the next
  eval-graph FR is filed, not standalone.

## 5. Hygiene debt (cheap, unblocks others)

- **Queue doc rev 4** ([plan-fr-queue-2026-07-15.md](../projects/ninchat_voice/docs/plan-fr-queue-2026-07-15.md)):
  Tiers 1–3 rows all COMPLETE; Tier 5 still lists NC-379 as parked
  (it's ENFORCED); enforcement order should shrink to §1 + §2 above.
- **Status-header sync**: NC-353–356 (read Proposed despite 07-08
  judgement), NC-370 (Proposed despite executed resize).
- **fr-board parse-failure rows** expose the same lag mechanically —
  fix headers, not the board.

## Anti-topics (judged, do not reopen)

- Delivery *graph* (superseded by NC-381 re-scope — `framework_costume`).
- Stress-rig N>5 pre-NC-370 (break-point known by config).
- Watcher subscription (FR-744-the-first, killed by the consumer test).
- Aggregate acceptance gates on multi-defect surfaces (`threshold_encodes_forecast` — gate on defect class).
