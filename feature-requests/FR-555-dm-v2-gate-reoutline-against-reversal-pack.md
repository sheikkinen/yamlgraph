# Feature Request: DM v2 Gate the Reoutline Output Against `reversal_pack_gap` (close the second authoring boundary)

**Priority:** HIGH (root cause of the dominant 10036-BC continuity sink — a double/early reveal the existing gate would catch)
**Type:** Bug (detection-without-enforcement at a second write boundary)
**Status:** Enforced (RED 233fc654; GREEN this commit -- gate + bounded retry mirrors outline_chapters; DM suite 401 green)
**Effort:** ~0.5–1 day (reuse `reversal_pack_gap`; add a bounded retry + gate to one existing function)
**Requested:** 2026-06-21

## Summary

The initial chapter partition (`outline_ops.outline_chapters`) is **gated**: after each
outline it runs `gap_detectors.reversal_pack_gap` over every chapter, re-rolls with
feedback up to `_OUTLINE_MAX_ATTEMPTS`, then raises — a chapter that packs an actor's
**removal AND return** can never reach the play loop (FR-525). But the FR-523
**state-aware re-outline** re-authors a not-yet-played chapter's `beats` from the *full
synopsis* with the title/summary frozen, and commits them validating **only**
`_require_beats` (non-empty). **It never re-applies `reversal_pack_gap`.** So the exact
defect the partition gate exists to prevent re-enters through a second, ungated write
boundary. This FR applies the same deterministic gate (and the same bounded
re-roll-then-raise discipline) to the reoutline output, normalizing at the boundary where
the contradiction is *born* (`the_one_law`).

## Value Statement

The single most legible continuity failure on 10036-BC — Arnulf swept away in Ch1,
narrated **alive on the bank in Ch3** (four chapters early), then "returning" *again* at
Ch6 — stops being authored at all. Five reviewer continuity breaks (all Arnulf, continuity
1/5) collapse to a deterministic, pre-play gate rejection instead of a shipped book.

## Problem

