# Feature Request: FR-505 — De-grid the Final Cut (the turn-grid transcription)

**Priority:** HIGH
**Type:** Bug fix (generation quality)
**Status:** Redrafted — B1–B4 resolved; awaiting re-judgement (2026-06-16)
**Effort:** ~1.5 days (metric harness + beat grouping + per-beat synthesis)
**Requested:** 2026-06-16

## Summary

FR-503 fixed the **plot axis** (chapters now escalate to `resolved`; the FR-501
cap dropped from a 4/6 majority to a 2/8 minority on the azure Floodmark regen).
But the `book_reviewer` verdict barely moved — engagement `1.83 → 2.00`, overall
still `2/5`, continuity still `1/5`. An independent prose audit of the witness
book (`outputs/dungeon-master/10005-BC/story.md`) confirmed *why*, and confirmed
the reviewer is an accurate oracle, not a hallucinating one: **the Final Cut prose
transcribes the turn grid one-to-one.** Every paragraph marches the same cast in
the same fixed order — `Hilde → Gunnar → Reinmar → Oda`, one clause each — for
~6 paragraphs per chapter. The bottleneck FR-503 unblocked simply **moved one
layer downstream**, from the director's phase stall to the composer's prose shape.

This FR makes the Final Cut **dissolve** the turn grid into varied prose instead
of mirroring it.

## Problem

### The evidence (independent prose audit, witness 10005-BC)

The `book_reviewer` (anthropic `claude-haiku-4-5`, FR-497) scored 10005-BC `2/5`
overall, `1/5` continuity, engagement mean `2.00`. Reading the actual prose, the
reviewer's three sharpest Chapter 1 findings are **all true** (verified against
the text, not taken on faith):

1. *"Paragraphs 3–6 are nearly identical repetitions… the same four-character
   sequence repeats verbatim."* Confirmed: every Ch1 body paragraph is
   `Hilde [weapon action] → Gunnar [cover/watch] → Reinmar [haul survivor] →
   Oda [staff gesture]`, one clause each, ~6× running.
2. *"Arnulf… is a placeholder, not a character"* — he appears only as "Arnulf was
   with Hilde's band" / "Arnulf stayed with Hilde's band" / "Arnulf yielded that
   step." Confirmed.
3. *"Syntactically monotonous… parallel construction without variation."*
   Confirmed verbatim.

The reviewer is **working as supposed** — its located, quoted findings are
grounded in the text. The defect it names is real and is in the Final Cut prose.

### The mechanism (why the composer mirrors the grid)

Each *turn* of the play loop emits exactly one intent per character, and the
turn's `recap` is itself a fixed-cast-order round-robin (FR-486: every reviewed
character acts every turn). `final_cut_context` (turn_ops.py, FR-492) feeds the
Final Cut **every played turn recap in order** as `arc`, plus a *separate* flat
`beats` list (the ordered beat TEXT from `chapter_beats`) — but **no beat→turns
mapping**; that must be derived (see Proposed Solution §1). The `final_cut.yaml`
prompt *already* instructs the composer to "STATE EACH STANDING FACT ONCE" and let
"the turn boundaries dissolve into one flowing scene" — but the model, handed N
recaps that are each a `Hilde→Gunnar→Reinmar→Oda` quadruple, **reproduces that
quadruple N times.** The advisory instruction is not enough: the input shape is a
grid, and the composer transcribes the grid.

This is the **same lesson FR-503 taught one layer up** (Scripture:
`composition_bug`, "the bottleneck that moved"): an advisory prompt instruction
("don't skip ahead" / "dissolve the turns") cannot overcome a structural input
pressure. FR-503 fixed it with a *computed* anchor (the finite beat ledger); the
Final Cut needs an equivalent *structural* lever, not a stronger adjective.

## Proposed Solution

The goal: Final Cut prose where (a) each standing fact is stated once, (b) the
fixed-cast round-robin is broken — sentence subjects vary, inactive characters
drop out of a passage, actions merge — and (c) the climax carries disproportionate
weight. The judgement (B3) established that the *macro* re-key alone leaves the
*micro* round-robin intact, so the chosen path is **structural input change +
per-beat synthesis + advisory reinforcement**, applied together:

