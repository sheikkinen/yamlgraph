# Feature Request: FR-564 DM v3 M4b — realize (beat-driven turn instruction, end-to-end)

**Priority:** HIGH
**Type:** Feature
**Status:** Enforced (2026-06-22)
**Effort:** 4–5 days
**Requested:** 2026-06-22

## Summary

Close the v3 loop: let the validated `PlotPlan` **steer the prose**, not just gate the cast.
FR-563 (M4a) made the plan *attachable* and activated the exclusion seam — the director now *excludes*
a presumed-dead character. M4b makes the plan *drive* what the surviving cast plays: the authored
`Function` for each chapter/turn becomes the **turn instruction** fed to the existing doc-assembled
`TurnRequest`, with the beat's effects focalized through belief (Arnulf's clan grieves BECAUSE
`believes(clan, not alive(Arnulf))`, while world-truth `alive(Arnulf)` is untouched). This is the
**second half of milestone M4** (design §6b + §7), and the milestone where floodmark renders six
chapters with **no continuity break in the witness gap-suite**.

## Value Statement

DM maintainers get the payoff of the entire v3 arc: a book whose emotional and causal beats are
*authored once, proven unspellable-if-wrong, and then realized faithfully* — instead of hoping the
turn LLM reconstructs intent from prose. The floodmark saga, which has defeated v2 all month, renders
end-to-end with the presumed-dead reveal landing at its authored chapter and the grief/guilt affect
arc closing on schedule. The recognition gates (`reversal_pack_gap`, `composition_gap`,
`unplayable_beat_gap`, dead-character prose) go green not by post-hoc detection but because the plan
that drove the prose was proven coherent before a word was written.

## Problem

After FR-563 the plan is attached and **read by exactly one consumer** — `compile_opening_onepager`'s
exclusion seam. The turn engine itself is still **plan-blind**:

- `turn_ops.invoke_turn` assembles a `TurnRequest` entirely from the **doc** (cast from the reviewed
  roster, `scene` from `running_scene`, `beats` from `chapter_beat_list`, `extras` from
  protected/gone). The `instruction` field is whatever the **stage caller** passed
  (`doc_ops.compose_stage(instruction=...)`) — today derived from the v2 outline, never the plan.
- The authored `Function` (kind + effects + observers) for a chapter/turn — the *intent* of the beat
  — never reaches the turn LLM. The plan proves the beat is spellable but does not tell the cast to
  spell it.

**The design §6b sketch is stale and must be corrected.** It shows:

```python
# design §6b — DOES NOT MATCH the as-built engine
return TurnRequest(cast=chapter_cast(plan, fn.chapter),
                   protected=protected_set(plan),          # NO such field
                   belief_context=_focalize(fn, plan),     # NO such field
                   extras={"function_id": fn.id, ...})      # extras is TurnExtras, not a dict
```

The **as-built FR-557** `TurnRequest` is `cast / scene / turn_n / instruction / beats /
prior_direction / extras: TurnExtras(protected, gone_this_chapter)`. There is **no** `protected` or
`belief_context` field on `TurnRequest`, `protected` lives *inside* `TurnExtras`, and one `Function`
is **one beat** while a `TurnRequest` runs the **whole cast for one turn** — so a `Function →
TurnRequest` wholesale builder is a category error. Realize must be **additive over the doc-driven
assembly**, mirroring how the exclusion seam is additive over `must_exclude`, not a replacement for
`invoke_turn`.

## Proposed Solution

One realize function (instruction derivation, not request construction), one additive wiring at the
stage→turn boundary, the §6b design correction, and the end-to-end witness render. **No change** to
the four checks, the projection, the exclusion seam, or the `TurnRequest`/`TurnExtras` schema.

### 1. `realize.py` — beat → instruction (`api/plot/realize.py`, pure)

```python
def beat_instruction(plan: PlotPlan, chapter: int) -> str:
    """Render the authored beat(s) scheduled at `chapter` as a turn instruction.

    Selects the Function(s) whose `chapter` matches, in `ordered_functions` order (a chapter may
    carry MORE than one beat -- floodmark ch6 has both `Fr` reveal and `Ff` reconciliation -- so the
    directives are concatenated in that order). Renders kind + effects + focalized belief into a
    directive string the turn LLM plays. Belief is focalized: the instruction states what THIS beat's
    observers BELIEVE, never world-truth the realizer cannot author. Returns '' when no beat maps to
    `chapter` -- so an un-planned chapter is byte-for-byte unchanged.
    """
```

