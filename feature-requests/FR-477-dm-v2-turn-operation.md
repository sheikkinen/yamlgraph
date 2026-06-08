# FR-477: Dungeon Master v2 — Turn Operation (Intents → Consolidated Recap)

**Priority:** MEDIUM
**Type:** Prototype enhancement (continues FR-475; inherits FR-474 J3/J4 regime)
**Status:** Implemented — 2026-06-08. Built under the frozen spec; the four
original Open Questions are resolved inline (marked **→ decided**). See
*Implementation Status* at the foot for what shipped and the one route deviation.
**Effort:** ~1–1.5 days (prototype)
**Requested:** 2026-06-08
**Judged:** 2026-06-08

**Continues:** FR-475 (preplan tree). Same J3/J4 rules apply — **no CAP/REQ, no
tests-first gate, no demo regeneration**; the deliverable is a keep/kill/reshape
decision, not a green pipeline. Walkthrough tests stay under
`examples/dungeon_master/tests/`.

**Precondition already in place:** the character roster is capped to **2–4
principals** (the casting prompt now lists only the few who drive the story).
This keeps the per-turn intent column short enough to read at a glance — a usable
turn needs a small cast, so the cap is a hard dependency of this design.

## Summary

Add the **play loop** that begins once the preplan (synopsis → key scene →
characters) is accepted. A **turn** is one round in which **every principal
character is prompted privately** for their *internal thinking* and *action
intent*, and those intents are then **consolidated into a single "Turn N actions"
recap** that is appended to the running scene. The per-character thinking/intent
appear as small cards in a **left column**; the consolidated recap fills the
**main editable card** (the existing prose component), where it gets the same
weave / edit / accept control every other stage already uses.

## Value Statement

The DM drives play as a sequence of turns where each character reasons and acts
from their own sheet and the scene so far, and the DM shapes the single
authoritative recap of what actually happened — seeing every character's private
intent side-by-side with the consolidated outcome.

## Problem

The preplan ends with an accepted synopsis, a key scene, and a reviewed cast, and
then **stops** — there is nowhere to go. Nothing turns the static cast + scene
into play. Two specific gaps:

1. **No turn primitive.** There is no operation that asks each character "what do
   you think and what do you do this turn?" and folds the answers into one shared
   outcome.
2. **No surface for parallel intents.** The current single-column card shows one
   prose block. A turn produces *N private intents + 1 shared recap*; that needs
   a two-column surface (intents aside + recap main) — which the retired
   journey-board already prototyped (`purgatory` `.story-grid`, `320px 1fr`).

## Proposed Solution

### 1. Stage tree: add a `Play` branch with dynamic `turn:<n>` stages

Extend the FR-475 tree. After **Characters**, add a **Play** branch peer, gated on
the whole preplan being reviewed (synopsis ✓, key scene ✓, **all** character cards
✓). Like the character roster, turns are **dynamic** — addressed by id
`turn:<n>` and resolved at runtime, not declared in `STAGES`.

```
Story
└── Synopsis ✓
    ├── Key Scene ✓
    ├── Characters ✓   (all cards reviewed)
    └── Play                              ← unlocks once preplan is complete
        ├── Turn 1   (dynamic; weave / edit / accept on the recap)
        ├── Turn 2
        └── …        (Accept on Turn N seeds Turn N+1)
```

### 2. Data model (extends `story.json`)

```jsonc
{
  // …preplan (synopsis, key_scene, characters)…
  "stage": "turn:2",
  "turns": [
    {
      "n": 1,
      "intents": {
        "kara":  { "thinking": "the fire buys me ten seconds",
                   "intent":   "break cover and rush the ledge to free Naru" },
        "tarek": { "thinking": "…", "intent": "…" },
        "naru":  { "thinking": "…", "intent": "…" },
        "sela":  { "thinking": "…", "intent": "…" }
      },
      "recap": { "text": "Turn 1 — Kara breaks cover as Sela's fire…",
                 "reviewed": true }
    },
    { "n": 2, "intents": { … }, "recap": { "text": "Turn 2 — …",
                                           "reviewed": false } }
  ]
}
```

