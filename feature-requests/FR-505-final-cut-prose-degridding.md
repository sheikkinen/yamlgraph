# Feature Request: FR-505 — De-grid the Final Cut (the turn-grid transcription)

**Priority:** HIGH
**Type:** Bug fix (generation quality)
**Status:** Draft — awaiting judgement
**Effort:** ~1 day
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
Final Cut **every played turn recap in order** as `arc`. The
`final_cut.yaml` prompt *already* instructs the composer to "STATE EACH STANDING
FACT ONCE" and let "the turn boundaries dissolve into one flowing scene" — but
the model, handed N recaps that are each a `Hilde→Gunnar→Reinmar→Oda` quadruple,
**reproduces that quadruple N times.** The advisory instruction is not enough:
the input shape is a grid, and the composer transcribes the grid.

This is the **same lesson FR-503 taught one layer up** (Scripture:
`composition_bug`, "the bottleneck that moved"): an advisory prompt instruction
("don't skip ahead" / "dissolve the turns") cannot overcome a structural input
pressure. FR-503 fixed it with a *computed* anchor (the finite beat ledger); the
Final Cut needs an equivalent *structural* lever, not a stronger adjective.

## Proposed Solution (candidate approaches — Judge to select)

The goal: Final Cut prose where (a) each standing fact is stated once, (b) the
fixed cast round-robin is broken — characters drop out of paragraphs, actions
merge, sentence subjects vary — and (c) the climax carries disproportionate
weight. Three candidate levers, in increasing structural strength:

1. **Beat-keyed composition (recommended).** FR-503 already gives each chapter a
   finite, ordered `beats` list with which turns satisfied each. Re-key the Final
   Cut from *one paragraph per turn* to *one passage per beat*: feed the composer
   the beats as the spine, and the turn recaps grouped under the beat they
   advanced, with the climax beat marked. The prose is then organized by *what
   happened* (3–6 beats), not by *the turn grid* (16 round-robins). This reuses
   the FR-503 ledger as the de-gridding structure — the same "compute the rails"
   doctrine, applied to prose layout.

2. **Recap pre-compression.** Insert a pure or LLM step that collapses the
   per-turn round-robin recaps into a smaller set of varied event beats *before*
   the Final Cut sees them, so the composer never receives the grid. Weaker than
   (1) because it adds a stage rather than reusing existing structure.

3. **Prompt-only hardening.** Strengthen `final_cut.yaml` with an explicit
   anti-round-robin constraint ("do NOT open every paragraph with the same
   character; vary the sentence subject; let characters who did nothing
   significant drop out of a paragraph entirely"). Cheapest, but it is the
   *advisory* lever FR-503 proved insufficient — likely necessary but not
   sufficient on its own; pair it with (1).

The recommended path is **(1) + (3)**: re-key composition to the beat spine and
add the anti-round-robin prose constraint as reinforcement.

## Acceptance Criteria

- [ ] Final Cut composition is organized by the chapter's finite beats (FR-503),
      not one paragraph per turn; a pure test pins the beat→turns grouping handed
      to the composer.
- [ ] `final_cut.yaml` carries an explicit anti-round-robin constraint (vary the
      sentence subject; do not open consecutive paragraphs with the same
      character; let inactive characters drop out of a paragraph).
- [ ] **Structural witness (deterministic):** a regenerated Floodmark book on
      **azure** shows the round-robin rate drop — e.g. the fraction of body
      paragraphs whose clause-subjects are the full cast in fixed order falls
      below a stated threshold (measure on the 10005-BC baseline first to set it).
- [ ] **Reviewer witness (live):** the `book_reviewer` engagement mean rises above
      the 10005-BC baseline of `2.00`, and the located "nearly identical
      paragraphs / parallel construction" findings no longer dominate the per-
      chapter notes — recorded in this FR on enforce.
- [ ] DM unit suite green; the Final Cut still preserves every canonical beat
      (no beat dropped by the re-keying); a test pins beat-preservation.

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
