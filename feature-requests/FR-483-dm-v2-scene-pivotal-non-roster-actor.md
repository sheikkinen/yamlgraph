# FR-483: DM v2 — Recognize Scene-Pivotal Non-Roster Actors (Casting + Continuity)

**Priority:** MEDIUM
**Type:** Enhancement (DM v2 prototype; inherits FR-474 J3/J4 regime)
**Status:** Judged (2026-06-14). Scope frozen to **A (key-scene casting, prompt)
+ B (continuity suppression, code-side in `turn_ops`)**. The `turn_direct.yaml`
clause reword is IN as honesty polish but the acceptance guarantee rests on the
code filter, not the prompt. See *Judgement*.
**Effort:** ~0.3 day (prototype, one prompt edit + one code filter + tests)
**Requested:** 2026-06-14
**Judged:** 2026-06-14
**Continues:** FR-480 (roster/scene name binding). FR-480 and FR-479 share one
flawed premise — *a name not on the roster is an error* — enforced in **two**
places: the key-scene roster lock (which drops the actor) and the director's
continuity clause (which would flag the actor as a phantom every turn). This FR
fixes the premise at both boundaries. Same J3 rules apply: **no CAP/REQ, no CI
gate, no demo-log**; the walkthrough tests under
`examples/dungeon_master/tests/` are a visibility harness, not a gate.

**Model under test:** `vertex` / `gemini-3.5-flash`.

## Summary

A scene can legitimately turn on an actor the roster does not carry — a beast, a
third party, a force of nature the synopsis itself introduces. The pipeline has
no category for such an actor: it knows only *rostered intent-owner* vs.
*phantom/error*. As a result the same non-roster name is punished twice — dropped
from the key-scene CHARACTERS (FR-480 lock) and, if cast anyway, re-flagged as a
continuity breach on every turn (FR-479 director clause). Introduce the missing
category: a **scene-declared non-roster actor** is legitimate. Teach both prompts
to recognize it — `key_scene.yaml` may cast it; `turn_direct.yaml` must not flag
it as a breach.

## Value Statement

A character who **makes the turn happen** is listed where principals are declared
and is not re-reported as an alarm every turn. The CHARACTERS section regains its
meaning (who drives the scene) and the continuity flag regains its meaning (a
genuinely invented name with no provenance) — instead of both firing on a
legitimate third party the synopsis named.

## Problem

Evidence — a `key_scene.text` produced under the FR-480 roster lock:

```
SUMMARY: In a forest ravine, Vane ambushes and wounds Tarka, attracting the cave
bear Krog, who kills Vane before Tarka kills Krog.
INT/EXT: EXT
LOCATION: Forest ravine
TIME: MORNING

CHARACTERS:
- Tarka — hunter tracking Krog to win Sela
- Vane — rival hunter tracking Tarka to eliminate him
```

`Krog` **kills Vane and is killed by Tarka** — he is the fulcrum of the turn. Yet
he is absent from CHARACTERS while present in SUMMARY (and the BEATS). The model
*knew* Krog was a principal; it refused to list him only in the section that
confers principal status. The result is the "shallow appearance" failure: a major
actor reduced to background because casting him would violate the roster lock.

### Root cause: one premise — *non-roster name = error* — enforced in two prompts

The roster is minted in `character_roster.yaml` from the **human principals**
only. Everything downstream then treats "not on the roster" as a fault, in two
places:

1. **Key-scene casting (`key_scene.yaml`, FR-480 lock).** The CHARACTERS rule
   says "list the principals who drive the scene" (Krog qualifies), but the CAST
   block says *"no new principals the list does not contain"* / *"introduce no
   name the roster does not list"*. The two contradict; the model obeys the
   stricter lock and cuts Krog from CHARACTERS while still narrating him in
   SUMMARY and BEATS. → the shallow-appearance symptom you saw.

2. **Director continuity (`turn_direct.yaml`, FR-479 clause).** The director is
   told to flag *"any name taking a decisive action that is NOT one of the
   rostered cast."* So even once Krog is correctly cast, the director would
   report him as a continuity breach **every turn** — the identical
   fires-as-noise failure FR-480 Deliverable B set out to kill. Fixing only
   `key_scene.yaml` would trade a silent drop for a perpetual false alarm.

