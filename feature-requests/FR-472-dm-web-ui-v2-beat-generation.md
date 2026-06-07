# Feature Request: FR-472 DM Web UI v2 — On-Demand Beat Generation (Phase C)

**Priority:** LOW
**Type:** Enhancement
**Status:** Implemented — GREEN (2026-06-06)
**Effort:** 1 phase
**Requested:** 2026-06-06

## Summary

Final phase of the DM Web UI v2 redesign: a **"Generate beat"** button that weaves
a single **chosen** beat on demand via a new stateless `weave-beat.yaml` graph,
returns editable prose, and commits it to the chapter file on **Accept** — with
per-beat status flowing `planned → generated → committed`. This is Phase C of
[docs/dm-ui-v2.md](../docs/dm-ui-v2.md), completing the journey-focused model atop
[FR-470](FR-470-dm-web-ui-v2-synopsis-review.md) (synopsis review) and
[FR-471](FR-471-dm-web-ui-v2-outline-nav.md) (outline browse + nav).

## Value Statement

The Dungeon Master decides **which moment is worth fully rendering** and generates
it deliberately — replacing v1's auto-rendered, forward-only beat with explicit,
per-beat generation that can be re-rolled, edited, and committed in any order.

## Problem

After FR-471 the DM can browse and edit the outline, but every beat is still a
planned stub — there is no way to render prose for a chosen beat. v1's only
generation path is the eager, forward-only `turn-loop.yaml` weave, which cannot
render an arbitrary beat the DM selects (docs/dm-ui-v2.md §4). The journey ends at
**"generate the final beat for a beat of your choosing"** (docs/dm-ui-v2.md §2.4),
which requires single-beat, random-access, stateless generation.

## Proposed Solution

A new narrow graph for one-beat generation plus Layer-1 wiring; the v1
checkpointed loop is **not** used on the web path (it remains for the CLI).

### Logic — single-beat weave (new graph)

