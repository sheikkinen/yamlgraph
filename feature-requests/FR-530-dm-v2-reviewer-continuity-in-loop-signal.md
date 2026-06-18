# Feature Request: FR-530 — DM v2: Reviewer Continuity as an In-Loop Signal

**Priority:** MEDIUM
**Type:** Enhancement (observability → correction)
**Status:** **ENFORCED — Stage 1 (2026-06-18).** Post-generation continuity witness shipped
as a non-blocking, machine-readable per-run emit. Stage 2 (per-seam corrective re-roll)
remains REMOVED from this FR (its own future FR, gated behind FR-531 trend + FR-532
calibration). See Implementation (2026-06-18) and Judgement (J1-J3).
**Effort:** ~0.5 day (Stage 1 alone)
**Requested:** 2026-06-18

## Summary

The independent `book_reviewer` is the only component that reads **across seams** and
computes a pairwise chapter-seam continuity score — it is the source of the `10025-BC`
continuity 1/5. Today it runs entirely **after** generation, as a separate example, so its
verdict never informs the run that produced the defect. This FR steps it inward in two
stages: (1) wire its continuity axis into `generate_and_review.sh` as a per-run
**post-generation witness** (visibility, not a gate — FR-522 posture), so every book
reports a continuity score on the same run; (2) longer term, a per-seam continuity check
at chapter close that can trigger a **bounded re-roll** of the next chapter's opening
under a deterministic budget, turning the critic from a post-hoc grade into a corrective
signal.

## Value Statement

Every generated book carries its own continuity score without a separate manual review
step, and (stage 2) the worst seam breaks can be corrected in-loop instead of only graded
after the fact.

## Problem

Continuity efficacy is a non-deterministic, live-LLM property: the deterministic witness
shelf proves *wiring*, but only the cross-seam critic measures the *emergent* property a
reader actually experiences. Keeping that signal post-hoc means the pipeline is blind at
generation time to the one metric that matters, and "did this FR move the needle?"
requires a manual second run. Bringing the signal in-loop is the precondition for ever
turning continuity into a corrective (not just diagnostic) loop.

## Proposed Solution

### Stage 1 — post-generation continuity witness (this FR's load-bearing scope)

Run the reviewer's `Continuity` axis (or the whole reviewer) at the end of
`generate_and_review.sh` and emit the score alongside the book artifacts. **Visibility
only — never a CI gate** (FR-522 posture; an LLM score is not a deterministic guarantee).

### Stage 2 — per-seam bounded re-roll (sketch, gated behind Stage 1 + FR-532)

At chapter close, run a per-seam continuity check; if it fails, re-roll the next chapter's
**opening** within a deterministic budget (like the FR-501 turn cap), then accept the best
and move on. This is sketched, not built here — it depends on Stage 1 proving the signal
useful and FR-532 confirming the axis is reader-calibrated (a corrective loop driven by a
miscalibrated critic would optimize the wrong thing).

## Judgement (2026-06-18 — Stage 1 only; Stage 2 removed)

- **J1 — Stage 1 is clean and authorized.** Emitting the reviewer's `Continuity` axis as
  a non-blocking post-generation witness is exactly the FR-522 posture (visibility, never
  a gate). Small, safe, and the precondition for any later correction. Approved.

- **J2 — Stage 2 is REMOVED from this FR, not deferred.** A per-seam corrective re-roll
  driven by an LLM continuity score is a feedback loop on an un-trended (FR-531),
  un-calibrated (FR-532) signal — it would optimize whatever the critic over-weights,
  which may be a seam-differ artifact. Keeping it as a "sketch" inside this FR invites
  scope creep at enforce. It becomes its own FR only after FR-531 and FR-532 land. Strike
  it from scope here; the FR body's Stage-2 text is retained as rationale, not as work.

- **J3 — machine-readable output.** Stage 1 must emit the score in a form FR-531 can later
  join (a small JSON/line the report can read), not only human prose. Example-scoped
  (FR-474 J3): NO `@pytest.mark.req`; `feat(dungeon_master)` + changelog `type:feat
  scope:examples` no `req:` + diary entry.

**Scope frozen:** Stage 1 post-generation continuity witness only, non-blocking,
machine-readable. Stage 2 is OUT.

## Acceptance Criteria

- [x] Stage 1: `generate_and_review.sh` emits a per-run continuity score (reviewer
      `Continuity` axis) into the run output; documented as visibility, not a gate.
- [x] The witness is non-blocking: a low score never fails the run or CI (FR-522 posture).
- [x] Example-scoped (FR-474 J3): NO `@pytest.mark.req`; changelog `type:feat
      scope:examples`, no `req:`.
- [x] Stage 2 is explicitly OUT OF SCOPE here (recorded as a sketch, gated behind
      Stage 1 evidence + FR-532).

## Implementation (2026-06-18)

- **`examples/dungeon_master/scripts/emit_continuity_witness.py`** (new): reads the
  reviewer's just-written `<out>/review.md`, projects its `## Continuity` axis into a
  small machine-readable record, and writes `<out>/continuity_witness.json`:
  `{book, continuity_score, break_count, posture: "visibility-not-gate"}`. Reuses
  `parse_continuity_breaks` from FR-532's calibration harness (no duplicate parser).
  `write_witness` returns `None` when no `review.md` exists yet — a missing review is a
  skipped, non-fatal step, not an error.
- **`generate_and_review.sh`**: appended a "📊 Emitting continuity witness" step after the
  review, invoked as `... emit_continuity_witness --out "$OUT" || echo "skipped"`. The
  `|| echo` makes it strictly non-blocking — a missing review or any emit error never
  fails the run (FR-522 posture).
- **J3 machine-readable:** the JSON is the join key for FR-531's `continuity_report.py`
  (the report can later read `continuity_witness.json` to attach the LLM score to its
  deterministic witness shelf). Not wired into FR-531 here — that join is its own work.
- **Tests** (`test_emit_continuity_witness.py`, 3, example-scoped, no `@pytest.mark.req`):
  score/break-count projection + posture stamp; JSON round-trip equality; non-blocking
  skip when `review.md` is absent. Full DM + reviewer suite: 297 passed. Smoke: emitted
  `10025-BC` continuity=1/5 (11 breaks) from its real review.

## Alternatives Considered

- **Gate the run on the continuity score** — rejected; flaky LLM gates are exactly the
  FR-522 anti-pattern. Visibility first.
- **Build the corrective re-roll now (skip Stage 1)** — premature; a corrective loop on an
  un-calibrated, un-trended signal risks optimizing a critic artifact (see FR-532).

## Related

- `examples/book_reviewer/` (the cross-seam critic), `generate_and_review.sh`.
- FR-522 (instrument posture — visibility, not gates), FR-501 (deterministic budget — the
  re-roll cap pattern).
- FR-531 (trend report — the other half of "measure before correct"), FR-532 (calibration
  — gates Stage 2).
- `examples/dungeon_master/docs/continuity-issues.md` §5.4.
