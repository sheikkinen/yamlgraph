# FR-480: DM v2 — Roster/Scene Name Binding & Continuity Flag Dedupe

**Priority:** MEDIUM
**Type:** Enhancement (DM v2 prototype; inherits FR-474 J3/J4 regime)
**Status:** Implemented (2026-06-13). Scope frozen to Deliverable A (name binding
via A1); Deliverable B (continuity dedupe) deferred to a future FR. See
*Judgement* and *Implementation Status*.
**Effort:** ~0.5 day (prototype, A only)
**Requested:** 2026-06-13
**Judged:** 2026-06-13
**Continues:** FR-479 (director/narrator split). This is the **J1 split-out** —
the roster-reconciliation concern that Judgement deferred out of FR-479 — plus a
small dedupe fix that FR-479's first real run surfaced. Same J3 rules apply:
**no CAP/REQ, no CI gate, no demo-log**; the walkthrough tests under
`examples/dungeon_master/tests/` are a visibility harness, not a gate.

## Summary

Bind the character names used by the **key scene** to the names in the
**roster** (and character cards), so the two generation passes stop inventing
divergent spellings of the same character. Then dedupe the director's
`continuity` flags so each distinct breach is surfaced once per scene instead of
re-reported every turn.

## Value Statement

The DM stops seeing the same name-mismatch alarm on every turn, and the turn
loop stops flagging a character as a "phantom" when it is really the same person
under a near-miss spelling. A continuity flag becomes a *signal* again — it
fires when something genuinely new and wrong happens, not as constant noise.

## Problem

### 1. The names drift at generation time (root cause)

The synopsis stage spawns two **independent** leaves, each deriving character
names from the synopsis without seeing the other:

- `character_roster.yaml` → `prompts/character_roster.yaml` — "names only, one
  per line", then `split_roster` lowercases each into an id (`Broga` → `brog`).
- `key_scene.yaml` → `prompts/key_scene.yaml` — writes a `CHARACTERS:` section
  with its own names (`Broga`), never shown the roster.

Neither pass is anchored to the other. In run `c8c0b08c`
("10,000 B.C. in heat") the roster minted `brog` while the key scene wrote
`Broga` — the same character, two names. This is the **Vane class** of FR-479's
motivating bug (a scene name with no exact roster match), here as a near-miss
spelling rather than a wholesale phantom.

### 2. The continuity flag is correct but fires as noise

FR-479's `direct` node correctly *detects* the `Brog`/`Broga` mismatch — that is
working as designed (J2: detection only, never auto-rewrite). But it re-reported
the **identical** breach on all 6 turns of run `c8c0b08c`:

```
T1: "Rostered character 'Brog' is referred to as 'Broga' in the scene plan."
T2: "Character 'Brog' is listed in the roster and intents instead of 'Broga'."
T3: "Character 'Brog' in the roster and intents is a misspelling of 'Broga'."
T4: "Character 'Broga' is misspelled as 'Brog' in the rostered cast and intents."
T5: "Character 'Broga' is rostered and submits intent under the name 'Brog'."
T6: "Character 'Brog' is acting, but the planned character name is 'Broga'."
```

An alarm that fires every turn trains the DM to ignore it — and will bury the
*next, genuinely new* phantom under repetition of an already-acknowledged one.

## Proposed Solution

Two deliverables, both within the synopsis/turn prototype. **The Judge should
decide whether these ship together or split into two FRs** (see *Open Questions*).

### Deliverable A — Bind scene names to the roster

Make character names consistent across the roster, the character cards, and the
key scene. Design alternatives (for the Judge to rule on):

- **A1 — Feed the roster into key-scene generation.** The roster is already
  derived on synopsis-accept *before* the key scene auto-drafts, so pass the
  roster names into `key_scene.yaml` as authoritative cast (`prompts/key_scene.yaml`
  gains a `roster` variable: "use exactly these character names"). Cheapest;
  respects the existing leaf order. Risk: the roster ids are already lowercased
  (`brog`) — binding the scene to an id loses the proper-noun casing, so the
  scene must receive the *display names*, not the split ids.
- **A2 — Derive the roster from the key scene.** Generate the key scene first,
  then extract the cast from its `CHARACTERS:` section instead of from the
  synopsis. Single source of truth, but inverts the current stage order and the
  roster prompt's contract.
- **A3 — A reconciliation pass.** Keep both independent, add a small normalizer
  that maps scene names onto the nearest roster name after generation. Most
  surgical, but adds a step whose only job is to paper over the drift A1/A2 would
  prevent at the source — a downstream-fix smell.

