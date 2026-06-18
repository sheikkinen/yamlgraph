# Dungeon Master v2 — Architecture & Generation Reference

The current technical reference for the DM v2 app. The design vision lives in the
[README](../README.md); this document is the *how* — the module map, the story
document shape, the stage tree, and the deterministic-vs-generative seam split.

> The app is a **stage tree** grown over FR-474 → FR-491, where every visitable
> node is the same iterable card. FR-491 made the book the spine: the synopsis
> derives a cast, the cast derives a chapter outline, **each chapter is played
> turn by turn**, and the played chapters compose into **The Book**. The old
> single-pivotal-scene "Key Scene" and the three turn-based finishes (Final Cut,
> Final Cut (Turns), Walkthrough) are retired.

---

## 1. Three layers

YAMLGraph's strict separation holds throughout the app:

| Layer | Files | Responsibility |
|-------|-------|----------------|
| **Presentation** | `api/app.py`, `api/routes/synopsis.py`, `api/templates/` | FastAPI routes, HTMX `#app-body` swaps, the session id, all rendering |
| **Logic (YAML)** | `*.yaml` graphs + `prompts/*.yaml` | One self-contained graph per stage; all LLM calls and structured outputs |
| **Side effects** | `api/story_doc.py`, `api/graph_app.py` | Per-session `story.json` read/write; the compiled-graph cache |
| **Adapter** | `api/session.py`, `api/doc_ops.py`, `api/tree.py`, `api/navigation.py`, `api/turn_ops.py`, `api/chapter_ops.py`, `api/render.py` | Glue HTTP ↔ graph ↔ doc; the stage tree, breadcrumb, pure navigation, the structured side-channels, and the full-story Markdown render |

### Module map

| Module | Role |
|--------|------|
| `app.py` | FastAPI app; `GET /` lands on the seeded synopsis card, sets `x-session-id`. |
| `routes/synopsis.py` | The four stage-agnostic endpoints (below); renders `#app-body`. |
| `session.py` | `DMSession` — `weave` / `edit` / `accept` / `navigate`, `StageView`, and the `_view` projection. The adapter's HTTP-facing surface; delegates the derived-doc work to `doc_ops`. |
| `doc_ops.py` | Derived operations over the loaded `doc` (FR-493): the doc accessors (`entry`, `characters`, `chapters`), the single stage-graph `invoke_stage`, and the side-effecting expansions (`expand_roster`, `expand_chapters`, `apply_chapter_close`, `compose_stage`, `autodraft`). Nine pure `(doc, …)` functions, no `self`; imports nothing from `session` (acyclic). |
| `tree.py` | `STAGES`, `Stage`, `resolve_stage`, `breadcrumb`, and the gate predicates (`cast_complete`, `all_chapters_played`). Pure. |
| `navigation.py` | Pure reachability (`can_visit`) and landing (`accept_target`, `next_unreviewed_char`). Reads the doc; never mutates or invokes a graph. |
| `turn_ops.py` | The **Scene lifecycle** (FR-493 J5) — `{plan, world_state_in} → play turns → {final_text, world_state_out}`: `running_scene` (threads the inherited `world_state` plus turn-1 `seam_packet`), `_retrieve_turn_ledger` (ranks the inherited relationships to the top-K cast-relevant for turn context, FR-516), `invoke_turn` (map → director → recap), `final_cut_context`, `invoke_final_cut`; plus deterministic lifecycle turn-1 gating (`LifecycleGateError`) and the per-character intent side-channel with director post-processing (phase clamp, beat canonicalisation). |
| `chapter_ops.py` | The book-chapter graph calls: `outline_chapters` (synopsis → chapter list), `close_chapter` (the Scene-lifecycle entry — applies the close's relationship **delta** to the inherited ledger via `apply_ledger_delta`, floors the other lanes via `apply_lane_floor`, threads the typed `seam_packet` handoff, runs per-chapter Final Cut), and `compose_book_deterministic` (the pure, no-LLM whole-book assembly over the played chapters' final texts). Pure reads. |
| `world_state.py` | The **typed ledger-as-memory** (FR-499/513–518). Pydantic models (`Character`, `WorldObject`, `Relationship`, `WorldState`); `parse_world_state` (boundary validation + relationship grounding gate); `format_world_state` (deterministic render to prompt text, `relationships="all"`/`"active"`/`"none"`); and the deterministic memory operators: `apply_ledger_delta` (apply add/reaffirm/update/invalidate ops + bi-temporal reconciliation + mechanical decay), `apply_lane_floor` (carry-forward floor for the non-relationship lanes), `rank_relationships` (top-K cast-relevant retrieval), `apply_merges` (grounded consolidation). Pure: no LLM, no I/O. |
| `seam_packet.py` | The typed chapter-seam handoff (FR-506/507): `parse_seam_packet` / `format_seam_packet` and the `character_lifecycle` gate state — the resolved-events / open-threads / must-carry-facts / opening-constraints contract injected into the next chapter's turn 1. |
| `render.py` | The pure, no-LLM **full-story Markdown render** (FR-494): `render_story_markdown(doc)` frames `compose_book_deterministic`'s Book with the tagline lead, `# Synopsis`, and an optional `# Cast` (first paragraph per non-empty character card); suppresses the `world_state` ledger and invents no title. Inherits the Book's *raise-on-empty* (no played chapter → `ValueError`). The reader serialization beside the machine `story.json`. |
| `story_doc.py` | Per-session `story.json` read/write. |
| `graph_app.py` | Compiled-graph cache (`get_app`) + output normalisers (`clean_text`, `field`). Dependency-free to avoid import cycles. |

