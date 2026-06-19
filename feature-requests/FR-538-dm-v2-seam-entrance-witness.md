# Feature Request: DM v2 Seam-Entrance Continuity Witness

**Priority:** HIGH (measures a 10028-BC defect class; harness for FR-539)
**Type:** Enhancement
**Status:** Proposed
**Effort:** ~0.5 day
**Requested:** 2026-06-19

## Summary

Add a **deterministic seam-entrance detector** that flags any character who *acts in a
chapter's prose but crossed the chapter seam with no on-page arrival* — present in chapter N
but neither on-page in chapter N−1 nor declared as an entrance. Emit it as a **witness**
(visibility, not a gate — FR-522/FR-530 posture), per chapter and per book. This FR builds the
measurement harness only; the generative fix is FR-539. It follows the investigation-before-fix
split (FR-371 → FR-372): the detector's fixtures become FR-539's regression suite.

## Value Statement

We get a per-run, machine-readable count of seam-entrance breaks among the tracked **roster**
characters — a roster member correctly scoped out of chapter N (FR-537) who re-enters N+1 with
no narrated arrival — so the fix can be proven against a moving number instead of a hand-read
review.

> **Scope (roster lens — validated 2026-06-19).** Running the detector on 10028-BC (the book
> whose review motivated this FR) reports `gap_count = 0` on every chapter — and that is the
> honest roster-lens truth: every **roster** character's entrance (including Reinmar's genuine
> Ch4 arrival) is established in prose. The reviewer's two salient seam-entrance breaks
> ("Arnulf appears in Ch3", "Eirik returns in Ch6") are about **non-roster named NPCs** —
> characters never in `characters.roster`, so the roster-scoped matcher cannot and does not see
> them. That non-roster named-character class is **explicitly out of scope** here (it overlaps
> the status/resurrection rail — FR-507/509/510 — and the dead-character prose detector);
> broadening to arbitrary proper names would require the noisier `_PROPER_NAME_RE` + stopword
> machinery and a re-judgement. This witness measures the roster lens deterministically; the
> unit fixtures prove it fires when a roster member enters unestablished.

## Problem

FR-537 scopes *who acts* per chapter; the seam packet gates *who is allowed back* (lifecycle).
Neither produces, or measures, the prose obligation *"establish how this character comes to be
here."* A character correctly absent from chapter N's scoped cast (a clean two-hander) now
enters N+1 with no narrated arrival. The reviewer LLM catches this by hand, but there is no
deterministic per-run signal: we cannot tell whether a change made seam entrances better or
worse without re-reading prose. The cheapest bug is the one named in the witness — but no
witness names this one yet.

The existing detectors are adjacent but do not cover it:
- `gap_detectors.seam_precondition_gap` detects unbridged *lethal exits* (carried-alive actor
  killed by a hazard with no reposition beat) — an **exit** gap, not an **entrance** gap.
- `prose_continuity.detect_dead_character_prose_violations` detects a *confirmed-dead* actor
  appearing in prose — a status violation, not a first-appearance/arrival gap.

Entrances are the unrendered mirror of exits.

## Judgement (2026-06-19)

Approved with one refinement. Resolutions applied:

- **B1 (blocking) — measure prose establishment, not manifest presence.** A non-gap
  ("resolved") entrance must be one the narrator *actually staged in prose*, not one merely
  listed in FR-539's `cast_entrances` manifest. A manifest entry is structural; it does not
  bridge a seam. Suppressing the gap by populating a list would be compliance theatre
  (`gate_checks_shape_not_substance`): FR-539 could drive `gap_count` to zero without writing
  a word of prose. The detector therefore measures an **arrival/establishment signal in
  `cid`'s text** (a reposition/arrival token-run near the entrant, mirroring
  `seam_precondition_gap`'s bridge check), and the `declared(cid)` manifest-subtraction term
  is **removed** from the formula. `declared` means *narrated*, never *listed*.
- **R1 — prose-based gating signal.** The reader-facing defect is purely prose, and the
  reviewer LLM reads prose, not turn intents. The gating signal is prose-based; a recorded
  turn intent is used only to separate *acted* from merely *mentioned* among the names that
  appear in the prose, not as an independent membership test.
- **Lens note (paired with FR-539):** this witness measures the **outcome** set (who actually
  arrived on the page). FR-539's manifest is the **candidate** set (the scope delta the
  narrator should stage). They are intentionally different lenses; the manifest feeds the
  narrator, never this gate.

## Proposed Solution

