# Feature Request: FR-506 — DM v2 Chapter Seam Continuity Contract

**Priority:** HIGH
**Type:** Enhancement
**Status:** Enforcing — Phase 1 implemented (A1/A2/A3/A6)
**Effort:** ~2-3 days
**Requested:** 2026-06-17

## Summary

FR-505 removed the intra-chapter paragraph grid and improved prose/engagement, but
book-level continuity still breaks at chapter boundaries. The current chapter
handoff carries a typed `world_state` ledger but not enough explicit seam
constraints for the next chapter opening. This FR adds a deterministic seam
contract that preserves causality from chapter N end -> chapter N+1 start.

## Value Statement

Writers get chapter-to-chapter flow that preserves causal state transitions,
reducing continuity defects without sacrificing the stronger prose gains from
FR-505.

## Problem

The generation pipeline currently transfers:
- fixed chapter plan (`title`, `summary`, `beats`) from outline,
- inherited typed `world_state` from chapter close,
- bounded recap window and beat ledger during turn play.

What is missing is an explicit chapter seam packet describing:
- what just changed in ways the next chapter must honor,
- what unresolved threads must open chapter N+1,
- what opening assertions are forbidden because they contradict chapter N close.

Observed symptoms (10007 reviewer continuity score 1/5):
- location/state jumps between chapter end and next opening,
- status contradictions (dead/alive framing drift),
- tactical-role reversals with no bridging beat,
- chapter openings that reintroduce stale assumptions despite inherited ledger.

Root cause: the handoff is structurally under-specified for narrative seam
requirements. The issue is not solved by parallel chapter generation; the chapters
are causally dependent and must remain sequential.

## Proposed Solution

Add a first-class seam contract and use it in turn-1 chapter openings.

### 1) Add a typed `seam_packet` to chapter close output (Phase 1, in scope)

Extend chapter close structured output with deterministic fields and strict
boundary normalization:
- `resolved_events`: list[str] — events conclusively resolved this chapter,
- `open_threads`: list[str] — unresolved pressures that should continue next chapter,
- `must_carry_facts`: list[str] — non-negotiable facts chapter N+1 opening must preserve,
- `opening_constraints`: list[str] — short do/don't constraints for chapter N+1 opening.

Schema contract (load-bearing):
- all four keys are REQUIRED on stored chapter cards,
- each value is normalized to `list[str]`, never `null`,
- non-list/invalid provider values normalize to `[]` at boundary parse,
- stable order preserved as emitted; duplicates removed preserving first occurrence,
- max items per list: 12, max chars per item: 240 (truncate, never drop keys),
- empty/default packet for legacy chapter cards:
      `{resolved_events: [], open_threads: [], must_carry_facts: [], opening_constraints: []}`.

Store this packet on each chapter card alongside `world_state` and final text,
and expose a deterministic formatter for prompt context (like `world_state`).

### 2) Add chapter opening re-anchor for turn 1 (Phase 1, in scope)

For turn 1 of chapter N+1, `running_scene(...)` includes:
- inherited `world_state`,
- previous chapter `seam_packet` (if present),
- current chapter summary/beats.

Director and character prompts receive explicit instructions:
- treat `must_carry_facts` as hard constraints,
- resolve `open_threads` before introducing new branch pressure,
- reject opening assertions that violate prior chapter closure facts.

Deterministic guardrail:
- add a pure seam validator over chapter N close packet + chapter N+1 turn-1
      context that returns structured violations (`missing_must_carry_fact`,
      `forbidden_opening_assertion`) with exact offending strings.

### 3) Keep chapter generation sequential (not parallel)

No chapter-level parallel generation. Parallelism remains inside chapter turn map
(character intent fanout) and in post-hoc analysis tools.

### 4) Adaptive re-outline deferred (Phase 2, OUT OF SCOPE for FR-506)

Bounded adaptive re-outline of remaining chapters is explicitly deferred to a
follow-up FR. FR-506 scope is seam packet + turn-1 re-anchor + deterministic seam
validation only.

## Acceptance Criteria

