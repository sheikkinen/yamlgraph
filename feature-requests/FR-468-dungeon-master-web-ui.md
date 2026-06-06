# Feature Request: FR-468 Dungeon Master Web UI

**Priority:** LOW
**Type:** Feature
**Status:** Judged — Approved (scope frozen 2026-06-06)
**Effort:** Phased (3 phases)
**Requested:** 2026-06-06

## Summary

A FastAPI + HTMX web board for the `examples/dungeon_master/` example: a browser
front end that preplans a story, then lets a Dungeon Master steer the
checkpointed turn loop beat-by-beat through buttons instead of CLI grammar. This
realizes the deferred **Phase 4** of [FR-466](FR-466-dungeon-master-example.md)
(the optional HTMX UI, its only unchecked acceptance item, `REQ-YG-434`),
promoting it to a standalone phased FR so each slice ships with its own witness
test. The full design is in [docs/plan-dm-ui.md](../docs/plan-dm-ui.md).

## Value Statement

YAMLGraph learners get a runnable, steerable web UI over a two-graph
preplan→turn-loop pipeline — demonstrating that the same `map` + `interrupt` +
`Command(resume=...)` machinery driving the CLI also powers a stateless web
session, with zero changes to the underlying graphs, prompts, or tools.

## Problem

The DM example (FR-466 Phases 1–3) delivers a complete CLI experience but no web
surface. The NPC example (`examples/npc/api/`) proves the FastAPI + HTMX + session
adapter pattern, but it drives a *single* graph (configure → loop). The DM example
has **two** graphs — `preplan.yaml` (runs once → `story.json`) and `turn-loop.yaml`
(checkpointed play loop) — so it needs an extra preplan stage and a richer UI that
keeps the preplanned structure (synopsis, chapters, cast) visible as persistent
context while the DM steers each beat. No example demonstrates a web layer over a
two-graph, preplan-then-resume pipeline.

## Proposed Solution

A pure Layer-1 presentation layer mirroring `examples/npc/api/`, reusing the
existing `nodes/story_io.py` tools untouched. No graph, prompt, or tool changes.

```
examples/dungeon_master/api/
├── app.py                      # FastAPI bootstrap, lifespan, mounts, GET /
├── session.py                  # DMSession adapter + TurnResult dataclass
├── routes/
│   └── story.py                # POST /story/preplan, /story/turn
└── templates/
    ├── base.html               # inline CSS (parchment/ink theme), header, blocks
    ├── index.html              # premise setup form (sidebar) + empty stage
    └── components/
        ├── story_banner.html   # top banner: logline + chapter progress strip
        ├── turn_result.html    # current beat card + DM action controls
        └── error.html
```

### Routes

| Method | Path | Form fields | Action | Returns |
|--------|------|-------------|--------|---------|
| GET | `/` | — | Render setup page | `index.html` |
| POST | `/story/preplan` | `session_id`, `premise`, `chapter_count`, `cast_size` | Run `preplan.yaml` → `story.json`; `ainvoke` turn-loop to first `dm_window` interrupt | `story_banner.html` + `turn_result.html` |
| POST | `/story/turn` | `session_id`, `dm_action`, `dm_payload` | Compose raw DM string, `Command(resume=...)` | new `turn_result.html` |

### DM input composition (the one subtlety)

The six DM actions become buttons/fields that compose the raw string the existing
`parse_dm_tool` expects — the browser gives controls instead of typed grammar:

- `accept` → `"accept"`
- `edit` + payload → `"edit: <payload>"`
- `nudge` + payload → `"nudge: <payload>"`
- `retry` → `"retry"` · `next-chapter` → `"next-chapter"` · `end` → `"end"`

### Session adapter (`DMSession`)

