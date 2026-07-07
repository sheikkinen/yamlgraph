# Feature Request: FR-690 — Event Sequence Field for Intra-Year Ordering

**Priority:** HIGH
**Type:** Enhancement
**Status:** Judged ✅ (amendments folded into body; Judgement retained as decision history)
**Effort:** 0.5 days
**Requested:** 2026-07-07
**Judged:** 2026-07-07
**Plan:** docs/plan-novel-fandom-story-pipeline.md (Phase 1 of 7)

## Summary

Add `sequence: int` to the novel_fandom `Event` schema and backfill the 22 existing Floodmark events from synopsis order. Port of Gen 1's `Beat.sequence` (`langgraph-poc-narrator/src_novel/models/synopsis.py`).

## Value Statement

Downstream story-pipeline steps (throughline timeline walk, chapter planning) get a canonical event order instead of silently inventing one.

## Problem

19 of 22 events sit at `year: 0` with no intra-year ordering. The story pipeline's throughline walk (FR-691) and chapter plan (FR-694) both require a total order over events. Without a `sequence` field, each LLM pass invents its own ordering the canon does not state — a `plausible_wrong_answer` factory.

## Proposed Solution

1. Add `sequence: int | None = None` to `Event` in `examples/novel_fandom/schema/canon.py`. Optional at the Pydantic layer so `create_event`/genesis (whose inline schemas do not emit it) keep validating; the story pipeline's mechanical check makes it mandatory for the Floodmark canon. Teaching `create_event` to assign `sequence` is FR-693 scope (the first FR that creates events after threads exist). Semantics: global total order across all events (not per-year); gaps allowed (10, 20, 30 …) so later insertion needs no renumbering.
2. Backfill all 22 events. Primary source: synopsis narrative order. Events not narrated in the synopsis (e.g. `reinthilde_birth`, framing events) are placed by `year` and a causal reading of their `consequences`; the full sorted listing is raw-read against the synopsis in review.
3. Mechanical check as **Python, not an LLM graph** (`ref_check` is the wrong tool for arithmetic): a reusable function in `examples/novel_fandom/nodes/` + pytest in `tests/unit/test_fr690_event_sequence.py` asserting (a) every Floodmark event has non-null `sequence`, (b) values unique, (c) `year` ordering never contradicts `sequence` ordering (for any two events with differing years, sequence order agrees with year order).

## Acceptance Criteria

- [ ] `Event` schema has `sequence: int | None = None`; all 47 canon files still validate; genesis/create_event untouched
- [ ] 22 events backfilled with unique, gapped values; sorted listing raw-read against synopsis in review
- [ ] Python check fails on fixtures with (a) missing sequence, (b) duplicate, (c) year/sequence contradiction — RED committed first
- [ ] Tests tagged `@pytest.mark.req("REQ-YG-523")`; CAP-175 extended with REQ-YG-523 (sequence ordering) — extension of existing canon-schema capability, no new CAP file
- [ ] Changelog fragment with `req: REQ-YG-523`

## Alternatives Considered

- **`day: int` per year** — insufficient: multiple events share days on the ledge; sequence is what consumers need, calendar precision is not.
- **Ordering in a separate manifest file** — splits truth across two files; the event page is the boundary where the event is defined.

## Related

- Plan: docs/plan-novel-fandom-story-pipeline.md
- Diary: docs/diary/diary-2026-07-06-the-dropped-plot-layer.md (Gen 1 `Beat.sequence`)
- Blocks: FR-691, FR-694

## Judgement (2026-07-07)

**Verdict: APPROVED with amendments (folded into body above).**

1. **Required → optional at the Pydantic boundary.** As proposed, required `sequence: int` breaks every future `create_event`/genesis run — their inline schemas don't emit the field. Enforcement moves to the mechanical check (mandatory for Floodmark); `create_event` support explicitly deferred to FR-693. This is `the_one_law` applied correctly: the schema is shared by two producers; only one is in scope.
2. **`ref_check` extension rejected.** Uniqueness and order consistency are arithmetic; putting them in an LLM graph-tool is the inverse of the LLM-over-regex rule. Python function + pytest.
3. **Backfill source disambiguated.** Synopsis order is partial (not all events are narrated); year + consequences fill the gaps, and the sorted listing is raw-read in review — the substance check for a `plausible_wrong_answer` ordering.
4. **Traceability:** extend CAP-175 with REQ-YG-523 rather than minting a CAP file for one field.

Scope frozen. Path is explicit and minimal. Authority granted.
