# FR-475: Dungeon Master v2 — Preplan as Navigable Scene + Characters

**Priority:** MEDIUM
**Type:** Prototype enhancement (continues FR-474; inherits its prototype regime)
**Status:** Implemented — Approved with amendments (A1–A4 folded in; defaults 1–6 adopted)
**Effort:** ~1 day (prototype) — the `char:<id>` dispatch, roster expansion, name
injection, and breadcrumb rebuild are more than the original half-day estimate.
**Requested:** 2026-06-07
**Continues:** FR-474 (stage-driven DM v2). Same J3/J4 rules apply — no CAP/REQ,
no tests-first gate, no demo regeneration; the deliverable is a keep/kill/reshape
decision, not a green pipeline. Walkthrough tests stay under `examples/`.

## Summary

Reshape the preplan stage that follows the synopsis. Replace the single linear
**plot** stage with **two synopsis-derived branches** — a **key scene** and a
**characters** roster that spawns **one card per character** — reachable by
**breadcrumb navigation** rather than a one-way accept-advance cursor. The key scene
and every character card keep the exact same `weave / edit / accept` control the
synopsis already uses.

## Value Statement

The DM shapes the two things that actually seed play — a pivotal scene and the cast —
directly from the accepted synopsis, and can move freely between them to adjust either,
instead of being marched through a single linear plot step.

## Problem

The current chain is strictly linear: `synopsis → plot`, where `accept` advances a
single cursor one step forward (FR-474). Two limits:

1. **Wrong artifact.** A three-act *plot* is premature preplan output. What a DM needs
   first from a synopsis is a **key scene** (a concrete, playable anchor) and the
   **characters** — both are direct, independent reads of the synopsis.
2. **No navigation.** Siblings cannot coexist or be revisited. The `stage` cursor only
   moves forward via `accept`; there is no way to jump from the scene to the characters
   and back to tune either. The breadcrumb is a passive trail, not a control.

## Proposed Solution

### Stage model: linear chain → tree with a dynamic roster

Today `STAGES` is an ordered tuple and `_next_stage` walks it. Generalize to a tree.
The **synopsis** is the root that gates its children. **Key Scene** is a static leaf.
**Characters** is a *roster* parent that, once woven, spawns **one navigable card per
character** (per the decision: 1 character per card).

```
Story
└── Synopsis              (root — must be reviewed before children unlock)
    ├── Key Scene         (static leaf; context: synopsis)   ← weave / edit / accept
    └── Characters        (roster; context: synopsis)        ← weave → derives names
        ├── Elara         (dynamic card; context: synopsis) ← weave / edit / accept
        ├── Coil          (dynamic card; context: synopsis) ← weave / edit / accept
        └── …             (one per name in the roster)
```

Two kinds of stage now exist:

- **Static stages** — declared in `STAGES` as today, gaining a `parent: str | None`
  (synopsis `parent=None`; key_scene/characters `parent="synopsis"`).
- **Dynamic character cards** — *not* in `STAGES`. They are instances addressed by id
  (`char:elara`) and materialised from the roster derived on synopsis accept. Each is
  treated as a stage whose `parent="characters"`, `context=("synopsis",)`, and whose
  seed is “draft this one character from the synopsis.”

**`characters` is a branch group, not a screen.** It is never rendered as its own
card. Its only job is to derive a **roster of names** from the synopsis (as a side
effect of accepting the synopsis) and to own the character cards as children. There is
**no intermediate roster/index page** — the character cards are reached *directly* from
the breadcrumb, which lists the cast inline as peers (see Navigation).

```python
STAGES = (
    Stage("synopsis", "Synopsis", ".../synopsis.yaml"),
    Stage("key_scene", "Key Scene", ".../key_scene.yaml",
          parent="synopsis", context=("synopsis",),
          seed="Write the single pivotal key scene implied by the synopsis."),
    Stage("characters", "Characters", ".../character_roster.yaml",
          parent="synopsis", context=("synopsis",), kind="roster",
          seed="Name the characters the synopsis requires (names only)."),
)
# Per-character cards are built at runtime from the roster, each using one shared
# character.yaml graph + prompts/character.yaml, parameterised by the character name.
# `characters` is non-visitable: its roster weave fires once on synopsis accept; its
# label only seeds the breadcrumb branch group — it has no card screen of its own.
```