The underlying defect is the missing category. The breach the guards *should*
catch is narrow: a **variant of a rostered name** (`Brog`/`Broga`) or an
**invented name with no provenance** — a principal that exists in neither the
synopsis, the roster, nor the frozen scene. A **scene-declared actor** has
provenance: the frozen `key_scene.text` names him. The correct breach test is
therefore *"not in the roster **and** not declared in the scene's CHARACTERS,"*
not *"not in the roster."*

## Proposed Solution

Prompt-only, two files. Both fix the same premise at the boundary where each
guard runs. No code, no schema, no roster-id change (a scene-local actor is a
scene principal, not a rostered character card with DRIVE/BOND/FLAW).

### Deliverable A — Narrow the key-scene roster lock (`key_scene.yaml`)

In the `{% if roster %}` CAST blocks (system and user messages), replace the
absolute "introduce no name the roster does not list" with a scoped rule:

- Rostered characters **must** use their exact rostered spelling — no variant, no
  near-miss; refer to a faction by its rostered leader's name.
- Introduce **no new *human* principal** absent from both the synopsis and the
  roster.
- You **may** cast a scene-pivotal **non-roster actor** (a beast, an animal, a
  third party, a natural force) **if the synopsis names or clearly supports it**
  and it **acts at the turn** — name it consistently across SUMMARY, CHARACTERS,
  BEATS, and END.
- The existing principal cap (~4–5) and "cut bystanders" rule still hold: a
  non-roster actor earns its line by acting at the turn, not by being background.

### Deliverable B — Redefine the continuity breach (`turn_direct.yaml`)

The director's `continuity` clause currently fires on *"any name taking a
decisive action that is NOT one of the rostered cast."* Redefine the breach so a
scene-declared actor is not a breach:

- The frozen scene's CHARACTERS list is already in the director's context (it is
  part of `{{ scene }}`). Flag a name only when it takes decisive action **and**
  is in **neither** the rostered cast **nor** the scene's declared CHARACTERS —
  i.e. a name with no provenance in roster or scene.
- A scene-declared non-roster actor (the beast the key scene cast) acting at the
  turn is **expected**, not a breach — do not flag it.
- Keep flagging the real failures: a rostered character under a variant spelling,
  or a wholly invented name that appears in neither roster nor scene.

## Acceptance Criteria

- **Casting (A):** Given a synopsis whose pivotal scene turns on a non-roster
  actor (a beast that kills one principal and is killed by another), the
  generated `key_scene.text` lists that actor in **CHARACTERS** — a walkthrough
  test asserts the actor's name appears in the CHARACTERS block, not only in
  SUMMARY/BEATS.
- **Continuity (B):** When that scene-declared actor takes a decisive action on a
  turn, the director's `continuity` list does **not** flag it — a walkthrough
  test asserts no continuity flag names the scene-declared actor.
- **Guards still bite:** a rostered character under a variant spelling, and a
  name present in neither roster nor scene, are still flaggable — the existing
  FR-479/480 name-binding tests stay GREEN.
- Full walkthrough suite GREEN; `yamlgraph graph lint examples/dungeon_master/*.yaml`
  clean.

## Open Questions (for the Judge)

1. **Test shape under J3.** The harness mocks `execute_prompt`, so both prompts'
   outputs are fixture-controlled. The honest witnesses are (a) a render-level
   assertion that each prompt now *carries the scoped rule*, and (b) a behaviour
   assertion that a fixture scene declaring the non-roster actor survives roster
   reconciliation in `session`/`turn_ops` without a phantom flag. Is render +
   behaviour the right pair, or render-only for A and behaviour-only for B?
2. **Where does the breach test live — prompt or code?** Deliverable B asks the
   *model* to compare against the scene's CHARACTERS. A stricter alternative is
   to compute the breach in `turn_ops` (parse the scene's CHARACTERS, suppress
   any continuity flag whose subject is a scene-declared name). Lean prompt-only
   to stay in the J3 prototype regime, but the Judge may prefer the deterministic
   code-side filter given FR-480's lesson that the model under test honors such
   rules inconsistently.
