# FR-490: DM v2 → Chapters Need a Face — Outline Overview Card + Discoverable Inter-Chapter Navigation

**Priority:** HIGH (the chapter outline is the load-bearing view of FR-488 and it has no surface)
**Type:** Enhancement (DM v2 prototype; inherits FR-474 J3/J4 regime)
**Status:** **Done** (2026-06-15) — RED-first, GREEN, full DM suite + ruff +
import contract green, live `vertex` witness recorded below. Was: Judged —
**Approved, scope frozen** (2026-06-15). The proposal is sound
but rests on one false premise (a *new* `chapters` overview stage): a `chapters`
stage name **already exists** in `STAGES`, as a **dead** non-visitable roster, and
must be **repurposed**, not duplicated. Two further collisions the proposal glossed
(`_entry("chapters")` aliasing the group dict; the overview must not auto-draft) are
resolved below. See *Judgement* (J1–J7).
**Effort:** ~0.5 day (one view-model extension + one overview template + breadcrumb/landing wiring + tests)
**Requested:** 2026-06-15
**Judged:** 2026-06-15
**Continues:** FR-488 (the book-scope chapter data + navigation seams) and FR-489
(pure `navigation`). Same J3 rules: **no CAP/REQ, no CI gate, no demo-log**; the
prototype tests under `examples/dungeon_master/tests/` are a visibility harness.

**Model under test:** `vertex` / `gemini-3.5-flash`.

## Summary

FR-488 built the chapter outline as data and as a navigation model, but gave it no
presentation. The outline — *the book's plan*, the single most important artifact
of book scope — is the one thing a writer cannot see. This FR adds the missing
face:

1. **A Chapters overview card** — a table of contents listing every chapter's
   `title` + `summary` together, the view that makes an outline an outline.
2. **Per-chapter context on the card** — surface each chapter's `summary` and the
   forward-carried `world_state` *above* its prose, so the writer sees what the
   chapter is meant to be and what state it inherited (the J7 mechanism made
   visible at exactly the place it matters).
3. **Discoverable inter-chapter navigation** — the chapter member peers must be
   reachable without first diving blind into `chapter:1`.

## Value Statement

The author can finally *read the plan* — every chapter title and one-paragraph
summary in one place — and steer the book before any prose is written; and inside
each chapter card they see the inherited world state, turning the FR-488
consistency anchor from an invisible internal mechanism into a visible planning
surface.

## Problem

The FR-488 judgement (J1–J7) was entirely about the data and navigation seams:
structured outline parse, world-state forward-carry, idempotency, dead-ends.
**Presentation was never in scope**, and the character-card UI was copied one level
up. But a character roster legitimately needs no overview — the breadcrumb names
suffice — whereas a **book outline is an overview by definition**. Copying the
roster's UI silently dropped the one view that makes the feature usable. Concretely:

- **No overview.** The Chapters group crumb (`tree.breadcrumb`) lands on
  `chapter:1` and drops the writer straight into auto-drafted prose. There is no
  stage that renders all `{title, summary}` together. The breadcrumb is a corridor,
  not a table of contents.
- **No context on the card.** `StageView` (`session.py`) carries only
  `text`/`label`/`reviewed`. It never carries `summary` or `world_state`.
  `stage_card.html` renders `stage.text` only. Land on `chapter:1` and you see
  prose — never the one-paragraph summary that *defines* the chapter, never the
  world-state ledger threaded in from the previous chapter.
- **Navigation hidden.** The chapter member peers only render `if in_chapters`
  (`tree.breadcrumb`), so the set is invisible until you are already inside it.

This is the *“it’s just the old feature one level up”* trap (named in the FR-488
diary) biting the **presentation** seam this time: the data model rhymes with the
roster, but the *purpose* — a plan you read as a whole — diverges, and the copied
UI dropped exactly that.

## Proposed Solution

Two seams, the same split FR-488 used.

### Deterministic seam (code — unit-testable, no LLM)

1. **Extend `StageView`** (`session.py`) with two optional chapter fields:
   `summary: str = ""` and `world_state: str = ""`. `_view` populates them from the
   resolved chapter card when `stage.kind == "chapter"` (empty for every other
   stage — additive, no behavior change elsewhere).
2. **A `chapters` overview stage** (static, visitable, `kind="chapters"` or a small
   dedicated kind). `_view`/a small accessor exposes the ordered list of
   `{id, title, summary, reviewed}` cards for the template. The Chapters **group
   crumb** lands here (`stage = "chapters"`) instead of on `chapter:1`.