- `intents` is keyed by character id (the same slug the roster uses).
- `recap` is a `{text, reviewed}` entry — **byte-identical in shape to every other
  stage entry**, which is what lets `weave`/`edit`/`accept` operate on it
  unchanged (see §4). `turns[n].intents` lives *outside* that entry and is never
  routed through the stage machinery — it is read-only render context.
- **→ decided (scene bound):** the **running scene** a character reads =
  `key_scene.text` + the **last 3** accepted `recap.text` values
  (oldest→newest) + the turn number — not a mutation of `key_scene` itself, and
  bounded so the prompt cannot grow without limit. `previous` is a character's
  intent from turn `n-1` **only** (a single prior, not full history). Widening
  either window is a future FR.

### 3. Graph: one `turn.yaml` (map over cast → consolidate)

**→ decided (one graph, not two):** a single `turn.yaml` produces **both** the
per-character intents and the recap, mirroring the proven purgatory
`weave-beat.yaml` shape (`type: map` over the cast → consolidate). No separate
`turn_intents` graph.

```mermaid
flowchart LR
  START([scene, cast, history]) --> M{{map over cast}}
  M -->|per character| CI[character_intent.yaml<br/>scene · sheet · history · prev intent]
  CI --> J[(intents[])]
  J --> R[turn_recap.yaml<br/>scene · all intents · turn n]
  R --> OUT([intents + recap])
```

The map's `over: {state.cast}` / `as: char` exposes a **per-item dict**, so the
session pre-assembles each cast item as `{name, sheet, previous}` and the
per-character prompt reads `{state.char.sheet}` / `{state.char.previous}` off the
item. Scene-level vars (`scene`, `history`, `turn_n`) are passed flat — exactly
as `weave-beat.yaml` passes `chapter_goal` / `recent_history`.

- **`character_intent.yaml`** (per character, run by the map node). Inputs:
  `char` (the `{name, sheet, previous}` item), `scene` (key scene + bounded
  recap digest), `history` (the turn number / log framing). Output two dry
  labeled fields: `THINKING:` (private — what they notice, fear, want this turn)
  and `INTENT:` (one concrete action they will attempt this turn).
- **`turn_recap.yaml`** (consolidation). Inputs: `scene`, the list of
  `{name, intent}`, and the turn number. Output: a dry **"Turn N — …"** recap of
  what actually happens when the intents collide, in order — the same factual,
  no-purple-prose voice as `key_scene.yaml`.

### 4. Session operation: `play_turn` via a dedicated `_invoke_turn` path

**→ decided (do not overload `_invoke_stage`):** `_invoke_stage` is `str → str`
(`_clean_text(result.get(output_key))`) and the whole
`weave`/`edit`/`accept`/`_entry`/`_view` chain assumes one `{text, reviewed}`
entry. A turn returns *N intents + 1 recap*, which does not fit — so the turn gets
its own invocation path while reusing the recap entry for everything else:

- `turn:<n>` resolves like `char:<id>` (dynamic `resolve_stage`), and `_entry`
  gains a `turn:` branch returning **`turns[n].recap`**. Because that is already
  a `{text, reviewed}` entry, `weave` / `edit` / `accept` operate on the recap
  **with no change**.
- A new `_invoke_turn(doc, n)` builds the cast bundles (`{name, sheet,
  previous}`) + bounded scene + history, runs `turn.yaml`, **writes
  `turns[n].intents` into the doc as a side effect**, and **returns the recap
  text** for `entry["text"]`. `_invoke_stage` stays honest (`str → str`); the
  structured side-channel is isolated to the turn path.
- `_autodraft` and `weave` dispatch to `_invoke_turn` when the stage is a
  `turn:<n>`, else to `_invoke_stage` as today.

