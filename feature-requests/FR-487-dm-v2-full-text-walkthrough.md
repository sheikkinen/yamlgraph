# Feature Request: DM v2 — Full-Text Scene Walkthrough (the Rendered Finish)

**Priority:** MEDIUM
**Type:** Enhancement (DM v2 prototype; inherits FR-474 J3/J4 regime)
**Status:** Judged (2026-06-14). **APPROVED, scope frozen** to a `walkthrough`
terminal leaf that renders one full-text passage per played turn from three
**already-authored** layers — the FR-485 cut spine, the FR-486 performance, and a
new whole-arc director-staging pass — validated 1:1 by the **reused**
`validate_cut_turns`. OQ1 → require the FR-485 cut **present** (not necessarily
reviewed); OQ2 → per-turn map; OQ3 → both scene `setting` + per-turn `staging`;
OQ4 → new whole-arc staging pass (not the turn-1 `establishing`); OQ5 → render
no `thinking`; OQ6 → whole-track edit only. **Ships after FR-486 and FR-485.**
Same J3 rules apply: **no CAP/REQ, no CI gate, no demo-log**. See *Judgement*.
**Requested:** 2026-06-14
**Continues:** FR-485 (the aligned `final_cut_turns` cut spine and its
`validate_cut_turns` alignment validator), FR-484 (the `final_cut_context` arc
assembly, the `scene_is_complete` gate, the additive terminal-leaf pattern).
**Depends on:** **FR-486** (the per-character `dialogue`/`expression`/`intent`
performance) — without it the full text would have to *invent* the spoken, acted
layer, the exact "compose, don't invent" violation this finish must avoid.
**Sequencing:** ships **after** FR-486 and FR-485 — it is their convergence point.
Same J3 rules apply: **no CAP/REQ, no CI gate, no demo-log**; the walkthrough
tests are a visibility harness, not a gate.

**Model under test:** `vertex` / `gemini-3.5-flash`.

## Summary

FR-484 dissolves the arc into one flowing scene; FR-485 keeps the turn skeleton as
a *polished play-by-play* — one de-repeated, climax-weighted segment per played
turn, aligned 1:1 and validated. Both are **summaries**: tight prose over the
recaps. This FR adds the **rendered finish** — the full text of the scene, turn by
turn, that no prior pass produces. For each played turn it takes the FR-485 cut
segment as the **structural reference** (the spine: order, what-happens, and
emphasis already decided), folds in that turn's **character performance** from
FR-486 (the actual `dialogue`, `expression`, and acted `intent` of each character),
and has the **director add the staging** — location, time, blocking — to produce
one full, playable passage per turn. The result is the scene as it would be *read
or performed*, not summarised: aligned 1:1 to the play-by-play, built only from
authored material, climax still heaviest.

## Value Statement

The three passes the prototype already has are all *compression* — the cut tells
you what happened on each turn in a sentence or two. None of them is the scene
itself: the spoken lines, the expressed gestures, the staged setting woven into
continuous full prose. This finish is the only artifact a player could actually
**read aloud or perform**. It is structurally honest precisely because every layer
it renders was authored upstream — the *what and the emphasis* by FR-485's cut, the
*voice and the body* by FR-486's performance, the *place* by the director — so the
renderer **composes** these into full text and **invents none of them**.

## Problem

A full rendering needs three things the play loop produced but never assembled
into prose: a per-turn structural spine, the per-turn cast performance, and the
setting. Each already exists; nothing has ever combined them.

1. **The cut is the spine, but it is only a spine.** FR-485 gives an aligned
   `[{n, text}]` where each `text` is a *polished summary* of the turn —
   de-repeated and climax-weighted, but still a recap, not the lines and actions
   playing out. It decides order and emphasis; it does not render the scene.

2. **The performance exists but is unrendered.** FR-486 captures, per character per
   turn, the `dialogue` they speak and the `expression` they show. Today that
   performance is inspectable on the turn card and then discarded at every finish —
   neither Final Cut weaves it. The full text is where authored voice and body
   finally appear on the page.

3. **The setting is thin and per-turn-1-only.** The director emits `establishing`
   (place, time, who is present) **only** on the opening turn (FR-479); there is no
   per-turn location/blocking, and the finishes carry almost no staging. A full
   text needs a setting header and the location/blocking *deltas* as the scene
   moves — which is a job for the director (the eye that judges the scene state),
   not the per-character actors.