The linear `_next_stage` cursor is replaced by **explicit navigation**: the `stage`
field in the per-session document is set by a nav action, not only by `accept`. A
character card's `stage` value is its instance id, e.g. `char:elara`.

### Graphs + prompts

- **Retire `plot.yaml` + `prompts/plot.yaml`** to `purgatory/` (parts bin; reuse the
  three-act prose later if an outline stage returns).
- **`key_scene.yaml`** (`state: synopsis, draft, instruction, key_scene`; node
  `key_scene`, `parse_json: false`, `context: synopsis`) + **`prompts/key_scene.yaml`**:
  one vivid, playable scene in plain prose — who is present (named), where, the stakes,
  the turn. Same empty-vs-nonempty-draft logic as the other prompts.
- **`character_roster.yaml`** + **`prompts/character_roster.yaml`**: from the synopsis,
  emit the **list of named characters** (names only, newline- or comma-separated plain
  text the session splits into a roster). Run as a side effect of accepting the
  synopsis; its output feeds the breadcrumb's inline character peers — there is no
  roster screen. Just the cast list that spawns the cards.
- **`character.yaml`** (`state: synopsis, name, draft, instruction, character`; node
  `character`, `parse_json: false`) + **`prompts/character.yaml`**: draft **one**
  character in plain prose from the synopsis + the character's `name` — their role,
  want, voice, and tie to the key events. Same empty-vs-nonempty-draft logic. One shared
  graph serves every character card (parameterised by `name`).

Prose cards throughout (no structured JSON yet — FR-474 / `phase_2_plot.md` decision).

### Navigation: the breadcrumb is the only selector

There are exactly two selection acts, and the breadcrumb handles both — no separate
index page, no tree sidebar:

1. **Branch selection (Key Scene vs Characters).** Once the synopsis is reviewed the
   breadcrumb **fans out** its two children as peers:
   `Story › Synopsis✓ · Key Scene · Characters`. Both are clickable; the current one is
   highlighted. (Two fixed branches is small enough that a fan-out *is* the whole
   branch selector — equivalent to a 2-item segmented control.)
2. **Member selection (which character).** While in the Characters branch, the cast is
   listed **inline as peers** after the group label:
   `Story › Synopsis✓ · Key Scene › Characters › Elara Coil Vesh`. The character names
   are the member selector — this inline peer list replaces the old index screen.

Mechanics:

- New nav route **`POST /story/nav`** (`session_id`, `stage`) sets the current stage
  (static name or `char:<id>`) and re-renders `#app-body`. Guarded: navigating to a
  child whose parent is not yet `reviewed` is rejected (accept the synopsis first;
  reach a character card only after the roster exists).
- Clicking **Characters** (the group label) jumps to the first — or last-visited —
  character; it is never a screen of its own.
- `weave / edit / accept` routes are unchanged — they keep operating on the *current*
  stage, which navigation now sets, including a character instance.
- **`accept`** stops being a linear advance. It marks the current stage `reviewed`. At
  the synopsis it derives the character roster (side effect) and lands on the first
  child (Key Scene). At a character card it lands on the next unreviewed character; when
  the cast is complete it stays on the current card read-only (there is no index to
  return to). Auto-draft on entry (FR-474) still fires when landing on an undrafted,
  well-fed card (each character card auto-drafts from the synopsis + its name on first
  visit).

*Deferred enhancement (not in scope):* if the inline peer list grows crowded, the last
crumb can become a `▾` dropdown of siblings (the GitHub branch-switcher / macOS path-bar
pattern). Ship the inline peers first; add the dropdown only if they prove unwieldy.

### Document schema

```jsonc
{
  "tagline": "...",
  "stage": "char:elara",                       // static name or char:<id>
  "synopsis":  { "text": "...", "reviewed": true },
  "key_scene": { "text": "...", "reviewed": false },
  "characters": {
    "reviewed": false,                          // derived: true when every card reviewed (no screen)
    "roster": ["elara", "coil"],                // ordered character ids
    "cards": {
      "elara": { "name": "Elara", "text": "...", "reviewed": true },
      "coil":  { "name": "Coil",  "text": "",    "reviewed": false }
    }
  }
}
```

