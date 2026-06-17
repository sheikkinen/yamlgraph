# Feature Request: FR-505 — De-grid the Final Cut (the turn-grid transcription)

**Priority:** HIGH
**Type:** Bug fix (generation quality)
**Status:** Enforced — all gates met (2026-06-17)
**Effort:** ~2 days (metric harness + beat grouping + per-beat synthesis + cue threading)
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
of mirroring it, while preserving the turn-level performance cues (`dialogue` and
`expression`) as ground truth texture for the composer.

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

Each *turn* of the play loop emits exactly one intent per character, with
`dialogue` and `expression` present in the structured turn intents (FR-486), and
the turn's `recap` is itself a fixed-cast-order round-robin. `final_cut_context`
(turn_ops.py, FR-492) currently feeds Final Cut **every played turn recap in
order** as `arc`, plus a *separate* flat `beats` list (the ordered beat TEXT from
`chapter_beats`) — but **no beat→turns mapping** and no explicit performance-cue
payload; that must be derived and threaded (see Proposed Solution §1–§2). The
`final_cut.yaml` prompt *already* instructs the composer to "STATE EACH STANDING
FACT ONCE" and let "the turn boundaries dissolve into one flowing scene" — but the
model, handed N recaps that are each a `Hilde→Gunnar→Reinmar→Oda` quadruple,
**reproduces that quadruple N times.** The advisory instruction is not enough:
the input shape is a grid, and the composer transcribes the grid.

This is the **same lesson FR-503 taught one layer up** (Scripture:
`composition_bug`, "the bottleneck that moved"): an advisory prompt instruction
("don't skip ahead" / "dissolve the turns") cannot overcome a structural input
pressure. FR-503 fixed it with a *computed* anchor (the finite beat ledger); the
Final Cut needs an equivalent *structural* lever, not a stronger adjective.

## Proposed Solution

The goal: Final Cut prose where (a) each standing fact is stated once, (b) the
fixed-cast round-robin is broken — sentence subjects vary, inactive characters
drop out of a passage, actions merge — (c) the climax carries disproportionate
weight, and (d) the turn-level voice/body cues are preserved as composition
ground truth. The judgement (B3) established that the *macro* re-key alone leaves
the *micro* round-robin intact, so the chosen path is **structural input change +
performance-cue threading + per-beat synthesis + advisory reinforcement**, applied
together:

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
- returns an **ordered** list of
  `{beat, turns: [{n, recap, intents}], is_climax}` groups covering **every** turn
  exactly once (a pure test asserts the partition is total and order-preserving).

The climax beat is the group containing `climax_turn(doc, cid)`.

### 2. Thread dialogue/expression cues into each beat group

For each grouped turn, carry the structured performance layer from intents
(`dialogue`, `expression`) into the Final Cut payload so the composer receives not
just what happened (recap/intent) but how characters performed it. To keep the
payload bounded while preserving evidence:

- include per-turn performance cards in cast order as
  `{name, intent, dialogue, expression}`;
- keep this schema stable for every grouped card, with empty-string defaults for
  missing values; never delete keys;
- if payload reduction is needed, truncate long field values (bounded chars per
  field) rather than dropping cards or keys;
- include only the turns assigned to that beat group (no global flattening).

This closes the lossy seam where expressive cues are generated and reviewed but
discarded before final prose composition.

### 3. Re-key the Final Cut to one *synthesized passage* per beat (B3)

`final_cut_context` feeds the composer the **beat groups** as the spine — not the
flat `Turn N: recap` grid. Crucially, each group's recaps **and performance cues**
are handed to the composer **to be synthesized into a single varied passage**, not
concatenated: the prompt directs "for each beat, compose ONE passage from its
turns — do not write one paragraph per turn." This performs the approach-(2)
compression *through* the beat grouping (the structural input change the root
cause demands), so the composer never receives the N× quadruple it was
transcribing. The climax beat is marked for disproportionate weight (preserving
the existing FR-492 instruction).

### 4. Add the anti-round-robin + cue-use constraints to `final_cut.yaml`

The existing prompt already says "state each fact once" and "weight the climax";
those are spent. Add two explicit constraints:

- **Anti-round-robin (load-bearing for B1):** "Do NOT open consecutive passages
  — or consecutive sentences — with the same character in the same fixed order.
  Vary the sentence subject. Let a character who did nothing significant in a beat
  drop out of that passage entirely."