- **`weave-beat.yaml` (new):** inputs = the chosen beat's `stub`, its chapter
  goal/setting, the cast, and a **windowed `recent_history`** of prior committed
  beats (reuse `prep_turn`'s windowing logic, docs/dm-ui-v2.md O4); runs
  `plan_all` (the existing `map` over cast → character plans) + `weave`; outputs
  woven prose. **No checkpointer, no interrupt, no loop** — a pure function graph
  (docs/dm-ui-v2.md §4/§5, O1). Reuses existing `prompts/` (`plan`, `weave`) — no
  prompt changes expected.

### Side effects — commit + status

- **`api/story_doc.py` (extend):** set a beat's `woven` prose, flip `status`
  (`planned → generated → committed`), and append committed prose to the chapter
  file via the existing `nodes/story_io.py` writer (reuse `_slugify` /
  chapter-file write).

### Presentation — generate / edit / accept a chosen beat

- **`DMSession`:** `generate_beat(session_id, chapter, beat)` (run
  `weave-beat.yaml`, store `woven`, status → generated), `accept_beat(session_id,
  chapter, beat, text)` (persist edited/verbatim prose, write chapter file, status
  → committed).
- **Routes:** `POST /story/beat/generate`, `POST /story/beat/accept`.
- **Templates:** the **beat-view** mode reuses v1's editable beat card
  (`components/turn_result.html` lineage, docs/dm-ui-v2.md O5) but is reached only
  for a **generated** beat; a planned beat shows a **"Generate beat"** button;
  status badges across the outline update to `generated` / `committed`.

## Capability / Requirement

Adds `REQ-YG-470` to **`CAP-170-dungeon-master-web-ui-v2.yaml`** (created in
FR-470).

- **REQ-YG-470** For a planned beat, **Generate beat** runs `weave-beat.yaml` and
  yields editable prose with status **generated**; **Accept** persists the prose
  (verbatim or edited), writes it to the chapter file, and flips status to
  **committed**; generation targets the **chosen** beat (arbitrary chapter/beat),
  not a forced forward order. LLM mocked at `llm_nodes.execute_prompt`.

## Acceptance Criteria

- [x] `weave-beat.yaml` generates one beat (no checkpointer, no interrupt, no loop)
- [x] `recent_history` windowing reused from `prep_turn` (committed beats before the
      chosen one) — `DMSession._recent_history` windows the last 3 committed beats
- [x] `api/story_doc.py` stores `woven`, flips `planned → generated → committed`,
      writes the chapter file via `nodes/story_io.py`
- [x] `generate_beat` / `accept_beat` session methods + routes
- [x] Planned beat shows **Generate beat**; generated beat shows the editable card +
      **Accept**; status badges update
- [x] Generation works for an **arbitrarily chosen** beat (not forward-only)
- [x] Witness test `@pytest.mark.req("REQ-YG-470")`, LLM mocked: generate flips a
      planned beat to generated with prose; accept writes the chapter file and marks
      committed; a non-first beat can be generated directly
- [x] Changelog fragment **and** diary entry in the PR
- [x] `demo-output.log` updated — full v2 journey: preplan → synopsis review →
      browse → edit → generate a chosen beat → accept → commit
      (demo-gate is N/A: no files under `examples/demos/`)
- [x] README "Web UI" section rewritten for the v2 journey model (retires the v1
      six-control forward-loop description)
- [x] Three-layer import boundary intact; CLI `turn-loop.yaml` untouched

## Alternatives Considered

- **Reuse `turn-loop.yaml` (drive it to the chosen beat) instead of a new graph:**
  rejected (docs/dm-ui-v2.md §4/O1) — the checkpointed loop resumes linearly and
  cannot render an arbitrary beat without unwinding; a stateless single-beat graph
  is the smaller, correct primitive and leaves the CLI loop intact.
- **Feed all prior committed beats as context** (vs. windowed): rejected
  (docs/dm-ui-v2.md O4) — unbounded context cost; reuse `prep_turn`'s window.
- **Auto-generate the next beat after Accept** (re-introduce a forward loop):
  rejected — defeats the deliberate, choose-your-beat model that is the point of v2.

## Related

- Plan: [docs/dm-ui-v2.md](../docs/dm-ui-v2.md) (Phase C)
- Prev: [FR-470](FR-470-dm-web-ui-v2-synopsis-review.md) (Phase A),
  [FR-471](FR-471-dm-web-ui-v2-outline-nav.md) (Phase B)
- Reuses the `plan_all` + `weave` machinery from `turn-loop.yaml` and the chapter
  writer in `nodes/story_io.py`

## Judgment (2026-06-06)

Judged against `turn-loop.yaml` (`plan_all` map + `weave` + `prep_turn`
windowing), `nodes/story_io.py` (`commit_beat_tool`, `save_story_tool`,
`_slugify`), and the v2 document store from FR-470/FR-471. **Approved with two
corrections; scope frozen.**

Defects found and resolved:

- **J1 (`commit_beat_tool` is NOT reusable — it advances linearly).**
  `commit_beat_tool` is coupled to the turn loop: it advances `turn_number`,
  `chapter_index`, and appends to `history`. It **cannot** commit an arbitrary
  chosen beat without corrupting that linear counter. The chapter-file write is
  also **inline** in `save_story_tool`/`commit_beat_tool`, not an exposed helper.
  **Resolution:** extract a small pure helper
  `append_beat_to_chapter(output_dir, chapter_index, title, prose)` in
  `story_io.py` (reusing `_slugify` and the existing
  `chapter-NN-<slug>.md` naming), and have `story_doc`/`accept_beat` call it.
  `weave-beat.yaml` and the web commit path do **not** use `commit_beat_tool`.
- **J2 (weave context is passed in, not derived from graph state).**
  `prep_turn_tool` derives `chapter_goal` + `recent_history` from turn-loop
  *state* (`history[-3:]`). `weave-beat.yaml` is stateless, so the session builds
  the windowed context from the **story document's committed beats** (last 3
  before the chosen beat) and passes `chapter_goal` + `recent_history` as graph
  **variables**. `weave-beat.yaml` flow: `START → plan_all (map over cast) →
  weave → normalize_beat → END` — no `load_story`, no `prep_turn`, no
  checkpointer, no interrupt. Witness test mocks
  `node_factory.llm_nodes.execute_prompt` (covers the map sub-nodes + weave).
- **J3 (README + demo ownership lands here).** Per FR-470/J4, the **full** README
  "Web UI" rewrite for the v2 journey and the **rewrite of `api/demo.py`** to the
  v2 scripted flow (preplan → review synopsis → browse → edit → generate a chosen
  beat → accept) are owned by this phase, since the journey is only complete here.
- **J4 (CAP registration).** Append `REQ-YG-470` to `CAP-170`.

Amended acceptance: replace *"writes the chapter file via `nodes/story_io.py`"*
with *"writes via a new `append_beat_to_chapter` helper extracted in
`story_io.py`; `commit_beat_tool` is untouched and unused on the web path"*; add
*"`api/demo.py` rewritten to the v2 flow"*.