### 1. Derive the beat→turns grouping (new pure function)

The FR-503 ledger records, per turn, the **cumulative** `beats_satisfied` (beat
TEXT). It does **not** already carry a beat→turns map — that must be computed.
Add a pure function in `turn_ops.py` (e.g. `beat_turn_groups(doc, cid)`) that:

- walks the chapter's turns in order, diffing each turn's cumulative
  `beats_satisfied` against the prior turn's to find the **beats first satisfied
  on this turn** (first-appearance diff);
- assigns each turn to the beat(s) it first advanced; **a turn that advances no
  new beat (connective/zero-beat turn) attaches to the most-recently-advanced
  beat** so its recap is never orphaned (resolves B2 — "compose, do not omit");
- returns an **ordered** list of `{beat, turns: [recaps], is_climax}` groups
  covering **every** turn exactly once (a pure test asserts the partition is total
  and order-preserving).

The climax beat is the group containing `climax_turn(doc, cid)`.

### 2. Re-key the Final Cut to one *synthesized passage* per beat (B3)

`final_cut_context` feeds the composer the **beat groups** as the spine — not the
flat `Turn N: recap` grid. Crucially, each group's per-turn recaps are handed to
the composer **to be synthesized into a single varied passage**, not concatenated:
the prompt directs "for each beat, compose ONE passage from its turns — do not
write one paragraph per turn." This performs the approach-(2) compression *through*
the beat grouping (the structural input change the root cause demands), so the
composer never receives the N× quadruple it was transcribing. The climax beat is
marked for disproportionate weight (preserving the existing FR-492 instruction).

### 3. Add the anti-round-robin constraint to `final_cut.yaml` (the B1 lever)

The existing prompt already says "state each fact once" and "weight the climax";
those are spent. Add the **load-bearing** micro constraint that the B1 metric
measures: "Do NOT open consecutive passages — or consecutive sentences — with the
same character in the same fixed order. Vary the sentence subject. Let a character
who did nothing significant in a beat drop out of that passage entirely." This is
the advisory reinforcement of the structural change in (2), and it targets exactly
the pattern the structural metric (B1) counts.

> **Why all three, not (1) alone:** per the FR's own thesis (structure beats
> advice), (1)+(2) collapse the grid in the *input* so the composer cannot mirror
> it; (3) names the residual micro pattern the metric scores. (1) alone changes
> only the passage *count*, leaving each passage round-robin-shaped (B3).

## Acceptance Criteria

**Primary (deterministic) gate — must pass to enforce:**

- [ ] **A1 — Beat grouping is total and ordered.** A pure test pins
      `beat_turn_groups(doc, cid)`: every chapter turn appears in exactly one
      group, groups are beat-order-preserving, zero-new-beat turns attach to the
      most-recently-advanced beat, and the climax group is flagged. No turn recap
      is orphaned (B2).
- [ ] **A2 — The round-robin proxy metric exists and is pinned.** Commit a pure
      function (e.g. `scripts/round_robin_metric.py` or under the example) that,
      given a chapter's prose, computes `round_robin_paragraph_fraction`: split on
      blank-line paragraphs; for each paragraph take the **leading proper noun
      restricted to the chapter's reviewed cast** (the first cast name to appear);
      find maximal runs of ≥ 3 consecutive paragraphs whose leading cast-names
      cycle through the same fixed order; report `covered_paragraphs / body_
      paragraphs`. It is a **named proxy**, not a clause-subject parser. A unit
      test pins it on a hand-built round-robin sample (≈ 1.0) and a varied sample
      (≈ 0.0).
- [ ] **A3 — Baseline recorded before any fix.** Run A2 on the existing
      `10005-BC` **and** `10004-BC` books and record both fractions **in this FR**
      before the composition change lands. The target is a **relative drop**: the
      mean `round_robin_paragraph_fraction` on a post-fix azure regen is **at
      least halved** vs. the pre-fix baseline mean. No absolute threshold chosen
      after seeing results (B1).