3. **`navigation.can_visit`** allows the `chapters` overview once the synopsis is
   reviewed (same gate as the chapter cards). The overview is read-only — no
   weave/accept, it is a directory.
4. **`tree.breadcrumb`** renders the chapter member peers whenever the synopsis is
   reviewed **or** the current stage is the overview/a chapter — so the chapter set
   is discoverable from the overview, not only from inside a chapter.

### Generative seam (none)

This FR adds **no new graph and no new prompt**. Everything rendered already exists
in the document (`title`, `summary`, `text`, `world_state` are written by FR-488).
This is purely a presentation/navigation change — which is precisely why it is a
`chore`-class prototype edit, not a `feat`.

### Template changes

- **New `chapters_overview` partial** (or a branch in `stage_card.html`): renders
  the table of contents — each chapter `title` as a clickable nav crumb to
  `chapter:<id>` with its `summary` beneath, and a ✓ on reviewed chapters.
- **`stage_card.html` chapter branch**: when `stage.kind == "chapter"`, render the
  `summary` (what this chapter is) and `world_state` (what it inherited) in a
  read-only context block *above* the prose textarea, then the existing
  weave/edit/accept form unchanged.

## Acceptance Criteria

- [ ] `StageView` carries `summary` and `world_state`; `_view` populates them for a
      chapter stage and leaves them empty for every non-chapter stage (unit test).
- [ ] The Chapters group crumb lands on the `chapters` overview, not `chapter:1`
      (breadcrumb/navigation test).
- [ ] `navigation.can_visit(doc, "chapters")` is `True` once the synopsis is
      reviewed and `False` before (unit test).
- [ ] Chapter member peers are present in the breadcrumb when on the overview, not
      only when on a chapter card (breadcrumb test).
- [ ] The overview template renders every chapter `title` + `summary`; the chapter
      card template renders `summary` + `world_state` above the prose (template
      smoke test or rendered-HTML assertion).
- [ ] The played turns / characters / final-cut surfaces are byte-for-byte
      unchanged — additive only (full DM suite stays green).
- [ ] One live `vertex` witness: accept a synopsis, confirm the overview lists the
      derived chapters with summaries, open a chapter, confirm its inherited
      `world_state` is shown. Recorded in *Implementation Status*.
- [ ] Diary reflection entry with a Seed.

## J3 Regime (inherited)

No CAP, no REQ tag, no CI gate, no demo-log. Prototype tests under
`examples/dungeon_master/tests/` carry no `@pytest.mark.req`. As a presentation-only
change with no new graph, this is a **`chore`** (or `refactor`) commit — no
changelog fragment required (changelog gate fires only on `feat`/`fix`). The diary
reflection is still written.

## Alternatives Considered

- **Render the overview inside the synopsis card.** Rejected: couples two stages,
  and the overview must be revisitable independently as the book grows.
- **Add an `overview` field to every roster group generically.** Rejected as
  premature abstraction (Commandment: no speculative extensibility); the character
  roster does not need one. Build the chapters overview concretely; generalize only
  if a second roster ever needs it.
- **Surface `world_state` only in a debug view.** Rejected: the inherited world
  state is authoring signal, not debug output — it belongs on the card the author
  edits.

## Judgement (2026-06-15)

The proposal's diagnosis is correct and the two-seam split is right (deterministic
only, no new graph/prompt). But the code does not match its central assumption, and
three concrete collisions must be nailed before enforcement. Scope is frozen to the
resolutions below; anything else is out.

### J1 — There is no "new" overview stage to add; repurpose the dead one

The proposal says *"add a `chapters` overview stage."* A `chapters` stage **already
exists** in `tree.STAGES` (`kind="roster"`, graph `CHAPTER_OUTLINE_GRAPH`, seed
"Split the synopsis…"). Critically it is **dead code**: unlike `_expand_roster`,
which invokes `STAGE_BY_NAME["characters"]`, `_expand_chapters` calls
`chapter_ops.outline_chapters(doc)` directly and **never touches the stage**. A
grep confirms `STAGE_BY_NAME["chapters"]` has zero references.

**Resolution:** *repurpose*, do not duplicate. Change that single existing Stage:
`kind="roster"` → `kind="chapters"`, **remove its `seed`**, keep
`parent="synopsis"`. This one edit makes it visitable (no longer the non-visitable
roster), gates it on synopsis-review for free (the generic `can_visit` parent
branch), and stops it auto-drafting (J3 below). Adding a second `chapters` entry
would shadow the first in `STAGE_BY_NAME` and is forbidden.

### J2 — The overview kind must be distinct so `app_body.html` can branch