---

## 2. HTTP surface

All endpoints operate on the session's **current** stage, so the paths are
stage-agnostic — the card re-renders whichever stage is now active. Every response
is an `#app-body` fragment swapped by HTMX `innerHTML`, which keeps the breadcrumb
(`#story-crumbs`) continuous.

| Method · Path | Action |
|---|---|
| `GET /` | Land on the seeded synopsis card; mint a fresh `session_id` (`uuid[:8]`). |
| `POST /story/synopsis/weave` | The single generation mode: apply the prompt to the current draft. |
| `POST /story/synopsis/edit` | Autosave the edited prose (textarea `change`, `hx-swap="none"`). |
| `POST /story/synopsis/accept` | Freeze the current stage, land on the next node, auto-draft it. |
| `POST /story/nav` | Jump to a tree node (`synopsis`, `chapters`, `book`, or `char:<id>` / `chapter:<cid>` / `turn:<cid>:<n>`). |

> The route prefix is still `/story/synopsis/*` for historical reasons — it is the
> *stage-agnostic* generation surface, not a synopsis-only endpoint.

---

## 3. The story document

The per-session `story.json` (under `outputs/dungeon-master/<session_id>/`) is the
single source of truth. It grows additively as stages are reached:

```jsonc
{
  "tagline": "...",
  "stage": "turn:2:1",                        // the current node
  "synopsis": { "text": "...", "reviewed": true },
  "characters": {
    "reviewed": true,
    "roster": ["hilde", "gunnar"],            // ordered char ids
    "cards": { "hilde": { "name": "Hilde", "text": "...", "reviewed": true }, ... }
  },
  "chapters": {                               // FR-488/490/491 — the book spine
    "reviewed": false,
    "order": ["1", "2"],                      // fixed 1-based ids, story order
    "cards": {
      "1": {
        "title": "...", "summary": "...",     // what the chapter is (the arc)
        "world_state": {                       // typed end-of-chapter ledger (FR-499/513)
          "characters": [ { "name": "Hilde", "faction": "Aschenwulf",
                            "status": "alive", "location": "the ledge",
                            "inventory": ["hand-axe"] } ],
          "objects":    [ { "name": "oath-stone", "holder": "Reinmar",
                            "location": "high valley" } ],
          "facts":      ["the river breached at dawn"],
          "relationships": [                   // FR-513–517 emotional/alliance memory
            { "between": ["Hilde", "Gunnar"], "type": "romantic_bond",
              "status": "active", "tensions": ["clan_feud"],
              "last_interaction": "the truce on the ledge",
              "recap_citations": ["Turn 4 — ..."],
              "valid_from": 0, "valid_to": null,   // bi-temporal (FR-515)
              "last_reaffirmed": 1 }                // decay clock (FR-517)
          ]
        },
        "seam_packet": {                       // FR-506/507 chapter seam handoff
          "resolved_events": ["..."],
          "open_threads": ["..."],
          "must_carry_facts": ["..."],
          "opening_constraints": ["..."],
          "character_lifecycle": [
            {
              "name": "Arnulf",
              "existence_state": "missing_presumed_dead",
              "visibility_mode": "absent",
              "allowed_reappearance_from_chapter": 5,
              "source_chapter": 2
            }
          ]
        },
        "text": "...",                        // the played prose (the recaps)
        "reviewed": true,                     // true once the chapter is played out
        "turns": [                            // FR-491 — turns are CHAPTER-SCOPED
          {
            "n": 1,
            "intents": { "hilde": { "thinking": "...", "intent": "...",
                                    "dialogue": "...", "expression": "..." }, ... },
            "direction": { "phase": "rising", "beats_satisfied": ["..."],
                           "beats_total": 0, "scene_complete": false,
                           "steer": "...", "continuity": [], "establishing": "..." },
            "recap": { "text": "Turn 1 — ...", "reviewed": true }
          }
        ]
      },
      "2": { "title": "...", "summary": "...", "world_state": {},
             "text": "", "reviewed": false, "turns": [] }
    }
  }
  // No persisted "book" entry (FR-492): The Book is composed on the fly from the
  // played chapters' final texts by compose_book_deterministic, never stored.
  // The close LLM emits a "world_state.operations" relationship DELTA (FR-514);
  // code applies it to the inherited ledger, so the stored "world_state" is the
  // already-resolved typed ledger above, never the raw operations list.
}
```