The operation itself, parallel to `weave`/`accept`:

1. Resolve the reviewed cast + key scene + the bounded digest of prior
   `turns[].recap.text` (last 3).
2. For each character, look up their turn `n-1` intent (single prior).
3. Run `turn.yaml` once via `_invoke_turn` → writes `intents`, returns `recap`.
4. Append a `turns[]` record with `n = len(turns)+1`; set `stage = "turn:<n>"`;
   persist.
5. Render the two-column turn view.

The **recap card reuses the existing weave/edit/accept**: Iterate re-runs the
whole `turn.yaml`, edit autosaves the recap prose, and **Accept** freezes
`recap.reviewed = true`, commits "Turn N actions" to the turn log, and seeds
**Turn N+1** (auto-drafts the next turn on entry, exactly as preplan stages
auto-draft — never a "Begin play" splash).

**→ decided (intents are co-generated, not hand-editable):** because Iterate
re-invokes the whole graph, it **re-rolls the intents along with the recap** — and
that is the desired invariant: the displayed intent cards always match the
generation that produced the visible recap, so the two can never drift apart. The
user cannot type into an intent card; they *can* refresh the whole turn via
Iterate. Accept freezes both together. (A per-intent editable route is explicitly
deferred — see Out of Scope.)

### 5. UI — two-column turn surface (wireframe)

Reuse the purgatory layout (`.story-grid { grid-template-columns: 320px 1fr }`,
`#story-aside` left, main right) inside the existing `#app-body` swap, so the live
breadcrumb stays put.

```
┌─ 🎲 Dungeon Master ──────────────────────────────────────────────────┐
│ Story › Synopsis ✓ › Key Scene ✓ › Characters ✓ › Play › Turn 2       │ ← breadcrumb
├───────────────────────────┬──────────────────────────────────────────┤
│  Turn 2 — Intents         │   📜 Turn 2 actions                       │
│  (#story-aside, 320px)    │   (main editable card, 1fr)               │
│ ┌───────────────────────┐ │  ┌─────────────────────────────────────┐ │
│ │ Kara                  │ │  │ Kara breaks cover and rushes the    │ │
│ │ THINKING the fire     │ │  │ ledge as Sela's fire spreads; Tarek │ │
│ │   buys me ten seconds │ │  │ wheels to meet her and Naru works   │ │
│ │ INTENT  rush the      │ │  │ his bonds loose in the smoke…       │ │
│ │   ledge, free Naru    │ │  │                                     │ │
│ ├───────────────────────┤ │  │ (editable prose — autosaves on      │ │
│ │ Tarek                 │ │  │  change, same component as every    │ │
│ │ THINKING …            │ │  │  other stage)                       │ │
│ │ INTENT  …             │ │  └─────────────────────────────────────┘ │
│ ├───────────────────────┤ │  ┌ prompt ───────────────────────────┐   │
│ │ Naru   THINKING …     │ │  │ Describe a change to apply…        │   │
│ │        INTENT  …      │ │  └────────────────────────────────────┘   │
│ ├───────────────────────┤ │   [ ↻ Iterate ]   [ ✓ Accept ]           │
│ │ Sela   THINKING …     │ │                                           │
│ │        INTENT  …      │ │   Accept → freezes Turn 2, seeds Turn 3   │
│ └───────────────────────┘ │                                           │
└───────────────────────────┴──────────────────────────────────────────┘
        read-only context              the one authoritative outcome
```

- Left **intent cards**: one per principal (so 2–4, never a wall), name +
  `THINKING` (muted italic) + `INTENT` (parchment). **Read-only** = not
  hand-editable; they refresh as a set when the recap is Iterated (§4).
- Main **recap**: the existing `text_block` editable card with Iterate/Accept.
- **Breadcrumb** gains a `Play` group peer and, inside it, per-turn members
  (`Turn 1`, `Turn 2`, …) exactly like the Characters branch lists cast members.