**No `turn_n` (J2 option (a)).** A `Function` carries `chapter`, not a turn index, and the
turn↔beat scheduling policy stays deferred (*Out of Scope*); shipping a `turn_n` parameter whose
semantics are deferred would be incoherent. `beat_instruction(plan, chapter) -> str` renders the
whole chapter's authored beat(s); turn placement within a chapter is a successor milestone.

Pure, leaf (no turn-engine import — the A1 island direction holds: `api.plot` is imported *by* the
turn path, never the reverse). It produces a **string**, the one field the engine already exposes for
caller intent.

**Focalization read (J5 option (a)).** `exclusion_set` collapses the belief timeline to a
`set[str]` and discards the observer dimension a focalized instruction needs, so realize cannot
"reuse" it. Add one small **pure** helper to `project.py`:

```python
def belief_at(plan: PlotPlan, chapter: int) -> dict[tuple[str, str], bool]:
    """The latest (observer, char) -> held belief about `alive` at chapter <= `chapter`.

    The same belief-timeline walk `exclusion_set` does (initial_belief, then `ordered_functions`
    whose chapter <= c), but KEEPING the observer dimension instead of collapsing to a set. Pure,
    leaf, engine-free. `beat_instruction` reads this so grief renders from `believes(clan, not
    alive(Arnulf))`, never from world-truth.
    """
```

The read stays in the leaf `project.py`; `realize.py` does not re-walk the timeline itself.

### 2. Additive wiring inside `invoke_turn` (J6)

The exclusion-seam precedent is additive **inside the consumer** (`compile_opening_onepager` unions
into `must_exclude`). Mirror it: do the merge **inside `invoke_turn`** (`turn_ops.py`, at the
`instruction=instruction` assignment on the `TurnRequest`, ~line 208), where the function already
holds `doc`, `cid`, `n`. Gate on `chapter_nav.attached_plot_plan(doc)` exactly like the seam:

- plan attached → `instruction = _merge(instruction, beat_instruction(plan, _chapter_index(doc, cid)))`
  (beat intent *appended to* the stage instruction, never silently replacing it);
- no plan → the `instruction` parameter is passed through **byte-for-byte** (the FR-560/563
  dormancy invariant continues to hold).

Wiring inside `invoke_turn` (not `compose_stage`) is deliberate: `compose_stage` receives
`instruction` as a parameter from *its* caller and does not hold the plan context, whereas
`invoke_turn` already reads `doc`/`cid`/`n` and constructs the `TurnRequest` — the same
consumer-owns-the-merge shape as the exclusion seam. The merge is additive and reversible: drop the
attach (FR-563) and the whole lane goes dormant again.

### 3. Correct the stale design §6b

Rewrite §6b to the real signature: `beat_instruction(plan, chapter) -> str` feeding the
**existing** `TurnRequest.instruction`, with a note that `protected`/cast/beats stay doc-assembled and
`extras` is the closed `TurnExtras`. Remove the phantom `protected=`/`belief_context=`/`extras={dict}`
sketch. (Doc-only; rides this FR since it is the FR that builds the real thing.)

## Acceptance Criteria (RED first)

RED commit (`SKIP=pytest`) lands failing tests; GREEN makes them pass. Example tests are
requirement-exempt (FR-474 J3): **no** `@pytest.mark.req`, **no** capability YAML. The ACs name the
real floodmark beat-bearing chapters (J1): `F1` villainy **ch1** (opens `loss`, flips the clan's
belief to dead), `Fr` reveal **ch6** + `Ff` reconciliation **ch6** (chapters 2–5 carry no beat).

1. **Beat renders to instruction.** `beat_instruction(floodmark, 1)` returns a non-empty directive
   naming the **ch1 villainy** intent (the loss / presumed-dead belief flip), focalized on belief
   (the clan now *believes* Arnulf dead), not a world-truth death. `beat_instruction(floodmark, 6)`
   returns a directive naming **both** ch6 beats in `ordered_functions` order (the reveal then the
   reconciliation), the reveal focalized on the *belief* flipping back — not a world-truth revival.
2. **Un-planned chapter is empty.** `beat_instruction(floodmark, 3)` (a chapter with no beat)
   returns `''`.
