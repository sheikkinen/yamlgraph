# Feature Request: FR-604 L7 Per-Kind Detection with Protagonist Focus

**Priority:** HIGH
**Type:** Enhancement (classifier architecture) — spike + prompt change, frozen gate untouched
**Status:** CLOSED — arm B (6-kind sweep) REFUTED as specified (precision 0.243 < arm A
0.375 while recall rose +0.107; the frozen revert rule fires). Arm A char-pinning KEPT as a
finding (precision 0.12->0.375). Investigation + harness kept; production single pass never
touched. 4-kind support-gated variant = FR-605 candidate. (2026-06-26)
**Effort:** ~1 day (per-kind spike harness + 6 narrow detector prompts + one corpus pass, recall+precision both read)
**Requested:** 2026-06-26
**REQ:** REQ-YG-020 (reuse — no new CAP)
**Predecessor:** FR-598 (single-pass collapse that killed the invention engine), FR-599
(probe), FR-600 (GT re-anchoring), FR-601 (close-op kind cue), FR-602 (gate-tolerance
ruled out), FR-603 (hope-open cue REFUTED — over-emission, sub-noise; named this lever
"structural, not textual")
**Gate (frozen, untouched):** FR-578 `affect_recall` (`main_l7` in `evaluate.py`)
**Lever this FR pulls:** decompose the six-kind, one-op-per-beat single pass into **six
narrow per-kind detectors fixed to the focal protagonist**, removing the cap and the 6-way
kind competition — explicitly **NOT** model scale (FR-603 proved 0/14 unperceived)

## Summary

L7 sits at **recall 6/28 (0.21) — KILL**, precision **6/49 (0.12)**. The FR-596→603 arc
established by committed evidence that the residual is not a detection floor (scale buys
nothing) and not a single missing cue (FR-603's hope-open cue was refuted: it bought recall
by over-emission, below the temp-0.7 noise floor). Two structural causes remain, and a
direct read of the quest 0/4 isolates both:

1. **The one-op-per-beat cap forfeits 25% of the recall ceiling.** 7 of 28 GT deltas are the
   2nd+ delta on a multi-affect beat (6 such beats). Single-pass recall is mathematically
   capped at **21/28 = 0.75** — only ~0.05 above the 0.70 GO line, so the cap makes GO
   *fragile* (any single misread drops below it), not impossible (J: correction 3).
2. **Wrong-feeler attribution destroys precision and steals recall.** The model detects the
   right affect on the right beat with the right kind+op, then binds it to the wrong
   character (hope at F4 → the ferryman who *gives* aid, not the protagonist who receives it).

This FR decomposes the single pass into **six narrow detectors, one abstract kind at a time,
each fixed to the focal protagonist** — removing the cap (each kind gets its own budget) and
the cross-character noise (char is pinned, not chosen) — while preserving the FR-598
invention guard as a hard precision floor.

## Value Statement

Narrowing the model's task from "juggle six abstract feelings across the whole cast under a
one-delta budget" to "find this one feeling, for this one character, where the text plainly
shows it" lifts the recall ceiling from 0.75 to 1.0 and removes the wrong-feeler poison that
floors precision at 0.12 — the first lever in the arc aimed at a *structural* cause rather
than a prompt phrase.

## Judgement (2026-06-26)

**Verdict: Authority GRANTED, with three corrections.** This is the correct escalation:
the arc has earned the move from prompt-wording to architecture by *exhausting* the cheaper
levers on committed evidence — FR-602 ruled out beat tolerance, FR-603's cue was REFUTED for
over-emission, and the `--absent` decomposition proved 0/14 unperceived (scale buys
nothing). The Raw Output Read is genuine: I reproduced every number against the files —
cap-forfeit **7/28 = 0.25** (6 multi-delta beats), the GT distribution (kinds
hope9/loss9/guilt5/betrayal3/hidden_blessing1/retaliation1; chars Marren7/Naima5/Brynn4/
Eira4/Mara8 = 28), the quest wrong-feeler reads (F4 hope→Ferryman Ossa, F6 hope→Thane Gault
who just drowned, F8 guilt→misread loss, plus Queen Livia / Usurper Kael spray), and
FR-603's **CLOSED — REFUTED** status. Char-pinning is legitimate, not cheating: the GT is
protagonist-anchored and `_classify_agent` already produces a per-agent cell — the 0.12
precision is a *merged-roster* artifact (non-protagonist deltas are false positives by
construction). Three corrections bind the grant.

