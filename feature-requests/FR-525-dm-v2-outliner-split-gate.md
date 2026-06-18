# Feature Request: FR-525 — DM v2: Outliner Split-Gate (Forbid Un-Playable Reversals in One Capped Chapter)

**Priority:** HIGH
**Type:** Bug (continuity defect, authored at planning time)
**Status:** **JUDGED — scope frozen, authorized for enforce (2026-06-18).** Boundary
corrected to the **whole-book partitioner** (`outline_chapters` + `chapter_outline.yaml`),
NOT a beat re-outline (J1); resolution frozen to **A1** prompt-constraint + deterministic
post-outline detector (J2); detector frozen as a pure summary-and-beat `reversal_pack_gap`
sibling of `beat_coverage_gap` (J3); deterministic gate corrected to the new detector, not
`beat_coverage_gap` (J4); reappearance handled by the EXISTING `CharacterLifecycle`
machinery once split — no new forward channel (J5). See Judgement below.
**Effort:** ~1 day
**Requested:** 2026-06-18

## Summary

The chapter outliner is told to *partition the whole synopsis: no gap, no overlap*
and to give each chapter a *3–6 beat contract the play loop drives toward and closes
when every one is satisfied*. But the play loop's real exit is
`chapter_should_close = scene_complete OR n >= 16` (FR-501). When the outliner packs
a **death-and-return reversal** — an actor removed *and* returned — into one chapter,
the 16-turn cap force-closes after the removal half, `close_chapter` faithfully
commits `status='dead'`, and the unplayed return beat becomes a **phantom promise the
chapter's own committed `world_state` contradicts**. The beat contract and the turn
cap silently disagree, and the cap wins. This FR makes the outliner **structurally
forbid** a same-chapter remove-and-return, killing the contradiction in the spec
before any turn is played (`spec_kill`, `the_one_law`).

## Value Statement

A reader stops hitting "the chapter said Arnulf would reappear alive, but he drowned
and the book treats him as dead from here on" — no chapter can promise a return its
own removal beat makes un-playable within the turn budget.

## Problem

Forensic root cause (proven by the FR-524 witness, not hypothesized):

- `chapter_ops.outline_chapters(doc)` (and the draft `expand_chapters()`) authors a
  chapter's beats as a *finite checklist the chapter is complete once all have
  happened*. The outliner has no model of the **16-turn budget**: it can pack two
  seam-crossing events (a removal AND a return) into a single chapter.
- The play loop closes a chapter at `scene_complete OR n >= 16` (FR-501,
  `/memories/repo/dm-play-loop-chapter-turn-budget.md`). A reversal needs both halves
  played; a chapter stuck realizing the removal half consumes the cap and force-closes.
- `close_chapter` then *correctly* commits the actor terminal (`dead`) from the played
  recaps. The return beat never played — it is dropped on the floor as a phantom the
  chapter's own ledger now contradicts.
- In `10024-BC` Ch3: summary promised a 5-beat reversal (Arnulf swept away → grief →
  **reappears alive** → demands blood → Hilde refuses); 16/16 turns played a single
  ledge scene realizing only beat 1; close committed Arnulf `status='dead'`; beat[3]
  "Arnulf reappears alive with a downstream group of refugees" is the phantom.

**This is the dual of the FR-501 runaway.** FR-501 bounded a chapter whose director
never says "done" (unbounded *above*). This is a chapter that promised *more than the
bound can play* (over-committed *within* the bound). Raising the cap re-opens the
runaway (FR-524 Candidate C, rejected); the cure is to **not author** a reversal that
needs two seam crossings in one capped chapter.

**This is distinct from FR-523.** FR-523 made the *next* chapter's beats state-aware
so a lethal beat is physically continuous with the carried position (a *bridge*
problem — add a beat). This is an *intra-chapter over-pack* problem (a *split*
problem — move beats to a later chapter). FR-523's re-outline faithfully reproduced
`10024-BC`'s packed reversal because its contract is to *cover the frozen summary* —
it cannot un-pack what the partitioner packed. The fix must act at the partitioner.

**The One Law (`the_one_law`).** Normalize at the boundary where the contradiction
enters — the **outliner** — not downstream in `close_chapter` (which commits a
*correct* death) or the director (which played a *valid* removal). The cheapest bug
is the one killed in the partition.