The decisive architectural gift: **alignment composes.** The cut is 1:1 to the
played turns (FR-485) and the performance is keyed per turn (FR-486), so the full
text is *also* turn-aligned — one full passage per played turn `n`. The same
`validate_cut_turns` post-condition that guards the cut guards this finish for
free; a misaligned full text is a defect, surfaced, not padded.

## Proposed Solution

A new terminal leaf — `walkthrough` — gated on `scene_is_complete`, that reads the
FR-485 cut spine and the FR-486 performance, runs one director-staging pass, then
renders the full text of each turn. Reuse the FR-484/485 leaf, gate, breadcrumb,
weave/edit/accept, and the `validate_cut_turns` alignment validator **unchanged**.

### The deterministic seam vs the generative seam (FR-482/483/484/485 law)

- **Deterministic (code, `turn_ops`):**
  - **Assemble per-turn render inputs.** For each played turn `n`, gather a bundle
    `{n, cut_text, cast: [{name, dialogue, expression, intent}], staging}` from
    the existing structures — `doc["final_cut_turns"]` segment `n` (the spine),
    `turn_intents(doc, chars, n)` (FR-486 performance), and the director-staging
    pass keyed by `n`. Pure function over existing data; no LLM.
  - **Reuse `validate_cut_turns`.** The rendered output is a list of full-text
    segments; code asserts it maps 1:1 onto the played turns — exactly one passage
    per turn, `n`-set equal to the played set, none missing/invented/duplicated.
    **Raises** on divergence (Commandment 6; the FR-485 post-condition, reused
    verbatim — no new validator).
  - **Additive artifact.** `doc["walkthrough"]` = `{setting, turns: [{n, text}]}`,
    separate from `doc["final_cut"]`, `doc["final_cut_turns"]`, and the played
    `turns[*]` — all of which stay byte-for-byte immutable (the mandatory
    non-destructive witness, as FR-484/485).
- **Generative (prompts):**
  - **Director staging pass** — over the whole arc once, the director returns the
    scene `setting` (location, time, who is present — the curtain-up header) and a
    per-turn `staging` note (location/blocking deltas as the scene moves). This is
    the director's job (FR-479's eye), now applied to the finish rather than each
    live turn.
  - **Per-turn full-text render** — for each turn, expand the cut segment into full
    prose: stage it with the turn's `staging`, speak the characters' `dialogue`,
    show their `expression`, and play out the acted `intent`, **preserving the
    cut's emphasis** (the climax turn stays the heaviest passage) and **inventing
    nothing** not present in the cut, the performance, or the staging.

  Why the render can be **per-turn (a map), not whole-scene**: FR-485's cut already
  did the *global* work — de-repetition and climax emphasis are baked into the
  spine. So each turn's full text is a *local dressing* of an already-correct,
  already-de-repeated segment with that turn's own performance and staging. The
  global coherence rides in on the spine; the renderer stays local. (Whole-scene
  single-call is the alternative — OQ2.)

### The leaf, gate, and editing unit are reused

- The `walkthrough` stage is a sibling terminal leaf beside `final_cut` and
  `final_cut_turns`, with the same `scene_is_complete` gate and a breadcrumb peer.
- It reads `doc["final_cut_turns"]` as its spine — so it is gated additionally on
  that cut being present (OQ1: require it *reviewed*, or render from its text if
  present).
- The whole track is the unit of weave/edit/accept for v1; per-turn re-render
  ("redo Turn 3's full text") is **out of scope** (OQ6), consistent with FR-485
  OQ4 — one concern per FR.

### Explicitly out of scope

- **Per-turn re-render / per-turn edit instructions** — a separate, independently
  shippable concern (OQ6).
- **In-place rewrite of the recaps, the cut, or the performance** — rejected, same
  as FR-484/485: the full text is purely additive.
- **A de-repetition / dialogue-coverage string gate** — lean against (ossifies a
  fragile heuristic on a prototype); quality witnessed by a live run (OQ-witness).
- **Rendering `thinking`** — the private interior is never put on the page; only
  its public projection (`expression`), the `dialogue`, the acted `intent`, and the
  staging are rendered (consistent with FR-486 OQ3).

## Acceptance Criteria (draft — the Judge supersedes)

- [ ] A `walkthrough` terminal leaf, gated on `scene_is_complete` and on the
      FR-485 cut being available, with a breadcrumb peer beside the two Final Cuts.
