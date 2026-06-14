# FR-484: DM v2 — Post-Play "Final Cut" Pass (De-repeat + Elaborate the Arc)

**Priority:** MEDIUM
**Type:** Enhancement (DM v2 prototype; inherits FR-474 J3/J4 regime)
**Status:** Judged (2026-06-14). Scope frozen to **the additive Final Cut leaf**:
a terminal `final_cut` stage gated on `scene_complete`, composing one narration
from the whole arc, turns untouched. OQ2 → pass a deterministic climax marker;
OQ3 → per-turn de-establish tweak split out; OQ1 → structural tests + one cited
live run, no n-gram gate. See *Judgement*.
**Effort:** ~0.5 day (prototype, one prompt + one leaf graph + stage wiring + tests)
**Requested:** 2026-06-14
**Judged:** 2026-06-14
**Continues:** FR-477 (play loop), FR-479 (director phases), FR-482 (canonical
beats). Same J3 rules apply: **no CAP/REQ, no CI gate, no demo-log**; the
walkthrough tests under `examples/dungeon_master/tests/` are a visibility
harness, not a gate.

**Model under test:** `vertex` / `gemini-3.5-flash`.

## Summary

Once a scene is played to completion, add a single **Final Cut** pass that reads
the whole finished arc — the scene plan, every turn recap, the director's phases,
and the canonical BEATS — and weaves **one continuous scene narration** that (a)
states each standing fact once instead of re-establishing it every turn, and (b)
gives each canonical beat prose proportionate to its dramatic weight, elaborating
the climax instead of leaving it a terse line. The played turns remain the
immutable play-by-play; the Final Cut is a separate composed artifact.

## Value Statement

The reader gets a scene that reads like a scene, not a stack of independently
written turn summaries. Repeated establishing lines collapse to one; the pivotal
beat reads as pivotal. The play-by-play turns stay intact for anyone who wants the
move-by-move record — the Final Cut is the polished narration on top.

## Problem

Two defects, with different causes, both visible in run
`outputs/dungeon-master/6eae1ce5/`:

### 1. Repetition — a windowing artifact (forward-only, 3-turn window)

`running_scene` feeds the recap writer only the **last 3 recaps**
(`prior[...][-3:]`). A standing fact established early falls out of the window and
gets re-established every turn. Across `6eae1ce5`, the observer's position recurs
verbatim in spirit on five consecutive turns:

```
T1: "…while Lana watches from the ridges."
T2: "From her position on the rocky ledge, Lana watches the two hunters wrestle…"
T3: "Lana leans forward on her rocky ledge, keeping her eyes locked on…"
T4: "From her position on the rocky ledge, Lana shifts her gaze entirely to Taka…"
T5: "On the rocky ledge above, Lana remains silent, her gaze fixed on Taka."
```

The writer cannot dedupe what it cannot see. Widening the window only moves the
horizon; it does not give the writer the whole arc.

### 2. Shallowness — a global-emphasis problem (online, no view of the future)

Each recap is written **online**: at turn _n_ the model does not yet know which
later turn is the climax, so it cannot allocate emphasis. Every beat gets roughly
equal, terse prose — the decisive turn (the kill, the yielded claim) reads no
weightier than a connective grapple. Dramatic weight is only knowable once the
arc is complete, so **no per-turn fix can solve this** — it needs a pass that sees
the finished whole.

### Why a per-turn prompt tweak is insufficient (the honest alternative)