3. **Wiring is additive + gated.** With a plan attached, the `instruction` reaching the `TurnRequest`
   in `invoke_turn` *contains* the beat directive merged with (appended to) the stage instruction;
   with **no** plan attached, the `instruction` is byte-for-byte the v2 value (regression).
4. **Belief focalization, not world revival.** During the belief window (believes-dead from `F1`@ch1
   until `Fr`@ch6), the rendered intent for an Arnulf observer reads grief from `believes(clan, not
   alive(Arnulf))` (asserted via `belief_at(floodmark, ch)` giving `(Clan, Arnulf) -> False` for
   ch1–5 and `True` at ch6); no instruction asserts world-truth `alive(Arnulf)` before ch6.
5. **(a) Machinery (pytest, no LLM).** The deterministic half — beat rendering (AC1/AC2), the
   additive+gated merge (AC3), focalization (AC4), and the dormancy regression — runs in the gated
   DM suite with **no live LLM**. This is the RED-first witness.
   **(b) End-to-end render (demo witness, not pytest).** A live floodmark render with the plan
   attached is exercised by the demo path (`generate_and_review.sh` → committed `demo-output.log`,
   demo-gate), and the **real** continuity gates are run on the rendered doc asserting `gap_count == 0`
   for the plot-lane gates: `reversal_pack_gap`, `unplayable_beat_gap` (chapter_gaps),
   `composition_gap`, `seam_entrance_gap`, and dead-character prose via
   `collect_dead_character_prose_violations` (J4 — the AC5 names in the original draft do not exist).
   The render path (`generate_and_review.sh`) currently exits non-zero (terminal); it **must be green**
   before it can serve as the AC5b witness — surface any breakage as a blocker, not a skip.
6. **Design §6b matches code.** The §6b sketch is rewritten to the real `beat_instruction(plan,
   chapter)` signature; no phantom `TurnRequest` fields (`protected=`/`belief_context=`/`extras={dict}`)
   remain (grep-asserted in the doc).

## Fixtures

Reuse `api/plot/floodmark.py`. The end-to-end render uses the existing floodmark premise +
`generate_and_review.sh` path; the witness is the existing gap-test suite, not a new fixture (M4b
proves the *whole lane*, so its witness is the production gates, per design §7 "witness metrics").

## Out of Scope

- **Realizing `eff_world` writes back to the doc.** The realizer renders effects as *already decided*
  (design §6b: "never writes back to the plan"); world-state mutation stays the v2 turn ledger's job.
- **Multi-beat-per-turn scheduling policy.** M4b renders a **chapter's** authored beat(s) into the
  turn instruction (concatenated in `ordered_functions` order when a chapter carries more than one —
  floodmark ch6 has `Fr` + `Ff`); a richer turn↔beat scheduler (placing distinct beats on distinct
  turns within a chapter) is a future milestone. No `turn_n` parameter ships in M4b (J2).
- **Widening the alphabets.** `FunctionKind`/`AffectKind` stay the floodmark subset.

## Dependencies

- **FR-563 (Enforced):** the attach seam + `attached_plot_plan` the wiring gates on.
- **FR-557 (Enforced):** the `TurnRequest`/`TurnExtras`/`invoke_turn` contract realize feeds —
  *the real one*, against which the stale §6b sketch is corrected.
- **FR-560/561/562 (Enforced):** the validated plan + belief ledger realize focalizes from.

## Risks

- **Re-deriving the stale sketch.** The §6b `to_turn_request(fn, plan) -> TurnRequest` shape is a
  category error against the as-built engine; coding it would fight `invoke_turn`'s doc-driven
  assembly. Mitigated by specifying `beat_instruction -> str` (the one caller-intent field the engine
  exposes) and by criterion 6 forcing the doc correction.
- **Instruction merge masks v2 intent.** A naive replace would drop the v2 stage instruction.
  Mitigated by the additive `_merge` (criterion 3) — beat intent *augments*, never replaces.
- **Witness flakiness.** The end-to-end render is an LLM path; assert the *gap metrics* go green
  (deterministic gates), not prose equality, and run the gap-suite as the witness rather than a
  bespoke assertion.

## Milestone closure

M4b is the **last** milestone of `design-v3-plot-model-implementation.md` §7. On enforcement the v3
plot lane is feature-complete: author (M4a) → attach (M4a) → validate (M0–M3) → exclude (M1) →
**realize (M4b)**, end-to-end, with the floodmark defect class retired at the source.