Same stateless pattern as `EncounterSession`: `config =
{"configurable": {"thread_id": session_id}}`, all state in a **process-stable,
module-level** checkpointer singleton (MemorySaver default, Redis if `REDIS_URL`)
that overrides the YAML's `:memory:` SQLite (J/F3). `preplan(...)` runs the
preplan graph into a per-session `outputs/dungeon-master/<session_id>/`, then
`ainvoke`s the turn-loop and detects the `dm_window` interrupt via
`aget_state(config).next` (the graph returns at the interrupt — it does not raise;
J/F1) to surface the first beat. `turn(...)` composes the DM string and resumes.
Termination via `is_complete = not state.next` (the clean `end` termination proven
by FR-467). `TurnResult` fields: `turn_number`, `chapter_index`, `chapter_title`,
`draft_beat`, `committed_count`, `is_complete`, `error`.

### UI — the "nice UI on top"

A persistent **story banner** (logline + chapter progress dots + turn/beat
counter) above a sidebar (synopsis, cast, chapter titles — static per session) and
a stage showing the current `draft_beat` in a serif "page" card with the six DM
controls. Distinct **parchment/ink storybook theme** (`--accent #c2873f` brass/gold)
to differentiate from NPC's navy/magenta console palette. Turn POSTs target
`#app-body` so banner and stage refresh together, keeping chapter progress live.

```bash
uvicorn examples.dungeon_master.api.app:app --reload   # → http://localhost:8000
```

## Phased Implementation

Each phase is independently demonstrable and lands as its own PR with a witness
test and demo output. A new capability `CAP-166-dungeon-master-web-ui.yaml`
carries `REQ-YG-435`..`REQ-YG-437`, created in Phase 1. This FR realizes the
deferred `REQ-YG-434` (FR-466 Phase 4); on completion, mark FR-466's Phase 4
acceptance item done with a pointer here.

### Phase 1 — Server + session (`REQ-YG-435`)
**Goal:** A working FastAPI app and stateless `DMSession` driving the existing
graphs over HTTP.
- `api/app.py` (bootstrap, GET `/`), `api/session.py` (`DMSession` + `TurnResult`),
  `api/routes/story.py` (preplan/turn routes), minimal placeholder templates so
  the app boots.
- Process-stable module-level checkpointer singleton overriding the YAML
  `:memory:` SQLite (J/F3); interrupt detected via `aget_state().next` (J/F1).
- Per-session story files under `outputs/dungeon-master/<session_id>/` (decision 1).
- **REQ-YG-435** GET `/` returns 200; POST `/story/preplan` runs preplan + advances
  the turn-loop to the first interrupt and returns a beat fragment; POST
  `/story/turn` with `accept` advances the turn; `end` yields a completion state
  (`is_complete` true). LLM mocked.
- **Demo:** scripted `TestClient` run (preplan → accept → end) → `demo-output.log`.
- **Acceptance:** witness test via FastAPI `TestClient`, `@pytest.mark.req("REQ-YG-435")`;
  DM-string composition asserted for each action. Changelog fragment + diary entry
  in the PR (J/F2).

### Phase 2 — Templates + theme (`REQ-YG-436`)
**Goal:** The full storybook board rendered via HTMX swaps.
- `base.html` (parchment/ink inline CSS, header, `#app-body`), `index.html` (setup
  form + sidebar), `components/{story_banner.html, turn_result.html, error.html}`.
- HTMX wiring: preplan spinner + `hx-disabled-elt`; turn buttons `hx-target="#app-body"`;
  `htmx:afterSwap` clears edit/nudge fields; completion panel on `is_complete`.
- **REQ-YG-436** rendered fragments contain the banner (logline, chapter progress
  strip, turn/beat counter), the `draft_beat` card, and the six DM controls; the
  completion panel renders when the session ends.
- **Demo:** `TestClient` asserting rendered-HTML markers across a multi-action run →
  appended to `demo-output.log`.
- **Acceptance:** witness test on rendered HTML, `@pytest.mark.req("REQ-YG-436")`.
  Changelog fragment + diary entry in the PR (J/F2).

