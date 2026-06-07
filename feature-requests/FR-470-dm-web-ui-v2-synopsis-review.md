# Feature Request: FR-470 DM Web UI v2 — Synopsis Review (Phase A)

**Priority:** LOW
**Type:** Enhancement
**Status:** Implemented — GREEN (2026-06-06)
**Effort:** 1 phase
**Requested:** 2026-06-06

## Summary

First phase of the DM Web UI v2 redesign: stop eagerly weaving the first beat
during preplan, and make the **synopsis a first-class, reviewable card** on the
main panel with **regenerate / edit / accept** actions. This is Phase A of the
journey-focused redesign in [docs/dm-ui-v2.md](../docs/dm-ui-v2.md), which
supersedes the *interaction model* of [FR-468](FR-468-dungeon-master-web-ui.md)
(the forward-only beat treadmill) without touching its graphs.

## Value Statement

The Dungeon Master gets to **read and shape the story's premise before any prose
is generated** — turning the opening from an opaque, auto-rendered beat into a
deliberate authoring decision, and proving that generation in a YAMLGraph web app
can be invoked on demand rather than eagerly.

## Problem

v1 (FR-468) runs the turn-loop's first `weave` *inside* `preplan()` and surfaces
only the woven `draft_beat`. The synopsis (logline, conflict, themes, tone, arc)
is computed but hidden — only the logline leaks into the aside. The DM cannot
re-roll or edit the story's foundation; the very first thing they see is an
already-rendered ending. **The journey to the story is the point** (per
docs/dm-ui-v2.md §1), and it must start with the synopsis.

## Proposed Solution

A pure Layer-1 change plus a thin side-effect store. **No graph or prompt
changes** in this phase — `synopsis` is invoked as a single-node call via the
existing `prompts/synopsis.yaml`.

### Decouple navigation from generation (foundation laid here)

- **Story document store** (`api/story_doc.py`, new): per-session JSON holding the
  skeleton (`synopsis`, `cast`, `chapters`) as the source of truth the UI reads
  and edits — replacing the checkpointer as the web persistence layer
  (docs/dm-ui-v2.md §4, O3). This phase persists and mutates only the `synopsis`
  block; chapters/beats are stored as produced by preplan but not yet browsed.
- **`DMSession` rework:** `preplan()` stops after the skeleton — **no eager
  weave**. New methods: `regenerate_synopsis(session_id)` (re-invoke synopsis),
  `edit_synopsis(session_id, fields)` (persist DM edits), `accept_synopsis(
  session_id)` (mark reviewed → advance to the outline placeholder).

### Routes

| Method | Path | Form fields | Action | Returns |
|--------|------|-------------|--------|---------|
| POST | `/story/preplan` | `session_id`, `premise`, `chapter_count`, `cast_size` | Run preplan → skeleton; **no weave** | synopsis-review card |
| POST | `/story/synopsis/regenerate` | `session_id` | Re-invoke `synopsis` | synopsis-review card |
| POST | `/story/synopsis/edit` | `session_id`, `logline`, `conflict`, `themes`, `tone`, `arc` | Persist edits to the document | synopsis-review card |
| POST | `/story/synopsis/accept` | `session_id` | Mark reviewed; advance | outline placeholder (Phase B fills it) |

### Templates

- New main-panel **synopsis-review** mode (`components/synopsis_card.html`):
  editable fields for logline/conflict/themes/tone/arc + **Regenerate / Accept**
  controls, in the existing parchment theme.
- Breadcrumb shows `Story · Synopsis` (docs/dm-ui-v2.md §6).

## Capability / Requirement

Creates **`CAP-170-dungeon-master-web-ui-v2.yaml`** carrying `REQ-YG-468`
(this FR), `REQ-YG-469` (FR-471), `REQ-YG-470` (FR-472).

- **REQ-YG-468** After preplan, the main panel shows a **synopsis card** (the five
  synopsis fields) and **no woven beat is present**; **regenerate** re-rolls the
  synopsis; **edit** persists changed fields to the story document; **accept**
  advances past the synopsis. LLM mocked at `llm_nodes.execute_prompt`.

## Acceptance Criteria

- [x] `preplan()` no longer eagerly weaves; first view is the synopsis card
- [x] `api/story_doc.py` persists/loads a per-session story document (synopsis block)
- [x] Regenerate / edit / accept routes + `DMSession` methods implemented
- [x] `components/synopsis_card.html` renders the five fields + controls in theme
- [x] Breadcrumb reads `Story · Synopsis`
- [x] Witness test `@pytest.mark.req("REQ-YG-468")`, LLM mocked, asserts: synopsis
      card present, **no `draft_beat`/beat-card** after preplan, regenerate returns
      a fresh synopsis, edit persists, accept advances
- [x] `CAP-170-dungeon-master-web-ui-v2.yaml` registers REQ-YG-468 (only)
- [x] Changelog fragment **and** diary entry in the PR
- [ ] `demo-output.log` updated (demo-gate) — deferred to FR-472 (full v2 demo
      rewrite per J4); dungeon-master is not under `examples/demos/` so demo-gate
      does not apply