---

## Judgement (2026-06-22)

**Verdict: APPROVE WITH CONDITIONS.** The milestone is real and correctly framed, and its hardest
claim — that the design §6b `to_turn_request(fn, plan) -> TurnRequest` sketch is a category error —
holds against the code: `TurnRequest` is `cast / scene / turn_n / instruction / beats /
prior_direction / extras: TurnExtras(protected, gone_this_chapter)` (turn_engine.py:44), there is
**no** `protected`/`belief_context` field, `protected` lives inside `TurnExtras`, and `invoke_turn`
(turn_ops.py:173) assembles the whole-cast request from the doc while one `Function` is one beat — so
the additive `beat_instruction -> str` reframing is the correct shape. The wiring boundary checks out:
`doc_ops.compose_stage(..., instruction=)` (doc_ops.py:339) is the sole feeder of
`invoke_turn(instruction=...)`, and `instruction` is the one caller-intent field the engine already
exposes (`TurnRequest.instruction: str = ""`). The projection helpers realize leans on exist
(`ordered_functions`, `chapter_cast`, `exclusion_set` in project.py). **But the acceptance criteria
are factually wrong against the floodmark fixture, AC5 cannot run in the gated suite, and the
witness-gate names do not exist.** Seven conditions (J1–J7) must be folded into the FR body before
enforce; authority is granted once they are.

**J1 — fold (blocking). The ACs reference chapters that carry no beat.** floodmark's functions are
`F1` villainy **chapter 1**, `Fr` reveal **chapter 6**, `Ff` reconciliation **chapter 6** (floodmark.py).
Chapter 3 is **empty**. Yet AC1 asserts `beat_instruction(floodmark, 3, 1)` returns "the chapter-3
beat's intent (the reveal)" — there is no chapter-3 beat and the reveal is at chapter 6. By the spec's
own rule ("Returns '' when no beat maps") that call must return `''`, contradicting AC1. AC4 asserts a
beat-bearing "chapter-1–5 instruction," but only chapter 1 carries a beat; 2–5 are empty. Rewrite the
ACs to the real beat-bearing chapters: AC1 → the **villainy at ch1** (opens `loss`, flips the clan's
belief to dead) and/or the **reveal at ch6** (flips belief back); AC2's empty case (ch99, or ch3) is
fine as the `''` witness; AC4 → belief-focalized grief during the **belief window** (believes-dead
from F1@ch1 until Fr@ch6) tied to a chapter that actually carries a beat or to the focalization read
directly, not to `beat_instruction` at an empty chapter.

**J2 — fold (blocking). Resolve the `turn_n` contradiction.** `Function` carries `chapter`, not a turn
index, and *Out of Scope* explicitly defers "multi-beat-per-turn scheduling policy" — the very policy
that would give `turn_n` meaning. Shipping `beat_instruction(plan, chapter, turn_n)` with a parameter
whose semantics are deferred is incoherent. Choose one: **(a)** drop `turn_n` — signature
`beat_instruction(plan, chapter) -> str` renders the chapter's authored beat(s), turn placement
deferred to a successor; or **(b)** define the trivial deterministic turn↔beat mapping now (and remove
it from Out of Scope). Recommended: **(a)** — it matches the deferral and keeps M4b minimal. Note ch6
has **two** beats (`Fr` + `Ff`), so even (a) must say how a multi-beat chapter renders (concatenate in
`ordered_functions` order is the obvious answer); state it.

**J3 — fold (blocking). AC5 cannot be a gated unit test — make it a demo witness (the FR-563 J2 path).**
The DM pre-commit/CI suite is **API-free** and runs the full DM suite on every commit; a six-chapter
floodmark render needs a live LLM, is slow, and is non-deterministic. AC5 as written ("a floodmark
render ... passes the continuity gap-suite") cannot live in that suite. Split it: **AC5a (machinery,
pytest)** — the deterministic half (beat rendering, additive merge, focalization, dormancy) runs in
the gated suite with no LLM; **AC5b (end-to-end witness, demo)** — the live render is exercised by the
demo path (`generate_and_review.sh` → committed `demo-output.log`, demo-gate), running the gap
functions on the rendered doc and asserting `gap_count == 0` for the plot-lane gates, with the log in
the diff. This is exactly the J2a resolution FR-563 used for its production-path witness. (Note: the
terminal shows `generate_and_review.sh` currently exiting non-zero — the render path must be green
before it can serve as the AC5b witness; surface any breakage as a blocker, not a skip.)

