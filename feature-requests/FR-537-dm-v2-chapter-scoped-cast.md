# Feature Request: FR-537 — DM v2: Chapter-Scoped Cast

**Priority:** HIGH (continuity + prose quality; addresses a measured 10026-BC defect class)
**Type:** Feature
**Status:** Re-judged (2026-06-19, post-FR-536) — scope frozen to roster-only v1 with the
intents-path correction (R2); see Re-judgement. Authority granted.
**Effort:** ~1 day
**Requested:** 2026-06-19

## Summary

A chapter's turn engine is currently fed the **whole-story roster** every turn, narrowed
only by *subtractive* status gates (within-chapter `cast_exits`, turn-1 lifecycle
`confirmed_dead`). There is no **chapter-scoped cast** — no declaration that "Chapter 2 is
Hilde and Gunnar on the ledge." This FR adds a per-chapter `cast` field, authored at outline
time, threaded into the **single existing** allowed-cast computation
(`build_allowed_scene_cast`) as a new first narrowing, so a chapter only **animates** the
characters that chapter is about.

v1 scopes the **intents-map roster only**. Scoping the `STARTING WORLD STATE` ledger render
and re-deriving cast at reoutline time are deferred to follow-up FRs (see Deferred), because
removing off-cast rows from the ledger can delete still-needed reference context (an absent
character's location/status) and needs its own evidence.

## Value Statement

A two-hander chapter stops animating its off-screen cast every turn, removing a measured
source of per-turn looping and flat character differentiation — the reader gets a focused
scene instead of bystanders who "hold the line" on repeat.

## Judgement (2026-06-19)

Conditionally approved; revised to the frozen scope below. Resolutions applied:

- **B1 (blocking) — no parallel cast notion.** An allowed-cast computation already exists:
  [`build_allowed_scene_cast`](../examples/dungeon_master/api/turn_ops.py) computes
  `reviewed_roster − lifecycle_blocked` and is consumed in three places (turn ledger
  ranking, final-cut allowed cast, chapter close). The chapter cast is threaded **into**
  that function as a new first narrowing, making it the single source of "who is in this
  chapter." No new `scope_roster_to_chapter_cast` helper is introduced (avoids the
  `false_duplicate` trap).
- **A1 — roster-only v1.** Ledger-render scoping is deferred: removing off-cast rows from
  `format_world_state` would also delete an absent character's location/status that a
  remaining character may still reference (e.g. grieving the swept-away). Roster scoping is
  the measured win and the safe minimal cut.
- **A2 — beats-as-floor.** The authored cast is unioned with the characters named in the
  chapter's `beats` (deterministic, names already present) so the LLM cannot wrongly omit a
  character the beats require. Authored cast adds; beats floor it.
- **A3 — deterministic test + non-gated witness.** Logic is proven by a unit test on a
  hand-authored fixture; the live-outline cast sanity is a non-gated witness (FR-522
  posture), never CI.
- **Scope reduction.** Steps 3 (ledger render) and 4 (reoutline parity) move to Deferred.

## Re-judgement (2026-06-19, post-FR-536)

The original Judgement above was authored against `turn_ops.py` as a 1169-line god-module.
FR-536 (commit `b822b936`) has since split it into four modules, moving two of this FR's
load-bearing anchors. Re-examined against the code as it now stands.

### R1 — Anchor correction (factual; the FR's inline paths are now stale)

| Symbol | FR cites | Actual home now |
|--------|----------|-----------------|
| `build_allowed_scene_cast` | `turn_ops.py` | `chapter_open.py` (L287) |
| `_filter_roster_for_lifecycle` | `turn_ops.py` (underscore) | `chapter_open.filter_roster_for_lifecycle` (L212, **promoted public**) |
| `chapter_beats` (beats-floor) | `chapter_ops.py` | `turn_state.py` (L180, a leaf) |
| `invoke_turn`, `running_scene`, `_retrieve_turn_ledger` | `turn_ops.py` | `turn_ops.py` (unchanged) |
| `format_world_state` | `world_state.py` | `world_state.py` (unchanged) |
| `expand_chapters` | `doc_ops.py` | `doc_ops.py` (unchanged) |
| `_norm_name` (canonical) | "existing" | `lifecycle_resolver.py` (L36); a second local copy lives in `prose_continuity.py` — use the resolver's |

