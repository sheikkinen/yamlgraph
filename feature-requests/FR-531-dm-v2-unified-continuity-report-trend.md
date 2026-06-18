# Feature Request: FR-531 — DM v2: Unified Continuity Report with Per-Book Trend

**Priority:** MEDIUM
**Type:** Chore (tooling / regression visibility)
**Status:** **ENFORCED (2026-06-18).** `continuity_report.py` aggregates the deterministic
witnesses into one per-book table grouped by exact premise (`tagline`), with a same-premise
delta column. `book_turn_waste` extracted into `witness_metrics.py` (shared by the script
and `scan_turn_waste.py` — no duplicated measurement). 7 example tests green; full DM suite
259 passed; lint clean. Corpus smoke run surfaced a real `wasted_turns 14->34` regression
trend inside the em-dash floodmark premise and flagged 10025-BC's recorded epilogue beat.
See Implementation (2026-06-18).
**Effort:** ~0.5-1 day
**Requested:** 2026-06-18

## Summary

The instrument shelf has grown to six-plus hand-run scan/witness scripts
(`scan_seam_gaps`, `scan_beat_gaps`, `scan_turn_waste`, `replay_chapter_continuity`,
`witness_continuity_metrics`, `cue_metrics`). They overlap, are run by hand, and never
produce a single view. This FR collapses them into one `continuity_report.py` that runs
over an `--out` directory and emits **one table of every deterministic metric per book**,
plus a **per-book score history** across the corpus — making "did this FR move the
needle?" a one-command answer and exposing whether the FR-506→527 arc actually moved the
aggregate or merely added detectors.

## Value Statement

A single command answers "did continuity improve?" with a per-book, per-metric trend,
instead of running six scripts by hand and eyeballing whether a regression hid in the gap
between two instruments.

## Problem

The continuity program has **measured a lot and never shown a trend.** Six visibility
witnesses (FR-522 posture, correctly un-gated) produced no aggregate score line across the
FR-506→527 arc; the latest book is still continuity 1/5 after many seam-hardening waves.
Without a trend, the program risks the `detection_without_enforcement` shape: many
detectors, no demonstrated movement. A unified report is the precondition for honest
prioritization — you cannot rank the open gaps (FR-528/529) by leverage if you cannot see
which past FRs moved which metric.

## Proposed Solution

### `scripts/continuity_report.py --out outputs/dungeon-master/`

A pure aggregator (no LLM) that, for every `*-BC/story.json` under `--out`:

- runs each existing deterministic witness (`scan_seam_gaps`, `scan_beat_gaps`,
  `scan_turn_waste`, `witness_continuity_metrics`, `cue_metrics`) and collects its numbers;
- emits one table: rows = books (chronological by slot number), columns = each metric
  (seam gaps, beat gaps, wasted turns, flag metrics, cue signals);
- highlights the **trend** per metric (delta vs the prior book) so a regression between
  two runs is visible at a glance.

It calls the existing witness functions (`api/witness_metrics.py`, `api/cue_metrics.py`)
rather than re-implementing them — a thin orchestration layer, not new measurement logic.

## Judgement (2026-06-18 — authorized, trend claim narrowed)

- **J1 — pure aggregator, clean chore.** Orchestrating the existing deterministic
  witnesses into one per-book table (reusing `witness_metrics` / `cue_metrics`, no new
  measurement) is the right shape and directly answers "did the arc move the needle?".
  Approved.

- **J2 — "trend" is only valid WITHIN a premise (frozen correction).** The corpus mixes
  premises (10021-10025-BC are floodmark; earlier slots differ). A single slot-ordered
  delta column would compare unlike books and manufacture a false trend. The report MUST
  group/label rows by premise (or restrict the delta to same-premise neighbours). This is
  the load-bearing constraint of the FR — a mis-scoped trend is worse than no trend.

- **J3 — deterministic shelf only; no LLM score here.** The reviewer's continuity score is
  non-deterministic and belongs to FR-530; this report is the deterministic shelf. Join
  them later once FR-530 emits machine-readable output (J3 there). Chore type is
  changelog-exempt — confirm at enforce; example-scoped, NO `@pytest.mark.req`.

**Scope frozen:** one pure `continuity_report.py` over `--out`, per-book rows grouped by
premise, per-metric same-premise delta, reusing existing witnesses. No LLM, no new
metrics.

## Implementation (2026-06-18)

**Shape delivered exactly as judged.** A pure aggregator, no LLM, no new measurement.

