# Feature Request: FR-603 L7 Hope-Emission Discrimination

**Priority:** MEDIUM
**Type:** Enhancement (prompt/classifier) — classifier change, frozen gate untouched
**Status:** CLOSED — cue REFUTED (over-emits hope, regresses FR-601 (c); effect within
temp-0.7 noise floor). Investigation kept; prompt reverted. (2026-06-26)
**Effort:** ~0.5 day (read + prompt clarification + spike re-run; one corpus pass)
**Requested:** 2026-06-26
**REQ:** REQ-YG-020 (reuse — no new CAP)
**Predecessor:** FR-599 (probe), FR-600 (GT re-anchoring), FR-601 (close-op kind cue),
FR-602 (gate-tolerance experiment — ruled out the beat-off lever)
**Gate (frozen, untouched):** FR-578 `affect_recall` (`main_l7` in `evaluate.py`)
**Lever this FR pulls:** hope emission — multi-affect-beat cap and/or hope-open
discrimination in `affect_throughline.yaml` — explicitly **NOT** model scale

## Summary

The post-FR-602 L7 residual is dominated by one cause: of 22 misses, **14 are (a) ABSENT**,
and the deterministic ABSENT decomposition (`--absent` mode,
`fixtures/affect-licensing/l7-absent-decomposition.md`) proves **14/14 are PROMPTABLE — 0
unperceived**. There is no detection floor in this corpus; scale would buy nothing. The
residual has a sharp single-kind cluster: **`hope` = 8 of 14 (57%)**, skewed `open`. On
every one of those beats the model engages the right character on or near the beat but does
not emit the hope arc. This FR closes that gap — but only after a read names which of two
candidate mechanisms dominates.

## Value Statement

The model already perceives the character and the beat at every absent-hope moment; naming
the in-reach hope arc converts the single largest, cheapest share of the recall floor (57%
of the residual) without touching the frozen ruler or buying a larger model.

## Judgement (2026-06-26)

**Verdict: Authority GRANTED, with three corrections.** This is the strongest FR of the
arc: it refuses scale on *committed evidence* (0/14 unperceived — there is no detection
floor to buy), names two structurally-grounded mechanisms instead of one guess, and
hard-gates the prompt edit behind a mechanical read. The committed decomposition file also
honours the FR-602 cross-cutting correction — the tally is now a durable artifact, not a
console line.