All enforcement references resolve to the above; the FR's inline snippets are illustrative
and superseded by this table.

### R2 — BLOCKING: the named narrowing point does not reach the measured defect

The original B1 resolution claimed `build_allowed_scene_cast` is "the single source" of
chapter scope and that threading the cast into it makes `invoke_turn`'s intents roster
inherit the scope "for free." **Read against the code, this is false.**
`build_allowed_scene_cast` is consumed in exactly three places — and none of them is the
intents map:

1. `turn_ops._retrieve_turn_ledger` (L68) — ranks *relationships* for the world-state render.
2. `final_cut.invoke_final_cut` (L273) — final-cut allowed cast.
3. `chapter_ops.close_chapter` (L279) — chapter close.

The **intents map** — the roster the turn graph animates every turn, i.e. the measured
defect ("Reinmar and Arnulf hold the line" on repeat) and the target of AC #4 and the Value
Statement — is built **inline** in `invoke_turn` (L178-184) on a *parallel* path that never
calls `build_allowed_scene_cast`:

```python
roster = [cid for cid in chars["roster"] if chars["cards"][cid].get("reviewed")]
roster = filter_roster_for_lifecycle(doc, chars, cid, n, roster)  # exits + turn-1 seam gate
```

Threading the chapter cast into `build_allowed_scene_cast` alone is therefore **necessary
but insufficient**: it scopes ranking/final-cut/close while leaving the animated roster
untouched — the feature would ship without delivering its own value (`composition_bug` /
`plausible_wrong_answer`: every step coherent, the wiring misses the defect).

**Resolution (R2).** Keep the FR's Step 2 cast resolution (authored `cast` ∪ beats-floor,
boundary-normalized) as the **single source of "who is in this chapter"** — one pure helper,
no parallel resolver (honors B1's anti-`false_duplicate` intent). Apply that resolved set as
a chapter-cast intersection at **both** narrowing call sites:

- **(a)** inside `build_allowed_scene_cast` (covers ranking / final-cut / close), and
- **(b)** in `invoke_turn`'s reviewed-roster build, **before** `filter_roster_for_lifecycle`
  (covers the intents map — the defect).

The *resolution* is single-sourced; the *intersection* is applied at the two points that
feed the two distinct roster paths. Empty-cast fallback (Step 4) applies identically at both.

### R3 — Module homes for enforcement (no new cycle)

Place the cast-resolution helper in `chapter_open.py`: it needs `turn_state.chapter_beats`
for the beats-floor (and `chapter_open` already imports `turn_state`), and both call sites
can import it cycle-free — `build_allowed_scene_cast` is *in* `chapter_open`, and `turn_ops`
(home of `invoke_turn`) already imports `chapter_open`. Do **not** add it to `turn_ops` (that
would make `chapter_open` import `turn_ops` → the exact cycle FR-536's leaf split dissolved).
The `cast` field normalization in `expand_chapters` (`doc_ops.py`) imports the canonical
`_norm_name` from `lifecycle_resolver`.

### R4 — Docs target correction

The last AC says "`docs/architecture.md`"; the real file is root **`ARCHITECTURE.md`**, which
now carries a "Module Organization: Concern Seams and Leaf Modules" section (FR-536). Document
chapter-scoped cast there as a **scope** narrowing distinct from the status gates, applied at
both roster paths.

**Verdict: approvable with R2. Scope re-frozen to roster-only v1, with the chapter-cast
intersection applied at BOTH `build_allowed_scene_cast` and `invoke_turn`'s intents-roster
build (single-sourced resolution). Anchors corrected per R1; helper home per R3. Authority
granted.** The original Judgement's A1/A2/A3 (roster-only, beats-as-floor, deterministic test
+ non-gated witness) and the Deferred list stand unchanged.

## Problem

In [turn_ops.py](../examples/dungeon_master/api/turn_ops.py) `invoke_turn`, the cast is the
full reviewed roster:

```python
roster = [cid for cid in chars["roster"] if chars["cards"][cid].get("reviewed")]
roster = _filter_roster_for_lifecycle(doc, chars, cid, n, roster)
```

`chars["roster"]` is **story-level**. The only narrowing is subtractive (exits, lifecycle).
Likewise `running_scene` → `format_world_state` renders **every** `world_state.characters`
row; the only pruning (`_retrieve_turn_ledger` → `rank_relationships`) is top-K on
*relationships*, never on the character list. The chapter card has no `cast` field
(`{title, summary, beats, world_state, seam_packet, chapter_memory, reviewed}`).

Consequences observed in `outputs/dungeon-master/10026-BC/review.md`:

- **Chapter 1** (intent: Hilde + Gunnar stranded): "The four characters (Hilde, Gunnar,
  Reinmar, Arnulf) perform nearly identical actions in a fixed pattern... Reinmar and Arnulf
  hold the line back." Off-stage actors are animated with nothing to do, so they repeat a
  filler action — contributing to the ~8–10× repeated ledge-collapse looping the reviewer
  flagged (coherence/engagement/prose all 2/5).