- [ ] **A4 — Beat preservation.** Every canonical beat (`chapter_beats`) is still
      recognisable in the re-keyed cut — the re-keying drops no beat; a test pins
      that each beat group contributes to the composed prose.
- [ ] **A5 — DM unit suite green.**

**Secondary (directional) witness — recorded, does not gate (B4):**

- [ ] **A6 — Reviewer does not regress.** On the post-fix azure regen, the
      `book_reviewer` engagement mean **does not fall below** the `10005-BC`
      baseline of `2.00`, and the located "nearly-identical paragraphs / parallel
      construction" findings **no longer dominate** the per-chapter notes.
      Recorded in this FR on enforce as a directional signal — enforce is **not**
      blocked on an LLM score crossing a hard threshold.

## Judgement response (2026-06-16) — B1–B4 resolved

- **B1 (metric under-specified)** → A2 defines the exact `round_robin_paragraph_
  fraction` proxy (leading cast-name, runs ≥ 3, fixed-order cycle), names it a
  proxy not a parser, commits it as a pure function **first**, and A3 fixes the
  target as a **relative halving** vs. a baseline recorded before the fix.
- **B2 (orphaned connective turns)** → Solution §1 + A1: zero-new-beat turns
  attach to the most-recently-advanced beat; the partition is total and tested.
- **B3 (macro vs. micro)** → Solution §2–§3: each beat group is **synthesized into
  one varied passage** (input-level grid collapse), and the anti-round-robin
  clause is the load-bearing micro lever that A2 measures — not a count change
  alone. Approach (2) is no longer "weaker"; per-beat synthesis *is* it.
- **B4 (reviewer as gate)** → A2–A4 are the **primary deterministic gate**; the
  reviewer (A6) is a **directional, non-blocking** witness.
- **Correction (overstated mapping)** → Solution §1 now states plainly the
  beat→turns map is **derived** by a new pure function, not pre-existing.

## Judgement (2026-06-16) — authority WITHHELD

The root cause is **validated, not asserted**: I confirmed against the code that
`final_cut_context` (turn_ops.py) feeds the composer a flat `Turn N [phase]:
recap` list (`arc`) plus a *separate* flat `beats` list, and that `final_cut.yaml`
*already* carries both "state each standing fact once" and "weight the climax" —
so the advisory levers the FR says are insufficient are indeed already spent. The
diagnosis (grid in → grid out) and the FR-503 lesson it invokes are sound, and the
sequencing (after FR-503/FR-504, both landed) is correct. **But the spec is not
yet executable.** Four blockers must be closed before authority is granted; the
cheapest bug is the one killed here.

### B1 — The "deterministic" structural metric is under-specified.

AC3 measures "the fraction of body paragraphs whose **clause-subjects** are the
full cast in fixed order." Extracting clause subjects from prose is **not
deterministic** without a parser — the word "deterministic" hides real NLP
difficulty, and an unpinned metric means *enforce* cannot objectively pass/fail.
Required before enforce:
- Define the **exact proxy** computation (e.g. take each body paragraph's leading
  proper noun restricted to the chapter's reviewed cast; count runs of ≥ k
  consecutive paragraphs whose leading cast-names cycle through the same fixed
  order; report `round_robin_paragraph_fraction`). Name it a proxy, not
  "clause-subjects."
- Commit the measurement as a small `scripts/`-level pure function **first**, and
  record the **baseline** on *both* `10005-BC` and the just-generated `10004-BC`
  before any fix lands.
- State the target as a **relative drop** (e.g. round-robin-paragraph fraction at
  least halved vs. baseline), never an absolute number chosen after seeing the
  result. The witness must not be retrofittable.

### B2 — Connective / zero-beat turns are unaccounted for in beat-keyed grouping.

`beats_satisfied` is **cumulative** per turn (FR-503 ledger): a turn may advance
zero new beats (pure connective turns) or several at once. "One passage per beat,
fed the turn recaps grouped under the beat they advanced" silently has no home for
a turn that advanced **no new beat** — its recap content would be **dropped**,
violating the composer's own "compose, do not invent **or omit**" law and risking
lost continuity. Required: specify the grouping rule explicitly (e.g. a turn
attaches to the latest beat whose first-appearance it triggered; a zero-new-beat
turn attaches to the most-recently-advanced beat, or an explicit `between-beats`
bucket rendered as connective tissue) and pin it with the AC1 pure test. No turn's
recap may be orphaned.

