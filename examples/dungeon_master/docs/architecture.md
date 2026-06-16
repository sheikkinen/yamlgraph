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
| `turn_ops.py` | The **Scene lifecycle** (FR-493 J5) — `{plan, world_state_in} → play turns → {final_text, world_state_out}`: `running_scene` (threads the inherited `world_state`), `invoke_turn` (map → director → recap), `final_cut_context`, `invoke_final_cut`; plus the per-character intent side-channel and director post-processing (phase clamp, beat canonicalisation). |
| `chapter_ops.py` | The book-chapter graph calls: `outline_chapters` (synopsis → chapter list), `close_chapter` (the Scene-lifecycle entry — the `world_state` forward-carry + the per-chapter Final Cut final text), and `compose_book_deterministic` (the pure, no-LLM whole-book assembly over the played chapters' final texts). Pure reads. |
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
        "world_state": "...",                 // end-of-chapter ledger (FR-491 B)
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
      "2": { "title": "...", "summary": "...", "world_state": "",
             "text": "", "reviewed": false, "turns": [] }
    }
  }
  // No persisted "book" entry (FR-492): The Book is composed on the fly from the
  // played chapters' final texts by compose_book_deterministic, never stored.
}
```

Every visitable stage exposes the same `{text, reviewed}` entry to the card; the
structured fields (per-turn `intents`, `direction`, chapter `summary` /
`world_state`) are **side-channels** that never enter the shared `str → str` weave
interface (FR-477 J3). There is no flat top-level `turns` list — turns live inside
the chapter that owns them.

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
| `turn:<cid>:<n>` | `turn.yaml` `map`(intents) → director → recap | `_clamp_phase` (monotonic arc — phase never regresses), `_canonicalize_beats` (accumulate the director's reported beat phrases cumulatively, `beats_total = 0` for the free-text chapter plan) |
| `chapter:<cid>` close | `chapter_close.yaml` (inherited ledger + played recaps → end-of-chapter `world_state`) | the **forward-carry**: `chapter:n-1`'s `world_state` is threaded into `chapter:n`'s `running_scene` as the established START, and into its close as `previous_world_state` (FR-491 B; preserving FR-488 J7) |
| **The Book** | _none — composition is assembly, not generation (FR-492)_ | `compose_book_deterministic` walks `chapters.order`, heads each played chapter's title + its per-chapter Final Cut final text, suppresses the `world_state` ledger from the manuscript, and **raises** rather than composing from nothing (Commandment 6). No LLM on the path to a *first* book. |

The director's judgement is **read-only signal** surfaced to the DM (phase, beats,
steer, continuity, scene-complete) — never auto-applied (FR-479 J2). Iterate on a
turn re-rolls intents + recap **together** so they cannot drift; a DM instruction
steers only the recap.

**The two load-bearing generative seams** (the ones the live witness exercises,
because the mocked tests can only prove their wiring):

1. **Chapter completion is judged from the summary.** Each chapter is played until
   the director — reading the chapter summary as the arc — sets `scene_complete`.
   No fixed turn count; the model decides when the chapter's events have happened.
2. **`world_state` threads across played chapters.** A chapter's close derives its
   end-of-chapter ledger from the inherited ledger + its played recaps; the next
   chapter is played from there, and The Book renders the whole carry into one
   continuous arc.

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