### Condemning evidence (RED, already committed)

`examples/dungeon_master/api/witness_metrics.py::beat_coverage_gap(doc, cid)` is a
pure deterministic witness (committed `c6f197a3`): it flags any beat that names an
actor the chapter's own committed `world_state` records terminal
(`_TERMINAL_STATUS_TOKENS`) while the beat promises their return/presence
(`_RETURN_PRESENCE_TOKENS`). On the real corpus it fires on `10024-BC` Ch3 **alone**,
clean on all 16 older books:

```
CH3: actor=Arnulf ledger='dead' beat[3]='Arnulf reappears alive with a downstream group of refugees'
TOTAL PHANTOM-PROMISE GAPS: 1
```

The fixture `tests/test_beat_coverage_gap.py` proves it deterministically
(`gap_count == 1`, non-vacuous removal-only negative control at `gap_count == 0`).
Driving the corpus scan (`scripts/scan_beat_gaps.py`) to **zero** is this FR's GREEN
target.

## Proposed Solution

Make the outliner **structurally unable** to emit a chapter whose beats both remove
an actor and return them. The contradiction is killed at authoring time; the witness
is the gate that proves it stays killed.

### Boundary of the change

- **Layer:** logic/planning (`chapter_ops` outliner + the `chapter_outline` prompt).
  No change to the director, `running_scene`, the turn loop, the 16-turn cap, or
  `close_chapter` — those are downstream and stay innocent (the death they commit is
  correct).
