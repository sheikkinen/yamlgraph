# Feature Request: FR-498 — Roster faction + starting inventory (front-boundary continuity)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged — scope frozen with amendments (2026-06-16); see Judgement
**Effort:** 0.5–1 day
**Requested:** 2026-06-16

## Summary

Pin every principal in the DM v2 cast roster to an explicit **faction/clan** and a
**starting inventory** *before any chapter plays*, so under-specified characters
can no longer drift their affiliation or spawn phantom possessions across chapters.

This is the cheapest of the three continuity fixes surfaced by reviewing the
6-chapter *Floodmark Saga* with `examples/book_reviewer` (FR-497): it kills the
highest-severity finding (a character switching clans between chapters) **at the
spec boundary** where the data enters, not downstream where it manifests.

## Value Statement

A reviewer-found, highest-severity continuity break — *Valda is an Aschenwulf
instigator in Chapter 1 and a Bärenschädel priestess in Chapter 2* — is eliminated
at its source: when the roster fixes each principal's faction and starting kit up
front, every chapter inherits one unambiguous fact instead of guessing, removing
the entire affiliation-flip and phantom-inventory *class* of break.

## Problem

Live evidence (`outputs/dungeon-master/10000-BC/review.md`, FR-497 reviewer over a
DM-generated book):

- **Faction flip (severity: high).** The premise calls Valda only "the keeper of
  the old rites" with **no clan**. Cast derivation
  ([prompts/character_roster.yaml](examples/dungeon_master/prompts/character_roster.yaml),
  [prompts/character.yaml](examples/dungeon_master/prompts/character.yaml)) never
  pinned a faction, so Chapter 1 placed her in the raiding Aschenwulf party and
  Chapter 2 made her the defending Bärenschädel priestess — a direct contradiction
  no per-chapter gate could see.
- **Phantom inventory.** Hilde acquires a "stone hand-axe" (Ch. 3) never in her
  established kit; Arnulf's stone knife appears, is lost, and reappears with no
  provenance. Inventory is not a roster fact, so nothing anchors it.

Both are *under-specification* propagating forward, not creative divergence — the
class of bug cheapest to kill in the spec (Scripture: `spec_kill`,
`normalize at the boundary`).

## Proposed Solution

Extend the character roster/sheet contract so each principal carries, at derivation
time, two new **fixed** fields the later chapter machinery treats as canon:

- `faction`: the clan/side the character belongs to (or an explicit `"unaligned"`).
  Derived once from the synopsis; never re-inferred per chapter.
- `inventory`: a short list of starting possessions (weapons, tools, tokens).

```yaml
# prompts/character.yaml schema (additions)
faction:
  type: string
  description: The character's clan/side, fixed at roster time. "unaligned" if none.
inventory:
  type: array
  items: { type: string }
  description: Starting possessions the character holds as the story opens.
```

The chapter director prompt
([prompts/turn_direct.yaml](examples/dungeon_master/prompts/turn_direct.yaml))
already flags actors-not-in-roster under `continuity`; extend that same flag to
fire when a rostered actor **acts under a faction other than their roster
`faction`**, or **wields an item not in their `inventory` and not acquired in a
prior recap**. Detection only — surface it, do not silently rewrite (Commandment 6).

This is a **prototype-scope** change under the FR-474 J3 regime: it touches only
`examples/dungeon_master/` prompts and the roster derivation, adds **no** CAP file
and **no** `@pytest.mark.req` markers, and is committed with an honest
`feat(dungeon-master): FR-498 …` plus the `FR-474 J3` trailer.

## Acceptance Criteria

- [ ] Roster schema gains `faction` (string) and `inventory` (list[str]); both
      populated for every derived principal.
- [ ] Derived `faction` is carried forward unchanged into every chapter's STARTING
      WORLD STATE (never re-inferred).
- [ ] Director `continuity` flags fire on faction-mismatch and on unprovenanced
      inventory use.
- [ ] A regenerated *Floodmark Saga* (or equivalent multi-faction premise),
      re-reviewed by `book_reviewer`, no longer reports the clan-flip break;
      captured to a log as the witness.
- [ ] Diary reflection + changelog fragment added.

## Alternatives Considered

- **Do nothing / fix in the editor pass (FR-500).** Treats the symptom downstream;
  every regenerate re-introduces the break. Rejected as the primary fix —
  front-boundary specification is strictly cheaper.
- **Free-text "background" field instead of typed `faction`/`inventory`.** Prose is
  lossy and unenforceable; the director cannot mechanically check it. Typed fields
  are the point.

## Related

- FR-497 — `book_reviewer` (produced the located findings this FR acts on)
- FR-491 J7 — forward-carry `world_state` ledger (the between-chapter half; FR-499)
- `examples/dungeon_master/prompts/character_roster.yaml`,
  `character.yaml`, `turn_direct.yaml`
- `outputs/dungeon-master/10000-BC/review.md` (live evidence)

## Judgement — 2026-06-16 (scope frozen with amendments)

**Status:** Judged — scope frozen. Verified against the live prompt architecture
before ruling; the original Proposed mechanism was corrected.