- [x] **A1 — Seam packet exists and is typed.**
      Chapter close returns and stores `seam_packet` with required keys
      (`resolved_events`, `open_threads`, `must_carry_facts`,
      `opening_constraints`), each normalized to `list[str]` (never null),
      deduped, bounded, and migration-safe defaulted for legacy cards.

- [x] **A2 — Turn-1 re-anchor consumes seam packet.**
      For chapter N+1 turn 1, `running_scene(...)` includes inherited
      `world_state` + prior chapter `seam_packet`, and prompt context reflects
      both.

- [x] **A3 — Deterministic seam validator exists and is pinned.**
      Add pure fixtures where chapter N closes with explicit status/location/
      possession facts and chapter N+1 opening context is validated by deterministic
      seam rules. Tests assert exact violation counts/types and exact offending
      facts; no LLM scoring in this gate.

- [ ] **A4 — Deterministic primary continuity gate.**
      On a Floodmark regen, deterministic seam violations between chapter closes
      and next chapter openings decrease versus 10007 baseline by at least 50%
      (or to zero when baseline is small).

- [ ] **A5 — Reviewer is directional secondary witness only.**
      `book_reviewer` continuity score does not regress versus 10007 (1/5), and
      FR-505 prose/engagement gains do not regress below 10007 means. This is
      recorded evidence, not a primary blocking gate.

- [x] **A6 — Tests and docs updated.**
      Unit tests for seam packet parsing/formatting + integration tests for
      chapter handoff context; DM architecture docs updated with seam lifecycle.

## Implementation Status (2026-06-17)

Completed in this enforcement pass:
- Added typed seam boundary module (`api/seam_packet.py`) with deterministic
      parse/normalize/format and a pure opening-context validator.
- Wired chapter close parsing to store `seam_packet` on chapter cards via
      `chapter_ops.close_chapter` + `doc_ops.apply_chapter_close`.
- Added migration-safe defaults for legacy/empty chapter cards in
      `doc_ops.entry` and `doc_ops.expand_chapters`.
- Injected prior chapter seam contract into `turn_ops.running_scene` for chapter
      turn 1 only.
- Updated chapter-close and turn prompts to consume/emit seam contract fields.
- Added pure seam tests (`test_seam_packet.py`) and integration assertions in
      `test_world_state.py` / `test_chapters.py`.

Validation evidence:
- `/Users/sami.j.p.heikkinen/src/yamlgraph/.venv/bin/python -m pytest examples/dungeon_master/tests --no-cov -q`
      -> `129 passed`
- `/Users/sami.j.p.heikkinen/src/yamlgraph/.venv/bin/python -m ruff check ...`
      on modified DM files -> clean.

Pending for full FR closure:
- A4 deterministic baseline-vs-post seam violation delta on Floodmark witness.
- A5 reviewer directional witness (continuity non-regression + prose/engagement guard).

## Alternatives Considered

1. Strengthen chapter summaries only.
Result: insufficient alone; summaries are intentionally high-level and do not
encode closure/opening seam obligations.

2. Parallel chapter generation.
Result: rejected for primary pipeline. Causal dependencies across chapters make
parallel chapter generation likely to increase contradictions.

3. Reviewer-only post-fix.
Result: useful detection, but does not correct seam defects during generation.

## Enforce Sequence (TDD)

1. RED: tests for `seam_packet` typed parsing/storage and turn-1 scene inclusion.
2. RED: deterministic seam validator fixtures (positive/negative) with exact
      violation assertions.
3. GREEN: chapter close prompt/schema + storage wiring + running scene injection.
4. GREEN: prompt updates for turn-direct/character-intent chapter opening rules.
5. WITNESS: Floodmark run, compute deterministic seam-violation delta vs 10007,
      then record reviewer directional evidence.
6. Distill: diary reflection on seam contract efficacy and remaining defect class.

## Related

- FR-488 — DM v2 book-scope chapters
- FR-491 — retire key-scene; chapter play loop
- FR-499 — structured world_state ledger
- FR-503 — finite beat ledger
- FR-505 — final-cut de-gridding (intra-chapter prose quality)
- Witness reviews: `outputs/dungeon-master/10005-BC/review.md`,
  `outputs/dungeon-master/10007-BC/review.md`