### Phase 3 — Demo + docs (`REQ-YG-437`)
**Goal:** Prove the end-to-end web experience and document it.
- `demo-output.log` capturing a full scripted browser-style session (preplan →
  accept → retry → edit → nudge → next-chapter → end).
- `examples/dungeon_master/README.md` "Web UI" section (run command, route table,
  screenshot-free walkthrough).
- Changelog fragment (`type: feat`, `scope: examples`, `req: REQ-YG-437`).
- **REQ-YG-437** the recorded demo shows a complete preplan→steer→end session and
  the README documents launch + the six controls.
- **Acceptance:** `demo-gate` satisfied (demo log in diff); README section present;
  `@pytest.mark.req("REQ-YG-437")` smoke test over the scripted session. Changelog
  fragment + diary entry in the PR (J/F2).

## Acceptance Criteria

- [ ] Phase 1: `api/app.py`, `session.py`, `routes/story.py` drive preplan + turn
      over HTTP (REQ-YG-435)
- [ ] Phase 2: storybook templates + parchment theme render via HTMX swaps
      (REQ-YG-436)
- [ ] Phase 3: end-to-end demo log + README Web UI section (REQ-YG-437)
- [ ] `CAP-166-dungeon-master-web-ui.yaml` registers REQ-YG-435..437
- [ ] Witness test per phase, tagged `@pytest.mark.req(...)`, LLM mocked
- [ ] `demo-output.log` committed (demo-gate)
- [ ] No changes to `preplan.yaml`, `turn-loop.yaml`, `prompts/`, or
      `nodes/story_io.py` (pure Layer-1 addition)
- [ ] Changelog fragment **and** diary entry in **every** phase PR (J/F2)
- [ ] FR-466 Phase 4 acceptance item updated to point here

## Alternatives Considered

- **Extend FR-466 in place under REQ-YG-434** (as the plan doc originally framed
  it): rejected — three substantial slices (server, templates, demo) under a single
  REQ gives weak per-phase witness traceability; a dedicated FR with one REQ per
  phase matches the project's per-phase test discipline.
- **Shared single `story.json`** across sessions: rejected — concurrent browser
  sessions would clobber each other's files; namespace under
  `outputs/dungeon-master/<session_id>/` (decision 1).
- **Streaming the preplan step:** rejected — 4 sequential LLM calls; a prominent
  spinner + "Preplanning…" copy matches NPC and avoids streaming complexity
  (decision 2).
- **Out-of-band banner swap** (`HX-Trigger` + OOB) instead of full `#app-body`
  swap: rejected at judgment — full-body swap is simpler and keeps chapter progress
  live (decision 3).
- **`GET /story/{session_id}` read route:** rejected at judgment (J/F4) — no
  consumer; re-introduce only when reconnect/poll exists.

## Judgment (2026-06-06)

Judged against the live NPC web pattern (`examples/npc/api/session.py`,
`app.py`), the DM graph (`turn-loop.yaml`), the DM tools (`nodes/story_io.py`),
and the CI branch-protection gates (`CLAUDE.md`). **Approved with corrections
folded in; scope frozen.**

Defects found and resolved:

- **F1 (correctness — interrupt detection).** The design said the session
  `ainvoke`s the turn-loop "catching `GraphInterrupt` to surface the first
  beat." For *this* graph that is the wrong primary path: `run.py` already
  proves the loop returns at the `dm_window` interrupt without raising
  (`app.invoke(...)` then `_is_done` via `state.next`). **Fix:** detect the
  interrupt the way the graph actually behaves — `await app.aget_state(config)`
  and treat a non-empty `state.next` (or an `__interrupt__` key in the result)
  as "awaiting DM input," as `EncounterSession._parse_result` does. Keep the
  `GraphInterrupt` `except` as a defensive fallback only, not the load-bearing
  branch. `is_complete = not state.next` is correct and stays.

