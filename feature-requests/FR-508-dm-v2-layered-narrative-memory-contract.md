# Feature Request: FR-508 - DM v2 Layered Narrative Memory Contract

**Priority:** HIGH
**Type:** Enhancement
**Status:** Judged - Granted
**Effort:** ~3 days
**Requested:** 2026-06-17

## Summary

Introduce a layered narrative memory contract for Dungeon Master generation:
deterministic chapter summaries, rolling synopsis updates, and a hard chapter
opening one-pager assembled from structured state. The goal is to prevent
cross-chapter continuity drift that current lifecycle gate logic can detect but
not always preempt.

## Redraft Response To Anticipated Judgement

This redraft resolves likely grant blockers explicitly:

1. Memory layers are non-overlapping and have distinct authority.
2. Input timing and source precedence are explicitly defined at chapter
  boundaries.
3. Violation surface is typed and machine-checkable, not prose-only.
4. Witness metrics are measurable and tied to concrete pass/fail thresholds.
5. Parse-time normalization and semantic enforcement are separated.

## Redraft v2 Response To Judgement

This revision resolves the formal judgement blockers:

1. Chapter turn-1 lifecycle source is fixed to a canonical committed seam
  pointer from chapter N-1 close.
2. Precedence is split into two domains: event-timing and world-truth.
3. Error contract is aligned with FR-507 via a typed hierarchy and shared
  payload envelope.
4. Legacy document migration defaults are explicit and deterministic.
5. Witness success thresholds and extraction method are specified.

## Value Statement

Story generation gets a single authoritative memory surface for each chapter
opening, reducing continuity regressions and improving gate pass rates without
loosening deterministic enforcement.

## Problem

Run 10010 demonstrates a higher-level architecture gap:
- Lifecycle gate correctly detects contradictions and blocks invalid openings.
- The run still degrades because upstream memory remains fragmented across
  free-form recap text, seam packet deltas, and static synopsis context.
- Chapter opening generation lacks a deterministic, consolidated contract of
  "what is true now" and "what must not regress".

Observed failure pattern in run 10010:
- Repeated lifecycle gate failures on chapter opening turn 1.
- Contradictory lifecycle states at chapter boundaries (dead/rumor-only vs
  active presence signals).
- Generation eventually times out before full completion.

Conclusion: detection is strong; source-of-truth memory composition is weak.

## Proposed Solution

Add a three-layer memory model and use it to build a deterministic chapter
opening contract.

### 1) Structured chapter summary at chapter close

Persist a typed chapter summary payload (chapter_memory) per chapter card:
- `resolved_events`: list[str] (bounded)
- `irreversible_facts`: list[str] (bounded)
- `character_state_deltas`: list[dict]
  - `name`: str
  - `from_state`: str | null
  - `to_state`: str
  - `evidence`: str
- `open_threads`: list[str]
- `forbidden_regressions`: list[str]

Rules:
- Parse-time normalization is shape-safe only.
- Semantic checks ensure irreversible facts cannot be silently removed in later
  chapter memory without an explicit overturn event.

Deterministic boundaries:
- Generated exactly once during chapter close.
- Stored under chapter card for the closed chapter id.
- Not edited during turn generation.

### 2) Rolling synopsis updater (state-of-book)

Maintain a concise live_synopsis updated after each chapter close:
- Captures book-level state after chapter N, not the initial premise.
- Uses structured chapter memory + seam packet to update deterministically.
- Preserves a small immutable ledger section for critical continuity facts
  (death status, returns, sworn alliances, irreversible injuries/oaths).

live_synopsis replaces static synopsis as primary opening context source.

Immutable ledger rule:
- Ledger entries are append-only unless an explicit overturn event is present in
  chapter_memory.character_state_deltas with evidence.

### 3) Deterministic chapter opening one-pager

Build opening_onepager for chapter N turn 1 from:
- previous chapter chapter_memory
- lifecycle seam snapshot
- live_synopsis
- chapter outline metadata for N

opening_onepager output fields:
- `opening_truths`: list[str]
- `must_include`: list[str]
- `must_exclude`: list[str]
- `active_cast_constraints`: list[str]
- `continuity_checks`: list[str]

Turn generation consumes only this compiled opening contract plus current
instruction. Free-form recap remains secondary and cannot override one-pager
constraints.

Deterministic timing:
- Compile once at chapter N turn 1 before direct prose generation.
- Reuse same opening_onepager for retries within the same turn.

Boundary source rule (hard requirement):
- For chapter N turn 1, lifecycle validation reads only
  `doc.chapters.cards[N-1].seam_packet` through a canonical pointer resolved at
  chapter-open start.