**I verified every load-bearing claim against the prompt and the committed evidence:**
the cap is real (`affect_throughline.yaml` line 45, "At most one operation per beat");
the FR-601 close-op cue actively steers away from hope (lines 64–65: "a triumph that
regains what was lost **closes loss (not opens hope)**; a solemn vindication **closes hope
(not opens loss)**") — so mechanism (2) is not speculative, the prompt textually suppresses
hope-opens; and the evidence file confirms 14/14 promptable, `hope` 8/14, op skew open:8 /
close:6, with detective `F8` (close hidden_blessing + close hope) and scifi `F9` (open
hope + close hope + open retaliation) as genuine multi-delta beats.

1. **The cap relaxation (mechanism 1) re-opens the FR-598 invention-engine door — gate it
   hardest (PRIMARY).** "At most one operation per beat" and "do not open a feeling because
   you expect it to close later" (lines 45–48) are the *anti-invention guardrails* installed
   after FR-598. Relaxing the cap has **corpus-wide** blast radius — every beat, not just
   hope. If mechanism 1 is chosen, the relaxation must be minimal ("two only when the text
   plainly shows two distinct feelings"), the precision guard must be a **hard,
   disqualifying gate** (not advisory), and the before/after must report `affect_precision`
   on **all kinds**, not just hope — because the cap touches every beat, a hope recall gain
   that quietly inflates loss/guilt/retaliation emission elsewhere is a net loss disguised
   as a win.

2. **Pre-commit the "dominant" decision rule and the both-material tie-break BEFORE the
   read (PRIMARY).** I can already see in the committed evidence that *both* mechanisms are
   materially present among the 8 hope absents — multi-delta beats (detective F8, scifi F9)
   are cap-blocked candidates; single open-hope beats (detective F5 "Pell agrees to
   testify", historical F3 "Naima decides to go", quest F4) are hope-open-missed candidates
   — so "fix whichever dominates" most likely faces a near-tie, not a clear winner. Define
   the threshold now (e.g. dominant = ≥6/8; else both material) and the tie rule: if both
   are material, write the **hope-open cue (mechanism 2) first**, because it is hope-scoped
   and low-blast-radius, whereas the cap relaxation is corpus-wide and reverts an FR-598
   guardrail. Don't let a near-tie produce an ad-hoc post-read decision.

3. **Not all 8 hope absents are equally recoverable — exclude the open+close-same-kind-
   same-beat pairs from the success denominator (secondary).** scifi `F9` wants BOTH `open
   Mara hope` AND `close Mara hope` on one beat (hope flares then dies: "for a moment he is
   himself … then he steps back"). Emitting open *and* close of the same kind for the same
   char on one beat is a fine distinction a beat-grounded classifier may legitimately not
   make — and forcing it to chase recall is exactly the over-emission the precision guard
   exists to catch. Treat these as a separate, possibly-irreducible sub-class (or an
   FR-600-style licensing question), and state the *recoverable*-hope denominator
   explicitly, so the cue is not judged a failure for missing an annotation no grounded
   model should emit.

**On the FR-601 reconciliation (endorsed, reinforced):** the open/close contradiction is
real on contested beats (quest F6 "the temple is theirs", detective F8) — the reconciliation
("close names what RESOLVES a tracked arc; open names what BEGINS a forward-looking belief;
a rich beat may do both") must be demonstrated on those specific beats in the before/after,
not merely asserted in prose, and the `--kindwrong` re-run must show FR-601's (c) gain does
not regress.

**Endorsed:** scale holstered on evidence, read-first hard gate, no bundling
(`mixed_commits_erode_auditability`), evaluator-loosening correctly refused (FR-602 settled
it), FR-601 not reverted but extended, frozen `main_l7` untouched, REQ-YG-020 reuse, no new
CAP.

**Frozen scope:** extend `probe_l7_misses.py --absent` (read-only) to carry per absent-hope
member the GT delta count on the beat and the model's exact-beat emission, classify each
`cap_blocked` vs `hope_open_missed`, re-commit the evidence; read the 8 and apply the
pre-committed dominance/tie rule; write the single chosen minimal cue (cap relaxation hard-
guarded on all-kind precision, OR hope-open cue reconciled with FR-601); deterministic
before/after showing ABSENT falls and recoverable-hope recall rises with no all-kind
precision regression and no FR-601 (c) regression. One lever this FR; the other is a
follow-up only if a material hope residual survives.

## Enforcement Outcome (2026-06-26) — CLOSED, cue REFUTED

Enforced faithfully through the frozen scope; the cue was built, measured against the hard
ACs, and **did not survive the (c) gate**. The prompt is reverted; the investigation
(probe + evidence) is kept.

**Hard gates 1 & 2 (PASSED):** `probe_l7_misses.py --absent` was extended to classify each
hope ABSENT member `cap_blocked` / `hope_open_missed` / `irreducible` from the GT delta
count and the model's exact-beat emission, and the evidence was re-committed
(`4eed2dab`). The read returned a **3–3 near-tie** (cap_blocked 3, hope_open_missed 3,
irreducible 2 → recoverable 6; neither ≥ 6), exactly as the Judge foresaw. The
pre-committed tie rule fired → **hope-open cue (mechanism 2) first**.

**The cue (written, then reverted):** an OPEN-OP HOPE block in `affect_throughline.yaml`
mirroring the FR-601 close-op cue — hope opens on a beat whose words give forward-looking
belief; name it for the character who *gains* the belief, not the deliverer; open only when
the text shows it (over-emission guard); reconciled as the OPEN mirror of the close cue.

**Validation (spike re-runs, claude-haiku-4-5, temp 0.7) — the cue trades (c) for hope:**

| metric | no-cue (n=4, incl. pinned) | with-cue (n=3) | shift |
|--------|----------------------------|----------------|-------|
| `affect_recall` (gate) | {5,6,7,7} mean 6.25 | {6,7,8} mean 7.0 | +0.75 (within 5–7 noise) |
| `affect_precision` | {0.11,0.12,0.16,0.16} | {0.12,0.15,0.15} | flat |
| **(c) kind-wrong** | {3,3,4,6} mean 4.0 | {5,5,7} mean 5.67 | **+1.67 — REGRESSES FR-601** |
| hope-recoverable (lower=better) | {3,4,5,6} mean 4.5 | {1,3,3} mean 2.33 | −2.17 (recovers ~2 hope) |

The mechanism is coherent, not noise: the cue makes the model **paint hope onto more beats**
— some land on GT hope (recovers ~2) but ~1.7 land on wrong-kind beats (the (c) regression).
This is the exact **hope over-emission** the precision guard exists to catch. The gate's
recall benefit (+0.75) sits *within* the no-cue noise band, while the (c) cost is consistent.
**AC violated:** "the FR-601 (c) close-op gain does NOT regress." The cue does not ship.

**Second, larger finding (drives the successor):** the single-pass per-character effects are
**at or below the temp-0.7 noise floor** on the 28-delta corpus — `(c)` alone swings 3→6
with no prompt change. The deterministic probe reports exact counts on **one stochastic
draw**, manufacturing false confidence about ~1-delta levers. Refining the single-pass cue
is chasing sub-noise. The real mechanism behind the misses (the one-op-per-beat cap + 6-way
kind competition) is **structural**, not textual: hope loses because it shares one budget
with five louder kinds. The next lever is therefore **map-over-kinds extraction** (one
focused pass per kind, dissolving the cap and the competition — guarded against the FR-598
invention engine), and/or **enlarging the corpus / dropping temperature** so a 1–2 delta
effect is resolvable at all. Tracked as the FR-604 candidate.

**Disposition:** CLOSED. Prompt reverted (no `OPEN-OP HOPE` in `affect_throughline.yaml`);
frozen `main_l7` untouched (empty diff); committed evidence reproduces from the pinned
baseline (empty diff); REQ-YG-020 reused, no new CAP. Deliverables kept: the hope-mechanism
decomposition (`4eed2dab`) and this refuted-lever record.

## Problem

`hope` is licensed at rescue / relief / vindication / turning-point beats — "belief that
things can yet be made right." Two structural causes are plausible, and they call for
*different* fixes:

1. **One-op-per-beat cap (multi-affect beats).** The classifier prompt commands "At most
   one operation per beat," but the ground truth places *multiple* affect deltas on rich
   climactic beats. Examples in the absent set: detective `F8` wants BOTH `close
   hidden_blessing` AND `close hope`; scifi `F9` wants `open hope`, `close hope`, AND `open
   retaliation` on one beat. When the model obeys the cap and emits one delta, every
   *additional* GT delta on that beat is ABSENT by construction — and hope, as the
   forward-looking second feeling, is the one most often dropped. This lever is a **cap
   relaxation** (allow a beat to carry more than one affect when its text plainly shows
   more than one), not a kind cue.

2. **Hope-open suppression, possibly induced by the FR-601 close-op cue.** FR-601 taught the
   model that "a triumph that regains what was lost **closes loss** (not opens hope)" and "a
   solemn vindication **closes hope** (not opens loss)." That cue is correct for the beats it
   targets, but it may over-generalise: an upturn that the corpus authors as *opening* a new
   forward-looking hope arc could now be read as merely *closing* the prior negative,
   suppressing the hope `open`. The absent set skews `open` (8 opens), which is consistent
   with this. This lever is a **discrimination cue**: an upturn can OPEN hope as a new arc,
   distinct from closing the fall that preceded it — without reviving the FR-598 invention
   engine (ground the open in the beat's own forward-looking words).

These are not mutually exclusive; the read must report the split.

## Raw Output Read (REQUIRED — this FR changes the classifier)

`read_raw_output_first`: no prompt edit until the 8 absent-hope members are read from the
committed evidence and each is assigned to mechanism (1) or (2), and the dominant mechanism
is **named from the read, not guessed** (the FR-601 hard-gate discipline).

- **Samples read:** `examples/plot_modeller/fixtures/affect-licensing/l7-absent-decomposition.md`
  (committed `83798483`) — the 14 ABSENT members with perception class, op, kind, and beat
  position; reproduce with `probe_l7_misses.py --absent`.
- **What I saw (to be completed before any edit):** for each of the 8 `hope` members, does
  the model already emit a DIFFERENT delta on the exact beat (→ mechanism 1, a second delta
  the cap forbids) or does it emit nothing for that character on the beat while engaging it
  nearby (→ mechanism 2, hope-open suppressed)? The extended probe must carry, per
  absent-hope member, **how many GT deltas the beat holds** and **what the model emitted on
  that exact beat**, so the (1)-vs-(2) split is mechanical, not impressionistic.

Preliminary signal (to be confirmed by the read): detective `F8` and scifi `F9` are
multi-delta beats (mechanism 1); detective `F5` and historical `F3` are single open-hope
beats (mechanism 2). Both mechanisms appear present; the read decides which cue to write
first and whether one suffices.

## Proposed Solution

Gated on the read. **Pre-committed dominance/tie rule (correction 2, fixed BEFORE the read):**
let `cap_blocked` and `hope_open_missed` be the two member counts over the *recoverable* hope
absents (correction 3 denominator, below).

- **Dominant = a mechanism with ≥ 6 of the recoverable members.** Fix that one only.
- **Otherwise (near-tie, both material):** write the **hope-open cue (mechanism 2) first**,
  because it is hope-scoped and low-blast-radius, whereas the cap relaxation is corpus-wide
  and reverts an FR-598 guardrail. The cap relaxation becomes a follow-up FR only if a
  material hope residual survives.

**Recoverable-hope denominator (correction 3):** any hope absent that is an
open+close-of-the-same-kind-on-the-same-beat pair (e.g. scifi `F9` wants BOTH `open Mara
hope` AND `close Mara hope` on one beat) is an irreducible distinction a beat-grounded
classifier may legitimately not make. These are excluded from the success denominator and
reported as a separate `irreducible` sub-class — the cue is NOT judged a failure for missing
them.

- **If the hope-open cue (mechanism 2) is chosen:** add a discrimination cue — an upturn that
  gives a character forward-looking belief OPENS hope as a new arc, even on a beat that also
  closes a prior fall; opening hope and closing loss are not mutually exclusive. Reconcile
  explicitly with the FR-601 close-op cue so the two do not contradict (the close cue names
  what RESOLVES a tracked arc; the open cue names what BEGINS a forward-looking belief — a
  single rich beat may do both). The reconciliation MUST be demonstrated on the specific
  contested beats (quest `F6`, detective `F8`) in the before/after, not merely asserted.

- **If the cap relaxation (mechanism 1) is chosen:** relax "At most one operation per beat"
  to "Emit one operation per feeling the beat's text plainly shows; most beats show none,
  some show one, a few climactic beats show two — only when the text plainly shows two
  distinct feelings." Keep default-NONE and ground-in-the-text rules intact (no invention
  engine). Because the cap touches EVERY beat (corpus-wide blast radius, correction 1), the
  precision guard is a **hard disqualifying gate** and the before/after MUST report
  `affect_precision` on **all kinds**, not just hope — a hope recall gain that inflates
  loss/guilt/retaliation emission elsewhere is a net loss disguised as a win.

Validate the same deterministic way as FR-601: spike re-run, then recount on the
re-annotated GT showing (a) ABSENT falls and recoverable-`hope` recall rises, with **no
all-kind `affect_precision` regression** (over-emission guard) and **no destabilisation of
the FR-601 close-op gains** (re-run `--kindwrong`; (c) must not rise).

## Acceptance Criteria

- [ ] **(Hard gate, FIRST)** `probe_l7_misses.py --absent` is extended (read-only, frozen
      gate untouched) to carry, per absent-hope member, the GT delta COUNT on the beat and
      the model's EXACT-BEAT emission, and to classify each member mechanically as
      `cap_blocked` (model emitted a different delta on the exact beat → mechanism 1),
      `hope_open_missed` (model emitted nothing for the character on the beat → mechanism 2),
      or `irreducible` (the beat wants open+close of the SAME kind for the SAME char —
      correction 3, excluded from the recoverable denominator). The extended evidence is
      re-committed to `fixtures/affect-licensing/l7-absent-decomposition.md`.
- [ ] **(Hard gate, depends on above)** The recoverable hope absents are read from the
      extended evidence and the lever is selected by the **pre-committed dominance/tie rule**
      (dominant = ≥6 of recoverable; else near-tie → hope-open cue first) — named from the
      printed `cap_blocked` / `hope_open_missed` / `irreducible` split, not guessed, before
      any prompt edit.
- [ ] The chosen prompt change is minimal and grounded: default-NONE and text-grounding
      rules intact; no revival of the FR-598 "close every open" invention engine.
- [ ] **(If hope-open cue)** explicitly reconciled with the FR-601 close-op cue
      (open-names-what-begins vs close-names-what-resolves; a rich beat may do both), and the
      reconciliation is DEMONSTRATED on quest `F6` and detective `F8` in the before/after.
- [ ] **(If cap relaxation — correction 1)** the relaxation is minimal ("two only when the
      text plainly shows two distinct feelings"); the precision guard is a **hard
      disqualifying gate**; the before/after reports `affect_precision` on **all kinds**, not
      just hope.
- [ ] Deterministic before/after on the re-annotated GT: (a) ABSENT falls and
      **recoverable**-`hope` recall rises; **all-kind** `affect_precision` does NOT regress;
      the FR-601 (c) close-op gain does NOT regress (`--kindwrong` re-run).
- [ ] Frozen `main_l7` untouched (verified by diff). No new CAP; REQ-YG-020 reused.
      Changelog fragment + diary reflection.

## Alternatives Considered

- **Jump straight to model scale.** Refuted by the evidence: 0/14 ABSENT are unperceived,
  so scale addresses nothing in this corpus. Scale stays holstered until a future corpus
  shows a real detection floor.
- **Write both cues at once (cap relaxation + hope-open).** Refuted: bundling two prompt
  levers destroys attribution — you could not tell which moved the number
  (`mixed_commits_erode_auditability`). Read first, fix the dominant one, measure, then
  decide if the second is needed.
- **Broaden the matcher to forgive the missing hope (evaluator change).** Refuted by FR-602:
  the gate is correctly strict; the miss is a real model omission, not a ruler artifact.
- **Revert or weaken the FR-601 close-op cue to free up hope opens.** Refuted: FR-601's
  (c) 4→1 gain is real; the fix is to *add* the open-hope distinction, not subtract the
  close discrimination. Reconcile, do not regress.

## Related

- Evidence: `examples/plot_modeller/fixtures/affect-licensing/l7-absent-decomposition.md`
- Probe: `examples/plot_modeller/probe_l7_misses.py` (`--absent`, `--kindwrong`, `--sweep`)
- Classifier prompt: `examples/plot_modeller/prompts/affect_throughline.yaml`
- Frozen gate: `examples/plot_modeller/evaluate.py` (`main_l7`, `_l7_counts`)
- Predecessors: FR-599, FR-600, FR-601, FR-602