- [x] FR-468 README/demo reconciled so the web path no longer implies an eager
      forward-only loop (eager-weave / six-control claim removed; full rewrite in
      FR-472)

## Alternatives Considered

- **Keep the checkpointer as the web store** and add a document-shaped state:
  rejected (docs/dm-ui-v2.md O3) — navigation/editing are not graph concerns; a
  plain JSON store is simpler and enables random access in Phase B.
- **Make `preplan.yaml` stepwise (pause after synopsis inside the graph):**
  rejected — the pause is a presentation concern; calling `synopsis` as a single
  node from the session keeps the graph reusable for the CLI.

## Related

- Plan: [docs/dm-ui-v2.md](../docs/dm-ui-v2.md) (Phase A)
- Supersedes interaction model of [FR-468](FR-468-dungeon-master-web-ui.md)
- Next: [FR-471](FR-471-dm-web-ui-v2-outline-nav.md) (Phase B),
  [FR-472](FR-472-dm-web-ui-v2-beat-generation.md) (Phase C)

## Judgment (2026-06-06)

Judged against the live web layer (`api/session.py`, `api/routes/story.py`),
the preplan graph (`preplan.yaml`), the persisted skeleton writer
(`nodes/story_io.py::save_story_tool`), and the CI gates (`CLAUDE.md`).
**Approved with corrections folded in; scope frozen.**

Defects found and resolved:

- **J1 (no parallel store — reuse `story.json`).** The proposal's
  `api/story_doc.py` must **not** invent a second persistence file.
  `save_story_tool` already writes `<session>/story.json` with
  `synopsis`/`plot`/`chapters`/`cast`. The v2 document store is a **read/edit
  wrapper over that same `story.json`** (plus a v2 overlay — `reviewed` flag
  here, `beats[]`/`status` in later phases). One file, one source of truth.
- **J2 (synopsis regeneration invocation + exact mock target).** The session
  currently drives *compiled graphs*, not single prompts; `preplan()` removes the
  turn-loop `ainvoke` and stops after the preplan graph. **Regenerate** invokes
  the synopsis prompt directly via `yamlgraph.executor.execute_prompt("synopsis",
  {"premise": ...})` and overwrites the `synopsis` block in `story.json`. The
  witness test therefore mocks **`yamlgraph.executor.execute_prompt`** (not
  `node_factory.llm_nodes.execute_prompt` — that path only covers graph nodes).
  The full preplan still runs through the graph, so the preplan call in the test
  mocks the `llm_nodes` path as today; assert the mock target per call site.
- **J3 (incremental CAP registration).** `CAP-170` is **created here registering
  only `REQ-YG-468`.** FR-471/FR-472 append their REQ when they land. Registering
  all three up front would make `req_coverage --strict` red until Phases B/C ship.
- **J4 (README ownership).** This phase only **deletes the eager-weave / six-
  control claim** from the README/demo so they aren't actively wrong; the full v2
  "Web UI" rewrite is owned by **FR-472** (Phase C), when the journey is complete.
  Acceptance item below amended accordingly.
- **J5 (view model).** The turn-centric `TurnResult` does not fit a synopsis card;
  introduce a small `SynopsisView` (the five fields + `reviewed`) for this mode.
  `TurnResult` stays for the beat-view mode reused in Phase C.

Amended acceptance: the README item reads *"remove the eager-weave / six-control
description from the README so it is not actively wrong (full rewrite deferred to
FR-472)"*; CAP item reads *"create `CAP-170` registering `REQ-YG-468` only"*.

## Follow-up — Synopsis as a single editable text (2026-06-06)

Post-implementation, the synopsis was simplified from five structured fields to a
single prose paragraph. Motivation (from a granularity review): downstream preplan
prompts (plot/chapters/cast) only ever consumed `{{ synopsis }}` as one opaque
blob — the five-field split was UI-only ceremony, and storing a dict made the blob
render as a Python repr.

Changes (TDD, all GREEN):
- `prompts/synopsis.yaml` now emits one paragraph (no `output_schema`, no JSON).
- `preplan.yaml` synopsis node `parse_json: false` → `state.synopsis` is a string;
  `save_story` stores a string; downstream templates render clean text.
- `SynopsisView` collapses to `text: str` (+ `reviewed`, `error`); module helper
  `_synopsis_text` normalizes dict-or-string at the boundary (legacy-tolerant).
- `edit_synopsis(text)` and the `/story/synopsis/edit` route take a single `text`.
- New shared `components/text_block.html` macro renders a full-height parchment
  editor; both the synopsis card and the woven-beat view use it (`stage=True`),
  so the synopsis editor fills the viewport like the beat stage. `.beat-card` and
  `.text-block` now share CSS; `.text-block-form` is a flex column that grows.

`REQ-YG-468` description updated in `CAP-170`. CAP-170 now 3/3 reqs, 19 tests.