- In-progress chapter N outputs are never used as lifecycle truth for the same
  chapter's opening gate.
- If chapter N-1 seam packet is missing, use deterministic empty seam defaults
  and record migration warning code `CONTINUITY_MIGRATION_DEFAULT_APPLIED`.

### 4) Boundary precedence contract

Define strict precedence in two non-overlapping domains.

Event-timing domain (who may appear/act now):
1. lifecycle seam packet (canonical N-1 committed source)
2. opening_onepager active_cast_constraints
3. recap text (advisory only)

World-truth domain (what is currently true):
1. chapter_memory.irreversible_facts (authoritative)
2. live_synopsis immutable ledger
3. lifecycle seam packet descriptive fields
4. recap text (advisory only)

If sources conflict, higher precedence wins and contradiction is surfaced as a
typed continuity violation.

Overturn rule:
- `chapter_memory.irreversible_facts` cannot be removed or contradicted unless
  an explicit overturn record exists in `character_state_deltas` with
  non-empty evidence.

Typed continuity violation payload:

```json
{
  "code": "CONTINUITY_MEMORY_CONFLICT",
  "chapter_id": "7",
  "turn_n": 1,
  "violations": [
    {
      "type": "state_conflict",
      "name": "Arnulf",
      "higher_source": "seam_packet",
      "lower_source": "live_synopsis",
      "detail": "confirmed_dead conflicts with alive/present"
    }
  ]
}
```

Standardized payload envelope (shared with FR-507-style gate failures):
- `code`: str
- `chapter_id`: str
- `turn_n`: int
- `violations`: list[dict]
- `source_pointer`: dict
  - `chapter_id`: str  # source seam chapter id used for this gate
  - `seam_hash`: str  # deterministic hash of normalized seam payload
  - `resolved_at`: str  # ISO timestamp when pointer resolved

source_pointer stability contract:
- For one chapter-open attempt, source_pointer values are immutable across retries.

Error behavior:
- Fail-fast on turn 1 with typed exception.
- Log warning with full payload.
- Propagate through existing session error surface.

Exception hierarchy:
- `ContinuityMemoryConflictError(LifecycleGateError)` for memory-precedence and
  source-conflict failures.
- Existing `LifecycleGateError` remains authoritative for pure lifecycle FSM and
  early-return violations.
- Both exceptions share the standardized payload envelope above.

### 5) Parse vs semantic enforcement split

Parse-time normalization (shape only):
- truncate oversized strings/lists,
- coerce nullable fields,
- dedupe repeated names by normalized key.

Semantic enforcement (contract only):
- no silent removal of irreversible facts,
- no source-precedence inversions,
- no lifecycle contradiction in opening cast contract.

### 6) Legacy migration contract

Load-time deterministic defaults for existing documents:
- missing `chapter_memory` -> initialize with empty typed object per chapter
  card on first close.
- missing `live_synopsis` -> initialize with empty summary + empty immutable
  ledger.
- missing seam packet in prior chapter -> use FR-506 default seam payload.

Migration behavior:
- no random or model-derived fill values during migration,
- migration must be idempotent,
- migration path must not relax gate strictness.

## Acceptance Criteria

- [ ] **A1 - Chapter memory schema implemented and persisted.**
  Each closed chapter stores a normalized typed `chapter_memory` payload with
  required fields and bounded lists.

  Required schema keys per chapter memory object:
  - resolved_events
  - irreversible_facts
  - character_state_deltas
  - open_threads
  - forbidden_regressions

- [ ] **A2 - Live synopsis is rolling and deterministic.**
  live_synopsis updates after each chapter close from structured inputs and
  contains immutable continuity ledger entries.

  Determinism requirement:
  - identical chapter_memory + seam inputs produce identical synopsis output.

- [ ] **A3 - Opening one-pager is compiled from structured memory.**
  Chapter turn-1 context uses compiled opening_onepager instead of ad-hoc
  recap stitching.

  Opening contract requirement:
  - direct generation prompt receives opening_onepager fields.
  - recap text cannot override must_exclude constraints.

- [ ] **A4 - Precedence contract enforced.**
  Conflicts between seam, chapter memory, synopsis, and recap are resolved by
  deterministic priority, with typed violations on contradictions.

  Violation requirement:
  - payload includes conflict type, entity name, higher source, lower source,
    and detail.