The `{text, reviewed}` per-card shape is unchanged; what changes is the *access path*.
The flat `_entry(doc, name)` (`doc.setdefault(name, …)`) only works for static stages.
For `char:<id>` stages, the entry lives nested at `doc["characters"]["cards"][<id>]` —
see A1/A2 below. Character ids are slugified names (suffix `-2`, `-3`… on collision).

### Implementation constraints (binding — from Judge; A1–A4)

These pin the mechanics the behavior above assumes. The current code
(`api/session.py`) does not yet satisfy them; they are the work.

- **A1 — `char:<id>` dispatch via a synthetic Stage.** `char:<id>` is not in
  `STAGE_BY_NAME`. `_stage()` must detect the `char:` prefix and build a *runtime*
  `Stage(name=f"char:{id}", label=card["name"], graph=character.yaml,
  context=("synopsis",), seed="Draft this one character from the synopsis.")` from the
  roster entry. `_stage`, `_entry`, `_view`, `weave`, `edit`, and `accept` all gain a
  `char:` branch.
- **A2 — nested entry access.** `_entry()` must route `char:<id>` to
  `doc["characters"]["cards"][id]` (creating `characters`, `roster`, `cards` as needed),
  while static stages keep the flat top-level path. The story_doc JSON store serializes
  either shape; only the access path differs.
- **A3 — `name` injection.** `_invoke_stage` builds variables from
  `draft + instruction + context` only. For `char:` stages it must also inject
  `name=card["name"]` so `character.yaml` can draft the right character. The synthetic
  Stage carries the name; a thin `char:` branch (or extra param) adds it to `variables`.
- **A4 — roster derivation is its own step, not `_invoke_stage`.** On synopsis `accept`,
  run `character_roster.yaml` once, split its plain-text output into names, slugify to
  ids, and create `cards[id] = {"name": Name, "text": "", "reviewed": false}` for each
  *new* id (existing cards preserved). This is dedicated logic — `_invoke_stage` returns
  a single string and cannot expand a list. Note synopsis-accept now runs **two** graphs
  (roster expansion + Key Scene auto-draft).

The **roster-exists** guard is subsumed by **synopsis-reviewed** (the roster is always
derived on accept), so a single parent-reviewed gate suffices. The breadcrumb control
needs new `StageView` fields beyond `trail` — the branch peers (Key Scene / Characters)
and, in the Characters branch, the character peers, each with current/clickable/reviewed
flags. That `StageView` contract change is part of the breadcrumb rebuild.

## UI Sketch

Low-fidelity wireframes of the new screens. All swaps target `#app-body`; the
breadcrumb is the persistent control strip above it. `✓` = reviewed (read-only),
`●` = current node, `›` = clickable ancestor/sibling.

### Breadcrumb states (the only selector)

The strip fans out at the branch level (Key Scene vs Characters) and, while in the
Characters branch, lists the cast inline as peers — there is no separate index page.

```
Synopsis (before accept):   Story · Synopsis●
On Key Scene:               Story › Synopsis✓ · Key Scene● · Characters›
On Elara:                   Story › Synopsis✓ · Key Scene› · Characters › Elara● Coil› Vesh›
On Coil:                    Story › Synopsis✓ · Key Scene› · Characters › Elara› Coil● Vesh›
```

`●` = current, `✓` = reviewed ancestor, `›` = clickable. Key Scene and Characters are
the two branch peers; inside the Characters branch the character names appear inline as
the member selector. Clicking **Characters** jumps to the first (or last-visited)
character. Branch peers are inert until the synopsis is reviewed; character names appear
only after the roster is derived (on synopsis accept).

### Key Scene card (static leaf — same card as synopsis)

```
┌─ Story › Synopsis✓ · Key Scene● ──────────────────────────────┐
│                                                                │
│  KEY SCENE                                              [✓ Accept]
│  ────────────────────────────────────────────────────────────  │
│  The lantern-keeper Mara climbs the seized clock-tower as the  │
│  gears below grind to their final tooth. Coil waits at the     │
│  rim, knife drawn, offering the one wind-key left … (prose,    │
│  directly editable — autosaves)                                │
│  ────────────────────────────────────────────────────────────  │
│  Describe a change ▸ [ make the stakes more personal      ]    │
│                                            [ Iterate ]         │
└────────────────────────────────────────────────────────────────┘
```

The cast is selected from the breadcrumb's inline peers — there is **no** Characters
index page. Clicking a character name opens its card directly.