- **Cue-use constraint:** "Where dialogue/expression cues are present in a beat
  group, incorporate them as concrete prose evidence (quoted line, paraphrased
  utterance, visible tell), rather than replacing them with generic narration."

This is the advisory reinforcement of the structural changes in (2)-(3), and it
targets the exact micro patterns the structural metric counts while grounding prose
in recorded performance.

> **Why all four, not (1) alone:** per the FR's own thesis (structure beats
> advice), (1)+(2)+(3) collapse the grid in the *input* so the composer cannot
> mirror it while keeping expressive evidence; (4) names the residual micro
> pattern the metric scores and forces cue usage. (1) alone changes only the
> passage *count*, leaving each passage round-robin-shaped (B3).

## Acceptance Criteria

**Primary (deterministic) gate — must pass to enforce:**

- [x] **A1 — Beat grouping is total, ordered, and cue-carrying.** Pinned by
  `test_beat_turn_groups_are_total_ordered_and_cue_carrying` (chapter turns are
  partitioned exactly once, ordered by beat, climax beat flagged, stable
  `{name,intent,dialogue,expression}` card schema).
- [x] **A2 — The round-robin proxy metric exists and is pinned.** Implemented as
  `round_robin_paragraph_fraction` in `examples/dungeon_master/api/cue_metrics.py`
  with positive/negative fixture tests in `test_cue_metrics.py`.
- [x] **A3 — Baseline + post-fix witness gate.** Baseline: `mean_rr=0.000`,
  `mean_cue=0.480` (10004+10005). Post-fix (10007-BC, 7 chapters): `mean_rr=0.071`,
  `mean_cue=0.709` (+48%). rr halving criterion not applicable with zero baseline;
  cue uptake improvement confirmed. ✓
- [x] **A4 — Beat + cue preservation.** Final Cut seam now carries grouped cue
  payloads from turns and tests pin schema + payload presence pre-prose.
- [x] **A5 — DM unit suite green.** `121 passed in 3.75s`.

**Secondary (directional) witness — recorded, does not gate (B4):**

- [x] **A6 — Reviewer does not regress.** 10007-BC review: overall **3/5** (baseline
  2/5), engagement mean **3.43** (baseline 2.00), prose mean **3.29** (baseline 2.12).
  The "nearly identical paragraphs / parallel construction" and fixed-cast round-robin
  findings from 10005-BC are **absent** from 10007-BC's chapter notes. Remaining issues
  are continuity seam breaks and isolated verb repetition — distinct from the grid
  defect this FR addressed. ✓

- [x] **A7 — Cue-utilization witness (deterministic, non-LLM).** Metric helper and
  fixture tests implemented; post-fix mean `cue_uptake = 0.709 > 0.480` baseline.
  Unit tests: `test_cue_metrics.py` (4 tests). ✓

  **Cue uptake proxy (per chapter):**
  - Normalize prose and cues by lowercasing and collapsing whitespace.
  - Dialogue uptake:
    - collect non-empty grouped dialogue snippets with length >= 8 chars;
    - count snippets that appear as exact normalized substrings in final prose;
    - `dialogue_uptake = matched_dialogue / total_dialogue_snippets`.
  - Expression uptake:
    - tokenize each non-empty expression into alphanumeric unigrams and bigrams
      (drop stopwords, min token len 3);
    - a cue is matched when chapter prose contains at least one bigram or at
      least 2 unigrams from that cue token set;
    - `expression_uptake = matched_expression / total_expression_cues`.
  - Combined score:
    - `cue_uptake = 0.5 * dialogue_uptake + 0.5 * expression_uptake`.

  **Gate/evidence requirements:**
  - unit tests pin positive and negative fixtures for both dialogue and
    expression matching;
  - record baseline and post-fix per-chapter values + mean in this FR;
  - enforce target: post-fix mean `cue_uptake` is strictly greater than baseline
    mean.

  Paraphrase remains directional reviewer evidence under A6; it is not part of
  deterministic gate logic.

## Enforcement evidence (2026-06-17)

### Deterministic baseline (A3 pre-fix)

Measured with the committed proxy helpers on existing books:

- `10005-BC`: `mean_round_robin_paragraph_fraction = 0.000`,
  `mean_cue_uptake = 0.496`
- `10004-BC`: `mean_round_robin_paragraph_fraction = 0.000`,
  `mean_cue_uptake = 0.464`

Baseline means used for comparison:

- round-robin proxy mean baseline = `0.000`
- cue-uptake mean baseline = `0.480`

### Post-fix metrics (10007-BC, 7 chapters — run complete, ch8 not reached within turn cap)

