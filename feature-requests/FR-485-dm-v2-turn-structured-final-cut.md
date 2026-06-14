# FR-485: DM v2 — Turn-Structured Final Cut (Polished Play-by-Play)

**Priority:** MEDIUM
**Type:** Enhancement (DM v2 prototype; inherits FR-474 J3/J4 regime)
**Status:** **DONE** (2026-06-14). Enforced TDD; the alignment validator written
RED first (test 27: happy path + dropped/duplicated/mislabelled → raises), then
GREEN. Full DM walkthrough suite GREEN (33 passed), `ruff` clean, `yamlgraph graph
lint final_cut_turns.yaml` clean, and one live `vertex` witness recorded below.
Judged (2026-06-14): **APPROVED, scope frozen** to the additive
turn-structured `final_cut_turns` leaf whose centre is a deterministic **alignment
validator** (one segment per played turn, emitted `n`-set == played set, raises on
mismatch). Reuses the FR-484 arc assembly (`final_cut_context`, `climax_turn`) and
`scene_is_complete` gate; writes a *separate* `doc["final_cut_turns"]` artifact
that must not clobber FR-484's `doc["final_cut"]`. OQ1 → separate leaf; OQ2 →
coexist, distinct key; OQ3 → raise, no position re-keying; OQ4 → whole-track edit
only; OQ5 → live-run witness, no string gate. See *Judgement*.
**Effort:** ~0.5 day (prototype; reuses the FR-484 arc-assembly + gate; one new
prompt mode, one structured output schema + alignment validator, stage wiring,
tests)
**Requested:** 2026-06-14
**Continues:** FR-484 (the additive Final Cut leaf, the `final_cut_context`
assembly seam, the `climax_turn` marker, the `scene_is_complete` gate). Same J3
rules apply: **no CAP/REQ, no CI gate, no demo-log**; the walkthrough tests under
`examples/dungeon_master/tests/` are a visibility harness, not a gate.

**Model under test:** `vertex` / `gemini-3.5-flash`.

## Summary

FR-484's Final Cut composes the whole arc into **one continuous scene** — its
defining instruction is literally *"the turn boundaries should dissolve into one
flowing scene."* That is right for a reader who wants a short story. This FR adds
the complementary axis: a Final Cut that **keeps the turn structure** — it emits
one polished segment **per played turn**, aligned 1:1 with the play-by-play, in
turn order, while still spending the whole-arc knowledge it gained (FR-484) on the
two things the online turn writer could not do: state each standing fact once, and
weight the climax turn. The result is a *polished play-by-play* — the move-by-move
record, cleaned of windowing repetition and given proportional emphasis, with its
turn skeleton intact.

## Value Statement

The reader keeps the navigable, move-by-move turn record — each polished turn sits
beside its raw recap for direct comparison and per-turn addressing — but the
repetition the 3-turn window forced is gone and the pivotal turn now reads as
pivotal. The dissolve-into-prose cut (FR-484) and the keep-the-skeleton cut (this
FR) are two finishes of the same played arc, for two different readers.

## Problem

FR-484 fixed the two play-loop defects (windowing repetition, online shallowness)
by **dissolving the turns**. That dissolution is also a cost:

1. **It discards the turn alignment.** The continuous cut cannot be put beside the
   play-by-play turn-for-turn; the reader who wants "what changed on Turn 3,
   cleanly written" loses the mapping. The move-by-move addressability — the thing
   the play loop exists to produce — is erased in the finish.

2. **Its de-repetition is only eyeball-checkable.** Because the output is one
   blob, "the ledge is established once, not five times" can only be judged by
   reading. With the turn skeleton preserved, the same claim becomes *mechanically
   locatable*: a standing fact should appear in exactly the one polished turn that
   introduces it.

3. **It is not the natural editing unit.** A continuous cut can only be re-woven
   whole. A turn-structured cut can, in principle, be corrected one turn at a time
   ("redo Turn 3") — though that granularity is **out of scope here** (OQ4).