Every visitable stage exposes the same `{text, reviewed}` entry to the card; the
structured fields (per-turn `intents`, `direction`, chapter `summary` /
`world_state` / `seam_packet`) are **side-channels** that never enter the shared
`str → str` weave interface (FR-477 J3). There is no flat top-level `turns` list
— turns live inside the chapter that owns them.

---

## 4. The stage tree

```
Synopsis (root — gates everything)
├── Characters (roster)    FR-475/491 · non-visitable group → one char:<id> card per name
└── Chapters (overview)    FR-488/490/491 · read-only TOC → one chapter:<cid> card each
      └── chapter:<cid>     FR-491 · PLAYED in place via the turn loop
            └── turn:<cid>:<n>   map(cast → intents) → director → recap
      The Book              FR-491/492 · terminal finish — deterministically composed (no graph)
```

Static stages live in `tree.STAGES` (`synopsis`, `characters`, `chapters`,
`book`); per-item cards (`char:<id>`, `chapter:<cid>`, `turn:<cid>:<n>`) are
**synthesised at runtime** by `resolve_stage`. Each `Stage` carries its graph, its
upstream `context` stages, an optional auto-draft `seed`, its `parent` gate, and a
`kind` that routes the UI (`""` ordinary, `roster`, `chapters`, `chapter`,
`turn`, `book`). The `book` stage is **seedless** and graph-less — its `kind`
routes `session._view` to `compose_book_deterministic` instead of any graph.

The flow is **book-first**: accepting the synopsis derives the cast (the characters
who will play it); accepting the **last** character derives the chapter outline (the
arc they will play); each chapter is then played turn by turn, carrying its
`world_state` forward to the next; once every chapter is played, **The Book**
unlocks and composes them into one manuscript.

### Gates (`tree.py` + `navigation.can_visit`)