Lean: **A1** (normalize at the generation boundary, not downstream), but the
roster-casing wrinkle is real and the Judge should confirm the data flow.

### Deliverable B — Dedupe continuity flags

The director already emits `continuity: list[str]`. Surface each *distinct*
breach once per scene rather than re-reporting it every turn. Options:

- **B1 — Dedupe at render/read time** in `turn_ops.py` / `session.py`: collapse
  a turn's `continuity` flags against the breaches already surfaced on prior
  turns of the same scene (e.g. by a normalized key of the character pair), so
  `StageView.continuity` shows only *new* breaches.
- **B2 — Tell the director** in `prompts/turn_direct.yaml` to report a breach
  only on first occurrence. Cheaper prompt-only change, but relies on the model
  honoring "only if new" without prior-turn context — fragile.

Lean: **B1** (deterministic dedupe in code, not a model promise).

## Judgement (2026-06-13)

**J1 — Scope frozen to Deliverable A; Deliverable B deferred.** A removes the
*cause* of the observed continuity noise: once the key scene and the roster
share names, the `Brog`/`Broga` mismatch that fired on all 6 turns of run
`c8c0b08c` cannot arise. B (dedupe) is therefore **not required to cure the
observed incident** and is deferred to its own future FR for two reasons:
  1. **Purge/YAGNI.** The only observed continuity noise is the name drift A
     eliminates at the source. Building dedupe machinery now hardens against a
     case (a genuine recurring narrator-invented phantom) not yet observed on
     the FR-479 pipeline.
  2. **B's correct form is a larger change than a dedupe.** The director emits
     `continuity` as *free prose that varies every turn* — the six flags in
     `c8c0b08c` are six different sentences describing one breach. String-equality
     dedupe cannot collapse them. Doing B properly means first restructuring
     `continuity` into stable keyed objects (a schema change to
     `prompts/turn_direct.yaml`), then deduping. That is too large to ride along
     with name binding and must be judged on its own. Recorded as a Seed below.