Repetition *alone* could be cheaply mitigated per-turn ("assume the reader has
read prior turns; do not re-establish standing facts"), and that may be worth
doing regardless. But it does nothing for shallowness, and it still writes each
turn blind to the arc's shape. The Final Cut is the structurally honest fix
because it is the only point at which the whole arc — and thus each beat's
relative weight — is visible.

## Proposed Solution

A new **terminal leaf**, the same shape as `synopsis` / `key_scene` (a weave
graph + prompt), that unlocks once the director reports `scene_complete` and
composes one continuous narration from the played turns. No mutation of any
reviewed turn.

### Deliverable — "Final Cut" compose leaf

- **A new `final_cut.yaml` leaf graph** (mirror `key_scene.yaml`: one `llm` node,
  `parse_json: false`, generous `max_tokens`) and a `prompts/final_cut.yaml`
  template.
- **The prompt reads the whole finished arc**, assembled in `turn_ops`:
  - the frozen `key_scene.text` (SUMMARY / CHARACTERS / BEATS / END),
  - **every** turn recap in order (not the 3-turn window — the whole point),
  - the per-turn director `phase` and cumulative `beats_satisfied` (FR-479/482),
    so the pass knows which turn is the climax and which beats matter.
- **It is instructed to:** state each standing fact once (no per-turn
  re-establishment); give each canonical BEAT prose proportionate to its weight,
  elaborating the climax beat; preserve the actual events and their order (it
  composes, it does not invent new beats); produce continuous scene prose, not a
  turn list.
- **A new terminal stage** `final_cut`, visitable once `scene_complete` is true
  (the point where `_accept_target` currently returns `None` to stop turn
  advance — FR-479 J5). Auto-drafted on entry like every other leaf (J5: never a
  blank splash). Reuses weave / edit / accept unchanged.
- **The played turns are not touched.** `turns[*].recap` stays the immutable
  play-by-play; `final_cut` is a separate `{text, reviewed}` entry. The accept
  contract on the turns is preserved.

### Explicitly out of scope

- **In-place rewrite of turn recaps** — rejected: it overwrites human-accepted
  text and destroys the play-by-play. The Final Cut is additive.
- **A per-turn "don't re-establish" prompt tweak** — a separate, cheaper concern;
  may be its own FR, but it does not deliver the elaborate-the-arc half and is not
  required for this one.
- **A deterministic repetition metric / n-gram gate** — see Open Questions; lean
  against, to avoid over-engineering the prototype.

## Acceptance Criteria

- **Unlocks at completion:** the `final_cut` stage is navigable only once a turn
  reports `scene_complete`; before then it is locked — a walkthrough test asserts
  both.
- **Consumes the whole arc:** the compose pass receives **every** turn recap (not
  the 3-turn window) plus the canonical beats — a test asserts the assembled
  prompt context contains a fact from the first turn and from the last.
- **Additive, non-destructive:** after composing and accepting the Final Cut, every
  `turns[*].recap.text` is byte-for-byte unchanged and still `reviewed: true` — a
  test asserts the turns are untouched.
- **Auto-drafted, reuses the generic controls:** entering `final_cut` lands on a
  populated, not-yet-reviewed draft; weave / edit / accept behave as for any leaf.
- Full walkthrough suite GREEN; `ruff check` clean; `yamlgraph graph lint` clean
  on `final_cut.yaml`.

## Open Questions (for the Judge)

1. **Witness for the generative half (the FR-483 A problem again).** "Less
   repetitive" and "climax elaborated" are model-judgement outcomes with no clean
   deterministic test under J3. The proposed witnesses are structural (unlocks at
   completion, consumes all turns, leaves turns untouched). Is that sufficient, or
   should the FR carry a *recorded live-run* citation (a real `vertex` Final Cut
   beside the play-by-play) as the acceptance witness for the prose-quality half —
   the live-run-acceptance idea seeded by FR-483? Lean: structural tests in code +
   one cited live run in the FR, no n-gram gate.
2. **Beat-proportionate emphasis — instruction or structure?** Should the prompt
   merely *ask* for proportionate emphasis (trusting the model), or should
   `turn_ops` pass an explicit "the climax is turn _k_" signal derived from the
   director `phase` sequence (the turn where `phase` first reaches `climax`)?
   Lean: pass the phase/beat signals as structured context and let the model
   compose — but the Judge may prefer an explicit climax marker given the model's
   inconsistency (FR-480/482 precedent).
3. **One leaf, or also a per-turn de-establish tweak?** Keep this FR to the
   additive Final Cut leaf only, and split the cheap per-turn "don't re-establish
   standing facts" prompt change into its own FR? Lean: yes — one concern per FR;
   the per-turn tweak is independently shippable and should not ride this one.
4. **Placement in the tree.** A terminal `final_cut` peer after the last turn, or
   a child of the Play branch? Lean: a terminal sibling leaf, unlocked by
   `scene_complete`, so the breadcrumb reads preplan → play → final cut.

## Judgement (2026-06-14)

**Verdict: APPROVED, scope frozen.** The diagnosis is the strongest part of the
FR and it is correct: repetition and shallowness are *different* defects with
*different* causes, and only shallowness is structurally unfixable per-turn. That
distinction earns the leaf. The additive shape — compose a new artifact, never
mutate the accepted turns — is the right call and is non-negotiable: in-place
rewrite would violate the turn accept contract and the FR-479 J5 "done, not
replayed" rule. Approved as the additive Final Cut leaf, with the four open
questions resolved below.

### Red Hat: is the pain real? Yes.

Run `6eae1ce5` shows the five-turn repetition verbatim in spirit and a climax
(the yielded claim, the kill) written no weightier than a connective grapple. The
premise is not hypothetical; the leaf is justified, not speculative
extensibility.

### Resolved: the deterministic seam vs the generative seam

The FR already half-sees this; the Judgement makes it binding. The leaf has two
parts, and they must not be confused (FR-482/483 precedent):

- **Deterministic (code, `turn_ops`):** assembling the arc context — gather
  **every** turn recap in order, the per-turn `phase` and cumulative
  `beats_satisfied`, the frozen `key_scene.text`, and a **derived climax marker**
  (see OQ2). This is a pure function over `doc`, fully unit-testable without an
  LLM. Name it e.g. `final_cut_context(doc) -> dict|str`.
- **Generative (prompt):** weaving that assembled context into continuous,
  de-repeated, beat-proportionate prose. Only the model can do this; it has no
  clean deterministic witness (OQ1).

The acceptance guarantees attach to the deterministic seam; the prose quality is
witnessed by a live run, not a unit test.

### Resolved Open Questions

1. **OQ1 — witness.** Structural tests in code **+ one cited live `vertex` run**
   in the FR's Implementation Status (the play-by-play beside its Final Cut), as
   the prose-quality witness. **No n-gram / repetition metric gate** — that is
   over-engineering for a prototype and would ossify a fragile heuristic. This
   graduates the FR-483 seed (live-run acceptance for the irreducibly-generative
   half) into practice; if it recurs a third time, it becomes a Scripture
   candidate.
2. **OQ2 — emphasis: structure, not trust.** Pass an **explicit deterministic
   climax marker** computed in `turn_ops`: the turn index where `phase` first
   reaches `"climax"`, falling back to the `scene_complete` turn when the model
   never emitted a climax phase. Do **not** ask the model to recompute which turn
   is the climax — code already knows it from the recorded phase sequence
   (FR-481 made phase monotonic precisely so it is trustworthy here). The model's
   job is prose weight; the *fact* of which beat is pivotal is deterministic and
   must be handed to it. This is the FR-482 law applied again: ask the model only
   for what only the model can do.
3. **OQ3 — split the per-turn tweak out. Confirmed.** This FR is the additive
   Final Cut leaf **only**. The cheap per-turn "assume the reader has read prior
   turns; do not re-establish standing facts" prompt change is a separate,
   independently-shippable concern — a future FR, not this one. One concern per
   FR. Do not let it ride.
4. **OQ4 — terminal sibling leaf. Confirmed.** A new top-level `doc["final_cut"]
   = {text, reviewed}` entry and a static `final_cut` `Stage`, gated on
   `scene_complete`, breadcrumb reading preplan → play → final cut. Not a child
   of Play.

### Constraints on the enforcer (binds scope)

- **Additive, non-destructive — enforced by test.** After composing and accepting
  the Final Cut, every `turns[*].recap.text` is byte-for-byte unchanged and still
  `reviewed: true`. This assertion is mandatory; it is the witness that the leaf
  is additive.
- **The leaf does not use `Stage.context`.** That mechanism passes the accepted
  text of *named static stages*; the turns are dynamic. Like the turn stages,
  `final_cut` gets its own invoke branch in `_autodraft` (and the weave path)
  that calls `turn_ops.final_cut_context(doc)` to build variables, rather than
  `_invoke_stage`. Name this seam explicitly in the wiring; do not try to force
  the turns through `context`.
- **Unlock gate is `scene_complete` on any played turn.** Add a
  `scene_is_complete(doc)` helper (mirroring `preplan_complete`) rather than
  re-deriving the predicate inline. `_accept_target` returns the `final_cut`
  target at the point it currently returns `None` for a completed turn (J5), and
  `_can_navigate` permits `final_cut` only when `scene_is_complete(doc)`.
- **Climax marker has a defined fallback** (resolved in OQ2): first `climax`
  phase turn, else the `scene_complete` turn. A unit test pins both paths.
- **`final_cut.yaml` mirrors `key_scene.yaml`:** one `llm` node,
  `parse_json: false`, generous `max_tokens` (the whole arc in, a full scene
  out). `yamlgraph graph lint` must pass.
- **Compose, do not invent.** The prompt preserves the actual events and their
  order and introduces no new beat; it reweights and de-repeats existing
  material. (No deterministic guard for this — it is part of the live-run
  witness.)
- **J3 regime holds:** no CAP/REQ, no CI gate, no demo-log; walkthrough tests are
  the visibility harness. Changelog fragment required (`type: feat, scope:
  examples`, no `req:`). Diary entry with a **Seed:** on completion.

### Acceptance Criteria (as judged — supersedes the draft list)

- `final_cut` is navigable **iff** `scene_is_complete(doc)`; locked before, open
  after — a test asserts both.
- `final_cut_context(doc)` includes **every** turn recap (a fact from the first
  turn and from the last), the canonical beats, and the derived climax marker — a
  pure-function test asserts all three, plus the climax-fallback path.
- After accept, all `turns[*].recap.text` are byte-for-byte unchanged and still
  reviewed — the mandatory non-destructive witness.
- Entering `final_cut` auto-drafts a populated, not-yet-reviewed entry; weave /
  edit / accept behave as for any leaf.
- Full walkthrough suite GREEN; `ruff` clean; `yamlgraph graph lint
  final_cut.yaml` clean.
- Implementation Status cites **one real `vertex` Final Cut run** beside its
  play-by-play as the prose-quality witness.

**Authority granted** for the additive Final Cut leaf with the deterministic
climax marker and the `final_cut_context` assembly seam. Scope frozen; the
per-turn de-establish tweak and any repetition-metric gate are **out**.

## Implementation Status (2026-06-14) — DONE

Enforced TDD; full DM walkthrough suite GREEN (29 passed), `ruff check` +
`ruff format` clean, `yamlgraph graph lint final_cut.yaml` clean.

### What was built

- **`api/turn_ops.py`** — three pure/async additions:
  - `climax_turn(doc) -> int`: the 1-based turn the scene turns on — first turn
    whose `phase` reached `"climax"`; fallback to the `scene_complete` turn; last
    resort the final turn. Pure over the recorded `direction` data (OQ2).
  - `final_cut_context(doc) -> dict`: the deterministic assembly seam — frozen
    `key_scene` text, **every** turn recap in order (phase-tagged, the climax
    marked), the canonical `parse_beats` list, and the `climax` marker. No LLM.
  - `invoke_final_cut(doc, instruction="", draft="")`: runs `final_cut.yaml` once
    over that context; returns cleaned prose; reads the turns, writes none.
- **`api/tree.py`** — `FINAL_CUT` / `FINAL_CUT_GRAPH` / `FINAL_CUT_SEED`
  constants, a static `final_cut` `Stage` (output_key `final_cut`, seeded so it
  auto-drafts), `scene_is_complete(doc)` (any turn's `scene_complete`; pure dict
  access, no `turn_ops` import → no cycle), and a terminal **Final Cut**
  breadcrumb peer shown once `scene_is_complete`.
- **`api/session.py`** — `_can_visit` permits `final_cut` iff `scene_is_complete`;
  `_accept_target` returns `final_cut` at the point a completed turn previously
  returned `None` (FR-479 J5); `_autodraft` and `weave` branch on the
  `final_cut` stage to call `invoke_final_cut` (its own invoke branch, **not**
  `Stage.context` — the turns are dynamic, as judged).
- **`final_cut.yaml`** — one `llm` node, `parse_json: false`, `max_tokens: 4000`,
  mirroring `key_scene.yaml`.
- **`prompts/final_cut.yaml`** — composes one continuous scene; instructed to
  state each standing fact once, weight the marked climax, preserve every
  canonical beat, and invent nothing.

### Tests (visibility harness, no `@pytest.mark.req` under J3)

- **22** `final_cut_context` consumes the whole arc (a fact from turn 1 **and**
  turn 9-equivalent), carries the canonical beats, and marks the climax.
- **23** `climax_turn` — phase path, `scene_complete` fallback, last-turn last
  resort.
- **24** Final Cut locked (absent + nav refused) before `scene_complete`,
  navigable after.
- **25** **Additive witness:** after compose+accept, every `turns[*].recap.text`
  is byte-for-byte unchanged and still reviewed; `final_cut` is its own reviewed
  artifact.
- **26** Entering `final_cut` auto-drafts a populated, not-yet-reviewed leaf.
- Test 10 extended: a completed scene now lands on `final_cut` (was: stayed on
  the last turn).

### Live `vertex` witness (OQ1 — the prose-quality half)

Composed the Final Cut of the cited run `outputs/dungeon-master/6eae1ce5/`
(9 turns, climax derived as **Turn 5**) against `vertex` / `gemini-3.5-flash`.
Full output: `logs/fr484-finalcut-live.log` (527 words). The two judged defects
are visibly fixed:

- **De-repetition.** The play-by-play re-established Lana's ledge on five
  consecutive turns ("From her position on the rocky ledge…" ×5). The Final Cut
  establishes it **once** at the open ("High on a nearby rocky ledge, Lana
  watched the basin"), lets it stand through the fight, and only returns to it as
  *new action* — her silent watch at the climax and her climb down at the
  resolution. The standing fact is stated once, not re-narrated.
- **Climax elaboration.** The terse per-turn climax ("Jarek verbally yields") is
  rendered as the dramatic peak it is — Taka holding the rope out of reach, the
  mud at Jarek's chin, the demanded yield and its breaking ("'I yield! She is
  yours!'") — given the most space and sharpest detail in the cut, exactly the
  proportional weight the marked climax instructs.

It composes only the events that happened, in order, and introduces no new beat —
the played turns remain the untouched move-by-move record beneath it.
