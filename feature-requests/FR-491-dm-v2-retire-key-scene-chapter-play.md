# FR-491: Retire the Key Scene — Play the Book Chapter by Chapter; Cast Before Chapters

**Priority:** HIGH (the Key Scene is the spine of the play loop, and it can only
ever play one moment of a many-chapter book)
**Type:** Refactor / Re-architecture (DM v2 prototype; inherits FR-474 J3/J4 regime)
**Status:** **Judged — Approved with amendments, scope frozen** (2026-06-15). The
core direction is sound and the Key Scene is correctly identified as the wrong
unit. But the proposal **glosses two load-bearing seams** that judgement against
the code exposed (G1 the director is BEATS/END-shaped; G2 retiring `chapter.yaml`
deletes the only producer of `world_state`) and leaves the turn-address scheme
ambiguous. All three are resolved below (J-amendments A–E). Enforce per the frozen
scope, not the original prose.
**Effort:** Large (touches tree, navigation, session, turn_ops, chapter_ops,
templates, and every walkthrough test)
**Requested:** 2026-06-15
**Continues / supersedes:** FR-477 (the play loop), FR-479/481/482/483 (the
director), FR-484/485/487 (the three finishes), FR-488/490 (book chapters). The
chapter outline stops being a dead-end planning artifact and becomes the unit of
play.

**Model under test:** `vertex` / `gemini-3.5-flash`.

## Problem

The whole preplan was built around a single **Key Scene** — one pivotal moment
the play loop drives toward (turns → director judges its BEATS → scene-complete →
finishes). But a book is *many* chapters; one key scene can only ever play one of
them. Meanwhile FR-488 already splits the synopsis into the real units of the
book — an ordered set of chapters, each with its own summary and a forward-carried
`world_state` — yet that outline was a planning artifact with no play behind it,
derived *before* the cast existed (at synopsis-accept), so it could not lean on
the established characters.

Three faults, one cause — the Key Scene is the wrong unit:

1. **Single-scene ceiling.** The arc the player can play is exactly one scene.
2. **Order inversion.** Chapters derive at synopsis-accept, before any character
   card, so the outline cannot reference the cast it will be played by.
3. **Dead outline.** The chapter cards expand to static prose (`chapter.yaml`) and
   dead-end; the rich play machinery (intents, director, recap, world_state carry)
   never touches them.

## Proposal

Retire the Key Scene. Make **each chapter the unit of play**: its summary +
inherited `world_state` is the per-chapter plan the turns drive toward, exactly as
the Key Scene's card used to be. Derive the chapter outline **after** the cast is
reviewed. Compose the whole book from the played chapters.

New shape:

```
Synopsis (root)
└── Characters (roster)     one char:<id> card per principal — reviewed first
      └── Chapters          derived once the cast is complete → overview (TOC)
            └── chapter:<n> EACH chapter is played: its turns drive its summary
                  · turn loop: map(cast → intents) → director → recap
                  · scene plan = chapter summary + inherited world_state
                  · chapter "played" when its director reports scene_complete
                  └── The Book   whole-book finish: compose every played chapter
```

## Judgement (proposed — to be frozen)

- **J1 — Order (cast before chapters).** `synopsis`-accept derives the **roster
  only** and lands on the first character card. Accepting the **last** character
  derives the chapter outline (`_expand_chapters` moves here) and lands on the
  Chapters overview. The preplan gate becomes **synopsis ✓ + all characters ✓**
  (no key scene).
- **J2 — Retire the Key Scene.** Delete the `key_scene` Stage, `key_scene.yaml`,
  its prompt, and every read of it: `running_scene`, `parse_beats`' source,
  `_parse_scene_characters`, `final_cut_context`, `preplan_complete`, the
  navigation landing, the breadcrumb peer. Delete dead code; no shim, no optional
  alt-mode (Commandment 8).