3. **Scope of "non-roster actor."** Restrict to clearly non-human forces (beasts,
   weather, terrain) to keep the human-principal lock tight, or allow any
   synopsis-supported third party? Lean: synopsis-supported only, of any kind,
   since the synopsis is the authoritative source either way.

## Judgement (2026-06-14)

**Verdict: APPROVED, scope frozen.** The premise diagnosis is correct and the
two-boundary framing is the right one — fixing only `key_scene.yaml` would trade
a silent drop for a perpetual false alarm, so both boundaries must move together.
The split of responsibility between them, however, is not symmetric, and the FR's
own Open Question 2 names the seam. The judgement resolves it by the FR-482
precedent: **ask the model only for what only the model can do; enforce
everything deterministic in code.**

### Resolved: A is generative (prompt), B is deterministic (code)

- **Deliverable A — casting — is irreducibly generative.** Only the model, given
  the synopsis, can decide that Krog is a turn-driving principal and write him
  into CHARACTERS. There is no code path that can cast him. So A is a prompt
  reword in `key_scene.yaml`, and its effect is visible only in real runs (the J3
  harness mocks the scene). Accept that A's witness is weak by nature — a render
  assertion that the scoped rule is present, plus a behaviour test that a scene
  *already containing* the actor flows downstream intact. **In scope.**

- **Deliverable B — suppression — is deterministic, so it must not be left to the
  model.** FR-480's whole lesson is that `gemini-3.5-flash` honors roster rules
  inconsistently; trusting the same model to now *exempt* a scene-declared actor
  from its own continuity check repeats the mistake FR-482 rejected (M2). The
  enforceable guarantee is a **code-side filter in `turn_ops`**, dropped into the
  existing normalization pass in `invoke_turn` beside `_clamp_phase` and
  `_canonicalize_beats` — the established "normalize the director output at the
  boundary, deterministically" seam. The `turn_direct.yaml` clause reword stays
  IN as honesty polish (so the instruction is not self-contradictory), but the
  acceptance criterion is satisfied by the code filter regardless of what the
  model emits. **In scope, code-side.**

### The filter, made concrete (binds the enforcer)

`invoke_turn` already has the frozen `key_scene.text` in hand. The filter:

1. Parse the scene's **CHARACTERS** block the same way `parse_beats` parses
   BEATS: bullets between the `CHARACTERS:` label and the next uppercase section
   label; take each bullet's name (the text before the `—`/`-` dash).
2. Subtract the roster display names → the set of **scene-declared non-roster
   actor names** (e.g. `{"Krog"}`).
3. From `direction["continuity"]`, drop any flag whose text contains a
   scene-declared non-roster name (case-insensitive, word-boundary). What remains
   are flags about genuinely invented names with no provenance in roster or scene
   — the breach the guard exists to catch.

This is exact-name containment, not fuzzy matching — simpler than `_match_beat`,
and deterministic. **Accepted residual (J4):** a flag that mentions Krog for a
*different* legitimate reason (e.g. "Krog acts but the scene says he is already
dead") is over-suppressed. In the prototype this is acceptable; record it as a
known limit, do not engineer around it.

### Resolved Open Questions

1. **Test shape.** A → render assertion (scoped rule present in the rendered
   `key_scene` prompt) **+** behaviour (a fixture scene whose CHARACTERS includes
   the non-roster actor runs a turn and is not flagged). B → behaviour only, two
   directions: (i) a mocked director that emits a continuity flag naming the
   scene-declared actor → recorded `direction["continuity"]` excludes it; (ii) a
   mocked director that emits a flag naming a name absent from both roster and
   scene → that flag is **kept**. The "kept" assertion is mandatory — it is the
   witness that the filter narrows rather than silences.
2. **Prompt vs code for B.** Code, per above. Prompt reword included but not the
   guarantee.
3. **Scope of non-roster actor.** Accept the lean: synopsis-supported, of any
   kind. The prompt says "the synopsis names or clearly supports it"; no
   taxonomy of beast/faction/force is encoded.

### Constraints on the enforcer

- **No roster-id change.** Confirmed against `invoke_turn`: `roster` derives from
  `chars["roster"]` (character cards), never from the scene CHARACTERS. A
  scene-declared actor must **not** become a roster id, gain a character card, or
  enter `zip(roster, items)`. It exists only as a name the filter reads.
- **B lands in `turn_ops`, in the `invoke_turn` normalization pass**, after
  `_canonicalize_beats`, as a `_filter_continuity(direction, roster_names,
  key_scene_text)` helper mirroring the existing helpers' shape (mutate the
  `direction` dict in place, return `None`).