- **Trigger:** after `outline_chapters` / the re-outline returns, a **deterministic
  detector** (the witness's own token logic, applied to *beats* not committed state)
  rejects any chapter that both removes and returns the same actor.

### Detector (J-candidate — pure, reuses the witness tokens)

A pure helper in `witness_metrics` (or a sibling), reusing `_TERMINAL_STATUS_TOKENS`
and `_RETURN_PRESENCE_TOKENS` and the existing `_beat_names_actor`: a chapter's beats
are **over-packed** for actor `X` when some beat removes `X` (terminal token) AND a
later beat returns `X` (return token). This is a spec-time check on *beats*, distinct
from `beat_coverage_gap` which checks beats against *committed* state.

### Resolution strategy (the open design question for the Judge)

Two options; the Judge must freeze ONE:

- **A1 — Reject + constrained re-outline (LLM, non-deterministic).** On a hit, append
  a hard constraint to the outline prompt — *"a character removed in a chapter must
  not also return in that same chapter; defer the return to a later chapter"* — and
  re-invoke. Cheapest to build, but may loop; needs a bounded retry + raise (no silent
  fallback, Commandment 6).
- **A2 — Mechanical split (deterministic).** Split the offending chapter at the
  removal beat: the removal + preceding beats stay in chapter N; the return beat(s)
  migrate to a new chapter N+1; re-number the partition. Deterministic and gate-clean,
  but rewrites the LLM-authored partition and must preserve `title`/`summary` framing
  for both halves (interacts with `_planned_reappearance_chapter`'s title/summary scan).

**Recommendation to the Judge:** A1 as the primary (smallest change, keeps the LLM as
partition author) with a deterministic **assert-clean post-check** (the detector must
return zero after re-outline, else raise) so the non-determinism cannot leak a phantom
past the gate. A2 is the fallback if A1's retry proves flaky in live regen.

### Prompt change

`prompts/chapter_outline.yaml` gains a hard partition rule (paraphrased):

> A character removed from the story within a chapter (swept away, drowned, killed,
> lost) MUST NOT also return or reappear within that same chapter. If the synopsis
> calls for a character to be lost and later return, the loss and the return belong to
> DIFFERENT chapters — author the return as a beat of a later chapter.

## Acceptance Criteria

> **The deterministic gate is AC-1 (mocked-LLM unit) + AC-2 (corpus scan to zero).
> Live regen (AC-6) is corroboration, not a gate** — a fresh book is a fresh LLM roll
> (FR-522 instrument posture). Tests prove the constraint; the witness corroborates.

- [ ] **AC-1 (deterministic gate, mocked LLM).** With the outline graph stubbed to
  return an over-packed chapter (remove + return same actor), the detector fires and
  the resolution (A1 re-outline stub OR A2 split) yields a doc where
  `beat_coverage_gap` is clean for every chapter. **Negative control (non-vacuous):**
  a stub returning a removal-only chapter passes through unchanged (no spurious split /
  re-outline) — proving the detector measures the reversal, not any removal.
- [ ] **AC-2 (corpus regression).** `scripts/scan_beat_gaps.py` over a regenerated
  Floodmark book that previously over-packed (`10024-BC` lineage) returns
  `GRAND TOTAL PHANTOM-PROMISE BEATS: 0`; the 16 historically-clean books stay clean.
- [ ] **AC-3 (purity + write split).** The detector is pure (no `doc` mutation,
  asserted via deep-copy equality). For A1, `reoutline`/`outline` stay pure reads and
  the adapter writes. For A2, the split write lives only in the `doc_ops` adapter.
  Raises (no silent fallback) if resolution cannot clear the detector.
- [ ] **AC-4 (no downstream change).** Director, `running_scene`, turn loop, the
  FR-501 cap, `close_chapter`, FR-521 roster-drop, FR-523 re-outline, and
  `_clamp_lifecycle_reappearance_to_plan` are untouched; their tests stay green;
  `lint-imports` clean (no new cross-layer edge).
- [ ] **AC-5 (frozen-summary interaction).** If A2 is chosen, the split preserves each
  half's `title`/`summary` framing so `_planned_reappearance_chapter`'s title/summary
  scan and FR-523's frozen-summary contract remain coherent. If A1, the re-outlined
  beats stay within the frozen summary (FR-523 J4) — the constraint defers the return,
  it does not invent events outside the summary.
- [ ] **AC-6 (live corroboration, not a gate).** A regenerated Floodmark book shows the
  Arnulf loss and return in DIFFERENT chapters (matching the 16-older-book pattern,
  e.g. `10023-BC` `reappear_from=6`); `book_reviewer` no longer scores the Ch3 phantom
  return as a continuity break.
- [ ] **AC-7 (regime).** Example tests REQ-exempt (FR-474 J3); no CAP/REQ minted;
  changelog fragment `type: fix, scope: examples`, **no** `req:`. Commit subject
  carries `FR-525`; a diary entry accompanies the GREEN commit (diary-gate).
- [ ] `architecture.md` updated: the outliner forbids same-chapter remove-and-return;
  the `beat_coverage_gap` witness documented as the gate.

## Alternatives Considered

- **Re-weave the rolling synopsis (FR-524 as drafted) — REJECTED.** Re-weave reads
  *committed* memory where Arnulf is correctly dead; it cannot resurrect a beat the
  play never reached. It patches a downstream symptom, not the partition.
- **Beat-coverage-aware turn budget (FR-524 Candidate C) — REJECTED.** "Raise the cap
  until all beats play" re-opens the FR-501 runaway: a director stuck in one scene
  becomes unbounded again. The cap is load-bearing.
- **`close_chapter` open-thread promotion — DEFERRED to FR-526** as defense-in-depth,
  not a substitute: it converts a *missed* return into an owed thread, but the cleaner
  cure is to not author the un-playable reversal in the first place.

## Related

- `examples/dungeon_master/api/witness_metrics.py` — `beat_coverage_gap` (the gate)
- `examples/dungeon_master/api/chapter_ops.py` — `outline_chapters`, `expand_chapters`
- `examples/dungeon_master/prompts/chapter_outline.yaml` — the partition prompt
- `examples/dungeon_master/scripts/scan_beat_gaps.py` — corpus scanner
- `feature-requests/FR-501-*` — the 16-turn chapter cap (the bound this respects)
- `feature-requests/FR-523-dm-v2-state-aware-chapter-reoutline.md` — the bridge sibling
- `feature-requests/FR-524-dm-v2-synopsis-summary-reweave.md` — the rejected re-weave + investigation
- `feature-requests/FR-526-dm-v2-close-chapter-open-thread-promotion.md` — the defense-in-depth follow-up

## Judgement (2026-06-18)

Examined against the live code: `chapter_ops.outline_chapters` /
`reoutline_chapter_beats` / `_planned_reappearance_chapter` /
`_clamp_lifecycle_reappearance_to_plan`, `seam_packet.CharacterLifecycle`,
`witness_metrics.beat_coverage_gap`, `prompts/chapter_outline.yaml`,
`prompts/chapter_reoutline.yaml`, and `docs/architecture.md`. The defect and the
witness are sound; the **boundary and the resolution in the draft were both wrong**
and are corrected here. Scope frozen.

- **J1 — Boundary is the whole-book partitioner, NOT a beat re-outline.** The draft's
  Candidate A1 ("constrained re-outline") is **incoherent** against the live
  contracts. FR-523 FROZE each chapter's `title`/`summary`, and
  `prompts/chapter_reoutline.yaml` is bound to *"cover exactly the events the summary
  describes — no fewer, no more, nothing invented beyond it."* The over-pack
  originates in the **summary** itself: the whole-book partitioner authored Ch3's
  summary containing BOTH the removal ("swept away") and the return ("reappears
  alive"). A beat re-outline that must cover that summary is therefore *required* to
  emit the return beat — it is structurally unable to defer it. The pack must be split
  at the **summary author** = `outline_chapters` + `chapter_outline.yaml`. The beat
  layer (FR-523) is downstream and stays innocent.

- **J2 — Resolution frozen to A1 (prompt-constraint + post-outline detector); A2
  (mechanical split) deferred.** A2 must author TWO new summaries from one packed
  summary — itself an LLM task, not a deterministic string split — so it buys no
  determinism over A1 while adding partition-rewrite complexity. Freeze A1: add the
  hard partition rule to `chapter_outline.yaml` (a character removed within a chapter
  must not also return within that same chapter; defer the return to a LATER chapter),
  then run a deterministic post-outline detector; on a hit, re-invoke the outline with
  the constraint reinforced (bounded retry, e.g. 2), then RAISE (Commandment 6: no
  silent fallback). The retry bound + terminal raise is the load-bearing guard that
  the LLM non-determinism cannot leak a pack past the gate.

- **J3 — Detector frozen as a pure `reversal_pack_gap(card)` sibling, summary-AND-beat
  aware.** A new pure helper in `witness_metrics.py` reusing `_TERMINAL_STATUS_TOKENS`
  / `_RETURN_PRESENCE_TOKENS` / `_beat_names_actor`: a chapter is an over-pack for
  actor `X` when X is named with a removal token AND a return token across the union of
  the chapter's `summary` text and its `beats`. This is a SPEC-time check on authored
  text — distinct from `beat_coverage_gap`, which checks beats against *committed*
  `world_state` and is unavailable at outline time (the chapter is unplayed, no ledger
  exists). Actor names at outline time come from the synopsis/summary; the detector
  scans for any name token shared between a removal phrase and a return phrase
  (matching the witness's token model), not a roster lookup.

- **J4 — Deterministic gate corrected (the draft's AC-1 was unrunnable).** AC-1 said
  "the resolution yields a doc where `beat_coverage_gap` is clean for every chapter,"
  but `beat_coverage_gap` reads committed `world_state` that does not exist until a
  chapter is PLAYED and CLOSED — it cannot run at outline-unit time. **Frozen AC-1:**
  with the outline graph stubbed to return an over-packed chapter,
  `reversal_pack_gap` fires and the A1 resolution (constrained re-outline stub) yields
  an outline where `reversal_pack_gap` is clean for every chapter; **non-vacuous
  negative control:** a removal-only chapter passes through untouched (no spurious
  re-invoke). The corpus `beat_coverage_gap → 0` (AC-2) stays as **post-close
  corroboration** under the FR-522 instrument posture (a real played+closed book),
  NOT the unit gate.

- **J5 — Reappearance needs NO new forward channel; the existing lifecycle machinery
  already carries it.** Once the reversal is split, the removal chapter closes the
  actor terminal and the LATER chapter's summary carries the return.
  `_planned_reappearance_chapter` already scans title/summary/beats for the return
  signal, and `_clamp_lifecycle_reappearance_to_plan` already raises a
  `CharacterLifecycle.allowed_reappearance_from_chapter` to that planned chapter
  (`existence_state=missing_presumed_dead`). `docs/architecture.md` documents exactly
  this `missing_presumed_dead` + `allowed_reappearance_from_chapter: 5` forward. So the
  split is **sufficient** — the reappearance is honored by code that already exists.
  (This is precisely why FR-526 is redundant absent a proven close-seam defect — see
  FR-526's return-to-plan.)

- **J6 — Regime unchanged.** Example tests REQ-exempt (FR-474 J3); no CAP/REQ minted;
  changelog fragment `type: fix, scope: examples`, no `req:`; commit subject carries
  `FR-525`; diary entry accompanies the GREEN commit (diary-gate).
  `lint-imports` must stay clean (the detector is pure, layer-3).

**Verdict:** **APPROVED with the scope corrections above. Frozen — authorized for
enforce.** Build order: (1) RED — add `reversal_pack_gap` + a fixture proving it fires
on an over-packed card and is clean on a removal-only card (non-vacuous); (2) GREEN —
add the `chapter_outline.yaml` partition rule + the bounded-retry/raise resolution in
the outliner so the unit gate (AC-1) passes; (3) corroborate — regenerate a Floodmark
book and confirm `scan_beat_gaps.py → 0` (AC-2) with Arnulf's loss and return in
DIFFERENT chapters. The committed `beat_coverage_gap` witness (`c6f197a3`) remains the
standing corpus regression. Enforce against THIS frozen scope; deviations return here.

---

## Implementation Status — ENFORCED (GREEN)

Built against the frozen scope above; no deviations.

- **RED (`b42ff067`)** — `witness_metrics.reversal_pack_gap(card)` + 5 fixtures
  (`tests/test_reversal_pack_gap.py`): fires on an over-packed card (Arnulf swept +
  presumed drowned AND reappears alive → `gap_count==1`, `packed_actors==["Arnulf"]`),
  clean on removal-only, return-only, and split-across-two-chapters controls, and
  does not crash on an empty card. Precision hardened against the real 10024-BC
  corpus: `_subjects_near(text, tokens, window=40)` attributes each removal/return
  token to the nearest proper name BEFORE it (subject proximity), so the witness
  fires on 10024-BC Ch3 = [Arnulf] ALONE and stays clean across all sixteen older
  books — the same precision signature as `beat_coverage_gap`, its committed-artifact
  dual. (First co-occurrence impl was a `plausible_wrong_answer`: fixtures passed,
  real corpus over-fired on CH2 idiom and named Hilde/Gunnar/Aschenwulf in CH3.)

- **GREEN (this commit)** —
  - **A1 prompt rule** (`prompts/chapter_outline.yaml`): a character removed within a
    chapter MUST NOT also return within that SAME chapter; the loss and the return
    belong to DIFFERENT chapters (author the return as a beat of a LATER chapter).
  - **Bounded-retry/raise resolution** (`chapter_ops.outline_chapters`): after each
    outline, `_packed_chapters` runs `reversal_pack_gap` over every authored chapter;
    on a pack the outline is re-invoked with `_reversal_feedback` (the named violation)
    appended to the synopsis, up to `_OUTLINE_MAX_ATTEMPTS = 3` (first roll + two
    corrected re-rolls); if the pack survives, RAISES `ValueError` (Commandment 6: no
    silent fallback). Kept pure (layer-3 import of `reversal_pack_gap`; `lint-imports`
    KEPT, 1 contract).
  - **AC-1 unit gate** (`tests/test_chapters.py`, +3): packed-first-roll re-rolled to a
    clean split is accepted; non-vacuous negative control — a removal-only outline
    passes untouched with no spurious re-invoke; an always-packed outline RAISES after
    exactly 3 attempts. Full DM suite 239 passed (+3); `lint-imports` KEPT; ruff clean.

- **Corroboration (AC-2/AC-6)** — `scan_beat_gaps.py` regen pending (FR-522 instrument
  posture: corroboration, not gate). The committed `beat_coverage_gap` witness
  (`c6f197a3`) remains the standing corpus regression on the committed artifact.

**Status: ENFORCED.** Prevention (this gate, at the partitioner boundary) +
detection (`beat_coverage_gap`, at the committed artifact) are duals reading the same
reversal from opposite ends of the pipeline. FR-526 remains return-to-plan pending the
close-seam probe (J5: the split is sufficient — reappearance is honored by existing
`CharacterLifecycle.allowed_reappearance_from_chapter` machinery).