### Single character card (dynamic leaf — same card mechanic)

```
┌─ Story › Synopsis✓ · Key Scene› · Characters › Elara● Coil› ───┐
│                                                                │
│  ELARA                                                  [✓ Accept]
│  ────────────────────────────────────────────────────────────  │
│  Elara keeps the harbor lanterns and the city's last honest    │
│  clock. She wants the tower's wind-key back not for power but  │
│  to buy the drowned quarter one more night … (prose, directly  │
│  editable — autosaves; auto-drafted on first entry)            │
│  ────────────────────────────────────────────────────────────  │
│  Describe a change ▸ [ give her a debt to Coil            ]    │
│                                            [ Iterate ]         │
└────────────────────────────────────────────────────────────────┘
```

Accept here marks Elara reviewed and lands on the next undrafted/unreviewed
character; when the cast is complete it stays on the card read-only (there is no
index to return to).

## Acceptance Criteria (walkthrough checklist, not gates — FR-474 J3/J4)

- [ ] After the synopsis is accepted, the breadcrumb fans out **Key Scene** and
      **Characters** as navigable branch peers; clicking Key Scene opens it, clicking
      Characters opens the first character. Each swaps `#app-body`.
- [ ] Key Scene weaves a single pivotal scene from the accepted synopsis (auto-drafted
      on first entry).
- [ ] Accepting the synopsis derives a **roster of named characters**; the breadcrumb
      lists them inline as member peers (1 character per card, **no index screen**).
- [ ] Clicking a character name opens that character's card; it auto-drafts that single
      character from the synopsis + name on first entry.
- [ ] A `char:<id>` stage reads and writes `characters.cards[<id>]` (nested), and its
      graph receives the character's `name` (A1–A3).
- [ ] Accepting the synopsis runs the roster graph and expands the cast into
      `characters.cards` (one entry per name, slug ids, existing cards preserved) **and**
      auto-drafts Key Scene — two graph runs on one accept (A4).
- [ ] The same `weave / edit / accept` control adjusts the key scene **or any one
      character card**; edits autosave; empty prompt = pure save.
- [ ] Navigating to a sibling before the synopsis is reviewed, or to a character card
      before the roster exists, is rejected.
- [ ] No `plot` stage is reachable from the v2 app; `plot.yaml` + `prompts/plot.yaml`
      live in `purgatory/`.
- [ ] Walkthrough tests under `examples/dungeon_master/tests/` cover: synopsis→accept
      derives the roster + character cards, nav into a character card via a breadcrumb
      peer, weave/edit/accept of one character, key-scene weave, and the parent-gate
      rejections. (No `@pytest.mark.req`; visibility harness only.)

## Open Questions (resolved in Judge — defaults adopted)

1. **Characters — RESOLVED: one character per card, no index screen.** Characters is a
   breadcrumb branch group, not a page; each named character is its own auto-drafted,
   individually adjustable card, selected inline from the breadcrumb peers.
2. **How is the roster produced — names only, or names+blurbs?** *Default:* names only
   (`character_roster.yaml` emits a plain list); the per-character prose lives on each
   card via `character.yaml`. Keeps the roster cheap and the card the source of truth.
3. **Can the DM add/remove characters?** *Default for prototype:* re-weaving the roster
   re-derives names and adds any new ones (existing cards preserved by id); explicit
   add/delete UI is deferred. Removal/renaming is out of scope.
4. **Free navigation vs. ordered?** *Default:* free — once the synopsis is reviewed, the
   DM may visit Key Scene and any character card in any order (selected from the
   breadcrumb peers) and revisit any. The only gates are parent-reviewed (children) and
   roster-exists (character cards).
5. **What does `accept` do at the leaves?** *Default:* mark reviewed + jump to the next
   unreviewed sibling/character; when all are reviewed, stay on the current card
   read-only (there is no index to return to). No further stage exists yet.
6. **Does editing the synopsis after children exist invalidate them?** *Default:* no
   auto-invalidation in the prototype; re-weaving a card re-reads the current synopsis.
   Cascade/staleness is out of scope.

## Non-Goals (must not leak in)

- Structured JSON for scene or characters (prose card stays — FR-474 decision).
- Relationship graphs, per-character portraits, chapter/outline/beat stages, turn-loop
  play.
- Explicit character add/remove/rename UI, and cascade invalidation when an upstream
  stage changes.