- [ ] **A5 - Floodmark witness stability target met.**
  Re-run premise class of 10010 shows:
  - zero lifecycle gate violations,
  - zero dead/alive opening contradictions,
  - no turn-cap timeout attributable to continuity rejection loops,
  - completed generation with chapter close/final cut progression intact.

  Completion threshold:
  - completed_chapter_count must equal planned chapter count in
    `chapters.order` for the witness run.
  - book gate opens before configured turn cap.

  Witness metric log fields to record:
  - lifecycle_gate_violation_count
  - continuity_memory_conflict_count
  - completed_chapter_count
  - total_turns_used

  Extraction method (must be scripted in witness notes):
  - parse generation log for typed gate/conflict payload counts,
  - parse story artifact for completed chapter count and planned chapter count,
  - report pass/fail against thresholds in one summary table.

- [ ] **A6 - Tests and docs updated.**
  Unit tests for schema/normalization/composition, integration tests for turn-1
  context assembly and precedence enforcement, architecture docs updated with
  three-layer memory model.

  Required test classes:
  - chapter memory schema + normalization unit tests
  - synopsis determinism unit tests
  - opening one-pager composition unit tests
  - precedence conflict integration tests
  - Floodmark witness regression test harness update

## Implementation Status (2026-06-17)

Completed in this enforcement slice:
- Added deterministic chapter_memory derivation at chapter close from normalized
  seam packet fields.
- Persisted chapter_memory on chapter cards during apply_chapter_close.
- Added rolling live_synopsis update with immutable_ledger append semantics and
  deterministic chapter summary text.
- Added tests for chapter_memory derivation and live_synopsis persistence.
- Added opening_onepager compilation at chapter turn-1 and injected it into
  running scene context.
- Added typed memory-precedence conflict gate with
  `CONTINUITY_MEMORY_CONFLICT` payload and source_pointer metadata.
- Added tests covering opening_onepager presence and precedence-conflict
  fail-fast behavior.
- Added deterministic FR-508 witness metrics utility and CLI script to extract
  lifecycle/conflict counts, chapter completion counts, turn usage, and overall
  pass/fail from generation log + story artifact.
- Hardened witness evaluation semantics so `book_gate_opened_before_turn_cap`
  cannot pass on partial/in-progress artifacts (requires full chapter
  completion parity).

Acceptance progress:
- A1: in progress (core shape + persistence implemented).
- A2: in progress (deterministic updater + immutable ledger append implemented).
- A3: in progress (turn-1 onepager compile + context injection implemented).
- A4: in progress (typed precedence conflict gate implemented for structured
  state sources).
- A5: in progress (witness metrics extraction tooling implemented; re-witness
  pass target pending).
- A6: in progress (tests expanded for A3/A4/A5 metric tooling; docs still pending).

## Implementation Notes

Primary insertion points:
- `examples/dungeon_master/api/chapter_ops.py`
  - emit and validate structured chapter summary at close
- `examples/dungeon_master/api/doc_ops.py`
  - persist chapter memory and rolling synopsis fields
- `examples/dungeon_master/api/turn_ops.py`
  - compile and enforce opening one-pager before turn-1 generation
- prompt contracts:
  - `examples/dungeon_master/prompts/chapter_close.yaml`
  - `examples/dungeon_master/prompts/turn_direct.yaml`
  - `examples/dungeon_master/prompts/character_intent.yaml`

Non-goals:
- Replacing lifecycle gate fail-fast behavior (FR-507 remains authoritative).
- Narrative style rewriting unrelated to continuity memory boundaries.

Data model placement:
- chapter_memory: under chapters.cards[chapter_id]
- live_synopsis: top-level doc synopsis runtime field
- opening_onepager: ephemeral per-turn compiled structure (not canonical store)

## Alternatives Considered

1. Expand seam packet only.
Result: rejected. Seam packet is a delta contract, not sufficient long-horizon
book memory.

2. Use recap prose as canonical memory.
Result: rejected. Free-form prose is too unstable for deterministic continuity
enforcement.

3. Disable strict gate for longer runs.
Result: rejected. This hides causality defects instead of fixing memory source
quality.

## Enforce Sequence (TDD)

1. RED: add failing tests for opening contract composition and precedence.
2. RED: add failing witness fixture reproducing 10010 contradiction loop.
3. GREEN: add chapter_memory schema + normalization + persistence.
4. GREEN: add rolling live_synopsis updater with immutable ledger.
5. GREEN: add opening_onepager compiler and turn-1 integration.
6. GREEN: add precedence conflict validator with typed continuity violation.
7. WITNESS: run Floodmark scenario and record metrics/time-to-complete.
8. Distill: diary entry on memory layering and boundary precedence.

## Related

- FR-505 - final cut prose de-gridding
- FR-506 - DM v2 chapter seam continuity contract
- FR-507 - DM v2 character lifecycle seam gate
- Witness run: `outputs/dungeon-master/10010-BC/story/story.json`
- Generation log: `logs/gen-10010-azure.log`