A pure detector in a new leaf `examples/dungeon_master/api/seam_entrance.py` (a sibling of
`gap_detectors`, which was at the 450-line ceiling), matching the existing
`*_gap(story_doc, cid) -> dict` shape and reusing the word-bounded name-in-text matching
already proven in `prose_continuity` / `chapter_open._name_tokens`.

### Detection (deterministic, no LLM)

For chapter `cid` (with prior chapter `prev`):

```
acting_in(cid)   = roster names whose token-run appears in cid's final-cut text
                   (a recorded turn intent only distinguishes "acted" from merely
                    "mentioned" AMONG names already present in the prose — R1)
on_page(prev)    = roster names whose token-run appears in prev's final-cut text
established(cid) = entrants whose arrival is staged in cid's text — an arrival /
                   reposition token-run near the entrant (mirrors the bridge check
                   in seam_precondition_gap); the gating, prose-based signal
entrance_gaps    = acting_in(cid) − on_page(prev) − established(cid) − {first-chapter cast}
```

The gap set subtracts **established-in-prose** entrants — *not* a manifest. A name FR-539
lists in `cast_entrances` but does not narrate still counts as a gap (B1).

Each gap is classified by the same taxonomy FR-539 will act on (derived, not authored):

- **new** — name never in `⋃ on_page(1..prev)` (a genuine newcomer, e.g. Reinmar in Ch4;
  *correct* to enter, but flagged so the fix can require an introduction).
- **returning** — name has a `character_lifecycle` absence/return record in the inherited seam
  packet (complements the reappearance gate).
- **continuing** — on-page in some earlier chapter, scoped out of `prev`, back in `cid`.

```python
def seam_entrance_gap(story_doc: dict, cid: str) -> dict:
    """Detect characters who act in chapter ``cid`` with no on-page arrival.

    Returns ``{chapter, gap_count, acting_count, gaps:[{name, kind,
    last_on_page_chapter, established}]}`` where ``established`` is the prose
    arrival signal (the gating term, NOT a manifest lookup). Pure: reads final-cut
    text + turn intents + inherited seam packet; no LLM, no turn_ops.
    """
```

### Emission (witness, non-gating)

Extend `scripts/emit_continuity_witness.py` to add a `seam_entrance` block to
`continuity_witness.json`:

```json
{
  "book": "10028-BC",
  "continuity_score": 1,
  "break_count": 5,
  "seam_entrance": { "gap_count": 1, "by_kind": { "continuing": 1 } },
  "posture": "visibility-not-gate"
}
```

A missing review or a non-zero gap count **never fails the run** (FR-522 posture). The block is
purely additive to the existing witness.

## Acceptance Criteria

- [ ] `gap_detectors.seam_entrance_gap(story_doc, cid)` returns the documented shape; pure
      (no LLM, no `turn_ops` import — respects the leaf-module layer).
- [ ] Name matching is word-bounded (a roster name matches only as whole-word token runs;
      `Ron` does not match inside `around`), reusing the FR-537 / `prose_continuity` matcher.
- [ ] "Acts" is a prose token-run in `cid`'s final-cut text; a recorded turn intent only
      separates *acted* from merely *mentioned* (e.g. grieved) **among names already in the
      prose** — it is not an independent membership test (R1).
- [ ] A resolved (non-gap) entrance is one whose **arrival is established in `cid`'s prose**
      (an arrival/reposition token-run near the entrant, mirroring `seam_precondition_gap`'s
      bridge check). The gating signal is prose-based (B1).
- [ ] No manifest-based suppression: FR-539's `cast_entrances` list **does not** subtract from
      the gap set; a name listed but not narrated still counts as a gap (B1).
- [ ] Taxonomy (`new` / `returning` / `continuing`) is derived from prior on-page history +
      inherited `character_lifecycle`; never read from an authored field.
- [ ] First-chapter cast is excluded.
- [ ] **Unit fixtures (gating):** a two-chapter fixture where Ch2 prose has a character absent
      from Ch1 prose, acting in Ch2, with **no** arrival signal yields exactly one
      `continuing`/`new` gap; the same fixture **with** an arrival/reposition line for that
      character yields zero (establishment resolves it); a fixture where the entrant is on-page
      in Ch1 yields zero; a fixture where the entrant is merely mentioned (no intent) yields
      zero.
