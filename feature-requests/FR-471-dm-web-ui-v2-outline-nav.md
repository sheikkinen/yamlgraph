# Feature Request: FR-471 DM Web UI v2 — Outline Browse + Breadcrumb Nav (Phase B)

**Priority:** LOW
**Type:** Enhancement
**Status:** Implemented — GREEN (2026-06-06)
**Effort:** 1 phase
**Requested:** 2026-06-06

## Summary

Second phase of the DM Web UI v2 redesign: extend preplan to emit **beat stubs**
per chapter, then make the chapters and their beats a **browseable, inline-editable
outline** with a **breadcrumb that navigates** (synopsis ↔ chapter ↔ beat). This
is Phase B of [docs/dm-ui-v2.md](../docs/dm-ui-v2.md) and builds directly on the
story-document store and synopsis-review flow from
[FR-470](FR-470-dm-web-ui-v2-synopsis-review.md).

## Value Statement

The Dungeon Master can **walk the planned story — chapter by chapter, beat by
beat — and make small edits anywhere**, with the breadcrumb as a real navigation
control, turning the opaque skeleton into an explorable, shapeable outline before
any prose is rendered.

## Problem

After FR-470 the DM can review the synopsis, but the chapters and their beats are
still inert: there are no beat stubs, no way to browse chapter→beat, and the
breadcrumb is a status readout, not navigation (docs/dm-ui-v2.md §6). The journey
requires the DM to **browse the preplanned chapters/turns/beats and edit here and
there** (docs/dm-ui-v2.md §2.3) — which needs (a) beat stubs to browse and (b)
random-access navigation the v1 forward loop cannot express (docs/dm-ui-v2.md §4).

## Proposed Solution

One small graph extension plus Layer-1 navigation/editing over the story document.

### Logic — beat stubs (the only graph change in v2 so far)

- **`prompts/beats.yaml` (new):** given a chapter's goal/setting + the cast, emit
  an ordered list of **2–5 one-line beat stubs** (planned intentions, no prose).
  Inline `output_schema`: `{beats: [{stub: str}]}`.
- **`preplan.yaml` (extend):** after `chapters`, add a `beats` node. Per
  docs/dm-ui-v2.md O2, beat stubs are generated **lazily per chapter on first
  visit** (cheaper; chapter shows its stubs when opened) — so this node is invoked
  on demand from the session, not eagerly across all chapters at preplan time.

### Side effects — story document addressing

- **`api/story_doc.py` (extend):** address a beat by `(chapter_index, beat_index)`;
  store per-beat `stub` / `status` (`planned`); update a chapter `summary`; update
  a beat `stub`; mark a chapter's stubs as materialized (lazy-fill guard).

### Presentation — browse + edit + navigable breadcrumb

- **`DMSession`:** `navigate(session_id, chapter, beat=None)` (returns the
  addressed view, lazily filling beat stubs on first chapter visit),
  `edit_chapter(session_id, chapter, summary)`, `edit_beat_stub(session_id,
  chapter, beat, stub)`.
- **Routes:** `GET /story/nav` (chapter/beat target → swap `#app-body`),
  `POST /story/chapter/edit`, `POST /story/beat/edit`.
- **Templates:** new **outline-browse** mode (`components/outline.html`) listing
  chapters → beat stubs with inline-editable summaries/stubs and per-beat
  **status** badges; the breadcrumb (`components/breadcrumb.html`) becomes clickable
  — `Story · Synopsis` / `Story · Ch 2/3 · Outline` / `Story · Ch 2/3 · Beat 1/4`
  (docs/dm-ui-v2.md §6). Chapter dots and the per-chapter beat strip are nav links.

## Capability / Requirement

Adds `REQ-YG-469` to **`CAP-170-dungeon-master-web-ui-v2.yaml`** (created in
FR-470).

- **REQ-YG-469** Navigating to a chapter shows its **beat stubs** (lazily
  generated on first visit); editing a chapter summary or a beat stub **persists**
  to the story document; the **breadcrumb links target the correct view**
  (synopsis ↔ chapter ↔ beat); each beat shows a **planned** status badge. LLM
  mocked at `llm_nodes.execute_prompt`.

## Acceptance Criteria

