# Dungeon Master — Game Design Document

> An LLM-driven story workbench. The Dungeon Master (you) shapes a novel-length
> story not by writing it, but by **directing** it: type a tagline, then steer
> the machine's prose through small, reversible edits until it says what you mean.

This README is the design doctrine for the rebuild. The first prototype lives in
[`purgatory/`](purgatory/) — detached, not deleted. We mine it for proven
components and leave its scope behind.

---

## 1. Vision

A story is too big to hold in one prompt and too personal to hand off entirely to
a model. The Dungeon Master treats generation as a **conversation with the text**:
the machine proposes, the human disposes. Every artifact — the synopsis, later the
outline, later each beat — is a card you can read, edit in place, and *iterate* on
with a plain-language instruction.

The design north star: **the human is always one keystroke from changing anything,
and never more than one click from accepting it.**

---

## 2. What is built

The app started as a single loop around the **synopsis** and has grown — one
judged feature request at a time — into a **preplan tree** that feeds a **play
loop** and three **finish** passes. Every visitable node is the same iterable
card; what changes is the graph behind it and the prior context it reads.

```
Synopsis (root — gates everything)
├── Key Scene              FR-475 · the single pivotal scene (reads synopsis + roster)
├── Characters (roster)    FR-475 · one char:<id> card per named principal
├── Chapters (overview)    FR-488/490 · the book split into an ordered chapter set
│     └── chapter:<n>      each expanded, carrying world_state forward (FR-488 J7)
└── Play                   FR-477 · unlocks once the whole preplan is reviewed
      └── turn:<n>         map(cast → intents) → director → recap (FR-477/479/481)
            └── Final Cut             FR-484 · one continuous scene from the whole arc
                  └── Final Cut (Turns)   FR-485 · one polished segment per played turn
                        └── Walkthrough     FR-487 · full-text render of every turn
```

1. **Synopsis** — the DM opens the app to a **tagline** prompt seeded into the
   synopsis card (no splash). The machine drafts a plain, reveal-all synopsis;
   the DM edits in place or describes a change and **Iterates**, then **Accepts**.
   Accepting the synopsis is the gate that reveals its children, and the act that
   derives both the character roster and the chapter set (FR-474/489).
2. **Key Scene** (FR-475) — reads the accepted synopsis (and the derived roster,
   FR-480) and drafts the single pivotal scene as a structured plan
   (`CHARACTERS:` / `SUMMARY:` / `BEATS:` / `END:`). Same weave → edit → accept.
3. **Characters** (FR-475) — accepting the synopsis derives a **roster** of
   names; each becomes a dynamic `char:<id>` card drafted from the shared
   `character.yaml` graph. The DM reviews each in turn.
4. **Chapters** (FR-488/490) — accepting the synopsis also splits it into a fixed,
   ordered set of one-paragraph chapter summaries. The **Chapters** crumb lands on
   a read-only **overview** (table of contents); each `chapter:<n>` card expands
   its summary into prose, threading the previous chapter's **world state**
   forward (FR-488 J7) so the book stays continuous. An *independent* branch — not
   part of the play gate.
5. **Play / Turns** (FR-477) — the moment synopsis ✓, key scene ✓, and *every*
   character card ✓, a **Play** branch appears and **Turn 1 auto-drafts**. Each
   turn runs the cast through private **intents** (a `map`: THINKING + INTENT,
   plus the outward DIALOGUE + EXPRESSION, FR-486), a **director** judges the
   arc (phase, beats satisfied, continuity, scene-complete — FR-479/481), and a
   **recap** consolidates it into one authoritative paragraph. Accepting a turn
   seeds the next, threading history forward.
6. **The three finishes** — once the director reports the scene **complete** on
   any turn, three terminal passes unlock and chain on accept:
   - **Final Cut** (FR-484) — dissolves the whole arc into *one continuous scene*.
   - **Final Cut (Turns)** (FR-485) — keeps the turn skeleton: one polished
     segment per played turn, validated 1:1 against the play-by-play.
   - **Walkthrough** (FR-487) — renders the *full text* of each turn from three
     authored layers (the FR-485 cut spine, the FR-486 performance, and a
     whole-arc director-staging pass).

### Still deferred (out of scope, by design)
- Asking for character or chapter counts up front (the roster and the chapter set
  both emerge from the synopsis instead).
- Hand-editable intents and any rules/dice engine (turns are narrative only).
- CAP/REQ/CI gates — this prototype lives under the FR-474 J3 regime; its
  walkthrough tests in [`tests/`](tests/) are a visibility harness, not a gate.

---

## 3. Core Components (proven in the prototype)

These primitives carried the prototype and survive the rebuild.

### 3.1 Breadcrumbs — *where am I in the story?*

A live navigation strip (`#story-crumbs`) above the work area. Each view declares
its trail, e.g. `Story · Synopsis`. Because every interaction swaps a single
`#app-body` region (HTMX `innerHTML`), the breadcrumb stays continuous as the DM
moves between artifacts — it is the spine that keeps a fragmented, swap-driven UI
feeling like one place.

*Source mined from:* `purgatory/api/templates/components/breadcrumb.html`.

### 3.2 The Iterable Text Card — *read, edit, iterate, accept*

The heart of the interaction. One card renders any prose artifact as a working
surface, not a read-only result:

| Element | Behaviour |
|---|---|
| **Prose textarea** | Shows the current synopsis. Autosaves on `change` (HTMX `hx-swap="none"`) — no Save button, no lost edits. |
| **Prompt textarea** | A 3-line box, seeded with the tagline on the first turn, then "Describe the story, or a change to apply…". This is the natural-language instruction. |
| **↻ Iterate** | Sends the live text **and** the prompt to the single `weave` step. On an empty draft the prompt *is* the premise (first generation); on a non-empty draft it is a change to apply. An empty prompt is a pure save (no model call). |
| **✓ Accept** | Commits the artifact, freezes it read-only, and lands on the next sensible node (chosen by the tree, not a linear cursor), auto-drafting it on arrival. |

One generation mode, three URLs (`weave`, `edit`, `accept`) plus `/story/nav`,
one card. *Generation and iteration are the same operation* — the only difference
is whether a draft already exists. There is no separate Generate button and no
throwaway Regenerate.

### 3.3 The single `weave` mode — *generate and iterate are one*

The prototype originally split a `synopsis` prompt (premise → prose) from a generic
`refine` prompt (instruction + text → revised text). v2 collapsed them: one prompt
takes the current draft (possibly empty) plus an instruction and returns the full
prose. Empty draft means the instruction is the premise; non-empty means apply
the change. This is the engine behind Iterate and it is the only generation path —
ordinary cards run it through `session._invoke_stage`; the structured stages
(turns, chapters, the three finishes) run a *composed* variant
(`session._compose_special`) that wraps the same weave contract around their
multi-node graphs and deterministic post-conditions (see
[`docs/architecture.md`](docs/architecture.md)).

---

## 4. The Card Loop (one operation, every stage)

Every node — synopsis, key scene, each character, each chapter, each turn, and
each of the three finishes — is the identical `{text, reviewed}` card driven by
the same three URLs (`weave` / `edit` / `accept`) plus `/story/nav` for
breadcrumb jumps. The tree only decides *which graph* runs and *what prior
context* it reads.

```mermaid
flowchart LR
    A[Stage entered · auto-drafts from seed] --> C[Read prose in edit mode]
    C -->|edit text| C
    C -->|describe change + Iterate| D[weave: draft + instruction → prose]
    D --> C
    C -->|Accept| E[Stage committed · unlocks next]
    E -->|next stage| A
```

The synopsis itself is a **plain, reveal-all** summary — concrete nouns and
verbs, the actual ending included — not an atmospheric teaser, and the key-scene
and turn-recap voices inherit that dry, factual register.

### The Play loop (FR-477)

A turn is the same card with a structured side-channel. `turn.yaml` is two
nodes: a **map** over the cast where each principal privately reasons
(`THINKING`) and commits one action (`INTENT`), then a **recap** node that
consolidates all intents into one authoritative "Turn N —" paragraph naming
every character. Intents render in a left aside; the recap is the editable card.
**Iterate** re-rolls the whole turn (intents + recap co-generated, so they can't
drift; a DM instruction steers only the recap). **Accept** seeds Turn N+1 with
the last three recaps as scene context and each character's prior intent.

```mermaid
flowchart LR
    P[preplan complete] --> T1[Turn 1 auto-drafts]
    T1 --> I[map · per-character intents]
    I --> R[recap · consolidate + name cast]
    R -->|Iterate re-rolls whole turn| I
    R -->|Accept| T2[Turn 2 · history threaded]
```

---

## 5. Architecture Intent

YAMLGraph's three-layer split holds:

```
Presentation  →  FastAPI + HTMX + Jinja  (cards, breadcrumb, #app-body swaps)
Logic         →  YAML graphs (one per stage) + prompts
Side effects   →  per-session story.json, the compiled-graph cache
```

**Each stage is its own self-contained graph** rather than an inline prompt call,
which makes every loop testable in isolation. The graphs are:

| Graph | Stage | Shape |
|---|---|---|
| `synopsis.yaml` | Synopsis | weave (draft + instruction → prose) |
| `key_scene.yaml` | Key Scene | weave, reads synopsis + roster |
| `character_roster.yaml` | Characters | derives the cast names from the synopsis |
| `character.yaml` | each `char:<id>` | weave, parameterised by the character name |
| `chapter_outline.yaml` | Chapters | splits the synopsis into `{title, summary}[]` |
| `chapter.yaml` | each `chapter:<n>` | expands a summary, threading `world_state` forward |
| `turn.yaml` | each `turn:<n>` | `map`(cast → intents) → director → recap |
| `final_cut.yaml` | Final Cut | one continuous scene from the whole arc |
| `final_cut_turns.yaml` | Final Cut (Turns) | one segment per played turn |
| `staging.yaml` + `walkthrough.yaml` | Walkthrough | whole-arc staging → per-turn full-text render |

The **shared card interface stays a pure `str → str`** (FR-477 J3). The structured
stages keep their side-channels (turn intents + director judgement; chapter
`world_state`; the cut/walkthrough `turns` track) out of that interface, isolated
in `turn_ops.py` / `chapter_ops.py`. Those modules also own the **deterministic
seams** — pure code the model is *not* trusted to do: the monotonic phase clamp,
beat canonicalisation against the frozen scene, the climax derivation, and the 1:1
alignment validator that **raises** on a misaligned finish (Commandment 6). See
[`docs/architecture.md`](docs/architecture.md) for the full module map and the
deterministic-vs-generative seam split.

---

## 6. Relationship to `purgatory/`

`purgatory/` is the **detached first prototype** — a working but over-scoped
turn-loop/outline/beat system. It is kept intact as a parts bin and reference, not
as live code. The rebuild pulls forward only the proven components above
(breadcrumb, the iterable text card, the plain-synopsis prompt direction) and
collapses the prototype's separate generate/refine prompts into the single `weave`
mode. Nothing in `purgatory/` is wired into the new app until it has earned its
place in the synopsis loop.