- **F2 (CI gate — per-phase changelog + diary).** Each phase ships as its own
  `feat(examples): FR-468 …` PR. Branch protection runs `changelog-gate` (blocks
  `feat` PRs lacking a `changelog/unreleased/` fragment) and `diary-gate` (blocks
  `feat` PRs referencing `FR-XXX` lacking a diary file in the diff) on **every**
  PR. The original plan placed the changelog only in Phase 3 and the diary "on
  completion." **Fix:** every phase PR carries its own changelog fragment
  (`type: feat`, `scope: examples`, `req: REQ-YG-43{5,6,7}`) **and** a diary
  reflection in-diff.

- **F3 (state — checkpointer override).** `turn-loop.yaml` declares
  `checkpointer: sqlite :memory:`. A `:memory:` SQLite checkpointer is bound to
  one connection and will not persist across HTTP requests. The web layer must
  compile with a **process-stable, module-level** checkpointer singleton
  (MemorySaver by default, Redis when `REDIS_URL` is set) — mirroring NPC's
  `get_checkpointer()` cache — and pass it to `graph.compile(checkpointer=…)`,
  overriding the YAML's `:memory:`. **Fix:** `session.py` owns a cached
  checkpointer + cached compiled graphs (preplan one-shot, turn-loop
  checkpointed), identical to `examples/npc/api/session.py`.

- **F4 (scope / YAGNI — speculative route).** `GET /story/{session_id}` has no
  consumer: no phase tests it, no template polls it, and the banner refreshes via
  the `/story/turn` full-body swap (decision 3). **Fix:** drop it. The surface is
  `GET /` + `POST /story/preplan` + `POST /story/turn`.

Open decisions resolved:

- **D1 — per-session story files: APPROVED.** `save_story_tool` and
  `load_story_tool` already honor `state["output_dir"]` (default
  `outputs/dungeon-master`), so passing
  `output_dir=outputs/dungeon-master/<session_id>` namespaces cleanly with no
  tool change. Concurrent sessions must not share one `story.json`.
- **D2 — preplan latency: APPROVED.** Spinner + "Preplanning…" copy, no
  streaming (matches NPC; preplan is 4 sequential LLM calls).
- **D3 — banner refresh: APPROVED.** Full `#app-body` swap on each turn keeps
  chapter progress live; OOB is unjustified complexity.

Non-blocking notes:

- `CAP-166` and `REQ-YG-435..437` are free locally (highest local CAP 165, REQ
  434) and on `origin/main` (highest FR/REQ 467/434). Confirm `CAP-166` unused on
  `origin/main` before creating it (mechanical pre-flight, as for CAP-164/165).
- **Out of scope (observation only):** `run.py` prints `state["beat"]` for
  display while the interrupt message correctly renders `{{ state.draft_beat }}`;
  the printed `beat` is stale/empty at the pause. The web design is *more*
  correct (it reads `draft_beat` for the pending card). Not this FR's concern; do
  not modify `run.py` here.

**Authority granted** to implement Phases 1–3 (server+session, templates+theme,
demo+docs). Per phase: write the failing witness test first (`TestClient`, LLM
mocked); smallest sufficient change; pure Layer-1 addition under
`examples/dungeon_master/api/` — no changes to `preplan.yaml`, `turn-loop.yaml`,
`prompts/`, or `nodes/story_io.py`; only the three routes above; carry a
changelog fragment **and** diary entry in every phase PR. On completion, tick
FR-466's Phase 4 acceptance item with a pointer here.

## Related

- [docs/plan-dm-ui.md](../docs/plan-dm-ui.md) — the full design this FR formalizes
- [FR-466](FR-466-dungeon-master-example.md) — parent example; this realizes its
  deferred Phase 4 (`REQ-YG-434`)
- [FR-467](FR-467-conditional-edge-to-map-node.md) — the edge-compiler fix that
  makes the turn loop terminate cleanly on `end` (`is_complete` detection)
- `examples/npc/api/` — the FastAPI + HTMX + session-adapter pattern this mirrors
- `examples/dungeon_master/turn-loop.yaml` — the graph the UI drives
  (`dm_window` interrupt, `resume_key: dm_input`)
