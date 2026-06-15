# FR-488: DM v2 → Book Scope, Step 1 — Chapter Overview + Per-Chapter Descriptions with World State

**Priority:** MEDIUM
**Type:** Enhancement (DM v2 prototype; inherits FR-474 J3/J4 regime)
**Status:** Done (2026-06-15). Enforced RED-first per the J1–J7 judgement; all
acceptance criteria met, live `vertex` forward-carry witnessed (see *Implementation
Status*). **Approved, scope frozen** to the chapter
*planning* layer with an explicit prose `world_state` forward-carry. Three
“mirrors the roster exactly” claims are corrected below (structured outline parse,
composed chapter card, fixed chapter set); the FR is rebased onto FR-489 (pure
`navigation`); chapters are ruled an **independent branch** that does not touch
`preplan_complete` or the play loop. See *Judgement*.
**Effort:** ~0.5 day (one roster-style graph + one chapter-card graph + stage wiring + tests)
**Requested:** 2026-06-15
**Judged:** 2026-06-15
**Continues:** FR-475 (the preplan tree + the Characters roster→cards→expand
pattern this mirrors). Same J3 rules: **no CAP/REQ, no CI gate, no demo-log**; the
prototype tests under `examples/dungeon_master/tests/` are a visibility harness.

**Model under test:** `vertex` / `gemini-3.5-flash`.

## Summary

Add the missing middle of the book-scope recursion. The architecture is
scale-invariant:

```
BOOK     premise → book outline → [chapters]            → final manuscript
                   ───────────     ──────────              ──────────────
                   (the gap we fill now)                   (later)
CHAPTER  chapter brief → chapter outline → [scenes] → chapter cut   (later)
SCENE    scene brief   → key scene       → [turns]  → final cut     (today's app)
```

Today **premise** is the tagline and **book outline** is the synopsis. What we
lack is **chapters in the plural**. This FR adds, right after the synopsis, a
**Chapters** stage that (1) splits the synopsis into chapter-size chunks — a
one-paragraph summary per chapter — and (2) spawns one **chapter card** per chunk,
each expandable into a **full chapter description that carries an explicit world
state** (what is true at the end of that chapter: who is where, what has changed,
what is now established).

This reuses the exact **Characters roster → cards → expand** mechanism (FR-475),
one level up: the synopsis-accept derives a chapter list the way it derives a
cast; each chapter card is the same weave/edit/accept card as every other stage.

## Value Statement

The author gets a steerable chapter breakdown — and, in each chapter card, an
explicit world-state ledger — *before* any prose is written. This is the
consistency anchor book scope rests on: the planned world state at each chapter is
the canon later scenes must respect, the same way roster binding stopped the scene
from minting an unsanctioned character.

## Problem

A scene fits in one context window; a book does not. The session's evaluation arc
(diaries 2026-06-14 *fifty-call story* → *consistency over length* → *final cut
that only stitched*) established that the pipeline's real product is **consistency
held across length**, and that the load-bearing work is the *planning/expansion
seams plus the consistency anchors*, not the consolidation passes. To reach book
length we must first decompose the single synopsis into an ordered set of chapters
**and** give each chapter an explicit, carried-forward world state — because the
canonical failure of long-form generation is drift/contradiction, and a window
that cannot see chapter 3 cannot keep chapter 12 consistent with it.

We start with the cheapest honest increment: the *planning* layer for chapters. No
play-loop wiring, no manuscript consolidation — just the chapter breakdown and the
per-chapter world-state ledger, proven additive and reusing the roster pattern.

## Proposed Solution

### Document shape (additive, mirrors `characters`)

```jsonc
{
  "synopsis":  { "text": "...", "reviewed": true },
  "chapters": {                       // new roster-like group, parallel to characters
    "reviewed": false,
    "order": ["1", "2", "3"],         // chapter ids (1-based, stable)
    "cards": {
      "1": {
        "title": "Chapter 1 — ...",
        "summary": "One-paragraph overview (the chunk split from the synopsis).",
        "text": "Full chapter description (expanded from the summary).",
        "world_state": "What is true at the END of this chapter: characters' status/location, established facts, what changed.",
        "reviewed": false
      }
    }
  }
}
```

`world_state` starts as **prose** (a short structured paragraph), not a typed
store — minimal first, per the J3 prototype regime. Promoting it to a deterministic
typed ledger is explicitly *out of scope here* and noted as future work.

### Stages (mirror the Characters roster pattern)

1. **`chapters` roster group** (non-visitable, `kind="roster"`), parented on
   `synopsis`, `context=("synopsis",)`. Its graph (`chapter_outline.yaml`) reads
   the accepted synopsis and emits **one paragraph per chapter** — the chunk
   split. The session splits the output into `chapters.order` + one card per
   chunk (carrying `title` + `summary`), exactly as `_expand_roster` does for the
   cast.
