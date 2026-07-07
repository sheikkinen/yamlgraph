# Feature Request: FR-691 — Plot Threads + Throughlines Extraction

**Priority:** HIGH
**Type:** Feature
**Status:** Enforced ✅ (RED `4d9873fd` → GREEN `08549508` → pipeline `feat(examples): FR-691 wire story_extract pipeline`; 1a/1b diff read below)
**Effort:** 2 days
**Requested:** 2026-07-07
**Judged:** 2026-07-07
**Depends:** FR-690 (event sequence — the throughline walk is its first consumer)
**Plan:** docs/plan-novel-fandom-story-pipeline.md (Phase 2 of 7)

## Summary

Resurrect the plot layer dropped in Gen 3: extract 3–6 plot threads from the synopsis (cheap, Gen 1 style), reconcile them against full canon (ground ids, mine latent threads from fears/tensions/rules), and generate per-character throughlines. All output to `story/` as regenerable derived artifacts with mechanical gates.

## Value Statement

The pipeline gains the artifact that makes de-escalation (`conflict_dissolution_bias`) visible and mechanically checkable — the deficit list every downstream step consumes.

## Problem

The canon is vertically deep, horizontally silent. Threads (by conflict) are the dual decomposition to throughlines (by character); the character slice alone cannot see de-escalation — an arc can look complete while every conflict quietly dissolves. Plot information entered at the synopsis boundary but genesis shredded it into per-entity fields (`the_one_law` violated); this FR extracts it where it entered.

## Proposed Solution

Single graph `examples/novel_fandom/story_extract.yaml`, three LLM nodes. Canon loading reuses the existing `reload_canon.py` node (honor existing patterns); prior-thread prefetch reads `story/thread/` if present.