**J4 — fold. The witness-gate names in AC5 do not exist.** AC5 lists `test_fact_reversal_gap`,
`test_beat_coverage_gap`, `test_dead_character_prose` — none are real. The actual gates are
`reversal_pack_gap` (chapter_gaps), `unplayable_beat_gap` (chapter_gaps), `composition_gap`
(composition_gap.py:77), `seam_entrance_gap` (seam_entrance.py:132), and dead-character prose via
`collect_dead_character_prose_violations` / `detect_dead_character_prose_violations`
(prose_continuity.py). The *Value Statement* already names them correctly; reconcile AC5 to that real
set so enforce does not chase phantom tests.

**J5 — fold. Name the focalization read in Frozen Scope.** The FR says realize "reuses the projection's
belief reads (the same `(observer, alive, char)` ledger)," but `exclusion_set` **collapses** that
timeline to a `set[str]` of excluded characters and discards the observer dimension a focalized
instruction needs. No exported helper returns "what does observer O believe about char C at chapter
N." Decide and record: realize either (a) adds a small **pure** helper to `project.py` (e.g.
`belief_at(plan, chapter) -> dict[(observer, char), bool]`) — named in Frozen Scope so the read stays
in the leaf and does not balloon — or (b) walks `ordered_functions` belief effects inside `realize.py`
itself. Pick one; do not leave "reuses the projection's reads" pointing at a read that does not exist.

**J6 — fold. Pin the exact wiring site.** "At the stage→turn boundary" is ambiguous between
`compose_stage` (which receives `instruction` as a parameter from *its* caller) and `invoke_turn`
(which already holds `doc`, `cid`, `n` and constructs the `TurnRequest`). The exclusion-seam precedent
is additive **inside the consumer** (`compile_opening_onepager` unions into `must_exclude`). Mirror it:
do the additive merge **inside `invoke_turn`** (turn_ops.py:208, where `instruction=instruction` is set
on the `TurnRequest`), gated on `chapter_nav.attached_plot_plan(doc)`, so a plan-less run passes
`instruction` byte-for-byte untouched (the FR-560/563 dormancy invariant). State the function + line
and the `_merge` rule (beat intent appended to, never replacing, the stage instruction — AC3).

**J7 — fold (minor, same pass). Fix the inaccurate scope note.** *Out of Scope* claims "the floodmark
fixture is one salient beat per chapter"; chapter 6 carries **two** (`Fr` + `Ff`). Correct it (it ties
to J2's multi-beat rendering) so the fixture description matches the data.

**Authority granted to enforce once J1–J7 are folded into the FR text.** Freeze scope to: the pure,
leaf `api/plot/realize.py` `beat_instruction(plan, chapter) -> str` (J2 option (a); renders the
chapter's `ordered_functions` beat(s) with belief-focalized intent; `''` for an un-planned chapter;
never a world-truth assertion before the reveal); the focalization read chosen in J5 (a named pure
helper in `project.py` **or** an in-`realize` walk, no third option); the **additive, gated** merge
inside `invoke_turn` (J6), reversible by dropping the FR-563 attach; the design §6b correction to the
real signature (J7); the deterministic machinery ACs (AC5a, pytest, no LLM) and the end-to-end demo
witness (AC5b, `demo-output.log`, demo-gate, real gate names per J4). **No** change to the four checks,
the projection sets, the exclusion seam, or the `TurnRequest`/`TurnExtras` schema; **no** `eff_world`
writeback to the doc; **no** turn↔beat scheduler beyond the trivial chapter render; **no**
`FunctionKind`/`AffectKind` growth. Example-exempt (FR-474 J3): **no** `@pytest.mark.req`, **no**
capability YAML. `unified-planning` stays optional (realize and the focalization read are pure). RED
commit first (`SKIP=pytest`): the deterministic ACs (beat-renders-to-instruction, un-planned-empty,
additive+gated wiring, belief-focalization-not-world-revival, dormancy regression) committed failing
before `realize.py` and the wiring exist; the AC5b demo witness lands with GREEN. Changelog fragment +
diary required.