- **J3 — Chapter as play unit.** Each `chapter:<n>` card carries a per-chapter
  turn loop. Turn storage moves from the flat `doc["turns"]` to per-chapter
  `chapters.cards[cid]["turns"]`. The turn `scene` becomes **this** chapter's
  summary + its inherited `world_state` + the last-3 recaps of **this** chapter.
  The chapter's played recaps compose its prose (`card["text"]`); the world-state
  ledger at chapter end carries to the next chapter (FR-488 J7 preserved). The
  static `chapter.yaml` prose-expansion is **replaced** by play.
- **J4 — Beats source.** A chapter summary is a paragraph, not a BEATS card. The
  director keeps `phase` + `scene_complete` + `steer` + `continuity`;
  `beats_satisfied` uses the existing graceful fallback (no canonical BEATS →
  raw phrases kept cumulatively, `beats_total` 0). The continuity actor filter
  now reads the **roster** as the authoritative cast (chapters introduce no new
  principals), not a scene CHARACTERS block.
- **J5 — Chapter completion + landing.** A chapter is *played* when its director
  reports `scene_complete`. Accepting a played chapter lands on the next chapter;
  the last chapter dead-ends into the whole-book finish. (Mirrors the FR-484 turn
  → Final Cut landing, but per-chapter.)