- **Guards still bite.** The existing FR-479/480 name-binding tests stay GREEN; a
  variant spelling of a rostered name and a no-provenance invented name remain
  flaggable.
- **J3 regime holds:** no CAP/REQ, no CI gate, no demo-log; walkthrough tests are
  the visibility harness. Changelog fragment required (`type: feat, scope:
  examples`, no `req:`). Diary entry with a **Seed:** on completion.

**Authority granted** for A (prompt) + B (code-side `_filter_continuity` +
`turn_direct.yaml` honesty reword), with the tests named above. Scope frozen;
the over-suppression residual is accepted, not to be engineered away.

## Implementation Status (2026-06-14)

Shipped **A (prompt) + B (code-side filter)** exactly as judged.

| Piece | Status | Where |
|---|---|---|
| A — key-scene CAST permits a pivotal non-roster actor | ✅ | `prompts/key_scene.yaml` (system + user CAST blocks) |
| B.1 — `_parse_scene_characters` (names from CHARACTERS block) | ✅ | `turn_ops.py` |
| B.2 — `_filter_continuity` (suppress scene-declared, keep phantom) | ✅ | `turn_ops.py`, wired into `invoke_turn` |
| Honesty reword of director continuity clause | ✅ | `prompts/turn_direct.yaml` |

**Decisions / notes:**

- **A is generative, B is deterministic.** `key_scene.yaml`'s CAST blocks now say
  the model MAY introduce one pivotal non-roster actor (beast / third party /
  force of nature) the synopsis supports and that drives the turn, named
  consistently across SUMMARY/CHARACTERS/BEATS/END; the human-principal lock and
  ~4–5 cap still hold. The enforceable guarantee is the code filter, not the
  prompt — per the FR-482 lesson that this model honors such rules inconsistently.
- **`_filter_continuity` mirrors the existing normalization seam.** It lands in
  `invoke_turn` right after `_canonicalize_beats`, mutating the `direction` dict
  in place (same shape as `_clamp_phase`). It parses the frozen scene's CHARACTERS
  via `_parse_scene_characters` (a sibling of `parse_beats`, reading names before
  the dash), subtracts the roster display names to get the scene-declared
  non-roster set, and drops only continuity flags that mention one of those names
  (exact-name, word-boundary, case-insensitive — not fuzzy). Every other flag is
  kept.
- **The Vane case (FR-479 test 11) stays a real breach.** `KEY_SCENE_TEXT` names
  "Naru" only in prose, with no CHARACTERS block, so `_parse_scene_characters`
  returns `[]`, the filter no-ops, and Naru's flag is preserved. Provenance is
  *being cast in the scene's CHARACTERS block*, not *being mentioned anywhere*.
- **Mandatory "kept" witness.** Test 20 proves a no-provenance name (`Zalor`,
  absent from both roster and scene) keeps its flag while the scene-cast `Krog` is
  suppressed — the witness that the filter narrows the breach definition rather
  than silencing it.
- **Accepted residual (J4):** a flag mentioning the scene actor for an unrelated
  legitimate reason is over-suppressed; recorded as a known limit, not engineered
  around.
- **Tests (FR-474 J3 visibility harness, no `req` tag):** prompt-render permission
  (gated under `{% if roster %}`), behaviour suppress-vs-keep through the turn
  re-read, `_parse_scene_characters` unit, `_filter_continuity` unit (incl. the
  prose no-op). Full suite **35 passed**; `ruff` + `ruff format` clean;
  `yamlgraph graph lint` clean on `key_scene.yaml` and `turn.yaml`.

**Seed carried forward:** A (casting) has no deterministic witness — only a real
`vertex`/`gemini-3.5-flash` run can show whether the model actually casts the
beast now that it is permitted. The filter (B) is proven; the prompt (A) is a
hypothesis until a live run confirms it. Worth a single real-run check before
trusting A.