- [ ] **Witness (non-gating):** `emit_continuity_witness.py` adds the `seam_entrance` block to
      `continuity_witness.json`, reading the session `story/story.json`. Run on `10028-BC` it
      reports `gap_count: 0` — the honest roster-lens truth (every roster entrance is
      prose-established; the Arnulf/Eirik breaks are non-roster and out of scope, see Scope).
      The unit fixtures (above) prove the witness fires when a roster member enters
      unestablished. Never wired into CI as a gate.
- [ ] Example tests are requirement-exempt (FR-474 J3): **no** `@pytest.mark.req`, no capability
      registry entry (mirrors FR-537's enforcement footprint — a deviation from the original
      `REQ-YG-XXX` criterion, corrected to the proven example convention).
- [ ] Changelog fragment (`type: feat`, `scope: examples`) + diary reflection.

## Implementation (2026-06-19)

**Status: implemented (roster lens).** RED `3dd6850e` (7 fixtures), GREEN this change.

- **Detector home \u2014 module split (deviation).** `gap_detectors.py` was at the 450-line ceiling,
  so adding ~90 lines there would trip the file-size gate. Per Commandment 8 (split before
  bloat), the detector lives in a new sibling leaf
  [`examples/dungeon_master/api/seam_entrance.py`](../examples/dungeon_master/api/seam_entrance.py).
  Callers (the detector test, the witness emitter) import `seam_entrance_gap` from that leaf
  directly — an initial re-export through `gap_detectors` was reverted because the three-line
  import alone pushed the file over 450 (`test_module_size`). The `*_gap(story_doc, cid) -> dict`
  shape still matches its `gap_detectors` siblings.
- **Layering.** The word-bounded matcher (`_name_tokens`/`_contains_token_run`) is duplicated
  from `chapter_open` rather than imported, so the witness stays a leaf *below* the chapter-open
  gate (no upward dependency). import-linter KEPT.
- **Establishment signal.** Prose proximity (`_ESTABLISH_TOKENS` within 60 chars of the
  entrant's name), mirroring `seam_precondition_gap`'s reposition/bridge check (B1). A manifest
  never subtracts.
- **Roster lens (validated against 10028-BC).** Reports `gap_count = 0` \u2014 the honest truth for
  the roster; the headline Arnulf/Eirik breaks are non-roster named NPCs, **out of scope** (see
  Scope note). Decision recorded after surfacing to the requester: keep the roster lens, correct
  the FR's worked example, do not broaden to arbitrary proper names.
- **Enforcement footprint.** No `@pytest.mark.req`, no capability YAML \u2014 example tests are
  requirement-exempt (FR-474 J3), matching FR-537.

## Alternatives Considered

- **Skip the witness, go straight to the fix (FR-539).** Rejected — FR-371→372 proved that a
  fix without a deterministic condemning signal is a hypothesis. The detector's fixtures *are*
  FR-539's red tests; building them here is not extra work, it is the work moved earlier.
- **Reuse `seam_precondition_gap`.** Rejected — it detects unbridged *lethal exits* over beats,
  the opposite edge; conflating entrances into it would overload a single detector
  (`framework_costume`).
- **Have the reviewer LLM emit a structured entrance count.** Rejected for the gating path —
  non-deterministic, cannot anchor a red test. The reviewer remains the qualitative witness;
  this detector is the deterministic one.
- **Let the FR-539 manifest suppress the gap (the original draft).** Rejected (B1) — declaring
  a name in a list is not narrating an arrival; a manifest-suppressed gate could read zero
  while the seam stays unbridged (`gate_checks_shape_not_substance`). The witness measures
  prose establishment; the manifest only feeds the narrator.

## Related

- [gap_detectors.py](../examples/dungeon_master/api/gap_detectors.py) — `seam_precondition_gap`
  (exit-edge sibling), the `*_gap(story_doc, cid) -> dict` shape to match
- [prose_continuity.py](../examples/dungeon_master/api/prose_continuity.py) — word-bounded
  name-in-text matching to reuse
- [chapter_open.py](../examples/dungeon_master/api/chapter_open.py) — `resolve_chapter_cast`,
  `_name_tokens` (FR-537 scoped-cast source; defines on-page vs scoped)
- [scripts/emit_continuity_witness.py](../examples/dungeon_master/scripts/emit_continuity_witness.py)
  — witness emission to extend
- `outputs/dungeon-master/10028-BC/review.md` — the Arnulf-in-Ch3 seam-entrance evidence
- **FR-539** (the generative fix this measures) — typed `cast_entrances` + prior-prose-aware
  Final Cut
- **FR-537** (the scoping that exposed the gap)
