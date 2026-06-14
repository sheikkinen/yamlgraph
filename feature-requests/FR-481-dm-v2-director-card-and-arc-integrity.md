# FR-481: DM v2 — Director Card & Arc Integrity

**Priority:** MEDIUM
**Type:** Enhancement (DM v2 prototype; inherits FR-474 J3/J4 regime)
**Status:** Judged (2026-06-14). Scope frozen to **Deliverable A (always-visible
Director card)** + **Deliverable B2 (deterministic monotonic phase clamp)**.
Deliverable C (beats cumulative) and Deliverable D (trait binding) deferred to
follow-on FRs. See *Judgement*. **Implemented (2026-06-14)** — see *Implementation
Status*.
**Effort:** ~0.5 day (prototype, A + B2)
**Requested:** 2026-06-14
**Judged:** 2026-06-14
**Continues:** FR-479 (director/narrator split) and FR-480 (roster/scene name
binding). Surfaced by the first full 9-turn run `6eae1ce5` ("10,000 B.C. in
heat"). Same J3 rules apply: **no CAP/REQ, no CI gate, no demo-log**; the
walkthrough tests under `examples/dungeon_master/tests/` are a visibility
harness, not a gate.

**Model under test:** `vertex` / `gemini-3.5-flash` (`PROVIDER=vertex`,
`VERTEX_MODEL=gemini-3.5-flash`). All observed defects below are from this model.

## Summary

The FR-479 director pipeline now runs end to end, but its structured judgement
(`direction`) is mostly **invisible** — the UI surfaces only `continuity` and
`scene_complete`, and only when non-empty. The director's `phase`,
`establishing`, `beats_satisfied`, and `steer` are computed every turn and shown
to no one. Make the full director signal **always visible as a small card**, and
fix three arc-integrity defects the full run exposed.

## Value Statement

The director becomes legible: on every turn the DM can see where the arc stands
(phase), which beats are satisfied, whether the narrator was steered, and whether
the scene has ended — instead of trusting an unseen judge. The arc-integrity
fixes stop the director from contradicting itself (un-climaxing, oscillating
beat lists), so the signal it shows is trustworthy.

## Problem

Evidence — run `outputs/dungeon-master/6eae1ce5/` (9 turns, `scene_complete`
reached cleanly on turn 9). What worked: roster binding held (cast =
`Taka/Jarek/Lana`, no phantom names, `continuity: []` every turn); `establishing`
fired only on turn 1; `steer` stayed empty; `scene_complete` flipped on the final
beat. What broke:

### A. The director's judgement is invisible (the primary ask)

`turn_card.html` renders only `stage.continuity` (when non-empty) and
`stage.scene_complete` (when true). `StageView` carries only those two fields
(`session.py`). The director computes `phase`, `establishing`, `beats_satisfied`,
and `steer` on every turn and the UI discards them. There is no way, from the
play view, to see that turn 5 was `climax` or that turn 9 satisfied the final
beat. **The director should always be visible — as a small, compact card.**

### B. Phase is non-monotonic — the arc runs backwards

Observed phase sequence across turns 1–9:

```
opening(1) → rising(2,3,4) → climax(5) → rising(6,7,8) → resolved(9)
```

The director labeled the yield (turn 5) `climax`, then **regressed to `rising`**
for the rope-throw and haul-out beats (turns 6–8). An arc should not un-climax.
The director has no monotonic-phase constraint and is given no memory of the
phase it already declared.

### C. `beats_satisfied` oscillates between cumulative and incremental

Turn 4 lists 4 beats (cumulative), turn 7 lists all 7 (cumulative), but turns 5,
6, 8, 9 each list only the single *new* beat (incremental). The field's contract
is undefined, so a consumer cannot tell "beats so far" from "beats this turn".
The prompt says "the BEATS that have now actually occurred" (implying cumulative)
but the model does not honor it consistently.

### D. Role/trait drift survives name binding (FR-480's next layer)

FR-480 bound character **names** to the roster, and it held. But the `key_scene`
describes *"Lana — shaman's daughter of 16 years"*, while her card and the
synopsis define her as an adult **gatherer** with no shaman lineage. The name is
correct; the *identity* drifted. FR-480 fed names into key-scene generation, not
the card summaries — so the generator invented a backstory the canon never
sanctioned.

## Proposed Solution

Four deliverables. **The Judge should decide scope** (which ship now, which
defer). Lean: ship A+B+C now (all surfaced by one run, all small); D is the
FR-480 follow-on and may split out.

### Deliverable A — Always-visible Director card (primary)

Surface the full `direction` on every turn as a compact card.

- `StageView` (`session.py`) gains the remaining director fields. Lean: carry the
  whole reader output as `direction: dict` (one field) rather than four scalars,
  so the template owns presentation and future director fields need no dataclass
  change. (Judge: one `direction: dict` vs explicit typed fields.)
- `_view` populates it from `turn_ops.turn_direction(doc, n)` (already called for
  `scene_complete`/`continuity` — no new read).
- A new compact component (e.g. `components/director_card.html`) rendered in the
  `turn_card.html` aside, always present on a turn. Shows: `phase` (badge),
  `beats_satisfied` (count + list), `steer` (when non-empty), `scene_complete`,
  and folds the existing `continuity` block into it. Empty/opening turns render a
  hint, not a blank.
- Keep the existing standalone `🏁 Scene complete` banner in the main column
  (it is a play-loop control signal, not just director metadata).

### Deliverable B — Monotonic phase

Phase must never regress (`opening < rising < climax < resolved`). Options:

- **B1 — Prompt + prior-phase context.** Pass the previous turn's `phase` into
  `turn_direct.yaml` and instruct the director that phase only advances, never
  retreats. Normalizes at the judgement boundary; relies on the model.
- **B2 — Deterministic clamp in code.** In `turn_ops.py`, clamp the recorded
  phase to `max(prior_phase, model_phase)` by ordinal before persisting. Cheap,
  deterministic, model-independent.
- Lean: **B1 + B2** — give the director the context to be right (B1) *and* a
  deterministic floor so a model slip cannot corrupt the record (B2).

### Deliverable C — Define `beats_satisfied` as cumulative

Fix the contract to one meaning: **cumulative** (all beats satisfied so far).
Options:

- **C1 — Code-side cumulative union.** In `turn_ops.py`, persist the union of
  this turn's `beats_satisfied` with all prior turns' (normalized phrases).
  Deterministic; the stored field is always the full satisfied set.
- **C2 — Prompt-only.** Pass prior `beats_satisfied` into the director and
  instruct it to return the cumulative set. Fragile (the very inconsistency we
  are fixing).
- Lean: **C1** (deterministic union in code, not a model promise).

### Deliverable D — Bind scene traits to the cards (defer candidate)

Extend FR-480's binding from names to identity: feed each rostered character's
**card summary** (role/origin, not full text) into `key_scene` generation so the
scene cannot invent a role the card never granted (the "shaman's daughter"
drift). Options: pass a short `cast_bios` block into `prompts/key_scene.yaml`
alongside the existing `roster` names. **Judge: ship with A–C, or split to its
own FR** (it is the FR-480 next-layer and arguably a separate concern from arc
integrity).

## Acceptance Criteria

- **A:** On any turn, the play view renders a Director card showing `phase`,
  `beats_satisfied`, `steer` (when present), `scene_complete`, and `continuity`.
  A walkthrough test asserts the rendered turn response contains the phase and a
  beat label for a drafted turn.
- **B:** A test asserts that, given a director returning a phase lower than the
  prior turn's, the persisted/recorded phase never decreases across turns
  (ordinal-monotonic).
- **C:** A test asserts `beats_satisfied` on turn _n_ ⊇ `beats_satisfied` on turn
  _n−1_ (cumulative), for a multi-turn scene.
- **D (if in scope):** A test asserts the generated `key_scene` does not assign a
  rostered character a role/descriptor absent from their card (e.g. no "shaman"
  when the card says "gatherer").
- Full walkthrough suite GREEN; `ruff check` clean; `yamlgraph graph lint`
  clean on any changed graph YAML.

## Open Questions (for the Judge)

1. **A's `StageView` shape:** one `direction: dict` field vs four typed scalars?
   Lean dict (template owns presentation, forward-compatible).
2. **B:** B1+B2 together, or B2 alone (deterministic floor) without spending
   prompt tokens on prior-phase context?
3. **C:** confirm cumulative (C1) is the intended contract — vs redefining the
   field as *incremental* (this-turn-only) and renaming it. Lean cumulative.
4. **D scope:** ship with A–C or split to FR-482? Lean split (separate concern).

## Implementation Notes

- DM example app: presentation in `api/` + `templates/`, logic in `turn.yaml` /
  `prompts/turn_direct.yaml`, no Python in the graph layer.
- Reuse `turn_ops.turn_direction(doc, n)` — already the single reader for the
  director dict. B persistence belongs in `turn_ops` where the turn record is
  written (`invoke_turn`), not in the view layer.
- TDD: RED test per deliverable first (SKIP=pytest split), then GREEN.
- Changelog fragment required (`type: feat, scope: examples`, no `req:`).
- Diary reflection with a Seed on completion.

## Judgement (2026-06-14)

Scope frozen to **A + B2**. C and D deferred. The run `6eae1ce5` surfaced four
defects but they are not one concern: A and B are about the *director's arc
signal* (make it visible, make it not contradict itself); C is a *field-contract*
cleanup with a hidden matching problem; D is the *FR-480 next layer* (identity,
not arc). Ship the coherent pair; split the rest.

**J1 — Deliverable A is IN and primary (the explicit ask: "direction should
always be visible, plan as small card").** Resolves *Open Question 1* in favour of
a **single `direction: dict` field** on `StageView`, and **folds the existing
`scene_complete: bool` and `continuity: list[str]` scalars into it** — they are
removed as separate `StageView` fields. Rationale: two sources for the same datum
(`StageView.scene_complete` vs `direction["scene_complete"]`) is a drift hazard;
one reader (`turn_direction`) already returns the whole dict; `StageView` already
carries `intents`/`crumbs` as dicts, so this conforms to the existing view-layer
pattern (the typed-output law governs *LLM outputs*, which are typed by the
`turn_direct` `output_schema` upstream — the view layer is presentation). The new
compact `components/director_card.html` lives in the `turn_card.html` aside,
**always rendered on a turn** (opening/empty turns show a hint, not a blank), and
shows `phase` (badge), `beats_satisfied` (count + list), `steer` (when non-empty),
`scene_complete`, and **absorbs** the existing `continuity` block. The standalone
`🏁 Scene complete` banner in the main column **stays** — it is a play-loop
control affordance, not director metadata.

  Consumers to update when the scalars move: `turn_card.html` switches
  `stage.scene_complete`/`stage.continuity` to `stage.direction.*`. The plain-
  advance stop in `_accept_target` reads `turn_ops.turn_direction` **directly**
  (not via `StageView`), so it is unaffected — confirmed not a hidden coupling.

**J2 — Deliverable B is IN, but B2 only (deterministic clamp); B1 deferred.**
Resolves *Open Question 2*. Phase is defined as "where the arc stands"; once an
arc reaches climax it cannot un-reach it, so a non-decreasing phase is not just a
guard but the *correct* semantics. A deterministic clamp at the persistence
boundary — `phase := max(prior_phase, model_phase)` by ordinal
(`opening<rising<climax<resolved`) in `invoke_turn` before the direction dict is
recorded — fully satisfies the acceptance criterion, is model-independent, and
spends no prompt tokens. B1 (feeding prior phase into the prompt) is **not
required**: the model already slipped, and the clamp makes the record correct
regardless of what the model returns. Defer B1 unless a future run shows the
clamp masking a *genuinely* wrong forward phase. The card (A) displays the
clamped, monotonic phase, so the two deliverables compose cleanly.

  Known, accepted limitation: the clamp does not police a *premature* high phase
  (model over-claiming `resolved` early). That is a distinct false-positive
  concern; `scene_complete` already guards the actual play-loop stop, so it is
  out of scope here.

**J3 — Deliverable C is DEFERRED to a follow-on FR.** Resolves *Open Question 3*
by confirming the intended contract is **cumulative**, but **not implementing it
now**. A *correct* cumulative union is not the free-string set-union the FR
sketched: the director copies beats "as short phrases" that drift in wording turn
to turn (paraphrases), so a naive union accumulates near-duplicates and the count
lies. The honest fix matches each turn's phrases against the **canonical `BEATS`
parsed from the frozen `key_scene.text`** — a fuzzy-matching problem worth its own
FR. Severity is lower than A/B: the Director card (A) shows each turn's raw
`beats_satisfied` usefully *without* a cumulative contract, so A does not depend
on C. Split out as **FR-482** (cumulative `beats_satisfied` via canonical-BEATS
matching). **Seed:** dedup satisfied beats against the canonical key-scene BEATS,
not by free-string union.

**J4 — Deliverable D is DEFERRED to its own FR.** Resolves *Open Question 4* in
favour of a split. D (binding scene *traits/roles* to character cards) is the
FR-480 next layer — an *identity* concern — not arc integrity. It carries its own
design question (how much of the card bio to feed key-scene generation without
bloating the prompt) and its own test. It does not belong in a director-card FR.

**J5 — Regime.** Inherits FR-474 J3: DM prototype under `examples/` is exempt
from CAP/REQ, CI gates, and demo-logs; the walkthrough tests are a visibility
harness, **not** a CI gate (no `@pytest.mark.req`). The `changelog-required`
pre-commit hook **still applies** — one fragment (`type: feat, scope: examples`,
no `req:`).

**J6 — TDD.** RED test first for each shipped deliverable (commit RED with
SKIP=pytest, GREEN separately): (A) a drafted-turn render asserts the response
contains the phase label and a beat label; (B) a director returning a phase below
the prior turn's yields a *recorded* phase that does not decrease. `ruff check`
and `yamlgraph graph lint` (on any changed graph YAML) must be clean.

**Authority granted** for **A + B2** only. C and D are out of scope for this FR —
do not implement them here; capture each as a follow-on FR on completion.

## Implementation Status (2026-06-14)

Shipped **A + B2** exactly as judged. C deferred to **FR-482**, D to a future FR.

| Deliverable | Status | Where |
|---|---|---|
| A — `StageView.direction: dict` (scalars folded in) | ✅ | `api/session.py` |
| A — `components/director_card.html` (always rendered) | ✅ | new component + `turn_card.html` aside |
| A — Director card CSS (compact) | ✅ | `api/templates/base.html` |
| A — main `scene-complete` banner reads `direction.scene_complete` | ✅ | `turn_card.html` |
| B2 — `_clamp_phase` ordinal floor in `invoke_turn` | ✅ | `api/turn_ops.py` |

**Decisions / notes:**

- **A — one `direction: dict`, scalars removed.** `StageView.scene_complete` and
  `StageView.continuity` were deleted; the card and the main banner now read
  `stage.direction.*`. Confirmed `_accept_target`'s plain-advance stop reads
  `turn_ops.turn_direction(doc, n)` directly (not via `StageView`), so it was
  unaffected — no hidden coupling.
- **A — `beats_total` forward-compat.** The card renders a `k / N` count only when
  `direction.beats_total` is truthy; FR-481 never sets it, so the count stays
  hidden until **FR-482** populates canonical beats. Jinja `Undefined` is falsy,
  so the absent key is safe.
- **B2 — clamp only, B1 deferred.** `_clamp_phase` floors `phase` at the prior
  turn's by ordinal (`opening<rising<climax<resolved`); a forward advance and an
  unknown phase string are left untouched. The director prompt was *not* changed
  (B1 deferred per J2). The card displays the clamped, monotonic phase.
- **Tests (FR-474 J3 visibility harness, no `@pytest.mark.req`):** test 13
  (`director-card` + phase badge + beat label rendered on a turn), test 14 (a
  forced `opening→climax→rising` sequence is recorded `opening→climax→climax`),
  and a `_clamp_phase` unit test (floor up, allow advance, no-prior). Full suite
  **26 passed**; `ruff check` + `ruff format` clean; `yamlgraph graph lint
  turn.yaml` clean.