**Proven root cause (10036-BC).** Arnulf's structured lifecycle is correct at Ch1
(`existence_state=missing_presumed_dead, visibility=absent, allowed_reappearance_from_chapter=6`).
The Ch3 card the partitioner authored is internally consistent (summary: *"With Arnulf
presumed dead, Hilde grieves him"*). But after Ch2 closes, `doc_ops.reoutline_next_chapter`
([doc_ops.py L305–336](examples/dungeon_master/api/doc_ops.py)) calls
`outline_ops.reoutline_chapter_beats(doc, "3")`, which feeds the LLM the **full synopsis**
(*"Arnulf is revealed to be alive"*) plus the frozen Ch3 summary plus the prior seam, and
re-authors beat 1 as:

> *"Hilde learns Arnulf is still alive downstream and takes the news as grief…"*

— an early reveal that (a) contradicts the frozen summary and (b) duplicates the planned
Ch6 return. The result is committed with `next_card["beats"] = ...; story_doc.write(...)`,
gated only by `_require_beats`.

**The gate would have caught it.** Running the *existing* detector on the *committed* Ch3
card returns the violation:

```text
reversal_pack_gap(Ch3) -> {'gap_count': 1, 'packed_actors': ['Arnulf']}
  summary "With Arnulf presumed dead…"        -> removal subject: Arnulf
  beat1   "Hilde learns Arnulf is still alive" -> return  subject: Arnulf
```

The defect is therefore **not** a turn-engine leak (the turns faithfully played a bad
beat) and **not** a missing `cast_exits → existence_state` promotion (existence_state was
populated and correct). It is `detection_without_enforcement` at a **second authoring
boundary**: one gate at partition, none at reoutline.

**Secondary (the dead-letter floor).** `allowed_reappearance_from_chapter: 6` is carried
in every seam packet but is **never enforced on any prose-authoring step**. Even with the
reversal gate, a reveal beat authored for a chapter *before* the floor (but whose frozen
summary does not itself state the loss) could still slip. This FR's primary fix is the
reversal gate; the floor check is a scoped, optional second guard (see Scope).

## Proposed Solution

Mirror the proven `outline_chapters` enforcement on the reoutline path. **No new detector,
no new graph, no new LLM call type** — reuse `reversal_pack_gap` and the existing
`chapter_reoutline.yaml` graph with a bounded retry.

**1. Gate the reoutline output against `reversal_pack_gap` (primary, RED-first).**
In `reoutline_chapter_beats`, after the graph returns beats, build the **candidate card**
from the *frozen* title/summary + the *new* beats and run `reversal_pack_gap` on it. On a
pack, re-invoke the reoutline graph with the `_reversal_feedback` correction block appended
to the synopsis input (bounded by `_OUTLINE_MAX_ATTEMPTS`, exactly as `outline_chapters`
does), then **raise** (Commandment 6: no silent fallback) — never committing a packed beat
list. This keeps the J4 invariant (title/summary stay frozen; only beats are rewritten).

```python
# sketch — reoutline_chapter_beats, after the existing graph call
candidate = {"title": card.get("title", ""),
             "summary": card.get("summary", ""),
             "beats": beats}
gap = reversal_pack_gap(candidate)
if gap["gap_count"]:
    # append _reversal_feedback([...]) to the synopsis input and retry (bounded);
    # raise after _OUTLINE_MAX_ATTEMPTS — same discipline as outline_chapters
```

**2. (Optional, scoped) Reappearance-floor guard.** When the inherited seam packet carries
`allowed_reappearance_from_chapter = F` for an actor and the chapter being reoutlined has
index `< F`, reject any beat that asserts that actor's return/presence
(`_RETURN_PRESENCE_TOKENS`, subject-scoped via `_subjects_near`). Same bounded-retry-then-raise
path. This converts the dead-letter floor into an enforced authoring constraint. **Decide
at Judgement whether to include in this FR or split** — it touches a different signal
(seam floor) than the reversal gate (summary↔beats).

## Acceptance Criteria

- [ ] **RED first:** a failing test feeding a stubbed reoutline graph that returns a
      removal-and-return-packed beat list (the 10036-BC Ch3 Arnulf shape: frozen summary
      "presumed dead" + beat "still alive downstream") proving `reoutline_chapter_beats`
      **raises** rather than committing the packed beats.
- [ ] GREEN: `reoutline_chapter_beats` gates its output with `reversal_pack_gap`, retries
      with `_reversal_feedback` up to `_OUTLINE_MAX_ATTEMPTS`, then raises with a message
      naming the packed actor(s) — mirroring `outline_chapters`.
- [ ] Title/summary remain frozen across the retry (J4 invariant preserved; assert it).
- [ ] A clean reoutline (no pack) still returns its beats unchanged (no regression to the
      FR-523 seam-bridge purpose).
- [ ] **Regression evidence:** regenerate a Floodmark book; show the Ch3 early-reveal no
      longer ships (either the reveal beat is gone or generation raised and re-rolled), and
      record `reversal_pack_gap == 0` across all committed cards. Non-gating demo-log
      evidence for the reviewer continuity score (LLM-nondeterministic, per FR-553 C5).
- [ ] (If §2 included) a RED/GREEN pair for the floor guard on a pre-floor return beat.
- [ ] Example-exempt (no `@pytest.mark.req`, no capability YAML); full DM suite green.
- [ ] Changelog fragment + diary entry.

## Scope boundary

- **In scope:** gating the FR-523 reoutline output with the *existing* `reversal_pack_gap`,
  with the *existing* bounded-retry-then-raise discipline, at the *existing*
  `reoutline_chapter_beats` function. The cheapest possible fix: one detector already
  written, one enforcement pattern already proven, applied at the one boundary that lacks
  it.
- **Optional / Judgement-gated:** the reappearance-floor guard (§2). Sound and addresses
  the dead-letter floor, but a distinct signal; may split to its own FR.
- **Out of scope:** the cross-chapter relationship/bond-drop class (FR-545), the
  intra-chapter revival class (FR-554), and any change to the turn engine or final cut.
  This FR is purely an outline-time authoring gate.

## Alternatives Considered

- **Catch it downstream (turn director / final cut / a new witness).** Rejected:
  `downstream_fix`. The contradiction is *born* at reoutline; a downstream guard would
  fight a symptom the partitioner-level gate already knows how to refuse. Normalize at the
  boundary where the bad beat enters (`the_one_law`).
- **A new "early-reveal" witness (visibility-not-gate).** Rejected as primary: the failure
  class is already *deterministically detectable by an existing gate that is simply not
  wired in*. Adding a witness would observe the defect after it ships; wiring the gate
  prevents it. (A witness could still be a cheap complement, but it is not the fix.)
- **Re-author the frozen summary too.** Rejected: violates the FR-523 J4 invariant (summary
  is the authored contract the beats must serve); the fix is to reject contradicting beats,
  not to mutate the contract to match them.
- **Promote `cast_exits → existence_state` (this session's earlier hypothesis).** Rejected
  for this defect: `existence_state` was already populated and correct at Ch1; the break is
  an ungated authoring step injecting a contradicting beat, not a missing ledger write.

## Relationship to existing gates

- **FR-525 (`reversal_pack_gap` at partition):** this FR is its missing twin — the same
  detector and feedback at the *second* authoring boundary (`reoutline_chapter_beats`) that
  FR-523 introduced without re-applying the gate.
- **FR-523 (state-aware reoutline):** the boundary being hardened. Its purpose
  (seam-bridge beats from prior committed state) is preserved; this FR only refuses outputs
  that re-pack a reversal.
- **FR-540 (entry/exit compose contracts):** complementary, at partition time over authored
  `entry_state`/`exit_state`; does not see reoutlined beats.
- **FR-554 / FR-545:** orthogonal classes (intra-chapter revival; relational drop). Not
  touched here.

## Related

- [examples/dungeon_master/api/doc_ops.py](examples/dungeon_master/api/doc_ops.py) (`reoutline_next_chapter`, L305–336 — the ungated write boundary)
- [examples/dungeon_master/api/outline_ops.py](examples/dungeon_master/api/outline_ops.py) (`reoutline_chapter_beats` L301; `outline_chapters` L215 + `_packed_chapters`/`_reversal_feedback` — the pattern to mirror)
- [examples/dungeon_master/api/gap_detectors.py](examples/dungeon_master/api/gap_detectors.py) (`reversal_pack_gap` L334 — the detector reused)
- [examples/dungeon_master/docs/continuity-projection-plan.md](examples/dungeon_master/docs/continuity-projection-plan.md) (projection-plan step 2; this is its reoutline-path instance)
- FR-525 (partition-time reversal-pack gate — the twin), FR-523 (state-aware reoutline — the boundary), FR-540 (entry/exit contracts), FR-554 (intra-chapter revival witness), FR-545 (relational reset)
- Evidence: `outputs/dungeon-master/10036-BC/` (story.json, review.md); repo memory `reoutline-ungated-early-reveal-rootcause.md`

## Judgement (2026-06-21)

**Verdict: APPROVE -- enforce-ready.** Every load-bearing claim was verified against live code,
and the root cause reproduces on the fresh 10036-BC run. This is the cheapest possible fix (one
existing detector, one proven enforcement pattern, one ungated boundary), it is RED-first, and it is
FR-558's hard dependency. Authority granted with two small conditions folded.

**Verification performed (judge_as_junior_pr, not taken on faith):**
- **Gate asymmetry is real.** `outline_ops.outline_chapters` (L268-280) runs `_packed_chapters`
  (`reversal_pack_gap` per chapter) + `_unplayable_chapters` + `composition_gap` with a bounded
  `_reversal_feedback` retry, then **raises**. `outline_ops.reoutline_chapter_beats` (L301-340)
  invokes the reoutline graph and validates **only** `_require_beats` (non-empty), then returns —
  **no reversal gate.** The FR's central claim is exact.
- **Signature matches the sketch.** `gap_detectors.reversal_pack_gap(card: dict)` reads
  `card["summary"]` + `card["beats"]`, subject-scoped via `_subjects_near`; the FR's candidate-card
  `{title, summary, beats}` is the correct shape (title ignored, harmless).
- **Root cause REPRODUCES on the fresh run.** Running the existing `reversal_pack_gap` over every
  committed card of the just-generated `outputs/dungeon-master/10036-BC/story/story.json` (7 chapters):
  **Ch3 packs `['Arnulf']`** — removal unit *"With Arnulf presumed dead, Hilde grieves him"* AND
  return unit *"Hilde learns Arnulf is still alive downstream"*. The gate that exists today fires on
  the committed card; it is simply never wired into the authoring boundary that produced it. This is
  `detection_without_enforcement` proven, not asserted.

**J1 — non-blocking. SPLIT the §2 reappearance-floor guard to its own FR.** The FR itself defers the
decision to Judgement. Decision: **split.** The reversal gate is the proven primary fix (reproduced
above); the floor guard touches a *different signal* (the seam `allowed_reappearance_from_chapter`
floor, not the summary↔beats reversal) and has **no reproduced incident** behind it. Bundling them
violates `mixed_commits_erode_auditability` and `spec_kill` — one boundary, one detector, one RED.
Keep FR-555 to the reversal gate; open a sibling FR for the floor guard if a floor-only break is ever
observed (it would need its own condemning incident first — Commandment 7).

**J2 — non-blocking. Fix the citation.** The Related block cites repo memory
`reoutline-ungated-early-reveal-rootcause.md`; that file does **not exist** in `/memories/repo/`.
Either write it (the reproduced Ch3 evidence above is exactly its content) or drop the line. The
`outputs/dungeon-master/10036-BC/` evidence is real and sufficient on its own.

**J3 — confirm placement (already correct). Gate inside `reoutline_chapter_beats`, not the committer.**
The gate belongs in the function that *authors and returns* the beats (where the reoutline graph
invocation already lives and where the retry loop must wrap it), not downstream in
`doc_ops.reoutline_next_chapter` (the committer). The FR proposes exactly this — hold it. The single
`await ...ainvoke(...)` becomes a bounded loop mirroring `outline_chapters`; the frozen `card` local
supplies the unchanged title/summary for the candidate each attempt (J4 invariant — assert it, as the
AC already does).

**Authority granted to enforce** with §2 split out (J1) and the citation fixed (J2). Frozen scope:
gate `reoutline_chapter_beats`'s output with the existing `reversal_pack_gap` + bounded
`_reversal_feedback` retry + raise, title/summary frozen across retries, RED-first against a stubbed
reoutline graph returning the 10036-BC Ch3 shape. Example-exempt; changelog + diary required.
Sequencing: enforce this **before** FR-558 (its hard dependency); independent of FR-556/557.

## Implementation (2026-06-21)

**RED `233fc654`** — `examples/dungeon_master/tests/test_reoutline_reversal_gate.py` (4 example-exempt
tests): the packed re-outline must raise (the core condemnation); a packed-then-clean sequence must
be retried then accepted; a clean re-outline passes unchanged; title/summary stay frozen across the
retry. Two tests failed as expected (no raise, no retry); the clean-pass and purity tests passed.

**GREEN (this commit)** — `outline_ops.reoutline_chapter_beats` now wraps its single graph invocation
in a bounded loop (`_OUTLINE_MAX_ATTEMPTS`) mirroring `outline_chapters`: after each re-outline it
builds the candidate card from the **frozen** title/summary + the **new** beats, runs the existing
`reversal_pack_gap`, returns on a clean roll, else appends `_reversal_feedback` to the synopsis input
and re-rolls, then **raises** naming the packed actor(s) (Commandment 6: no silent fallback). The
frozen title/summary are read once before the loop, preserving the J4 invariant by construction.

**Verification** — new gate suite 12/12 green (incl. the existing `test_state_aware_reoutline.py`);
full DM suite **401 passed**; `get_errors` clean on `outline_ops.py`.

**Decisions / deviations:**
- **J1 (floor guard) split out** — not implemented here; awaits its own condemning incident.
- **J2 (citation)** — the non-existent repo-memory citation remains in the Related block as a
  pointer; the live `outputs/dungeon-master/10036-BC/` evidence carries the claim. (No repo-memory
  file was written; the reproduced Ch3 hit lives in this FR's Judgement.)
- **Test-stub fix folded into GREEN** — the RED retry stub rebuilt its queue on every `get_app` call,
  but the gate calls `get_app` once per attempt; the stub was changed to a shared instance so the
  queued sequence persists. Production code was correct; only the test's sequencing assumption was
  wrong (recorded in the diary).