`app_body.html` renders `turn_card.html` when `kind == "turn"`, else
`stage_card.html` (the weave/edit/accept form). An overview is a **read-only
directory**, not a card. It therefore needs its own `kind` (`"chapters"`) and its
own branch: `app_body.html` gains `{% elif stage.kind == "chapters" %}` →
`components/chapters_overview.html`. Reusing `kind=""` would wrongly render the
weave form; this is why J1 sets `kind="chapters"`, not `kind=""`.

### J3 — The overview must never auto-draft and never present weave/accept

Because the repurposed stage keeps a `graph`, `_autodraft` would try to generate
into it if it had a `seed`. **Removing the seed (J1) is load-bearing**, not
cosmetic: with no seed, `_autodraft` no-ops and `_view` leaves `text=""`. The
overview template renders **no** weave/edit/accept form, so `weave`/`accept` routes
are never reached for it. The overview is pure navigation.

### J4 — `_entry("chapters")` aliases the group dict — assert it stays harmless

`doc["chapters"]` is the FR-488 group dict `{reviewed, order, cards}`, not a
`{text, reviewed}` entry. When `navigate`/`_view` call `_entry(doc, "chapters")`,
the generic branch runs `doc.setdefault("chapters", …)` — a **no-op** since the key
exists — and returns the existing group dict. Reading `.get("text","")` yields `""`
(fine) and `.get("reviewed")` yields the group's own flag. This is acceptable **as
is** (no new `_entry` branch needed), but the behavior must be **pinned by a test**:
navigating to `chapters` must not mutate `order`/`cards`. Normalize-at-boundary: the
test is the boundary guard that this alias never corrupts the group.

### J5 — `StageView` carries the outline; `_view` populates it only for the overview + chapter cards

- Add `summary: str = ""`, `world_state: str = ""`, and
  `chapters: list[dict] = field(default_factory=list)` to `StageView`.
- `_view`: when `stage.kind == "chapter"`, set `summary`/`world_state` from the
  resolved card. When `stage.kind == "chapters"`, set `chapters` to the ordered
  `[{id, title, summary, reviewed}]` projection from `_chapters(doc)`. Every other
  stage leaves all three at their empty defaults — additive, no behavior change.

### J6 — Landing + discoverability are two edits in `tree.breadcrumb`, both required

1. The **Chapters group crumb** `stage` changes from `CHAPTER_PREFIX + ch_order[0]`
   to `"chapters"` (land on the overview, not blind into chapter 1).
2. The member-peer loop renders when `in_chapters` **or** `current == "chapters"`,
   so the chapter set is visible from the overview, not only from inside a chapter.

`navigation`: no change to `accept_target` (the overview is read-only, never
accepted; the existing chapter→chapter chain and dead-end stand). `can_visit` needs
**no chapters-overview branch** — the generic `STAGE_BY_NAME` + `parent` path
already gates a non-roster `chapters` stage on synopsis-review. Confirm with a test;
do not add a special case (no fourth special case — boundary parser, not ad-hoc).

### J7 — Templates: one new partial + one branch, nothing more

- **`components/chapters_overview.html`** (new): iterate `stage.chapters`; each row
  is a nav link to `chapter:<id>` (reuse the `hx-post="/story/nav"` pattern from
  `breadcrumb.html`) showing `title`, the `summary` beneath, and `✓` when reviewed.
- **`stage_card.html`** gains a `{% if stage.kind == "chapter" %}` read-only context
  block rendering `summary` (what this chapter is) and `world_state` (what it
  inherited) **above** the existing prose textarea; the weave/edit/accept form is
  unchanged.

### Frozen scope / out

- **No new graph, no new prompt, no new doc field.** Everything rendered already
  exists in the FR-488 document. This is presentation/navigation only → a
  **`chore`** (or `refactor`) commit; no changelog fragment (gate fires only on
  `feat`/`fix`); diary still required.
- **No `accept` for the overview**, no editing of the outline as a whole, no
  generic "overview for any roster" abstraction (the character roster does not need
  one — build chapters concretely; YAGNI).
- **Acceptance criteria stand as written**, refined by J1–J7: the "Chapters overview
  stage" criterion is satisfied by the *repurposed* stage, and the "lands on the
  overview" criterion means `stage == "chapters"`, not `chapter:1`.

**Authority granted.** Enforce RED-first: a failing test per J4 (alias no-op), J5
(`_view` populates `chapters`/`summary`/`world_state` for the right kinds, empty
elsewhere), and J6 (group crumb stage `== "chapters"`; member peers present on the
overview). Then GREEN with the minimal `tree`/`session`/template edits. One live
`vertex` witness recorded in *Implementation Status*. Diary with a Seed.

