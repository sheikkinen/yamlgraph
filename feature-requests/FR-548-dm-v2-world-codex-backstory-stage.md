# Feature Request: DM v2 World Codex — Faction & Location Backstory Stage

**Priority:** MEDIUM (length + grounding elaboration; lowest continuity-cost vector)
**Type:** Feature
**Status:** Enforced (RED 7aeba5c0 -> GREEN 5334a7f5) — 5 deterministic tests; 390 DM tests green; world_codex.yaml lints clean
**Effort:** ~1.5 days
**Requested:** 2026-06-20

## Summary

Add an outline-time **World Codex** stage — a side-effect graph (parallel to `character_roster`,
FR-475) that derives **faction** and **location** backstory from the accepted synopsis and
persists it as immutable reference state on the doc. The codex is woven by `final_cut` as
grounding texture and read by the turn director as setting context, so the book gains depth and
length **without adding cross-seam continuity load** — backstory is additive (it states a world,
it does not reverse one).

## Value Statement

The book lengthens from short-story (~6,250 words) toward novelette (7,500+) by adding *grounding*
the generator currently invents ad hoc, and a documented faction/allegiance history gives the
turn director a stated prior to honor — which *reduces* the silent allegiance flips the FR-545
witness measures, rather than adding to them.

## Problem