**Red Hat — is the pain real?** Yes. The roster
([character_roster.yaml](examples/dungeon_master/prompts/character_roster.yaml))
"collapse[s] a faction into its single leader", so a *non-leader* principal like
Valda is cast with no clan anchor — exactly why she flipped Aschenwulf→Bärenschädel
across Ch1→Ch2 in `review.md`. Concrete, highest-severity, reproducible. Authorized.

- **J1 (premise correction — BLOCKING amendment).** The Proposed Solution's
  `output_schema` fields are **wrong for this codebase**. The character sheet
  ([character.yaml](examples/dungeon_master/prompts/character.yaml)) is **labeled
  prose** with EXACT uppercase labels (`SUMMARY/ROLE/ORIGIN/APPEARANCE/PERSONALITY/
  DRIVE/BOND/FLAW`), not a JSON schema; the roster returns **names only**. The fix
  is therefore a **new labeled field**, not a schema property. Ruling: add a single
  `FACTION:` label (one canonical token, e.g. `Aschenwulf` / `Bärenschädel` /
  `unaligned`) and promote the inventory concept to its own `INVENTORY:` label.
- **J2 (kill the duplication).** `ORIGIN:` already encodes "their people, place, or
  past" and `APPEARANCE:` already lists "what they carry". Do **not** add a second
  prose home for the same fact. `FACTION:` extracts the *clan token* as canon (ORIGIN
  stays prose flavor); `INVENTORY:` **replaces** the "what they carry" bullets in
  APPEARANCE so possessions live in exactly one place the director can check.
- **J3 (leak-guard is a hard dependency).** FR-496 just fought *leaked* `SUMMARY:`/
  `ROLE:` scaffolding into final prose. Two new labels enlarge that leak surface.
  Ruling: the FR-496 label-strip guard MUST be extended to `FACTION:`/`INVENTORY:`
  in the **same** change; a regenerated book showing either label in `story.md` is a
  failing acceptance criterion.
- **J4 (detection only, this FR).** The director `continuity` flag fires on
  faction-mismatch / unprovenanced-inventory — it **surfaces**, does not block.
  Blocking/enforcement is FR-499's scope; do not creep it here.
- **J5 (regime).** Prototype-only (`examples/dungeon_master/`). FR-474 J3 applies:
  no CAP, no `@pytest.mark.req`, honest `feat(dungeon-master): FR-498 …` + `FR-474 J3`
  trailer.
- **J6 (sequence).** This is the front-boundary fix and supplies the canonical
  `faction` token FR-499's ledger carries. **Do FR-498 before FR-499.**

**Frozen acceptance criteria** (supersede the Proposed list):
1. Sheet gains `FACTION:` (single token) and `INVENTORY:` (terse list) labels;
   `INVENTORY:` subsumes APPEARANCE's "what they carry".
2. `FACTION:` carried forward unchanged into every chapter's STARTING WORLD STATE.
3. FR-496 leak-guard extended to the two new labels; regenerated `story.md` shows
   neither label (witness log).
4. Director `continuity` flags (advisory) fire on faction-mismatch and
   unprovenanced-inventory use.
5. Regenerated Floodmark-class book, re-reviewed by `book_reviewer`, no longer
   reports the clan-flip break (witness log).
6. Diary + changelog fragment.

## Implementation Status — Enforced

- **Sheet labels (AC1).** `prompts/character.yaml` now declares `FACTION:` (after
  `ORIGIN:`, "ONE token … or unaligned … the affiliation later chapters carry
  forward unchanged") and `INVENTORY:` (after `APPEARANCE:`, "subsumes what they
  carry; do not also list it under APPEARANCE"). `APPEARANCE:`'s old "what they
  carry" clause was removed; the user reminder line lists the full label order
  including the two new labels.
- **Carry-forward (AC2).** The faction token rides the structured ledger
  (FR-499A): `chapter_close.yaml` is instructed faction is FIXED and carried
  forward unchanged, and the formatted ledger renders `Name (Faction)` into the
  next chapter's STARTING WORLD STATE.
- **Leak-guard (AC3).** No generic strip exists; the cast gloss reads the
  `SUMMARY:` value alone (FR-496), so the two new labels can never leak.
  `test_render_cast_never_leaks_faction_or_inventory_labels` proves it; the live
  witness asserts no `FACTION:`/`INVENTORY:` in `story.md`.
- **Director flags (AC4).** `prompts/turn_direct.yaml`'s `continuity` guidance now
  enumerates faction-mismatch and unprovenanced-item as breaks to surface
  (advisory; no blocking — that is FR-499 Phase B).
- **Tests.** New `tests/test_character_prototype.py` (5 prompt-contract +
  render-purity tests). Full DM suite: **107 passed**. ruff + import-linter clean.
- **Regime (J5).** `feat(dungeon-master): FR-498 …` + `FR-474 J3` trailer; no CAP,
  no `@pytest.mark.req`. Changelog fragment + diary added.

**Status: Enforced** (AC5 live-witness: see combined Floodmark-v2 regen + review).
