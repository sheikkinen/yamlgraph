# Feature Request: FR-590 Plot Modeller — L5 multi-perspective (per-agent comprehend → combine)

**Priority:** HIGH
**Type:** Feature (architecture revision — alternative decomposition axis)
**Status:** Limbo — KILL authority withheld (Gate 1, 2026-06-25); conversion mechanism superseded by FR-591
**Effort:** ~1 day (spike-gated; Gate 1 may KILL early)
**Requested:** 2026-06-25
**Predecessor:** FR-587 (snapshot→diff KILLed — Gate 1, 2026-06-25). See its enforcement result.
**Sibling:** FR-585 (select→type KILLed). FR-590 attacks the **same wound** from a new axis.

## Summary

FR-585 and FR-587 both KILLed the same way: L5 precision is capped by **`at`
over-tracking** — the model floods every beat with every entity's location, while
the ground truth scores only the *salient* relocations. Both prior FRs decomposed
L5 along the **operation** axis:

- FR-585 split *typing* off *selection* (both still on the encoding side) → flat
  precision ~0.30, `at`-FP **86** (88% of all FPs).
- FR-587 split *comprehension* (per-beat snapshot) off *encoding/salience*, moving
  change-and-salience into deterministic code → `at`-FP fell only to **69** (still
  85% of all FPs), and recall collapsed to **0.32** (below the 0.50 floor) → KILL.

FR-587's lesson: moving salience into deterministic code **relocated the flood, it
did not heal it** — code cannot recover salience the model never encoded. The model
still emitted per-beat, per-leg locations and drifted place-phrasing.

This FR cuts a **different axis: subject, not operation.** Instead of one global
pass over all beats, the graph **maps over each agent** and asks the model to do
the one thing it is strongest at — narrate a **single character's throughline**:

1. **Summarize** the plot *from that agent's perspective* (free prose, stored for
   inspection).
2. **Encode** only that agent's pre/eff fluents, keyed to the shared beat ids.
3. **Combine** all agents' encodings deterministically into the unified per-beat L5
   (group by beat, dedup symmetric fluents).

The bet: a single-agent narrative **intrinsically elides non-salient waypoints** —
"Pell flees the safe house for the warehouse, then is summoned to court" names the
two relocations that matter to Pell's story and silently drops the legs between.
Salience becomes a property of the **framing**, not an instruction (FR-585) and not
a post-hoc deterministic computation (FR-587).

## Value statement

L5 precision rises toward ~0.5 — by scoping comprehension to one character at a
time, so the model's strongest faculty (single-subject narrative) does the salience
filtering for free, removing the `at` waypoint flood at its *source* (the framing)
rather than instructing against it (FR-585) or subtracting it after the fact
(FR-587) — and the per-agent prose summaries are a **human-legible diagnostic** the
prior approaches never produced.

## Judgement (2026-06-25)

**Verdict: Authority GRANTED — over a real objection, on a tightened stop rule.**
The FR is clear, minimal, internally consistent, and YAMLGraph-native (a CAP-11
map-reduce over agents, not the FR-588 standalone-spike anti-pattern). Its premise
is verified: FR-587's KILL is real (diary `the-wound-that-only-changed-its-address`:
`at`-FP 86→69, recall 0.32, KILL on the recall-floor conjunct), the reused helpers
(`diff_snapshots`, `_fluent_key`, `_clean_fluent`, `_norm_name`) exist in
`nodes/tools.py`, and `REQ-YG-020` exists in CAP-05. The decomposition axis is
genuinely new: FR-584/585/587 all split the **operation** while keeping the global
all-entities-per-beat framing; FR-590 splits the **subject** so the model never sees
the whole board, betting that single-character narrative compression elides
non-salient waypoints intrinsically. The structured-output encode also removes the
dumb-adapter confound that capped FR-587's precision.

**Red Hat — the serious objection (why this nearly REJECTed).** FR-587's own diary
concludes *"single-tier framing is exhausted"* and names **scale (FR-578)** as the
honest next lever the stop rule reserved. FR-590 is the *fifth* single-tier framing
attempt (after 581/582 wording, 584 architecture, 585 select→type, 587
comprehend→represent). The Scripture trap `audit_as_ritual` (3+ attempts without a
fix = ritual) is live. GRANTED anyway, on three grounds: (1) the subject axis is the
one axis the prior four never touched, and the diary's *own Seed* invites a framing
test before concluding the wound is the model tier; (2) the cost is ~1 day,
hard-gated, falsifiable; (3) a KILL here is **diagnostic** — it resolves
framing-vs-model-tier and *justifies* the FR-578 scale escalation on evidence rather
than blindly. That diagnostic value is the entire reason to spend the day, and it is
also the source of the binding corrections below.