1. **The FR bundles three structural levers — add a char-pinned single-pass control arm so
   the gain is attributable, and make it the baseline (PRIMARY).** This FR changes three
   things at once — cap removal, char-pinning, and per-kind decomposition — the exact
   `mixed_commits_erode_auditability` trap it invokes against FR-603's bundling. Char-pinning
   (scoring the protagonist cell instead of the merged roster) is nearly free and almost
   certainly recovers most of the precision on its own; it can be measured by simply
   re-scoring the *existing* prediction restricted to the protagonist char — no re-run, no
   new prompt. Add **arm A** (single-pass, protagonist-cell-scored, cap intact) and report
   recall AND precision for it. The six-detector sweep (**arm B**) must then justify its 6×
   call cost by its **marginal** lift over arm A, not over the unpinned 0.12/0.21 baseline.

2. **The precision guard must compare against arm A, not the merged-roster 0.12 (PRIMARY).**
   Because char-pinning recovers precision regardless of decomposition, benchmarking arm B's
   precision against 0.12 flatters it — it would claim credit for char-pinning's win. The
   ≥0.40 floor is also asserted, not derived: tie it to arm A (a REVISE-recall result whose
   precision is below arm A's protagonist-cell precision is not progress), and harden the
   over-emission defence. Removing the cap AND the 6-way kind competition *together* is the
   **maximal over-emission configuration** — those two were the suppressors that kept the
   FR-598 invention engine down, and FR-603 showed even a single cue floods. So: keep each
   detector's "most beats emit nothing for this kind" bar hard and exemplar-backed, and if
   the guard fails, the verdict must report **per-kind precision** (which detector flooded),
   not just the aggregate.

3. **Factual: the 0.75 ceiling is ABOVE the 0.70 GO line, not "at or below" (secondary).**
   The cap caps recall at 21/28 = 0.75, which leaves only ~0.05 of headroom over GO — so the
   cap makes GO *fragile* (any misread drops below it), not mathematically impossible. Fix
   the phrasing; the structural claim (the cap forfeits 25% of the ceiling) stands and is
   verified.

**Endorsed:** scale refused on committed evidence (0/14 unperceived), the ≥3-draw temp-0.7
noise-floor discipline (the FR-603 lesson correctly inherited — no single-draw claims), the
FR-598 invention guard preserved as a hard precision floor, frozen `main_l7` byte-identical,
fork-not-delete the single pass until the spike wins, REQ-YG-020 reuse, no new CAP. One
note, non-blocking: a six-call-per-agent architecture carries a real production latency/cost
multiplier — if the spike wins, weigh that in the productionization FR.

**Frozen scope:** the `spike_affect_per_kind.py` harness + per-kind detector prompt(s),
reporting **arm A (char-pinned single pass)** and **arm B (per-kind sweep)** over ≥3 draws
with recall AND per-kind precision, the quest F6 double-close recovered as a named hit, no
non-protagonist deltas in the scored cell, and a GO/REVISE/REFUTED verdict attributing the
lift to the decomposition's margin over arm A. Frozen gate untouched; if arm B's precision
falls below arm A while recall rises, the per-kind architecture is REFUTED and reverted
(FR-603 precedent).

## Enforcement Outcome (2026-06-26) — CLOSED, arm B REFUTED (precision), arm A KEPT

Enforced through the frozen scope with the three folded corrections. The frozen gate
(`evaluate.py`) and the production single pass (`affect_throughline.yaml`) are byte-identical
(empty diff); arm B writes to the gitignored `results/l7_perkind/`, never the pinned baseline.

### Arm A — char-pinned single pass (the honest baseline; J corrections 1 & 2)

Re-scoring the EXISTING predictions restricted to the focal protagonist (no LLM):

| metric | merged roster | **arm A (char-pinned)** |
|---|---|---|
| recall | 6/28 = 0.214 | 6/28 = **0.214** (unchanged — pinning cannot move recall) |
| precision | 6/49 = 0.122 | 6/16 = **0.375** |

The 0.12 precision was a merged-roster artifact, exactly as judged. **Char-pinning is a free,
clean precision win (0.12->0.375) and a keeper finding** independent of the per-kind question.
It is the benchmark arm B must beat — not 0.12.

### Arm B — per-kind sweep (3 draws @ temp 0.7; near-zero variance)

| draw | recall | precision | multi-recovered | nonprot |
|---|---|---|---|---|
| 1 | 9/28 = 0.321 | 9/37 = 0.243 | [] | 0 |
| 2 | 9/28 = 0.321 | 9/37 = 0.243 | [] | 0 |
| 3 | 9/28 = 0.321 | 9/37 = 0.243 | [] | 0 |

Recall **mean 0.321, band [0.321, 0.321]** (+0.107 margin over arm A — a *real*, noise-free
recall lift, 6->9 hits). Precision **mean 0.243, band [0.243, 0.243]** — **below the arm A
0.375 floor while recall rose**, so the frozen revert rule fires: **arm B (6-kind) is
REFUTED.**

### Per-kind precision names the flooded detectors (J correction 2)

| kind | precision | GT support |
|---|---|---|
| hope | 18/30 = **0.60** | 9 |
| betrayal | 3/9 = 0.33 | 3 |
| guilt | 3/12 = 0.25 | 5 |
| loss | 3/15 = 0.20 | 9 |
| **retaliation** | 0/18 = **0.00** | 1 |
| **hidden_blessing** | 0/27 = **0.00** | 1 |

**100% of the precision violation is the two minimal-support detectors.** retaliation and
hidden_blessing emit 18 and 27 corpus deltas against a GT support of 1 each — pure FR-598
invention engines, exactly the maximal-over-emission risk the Judge flagged. Removing the cap
AND the six-way competition dropped both suppressors that had held them down.

### Two findings that survive the refutation

1. **The wrong-feeler bug is FIXED.** Quest now emits `F4 open hope Eira` (was `Ferryman
   Ossa`) — char-pinning plus the receiver-anchored hope exemplar ("the hope is the
   RECEIVER's, not the giver's") binds the feeling correctly. `nonprot = 0` every draw: no
   supporting-character deltas reach the scored cell.
2. **The cap was NOT the binding constraint (refutes this FR's own cause #1).** `multi-recovered
   = []` every draw — the F6 `loss`+`hope` double-close is still missed even with the cap
   removed: the loss detector skips F6, and the hope detector closes at F8 (crown placement)
   instead of F6. The 25% ceiling forfeit was real arithmetic, but giving each kind its own
   budget did not convert it to recall, because the per-kind reading still misplaces *which
   beat* carries the close. The recall floor is a **beat-localization** problem, not a budget
   problem.

### Disposition

REFUTED as specified; production single pass untouched (fork-not-delete — nothing to revert).
The harness `spike_affect_per_kind.py` + detector prompt `affect_detect_kind.yaml` are KEPT as
the committed investigation (regression harness + FR-605 evidence), mirroring the FR-603 close.

### FR-605 candidate (measured from the same draws, free — not shipped here)

Dropping the two zero-support detectors (a **support-gated 4-kind sweep**) recomputes to
**precision 9/22 = 0.409 > arm A 0.375 (PASS), recall held at 0.321** (the rare kinds
contributed 0 hits). That clears the floor with the +0.107 recall intact — but it is a NEW
scope (which kinds to sweep, how to gate rare kinds) that needs its own judgement. It does NOT
address the beat-localization miss (finding 2), which is the larger remaining lever.

## Problem

The FR-578 gate rewards an **exact 5-tuple** (op + kind + char + symmetric toward) on the
**exact beat id**, against a **sparse, protagonist-only** ground truth (one feeler per genre:
Marren 7, Naima 5, Brynn 4, Eira 4, Mara 8 = 28 deltas; kinds hope 9, loss 9, guilt 5,
betrayal 3, hidden_blessing 1, retaliation 1; 14 open / 14 close). The current
`affect_throughline.yaml` runs ONE pass that must (a) pick among six abstract emotional
categories, (b) emit at most one op per beat, and (c) is invoked over the whole GT agent
roster and merged. Each of those three fights the gate:

- (b) makes 25% of GT mechanically unreachable;
- (c) sprays supporting-character deltas the protagonist-only gate scores as false positives;
- (a) forces a 6-way discrimination on one-line beat glosses, where subtle reframings
  collapse (placing the crown = guilt-close "earning one's place" misread as loss-close).

FR-603 proved a textual cue cannot move this — the effect is below the temp-0.7 noise floor
on the 28-delta corpus. The cause is the architecture of the pass, not its wording.

## Raw Output Read

<!-- read_raw_output_first: the quest 0/4 prediction file read end-to-end against GT. -->

- **Samples read:** `results/l7/quest-adventure-the-sunken-crown.yaml` (predicted) vs
  `fixtures/ground-truth/quest-adventure-the-sunken-crown.yaml` (GT), full delta lists; plus
  corpus-wide cap-forfeit tally over all five `fixtures/ground-truth/*.yaml`.
- **What I saw (each line is a real read, not a generated dump):**
  - GT wants `F4 open hope Eira`; the model emitted `F4 open hope **Ferryman Ossa**` — the
    correct beat, op, AND kind, bound to the character who *gives* the breathing charm
    instead of the protagonist who *receives* the hope. Wrong-feeler, not wrong-kind.
  - GT wants `F6 close hope Eira`; the model emitted `F6 close hope **Thane Gault** — a
    character who has just drowned on that beat`. Again right beat+op+kind, wrong feeler.
  - GT wants BOTH `F6 close loss Eira` AND `F6 close hope Eira` on one beat; the single-pass
    cap structurally forbids the second — the model never had a budget to emit it.
  - GT wants `F8 close guilt Eira→Queen Livia` (placing the crown = earning her place); the
    model read the surface ("gives away the crown") as `F8 close **loss** Eira` — a 6-way
    competition collapse a single-kind detector would not face.
  - Corpus tally: **7 of 28 GT deltas (25%) are the 2nd+ on a multi-affect beat** → the cap
    caps recall at 21/28 = 0.75 before any misread.

## Proposed Solution

The FR changes three things at once — cap removal, char-pinning, per-kind decomposition. To
keep the gain **attributable** (J: correction 1, the `mixed_commits_erode_auditability`
trap), measure two arms; arm A is the baseline arm B must beat at the margin.

### Arm A — char-pinned single pass (baseline, nearly free)

No new prompt, no re-run: re-score the **existing** `results/l7/<genre>.yaml` predictions
with predicted deltas **restricted to the focal protagonist char** (the single GT feeler per
genre), then run the frozen counts.

- Char-pinning cannot change recall (non-protagonist predictions never matched the
  protagonist-only GT anyway) — it isolates the **precision** win of dropping the
  merged-roster false positives. This is the honest precision baseline.
- Report arm A recall (expected ~0.21, unchanged) AND precision (expected to jump from the
  0.12 merged-roster artifact) — the number arm B is benchmarked against.

### Arm B — per-kind, protagonist-fixed sweep (the lever under test)

```
for kind in [loss, guilt, betrayal, retaliation, hidden_blessing, hope]:
    detector(kind, agent=protagonist, glosses) -> open/close deltas for THAT kind only
union(all six) -> agent throughline   # no per-beat cap; each kind has its own budget
score recall AND per-kind precision against protagonist GT
```

- **One abstract concept per call.** Each detector carries the full definition + the FR-601
  resolution signature + 2–3 concrete beat-text exemplars for that ONE kind — richer than the
  shared prompt could afford, with no competing kinds to blur it.
- **Char pinned, not chosen.** `char` is fixed to the focal protagonist (the GT feeler); the
  detector never attributes the feeling to a supporting character. This is the existing
  `_classify_agent` cell semantics — scored directly, not via the roster merge.
- **No cap.** F6's loss-close and hope-close both emit, from independent passes.
- **Maximal over-emission configuration — guard hard (J: correction 2).** Removing the cap
  AND the 6-way kind competition together drops *both* suppressors that held the FR-598
  invention engine down; FR-603 showed even a single cue floods. Each detector keeps the
  "most beats emit nothing for THIS kind; plain-text-grounded; never invent to complete an
  arc" bar, exemplar-backed. On a precision failure the verdict reports **per-kind**
  precision (which detector flooded), not just the aggregate.

arm B must justify its 6×-call cost by its **marginal** recall/precision lift over arm A, not
over the 0.12/0.21 merged-roster baseline (J: corrections 1 & 2).

New harness `spike_affect_per_kind.py` (sibling to `spike_affect.py`); new prompt(s) under
`prompts/` (one parameterised detector). The frozen `evaluate.py` / `main_l7` reads the
resulting merged results file unchanged.

## Acceptance Criteria

- [x] **Arm A baseline reported first.** Re-score the existing predictions char-pinned to the
      protagonist; record arm A recall (expected ~0.21) AND precision. This precision is the
      benchmark — NOT the 0.12 merged-roster number (J: corrections 1 & 2). **Met: recall
      0.214 (unchanged), precision 0.122→0.375.**
- [~] **Arm B recall lifts the gate verdict at the margin.** `main_l7` (frozen) on the
      per-kind results moves corpus `affect_recall` out of KILL (≥ 0.50), target REVISE→GO,
      measured as the **mean of ≥3 spike draws** at temp 0.7 (FR-603 noise-floor discipline:
      no single-draw claims), reported with its run-to-run band, AND the lift is stated as a
      **margin over arm A**, not over the merged-roster baseline. **Partial: recall lifted
      +0.107 (0.214→0.321, band [0.321,0.321]) — real and noise-free, but still KILL (<0.50).**
- [x] **Arm B precision does not fall below arm A (hard guard, maximal over-emission config).**
      Corpus `affect_precision` over the same ≥3 draws is **≥ arm A's precision** (the
      char-pinned benchmark, not 0.12). A recall gain bought by spraying is REFUTED, not
      shipped. On failure the verdict reports **per-kind** precision (which detector flooded).
      If arm B precision < arm A while recall rises, the per-kind architecture is REFUTED and
      reverted (FR-603 precedent). **Guard FIRED: precision 0.243 < arm A 0.375 → REFUTED;
      per-kind precision names retaliation (0/18) + hidden_blessing (0/27) as the floods.**
- [ ] **The cap-forfeited multi-affect beats are recovered.** At least the quest F6
      `loss`+`hope` double-close (and ≥1 other of the 6 multi-delta beats) scores as a hit —
      proving the cap removal, not just aggregate drift. **NOT met: multi-recovered [] every
      draw — the cap was not the binding constraint (beat-localization miss, finding 2).**
- [x] **Wrong-feeler poison removed.** No non-protagonist deltas appear in the scored cell
      (char pinned); the F4/F6 hope deltas, if emitted, are bound to the protagonist. **Met:
      nonprot 0 every draw; quest F4 hope now binds to Eira (was Ferryman Ossa).**
- [x] **Frozen gate byte-identical.** `git diff --stat examples/plot_modeller/evaluate.py`
      is empty; the change lives entirely in the spike harness + prompts. **Met (empty diff;
      production `affect_throughline.yaml` also untouched).**
- [x] Per-kind spike harness + detector prompt(s) added; ≥3-draw distributions logged to
      `logs/` and the verdict (attributing arm B's margin over arm A) recorded in this FR's
      Enforcement Outcome. **Met: `logs/fr604-arm-b-3draws.log` (gitignored), outcome above.**
- [x] Diary reflection added.

## Alternatives Considered

- **Single-pass cue tweaks (FR-601, FR-603).** Exhausted. FR-603 proved a textual cue moves
  recall below the noise floor while regressing kind-precision — the cause is architectural.
- **Relax the gate tolerance (FR-602).** Already ruled out — the beat-off lever does not
  explain the residual.
- **Buy a larger model.** Refused on committed evidence: FR-603's `--absent` decomposition
  proved 0/14 absent-hope beats are unperceived. There is no detection floor to buy.
- **One prompt that internally lists six kinds but lifts the cap.** Rejected: it removes the
  cap but keeps the 6-way competition and the abstract-overload the user named ("feelings are
  very abstract and hard for an LLM — analyze one at a time"). Separate calls are the point.
- **Extend GT to the full roster instead of pinning char.** Rejected: the GT is
  deliberately protagonist-anchored (the throughline feeler); pinning char to the gate's
  feeler is the aligned fix, not re-labelling 5× more ground truth.

## Related

- `examples/plot_modeller/prompts/affect_throughline.yaml` (current single pass — to be
  forked, not deleted, until the spike wins)
- `examples/plot_modeller/spike_affect.py` (`_classify_agent` cell semantics to reuse)
- `examples/plot_modeller/evaluate.py` (`main_l7`, `_l7_counts` — frozen gate)
- `examples/plot_modeller/fixtures/ground-truth/*.yaml` (protagonist-only GT)
- FR-603 close + `docs/diary/diary-2026-06-26-deterministic-precision-on-one-noisy-draw.md`
  (noise-floor discipline this FR's ACs inherit)
- Repo memory: `l7-affect-noise-floor-fr603.md`