| Node | Unlocks when |
|------|--------------|
| Characters / Chapters | the synopsis is reviewed |
| each `char:<id>` | synopsis reviewed **and** id in the roster |
| each `chapter:<cid>` | synopsis reviewed **and** id in the chapter set |
| each `turn:<cid>:<n>` | `cast_complete` (synopsis ✓ + **every** character ✓) **and** `cid` is in the chapter order **and** `n` is the next unplayed turn (≤ played + 1) |
| **The Book** | `all_chapters_played` — the chapter order is non-empty **and** every chapter card is `reviewed` (played to its director-judged end) |

### Landing (`navigation.accept_target`)

Accept is **not** a linear cursor — the tree chooses the next node:

- **synopsis** → the first character (the cast is derived first; FR-491 J1).
- each **character** → the next unreviewed character; the **last** character →
  the Chapters overview (accepting it derives the outline).
- each **chapter** → its **first turn** (`turn:<cid>:1`) — a chapter is *played*,
  not expanded; visiting/accepting it opens the play loop.
- each **turn** → the next turn in the chapter, **unless** the director reported
  the scene complete — then it closes the chapter (deriving its `world_state`) and
  lands on the **next chapter's** first turn; the **last** chapter's completion
  dead-ends (the Book is reached via navigation once unlocked).
- **The Book** → terminal (`None`).

The side-effects accept performs before asking where to land — the synopsis
roster expansion (`doc_ops.expand_roster`), the last-character chapter-outline
expansion (`doc_ops.expand_chapters`), and the scene-complete chapter close
(`doc_ops.apply_chapter_close`) — all live in `doc_ops` (FR-493), invoked from
`session`; `navigation` itself stays pure (FR-489 J1).

---

## 5. Generation: deterministic vs generative seams

The governing law (`.github/copilot-instructions.md`): a **deterministic seam** is
code (pure, unit-testable); a **generative seam** is a prompt (live-witnessed). DM
v2 splits every structured stage along that line — the model is handed assembled
context and asked **only for prose/structure it cannot derive**, never to recompute
what the recorded arc already knows.

### Ordinary cards — one weave

`doc_ops.invoke_stage` builds `{draft, instruction, <context stages>, name?}`,
runs the stage graph, and returns the cleaned output. Empty draft ⇒ the
instruction is the premise; non-empty ⇒ apply the change; empty instruction ⇒ pure
save (no model call). An empty completion with no recorded error is treated as the
silent shape of a content-policy decline and **raised**, never written over the
draft (Commandment 6).

### Composed stages — `doc_ops.compose_stage`

| Stage | Generative seam | Deterministic seam (pure code) |
|-------|-----------------|--------------------------------|
| `turn:<cid>:<n>` | `turn.yaml` `map`(intents) → director → recap | `_apply_beat_ledger` (resolve the director's satisfied-beat NUMBERS over the chapter's finite `beats` list back to canonical text, accumulate cumulatively, and COMPUTE `phase`/`scene_complete` from k / N — monotonic by construction, FR-503/FR-504) |
| `chapter:<cid>` close | `chapter_close.yaml` (inherited ledger + played recaps → the three full lanes + a relationship **`operations`** delta) | the **memory apply** (§5a): `apply_lane_floor` carries the non-relationship lanes forward (an emptied lane never zeroes state), `apply_ledger_delta` applies the close's add/reaffirm/update/invalidate ops to the inherited relationship edges with bi-temporal reconciliation + mechanical decay; the resolved typed ledger is threaded into `chapter:n+1`'s `running_scene` as the established START and into its close as `previous_world_state` (FR-514/515/517; preserving FR-488 J7). The prior chapter's `seam_packet` is injected into turn-1 `running_scene` as the chapter-open continuity contract (FR-506), and lifecycle constraints can hard-block turn-1 fanout (`LifecycleGateError`, FR-507) |
| **The Book** | _none — composition is assembly, not generation (FR-492)_ | `compose_book_deterministic` walks `chapters.order`, heads each played chapter's title + its per-chapter Final Cut final text, suppresses the `world_state` ledger from the manuscript, and **raises** rather than composing from nothing (Commandment 6). No LLM on the path to a *first* book. |