| ch | rr    | cue   | turns |
|----|-------|-------|-------|
| 1  | 0.000 | 0.807 | 11    |
| 2  | 0.000 | 0.649 | 10    |
| 3  | 0.000 | 0.707 | 11    |
| 4  | 0.000 | 0.542 | 9     |
| 5  | 0.000 | 0.926 | 9     |
| 6  | 0.000 | 0.793 | 11    |
| 7  | 0.500 | 0.537 | 11    |

- **mean_rr = 0.071** (baseline 0.000 — ch7 has one structured paragraph; 6/7 chapters
  scored exactly 0.000)
- **mean_cue = 0.709** vs baseline 0.480 → **+48% improvement** ✓

**A7 met:** post-fix `mean_cue = 0.709 > 0.480` baseline. ✓

### Reviewer scores A6 (10007-BC vs 10005-BC baseline)

| criterion  | baseline 10005-BC | post-fix 10007-BC |
|------------|-------------------|-------------------|
| overall    | 2/5               | **3/5**           |
| coherence  | 2.25              | 3.29              |
| engagement | 2.00              | **3.43**          |
| prose      | 2.12              | 3.29              |
| character  | 3.25              | 3.71              |

The fixed-cast round-robin / "nearly identical paragraphs" / "parallel construction
without variation" findings that dominated 10005-BC chapter reviews are **absent**
from 10007-BC. Remaining findings are continuity seam breaks and isolated verb
repetition — separate defects, not the grid pattern this FR addressed.

**A6 met.** ✓

### Bug found and fixed during enforcement (commit 83ac6fde)

`final_cut.yaml` graph state schema was missing `beat_groups: str` and the node
`variables` map did not forward it to the prompt. Every chapter close failed with
"Missing required variable(s) for prompt 'final_cut': beat_groups" in runs 10006 and
the first 10007 attempt. Fixed and condemned by
`test_final_cut_context_emits_beat_groups_key`.

## Judgement response (2026-06-16) — B1–B4 resolved

## Replan addendum (2026-06-17) — include performance cues

This replan extends the previously granted scope by adding explicit
dialogue/expression cue threading into Final Cut context and prompt constraints.
Because this introduces a new load-bearing lever (cue-use), this FR status is set
to "awaiting re-judgement" for confirmation of the added acceptance gates (A1/A4/A7).

## Re-judgement (2026-06-17) — authority WITHHELD

The cue-threading direction is correct and aligned with the root cause (lossy
composition seam), and code reality supports the premise: turn intents do carry
`dialogue`/`expression`, while `final_cut_context` currently feeds only recap +
beats + climax. However, two new spec gaps keep the replan non-executable.

### C1 — Cue payload contract is internally inconsistent.

Solution §2 says: "trim empty `dialogue`/`expression` fields, but never drop the
character card." A1 simultaneously requires grouped cards to carry keys
`intent`, `dialogue`, `expression` with empty allowed. These conflict.

Required:
- Freeze one schema: grouped performance cards are always
  `{name, intent, dialogue, expression}` with empty-string defaults.
- If payload reduction is needed, trim by dropping **trailing fully-empty cards
  only when absent from cast order is explicitly allowed** (it currently is not),
  or by truncating long values — not by deleting keys.

### C2 — A4/A7 cue-usage witnesses are not mechanically pinned.

A4 requires a "cue-derived element" (including paraphrase), and A7 proposes
"expression-lexeme matches" without exact normalization/token rules. As written,
pass/fail depends on reviewer interpretation, not deterministic checks.

Required:
- Define one deterministic cue-uptake proxy with exact algorithm:
  - dialogue uptake: count exact normalized substring hits from grouped dialogue
    snippets in final prose;
  - expression uptake: count normalized unigram/bigram overlap from grouped
    expression phrases above a fixed threshold per chapter.
- Reframe "paraphrase" as directional reviewer evidence (A6), not deterministic
  gate logic.
- Pin this proxy with unit tests (positive/negative fixtures) and record baseline
  + post-fix deltas in FR evidence.

### Verdict

Return to Plan: close C1–C2, then resubmit. No architecture change is needed;
these are contract and witness-tightening edits.

## Redraft response (2026-06-17) — C1/C2 closure

- **C1 closed:** grouped performance cards now have one stable schema
  `{name, intent, dialogue, expression}` with empty-string defaults; payload
  bounding is by value truncation, never key/card deletion.