- The same pattern recurs in Chapters 5, 6, 7 (chant-like repetition, static staging).

This is **presence/scope**, orthogonal to the resurrection/status problem (FR-507/509/510,
and the root-cause notes). Status gates answer "is this character alive enough to act?";
this FR answers "is this character *in this chapter* at all?".

## Proposed Solution (frozen v1 — roster scoping only)

Add a chapter-scoped `cast` to each chapter card and thread it into the single existing
allowed-cast computation.

### 1. Author the cast at outline time (generative, boundary-normalized)

Extend `chapter_outline.yaml` to emit a `cast` array per chapter — the named principals the
chapter portrays — alongside `title`/`summary`/`beats`. The outline LLM already names
characters in beats and summary; it states the focal cast explicitly.

```yaml
# chapter_outline.yaml schema (added field)
chapters:
  - title: "Chapter 2 — A Truce in the Water"
    summary: "..."
    beats: ["...", "..."]
    cast: ["Hilde", "Gunnar"]   # NEW — focal principals for this chapter
```

Normalize at the boundary (`expand_chapters` in
[doc_ops.py](../examples/dungeon_master/api/doc_ops.py)): keep only cast names that match a
roster character (case-insensitive, whitespace-collapsed via the existing `_norm_name`);
drop unknowns with a warning. Store on the card as `cast: list[str]` (display names).

### 2. Resolve the chapter cast with beats-as-floor (deterministic)

The effective chapter cast is the **union** of the authored `cast` and every roster
character named in the chapter's `beats` (the existing beat list; matched by `_norm_name`).
Beats name characters the chapter must portray, so a character the beats require is in the
cast regardless of whether the LLM listed them in `cast`. Authored cast adds; beats floor
it. This is pure code — no free-text name extraction beyond matching against the known
roster (avoids the `regex_fourth_exclusion` trap: we only ever *match* known names, never
parse arbitrary structure).

### 3. Thread the chapter cast into `build_allowed_scene_cast` (single source)

[`build_allowed_scene_cast(doc, cid)`](../examples/dungeon_master/api/turn_ops.py) today
computes `reviewed_roster − lifecycle_blocked`. Add the chapter cast as a **new first
narrowing**, so the one function every consumer already calls becomes the single source of
chapter scope:

```
allowed = reviewed_roster
        ∩ chapter_cast            # NEW (cast ∪ beats-floor); identity when empty
        − lifecycle_blocked
```

`invoke_turn`'s intents roster is then `allowed − within_chapter_exits` via the existing
`_filter_roster_for_lifecycle`. Because ledger ranking, final-cut, and chapter close already
read `build_allowed_scene_cast`, they inherit the chapter scope for free — which is the
desired behavior (a chapter's close and final-cut should reason over the chapter's cast).
The ledger *render* in `running_scene` is **not** changed in v1 (see Deferred): off-cast
characters stay visible as reference context but are no longer animated.

### 4. Non-empty fallback (match existing guards)