### B3 — Approach (1) attacks the *macro* axis; the named root cause is *micro*.

The reviewer's actual complaint is micro: *every body paragraph opens*
`Hilde→Gunnar→Reinmar→Oda`. Re-keying 16 turns → 3–6 beat passages changes the
organizing axis and the **count**, but the recaps grouped **under each beat are
still round-robin-shaped** — so without more, each of the 3–6 passages still opens
Hilde→Gunnar→Reinmar→Oda and the reviewer's exact finding survives at lower count.
By the FR's **own thesis** (structure beats advice), the lever that addresses the
named cause is collapsing the grid *in the input*. Resolve the tension explicitly:
the beat-keyed re-key must hand the composer each beat's grouped recaps **with the
instruction to synthesize them into a single varied passage** (a lightweight
approach-(2) compression performed *by* the beat grouping), not to concatenate
per-turn recaps. State plainly that (3)'s anti-round-robin clause is the
**load-bearing** lever for the metric in B1, and that B1 measures exactly that
micro pattern. (This also retires the FR's dismissal of approach (2) as merely
"weaker" — per-beat synthesis *is* the structural input change the root cause
demands.)

### B4 — The reviewer witness is a *secondary, directional* signal, not a gate.

AC4's hard `engagement > 2.00` gates the FR on a single azure regen scored by a
noisy LLM oracle — FR-503 moved this metric only `1.83 → 2.00` for an entire plot
fix, so reviewer variance alone could pass or fail it. Make the **deterministic**
metric (B1) the **primary** gate; downgrade AC4 to a directional secondary witness:
"engagement does not regress vs. the 2.00 baseline, and the located
'nearly-identical paragraphs / parallel construction' findings no longer dominate
the per-chapter notes," recorded on enforce. Do not block enforce on an LLM score
crossing a hard threshold.

### Correction (not a blocker)

The Summary's "FR-503 already gives each chapter a finite, ordered `beats` list
**with which turns satisfied each**" overstates: the ordered beat list exists
(`chapter_beats`), but the **beat→turns mapping is not assembled** — it must be
derived as a new pure function from the per-turn cumulative `beats_satisfied`
(first-appearance diff). AC1 already implies this; state it as an explicit work
item so the effort estimate is honest.

### Verdict

Diagnosis sound, sequencing correct, scope honest. **Return to Plan:** close
B1–B4 (and the correction) in this FR, then resubmit for judgement. The path to
GRANT is short — these are spec sharpenings, not redesigns.

## Notes / Scope

- Single example (`examples/dungeon_master/`), FR-474 J3 regime: no CAP file, no
  `@pytest.mark.req` markers, honest `fix(dungeon-master): FR-505 …` commits with
  an `FR-474 J3` trailer, a changelog fragment, and a diary reflection.
- **Out of scope:** the per-turn play loop's own round-robin (every character
  acting every turn is FR-486 by design — the fix is at the *composition* seam,
  not by silencing characters mid-play); book-level revision passes; FR-502
  resume; the `closed_by` degradation flag (FR-501 Seed).
- This FR depends on FR-503 (the finite beat ledger is the de-gridding spine) and
  should land after FR-504 (which removes the free-text fallback, so every chapter
  reliably carries the beats this FR keys on).

## References

- FR-503 — finite beat ledger (the structure this FR re-keys the prose to)
- FR-504 — retire the free-text fallback (guarantees every chapter carries beats)
- FR-497 — `book_reviewer` (the oracle, validated as accurate against 10005-BC)
- FR-492 — `final_cut_context` / the Final Cut composer (the seam this FR changes)
- FR-486 — per-turn performance cards (the round-robin source, out of scope here)
- Witness: `outputs/dungeon-master/10005-BC/story.md` (the transcription evidence)
- Scripture: `composition_bug`; "the bottleneck that moved" (advisory instruction
  cannot overcome a structural input pressure — FR-503's lesson, one layer down)