The director's judgement is **read-only signal** surfaced to the DM (phase, beats,
steer, continuity, scene-complete) — never auto-applied (FR-479 J2). Iterate on a
turn re-rolls intents + recap **together** so they cannot drift; a DM instruction
steers only the recap. One director field is **not** advisory: `cast_exits` names
rostered characters who have left the scene this chapter (killed, drowned, swept
away). A character may act up to and including the turn it exits; from the next turn
the roster filter accumulates the chapter's `cast_exits` and **drops** the actor
from the cast, so the intent map can no longer animate a swept-away brother climbing
back up the bank (FR-521 S2 — the enforced fix; the earlier advisory feed-forward
was reverted after a witness showed an instruction in the scene is not a gate).
Within a chapter `missing_presumed_dead` is a death-point too (the warn-only
`dead_character_names` within-lane), while the cross-chapter before-open bar stays
`confirmed_dead` so a synopsis return is never barred (FR-521 J2).

**The two load-bearing generative seams** (the ones the live witness exercises,
because the mocked tests can only prove their wiring):

1. **Chapter completion is judged from the summary.** Each chapter is played until
   the director — reading the chapter summary as the arc — sets `scene_complete`.
   No fixed turn count; the model decides when the chapter's events have happened.
2. **The ledger threads across played chapters as memory.** A chapter's close
   emits a relationship *delta* (not a regenerated web); deterministic code applies
   it to the inherited ledger (§5a), the next chapter is played from the resolved
   ledger, and The Book renders the whole carry into one continuous arc.

### Single-chapter replay — the controlled continuity witness (FR-522)