**Corrections required before enforce (the diagnostic must be clean; do not widen
scope):**

1. **Make any KILL diagnostically attributable (primary — this is the FR's whole
   value).** FR-590 runs *two* LLM passes per agent (prose `summarize` → typed
   `encode`). If it floods, the KILL is uninterpretable unless the flood is
   attributed: did the **prose summary itself list waypoints** (→ subject-axis
   framing falsified; the flood is intrinsic to the model at this tier; FR-578 scale
   justified), or was the prose **clean but the encode pass re-introduced them**
   (→ the subject axis is *still untested* — a fused-instrument confound of the same
   family as FR-585 Pass-1, and the encode prompt is the bug, not the framing)? The
   stored `results/l5/perspectives/<genre>/<agent>.md` summaries make this checkable;
   the verdict MUST state which stage flooded, by reading the raw summaries before
   reading the aggregate (FR-585 lesson #1). Without this attribution the spike
   cannot deliver the diagnostic that is its only justification over "scale now."

2. **Pin the `at`-FP GO threshold (one-iteration discipline needs a hard line).**
   "Materially below 69" is too soft to hold the line FR-587 nearly lost to a
   "trending down" reading. Set **GO = `at`-FP ≤ ~35 (≈ halved from 69) AND recall
   ≥ 0.50 AND the dominant FP class shifts off `at`**; `at`-FP above ~35, or recall
   < 0.50, or `at` still dominant = KILL. Mirror FR-587's concrete "86 toward ≤30."

3. **Commit the stop: this is the LAST single-tier decomposition.** On KILL, FR-578
   (scale, with the perspective prompt as the larger model's input) is mandatory
   next — no sixth framing. State this in the Stop rule so the `audit_as_ritual`
   guard is explicit and the escalation is not deferred a fifth time.

4. **Record FR-587's KILL in FR-587 itself (auditability).** FR-590's predecessor
   line says "see its enforcement result," but FR-587's Status still reads *GRANTED*
   and it has no enforcement-result section — the outcome lives only in the diary.
   The FR is the source of truth, not the diary (Scripture: cited rationale in
   `feature-requests/`). Update FR-587's Status to KILLed and add the Gate-1 result
   (`at`-FP 86→69, recall 0.32) so the lineage resolves in the FR record.

**Frozen scope:** the two prompts (`summarize_perspective`, `encode_perspective`) +
`combine_perspectives` (pure, unit-tested, reusing the FR-587 fluent helpers) + the
throwaway spike harness; the map-over-agents subgraph wiring of `assign_pre_eff.yaml`
+ `run.py` follows only on GO. Gate 1 decides the whole FR. One wording iteration
only. `REQ-YG-020` reused (no new CAP). No GT leakage, no evaluator change, no
belief-layer investment, no LLM in `combine_perspectives`, no larger model before
this axis is tested. The corrections above are clarifications within this scope.

## Problem

The shared wound across FR-584/585/587 is **journey-waypoint over-tracking in `at`**
(86 → 69 FPs, never below ~85% of all FPs). Root cause, verified by reading raw
output: a global per-beat pass treats location as a per-beat fact to be re-asserted
for every entity, so it emits every leg of every journey. The GT scores only an
entity's **salient relocations** (FR-587 GT validation: departure scored only for
each entity's *first* move from an established origin; ~8 such departures across 5
fixtures; all later moves arrival-only).

Both prior cuts kept the **global, all-entities-per-beat framing**. Neither asked:
*what if the model never sees the whole board at once?* A single-agent narrative is
the model's native compression — it does not list the side streets a character
walked down, it names where they went. The untested hypothesis is that the wound is
an artifact of the **global framing**, not of the encoding load.

## Proposed solution

### Decomposition axis: per-agent perspective (map-reduce)

This is a **YAMLGraph-native map-reduce** over agents — the framework's core shape,
not a standalone Python spike (the FR-588 anti-pattern). `extract_agents` already
produces the agent list; CAP-11 map nodes already fan out per item.

```
extract_agents (exists) ──► [agent, agent, …]
        │
        ▼  map over agents (CAP-11 map node)
   ┌─────────────────────────────────────────┐
   │  summarize_perspective  (LLM, free prose)│  ← stored to results/l5/perspectives/
   │            │                              │
   │            ▼                              │
   │  encode_perspective     (LLM, fluents     │  ← closed 5-pred vocab, keyed by beat_id,
   │                          for THIS agent)  │     ONLY this agent's participations
   └─────────────────────────────────────────┘
        │
        ▼  combine_perspectives (deterministic code, no LLM)
   per-beat L5  { id, pre_world, eff_world, pre_belief: [], eff_belief: [] }
```

### Stage 1 — per-agent comprehension (LLM, the map body)

**`summarize_perspective.yaml`** — input: the full beat glosses + one focal agent.
Output: free prose narrating the story *as that agent experiences it*, anchored to
beat ids (e.g. "F1: I wait in the safe house … F2: betrayed, I flee to the
warehouse …"). This is the salience filter: a character throughline names the moves
that matter to *them*. **Stored for inspection** at
`results/l5/perspectives/<genre>/<agent>.md`.

**`encode_perspective.yaml`** — input: the focal agent's perspective summary + the
beat ids. Output: typed fluents (`alive`/`at`/`holds`/`rel`/`faction`, same closed
vocabulary as `assign_pre_eff.yaml`) for **only this agent's** state, each tagged
with its `beat_id`. Because the model emits typed fluents directly (structured
output), there is **no dumb-keyword-adapter confound** — this gate is *cleaner* than
FR-587's, whose absolute precision was capped by the `_type_triple` adapter.

### Stage 2 — combination (deterministic code, no LLM)

**`combine_perspectives` helper (`nodes/tools.py`).** Given the per-agent fluent
lists:

- **Group by `beat_id`** into per-beat `eff_world` (and the prior beat's referenced
  subset into `pre_world`, reusing the FR-587 pre/eff pairing).
- **Dedup symmetric fluents** by `_fluent_key` — `rel(Pell,Marren)=hostile` reported
  from both Pell's and Marren's perspective collapses to one (reuse the FR-587
  `_fluent_key`/`_clean_fluent`/`_norm_name` helpers; no new salience logic).
- **No waypoint collapse needed** — that is the whole bet: per-agent framing should
  arrive *already* free of intermediate legs. (If it does not, see Gate 1 KILL.)

Belief slices stay empty for the spike (FR-585: belief is not the wound).

### Files (spike, Gate-1-first — do NOT wire the full graph until GO)

- `prompts/summarize_perspective.yaml` — new (per-agent prose).
- `prompts/encode_perspective.yaml` — new (per-agent typed fluents, beat-keyed).
- `nodes/tools.py` — `combine_perspectives` deterministic helper (pure, unit-tested;
  reuses existing FR-587 fluent helpers).
- `examples/plot_modeller/spike_perspective.py` — spike harness: per fixture, per
  agent → summarize (store) → encode → `combine_perspectives` →
  `results/l5/<genre>.yaml` → `evaluate.main_l5`.
- `evaluate.py` — **frozen** (clean A/B against FR-585 Pass-2 / FR-587 baselines).
- On GO only: `graphs/assign_pre_eff.yaml` gains the map-over-agents subgraph; `run.py`
  wires it.

## Acceptance criteria

- [ ] **Gate 1 — perspective spike (decides the whole FR).** Build the two prompts
      + `combine_perspectives` only. Run on haiku (verify
      `Creating LLM: anthropic/claude-haiku-4-5`), regenerate `results/l5`, report
      precision, recall, and `at`-FP via `analyze_l5_confusion.py`. **Decision rule
      (carries FR-587's recall-floor discipline):** GO requires `at`-FP to fall
      **materially below FR-587's 69** *with recall holding* (**≥ 0.50** — the floor
      FR-587 broke at 0.32). The recall floor is the real bar: per-agent framing must
      not drop participant events. `at`-FP down **with recall < 0.50** is a KILL, not
      a GO.
- [ ] `combine_perspectives` has unit tests (pure function): per-beat grouping,
      symmetric-`rel` dedup across two agents, pre/eff pairing, and union recall
      (an event reported by exactly one of two agents survives), each tagged
      `@pytest.mark.req("REQ-YG-020")` (python tool node) — reuse the existing REQ,
      do not mint a new CAP for an example spike.
- [ ] Perspective summaries are written to `results/l5/perspectives/<genre>/<agent>.md`
      and are **human-legible** — the diagnostic artifact for any recall miss.
- [ ] Confusion re-analysis: the dominant FP class must shift away from `at` flooding
      (`analyze_l5_confusion.py`) for the decomposition to be judged working.
- [ ] One prompt-wording iteration only (FR-584 fourth-iteration lesson). No GT
      leakage, no evaluator change, no belief-layer investment, no LLM in
      `combine_perspectives`, no larger model before this axis is tested.
- [ ] Diary reflection recorded (satisfies `diary-gate`); changelog fragment with
      `req: REQ-YG-020` (satisfies `changelog-req-gate`).

## Alternatives considered — head-to-head with the prior L5 cuts

| FR | Decomposition axis | Salience handled by | `at`-FP | recall | verdict |
|----|--------------------|---------------------|---------|--------|---------|
| 584 | none (one global pass) | LLM, fused | — | — | precision 0.30 |
| 585 | **operation** — typing off selection | LLM (selection) | 86 (88%) | — | KILL |
| 587 | **operation** — comprehend off encode | deterministic code (diff+collapse) | 69 (85%) | 0.32 | KILL |
| **590** | **subject** — per-agent perspective | **the framing itself (intrinsic)** | target ≪ 69 | must hold ≥ 0.50 | **spike** |

**Why this is a genuinely new lever, not a re-skin of FR-587.** FR-587 tried to
*compute* salience after a global comprehension pass and failed because the model
never encoded it — you cannot subtract a flood the model already merged into noise.
FR-590 makes salience **intrinsic to the input framing**: a single character's story
is generated *already* compressed. The attack moves one layer earlier — from "fix the
representation of what was comprehended" to "change what is comprehended at all."

**Why YAMLGraph-native (unlike FR-588).** FR-588 was rejected for fighting the
framework with a standalone Python spike. This decomposition *is* the framework's
map-reduce: `map over agents → combine`. The spike harness is throwaway, but the GO
path is a clean map subgraph, honoring CAP-11.

**Alternatives rejected:**

- **Bigger model on the global framing (the FR-578-style anti-scaling escalation).**
  Still available as the *last* single-architecture lever, but it pays for scale
  before testing whether the wound is the *framing*. FR-590 is the cheaper, more
  diagnostic move first — if per-agent framing also floods `at`, that is strong
  evidence the wound is the model tier, and the escalation is then justified on
  evidence rather than reached for blindly.
- **Per-location or per-object decomposition.** Rejected: locations/objects have no
  natural narrative voice; the per-agent throughline is the model's strongest
  compression mode and the GT's `at` events are agent-owned.
- **Keep FR-587's diff and add a salience LLM pass.** Rejected: adds an LLM to the
  deterministic step (FR-587 J: "no LLM in the diff") and re-introduces the salience
  judgment whose failure is the whole problem.

## Risks (Red Hat)

1. **Combine duplicates symmetric fluents** → mitigated by deterministic
   `_fluent_key` dedup (code, not LLM).
2. **Recall gaps from perspective blind spots** — an agent may not narrate an event
   they witnessed but did not drive. Mitigated: GT world fluents are participant-owned
   (`at`/`holds`/`alive` are about the agent; `rel`/`faction` are symmetric, so at
   least one side reports them). Union recall ≥ per-beat recall *if* each agent reports
   their own state. The recall ≥ 0.50 gate exists precisely to falsify this.
3. **Beat-id misalignment at combine** — the encode prompt MUST key every fluent to a
   shared beat id, or combine cannot align agents. Enforced by the prompt contract +
   a combine unit test.
4. **N× LLM calls** (N agents). Accepted: the map node parallelizes; this is a quality
   spike, not a perf one.

## Disposition (2026-06-25)

**Limbo — KILL authority withheld; superseded as a *mechanism*.** Gate 1 run 1
of the throwaway `spike_perspective.py` harness held world recall ~0.53 but with
`pre_world` 81% garbage (precision 0.21); a "corrected" eff-only + global
`diff_snapshots` variant regressed recall to 0.25 (lossy on partial per-agent
timelines). Neither outcome earned a clean KILL or a GO — the metric is open and
the harness was the wrong instrument (it conflated conversion with scoring).

The **decomposition idea** (per-character viewpoint → typed encoding → deterministic
combine) survives and is promoted into a proper graph by **FR-591**
(`perspective_l5.yaml` + `perspective_agent.yaml`), which carries the encoding
contract as **provisional / precision-open** and defers the pre_world precision
fix to the ensemble follow-up FR. FR-590's throwaway `spike_perspective.py` is
deleted by FR-591. The L5 *metric* verdict remains unresolved (open question), so
this FR is recorded as limbo rather than KILL or GO.

## Related

- [FR-587](FR-587-plot-modeller-L5-snapshot-then-diff.md) — snapshot→diff KILL (predecessor; reuse its fluent helpers).
- [FR-585](FR-585-plot-modeller-L5-salience-gate-decode.md) — select→type KILL; GT departure validation; dumb-adapter confound.
- [FR-584](FR-584-plot-modeller-L5-salience-and-roles.md) — monolith baseline (precision 0.30) and the one-iteration rule.
- `docs/diary/diary-2026-06-25-the-wound-that-only-changed-its-address.md` — FR-587 reflection; this FR is one answer to its Seed ("is single-beat salience even learnable" — try a new framing before concluding it is not).
- `examples/plot_modeller/nodes/tools.py` — `diff_snapshots`, `_fluent_key`, `_clean_fluent`, `_norm_name` (reused by `combine_perspectives`).
- `examples/plot_modeller/evaluate.py` — `main_l5` scorer (frozen for clean A/B).
- CAP-11 — map node compilation (the GO-path graph shape).