The arc knowledge FR-484 assembled (`final_cut_context`: every recap in order,
phase tags, the derived climax marker) is exactly what a per-turn rewrite needs —
it is the *only* point at which a turn can be rewritten knowing what comes after
it. So the same whole-arc pass can produce a turn-structured finish; it is a
prompt-mode + output-shape change over a seam that already exists, not new
machinery.

## Proposed Solution

Reuse the FR-484 leaf shape, the `scene_is_complete` gate, and the
`final_cut_context` arc assembly **unchanged**. Change two things: the prompt's
instruction (keep the skeleton instead of dissolving it) and the **output shape**
(structured, per-turn, deterministically alignable instead of one blob).

### The deterministic seam vs the generative seam (FR-482/483/484 law)

This is binding and must not be confused — the new risk lives entirely in the
deterministic seam:

- **Deterministic (code, `turn_ops`):**
  - **Reuse** `final_cut_context(doc)` and `climax_turn(doc)` verbatim — the arc
    is assembled identically; only the consumer differs.
  - **New: alignment validator.** The model now returns a *list of N segments*.
    Code must verify the structured output maps 1:1 onto the played turns —
    **exactly one segment per turn, contiguous `n` values `1..N`, every played
    turn covered, none invented.** This is a pure function over
    `(played_turns, model_output)` and is fully unit-testable without an LLM. A
    misaligned cut is a **defect**, surfaced — not silently padded or truncated
    (Commandment 6: no silent fallback; OQ3).
- **Generative (prompt):** rewrite each turn's prose given the whole arc — in the
  turn that *introduces* a standing fact, establish it; in later turns, assume the
  reader has read prior turns and do **not** re-establish it; give the marked
  climax turn the most space and sharpest detail. Per-turn, but arc-aware. No
  clean deterministic witness for prose quality (OQ5).

### Deliverable — turn-structured Final Cut mode

- **Structured output.** `final_cut.yaml` gains (or a sibling `final_cut_turns.yaml`
  carries — OQ1) a `parse_json: true` node with an inline schema, e.g.
  `Cut{ turns: list[CutTurn] }`, `CutTurn{ n: int, text: str }`. The typed shape
  is what makes alignment a deterministic post-condition rather than a string
  parse.
- **The prompt** (a new `prompts/final_cut_turns.yaml`, or a mode branch — OQ1):
  same whole-arc input as FR-484, but instructed to **keep the turn skeleton** —
  return one polished segment per played turn, in order, keyed by turn number;
  establish each standing fact in the turn that introduces it and not again;
  weight the climax turn; compose, do not invent; preserve every canonical BEAT
  across the set.
- **The artifact stays additive.** The played `turns[*].recap.text` remain
  byte-for-byte immutable (the mandatory non-destructive witness, as FR-484). The
  polished track is a separate structure — `doc["final_cut"].turns` (or a parallel
  `final_cut_turns`), each `{n, text}` aligned to a played turn — never written
  back onto the recaps.
- **The leaf gate, breadcrumb, and weave/edit/accept are reused** from FR-484; the
  whole track is the unit of weave/edit/accept for v1 (per-turn editing is OQ4).

### Explicitly out of scope

- **Per-turn re-weave / per-turn edit instructions** ("redo Turn 3 only") — a
  separate, independently-shippable concern; its own future FR (OQ4). One concern
  per FR.
- **In-place rewrite of the raw recaps** — rejected, same as FR-484: it destroys
  the play-by-play. The polished track is additive.
- **A string/n-gram de-repetition *gate*** — lean against, same reasoning FR-484
  used (ossifies a fragile heuristic on a prototype). De-repetition is witnessed
  by a live run, not gated (OQ5).
- **Changing the FR-484 continuous cut's behaviour** — whether this mode replaces
  or coexists with it is OQ2; either way the continuous cut's *prompt* is not
  silently altered.

## Acceptance Criteria (draft — the Judge supersedes)