If a chapter's resolved cast is empty (no `cast`, no beat-named roster member, or every
member lifecycle-filtered), `build_allowed_scene_cast` **falls back to its current result**
(full reviewed roster minus lifecycle) — exactly the posture of `_drop_within_chapter_exits`
and `_filter_roster_for_lifecycle` (never hand the turn an empty cast; the chapter turn cap
closes a degenerate chapter). This keeps the feature strictly additive: a story.json without
`cast` fields reproduces today's behavior.

## Acceptance Criteria

- [x] `chapter_outline.yaml` emits `cast: list[str]` per chapter; `expand_chapters` stores a
      roster-normalized `cast` on each card (unknown names dropped, logged).
- [x] Cast resolution unions the authored `cast` with beat-named roster characters
      (beats-as-floor); both matched via `_norm_name`.
- [x] A single cast-resolution helper (Step 2: authored `cast` ∪ beats-floor, normalized)
      lives in `chapter_open.py`; no parallel resolver (R2).
- [x] `build_allowed_scene_cast` applies the chapter cast as a first narrowing
      (`reviewed ∩ chapter_cast − lifecycle`), scoping ranking / final-cut / close.
- [x] **`invoke_turn`'s reviewed-roster build intersects the resolved chapter cast BEFORE
      `filter_roster_for_lifecycle`** (R2 — the intents map is on a parallel path that does
      not call `build_allowed_scene_cast`); off-stage actors are not animated. A test asserts
      the intents roster (not just `build_allowed_scene_cast`) is chapter-scoped.
- [x] Empty resolved cast falls back to the current `build_allowed_scene_cast` result; a
      `cast`-less story.json reproduces today's behavior (regression test).
- [x] **Unit test (gating):** a hand-authored fixture chapter with `cast: ["Hilde",
      "Gunnar"]` and beats naming only those two resolves its allowed cast to
      `{Hilde, Gunnar}` (not the full roster); a fixture whose beats name a third character
      includes that third via the beats-floor; an empty-cast fixture falls back to the full
      roster.
- [ ] **Witness (non-gating, FR-522 posture):** a by-hand check that a live outline run emits
      a sane per-chapter `cast`; never wired into CI.
- [x] Tests added (outline schema parse, boundary normalization, beats-floor union,
      `build_allowed_scene_cast` narrowing, empty-cast fallback).
- [x] `ARCHITECTURE.md` ("Module Organization" section, R4) updated to document chapter-scoped
      cast as a **scope** narrowing distinct from the status gates, applied at both roster
      paths (`build_allowed_scene_cast` and the `invoke_turn` intents build).

## Deferred (follow-up FRs)

- **Ledger-render scoping.** Filtering `world_state.characters` in `running_scene` to the
  chapter cast. Deferred (A1): removing an off-cast row also removes that character's
  location/status, which a remaining character may still need to reference (grief, rumor,
  pursuit). Needs its own evidence that scene focus outweighs lost reference context.
- **Reoutline cast re-derivation (FR-523 parity).** Re-deriving `cast` from prior
  world_state at reoutline time (drop an exited character, add a planned returner at their
  floor). Deferred: with beats-as-floor, the frozen outline cast + beat floor is sufficient
  for v1; reoutline parity lands once the base is proven.

## Alternatives Considered

- **Derive cast *solely* from beats' named characters** (no schema change, no authored
  field): pure code, but a character present-but-unnamed-in-a-beat (a silent witness) would
  be wrongly excluded, and treating beats as the *only* source invites parsing free-text for
  structure. Rejected as the *sole* source — but adopted as a **floor**: beats-named roster
  characters are unioned into the authored cast (A2), so the LLM cannot omit a beat-required
  character. We only ever *match* known roster names, never parse arbitrary structure
  (sidesteps `regex_fourth_exclusion`).
- **Introduce a new `scope_roster_to_chapter_cast` helper** (the original plan): rejected
  (B1) — `build_allowed_scene_cast` already computes a per-chapter allowed cast consumed in
  three places; a parallel helper would drift (`false_duplicate`). The chapter cast is
  threaded into the existing function as a first narrowing instead.
- **Keep subtractive-only and lean on the director's `cast_exits`**: already in place and
  insufficient — it removes someone *after* they've been animated into the scene, so the
  first turns still animate the full roster. Scope must be set *before* the intents map, not
  recovered after.