- **J6 — Whole-book finish.** Retire the three turn-based finishes
  (`final_cut` / `final_cut_turns` / `walkthrough`) and their graphs. Replace with
  ONE **Book** finish that composes the manuscript from every played chapter
  (each chapter's final text + world_state), gated on **all chapters played**.
- **J7 — Navigation / breadcrumb.** `preplan_complete` → cast-only. The playable
  branch is now Chapters. Breadcrumb: Story · Synopsis · Characters(group) ·
  Chapters(group → overview; each chapter a playable member). The Book finish
  appears once every chapter is played.

### Frozen out

- No per-chapter structured BEATS card (the summary is the plan; the director's
  fallback already handles a beat-less plan).
- No keeping the Key Scene as an optional mode (retire, don't branch).
- No dice/rules engine; no structured chapter editor; turns stay narrative-only.

## Acceptance criteria

- [ ] Accepting the synopsis lands on the **first character** (not key scene, not
      chapters); the roster is derived, the outline is **not** yet.
- [ ] Accepting the **last character** derives the chapter outline and lands on
      the **Chapters overview**, which lists every chapter.
- [ ] No `key_scene` stage is reachable; `key_scene.yaml` and its prompt are gone;
      `grep key_scene` finds no live references.
- [ ] Each `chapter:<n>` plays a turn loop scoped to that chapter; turns persist
      under `chapters.cards[<id>].turns`, never the flat `doc["turns"]`.
- [ ] A chapter's turn `scene` is built from its own summary + inherited
      `world_state` + its own prior recaps (a test asserts chapter 2's play sees
      chapter 1's world_state, not chapter 1's turns).
- [ ] Accepting a played chapter lands on the next; the last dead-ends into the
      **Book** finish, which composes from every played chapter.
- [ ] Full DM suite green; `ruff` clean; import contract KEPT.
- [ ] One live `vertex` witness: synopsis → cast → outline → play chapter 1 to
      scene-complete → chapter 2 inherits chapter 1's world_state → Book finish.

## Related

- `examples/dungeon_master/api/tree.py` — `STAGES`, `breadcrumb`, gates
- `examples/dungeon_master/api/navigation.py` — `can_visit`, `accept_target`
- `examples/dungeon_master/api/session.py` — `accept`, `_expand_chapters`, `_view`
- `examples/dungeon_master/api/turn_ops.py` — the play loop + finishes (the bulk
  of the change: per-chapter scene source, storage, the book finish)
- `examples/dungeon_master/api/chapter_ops.py` — chapter outline + world_state
- `examples/dungeon_master/{turn,chapter}.yaml`, `prompts/*` — graphs/prompts
- FR-488 (chapters + world_state carry), FR-490 (chapters overview), FR-477 (play)

## Judgement (frozen — 2026-06-15)

Walked the code to test every premise. The retirement is justified, but two seams
the proposal treats as deletions are actually **changes**, and one mechanism is
underspecified. The scope below supersedes the proposal's J1–J7 where they differ.

### Confirmed blast radius (the "delete every read" criterion, made enumerable)

`key_scene` is read in exactly these live sites — the retirement is GREEN only
when all are gone or repointed:

- `tree.py`: the `key_scene` Stage in `STAGES`; the breadcrumb peer.
- `navigation.py`: `accept_target` synopsis-landing (`return "key_scene"`); the
  `preplan_complete` import + play gate.
- `session.py`: the docstring shape example (cosmetic) + `_view`/landing flow.
- `turn_ops.py`: `running_scene` (`plan = doc["key_scene"]`), `_canonicalize_beats`
  source, `_filter_continuity` source (`_parse_scene_characters`),
  `final_cut_context` (`key_scene = …`), and the now-dead `parse_beats` /
  `_parse_scene_characters` if the finishes go.
- `key_scene.yaml` + `prompts/key_scene.yaml`.

### G1 — The director is BEATS/END-shaped; a chapter summary is not (AMENDMENT A)

**Premise tested:** J4 claims the director "keeps `phase` + `scene_complete`" for
free. **False.** `prompts/turn_direct.yaml` is built entirely around a scene with
"a START, BEATS, and an END": `scene_complete` is defined as "the scene's END
state has been reached"; `beats_satisfied` is "the key-scene BEATS that have
occurred." A chapter summary is a prose paragraph with **no END condition** — fed
as-is, the director has nothing to test completion against and `scene_complete`
becomes meaningless.

**Resolution (load-bearing, NOT a deletion):** revise `turn_direct.yaml` (and the
`scene`-consuming `character_intent` / `turn_recap` framing) so the per-chapter
plan is *the chapter summary as the intended arc* + *the inherited `world_state`
as the established START*. `scene_complete` ⇒ "every event the chapter summary
describes has now occurred in the recaps." `beats_satisfied` ⇒ "the chapter's key
events that have occurred" (free-text; the existing `_canonicalize_beats` fallback
keeps them cumulatively with `beats_total = 0`, so no canonical-BEATS parser is
needed — `parse_beats` is retired with the finishes). This is a **generative-seam
change** and must be live-witnessed, not just unit-tested.

### G2 — Retiring `chapter.yaml` deletes the only producer of `world_state` (AMENDMENT B)

**Premise tested:** J3 says "the static `chapter.yaml` prose-expansion is replaced
by play" and "the world-state ledger at chapter end carries to the next chapter
(FR-488 J7 preserved)." **Contradiction.** `chapter.yaml` is the *only* thing that
emits `{text, world_state}`. If play produces the chapter text from recaps, then
**nothing produces the `world_state` ledger** — and the forward-carry (the
load-bearing FR-488 seam) silently breaks. A play loop that threads an empty
world_state forward is the exact "plausible wrong answer" Commandment 6 forbids.

**Resolution:** add a **chapter-close world_state derivation** — a new small graph
`chapter_close.yaml` (+ prompt) invoked once when a chapter is played
(`scene_complete`), reading the inherited `world_state` + this chapter's played
recaps → the end-of-chapter `world_state` ledger written to the card. This
*replaces* `chapter.yaml`'s world_state half; `chapter.yaml` (one-shot summary →
prose) is retired. `chapter_ops.invoke_chapter` is replaced by
`chapter_ops.close_chapter`. A test asserts chapter 2's play sees chapter 1's
derived world_state.

### Resolved ambiguities

- **AMENDMENT C — turn address & storage.** Turns are stored at
  `chapters.cards[<cid>]["turns"]` (a list, same record shape as today). Turn
  stages are **chapter-qualified**: `turn:<cid>:<n>`. `resolve_stage`,
  `turn_record`, `turn_direction`, `turn_intents`, `prior_intents`,
  `running_scene`, `invoke_turn`, and the session `_entry`/`_view` turn branches
  all take the chapter id, not the flat `doc["turns"]`. The existing
  `turn_card.html` + director card are **reused** per chapter (no new turn UI).