- On narrow screens the grid collapses to one column (aside above main), reusing
  the purgatory `@media (max-width: 768px)` rule.

### 6. New / changed files (anticipated)

| File | Change |
|------|--------|
| `examples/dungeon_master/turn.yaml` | new graph: map `character_intent` over cast → `turn_recap` |
| `examples/dungeon_master/prompts/character_intent.yaml` | new per-character THINKING/INTENT prompt |
| `examples/dungeon_master/prompts/turn_recap.yaml` | new consolidation prompt |
| `examples/dungeon_master/api/tree.py` | add `Play` peer + `turn:<n>` resolution + breadcrumb members |
| `examples/dungeon_master/api/session.py` | `play_turn`, turn log, auto-draft of next turn |
| `examples/dungeon_master/api/routes/story.py` (or synopsis.py) | `POST /story/turn` |
| `examples/dungeon_master/api/templates/components/turn_card.html` | new two-column turn view |
| `examples/dungeon_master/api/templates/base.html` | port `.story-grid` / `#story-aside` CSS from purgatory |

## Acceptance Criteria (walkthrough checklist, not gates — FR-474 J3/J4)

- [ ] Once synopsis ✓, key scene ✓, and **all** character cards ✓, the breadcrumb
      shows a navigable **Play** peer; before that it is absent/locked.
- [ ] Starting a turn prompts **each principal** and produces, for every
      character, a `THINKING` and an `INTENT` (2–4 intent cards, matching the
      capped roster).