- **Also scope the ledger render in v1**: deferred (A1) — removing an off-cast character's
  row deletes their location/status, which a remaining character may still reference (grief,
  rumor, pursuit). Roster scoping alone is the measured win; ledger-render scoping needs its
  own evidence. Off-cast characters stay visible as reference context, just not animated.

## Related

- [turn_ops.py](../examples/dungeon_master/api/turn_ops.py) — `build_allowed_scene_cast`
  (the single narrowing point), `invoke_turn`, `_filter_roster_for_lifecycle`,
  `running_scene` (unchanged in v1; deferred ledger-render scoping)
- [world_state.py](../examples/dungeon_master/api/world_state.py) — `format_world_state`
  (deferred ledger-render scoping)
- [doc_ops.py](../examples/dungeon_master/api/doc_ops.py) — `expand_chapters` (cast boundary
  normalization)
- [chapter_ops.py](../examples/dungeon_master/api/chapter_ops.py) — `chapter_beats` (the
  beats-as-floor source), and the final-cut/close consumers of `build_allowed_scene_cast`
  that inherit chapter scope
- `examples/dungeon_master/prompts/chapter_outline.yaml` (cast field),
  `examples/dungeon_master/prompts/chapter_reoutline.yaml` (deferred reoutline parity)
- `outputs/dungeon-master/10026-BC/review.md` — the looping/flat-cast evidence
- Distinct from (orthogonal to) the resurrection/status work: FR-507, FR-509, FR-510,
  FR-526, and the chapter-seam resurrection root-cause notes.

## Implementation (2026-06-19, enforced)

**Status:** Implemented. RED `dbf182e7`, GREEN to follow. DM suite 307 passed; ruff,
import-linter (1 kept / 0 broken), vulture clean.

### What was built

1. **Single resolution leaf — `chapter_open.resolve_chapter_cast(doc, cid) -> set[str]`.**
   Unions the authored `cast` (restricted to the roster) with the **beats-floor** — roster
   characters word-named in the chapter's authored beats. Word-bounded token matching
   (`_name_tokens` + `_contains_token_run`), so a roster name matches only as whole words
   (`Ron` does not match inside `around`); we only ever *match* known roster names, never
   parse free-text structure (sidesteps `regex_fourth_exclusion`).
2. **Two narrowing sites, both single-sourced through the leaf.**
   - `_scope_names_to_chapter_cast` narrows the prose-control cast inside
     `build_allowed_scene_cast` (covers ranking / final-cut / close).
   - `scope_roster_to_chapter_cast` narrows the **per-turn intents roster** in
     `turn_ops.invoke_turn`, applied *before* `filter_roster_for_lifecycle`.
3. **Boundary normalization — `doc_ops._normalize_chapter_cast`.** `expand_chapters` stores a
   roster-normalized `cast` per card: authored names matched case-insensitively to the
   roster's canonical display name, unknowns dropped with a `logging.warning` (`the_one_law`).
4. **Outline schema.** `outline_ops._cast_list` parses the field; `outline_chapters` includes
   `cast` in each chapter dict. `chapter_outline.yaml` prompt asks for the focal cast.
5. **Empty-cast fallback at both sites:** an empty resolved cast returns the prior result, so
   a `cast`-less story.json reproduces today's behavior (additive feature; regression test).

### Deviations from the original plan (resolved by the Re-judgement)

- **A `scope_roster_to_chapter_cast` helper WAS introduced** — the "Alternatives Considered"
  rejection of a parallel helper was itself overturned by R2. Threading the cast only into
  `build_allowed_scene_cast` would have left the measured defect untouched: the intents roster
  is built inline in `invoke_turn` and never calls `build_allowed_scene_cast`. The resolution
  is single-sourced (`resolve_chapter_cast`); only the tiny intersection-with-fallback is
  applied at each site — not a duplicate resolver (`false_duplicate` avoided).
- **Beats-floor source is `turn_state.chapter_beat_list`, not `chapter_ops.chapter_beats`.**
  The FR's "Related" line cited the wrong accessor: `chapter_beats` is the *satisfied* beat
  accumulator (empty at turn 1), while `chapter_beat_list` returns the authored beats present
  from turn 1 — the correct floor for a turn-1 cast scope.