1. **1a threads-from-synopsis** (~2k tokens input): 3–6 named tensions — carriers, stakes, required `opposition`, raise/release beats in synopsis order. Persisted to `story/threads_1a.yaml` (kept — it is the diff's left side).
2. **1b reconcile** (full canon ~23k): map carriers/raises/releases to canon ids (unresolvable → deficit entries, not errors); mine latent threads from character `fears`/`backstory`, faction `internal_tensions`, and rules. Receives prior `story/thread/` set for id stability. **Final union capped at 8 threads**: 1a contributes ≤6; each admitted latent thread carries a one-line justification citing the canon field it was mined from; reconcile ranks and drops beyond the cap with reasons.
3. **1c throughlines**: per major character, walk events in `sequence` order; emotional state, gain/loss, slack points.

Schemas first: `Thread` and `Throughline` Pydantic models in `examples/novel_fandom/schema/story.py` (new module — derived artifacts, not canon; keeps `canon.py` under the module-size limit). Thread shape per plan (closed `kind` enum, `carriers`, `sources`, `opposition` required non-empty, `raises`/`releases` event ids, `status`).

**Mechanical gates** — pure functions in `examples/novel_fandom/nodes/thread_gates.py`, invoked as Python nodes inside `story_extract.yaml` (fail the run) and imported directly by tests (one implementation, two callers):

1. Citation integrity — every carrier/source/raise/release id resolves against canon
2. Ledger walk — release without prior raise (by `sequence`) fails (ported from `dungeon_master/api/plot/validate.py::validate_plan`)
3. Cap and distinctness — final union ≤8; distinct carrier-sets; `opposition` non-empty. Non-emptiness is a shape check (`gate_checks_shape_not_substance` acknowledged); opposition *substance* is judged in the raw read, not by the gate
4. Id stability — regeneration preserves ids for persisting threads; drops listed with reasons; waiver/ledger references checked against current set. **No-op on first run** (empty `story/thread/`); its RED test uses a fixture prior-set, not the first Floodmark run

All gates run persist-then-fail: `story/` artifacts are written before the verdict (evidence before verdict), for threads and throughlines alike.

**Throughline acceptance:** every major character has ≥1 slack point or a cited "arc is taut" claim; zero-delta throughline for a major character fails the gate but the artifact is persisted; every entry cites an event id.

## Acceptance Criteria

- [x] `Thread` + `Throughline` schemas in `schema/story.py`; gates in `nodes/thread_gates.py` with RED-first tests per gate (id-stability RED uses a fixture prior-set)
- [x] `story/threads_1a.yaml`, `story/thread/*.yaml`, `story/throughline/*.yaml` generated for Floodmark canon
- [x] All four thread gates pass on the final union (8 threads, at cap); throughline criteria pass or produce persisted-artifact failures
- [x] **1a/1b diff read in FR review** (raw read, no similarity metric — `metric_archaeology_before_reading_output`): documented verdict on how much plot the entity fields add, feeding FR-696's go/no-go
- [x] Tests tagged `@pytest.mark.req("REQ-YG-530")`; new `capabilities/CAP-194-novel-fandom-plot-threads.yaml` with REQ-YG-530; changelog fragment; run proof committed as `story/` artifacts

## Deviations from Judged Plan

1. **ID reassignment.** The FR body cites `REQ-YG-524` / `CAP-189`; both were already taken when enforcement began. Actual IDs used: **`REQ-YG-530` / `CAP-194`**. No semantic change — the requirement text is as judged.
2. **Ledger walk — one raise, many releases.** The judged gate ported `validate_plan`'s balanced raise/release model. The Floodmark acceptance run condemned it: `hilde_gunnar_feud` opens once (`dawn_raid`) and de-escalates over four releases. Fixed under a condemning test (`test_one_raise_many_releases_passes`) to require *a* prior raise by sequence for each release, not one raise per release.
3. **Distinctness keys on `(kind, carriers)`.** The judged gate keyed distinctness on carrier-set alone; the run condemned it by rejecting `ledge_survival` as a duplicate of `hilde_gunnar_feud` (same two carriers, different conflict). Fixed under `test_same_carriers_different_kind_passes`.
4. **Latent-mining shortfall (open, routed to prompt fix).** The reconcile prompt under-mined: all 8 threads closed, `sources`/`justification` empty on grounded threads, and `young_men_grievance` unmined despite being in the prompt design. Diagnosed in the 1a/1b read below; scoped as a prompt-only FR-691 review amendment blocking FR-692/693 (gates and schemas are correct).

## Alternatives Considered

- **Extract threads from full canon in one pass** — loses the 1a/1b diff diagnostic and re-mines downstream what entered at the synopsis boundary.
- **Throughlines only (original plan v1)** — character slice cannot see de-escalation; rejected in plan revision.

## Related

- Plan: docs/plan-novel-fandom-story-pipeline.md
- Diary: diary-2026-07-05-vertical-depth-horizontal-silence.md, diary-2026-07-06-the-synopsis-that-de-escalates.md, diary-2026-07-06-the-dropped-plot-layer.md
- Ancestors: `langgraph-poc-narrator/src_novel/models/synopsis.py` (PlotThread), `dungeon_master/api/plot/validate.py` (affect closure)
- Blocks: FR-692, FR-693, FR-694; informs FR-696

## Judgement (2026-07-07)

**Verdict: APPROVED with amendments (folded into body above).**

1. **Cap made numeric.** "Cap applies to the final union" without a number is an unenforceable gate. Ruled: union ≤8, 1a ≤6, each latent admission justified by the canon field it was mined from. Reconcile ranks; the gate counts.
2. **Id-stability gate vacuity named.** On first run there is no prior set — the gate is a no-op and an honest RED test needs a fixture prior-set. Stating this prevents a fake-RED that passes trivially.
3. **Gates given one home.** Pure functions in `nodes/thread_gates.py`, called by both graph nodes and tests — one implementation, two callers; no drift between what the pipeline enforces and what CI proves.
4. **`ref_check` reference removed from gate 4.** Same ruling as FR-690: id resolution against a YAML set is arithmetic, not an LLM task.
5. **Measurement-FR clause examined and not applied.** The Sermon withholds authority from scorers/metrics until raw output is read. These gates are pass/fail invariant validators, not scorers — no aggregate number exists to hide behind. The substance check lives in the mandated 1a/1b diff read (AC 4), which is `read_raw_output_first` in its native form. Authority is therefore not withheld — but AC 4 is non-negotiable and blocks FR-696's Judgement.
6. **Schema placement:** new `schema/story.py` — derived artifacts are not canon; mixing them into `canon.py` would blur the plan's core distinction (canon grows, story/ regenerates).
7. **`threads_1a.yaml` persisted**, not discarded: the diff's left side must exist as an artifact or the FR-696 go/no-go verdict is unreviewable.

Scope frozen. Path is explicit and minimal. Authority granted, contingent on FR-690 merging first.

## 1a/1b Diff Read (2026-07-07, raw read of `story/threads_1a.yaml` vs `story/thread/*.yaml`)

**Verdict: entity fields DO add plot → FR-696 takes the Go branch** (genesis reordering must preserve a post-entity reconcile pass, not replace it with a single synopsis-time extraction).

Evidence — concrete details a generated dump would not produce:

1. **1b mined 3 threads 1a could not see**, each with a verifiable justification quoting the exact canon field: `gunnar_peacetime_identity` from gunnar.fears ("only useful as a fighter"), `heidrun_legacy` from heidrun.fears ("the old songs will die with her"), `reinmar_departure`. These are real plot — heidrun_legacy releases on `heidrun_dies`, a beat 1a's prose-level pass skipped entirely.
2. **Grounding worked but source citation didn't**: all 5 grounded threads carry `sources: []` and `justification: ''` — the reconcile prompt grounds raises/releases to event ids yet never fills `sources` for 1a-originated threads. Gate 1 passes because empty lists cite nothing false — shape passes, substance is missing.
3. **`conflict_dissolution_bias` reproduced inside the extractor**: all 8 threads are `status: released`; zero latent, zero open. The plan's own worked example — `young_men_grievance` from aschenwulf `internal_tensions` ("see her relationship with Gunnar as a betrayal of the dead") — was **not mined**, despite being quoted verbatim in the reconcile prompt's design. The miner found only threads it could close, and closed them. The deficit list that was to be FR-692/693's work queue is empty.
4. Substance wobble in grounding: `hilde_gunnar_feud` lists `clan_divide` as a *release* — in canon it is an escalation (of `community_peace`); the LLM bent the event's valence to fit the release column.

**Consequences:**
- FR-696: **Go** — canon fields contribute threads the synopsis lacks; reordering keeps the reconcile pass.
- FR-692/693 are **blocked on a reconcile prompt fix** (latent-mining hardening): the prompt must state that latent threads have empty `raises`/`releases` and `status: latent`, and that a mining pass returning zero latents against a canon with loaded `internal_tensions` is itself suspect. Also fix `sources` population for grounded threads. This is prompt-only — gates and schemas are correct — in scope as an FR-691 review amendment, not a new FR.