- [ ] The rendered output is validated 1:1 against the played turns via the reused
      `validate_cut_turns`; a misaligned render raises (no silent pad/truncate).
- [ ] `doc["walkthrough"] = {setting, turns: [{n, text}]}` is additive; the recaps,
      `final_cut`, `final_cut_turns`, and per-turn performance stay byte-for-byte
      immutable (a mandatory non-destructive test).
- [ ] Each turn's full text incorporates that turn's authored `dialogue` and
      `expression` (FR-486) and the cut segment's content (FR-485); the director
      supplies a scene `setting` and per-turn `staging`.
- [ ] One live `vertex` witness: a turn whose full text contains a character's
      actual `dialogue` line, an `expression`-derived gesture, and a director
      location cue, with the climax turn the heaviest passage; recorded as
      structural facts in the Implementation Status.
- [ ] Tests added (the walkthrough visibility harness; no `@pytest.mark.req`).

## Open Questions (for the Judge)

- **OQ1 — spine dependency.** Require `final_cut_turns` **reviewed** before the
  walkthrough unlocks, or render from its cut text whenever present? Lean: require
  the cut present (it is the spine); reviewed-vs-present is the Judge's call.
- **OQ2 — render shape.** Per-turn map (lean: the cut already carries global
  de-repetition/emphasis, so the render is local) vs one whole-scene call (keeps
  cross-turn prose flow in one context). The Judge picks.
- **OQ3 — staging shape.** Scene-level `setting` only, per-turn `staging` only, or
  both? Lean: both — one curtain-up header + per-turn location/blocking deltas.
- **OQ4 — director-staging source.** A new whole-arc director-staging pass (lean —
  the per-turn `establishing` is turn-1-only and lacks later location shifts) vs
  reusing the stored `establishing`. The Judge picks.
- **OQ5 — performance privacy.** Confirm only `dialogue`/`expression`/`intent` +
  staging are rendered and `thinking` stays private. Lean: yes.
- **OQ6 — editing unit.** Whole-track weave/edit/accept for v1; per-turn re-render
  out of scope (own FR). Lean: yes, consistent with FR-485 OQ4.

## Alternatives Considered

- **Fold the full text into FR-485's cut** (make the cut itself full prose).
  Rejected: the cut's value is being a *checkable, de-repeated summary*; full text
  is a different artifact with different inputs (performance + staging) and a
  longer length budget. Two finishes, two purposes (the FR-484/485 precedent).
- **Render full text without FR-486** (let this pass invent dialogue). Rejected:
  inventing voice and gesture the player never authored is the compose-don't-invent
  violation; FR-486 exists precisely so this pass renders authored material.
- **A whole-scene single call instead of a per-turn map** (OQ2). Plausible —
  preserves cross-turn flow — but the cut spine already carries global coherence,
  so the local per-turn render is the cheaper default; left to the Judge.
- **Reuse the per-turn `establishing` for setting instead of a new director pass**
  (OQ4). Rejected as the default: `establishing` is turn-1-only and has no later
  location/blocking; a whole-arc staging pass is what a moving scene needs.

## Related

- `examples/dungeon_master/api/turn_ops.py` — `validate_cut_turns` (reused),
  `turn_intents` (FR-486 performance), the new render-input assembly.
- `examples/dungeon_master/api/tree.py` / `session.py` — the new `walkthrough`
  terminal leaf, gate, breadcrumb, weave/autodraft wiring.
- `examples/dungeon_master/final_cut_turns.yaml` + `prompts/final_cut_turns.yaml`
  — the FR-485 cut spine this finish references.
- FR-484, FR-485 — the two summary finishes; FR-486 — the captured performance.

## Judgement (2026-06-14)

**Verdict: APPROVED, scope frozen.** This is the convergence the whole DM finish
arc has been building toward, and — critically — it adds almost no new machinery:
its guarantee is *inherited*. The cut is 1:1 to the played turns (FR-485) and the
performance is keyed per turn (FR-486), so the full text is turn-aligned by
construction and the **same `validate_cut_turns` post-condition guards it for
free.** That reuse is the strongest thing in the FR and I bind it: no new
validator, no second alignment contract.

### Red Hat — does a third terminal finish justify itself?