2. **`chapter:<n>` cards** (dynamic leaves, resolved at runtime like `char:<id>`
   and `turn:<n>`). Each card auto-drafts on entry by expanding its `summary`
   into a full `text` **and** a `world_state`, via `chapter.yaml`, given the
   synopsis + this chapter's summary + the **previous chapter's world_state** as
   context (the forward-carry — the seed of the consistency anchor).

### Flow

- Accepting the **synopsis** keeps its current landing on Key Scene, and
  *additionally* derives the chapter outline (spawns the cards) — just as it
  derives the cast today. (Both side-effects run on synopsis-accept; chapters and
  characters are siblings under the synopsis.)
- The breadcrumb gains a **Chapters** group with one peer per chapter, gated on
  the synopsis being reviewed (identical gate to Characters).
- Each chapter card uses weave/edit/accept unchanged.

### Files (all under `examples/dungeon_master/`)

- `chapter_outline.yaml` + `prompts/chapter_outline.yaml` — split synopsis → one
  paragraph per chapter (names/titles + summaries). Mirrors `character_roster`.
- `chapter.yaml` + `prompts/chapter.yaml` — expand one chapter: `summary` (+
  synopsis + previous `world_state`) → full `text` + `world_state`. Parses JSON
  `{text, world_state}` so the ledger is a first-class field. Mirrors `character`.
- `api/tree.py` — `CHAPTER_PREFIX`, `Stage("chapters", …, kind="roster")`,
  `resolve_stage` chapter branch, breadcrumb peers, gate in `_can_visit`.
- `api/session.py` — `_chapters(doc)` accessor, `_expand_chapters` (mirror of
  `_expand_roster`), `_entry` chapter branch, chapter auto-draft in `_autodraft`,
  chapter weave branch (parse `{text, world_state}`), synopsis-accept also calls
  `_expand_chapters`.

## Acceptance Criteria

- [x] **(J7, RED first)** Expanding `chapter:2` threads `chapter:1`'s
      `world_state` into the chapter graph variables (assert on the variables
      passed, not on LLM content). — `test_chapters.py::test_chapter_two_expansion_threads_chapter_one_world_state` (RED witnessed: `chapter_ops` ImportError → GREEN).
- [x] Accepting the synopsis spawns N chapter cards, each with a non-empty
      one-paragraph `summary` parsed from a structured `{title, summary}` outline
      (J1; N decided by the model, fixed at derivation per J6). — `chapter_outline.yaml` (parse_json) + `chapter_ops.outline_chapters` + `_expand_chapters`; `test_outline_chapters_parses_structured_title_summary`.
- [x] Entering a chapter card auto-drafts a full `text` **and** a non-empty
      `world_state` via `_compose_special` → `invoke_chapter` (J2). — `session._compose_special` `kind == "chapter"` branch.
- [x] `_expand_chapters` is idempotent: re-running on an already-populated
      `chapters.order` is a no-op (J6). — `test_expand_chapters_is_idempotent` (outline graph invoked exactly once).
- [x] **(J3)** `preplan_complete` and the play-loop unlock are unaffected by the
      presence or absence of chapters; synopsis-accept still lands on `key_scene`. — `test_chapters_do_not_affect_preplan_complete`; `tree.preplan_complete` never reads `chapters`.