- A dedicated Characters index/roster **page** (removed by request — character
  selection lives in the breadcrumb's inline peers).
- Any CAP/REQ/gate/demo-log governance (FR-474 J3 still in force).

## Alternatives Considered

- **One roster prose card (no per-character cards).** Simpler (no dynamic instances, no
  roster/cards schema), but the user explicitly chose *1 character per card*. Rejected.
- **Keep it linear (`synopsis → key_scene → characters`).** A one-way cursor cannot
  revisit, but the request is to *navigate to and adjust any* scene or character.
  Rejected.
- **Reuse `plot` and just add characters.** Leaves the wrong first artifact (a full
  three-act plot) in place; the request replaces plot with a key scene. Rejected.
- **A dedicated Characters index/roster screen.** A full page listing the cast was the
  first sketch; removed by request — the inline breadcrumb peers are a cheaper selector
  and keep the “one card at a time” feel. Rejected.
- **Dropdown/menu breadcrumb (last crumb `▾`).** The well-trodden switcher pattern
  (GitHub branch, macOS path bar). Deferred, not rejected — add only if the inline peer
  list gets crowded.

## Related

- Continues FR-474 (stage-driven DM v2); reuses its `Stage`/`STAGES`, `weave/edit/accept`,
  auto-draft-on-entry, and `story_doc`.
- `examples/dungeon_master/api/session.py` (STAGES, nav, accept), `api/routes/synopsis.py`
  (add `/story/nav`), `api/templates/components/{breadcrumb,stage_card,app_body}.html`.
- `examples/dungeon_master/docs/phase_2_plot.md` (prose-card decision this inherits).
- Diary `docs/diary/diary-2026-06-07-the-cursor-that-forgot-to-weave.md` (the
  `cursor_is_not_artifact` heuristic motivating auto-draft on sibling entry).

## Implementation Status (2026-06-07)

**Done — 11 walkthrough tests green** (`examples/dungeon_master/tests/test_synopsis_prototype.py`).

Graphs (new): `key_scene.yaml`, `character_roster.yaml`, `character.yaml` — all
lint clean. The roster graph is a pure function of the synopsis (no `draft`/
`instruction` channels); the character graph injects `name` per card (A3).
Prompts (new): `prompts/{key_scene,character_roster,character}.yaml` — prose, with
empty-vs-nonempty `draft` branches. `character_roster` emits **names only**, one
per line.

Tree model (`api/tree.py`, new): frozen `Stage` dataclass + `STAGES` (synopsis
root; `key_scene` static leaf; `characters` non-visitable `kind="roster"` branch
group). `resolve_stage` maps a `char:<slug>` cursor to a **synthetic Stage** (A1)
backed by `CHARACTER_GRAPH`, with `var_name` = card name for injection.
`unique_slug` adds `-2/-3` suffixes on collision. `breadcrumb(doc)` returns crumb
dicts (`label/stage/current/reviewed/group/member`); branch peers appear only once
the synopsis is reviewed, and cast members render inline as peers only while a
`char:` card is current.

Session (`api/session.py`, rewritten): `StageView.crumbs` replaces `trail`;
`_entry` resolves nested `characters.cards[id]` (A2) vs flat stage entries;
`navigate(target)` with `_can_visit` gate (synopsis always; `char:` needs synopsis
reviewed + known card; static needs parent reviewed; roster rejected). `accept`
computes `_accept_target` → synopsis-accept runs **two graphs** (`_expand_roster`
+ `key_scene` auto-draft, A4); key-scene/char accept advance to the next unreviewed
character (wrapping), else read-only. `_autodraft` fills an empty sibling on entry.

Presentation: `routes/synopsis.py` adds `POST /story/nav`; `app.py` index lands via
`DMSession.view()`; `breadcrumb.html` rebuilt into a control (`hx-post /story/nav`,
`hx-vals` session+stage), current/member styling in `base.html`. Default tagline:
**"10,000 B.C. in heat. Adult story."**

Retired: `plot.yaml` → `purgatory/plot.yaml`; `prompts/plot.yaml` →
`purgatory/prompts/plot-v2.yaml` (v1 `purgatory/prompts/plot.yaml` preserved).

Deferred (per Open Questions): last-crumb `▾` dropdown; cascade invalidation; any
explicit add/remove/rename UI.