The sharpest objection: we now have `final_cut`, `final_cut_turns`, and
`walkthrough` — three terminal leaves on a prototype. Is the walkthrough a
real third artifact or vanity? It is real. The two Final Cuts are *compression* —
tight summaries over the recaps. The walkthrough is the only artifact a player
could **read aloud or perform**: full prose, spoken lines, staged setting,
different length budget, different inputs (performance + staging that the cuts
never touch). Different reader, different purpose — the same justification that let
FR-485 coexist with FR-484. Three finishes on a prototype exploring the finish
space is acceptable; if a fourth is ever proposed, *that* one bears the burden.

### The honest core — it renders only authored material

The FR's structural honesty is its load-bearing virtue and I make it the binding
constraint: every layer the walkthrough renders was authored upstream — *what and
emphasis* by FR-485's cut, *voice and body* by FR-486's performance, *place* by
the director's staging pass. The render **composes** these and **invents none**.
This is the whole reason FR-486 was approved as its prerequisite. A render that
fabricates a line or a gesture absent from the cut/performance/staging is a
defect, not a flourish.

### The risk the FR underweights — cross-turn prose continuity

I accept the per-turn map (OQ2) — the cut spine already carries the *global*
work (de-repetition, climax weight), so each turn's full text is a local dressing
and the global coherence rides in on the spine. But a per-turn map has a real
cost the FR mentions only in passing: **independently rendered passages can read
disjointed** — no connective tissue between Turn 2's close and Turn 3's open. My
resolution is not to abandon the map but to **make the staging pass carry the
continuity**: the per-turn `staging` deltas (location/blocking *changes*) are
exactly the seams between passages, and the whole-arc staging pass sees the full
sequence, so it can author transitions the local render then honours. **Binding:**
the staging pass is whole-arc (OQ4) precisely so it owns cross-turn continuity;
the live witness must show two adjacent passages reading as continuous scene, not
two islands. If they read as islands, the fix is a richer staging delta, not a
retreat to a whole-scene render (which remains a *future* option, not this FR).

### Dependency ordering — binding

FR-487 **must not enforce before FR-486 is shipped** (the performance it renders)
and depends on FR-485 (done). The enforcer reads `turn_intents` carrying
`dialogue`/`expression`; if those are absent the walkthrough would invent — the
forbidden path. Build order: FR-486 → FR-487. A test must assert the render
incorporates the FR-486 fields, so the dependency is mechanically visible.

### Open questions — resolved

- **OQ1 (spine dependency):** require the FR-485 cut **present** (its segments
  exist), not necessarily *reviewed*. The cut is the spine; gating on present is
  enough, and forcing a review step couples two finishes more than needed.
- **OQ2 (render shape):** per-turn map. The cut carries global coherence; the
  render stays local. Whole-scene single call is a future alternative, out here.
- **OQ3 (staging shape):** both — one scene-level `setting` (curtain-up header)
  **and** per-turn `staging` deltas. The deltas are the continuity seams (above).
- **OQ4 (staging source):** a new whole-arc director-staging pass. The stored
  turn-1 `establishing` is insufficient — it has no later location/blocking and
  cannot author cross-turn transitions.
- **OQ5 (privacy):** render `dialogue` / `expression` / acted `intent` / staging
  only. `thinking` is never put on the page (consistent with FR-486 OQ3).
- **OQ6 (editing unit):** whole-track weave/edit/accept for v1; per-turn
  re-render is its own future FR (consistent with FR-485 OQ4).

### Binds on the enforcer

1. **Reuse `validate_cut_turns` verbatim** — no new alignment validator. The
   render is a list of full-text segments validated 1:1 against the played turns;
   misalignment raises (Commandment 6).
2. TDD: the render-input assembly (`{n, cut_text, cast, staging}` per turn) is a
   pure function, tested first without an LLM.
3. Additive artifact `doc["walkthrough"] = {setting, turns: [{n, text}]}`; a
   mandatory non-destructive test asserts the recaps, `final_cut`,
   `final_cut_turns`, and per-turn performance stay byte-for-byte immutable.
4. The staging pass is **whole-arc** and owns cross-turn continuity (OQ3/OQ4).
5. One live `vertex` witness recorded as structural facts: a turn's full text
   contains a character's actual `dialogue`, an `expression`-derived gesture, a
   director location cue; the climax turn is the heaviest passage; two adjacent
   passages read continuous.
6. Reuse the FR-484/485 leaf, gate, breadcrumb, weave/edit/accept; lints + graph
   lint clean. Enforce **after** FR-486.