- **`api/witness_metrics.py`** — extracted `book_turn_waste(doc) -> {wasted_turns,
  capped_chapters, chapters}` (plus the supporting `_turn_direction`,
  `_turn_satisfied_count`, `_last_progress_turn`, `_scene_complete_turn` helpers and the
  `CHAPTER_TURN_CAP=16` / `TURN_WASTE_STALL_THRESHOLD=3` constants). This is the only
  measurement logic that previously lived solely inside `scan_turn_waste.py`; promoting it
  to the witness module is what lets both the script and the report share one
  implementation (J1: no duplicated measurement). No import cycle — `turn_ops` does not
  import `witness_metrics`.

- **`scripts/scan_turn_waste.py`** — refactored to import the shared `book_turn_waste`
  (and constants) from `witness_metrics`; the module-level `sys.argv` loop moved into
  `_main(paths)` under `if __name__ == "__main__":`. Behaviour unchanged; the duplicated
  measurement is gone.

- **`scripts/continuity_report.py`** (new) — `book_metrics(doc)` sums six deterministic
  witnesses into one row (`seam_gaps`, `beat_gaps`, `reversal_packs`, `unplayable_beats`,
  `wasted_turns`, `completed_chapters`), reusing `seam_precondition_gap`,
  `beat_coverage_gap`, `reversal_pack_gap`, `unplayable_beat_gap`, `book_turn_waste`, and
  `parse_story_progress_metrics` (the established chapter-completion witness — not a
  re-implementation). `premise_of(doc)` keys on the exact stripped `tagline`.
  `render_markdown` groups rows into per-premise sections (J2: the load-bearing
  correction), and the delta column compares only against the prior **same-premise** book.
  `main(argv)` takes `--out`.

- **`tests/test_continuity_report.py`** (new, 7 example tests, FR-474 J3: no
  `@pytest.mark.req`) — covers `book_turn_waste` (capped-stall only / clean-doc-zero),
  `book_metrics` witness reuse + the recorded epilogue flag, exact-tagline premise keying,
  and per-premise grouped delta rendering (multi-book and single-book).

**Validation.** `pytest examples/dungeon_master/tests` → 259 passed (252 + 7). Lint +
format clean on all four files. Corpus smoke run
(`python -m examples.dungeon_master.scripts.continuity_report --out
outputs/dungeon-master/`) confirmed: per-premise grouping separates the hyphen- and
em-dash floodmark variants; the hyphen group shows a real `seam_gaps 2->1->0` improvement;
the em-dash group exposes a `wasted_turns 14->23->26->34` regression and flags 10025-BC's
recorded `unplayable_beats = 1` epilogue (the very pathology FR-528 now prevents at outline
time). The report is the precondition for honest leverage-ranking the FR-506->527 arc
asked for.

**Deviations from plan.** None material. The six "witness scripts" the Summary listed are
collapsed into one orchestrator as specified; `completed_chapters` reuses the existing
`parse_story_progress_metrics` rather than a bespoke counter, strengthening J1's
no-duplication guarantee. Chore type confirmed changelog/diary-exempt at the hook boundary.

## Acceptance Criteria

- [x] `continuity_report.py --out <dir>` produces one per-book table of every existing
      deterministic metric, ordered by slot number.
- [x] Each metric column shows the per-book delta (trend) vs the prior book.
- [x] Pure: no LLM call; reuses existing witness functions (no duplicated measurement).
- [x] Runs over the full recorded corpus in one invocation.
- [x] Example-scoped (FR-474 J3): NO `@pytest.mark.req`; changelog `type:chore
      scope:examples`, no `req:`. (Chore type is changelog-exempt — confirm at enforce.)

## Alternatives Considered

- **Leave the six scripts separate** — status quo; the cost is no trend line and the risk
  of a regression hiding between instruments.
- **Add the trend logic into each script** — scatters the aggregation and re-introduces
  the "run six things by hand" problem; one orchestrator is the right shape.
- **Include the LLM reviewer score in the table** — deferred to FR-530 (the reviewer
  score is non-deterministic; this report is the deterministic shelf). The two can be
  joined later once FR-530 emits a machine-readable score.

## Related

- `examples/dungeon_master/scripts/` (the six witnesses), `api/witness_metrics.py`,
  `api/cue_metrics.py`.
- FR-522 (instrument posture), FR-530 (the LLM-reviewer score, joined later).
- `examples/dungeon_master/docs/continuity-issues.md` §5.5, "the program has measured a
  lot and never shown a trend".
