# Feature Request: DM v2 Typed `StoryDoc` Contract + Sole Accessor (Contract A — the keystone)

**Priority:** HIGH (the largest structural debt in v2; unblocks Contracts B and C)
**Type:** Enhancement (refactor — additive, behavior-preserving)
**Status:** Enforced (2026-06-21) -- StoryDoc type + sole accessor (getter `chapter_turns` + setter `write_chapter_card`) + instruments cluster migrated; 407 DM tests pass, 42/42 live books validate. (J1 evidence corrected against live code 2026-06-21; J2 parse-once + J4 first-class setter folded into Solution/AC)
**Effort:** ~1 day for the type + accessor; the call-site migration is a series of small follow-up FRs
**Requested:** 2026-06-21

> Reference: [`docs/refactoring-plan.md`](../examples/dungeon_master/docs/refactoring-plan.md) §3 Contract A.

## Summary

The per-session story document is an **untyped `dict`** whose shape
(`doc["chapters"]["cards"][cid]["turns"][n]["recap"]["text"]`) is re-derived inline in
**14 of 32** `api/` modules (~29 raw reach-in sites). An accessor module
([`chapter_nav.py`](../examples/dungeon_master/api/chapter_nav.py)) already exists and is
imported by **10** modules — but it is **not the sole accessor**: 6 of those importers still
mix its typed getters with raw `doc[...]` reach-ins for other reads, and there is **no typed
setter at all**. This FR defines a typed `StoryDoc` contract and makes `chapter_nav` the
**sole** accessor — every structural read through a typed getter, every structural write
through a typed setter — so the doc shape is defined and validated once at its boundary
instead of re-derived across 14 modules.

## Value Statement

A maintainer renaming or extending a doc field changes **one** definition instead of
grepping 21 modules; and every chapter-card write funnels through a single typed setter —
the structural seam where the gate battery (Contract C / FR-555) can be bound by
construction.

## Problem

The two typed islands in v2 — `world_state.py` (imported by 9 modules) and `seam_packet.py`
(7) — are exactly where continuity is *strong*. The `doc` that carries them is untyped, and
that is exactly where regressions persist:

- **14 modules** reach into the raw doc shape directly (~29 sites; `tree` 4, `chapter_ops`
  4, `witness_metrics` 3, `gap_detectors` 3, `prompt_salience` 2, `outline_ops` 2 …).
- `chapter_nav` is **partially adopted, not bypassed**: 10 modules import it, but 6 of those
  still mix its getters with raw `doc[...]` reads, so the implicit schema drifts. Critically,
  there is **no typed setter** — so a malformed card has no boundary to be caught at, which
  is exactly why the FR-555 second-authoring-boundary class can write an uncaught reversal.

This is `the_one_law` applied unevenly: the contract is typed for relationships and seams,
implicit for the document that holds them.

## Proposed Solution

1. **Define `StoryDoc`** — a Pydantic model covering only what the reach-in sites actually
   read: `tagline`, `stage`, `synopsis`, `characters`
   (`roster`, `cards`), `chapters` (`order`, `cards[cid]`: `title`, `summary`, `beats`,
   `entry_state`, `exit_state`, `turns[n]`: `recap`, `intents`, `direction`, `world_state`,
   `seam_packet`, `reviewed`). Reuse the existing typed `world_state` / `seam_packet` shapes
   as nested members — do **not** re-type them. **Parse ONCE at the boundary** (load / first
   build), keep the in-memory representation a plain dict read through typed accessors — exactly
   as `world_state`/`seam_packet` are parsed at their boundary and then read as typed views.
   **No getter calls a validator** (J2: re-parsing per read would change behavior — raise
   mid-run on a doc that today degrades — and cost the per-turn hot path).
2. **Make `chapter_nav` the sole accessor** — typed getters (`chapter_card`, `chapter_turns`,
   `turn_record`, `inherited_world_state`, `inherited_seam_packet`, …) and, as a
   **first-class, separately-tested deliverable**, a typed structural **setter**
   (`write_chapter_card` / `write_turn_result`) that **rejects a structurally-invalid card**
   (J4 — the setter is the seam Contract C / FR-555 binds gates to; it is new, unlike the
   partly-adopted getters). Re-export the helpers the other modules currently inline.
3. **Migrate reach-in sites cluster by cluster**, each its own follow-up FR/commit:
   **instruments first** (component ⑥ — `witness_metrics`, `prose_continuity`, `cue_metrics`,
   `fact_reversal`, `prompt_salience`; read-only, safest), then planning/finish, then the
   adapter.