Length in this system is the product of structural knobs, not a verbosity dial:
`book ≈ chapters × beats/chapter × words/beat`. The `final_cut` stage is deliberately a
**compressor** ([final_cut.yaml](examples/dungeon_master/prompts/final_cut.yaml): "STATE EACH
STANDING FACT ONCE… one prose passage per beat") — so asking the narrator for "more words"
fights the architecture (it de-duplicates them back out). To elaborate the book you must widen
the funnel's *inputs*, not inflate its *output*.

Four elaboration vectors exist; this FR is the highest-leverage, lowest-risk one:

| Vector | Length gain | Continuity cost | Fit |
|--------|-------------|-----------------|-----|
| Prose embellishment | low (compressed away) | none | ❌ fights final_cut |
| **Faction/location backstory** | **high** | **~zero (additive)** | ✅ this FR |
| Deeper dialogue | medium | moderate | ✅ later |
| More plot twists | high | **high** (every twist is a seam reversal) | ⚠️ gated on witnesses |

The generator currently has **no world-grounding stage**. `character.yaml` drafts per-character
*origin sheets*, but nothing authors **faction** identity (the Aschenwulf vs Bärenschädel clan
politics that drive every floodmark-saga book) or **location** lore (the flood zone, the ledge,
the salt road, the high valley). These are invented inconsistently per chapter at 0.7 temperature
— the same gap that produces non-roster collective-entrance breaks (clan members appearing
unbridged) and the locative collisions that confused the fact-reversal witness (FR-547, "flood
zone"). Backstory authored once, up front, and carried as immutable reference closes that gap.

Empirically, the twist-dense books score worst on continuity (10031-BC: 8 breaks, 1/5) and the
calm, well-grounded book scores best (10032-BC: 0 breaks, 5/5). Backstory adds the *calm* kind of
length: world texture, not new reversible events.

## Proposed Solution

> **Amended per Judgement C1–C5 (2026-06-20).** The original draft proposed an inline
> `schema: WorldCodex` with `type: list[object]` + nested `fields:`. That path does **not** load
> ([`schema_loader.resolve_type`](../yamlgraph/schema_loader.py#L83) has no `object` in `TYPE_MAP`
> and [`build_pydantic_model`](../yamlgraph/schema_loader.py#L110) never recurses into nested
> `fields:`). The mechanism below replaces it with the verified `parse_json: true` + boundary-
> normalize pattern that every nested-output DM graph already uses
> ([chapter_outline.yaml](../examples/dungeon_master/chapter_outline.yaml) +
> `outline_ops.outline_chapters`). The superseded inline-schema draft is preserved in the
> Judgement section as the condemned premise.

A new side-effect graph `examples/dungeon_master/world_codex.yaml` + prompt
`prompts/world_codex.yaml`, and a `doc_ops.expand_codex(doc, story_dir)` boundary that persists the
result. **Trigger-site precedent** (a synopsis-fed, non-visitable side-effect graph): mirrors
`character_roster.yaml`. **Output-shape precedent** (nested structured JSON): mirrors
`chapter_outline.yaml` — `parse_json: true` with the contract written into the prompt and validation/
normalization at the Python boundary, **not** an inline schema (C1, C2).

**Graph:** synopsis → LLM (`parse_json: true`) → a `{factions: [...], locations: [...]}` JSON object.
The shape is specified in the prompt contract (as `chapter_outline.yaml` specifies `{chapters:
[{title, summary, ...}]}`), not in a `schema:` block:

```text
# prompts/world_codex.yaml — JSON contract (in the prompt body, parse_json: true)
{
  "factions": [
    {"name": "...",
     "identity": "who they are, what they value (2-3 sentences)",
     "history": "how they came to be, their grievance/stake",
     "stance": "their position as the story opens"}
  ],
  "locations": [
    {"name": "...",
     "description": "physical character, sensory texture (2-3 sentences)",
     "significance": "why it matters to the conflict"}
  ]
}
```

`doc_ops.expand_codex` normalizes the parsed object at the boundary (coerce to lists, drop unknown
keys, default missing string fields to `""`) before persisting — the same boundary discipline
`outline_ops.outline_chapters` applies to chapter chunks.

**Persistence (doc shape, additive — no existing key changes; immutable reference, no `reviewed`
gate per C3):**

```json
"codex": {
  "factions": [{"name": "...", "identity": "...", "history": "...", "stance": "..."}],
  "locations": [{"name": "...", "description": "...", "significance": "..."}]
}
```

Like `characters.cards[].text`, the codex is authored once and carries no per-stage review flag —
it is non-visitable immutable reference, so a `reviewed` field would be unreachable dead state.

**Sequencing (C4):** the codex reads only the accepted synopsis, so author it in the
`stage.name == "synopsis"` branch of [session.weave](../examples/dungeon_master/api/session.py#L287)
immediately after `expand_roster` (both consume the same accepted synopsis):
`expand_roster` → **`expand_codex`** on synopsis-accept. `expand_chapters` is unchanged — it remains
on its own `cast_complete` branch (the two expansions fire on different accept events, not adjacent
calls). Mirror the same synopsis-accept insertion in `scripts/generate.py`.

**Consumption (additive prompt blocks, `{% if %}`-guarded so absence is byte-identical):**
- `final_cut.yaml` user template: a `WORLD CODEX` reference block (faction/location entries
  relevant to the chapter cast) — woven as texture, governed by the existing "compose, do not
  invent" rule so it grounds rather than spawns events.
- `chapter_outline.yaml`: codex available so chapter summaries name real factions/locations.
- (Optional, follow-up) turn director context: faction `stance` as a relational prior feeding
  the FR-545 allegiance rail.

The codex is **immutable reference** (like `characters.cards[].text`): authored once, never
mutated by chapter close, so it adds **zero** cross-seam reversible state.

## Acceptance Criteria

- [ ] **(deterministic RED, the real gate)** committed separately, `SKIP=pytest`: `expand_codex` on
      a doc with an accepted synopsis persists a `codex` block (no `reviewed` key) with ≥1 faction
      and ≥1 location; a malformed/partial LLM object is normalized at the boundary (missing string
      fields default to `""`, non-list `factions`/`locations` coerced, unknown keys dropped); and
      first-run absence of `codex` leaves the doc byte-identical through `final_cut` (the guarded-
      block invariant).
- [ ] `world_codex.yaml` graph (`parse_json: true`, **no inline `schema:` block**) + `world_codex`
      prompt carrying the `{factions, locations}` JSON contract; lints clean (`yamlgraph graph lint`).
- [ ] `doc_ops.expand_codex(doc, story_dir)` boundary normalizes the parsed object, sequenced on
      **synopsis-accept after `expand_roster`** in `session.weave` and `scripts/generate.py` (not
      between roster and chapter expansion — those fire on different accept events).
- [ ] `final_cut.yaml` + `final_cut.py` thread a `world_codex` context var through
      `FINAL_CUT_GRAPH`; the block is `{% if %}`-guarded so absence is byte-identical.
- [ ] **(visibility evidence, NOT a blocking test — C5)** `demo-output.log` records a fresh book's
      added prose words and continuity score vs the 10032-BC baseline, documenting the additive
      claim. The length/continuity numbers are LLM-nondeterministic and do not gate CI.
- [ ] Example-exempt: NO `@pytest.mark.req`, NO capability YAML; changelog fragment
      `type: feat`, `scope: examples`, no `req:`.
- [ ] Distill diary entry.
- [ ] New modules/prompts stay under the 450-line ceiling.

## Alternatives Considered

- **Prose embellishment in final_cut**: rejected — final_cut's de-duplication rule compresses it
  away; inflates `prose` axis risk without adding story.
- **Fold faction/location into `character.yaml` origin sheets**: rejected — factions and locations
  are not characters; conflating them bloats the character stage and gives no shared reference the
  outline and turns can read (`false_duplicate`).
- **Mutable codex (factions evolve per chapter)**: rejected for v1 — that reintroduces exactly the
  cross-seam reversible state the additive design avoids; faction *stance* evolution belongs to the
  relationship ledger (FR-513/545), not the codex. Keep the codex immutable reference.
- **More plot twists instead**: higher engagement but highest continuity cost; deferred until the
  allegiance (FR-545) and fact-reversal (FR-547) witnesses are gating, not visibility-only.

## Related

- `examples/dungeon_master/character_roster.yaml` — the side-effect-graph pattern to mirror
- `examples/dungeon_master/api/doc_ops.py` — `expand_roster`, `expand_chapters` (sequence point)
- `examples/dungeon_master/api/session.py` — `weave` (L212), expansion sequencing (L288–290)
- `examples/dungeon_master/prompts/final_cut.yaml` — the compressor; codex woven here as texture
- `feature-requests/FR-545-dm-v2-identity-allegiance-reset-witness.md` — faction stance as allegiance prior
- `feature-requests/FR-547-dm-v2-fact-reversal-subject-binding.md` — locative grounding the codex names
- Evidence: 10031-BC (8 breaks, twist-dense) vs 10032-BC (0 breaks, grounded) — backstory adds the calm kind of length

## Judgement (2026-06-20) — APPROVE WITH CONDITIONS; C1 blocking, requires FR amendment before enforce

The value thesis is sound and well-argued: length comes from widening the funnel's *inputs*,
not inflating `final_cut`'s output (verified — [final_cut.yaml](examples/dungeon_master/final_cut.yaml)
is `parse_json: false` and the prompt is a de-duplicating compressor). The additive/immutable design
is the right shape: backstory states a world, it does not reverse one, so it adds zero cross-seam
reversible state. But the **mechanism as specified will not run**, and three claims are falsified by
the live code. These are mechanical to fix in the spec (`spec_kill` — the cheapest bug is the one
killed before a test is written), so this is a conditional approval, not a rejection of the idea.

**Verified defects (measured against the code, not the prose):**

1. **(C1 — blocking) The inline `WorldCodex` schema cannot load.**
   [`schema_loader.resolve_type`](yamlgraph/schema_loader.py#L83) matches `list[(\w+)]` and resolves
   the inner token through `TYPE_MAP`, which contains only `str/int/float/bool/dict/Any` — there is
   **no `object`**. `type: list[object]` raises `ValueError: Unknown type: 'object'`. Worse,
   [`build_pydantic_model`](yamlgraph/schema_loader.py#L110) reads only `field_def["type"]` and
   **never recurses into nested `fields:`** — the nested faction/location field specs would be
   silently ignored even if `object` resolved. The inline-schema path does not support nested object
   lists at all.

2. **(C2) "Mirrors `character_roster`" is false.**
   [character_roster.yaml](examples/dungeon_master/character_roster.yaml#L31) is `parse_json: false`
   + `split_roster(raw)` — a plain names-only string, then per-name drafting by `character.yaml`. It
   has no schema. Every DM graph that emits a *nested structure* uses `parse_json: true` with the JSON
   contract written into the prompt and normalization at the Python boundary —
   [chapter_outline.yaml](examples/dungeon_master/chapter_outline.yaml#L38) (`{chapters:[{title,
   summary}]}` via `outline_ops.outline_chapters`), [chapter_close.yaml](examples/dungeon_master/chapter_close.yaml#L52),
   [turn.yaml](examples/dungeon_master/turn.yaml#L55). The real structural sibling is
   `chapter_outline.yaml`, not `character_roster.yaml`.

3. **(C4) The sequence point does not exist as described.**
   [session.weave](examples/dungeon_master/api/session.py#L287-L290): `expand_roster` fires in the
   `stage.name == "synopsis"` branch; `expand_chapters` fires in the separate `CHAR_PREFIX … cast_complete`
   branch. They are two `if/elif` arms triggered by **different accept events**, not adjacent calls —
   there is no single "between" location to insert `expand_codex`.

4. **(C3) `reviewed: false` is dead state.** The FR calls the codex graph "non-visitable" and the codex
   "immutable reference," yet the doc shape carries `"reviewed": false`. Roster/chapter cards have
   `reviewed` because they are human-visitable stages with a review gate that flips it true. A
   non-visitable immutable codex has nothing to flip it — the field is unreachable state.

**Conditions (amend the FR's Proposed Solution + Acceptance Criteria, then enforce; no re-judge if met):**

- **C1 (blocking):** Replace the inline `schema: WorldCodex` (`list[object]`) with `parse_json: true`
  + an explicit `{factions:[...], locations:[...]}` JSON contract written into
  `prompts/world_codex.yaml`, validated/normalized at the `doc_ops.expand_codex` boundary — exactly
  how `chapter_outline.yaml` + `outline_ops.outline_chapters` already produce nested output. No inline
  schema. (Do **not** instead extend the schema loader to support nested objects — that is a separate
  framework FR with its own REQ/CAP/tests, out of scope for an example feature.)
- **C2:** Correct the "mirrors `character_roster`" framing throughout to "mirrors the `parse_json: true`
  + boundary-normalize pattern of `chapter_outline.yaml`." `character_roster` is the *trigger-site*
  precedent (a synopsis-fed side-effect graph), not the *output-shape* precedent.
- **C3:** Drop `reviewed` from the codex doc shape (immutable reference, like `characters.cards[].text`
  which carries no per-stage gate once drafted). If a review surface is actually wanted, that is a
  visitable stage — restate scope and re-estimate; do not smuggle it via a dead flag.
- **C4:** Name the concrete trigger. The codex reads only the synopsis, so author it in the
  `stage.name == "synopsis"` branch immediately after `expand_roster` (both consume the same accepted
  synopsis). State `expand_roster → expand_codex` on synopsis-accept; `expand_chapters` remains on its
  own cast-complete event.
- **C5:** Re-frame the length/continuity AC as a **demo-log measurement, not a blocking test**. "≥1,500
  added words, continuity not regressed" is LLM-nondeterministic and cannot gate CI. The deterministic
  RED (the real gate) is the one already listed: `expand_codex` persists ≥1 faction + ≥1 location, and
  first-run absence leaves the doc byte-identical through `final_cut` (the guarded-block invariant).
  Capture the length/continuity numbers in `demo-output.log` as visibility evidence of the additive
  claim.

**Note on the additive-continuity premise.** "A stated faction history *reduces* allegiance flips" is a
plausible hypothesis, not a measured fact — keep it visibility-only. The codex stance must not silently
become a *gate* the turn director is scored against; that is the FR-545 ledger's job. The optional
turn-director `stance` prior (already deferred to follow-up) is the correct home if it ever earns
evidence.

**Scope after conditions:** unchanged in spirit, corrected in mechanism — a `parse_json: true`
`world_codex.yaml` graph, a `prompts/world_codex.yaml` JSON contract, a `doc_ops.expand_codex` boundary
sequenced on synopsis-accept after `expand_roster`, a `{% if %}`-guarded `world_codex` block threaded
into `final_cut`, the byte-identical-absence RED, and example-exempt changelog + diary. No inline nested
schema. No `reviewed` flag. No length test as a gate.

**Verdict: APPROVE WITH CONDITIONS.** Amend Proposed Solution + ACs per C1–C5 (C1 is load-bearing —
the current graph cannot compile), then proceed to RED-first enforce under the existing example-exempt
discipline. No re-judge required if the amendment honors the five conditions.

---

## Implementation (2026-06-20) — Enforced

**Commits (local):** RED `7aeba5c0` (test, `SKIP=pytest`) -> GREEN `5334a7f5` (feat).

**Mechanism (per amended C1–C5):**
- [examples/dungeon_master/world_codex.yaml](examples/dungeon_master/world_codex.yaml) — new
  `parse_json: true` single-node graph, state `{synopsis: str, codex: dict}`, state_key `codex`,
  prompt `world_codex`. Output-shape sibling of `chapter_outline.yaml` (C1/C2), **not** a schema
  clone of `character_roster.yaml`.
- [examples/dungeon_master/prompts/world_codex.yaml](examples/dungeon_master/prompts/world_codex.yaml) —
  world-builder system prompt; JSON contract `{factions:[{name,identity,history,stance}],
  locations:[{name,description,significance}]}`, no markdown fences. Backstory-only rule: state the
  world, never narrate plot or reverse a fact.
- [examples/dungeon_master/api/doc_ops.py](examples/dungeon_master/api/doc_ops.py) — `expand_codex`
  boundary: idempotent guard (existing factions/locations -> return untouched, no graph call),
  `_normalize_codex` coerces each entry's string fields via `field()` (missing -> `""`), drops
  unknown keys, coerces non-list arrays to `[]`, drops unnamed entries; persists `doc["codex"]` via
  `story_doc.write`. **No `reviewed` key (C3).**
- [examples/dungeon_master/api/session.py](examples/dungeon_master/api/session.py) — `expand_codex`
  sequenced on the **synopsis-accept** branch immediately after `expand_roster` (C4). The "between
  expand_roster and expand_chapters" point in the original FR did not exist as a single call site.
- [examples/dungeon_master/api/final_cut.py](examples/dungeon_master/api/final_cut.py) —
  `_format_world_codex` renders faction/location lines; `final_cut_context` carries `world_codex`
  (empty string when no codex).
- [examples/dungeon_master/final_cut.yaml](examples/dungeon_master/final_cut.yaml) +
  [examples/dungeon_master/prompts/final_cut.yaml](examples/dungeon_master/prompts/final_cut.yaml) —
  `{% if world_codex %}` guarded block so a doc with no codex composes byte-identically (additive
  invariant, C5).
- [examples/dungeon_master/api/tree.py](examples/dungeon_master/api/tree.py) — `WORLD_CODEX_GRAPH`
  path constant.

**Deviation from spec (recorded):** the FR listed a `generate.py` call site to mirror the
`session.py` insertion. During enforce, `generate.py` was found to drive `session.accept()` (the same
adapter), so the single `session.py` insertion covers both entry paths — the "two call sites" were
one. No second insertion was made.

**Acceptance verification:**
- [examples/dungeon_master/tests/test_world_codex.py](examples/dungeon_master/tests/test_world_codex.py) —
  5 deterministic tests: persists factions+locations (no `reviewed` key), normalizes malformed
  object (missing fields -> `""`, bogus key dropped, non-list -> `[]`), idempotent for immutable
  reference (`_ExplodingApp` never invoked), `final_cut` world_codex empty when absent (byte-identical
  guard), world_codex present when codex set. All green.
- Full DM suite: `390 passed, 1 deselected` (`-m "not slow"`).
- `yamlgraph graph lint` clean for `world_codex.yaml` and `final_cut.yaml` (the W023 `arc`/`climax`
  warning on `final_cut.yaml` is pre-existing, unrelated to this change).
- C5 length/continuity remains visibility-only (demo-output.log), not a CI gate — LLM-nondeterministic.