**J2 — A1 (bind the key scene to the roster's display names). Reject A2 and A3.**
The draft's "roster-id casing wrinkle" **does not exist**. Verified data flow:
`accept(synopsis)` → `_expand_roster` derives the roster and writes
`characters.cards[cid] = {"name": <display>, …}` keeping the proper-case display
name (`split_roster` preserves the name; only `unique_slug` lowercases the *id*)
→ lands on `key_scene` → `_autodraft` → `_invoke_stage`. So at key-scene draft
time the display names (`"Brog"`, `"Sela"`, `"Tark"`) already exist in the doc.
A1 feeds **those display names** (not the lowercased cids) into key-scene
generation as the authoritative cast. The roster is generated first and gates the
cards, so it is the natural source of truth — this is normalizing at the
generation boundary (the_one_law), not downstream.
  - **Reject A2** (derive roster from the key scene): inverts the
    `synopsis → roster → key_scene` order that the whole tree gating
    (`preplan_complete`, `_next_unreviewed_char`, card spawning) depends on.
  - **Reject A3** (post-hoc reconciliation pass): a `downstream_fix` — a step
    whose only job is to paper over drift A1 prevents at the source.

**J3 — Thread the roster as a `key_scene.yaml` variable.** Verified
`_invoke_stage` builds graph variables from `stage.context` (text stages) plus
`stage.var_name`. The roster is not a text stage, so threading it needs a small
declarative hook, not a `key_scene`-name special-case. Implementation lands the
binding so `prompts/key_scene.yaml` receives the roster display names as an
authoritative cast list ("use EXACTLY these character names; introduce no others").
Confirm the exact mechanism in enforce (a `Stage` flag like `include_roster`, or
a roster entry in the variable builder) — the contract is: the key-scene prompt
sees the roster display names.

**J4 — Acceptance is one structural walkthrough test + green regressions.** Mock
generation with a deliberate name drift in the *inputs* (roster says `Brog`, the
unbound key-scene mock would say `Broga`) and assert that, with the binding, the
key scene's `CHARACTERS:` names are a case-insensitive subset of the roster
display names. All FR-477/FR-479 turn tests stay green.

**J5 — One concern, one commit.** A is a single concern (name binding); it lands
as one commit. (B, when it returns, is its own FR and its own commit.)

## Acceptance Criteria (structural, per FR-474 J3)

1. **Name consistency.** After a fresh synopsis→roster→key-scene draft, every
   name in the key scene's `CHARACTERS:` section matches a roster display name
   (case-insensitive subset). A walkthrough test mocks generation with a
   deliberate `Brog`/`Broga` drift in the *inputs* and asserts the binding
   reconciles them (the key scene uses the roster's names).
2. Existing FR-477/FR-479 turn tests still pass (establishing, scene_complete,
   steer, the phantom flag).

## Out of Scope

- **Deliverable B (continuity-flag dedupe)** — deferred to a future FR per J1.
  Recorded as a Seed below.
- Multi-scene semantics, scene transitions, or any change to `scene_complete`
  beyond what FR-479 shipped.
- Auto-applying continuity as `steer` — FR-479 J2 keeps continuity informational;
  this FR does not change that.
- Roster editing UI / drafting a genuine phantom as a real player. Detecting and
  binding names is in scope; promoting an unrostered actor into the cast is not.
- Any CAP/REQ/gate/demo-log (J3 regime).

## Seed (deferred Deliverable B)

The director's `continuity` is free prose that varies every turn, so it cannot be
deterministically deduped as-is. A future FR should (a) restructure `continuity`
into stable keyed objects in `prompts/turn_direct.yaml`'s `output_schema` (e.g.
`{character, issue}`), then (b) surface each distinct breach once per scene. Trigger
the FR when a genuine recurring narrator-invented phantom (the Vane class) is
observed firing every turn on a post-FR-480 run.

## Evidence

Run `outputs/dungeon-master/c8c0b08c/story.json` (2026-06-13, first run on the
FR-479 director pipeline): 6 turns, scene_complete correctly at T6, establishing
and steer worked; continuity flagged the `Brog`/`Broga` mismatch on all 6 turns.
Roster `["tark","sela","brog"]` vs key-scene `CHARACTERS: Sela / Broga / Tark`.

## Files (anticipated)

| File | Change |
|------|--------|
| `examples/dungeon_master/prompts/key_scene.yaml` | consume roster display names as authoritative cast ("use EXACTLY these names") |
| `examples/dungeon_master/key_scene.yaml` | add a `roster` variable to the key-scene node |
| `examples/dungeon_master/api/session.py` (`_invoke_stage` / `Stage`) | thread roster display names into key-scene drafting (J3) |
| `examples/dungeon_master/tests/test_turn_prototype.py` | assert key-scene names ⊆ roster names under input drift |

*(Deliverable B files are out of scope per J1.)*

## Implementation Status (2026-06-13)

Shipped Deliverable A exactly as judged (A1 via J2/J3). All 23 DM walkthrough
tests pass; the key-scene graph lints clean; the prompt renders the roster
binding when names are present and cleanly omits it when empty.

| File | What shipped |
|------|--------------|
| `examples/dungeon_master/api/tree.py` | `Stage` gains `include_roster: bool = False`, set `True` on the `key_scene` stage. |
| `examples/dungeon_master/api/session.py` (`_invoke_stage`) | when `stage.include_roster`, builds the rostered display names (in roster order, from `characters.cards[cid].name`) and threads them as a `roster` graph variable. |
| `examples/dungeon_master/key_scene.yaml` | adds `roster: str` to state and `roster: "{state.roster}"` to the node; usage comment documents `--var roster=""`. |
| `examples/dungeon_master/prompts/key_scene.yaml` | a `{% if roster %}` CAST block makes the rostered names authoritative ("use EXACTLY these names, no variants, no new principals"); a matching reminder in the user prompt. |
| `examples/dungeon_master/tests/test_turn_prototype.py` | new `test_key_scene_binds_to_roster_names` asserts the generated scene's proper names ⊆ roster names (the unbound drift name `Naru` cannot appear); `test_phantom_actor_raises_continuity_flag` adapted to inject the stray name post-generation (director detection is now defense in depth). |

**Verified data flow (confirms J2's “no casing wrinkle”):** `accept(synopsis)` →
`_expand_roster` writes `cards[cid] = {"name": <display>}` (proper case; only the
*id* is lowercased) → lands on `key_scene` → `_autodraft` → `_invoke_stage` threads
the **display** names. The roster is populated before the key scene drafts, so
the binding always has the cast available.

**Deviation — phantom-test setup, not assertion.** FR-480 stops the *generator*
from minting a non-roster name, so the FR-479 phantom test could no longer obtain
its phantom from generation. Its assertion (the director flags a non-roster name)
is unchanged; only the injection moved from “generator emits `Naru`” to “test
writes `Naru` into the frozen scene, then re-rolls.” This keeps director detection
tested as defense in depth after the generation boundary is hardened.