```python
# Before (duplicated in 21 modules)
text = doc["chapters"]["cards"][cid]["turns"][str(n)].get("recap", {}).get("text", "")

# After (one typed accessor)
text = chapter_nav.turn_recap_text(doc, cid, n)
```

## Acceptance Criteria

- [ ] `StoryDoc` type defined, covering exactly the fields the current reach-in sites read
      (no speculative fields — Scripture *purge*).
- [ ] A characterization test asserts a live generated `story.json` validates against
      `StoryDoc` (boundary parse, no behavior change). **Parse happens once at the boundary;**
      no getter re-validates (J2).
- [ ] `chapter_nav` exposes typed getters AND a typed structural **setter** that rejects a
      structurally-invalid card (J4 — separately tested), and is the documented sole accessor.
- [ ] **Instruments cluster (⑥) migrated** to the accessor in this FR; remaining clusters
      tracked as named follow-up FRs.
- [ ] DM suite green; no behavior change in migrated modules (characterization-tested).
- [ ] `docs/architecture.md` module map updated to name `chapter_nav` as the accessor;
      `docs/refactoring-plan.md` Contract A marked in-progress.

## Alternatives Considered

- **Big-bang migration of all 21 modules** — rejected; high blast radius, hard to review.
  Incremental cluster migration keeps each commit behavior-preserving and revertible.
- **`TypedDict` only, no runtime validation** — viable, but a Pydantic boundary parse buys
  the same drop-malformed guard that made `world_state`/`seam_packet` strong; chosen for
  parity with the existing typed islands.
- **Leave the doc untyped, fix shape bugs as they appear** — rejected; that is the status
  quo that produced FR-555.

## Related

- [`docs/refactoring-plan.md`](../examples/dungeon_master/docs/refactoring-plan.md) §3 Contract A (keystone)
- [`api/chapter_nav.py`](../examples/dungeon_master/api/chapter_nav.py) — the accessor to elevate
- FR-499/513–518 (`world_state` typed ledger — the model to copy)
- FR-506/507 (`seam_packet` typed seam — the model to copy)
- FR-555 (Contract C minimal; the setter funnel this FR enables)

## Judgement (2026-06-21)

**Verdict: APPROVE WITH CONDITIONS.** The *problem* is real and is the right keystone: the story doc
is an untyped dict, the two typed islands (`world_state`, `seam_packet`) are exactly where continuity
is strong, and there is no typed **setter** — which is precisely why FR-555's second authoring
boundary can write a malformed card uncaught. That structural argument stands. **But the headline
evidence is false as written, and a keystone may not rest on a false number (J1, blocking).**

**J1 — BLOCKING. Correct the central evidence; it is contradicted by the live code.** The FR (and
`refactoring-plan.md` §1/§2) states `chapter_nav` is *"imported by **one** module; everyone else
bypasses it."* Grep of `examples/dungeon_master/api/` shows **`chapter_nav` is imported by at least 10
modules** — `turn_ops`, `turn_state`, `seam_entrance`, `prose_continuity`, `lifecycle_resolver`,
`chapter_open`, `cast_entrances`, `outline_ops`, `gap_detectors`, `final_cut` (plus tests). The
accessor is **not** bypassed-by-all-but-one; it is *partially adopted*. The true, defensible problem
is weaker but still sufficient: **`chapter_nav` is not the SOLE accessor — modules call its typed
getters for some reads while still reaching into the raw `doc[...]` shape for others, and there is no
typed setter at all.** Rewrite the Problem section to that claim. Likewise **re-derive the "21 of 33
modules" / "80+ duplications" counts before citing them**: a spot check shows many raw `["cards"]`
hits are `chars["cards"]` (the character roster, a *different* structure) and several chapter reads
already route through `chapter_nav`/`turn_state`. An inflated count cannot justify a HIGH-priority
keystone — `quick_confidence` / `judge_as_junior_pr`: verify the number, then let it carry the weight.

**J2 — BLOCKING (design). Validate ONCE at the boundary, never on every getter.** The FR offers
"Pydantic model **or** `TypedDict` + validator." These are not interchangeable here. A Pydantic
`StoryDoc` whose getters re-parse on every read would (a) change behavior — raising mid-run on a doc
that today degrades gracefully — and (b) cost real time in the per-turn hot path the instruments
walk. Pin the contract: **parse once where the doc enters (load / first build), keep the in-memory
representation a plain dict behind typed *accessor functions*** (the `chapter_nav` getters), exactly
as `world_state`/`seam_packet` are parsed at their boundary and then read as typed views. The getter
layer gives the type safety; the boundary parse gives the drop-malformed guard. No getter calls a
validator.