- [x] Chapters are additive: deriving/expanding chapters mutates neither the
      synopsis, the characters, nor (if present) any played turns (immutability
      test, mirroring FR-484's). — `test_invoke_chapter_does_not_mutate_doc`; `chapter_ops` are pure reads.
- [x] The Chapters group is gated on the synopsis being reviewed and is
      non-visitable as a group; `chapter:<n>` peers are reachable via
      `navigation.can_visit`; `accept_target(chapter:<n>)` → `chapter:<n+1>` then
      `None` (J4/J5), covered in `test_navigation.py` (no `DMSession`). — `test_chapter_card_needs_synopsis_reviewed_and_membership`, `test_chapter_unlocks_without_preplan_or_play`, `test_accept_chapter_lands_on_next_chapter_then_dead_ends`.
- [x] Prototype tests added under `examples/dungeon_master/tests/` (visibility
      harness; no `@pytest.mark.req`). — `test_chapters.py` (8) + 3 in `test_navigation.py`; full DM suite 77 passed.
- [x] One cited live `vertex` run recorded here, read for: chapters partition the
      synopsis without gaps/overlap, and each `world_state` is consistent with the
      prior chapter's (forward-carry holds). — see *Implementation Status* below.

## Implementation Status (2026-06-15 — DONE)

**Files.** New graphs `examples/dungeon_master/chapter_outline.yaml` (parse_json
`{chapters:[{title,summary}]}`) + `chapter.yaml` (parse_json `{text,world_state}`)
and prompts `prompts/chapter_outline.yaml` + `prompts/chapter.yaml`. New pure
module `api/chapter_ops.py` (`outline_chapters`, `invoke_chapter` — graph reads,
no mutation). `api/tree.py`: `CHAPTER_*` constants, the `chapters` roster Stage,
the `chapter:<n>` `resolve_stage` branch (`kind="chapter"`), and the Chapters
breadcrumb group (peer after Key Scene, members when in-branch). `api/session.py`:
`_chapters` accessor, `_entry` chapter branch, `_compose_special` `kind=="chapter"`
branch (threads forward `world_state` via `invoke_chapter`), `_expand_chapters`
(idempotent — J6), wired into `accept()` beside `_expand_roster`. `api/navigation.py`:
`can_visit` + `accept_target` chapter branches (independent of preplan/play — J3).
Both shared test mocks gained `chapter_outline`/`chapter` branches (chapters now
spawn on every synopsis-accept).

**Judgement adherence.** J1 structured outline (not `split_roster`); J2 composed
card (not bare `_invoke_stage`); J3 independent branch (`preplan_complete`
untouched); J4 rebased onto FR-489 `navigation`; J5 chapter chain dead-ends; J6
fixed set / idempotent; J7 RED-first forward-carry. `lint-imports` KEPT; ruff
clean.

**Live `vertex` / `gemini-3.5-flash` witness.**
- `chapter_outline` over a flood-raider synopsis → **4 ordered chapters**
  (Clashing Clans → Lost to the Current → Uneasy Truce → High Ground): a clean
  partition, no gaps, no overlap (J1, OQ2 model-decided count).
- `chapter:1` (no prior world state) → prose + `world_state`: *“Jaren, Kara's
  brother, is alive and by her side … floodwaters threaten both factions,
  forcing an immediate halt to the combat.”*
- `chapter:2` with that exact `world_state` as `previous_world_state` → the
  chapter **opened from Jaren alive at her side** and advanced to losing him; new
  `world_state`: *“Jaren has been swept away … and is lost. Tarek is alive,
  leading his surviving clan up the steep ridge.”* The forward-carry held — the
  prior ledger was honored, never contradicted, and advanced (J7, OQ3 previous-
  only). Traces in LangSmith (run `019ec9c5-83f8-7750…` for the outline).

**Honest caveat (carried from the eval arc).** At this 2-chapter scale the
forward-carry's *value* (consistency held across length) is visible only as
plumbing, not as a measured win. The consistency-vs-length eval (the Seed) is the
proper witness; this FR delivers the seam the eval will exercise, not the proof
that it scales.

## Open Questions (for Judgement)

- **OQ1 — World state shape.** Prose paragraph (proposed, minimal) vs typed
  JSON object now. *Recommendation:* prose now; typed deterministic ledger is a
  separate FR (it is the real consistency engine and deserves its own RED tests).
- **OQ2 — Chapter count.** Model-decided from the synopsis (proposed, mirrors
  roster) vs author-specified. *Recommendation:* model-decided; the author edits
  the outline card to add/remove like any other prose.
- **OQ3 — Forward-carry source.** Pass the *previous chapter's* `world_state`
  (proposed) vs accumulate all prior world states. *Recommendation:* previous only
  for now; full accumulation belongs with the typed ledger (OQ1) where dedup is
  deterministic, not prompt-stuffed.
- **OQ4 — Do chapters feed the play loop now?** *Recommendation:* No. This FR is
  the planning layer only. Wiring a chapter → its scenes (the CHAPTER row of the
  recursion) is the next FR, justified by the consistency-vs-length eval.

## Judgement (2026-06-15)

The premise is sound and the increment is the cheapest honest one: build the
planning seam and the world-state forward-carry, defer the typed ledger. Approved.
But “mirrors the Characters roster — each chapter card is the same card as every
other stage” is true only for the *UI* (weave/edit/accept); at the *invocation
seam* it is false in two ways, and the FR predates FR-489. The ruling makes the
divergences explicit so the enforcer does not discover them mid-build.

- **J1 — The chapter outline is a *structured* parse, not a `split_roster` mirror.**
  `character_roster` emits names one-per-line and `split_roster` line-splits them.
  A chapter outline emits `{title, summary}` per chapter — structure
  `split_roster` cannot carry. `chapter_outline.yaml` therefore uses an inline
  schema (`parse_json: true`, a list of `{title, summary}`); `_expand_chapters`
  consumes that structured list, it does **not** call `split_roster`. Say so in
  the prompt and the accessor.

- **J2 — The chapter card is a *composed* stage, dispatched through
  `_compose_special`, not `_invoke_stage`.** A character card is a single
  `_invoke_stage` call returning one `text`. A chapter card expansion returns
  **two** outputs (`text` + `world_state`) and reads context the plain path has
  no access to (this chapter's `summary`, its index, and the *previous* chapter's
  `world_state`). That is the same shape as a turn or a finish. Put the
  invocation in a dedicated `invoke_chapter(doc, n, *, instruction, draft)` (new
  `chapter_ops.py`, or `turn_ops` if it stays small) and add **one** branch to
  `_compose_special` — this is exactly the extension FR-489 Phase 1 made a
  one-place edit. The auto-draft and weave paths then reach chapters through
  `_compose_special`, like every other composed stage. (Confirmed by the FR's own
  “`chapter.yaml` parses JSON `{text, world_state}`” — that is a composed stage,
  not an ordinary card.)

- **J3 — Chapters are an INDEPENDENT branch; they must not touch
  `preplan_complete` or synopsis landing.** The existing app is scene-scoped:
  `preplan_complete` (synopsis ✓ + key_scene ✓ + cast ✓) unlocks the play loop, and
  56 tests depend on it. Chapters are a *book-layer sibling* that feeds nothing
  downstream yet (OQ4). Therefore: `preplan_complete` is **unchanged** (chapters
  are not a precondition for play); synopsis-accept still lands on `key_scene`;
  `_expand_chapters` runs in `accept()` *alongside* `_expand_roster` purely as an
  additive side-effect. An acceptance test must assert the play-loop unlock is
  unaffected by the presence/absence of chapters.

- **J4 — Rebase onto FR-489. The file list names methods that no longer exist.**
  FR-489 Phase 2 removed `_can_visit` and `_accept_target`; reachability and
  landing now live in pure `api/navigation.py`. So:
  - the `chapter:` reachability branch goes in **`navigation.can_visit`**
    (gated on synopsis reviewed + id present in `chapters.cards`, mirroring the
    `char:` branch), staying pure;
  - the chapter **landing** goes in **`navigation.accept_target`** (see J5),
    staying pure;
  - the chapter **expansion side-effect** (`_expand_chapters`) goes in
    `session.accept()` next to `_expand_roster`, not in navigation.

- **J5 — Define chapter landing; it dead-ends (it feeds nothing yet).**
  `accept_target(chapter:<n>)` returns `chapter:<n+1>` while a next chapter
  exists, else `None`. It does **not** advance into the play loop or any scene
  (OQ4). Add this pure branch to `navigation.accept_target` and cover it in
  `test_navigation.py`.

- **J6 — OQ2 corrected: the chapter SET is fixed at derivation.** Numeric
  positional ids (`1..N`) plus “author edits the outline to add/remove” collide:
  the roster's idempotent append keys by *slug* (`if cid not in cards`), which
  positional numeric ids cannot do without re-derive collisions. Ruling:
  `_expand_chapters` derives **once** — it is a no-op when `chapters.order` is
  already populated (simpler than the roster's per-item check, and it removes the
  count-mismatch ambiguity). The author may edit a chapter's prose
  (`summary`/`text`/`world_state`); changing the *number* of chapters is **out of
  scope** for this FR. (OQ1 prose-now: accepted. OQ3 previous-only: accepted.
  OQ4 no play-loop wiring: accepted — it is what makes J5 a dead-end.)

- **J7 — The priority RED test is the forward-carry seam.** The first failing
  test asserts that expanding `chapter:2` threads `chapter:1`'s `world_state` into
  the graph variables (a deterministic-seam assertion on the *plumbing*, not the
  LLM's use of it — `world_state` content is mock-driven). The structured-outline
  parse (J1) and the additive/immutability + play-unlock-unaffected checks (J3)
  are the supporting RED tests. One cited live `vertex` run witnesses that the
  chapters partition the synopsis and the carried world states do not contradict.

Scope frozen to the above. Where the OQ recommendations and the Judgement differ
(OQ2), the Judgement governs.

## Alternatives Considered

- **One giant "expand synopsis into full book" prompt.** Rejected: it is the
  single-shot baseline the whole session indicted for length scope — no
  steering seams, no per-chapter world-state anchor, drift unbounded.
- **Typed world-state store now.** Deferred: it is the load-bearing consistency
  primitive and must be built RED-first as its own FR with a deterministic
  reducer + continuity gate, not smuggled into a planning-layer prototype.

## Related

- FR-475 (the roster→cards→expand pattern this mirrors)
- Diaries 2026-06-14: *the-fifty-call-story*, *the-final-cut-that-only-stitched*
  (consistency-over-length, provenance, the curve-vs-scale heuristic)
- Future: typed world-state ledger + continuity gate (the consistency engine);
  chapter → scenes wiring; manuscript consolidation; consistency-vs-length eval
