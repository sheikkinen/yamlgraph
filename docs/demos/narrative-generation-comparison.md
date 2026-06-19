# Narrative Generation: `novel_generator` vs `dungeon_master`

Two YAMLGraph examples solve the same underlying problem — *a story is too big for a single
prompt* — at opposite ends of a complexity spectrum. This note compares their approaches so
future authors can pick the right altitude for a new long-form generation task.

- `novel_generator` — [examples/demos/novel_generator/](../../examples/demos/novel_generator/)
- `dungeon_master` — [examples/dungeon_master/](../../examples/dungeon_master/)

## At a glance

| Dimension | `novel_generator` | `dungeon_master` (v2) |
|---|---|---|
| Purpose | Pedagogical showcase — one 84-line YAML | Production-grade interactive narrative system |
| Code | 100% YAML, zero Python | ~30 Python modules + 9 graphs + 10 prompts + FastAPI/HTMX UI |
| Control model | Batch pipeline (DAG) | Stateful play loop (turn-by-turn) |
| Scope unit | Whole book in one pass | Chapter → turn → actor, forward-carried |
| State | 9 keys, memory-only, ephemeral | Per-session `story.json`, typed ledgers, seam packets |
| Human role | None (fire-and-forget) | "One keystroke from changing anything, one click from accepting" |
| Continuity | Single review/revise gate | Typed ledger + bi-temporal reconciliation + lifecycle gates |
| Final assembly | Implicit (`prose_sections` collected) | Deterministic `compose_book_deterministic` (no LLM) |

## How they work

### `novel_generator` — three clean phases

Each phase demonstrates one YAMLGraph primitive:

1. **Ideation**: `generate → analyze → evolve` loop, gated on a letter grade
   (`analysis.grade > 'B'`).
2. **Generation**: a single `map` node fans out prose generation across `timeline.beats`,
   collected into `prose_sections`.
3. **Review**: `review → revise` conditional loop on `review.passed`.

All flow is forward; once prose is generated it is only surgically revised. No persistence,
no Python.

### `dungeon_master` — generation as a conversation with the text

The book is the spine: synopsis → cast → fixed chapter outline → **play each chapter
turn-by-turn**, carrying a typed `world_state` ledger forward → compose the book
deterministically. Each turn is `map(cast → intents) → director → recap`, looping until the
director signals `scene_complete`. Between chapters, `chapter_close` derives a typed ledger
*delta* and a `seam_packet` of continuity constraints; `chapter_reoutline` (FR-523)
re-derives the next chapter's beats from that state before play begins.

## Pros and cons

### `novel_generator`

**Pros**

- **Legibility**: the entire system fits in one readable file; topology is obvious in a diff.
- **Demonstration value**: cleanly isolates the three core patterns (evolution loop, map
  node, review gate) — ideal as a template and teaching artifact.
- **Safety by default**: loop limits on every iterative node, `max_items: 20` on the map.
- **Zero platform coupling**: pure YAML, trivially testable and reproducible.

**Cons**

- **Untyped seams**: beats are pipe-delimited strings (`"beat_1|1|summary|chars|7"`) parsed
  by each downstream prompt — fragile if the format drifts. Violates the project's own
  "normalize at the boundary" law.
- **Stringly-typed gating**: `grade > 'B'` relies on ASCII ordering with no validation the
  value is a real grade.
- **Weak continuity**: one whole-draft review gate is the only coherence mechanism; no memory
  of entities across beats, so contradictions can survive.
- **Dead state**: `revised_sections` is written but never read — the review loop re-reads
  `prose_sections`, so revisions may not actually feed forward.
- **No count enforcement**: if the timeline returns fewer beats than `target_beats`, it
  silently proceeds.

### `dungeon_master`

**Pros**

- **Typed ledger-as-memory**: relationships/objects/facts validated at the boundary, with
  bi-temporal reconciliation and mechanical decay — eliminates the silent-contradiction class
  of bugs entirely.
- **Deterministic where it can be**: ledger application, beat canonicalization, and
  whole-book assembly are pure code, so manuscript integrity is guaranteed by construction,
  not LLM consistency.
- **Hard continuity gates**: lifecycle state machine + `cast_exits` prevent dead/absent
  characters from acting.
- **Human-in-the-loop**: every stage is editable/acceptable; director output is *advisory
  signal*, never auto-applied (except roster filtering).
- **Observability**: witness/replay harnesses measure continuity without mocking; the same
  adapter powers both the UI and headless generation.

**Cons**

- **High complexity**: ~30 modules, 9 graphs, FastAPI UI, multiple interlocking FRs
  (FR-499/506/507/513–518/521/523). Steep to understand and maintain.
- **Many subtle invariants**: ledger *delta* semantics (forgetting to reaffirm ≠ deleting),
  off-by-one in `allowed_reappearance_from_chapter` can bar a character forever, exact
  name-matching required for continuity detection.
- **Generative seams can still poison state**: if `chapter_close` hallucinates a
  grounded-looking fact, boundary parsing will not always catch it.
- **Context windowing tradeoffs**: the 3-turn recap window bounds cost but can hide events
  more than three turns back.
- **Provider-fragile spots**: e.g. reasoning-budget starvation on `chapter_close` (FR-261)
  needed tuning to stop thinking tokens from eating the JSON output.
- **Ephemeral sessions**: no resume UI; reload mints a new session and orphans the old
  `story.json`.

## The core tradeoff

They are the same problem solved at two different altitudes:

- `novel_generator` keeps everything in one YAML by accepting **prose as the unit of memory**
  — elegant, but continuity is "best effort" and the seams are untyped strings.
- `dungeon_master` drops to chapter/turn granularity and makes **resolved typed state the
  unit of memory** — buying controllability, iterability, and provable continuity at the cost
  of substantial Python machinery and many invariants to uphold.

## Which to reach for

- **Teaching YAMLGraph primitives or scaffolding a 3-phase pipeline** → `novel_generator` is
  the reference template.
- **Sustaining a coherent long narrative with human steering** → `dungeon_master` is the
  architecture.

The one transferable lesson for `novel_generator` is to **type the beat seam and carry a
small entity ledger** rather than passing pipe-delimited strings between phases.