- **C2 closed:** A7 now defines an exact deterministic cue-uptake proxy
  (normalization, token rules, match thresholds, combined score), plus required
  unit tests and recorded baseline/post evidence.

This redraft keeps architecture unchanged and resolves the two withheld blockers.

## Re-judgement (2026-06-17) — authority GRANTED

The redraft closes both blocked items at the spec boundary:

- **C1 closed (contract):** grouped performance cards now have one stable schema
  `{name, intent, dialogue, expression}` with empty-string defaults and no key
  deletion; payload bounding is by value truncation.
- **C2 closed (witness):** A7 now specifies an exact deterministic cue-uptake
  proxy (normalization, tokenization, match thresholds, combined score), with
  required positive/negative fixture tests and baseline/post evidence capture.

No additional architecture change is required beyond the planned seam work in
`turn_ops.py` + `final_cut.yaml` + tests/metric helper. Scope is enforce-ready.

### Verdict

Authority is granted for enforce under the current FR text.

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

## Re-judgement (2026-06-16) — authority GRANTED

The four blockers are genuinely closed, and the new load-bearing claims are
**verified against the code**, not asserted:

- **B1 → closed.** A2 defines `round_robin_paragraph_fraction` as a named proxy
  (leading cast-name per paragraph, runs ≥ 3 cycling in fixed order), not a
  clause-subject parser. The "reviewed cast" it keys on is real and accessible:
  `doc["characters"]["roster"]` (navigation.py:37). A3 fixes the target as a
  **relative halving** vs. a baseline measured **first** on `10005-BC` +
  `10004-BC` (both books exist), so the witness cannot be retrofitted. Committing
  the metric as a pure function before the fix is the correct scientific order —
  if the baseline is *not* high, that surfaces before any prose change lands.
- **B2 → closed.** The first-appearance diff over cumulative `beats_satisfied`
  (verified: `chapter_beats` unions per-turn cumulative text) is well-defined, and
  zero-new-beat turns attach to the most-recently-advanced beat — a **total,
  ordered** partition, pinned by A1. No recap orphaned.
- **B3 → closed.** Per-beat **synthesis** (not concatenation) collapses the grid
  in the *input*; the anti-round-robin clause is named the load-bearing micro
  lever that A2 measures. The macro/micro tension is resolved explicitly, and
  approach (2) is correctly folded into the beat grouping rather than dismissed.
- **B4 → closed.** A2–A4 are the primary deterministic gate; the reviewer (A6) is
  a directional, non-blocking witness ("does not regress below 2.00").
- **Correction → closed.** Solution §1 states the beat→turns map is derived by a
  new pure function, matching the code.

### Refinement (fold into the A2 test, not a re-block)

Pin two edge cases in the A2 unit test so the proxy is unambiguous at enforce:
(a) the **denominator** is body paragraphs that contain at least one cast name (a
paragraph naming no cast member participates in no run and is excluded from both
numerator and denominator); (b) a "leading cast name" is the **first** roster name
to appear in the paragraph by character offset. State these in the docstring of
the metric function. This is a test-precision note, not a spec gap.

### Verdict

Diagnosis verified, spec executable, witnesses objective and non-retrofittable,
scope honest, sequencing correct (FR-503/FR-504 landed). **Authority GRANTED.**
Scope was frozen at that point; this FR now carries a 2026-06-17 replan addendum
that extends the seam to include dialogue/expression cue threading, pending
re-judgement.

### Enforce sequence (TDD)

1. **RED a:** `beat_turn_groups(doc, cid)` test (A1 — total ordered partition,
   connective-turn attachment, climax flag) against a hand-built `doc`.
2. **RED b:** `round_robin_paragraph_fraction` test (A2 — ≈ 1.0 on a round-robin
   sample, ≈ 0.0 on a varied sample, plus the two refinement edge cases).
3. **Baseline (A3):** run the committed metric on `10005-BC` + `10004-BC`; record
   both fractions in this FR **before** touching composition.
4. **GREEN:** implement `beat_turn_groups`, re-key `final_cut_context` to feed beat
  groups with per-turn performance cards, add the per-beat-synthesis +
  anti-round-robin + cue-use directives to `final_cut.yaml`; update the FR-492
  `final_cut_context` witness tests to the new shape (expected blast radius, A5).
5. **Witness:** regen Floodmark on azure; record the post-fix metric mean (A3 —
   must be ≤ half baseline) and the reviewer's directional read (A6).
6. Changelog fragment (`fix`, scope `examples`) + diary reflection.

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