- [ ] The consolidated **"Turn N actions"** recap is non-empty, renders in the
      main editable card, and names each principal at least once. (Structural
      check only — a mocked walkthrough cannot verify the semantic "every intent
      honoured or thwarted" claim, so that is deliberately *not* asserted.)
- [ ] The recap card supports the same weave / edit / accept as other stages;
      **Accept** freezes the turn, appends it to the turn log, and seeds Turn N+1.
- [ ] Turn 2's character prompts receive the prior recap as `history` and each
      character's Turn 1 intent as `previous`.
- [ ] Layout is two-column (intents aside + recap main) on wide screens and
      collapses to one column under 768px.
- [ ] Walkthrough tests under `examples/dungeon_master/tests/` cover: Play unlocks
      only when preplan is complete, a turn yields N intents + a recap, accept
      seeds the next turn, and history/previous threading into Turn 2.
      (No `@pytest.mark.req`; visibility harness only — LLM mocked at the two
      executor boundaries, as in `test_synopsis_prototype.py`.)

## Out of Scope

- Any CAP/REQ/gate/demo-log governance (FR-474 J3 still in force).
- Dice, stats, initiative order, or rules adjudication — the recap is authored by
  the LLM + DM, not computed.
- Editable/iterable per-character intent cards (deferred — §4 makes intents
  co-generated and non-hand-editable; a per-intent weave route is a future FR).
- Scene digest beyond the last 3 recaps, or multi-turn `previous` history.
- Changing `_invoke_stage`'s `str → str` contract — the structured turn result is
  isolated to `_invoke_turn`.
- Persisting turns to a chapter/manuscript file (the turn log lives in
  `story.json` for the prototype).

## Scope Freeze (Judged 2026-06-08)

Deliverables = the six anticipated files above, implementing the inline
**→ decided** rulings, plus walkthrough tests asserting the structural acceptance
criteria. The motivation was confirmed against code (the preplan genuinely
dead-ends — `_accept_target` returns `None` after the last character) and the map
mechanism is proven (`purgatory/weave-beat.yaml`). What is not in the design or
the anticipated-files list shall not be built.

## Alternatives Considered

- **Single-column sequential intents** (scroll a list, then a recap). Rejected —
  the DM needs intents and outcome side-by-side; that is the whole point of
  porting the purgatory two-column grid.
- **One combined prompt** ("write the turn for all characters at once"). Rejected
  — loses each character reasoning from their own sheet privately; the map over
  the cast is what makes intents independent and the recap a genuine consolidation.
- **Compute outcomes from rules.** Rejected for this prototype — the DM authors
  the recap; FR is about the intent→recap surface, not a rules engine.

## Related

- FR-475 / `tree.py` / `session.py` — the preplan tree this extends; the
  `char:<id>` dynamic-stage + breadcrumb-member pattern is the template for
  `turn:<n>`.
- `examples/dungeon_master/purgatory/api/templates/base.html` — the `.story-grid`
  / `#story-aside` two-column CSS to port.
- `examples/dungeon_master/purgatory/weave-beat.yaml` — the map-over-cast →
  consolidate graph shape to mirror.
- `examples/dungeon_master/key_scene.yaml` — the dry, factual recap voice
  `turn_recap.yaml` should match.

## Implementation Status (2026-06-08)

Shipped under the frozen spec. All 17 DM prototype walkthrough tests pass
(11 preplan + 6 new turn) and the turn graph was verified live against
`vertex/gemini-3.5-flash`: each principal produced structured private
THINKING + INTENT and the recap consolidated them into a dry "Turn 1 — …"
account naming every character (LangSmith trace captured).

**Files (built):**

| File | Status |
|------|--------|
| `examples/dungeon_master/turn.yaml` | new — map `character_intent` over cast → `turn_recap` (lints clean) |
| `examples/dungeon_master/prompts/character_intent.yaml` | new — per-character `output_schema` {thinking, intent} |
| `examples/dungeon_master/prompts/turn_recap.yaml` | new — consolidation; names cast by index, not LLM echo |
| `examples/dungeon_master/api/tree.py` | `TURN_*` consts, `turn:<n>` resolution, `preplan_complete`, Play breadcrumb |
| `examples/dungeon_master/api/session.py` | `_invoke_turn` side-channel, `_turn_record`, scene/prior helpers, `_field`, dispatch in weave/autodraft/accept/can_visit, `StageView.kind`/`.intents` |
| `examples/dungeon_master/api/templates/components/turn_card.html` | new — two-column intents aside + recap (reuses `stage_card`) |
| `examples/dungeon_master/api/templates/components/app_body.html` | branch to `turn_card` when `stage.kind == "turn"` |
| `examples/dungeon_master/api/templates/components/stage_card.html` | added a turn-specific hint |
| `examples/dungeon_master/api/templates/base.html` | ported `.story-grid` / `#story-aside` + `.intent-card` CSS + 768px collapse |
| `examples/dungeon_master/tests/test_turn_prototype.py` | new — 6 walkthrough tests (gate, autodraft, two-column, accept-seeds-next, iterate-rerolls, members) |

**Deviation from §6 (anticipated files) — no new route.** The plan anticipated a
`POST /story/turn`. The judged J3 design routes the turn's recap through the
existing `{text, reviewed}` entry, so turns reuse the stage-agnostic
`weave` / `edit` / `accept` / `nav` endpoints unchanged — entering, iterating,
accepting, and navigating turns all work through the existing four routes. A
fifth route would have been dead weight. `routes/synopsis.py` is untouched.

**Faithful to the rulings:** J1 one graph, per-character `{name, sheet, previous}`
bundles on the map item; J2 intents co-generated each pass (recap-only steer,
proven by `test_iterate_rerolls`); J3 dedicated `_invoke_turn` keeps
`_invoke_stage` a pure `str → str`; J4 scene = key scene + last-3 recaps,
single prior intent per character; J5 auto-draft Turn 1 on preplan completion,
no splash; J6 structural acceptance assertions only (count of intent cards,
non-empty fields, recap names principals, `turns[n+1]` created, `Play › Turn N`
crumb).

**Out-of-scope held:** no CAP/REQ/gate/demo-log (FR-474 J3), no editable intents,
no rules engine, `_invoke_stage` contract unchanged.