Because efficacy is a non-deterministic, live-LLM property, a continuity change
cannot be proven by a unit test (which can only assert *wiring*) — it needs a live
witness. `scripts/replay_chapter_continuity.py` re-plays **one** chapter from its
inherited start, holding every prior chapter constant, so the only changed variable
is the code under test (one changed variable, same inherited state — an experiment,
not an anecdote). The doc-shape reset is one named, tested site
(`turn_ops.reset_chapter_for_replay`); the impure driver lives in
`api/chapter_replay.py` (deep-copies the doc, then drives the real
`turn_ops.invoke_turn` loop, so a test can monkeypatch the LLM and prove a prior
chapter is byte-identical); the deterministic measurement lives in
`witness_metrics.chapter_actor_flag_metrics` and reports the **director-flag** count
alongside the **intent-map acting** count per turn — so a change that injects text
into the scene (which `running_scene` feeds to all three turn nodes) cannot inflate
the director's flag count without the independent acting count revealing it
(FR-521's metric-pollution lesson). This is an **instrument, not a gate**: it is
never wired into CI; its measurement functions are unit-tested, its live replay is
run by hand. (It already falsified FR-521's S1 feed-forward — see §5's note that the
advisory was reverted after a witness showed an instruction in the scene is not a
gate.)

### 5a. The ledger as agent memory (FR-513–518)

The forward-carry `world_state` began as a free-prose `str`, which let each close
silently contradict an earlier chapter (a clan-flip, a phantom hand-axe, lovers
re-met as strangers) or — worse — zero the relationship web when one close forgot
to re-list it. It is now a **typed ledger the model never regenerates whole**;
the LLM authors meaning, deterministic code authors persistence. All operators
live in `world_state.py` and are pure (no LLM, no I/O).

| Concern | Mechanism (pure code) |
|---------|-----------------------|
| **Boundary grounding** | `parse_world_state` validates the close payload into the typed shape and **drops** any relationship lacking ≥2 named parties or ≥1 `recap_citation` — a hallucinated bond never enters the ledger (FR-513). |
| **Delta, not regeneration** | The close emits relationship `operations` (`add` / `reaffirm` / `update` / `invalidate`); `apply_ledger_delta` applies them to the inherited edges. **Zero ops carry the inherited set forward unchanged** — a forgetful close can no longer reset the bonds (FR-514). The non-relationship lanes use `apply_lane_floor`: an emptied lane carries forward, never zeroes (FR-514 J4). |
| **Bi-temporal reconciliation** | Edge identity is the participant set, type-independent, so a contradiction (`enmity` → `romantic_bond`) lands on the *same* edge: the old version is **closed** (`valid_to` = closing ordinal), a new one opened (`valid_from`). History is retained, not overwritten; only `valid_to is None` edges reach turn context (FR-515). |
| **Mechanical decay** | After the ops, an active edge unrefreshed for more than `DECAY_AFTER` (2) chapters is demoted to `dormant` by arithmetic on the `last_reaffirmed` ordinal — not by the LLM's recollection. Ordinals are integers so decay and recency are arithmetic, never string parsing (FR-517). |
| **Top-K retrieval** | `_retrieve_turn_ledger` ranks the inherited relationships by cast-relevance × salience (tension count) × recency and keeps `RETRIEVAL_TOPK` (6) for turn context, so a long saga does not drag every bond into every turn; empty cast falls back to the full ledger rather than blanking it (FR-516). |
| **Consolidation** | `apply_merges` folds grounded overlapping edges into one, closing the merged-out sources with `valid_to` (no-op on a clean ledger). Primitive shipped; cadence/LLM-wiring deferred (FR-518). |

`format_world_state(…, relationships=…)` is the single render: `"active"` (turn
context — only currently-valid, non-dormant/archived edges), `"all"` (close
carry-forward, status-labelled), or `"none"`. The ledger is never rendered into the
reader manuscript (`render.py` suppresses it).

---

## 6. The UI

A single `#app-body` region, swapped by HTMX `innerHTML` on every action, with the
breadcrumb above it. `app_body.html` branches on `stage.kind`:

| `kind` | Template | What it shows |
|--------|----------|---------------|
| `turn` | `turn_card.html` | Two columns: the per-character **intents** aside + the always-on **director card** (`director_card.html`), and the editable **recap** card. A 🏁 banner when the chapter's scene is complete. |
| `chapters` | `chapters_overview.html` | A read-only **table of contents** — every chapter `title` + `summary`, each a nav link to its `chapter:<cid>` card, ✓ when played. |
| `book` | `stage_card.html` (else) | **The Book** — the deterministic compose of the played chapters' final texts (`compose_book_deterministic`), rendered as the terminal manuscript. Reachable only when `all_chapters_played`. |
| else | `stage_card.html` | The iterable prose card (textarea autosave + prompt box + Iterate / Accept). On a `chapter` card it shows the **Summary** and **Inherited world state** above the prose (FR-490). |

Accepted stages render read-only with an `Accepted ✓` badge. Errors render as a
banner **above** the surviving card (2xx, so HTMX swaps it) — the draft and
breadcrumb are never lost, so the DM can rephrase and retry in place.

---

## 7. Running it

```bash
uvicorn examples.dungeon_master.api.app:app --reload --port 8000
```

Generation calls a real LLM, so a provider must be configured (e.g.
`ANTHROPIC_API_KEY`, or `PROVIDER` + the matching key; the repo default is
`vertex` / `gemini-3.5-flash`).

Tests (mocked LLM, no API key needed) — a visibility harness, not a governance
gate (FR-474 J3):

```bash
pytest examples/dungeon_master/tests/ --no-cov
```

### Limits of the prototype

- **Session-scoped, not durable across reloads.** `session_id` is a fresh
  `uuid[:8]` minted on every `GET /`. Reloading mints a new session; the old
  `story.json` stays on disk but nothing links back to it (no resume/list UI).
- **No checkpointer.** Graphs compile without one — generation is stateless; all
  persistence is the JSON file, not LangGraph state.
- **CAP/REQ/CI-exempt.** Under the FR-474 J3 regime: no capability registry, no
  requirement tags, no CI gate; the tests are a harness.