## Related

- `examples/dungeon_master/api/session.py` — `StageView`, `_view`, `_chapters`
- `examples/dungeon_master/api/tree.py` — `breadcrumb`, `resolve_stage` chapter branch
- `examples/dungeon_master/api/navigation.py` — `can_visit`, `accept_target`
- `examples/dungeon_master/api/templates/components/stage_card.html`,
  `breadcrumb.html`
- FR-488 (chapter data + navigation), FR-489 (pure navigation), FR-475 (preplan tree)

## Implementation Status

**Done — 2026-06-15.** RED-first under the FR-474 J3 regime (no CAP/REQ, no CI
gate, no changelog fragment; `chore` commit; diary required).

### What shipped

- **`tree.py`** — repurposed the *dead* `chapters` stage: `kind="roster"` →
  `kind="chapters"`, **removed** its `seed` (load-bearing: a seedless stage never
  auto-drafts, J3), kept `parent="synopsis"`. `breadcrumb` now lands the group
  crumb on `"chapters"` (not `"chapter:1"`) and renders member peers when on the
  overview *or* inside a chapter (`on_chapters`). `resolve_stage("chapters")`
  returns the repurposed stage; `chapter:<n>` unchanged.
- **`session.py`** — `StageView` gained `summary` / `world_state` / `chapters`;
  `_view` projects the chapter cards in order for `kind=="chapters"`, and surfaces
  the per-chapter `summary` + forward-carried `world_state` for `kind=="chapter"`,
  empty elsewhere. `_view` is pure — navigating the overview does **not** mutate
  the FR-488 group dict (J4 purity guard test).
- **Templates** — new `chapters_overview.html` (📚 table of contents, each row an
  `hx-post=/story/nav` link to `chapter:<n>` with a ✓ for reviewed); `app_body.html`
  branches to it on `kind=="chapters"`; `stage_card.html` shows the chapter's
  Summary + Inherited world state above the prose; `base.html` CSS for both.
- **`navigation.py`** — **unchanged**: the repurposed `kind=="chapters"` no longer
  matches the `kind=="roster"` early-return, so `can_visit` falls through to the
  generic `parent="synopsis"` gate (J6, confirmed by
  `test_chapters_overview_visitable_once_synopsis_reviewed`).

### Acceptance criteria

- [x] **Chapters overview card** lists every chapter `title` + `summary` together —
      *witnessed: 4 chapters projected with titles + summaries.*
- [x] **Per-chapter context** surfaces `summary` + inherited `world_state` above the
      prose — *witnessed on the chapter-1 and chapter-2 cards.*
- [x] **Discoverable navigation** — group crumb lands on the overview, member peers
      visible from it (`test_chapters_group_crumb_lands_on_overview`,
      `test_chapter_member_peers_visible_from_overview`).
- [x] Overview is visitable only once the synopsis is reviewed; never auto-drafts.
- [x] Navigating the overview does not mutate chapter order/cards (purity guard).

### Tests

7 new tests (6 RED → GREEN, 1 green-at-RED purity guard): `test_chapters.py` (J4
alias no-op; J5 `_view` populates `summary`/`world_state`/`chapters` for the right
kinds and empty elsewhere; J6 group crumb + member peers) and `test_navigation.py`
(J6 overview gated on synopsis-review). Full DM suite **84 passed** (was 77).
`ruff check` clean, `ruff format` unchanged, `lint-imports` — three-layer contract
**KEPT**.

### Live witness — `vertex` / `gemini-3.5-flash` (2026-06-15)

`tmp/witness_fr490.py` → a reviewed Iron-Age synopsis, real outline + chapter
expansion:

```
=== OVERVIEW kind='chapters' (4 chapters) ===
  [1] Chapter 1 — The Dawn Raid
  [2] Chapter 2 — The Broken Banks
  [3] Chapter 3 — The Cold Truce
  [4] Chapter 4 — The Last Valley

=== CHAPTER 1 CARD ===
world_state:  Hilde is alive, armed with a shortsword and shield ... has breached
              Gunnar's hall. Gunnar is alive, armed with a two-handed sword ...

=== CHAPTER 2 CARD (inherits ch1 world_state) ===
world_state:  Hilde is alive, armed with her shortsword, but has lost her shield.
              Gunnar is alive but unarmed, having lost his two-handed sword in the flood ...
```

The overview renders the whole plan; the chapter-2 card makes the FR-488
forward-carry **visible** — the shield Hilde held in ch1 is gone, Gunnar's sword
lost to the flood — exactly the inherited state this FR set out to surface.