- **1:1 alignment, enforced by code.** The turn-structured cut yields exactly one
  polished segment per played turn, with contiguous `n` values `1..N` covering
  every turn and inventing none — a pure-function alignment test asserts count,
  contiguity, and coverage.
- **Misalignment is surfaced, not patched.** A test drives a mock whose output
  drops/duplicates a turn and asserts the validator raises (or the single defined
  recovery — OQ3), never silently emits a misaligned track.
- **Additive, non-destructive.** After compose + accept, every
  `turns[*].recap.text` is byte-for-byte unchanged and still `reviewed: true` —
  the mandatory witness, carried over from FR-484.
- **Gated and auto-drafted.** Navigable iff `scene_is_complete(doc)`; entering it
  auto-drafts a populated, not-yet-reviewed track; weave / edit / accept behave as
  for any leaf.
- **Live witness.** Implementation Status cites **one real `vertex` run** showing
  the polished per-turn track beside the raw recaps: the standing fact established
  in exactly one turn (not re-established downstream), and the climax turn given
  visibly more weight than a connective turn.
- Full walkthrough suite GREEN; `ruff check` clean; `yamlgraph graph lint` clean
  on the new/modified leaf graph.

## Open Questions (for the Judge)

1. **One leaf with two modes, or two leaves?** Add a turn-structured mode onto the
   existing `final_cut.yaml` (a flag/variant the leaf selects), or ship a separate
   `final_cut_turns.yaml` + `prompts/final_cut_turns.yaml` peer? Lean: a **separate
   leaf graph + prompt**, because the output schema differs fundamentally
   (`parse_json: true` structured list vs FR-484's `parse_json: false` blob) and
   mixing modes in one node muddies both — but the Judge may prefer one leaf with a
   mode switch to avoid a second stage.

2. **Replace or coexist with the FR-484 continuous cut?** Does the turn-structured
   cut *replace* the continuous Final Cut (one finish, simpler tree), or do both
   ship as alternative finishes (richer, but two artifacts and a choice in the UI)?
   Lean: **coexist as sibling leaves** — the continuous cut is already shipped and
   live-witnessed (FR-484); replacing it discards proven work, and the two finishes
   genuinely serve different readers. The Judge weighs prototype simplicity against
   that.

3. **Alignment-failure handling under a flaky model.** On a count/coverage
   mismatch, raise (Commandment 6 — surface the defect) vs one bounded retry vs
   best-effort fill. Lean: **raise** — a misaligned polished play-by-play is a
   defect, not a degraded-but-acceptable result; a silent pad/truncate would be the
   plausible-wrong-answer trap. The Judge may permit a single retry given the J3
   prototype model's known inconsistency (FR-480/482 precedent).

4. **Editing granularity.** Whole-track weave/edit/accept only (v1), or per-turn
   edit ("redo Turn 3")? Lean: **whole-track only this FR**; per-turn editing is a
   distinct, independently-shippable concern — its own future FR. One concern per
   FR; do not let it ride.

5. **De-repetition witness — structural assertion or live-run only?** With the turn
   skeleton preserved, "the standing fact appears in exactly one polished turn" is
   *partly* mechanically checkable (a chosen establishing phrase present in ≤1
   segment). Add a light assertion, or keep de-repetition to the live-run witness
   as FR-484 did? Lean: **live-run witness only** — a string-presence dedup check
   ossifies a fragile heuristic (the same argument FR-484 used to reject the n-gram
   gate); the *alignment* post-condition is the deterministic guarantee, prose
   quality stays a live-run citation. The Judge may want one cheap structural
   assertion as a tripwire.

## Alternatives Considered

- **Widen the live recap window / per-turn "don't re-establish" tweak (FR-484
  OQ3).** Rejected there and here: it cannot allocate emphasis (the turn writer is
  online and cannot know the climax), and widening the window only moves the
  horizon. The finish must see the whole arc — which is exactly what this mode
  reuses from FR-484.
- **In-place rewrite of the raw recaps into a polished turn log.** Rejected:
  overwrites human-accepted text, destroys the play-by-play, breaks the turn accept
  contract (FR-479 J5). The polished track must be additive.
- **Parse the continuous FR-484 blob back into turns with code.** Rejected: there
  is no reliable deterministic turn boundary in dissolved prose (the FR-484 prompt
  *deliberately* erases it); reconstructing turn alignment from a blob is the
  regex-fourth-exclusion trap. The model must emit the structure, validated by
  code — not have code re-derive it.

## Judgement (2026-06-14)

**Verdict: APPROVED, scope frozen** — but the *justification* is re-seated. The
FR sells itself on a reader-need ("someone wants Turn 3 cleanly written"), and
that framing is the **weakest** part: for a prototype, "a second, turn-aligned
finish" is exactly the kind of speculative extensibility the doctrine purges. The
reader-need alone would earn a rejection. What earns the FR is the part it states
almost in passing: **keeping the turn skeleton converts FR-484's eyeball-only
guarantee into a deterministic post-condition.** FR-484's continuous cut can only
be checked by reading; this cut produces a structure whose *alignment to the
played arc* is a pure function code can assert. The deliverable is therefore not
"a nicer finish" — it is **a Final Cut with a deterministic witness FR-484 could
not have.** Approved on that basis, with the five OQs resolved below and scope
bound to it.

### Red Hat: is the pain real? Partly — and the honest half is the one that earns it.

- **The addressability pain (OQ-framing) is thin.** No live evidence is cited that
  a reader of `6eae1ce5` wanted turn-for-turn alignment; it is asserted, not shown.
  On its own this is unchallenged-premise. It does **not** earn the leaf.
- **The structural-honesty pain is real and is the justification.** FR-484's
  Implementation Status had to witness de-repetition by *quoting prose and reading
  it* ("established once at the open… lets it stand"). That is the
  `gate_checks_shape_not_substance` smell inverted — the substance could only be
  judged by eye because the output had no checkable structure. The turn-aligned
  cut removes that: 1:1 alignment is a mechanical post-condition. **That** is a
  defect-class improvement, not a preference. The leaf is justified by its witness,
  not by its readership.

### Resolved: the deterministic seam vs the generative seam (binding)

All the **new** risk lives in code, and that is where the FR's value concentrates:

- **Deterministic (code, `turn_ops`):**
  - **Reuse `final_cut_context(doc)` and `climax_turn(doc)` verbatim.** The arc is
    assembled identically to FR-484; only the consumer changes. No new assembly.
  - **New: the alignment validator — the heart of this FR.** A pure function over
    `(played_turns, model_output)` asserting **exactly one segment per played
    turn, the emitted `n`-set equal to the played `n`-set, none missing, none
    invented.** Fully unit-testable without an LLM. This validator *is* the
    deliverable's reason to exist; it must be written and tested first (TDD RED),
    and it must **raise** on mismatch (see OQ3) — never repair.
- **Generative (prompt):** rewrite each turn arc-aware — establish each standing
  fact in the turn that introduces it and not again, weight the marked climax
  turn, compose without inventing. No clean deterministic witness for prose
  quality (OQ5); witnessed by a live run.

The acceptance guarantee attaches to the alignment validator. Prose quality is a
cited live run, as FR-484.

### Resolved Open Questions

1. **OQ1 — separate leaf. Confirmed.** Ship `final_cut_turns.yaml` +
   `prompts/final_cut_turns.yaml` as a distinct leaf, **not** a mode switch on
   `final_cut.yaml`. The output contract differs at the schema level
   (`parse_json: true` structured `list[CutTurn]` vs FR-484's `parse_json: false`
   blob); folding two output shapes into one node muddies both and invites a
   conditional in the leaf that the three-layer rule resents. Two leaves, two
   prompts, two schemas — clean.

2. **OQ2 — coexist, with a distinct doc key. Confirmed, with a binding
   constraint.** The two finishes serve different consumers and FR-484's continuous
   cut is already shipped and live-witnessed; replacing it discards proven work for
   no gain. They coexist as sibling leaves. **Constraint:** the turn-structured
   artifact is a *separate* top-level entry — `doc["final_cut_turns"] = {turns:
   [...], reviewed: bool}` — and must **not** overload or clobber FR-484's
   `doc["final_cut"] = {text, reviewed}`. Two keys, two breadcrumb leaves, both
   gated on `scene_is_complete`. (This resolves the latent clobber the FR left
   implicit by writing "`doc["final_cut"].turns` (or a parallel `final_cut_turns`)"
   — it is the parallel key, not a sub-field, precisely so coexistence cannot
   collide.)

3. **OQ3 — raise. No retry, no fill. Confirmed and made non-negotiable.** A
   count/coverage mismatch is a **defect**, and a silently padded or truncated
   polished play-by-play is the exact `plausible_wrong_answer` trap — output that
   passes a shape check while being structurally wrong. Commandment 6: no silent
   fallback; surface the fault. The J3 model's inconsistency (FR-480/482) is an
   argument for a *better prompt and a clear error*, not for masking the failure.
   **Additional constraint:** the validator checks the model's emitted `n` values
   against the played set and raises on any divergence; it must **not** silently
   re-key segments by position. Re-keying by position assumes the model emitted in
   order and would convert "the model got alignment wrong" into a hidden guess —
   the downstream-fix trap. Validate the labels; do not paper over them.

4. **OQ4 — whole-track only. Confirmed.** v1 weaves / edits / accepts the whole
   `final_cut_turns` track as one unit, reusing the generic controls. Per-turn
   editing ("redo Turn 3 only") is a distinct, independently-shippable concern —
   its own future FR. One concern per FR; it does not ride this one.

5. **OQ5 — live-run witness only for de-repetition; no string tripwire.
   Confirmed.** Tempting as it is to exploit the new structure for a dedup
   assertion, choosing *which* phrase represents a "standing fact" is itself a
   heuristic — the same fragile, ossifying choice FR-484 rejected the n-gram gate
   to avoid, merely relocated. The deterministic dividend this FR buys is
   **alignment**, and that is asserted in full; prose-level de-repetition stays an
   irreducibly-generative outcome, witnessed by one cited live run. Do not add a
   phrase-presence dedup check; it would be a tripwire pretending to be a
   guarantee.

### Constraints on the enforcer (binds scope)

- **TDD on the validator first.** The alignment validator is the FR's reason to
  exist. Write it RED first — a test driving a mock that drops a turn, duplicates a
  turn, and mislabels an `n`, each asserting the validator **raises** — then GREEN.
  This is the witness that the leaf is structurally honest where FR-484 was only
  eyeballed.
- **Reuse, do not re-implement, the arc assembly.** `final_cut_context(doc)` and
  `climax_turn(doc)` are consumed unchanged. The only new pure code is the
  validator and the structured-output plumbing. If you find yourself re-assembling
  the arc, stop — you are duplicating FR-484.
- **Separate artifact key, enforced by test.** `doc["final_cut_turns"]` is its own
  entry; a test asserts composing/accepting it leaves both `doc["final_cut"]` (the
  FR-484 continuous cut, if present) and every `turns[*].recap.text` byte-for-byte
  unchanged and still reviewed. **The non-destructive witness is mandatory** — it
  is carried over from FR-484 and extended to cover the sibling cut.
- **The leaf does not use `Stage.context`.** Like the turns and like FR-484's
  `final_cut`, `final_cut_turns` gets its own invoke branch in `_autodraft` and
  `weave` that calls the new `turn_ops` seam (e.g. `invoke_final_cut_turns(doc)`)
  to build variables and validate the structured output, not `_invoke_stage`.
- **Gate reused, not re-derived.** Navigability is `scene_is_complete(doc)` —
  reuse the FR-484 helper; do not inline the predicate. Breadcrumb reads
  preplan → play → final cut → final cut (turns), or the two finishes as peers —
  the enforcer picks the cleaner ordering but both are gated identically.
- **`final_cut_turns.yaml` lints.** One `llm` node, `parse_json: true`, an inline
  schema `Cut{ turns: list[CutTurn{ n: int, text: str }] }`, generous
  `max_tokens`. `yamlgraph graph lint` must pass.
- **Compose, do not invent.** Same as FR-484 — preserve the actual events and
  order, every canonical BEAT recognisable across the set, no new beat. Part of the
  live-run witness, no deterministic guard.
- **J3 regime holds:** no CAP/REQ, no CI gate, no demo-log; walkthrough tests are
  the visibility harness. Changelog fragment required (`type: feat, scope:
  examples`, no `req:`). Diary entry with a **Seed:** on completion.

### Acceptance Criteria (as judged — supersedes the draft list)

- The validator yields **exactly one segment per played turn**, emitted `n`-set
  equal to the played `n`-set, full coverage, none invented — a pure-function test
  asserts count, label-equality, and coverage.
- The validator **raises** on a dropped turn, a duplicated turn, and a mislabelled
  `n` — three tests, one per failure mode; it never silently re-keys by position
  nor emits a misaligned track.
- After compose + accept, `doc["final_cut"]` (if present) **and** every
  `turns[*].recap.text` are byte-for-byte unchanged and still reviewed — the
  mandatory non-destructive witness, extended to the sibling cut.
- `final_cut_turns` is navigable **iff** `scene_is_complete(doc)`; entering it
  auto-drafts a populated, not-yet-reviewed track; weave / edit / accept behave as
  for any leaf.
- Full walkthrough suite GREEN; `ruff` clean; `yamlgraph graph lint
  final_cut_turns.yaml` clean.
- Implementation Status cites **one real `vertex` run** showing the polished
  per-turn track beside the raw recaps: a standing fact established in exactly one
  turn (not re-established downstream), and the climax turn visibly weightier than
  a connective turn.

**Authority granted** for the turn-structured `final_cut_turns` leaf with the
alignment validator as its centre, the separate `doc["final_cut_turns"]` artifact,
and reuse of the FR-484 arc assembly and gate. Scope frozen; per-turn editing
(OQ4), any de-repetition string gate (OQ5), and replacement of the FR-484
continuous cut (OQ2) are **out**.

## Implementation Status (2026-06-14) — DONE

Enforced TDD; full DM walkthrough suite GREEN (33 passed), `ruff check` +
`ruff format` clean, `yamlgraph graph lint final_cut_turns.yaml` clean.

### What was built

- **`api/turn_ops.py`** — three additions, the validator written RED first:
  - `validate_cut_turns(played_turns, segments) -> list[dict]`: **the centre of
    the FR.** A pure function asserting exactly one segment per played turn, the
    emitted `n`-set equal to the played set, none missing / invented /
    duplicated. **Raises `ValueError`** on any divergence — it validates the
    model's emitted `n` labels and never silently re-keys by position, pads, or
    truncates (OQ3; Commandment 6). Returns the segments ordered by played order.
  - `render_cut_turns(segments) -> str`: a readable `Turn n — …` join for the
    generic edit control (the structured `segments` carry the guarantee; the text
    is only the rendering).
  - `invoke_final_cut_turns(doc, instruction, draft) -> list[dict]`: runs
    `final_cut_turns.yaml` once over **the reused** `final_cut_context(doc)` plus
    draft + instruction, reads the structured `{turns: [...]}` output, and returns
    `validate_cut_turns(...)`. Reads the played turns; writes none.
- **`api/tree.py`** — `FINAL_CUT_TURNS` / `_GRAPH` / `_SEED` constants, a static
  `final_cut_turns` `Stage` (output_key `cut`, seeded so it auto-drafts), and a
  **sibling** terminal breadcrumb peer "Final Cut (Turns)" shown beside the FR-484
  "Final Cut" once `scene_is_complete` (the two finishes coexist — OQ2).
- **`api/session.py`** — `_can_visit` permits both terminal leaves iff
  `scene_is_complete` (reused gate, not re-derived); `weave` and `_autodraft`
  branch on `final_cut_turns` to call `invoke_final_cut_turns`, store the validated
  structure under `entry["turns"]` and the rendered view under `entry["text"]` —
  its own invoke branch, **not** `Stage.context` (the turns are dynamic, as
  judged).
- **`final_cut_turns.yaml`** — one `llm` node, `parse_json: true`, `max_tokens:
  4000`, state_key `cut: dict`.
- **`prompts/final_cut_turns.yaml`** — keeps the turn skeleton: one polished
  segment per played turn, establishing each standing fact in the turn that
  introduces it (not re-establishing it downstream), weighting the marked climax,
  inventing nothing. Carries an `output_schema` of `{turns: [{n:int, text:str}]}`.

### A boundary bug caught during enforcement (normalize at entry)

The first live run failed with `KeyError '"turns"'`: the prompt rendering picks
Jinja2 only when the template contains `{{`/`{%`, else falls back to
`str.format(**vars)` (`executor_base.format_prompt`). The system prompt had a
literal JSON example `{"turns": […]}` and no Jinja markers, so `.format` read
`{"turns": …}` as a replacement field. Fixed by describing the shape in words —
the `output_schema` already enforces the structure. The defect lived at the
template boundary, normalized there (the one law).

### Tests (visibility harness, no `@pytest.mark.req` under J3)

- **27** `validate_cut_turns` — happy path (out-of-order input returned in played
  order) **and** raises on a dropped turn ("missing"), a duplicated turn
  ("duplicat"), and an invented label ("invented"). The RED-first witness.
- **28** `final_cut_turns` locked (absent + nav refused) before `scene_complete`,
  navigable after, breadcrumb reads "Final Cut (Turns)".
- **29** Entering it auto-drafts an **aligned** track — `[s.n] == [1,2,3]`, every
  segment non-empty, not yet reviewed.
- **30** **Additive witness, extended:** after composing+accepting the cut, both
  the FR-484 `doc["final_cut"]` (composed+accepted first) **and** every
  `turns[*].recap.text` are byte-for-byte unchanged and still reviewed — the two
  finishes coexist without clobber.

### Live `vertex` witness (OQ5 — the prose-quality half)

The cited DM runs are seeded toward disallowed adult content and the provider
**intermittently returned empty content** for them — against which the validator
correctly **raised** (`missing turns [1…9]`) rather than emit a misaligned track,
exactly the defect-surfacing behaviour OQ3 demands. The generative witness was
therefore taken on a clean, neutral arc (a flood-ledge standoff, 4 turns, climax
turn 3) against `vertex` / `gemini-3.5-flash`. Structural facts only (prose not
reproduced); full log `logs/fr485-witness.log`:

```
PLAYED turns:   [1, 2, 3, 4]
POLISHED turns: [1, 2, 3, 4]
ALIGNED 1:1:    True
CLIMAX turn:    3
  Turn 1: 33 words
  Turn 2: 20 words
  Turn 3: 88 words  <- CLIMAX
  Turn 4: 22 words
climax 88 words vs avg other 25 words
segments mentioning 'ledge': 1/4 (raw recaps: 4/4)
segments mentioning 'ris*':  1/4 (raw recaps: 4/4)
```

Both judged outcomes are visible:

- **1:1 alignment on a real run** — the deterministic post-condition the FR exists
  to buy (its advantage over FR-484's eyeball-only blob) holds against the live
  model, validated by code.
- **Climax weight** — the marked turn 3 got 88 words vs an average of 25 for the
  connective turns (~3.5×), exactly the proportional emphasis the prompt instructs.
- **De-repetition** — the standing facts (the ledge, the rising water) appear in
  **4/4** raw recaps but only **1/4** polished segments each: established once in
  the turn that introduces them, then assumed read — the windowing repetition
  removed while the turn skeleton is kept.