**Authority granted** for the `walkthrough` leaf with the reused alignment
validator, the whole-arc staging pass, and the per-turn map render over
FR-485 + FR-486 inputs. Per-turn re-render, a whole-scene single-call render,
any rewrite of the recaps/cuts/performance, rendering `thinking`, and a
de-repetition string gate are **out**.

## Implementation Status (2026-06-14) — DONE

Enforced under TDD, **after** FR-486 shipped (the performance it renders). RED
first: five `walkthrough` tests failed (render-input assembly, the cut-present
gate, aligned auto-draft, authored-layer render, additive immutability). GREEN:
**42 passed** (37 prior + 5 new), `ruff check` clean, `ruff format` clean,
`yamlgraph graph lint` clean on `staging.yaml` + `walkthrough.yaml`.

**Changes:**
- `api/turn_ops.py` — `walkthrough_render_inputs` (pure: one `{n, cut_text,
  setting, staging, climax, cast}` bundle per played turn, `cast` carrying only
  `name`/`dialogue`/`expression`/`intent` — **`thinking` dropped at the assembly
  boundary**, OQ5); `walkthrough_staging_context`; `invoke_walkthrough_staging`
  (whole-arc setting + per-turn deltas); `render_walkthrough`; `invoke_walkthrough`
  (staging → per-turn render map → **reused `validate_cut_turns`**, no new
  validator); `_cut_spine` (raises if the FR-485 cut is absent — the dependency
  made mechanical); `_ordered_render_texts` (see boundary fix below).
- `examples/dungeon_master/staging.yaml` + `prompts/staging.yaml` — the whole-arc
  director-staging pass returning `{setting, staging:[{n,text}]}`.
- `examples/dungeon_master/walkthrough.yaml` + `prompts/walkthrough.yaml` — a
  `map` over the per-turn bundles rendering one full passage each; the prompt
  weights the passage by the `climax` flag.
- `api/tree.py` — `WALKTHROUGH` constant/stage, `cut_present` gate, a breadcrumb
  peer shown once the scene is complete **and** the cut is present.
- `api/session.py` — `weave`/`_autodraft`/`_can_visit` branches; additive
  `doc["walkthrough"] = {setting, turns:[{n,text}], text, reviewed}`.

**Boundary fix witnessed by the live run (not the mock).** A `map` node collecting
a `parse_json: false` string sub-result wraps each item as `{"_map_index": i,
"value": <text>}` (`map_compiler`), and list order is not guaranteed. The mock
returned clean strings, so the unit tests passed *even though* the wrapper dict
repr was leaking into the prose — the substring assertions survived the pollution.
The live witness exposed `{'_map_index': 2, 'value': '...'}` in the rendered text.
Fixed at the boundary with `_ordered_render_texts` (sort by `_map_index`, unwrap
`value`), and added a regression assertion (`"_map_index" not in resp.text`) so a
mock-green-but-polluted render can never recur. *(Trap: the mock hid a real
boundary shape; the witness is what caught it — demo_vs_test, normalize-at-boundary.)*

**Climax emphasis.** The first live run rendered all passages at roughly equal
length (climax not heaviest) because the local per-turn render had no climax
signal — "emphasis rides on the spine" was insufficient when the spine segments
were uniform. Added a per-bundle `climax` boolean (from `climax_turn(doc)`) and an
explicit weight instruction in the render prompt.

**Live vertex witness** (neutral flood-ledge arc, `gemini-3.5-flash`, structural
facts only): setting 64 words with a location cue; turn n-set `[1,2,3]`; **every**
turn's full text contained that character's authored dialogue line, an
expression-derived gesture, and a second character's line — all composed, none
invented; the private `thinking` ("reads the ledge") appeared nowhere. The
**climax turn (3) was the heaviest passage** — 170 words vs 94/93 for the rising
turns. The Turn 2 → Turn 3 seam read continuous: Turn 2 closed on *"The herd goes
free. That's the only deal."* and Turn 3 opened mid-confrontation (*"Kara lunges
forward with everything she has, her teeth bared…"*) — one scene, not two islands
(the Judge's continuity bind). No `_map_index` bookkeeping leaked.

**Alignment composed for free:** the cut spine is 1:1 to the played turns (FR-485),
so the walkthrough is turn-aligned by construction and the same
`validate_cut_turns` post-condition guards it — the strongest thing the Judge bound,
and it required no new code.