- [x] `prompts/beats.yaml` produces 2–5 beat stubs per chapter (schema-validated)
- [x] ~~`preplan.yaml` gains a `beats` node~~ — **Judgment J2**: no preplan.yaml
      change; `beats` invoked lazily on first chapter visit (`_materialize`)
- [x] `api/story_doc.py` addresses/edits chapters and beats by index; lazy-fill guard
- [x] `navigate` / `edit_chapter` / `edit_beat_stub` session methods + routes
- [x] `components/outline.html` + `components/breadcrumb.html` render browse + nav
      (chapter view in `components/chapter.html`)
- [x] Breadcrumb crumbs and chapter links are working navigation links
- [x] Per-beat **status** badge visible (`planned` in this phase)
- [x] Witness test `@pytest.mark.req("REQ-YG-469")`, LLM mocked: chapter view shows
      stubs, edit persists, breadcrumb targets resolve, status badge present
- [x] Changelog fragment **and** diary entry in the PR
- [ ] `demo-output.log` updated (demo-gate) — deferred to FR-472 (full README +
      demo rewrite); demo-gate is N/A (no files under `examples/demos/`)
- [x] Three-layer import boundary intact (navigation stays out of graph state)

## Alternatives Considered

- **Generate all beat stubs eagerly at preplan time** (docs/dm-ui-v2.md O2):
  rejected for the default path — more LLM cost up front and slower preplan; lazy
  per-chamber filling matches "browse here and there." (Revisit if browse latency
  hurts.)
- **Reordering / inserting / deleting beats:** out of scope (docs/dm-ui-v2.md O6)
  — browse + edit + navigate only; structural editing is a later pass.
- **Drive navigation through a LangGraph checkpointer:** rejected (docs/dm-ui-v2.md
  §4/O3) — random access and per-beat editing are document operations.

## Related

- Plan: [docs/dm-ui-v2.md](../docs/dm-ui-v2.md) (Phase B)
- Prev: [FR-470](FR-470-dm-web-ui-v2-synopsis-review.md) (Phase A)
- Next: [FR-472](FR-472-dm-web-ui-v2-beat-generation.md) (Phase C)

## Judgment (2026-06-06)

Judged against `preplan.yaml`, the persistence boundary in
`nodes/story_io.py`, the v2 document store decided in FR-470/J1, and the CI
gates. **Approved with one structural correction; scope frozen.**

Defects found and resolved:

- **J1 (the contradiction — lazy stubs cannot be a `preplan.yaml` node).** A node
  added to `preplan.yaml` runs **eagerly for every chapter** during preplan,
  which directly contradicts the FR's own "lazily per chapter on first visit"
  (O2). **Resolution: do NOT touch `preplan.yaml`.** Beat stubs come from a new
  `prompts/beats.yaml` invoked **on demand by the session** the first time a
  chapter is opened, via `yamlgraph.executor.execute_prompt("beats", {...})`
  (same direct-prompt pattern as FR-470/J2). The witness test mocks
  **`yamlgraph.executor.execute_prompt`**. The earlier "only graph change in v2"
  framing is **struck** — v2 adds no node to the preplan spine; it adds one
  on-demand prompt here and one standalone graph in FR-472.
- **J2 (overlay shape).** The document store from FR-470 gains a per-chapter
  `beats: [{stub, status}]` overlay written back into `story.json`; a chapter's
  `materialized` flag guards the lazy fill so re-visiting a chapter does not
  re-roll its stubs. Editing a chapter `summary` or a beat `stub` is a plain
  document write — no graph, no LLM.
- **J3 (navigation is GET-safe).** `GET /story/nav` performs **no** generation
  except the one-time lazy stub fill on first chapter visit; that single side
  effect is acceptable (it is idempotent under the `materialized` guard). All
  edits remain POSTs. Keeps the three-layer boundary clean (navigation never
  enters graph state).
- **J4 (CAP registration).** Append `REQ-YG-469` to the existing `CAP-170`
  (created by FR-470); do not create a new capability file.

Amended acceptance: strike *"`preplan.yaml` gains a `beats` node"*; replace with
*"`prompts/beats.yaml` is invoked on demand by the session per chapter (no
`preplan.yaml` change); witness test mocks `yamlgraph.executor.execute_prompt`"*.