- **AMENDMENT D — continuity source.** With no scene CHARACTERS block,
  `_filter_continuity` uses the **roster** as the authoritative cast and
  `_parse_scene_characters` is retired. Accepted residual: a chapter that
  legitimately introduces a synopsis-supported non-roster actor (a beast, a third
  party) will over-flag it as a continuity breach. Acceptable in the prototype —
  named, not hidden.
- **AMENDMENT E — the Book finish.** ONE `book.yaml` composes the manuscript from
  every played chapter's final `text` + `world_state`, gated on **all chapters
  played** (each chapter's last turn reported `scene_complete`). The three
  turn-based finishes (`final_cut` / `final_cut_turns` / `walkthrough` + their
  graphs, prompts, and the `turn_ops` machinery `climax_turn`,
  `final_cut_context`, `validate_cut_turns`, `render_*`, `walkthrough_*`,
  `invoke_final_cut*`, `invoke_walkthrough*`) are **deleted wholesale**. No
  cross-turn climax derivation survives (frozen out).

### Enforce sequencing (RED-first, one concern per commit)

1. **Reorder + cast gate.** synopsis-accept → first character; last-character-accept
   derives the outline → Chapters overview. `preplan_complete` → `cast_complete`
   (synopsis ✓ + all chars ✓). *(Supersedes the uncommitted "chapters before key
   scene" test edits — discard those; the order is now cast → chapters.)*
2. **Retire Key Scene.** Delete the stage, graph, prompt, and every read (the
   blast-radius list). Director prompt amended (G1/A) in this slice so the turn
   loop still compiles against a chapter plan.
3. **Per-chapter play.** Turn storage + addressing (C); `running_scene` from the
   chapter summary + inherited world_state + this chapter's recaps; chapter-close
   world_state derivation (G2/B); continuity from roster (D). Chapter played on
   `scene_complete`; accept lands on the next chapter.
4. **The Book finish.** Delete the three finishes (E); add `book.yaml`; gate on
   all chapters played; landing + breadcrumb.

**Authority granted** for the frozen scope above. Each slice: failing test first,
minimal change, separate commit. One live `vertex` witness at the end exercising
both generative seams (chapter completion judged from a summary; world_state
threaded across two played chapters). Diary with a Seed.

---

## Implementation Status

- **Slice 1 — Reorder + cast gate** ✓ `aaa841b0` (FR-491 plan frozen at `ffa6a43a`).
  `preplan_complete` → `cast_complete`; synopsis-accept lands on the first character;
  last-character-accept derives the outline → Chapters overview. 84 tests pass.
  *Note:* `git add -u <dir>` swept a stale `README.md` into the commit — it is rewritten
  in the docs step.
- **Slice 2 — Retire Key Scene** ✓ `2b1ccb1e` (+156/−549). Deleted the `key_scene`
  Stage, graph, and both prompt files; `running_scene` now reads `_chapter_plan(doc)`;
  `_canonicalize_beats` keeps free-text phrases cumulatively (`beats_total=0`); amended
  `turn_direct` / `character_intent` / `turn_recap` to the "chapter plan" framing
  (Amendment A / G1). Removed `_norm`, `_match_beat`, `_BEAT_FLOOR`, `_BEAT_MARGIN`,
  `_NAME_SPLIT_RE`, `_parse_scene_characters`, `_filter_continuity`, and the
  `SequenceMatcher` import. 79 tests pass; ruff + lint-imports + vulture clean.
  - **Deviation:** Amendment D's continuity-source switch (roster is the authoritative
    cast; drop the `_filter_continuity` post-filter) landed in this slice rather than
    Slice 3, because `_filter_continuity` read `doc["key_scene"]` and could not survive
    the stage's deletion. Accepted residual per D: a synopsis-supported non-roster actor
    over-flags (named, acceptable).
  - **Kept until Slice 4:** `parse_beats`, `_SECTION_RE`, and the finishes machinery
    (`final_cut_context` still reads `key_scene` → `""`).
- **Slice 3 — Per-chapter play** — pending.
- **Slice 4 — The Book finish** — pending.