**J3 — non-blocking. Freeze scope to type + accessor + instruments (⑥) only; it already does — hold
the line.** The keystone's value is unblocking B/C, not migrating 21 modules. Enforce ships: the
`StoryDoc` type, a characterization test that a live `story.json` validates, the `chapter_nav` getter/
setter surface, and the **read-only instruments cluster** migrated (safest, behavior-preserving).
Every other cluster is a named follow-up FR. Resist migrating planning/adapter in this FR.

**J4 — non-blocking. The setter is the actual keystone deliverable; make it explicit.** B and C both
hinge on "every structural write funnels through one typed setter." The getters are the easy, already-
partly-done half; the **setter** (`write_chapter_card` / `write_turn_result`) is what Contract C binds
gates to and is new. The AC lists "typed getters/setters" in passing — promote the setter to a
first-class, separately-tested deliverable (a write that rejects a structurally-invalid card), because
that is the seam the whole program is for.

**Conditional authority.** J1 and J2 must be folded into the FR text **before** enforce (the evidence
and the parse-once contract change what gets built). With those corrected, scope is frozen to J3 and
the setter (J4) is first-class. Sequencing: A is the keystone but B (FR-557) is independent and can
proceed in parallel; C (FR-558) waits on FR-555 regardless.

**Resolution (2026-06-21).** Conditions folded; status promoted to enforce-ready:
- **J1 corrected against live grep** of `examples/dungeon_master/api/` (32 modules): `chapter_nav`
  imported by **10** modules (not 1); **14** modules reach into the raw `doc["chapters"]...` shape
  (~29 sites, not "21 of 33 / 80+"); 6 modules mix both (partial adoption). Summary + Problem rewritten;
  same false claim fixed in `refactoring-plan.md` §1/§2.
- **J2 folded** into Solution #1 + AC: parse once at the boundary, no getter re-validates.
- **J4 folded** into Solution #2 + AC: the typed setter is now a first-class, separately-tested
  deliverable that rejects a structurally-invalid card.
- **J3** scope (type + accessor + setter + instruments ⑥) already held.

## Enforcement (2026-06-21)

RED (`test(examples): FR-556 condemn untyped story-doc boundary`,
`examples/dungeon_master/tests/test_story_doc_contract.py`): a representative real-shaped book must
validate via `story_doc.parse`; the typed setter `chapter_nav.write_chapter_card` must persist a
well-formed card AND reject a structurally-invalid one (`beats` a string) -- none of `StoryDoc`,
`parse`, `InvalidChapterCard`, `write_chapter_card`, `chapter_turns` existed.

GREEN:
- **Type + boundary (`story_doc.py`).** Added permissive Pydantic `ChapterCard` / `Chapters` /
  `StoryDoc` (`extra="allow"`, all fields optional with defaults) typing only the structural spine
  the reach-in sites read; `parse(doc) -> StoryDoc` and `validate_chapter_card(card) -> ChapterCard`
  (raising `InvalidChapterCard`). `world_state`/`seam_packet`/`text` are deliberately NOT typed
  (legacy `world_state` is the `""` placeholder on a fresh card and a ledger dict on a closed one).
- **Sole accessor (`chapter_nav.py`).** Added the `chapter_turns` getter and the `write_chapter_card`
  setter (validate-then-commit). The setter imports `story_doc` only (leaf -> leaf), so `chapter_nav`
  stays acyclic; its docstring softened from "imports nothing from api" to "near-leaf, imports only
  story_doc."
- **Boundary-at-write decision (J2).** The parse is bound to WRITES (the setter), not reads. Wiring
  validation into `story_doc.read` would raise mid-run on legacy/partial books that degrade today;
  reads stay plain-dict. Documented here as the enforce interpretation of "parse once at the boundary."
- **Instruments cluster ⑥ migrated.** `witness_metrics` (`parse_story_progress_metrics`,
  `chapter_actor_flag_metrics`, `book_turn_waste`), `prose_continuity.build_source_pointer` (now
  `chapter_nav.previous_chapter_id`), and `prompt_salience` (both reach-in sites) read through the
  accessor. `turn_state.chapter_turns` delegates to `chapter_nav.chapter_turns`.
- **Funnel.** `doc_ops.expand_chapters` writes each card via `chapter_nav.write_chapter_card` -- the
  one validated write seam FR-558 binds the gate battery to.

Verification: `examples/dungeon_master/tests/` 407 passed (404 + 3 new contract tests); a one-off
validated **42/42** live `outputs/dungeon-master/*/story.json` against `StoryDoc` (outputs/ is
gitignored, so the committed characterization test uses a representative inline doc). DM is not under
import-linter; the new `chapter_nav -> story_doc` and `doc_ops -> chapter_nav` edges are leaf-safe.
