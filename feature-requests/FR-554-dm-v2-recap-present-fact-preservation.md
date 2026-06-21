# Feature Request: DM v2 Recap Present-Fact Preservation (the "present-but-ignored" lever)

**Priority:** MEDIUM (continuity is the dominant review-score sink on 10035-BC; FR-553 localized the lever here)
**Type:** Enhancement
**Status:** Enforced (RED 1ab20a8b -> GREEN this commit) -- revived-actor witness live (10035-BC reads 10 incidents, the deterministic gauge); recap + director salience clauses shipped; C1 resolved (a), C2-C4 folded
**Effort:** ~1 day (deterministic witness + two prompt-wording changes; validated against the FR-553 harness)
**Requested:** 2026-06-21

## Summary

FR-553 falsified the "the small model is drowning in a 12k director prompt" premise and found the
opposite: on 10035-BC, **2/2 measured continuity breaks were *present-but-ignored*** -- the
governing fact (Arnulf is dead / Arnulf has exited the scene) was already present in the running
scene the recap narrator received, and the narrator contradicted it anyway. The lever is therefore
**wording and salience in the recap path, not prompt mass**. This FR (a) adds a *deterministic*
**revived-actor witness** -- a character recorded as exited/dead in an earlier turn who is narrated
*acting* in a later recap of the same chapter -- and (b) makes two minimal prompt changes that hoist
the already-present "who is gone this chapter" fact from buried prose into a salient, structured
directive in both the director and the recap prompts. Visibility-not-gate posture (FR-522/530/553).
The witness is the RED-able regression target the wording change must drive toward zero.

## Value Statement

The narrator stops resurrecting characters it has already killed: the single most legible continuity
failure on 10035-BC (Chapter 8's "Arnulf went down and did not rise" -> "Arnulf drove forward"
-> "Arnulf surges up once more") becomes a deterministically detectable defect and a measurable
target, and the fix is a prompt-salience change rather than more orchestration.

## Problem

**The finding (FR-553, 10035-BC, continuity 1/5).** The director scene peaks at ~2k tokens and the
fact was *in* the scene -- so the defect is not mass, placement, or context-window pressure. It is
that a fact present in the running scene is **not salient enough** for the small model to honor,
because the recap path relies on the model *re-deriving* "Arnulf already died this chapter" by
scanning prior recaps, instead of being *told* it as a standing constraint.

**The two concrete failures the reviewer cited** (both subject Arnulf, both `subject_present == True`):

- **LIFECYCLE (Ch8, the clean case).** "Arnulf went down in the moving line and did not rise" then,
  paragraphs later, "Arnulf drove forward toward Gunnar's midsection" and "Arnulf surges up once
  more from the salt road with his weapon raised." A character recorded as down/dead in an earlier
  turn acts again in a later turn's recap. This is **deterministically detectable** and is the
  primary target of this FR.
- **PLOT-RESET / SEAM (Ch2->Ch3, the harder case).** Chapter 3 opens on the same ledge as Chapter
  2 but drops the intimacy/bond established in Chapter 2. The witness keys this to the entering
  character (Arnulf) so `subject_present` reads True, but the *actual* dropped fact is the
  **relational bond** -- which is FR-545's pairwise-edge slice, not a revived-actor. This FR carves
  it out (see Scope boundary); it is named here only to keep the finding honest.

**Why the present fact is ignored (the wording diagnosis).**

- `turn_recap.yaml` instructs the narrator to "advance the chapter one step", "name every character
  at least once", and "do NOT invent a new character" -- but contains **no instruction to honor
  still-true established facts** (who has died/exited this chapter). The dead-status of a character
  lives only as prose inside `{{ scene }}`, which the model must re-read and re-infer every turn.
- `turn_direct.yaml` already produces `cast_exits` (the structured authority that drops an actor
  from the cast going forward), but its `continuity` flag scope is enumerated to exactly three
  classes -- non-roster name, faction-mismatch, unprovenanced item -- and **does not include "a
  character recorded as exited this chapter acting again"**. So when the climax turns get muddled,
  nothing flags the revival and nothing feeds a corrective `instruction` back to the recap.

## Proposed Solution

Three minimal, in-scope changes. No new graph, no new LLM call, no change to `running_scene`.

**1. Deterministic revived-actor witness (`prompt_salience.py` or a sibling; RED-first).** For each
chapter, walk the turns in order; track the set of names that have appeared in a turn's
`cast_exits` (the director's own structured exit authority). Flag any later turn whose recap
narrates an exited name as an *actor* (subject-position name match against the recap text, reusing
the deterministic presence machinery from FR-553). Emit `revived_actor_count` and the per-incident
list (chapter, exit_turn, revival_turn, name) into the continuity witness, visibility-not-gate.

The data dependency is already met: the director's `cast_exits` is persisted per turn under
`chapters.cards[cid].turns[n].direction.cast_exits` ([turn_ops.py](examples/dungeon_master/api/turn_ops.py)),
and `turn_state._chapter_cast_exits(doc, cid, n)` already accumulates the exits recorded *before*
turn `n` in order. The witness **reuses that primitive** for the exit-set walk (it does not re-derive
it), then adds only the new half — scanning each later turn's recap text for an exited name in actor
position. No new persistence and no new walk; the novelty is the recap-side revival check.

```text
# witness excerpt (target: revived_actor_count -> 0)
revived_actors:
  count: 1
  incidents:
    - {chapter: 8, name: Arnulf, exit_turn: 3, revival_turn: 5}
```

**2. Hoist the "gone this chapter" fact into the recap prompt (salience, not mass).** Pass the
accumulated `cast_exits` set into `turn_recap.yaml` as a dedicated structured block and add a
fact-preservation clause:

```jinja
{% if gone_this_chapter %}
GONE THIS CHAPTER (already left the scene -- killed, drowned, swept away): {{ gone_this_chapter | join(", ") }}.
These characters must NOT act, speak, or strike this turn. Do not revive them. If an intent narrates
one of them acting, narrate the still-present characters reacting to their absence instead.
{% endif %}
```

This converts a fact the model already *had* (buried in `{{ scene }}`) into a salient standing
constraint -- the direct test of the FR-553 present-but-ignored diagnosis.

**3. Broaden the director's continuity scope by one class (a *lagging* corrector -- C3).** Add to
`turn_direct.yaml`'s continuity list: "a character already recorded as gone this chapter (named in an
earlier turn's `cast_exits`) narrated as acting again -- a revival." Because the turn graph runs
`direct -> recap` within one turn, the director at turn *k* judges from turns `1..k-1` and **cannot**
see turn *k*'s own recap; a revival narrated in turn 5's recap is first visible to the director at
turn **6**, feeding a corrective `instruction` to turn 6. So change #3 is a one-turn-late steer, not
an in-turn fix -- the **deterministic witness, not the director, is the authority for the failing
turn.** To make the flag actionable the director also receives `gone_this_chapter` (same variable as
change #2).

**C1 resolution -- the detection method (option (a), honest substring proxy).** The witness does NOT
claim subject/actor-position parsing (that is the `regex_fourth_exclusion` / `plausible_wrong_answer`
trap, and the FR-553 "presence machinery" only does a turn-1 opening-scene substring test). Instead:
a **revived-actor incident** is *an exited name appearing in a strictly-later recap's text, excluding
occurrences that are purely possessive* (`Name's` / `Name\u2019s` -- e.g. "Arnulf's fallen body",
"Arnulf's weapon arm": aftermath the narrator may legitimately describe). The single frozen
exclusion is **possessive-only**; no verb lexicon, no position parser. It is a **flag to look, not a
verdict**: it will still fire on legitimate non-possessive references (grief: "they wept for Arnulf";
passive: "Arnulf pinned"), and that over-count is accepted under visibility-not-gate. The RED test
**freezes both surfaces**: a true-positive ("Arnulf surges up" counts) AND a true-negative
(possessive-only "Arnulf's fallen body was carried past" does NOT count). If a *fourth* special case
ever demands its own exclusion during enforce, that is the signal to stop growing the rule and accept
the bare-substring over-count (option (a) proper), not to build a parser.

## Acceptance Criteria

- [ ] **RED first (C1):** failing tests for the revived-actor witness on a fixture derived from
      10035-BC -- a **true-positive** (exited name, non-possessive, strictly-later recap -> counts)
      AND a **true-negative** (possessive-only mention -> does NOT count). Both surfaces frozen.
- [ ] `revived_actor` block (`count` + per-incident `{chapter, name, exit_turn, revival_turn}`)
      emitted into the continuity witness (visibility-not-gate; empty when no exits recorded),
      printed by the witness report.
- [ ] `turn_recap.yaml` receives `gone_this_chapter` and carries the fact-preservation clause,
      plumbed via the **`protected` precedent (C2)**: computed at the invoke site (reusing the
      ordered `cast_exits` walk), declared in `turn.yaml` `state:`, bound in the `recap` node
      `variables:`.
- [ ] `turn_direct.yaml` continuity scope extended by the revival class, worded as a **lagging
      corrector (C3)**; `gone_this_chapter` also bound on the `direct` node.
- [ ] **Regression evidence (C4, NON-GATING):** regenerate 10035-BC (or its seed) and record the
      trace + `revived_actor_count`; the LLM-reviewer break drop is demo-log visibility, never a
      blocking test. The only gating regression target is the deterministic `revived_actor` count.
- [ ] Example-exempt tests (no `@pytest.mark.req`, no live LLM in unit tests); full DM suite green.
- [ ] Changelog fragment + diary entry.

## Scope boundary (honesty per FR-553 / FR-545)

- **In scope:** the *revived-actor* class -- a character with a recorded `cast_exits` who acts again
  in a later recap. This is the deterministic, Ch8-Arnulf failure and the clean target.
- **Out of scope:** the **relational/bond drop** (Ch2->Ch3 intimacy loss). It has no `cast_exits`
  edge to diff; it is FR-545's pairwise-allegiance slice and the LLM reviewer's domain. The
  `seam_entrance` presence-but-ignored check that keyed on Arnulf is *not* claimed fixed here.
- **Limitation (`plausible_wrong_answer` guard):** the witness counts *revivals it can name from
  `cast_exits`*, not all lifecycle contradictions. A death the director never recorded as an exit is
  invisible to it -- so a low `revived_actor_count` is a regression gauge, never an all-clear. It is
  a complement to the LLM reviewer's localization, consistent with FR-545's C4 limitation.

## Alternatives Considered

- **Bound/re-rank the director prompt (the FR-553 deferred fix).** Rejected: FR-553's C5 gate
  resolved to outcome (b) -- 0 presence gaps -- so re-ranking a prompt that already contains the
  fact cannot help. The fact is present; the problem is salience and an absent constraint.
- **A second LLM "continuity-check" pass over each recap.** Rejected as more orchestration on a
  small model -- the exact complexity FR-553's originating question pushed back on. The deterministic
  witness + a one-line prompt clause is cheaper and testable.
- **Enforce `cast_exits` as a hard gate that strips revived names post-hoc.** Rejected for this FR:
  visibility-not-gate posture first (FR-522/530); measure the wording change against the witness
  before adding a mutating gate. **If the wording change underperforms, the pre-committed escalation
  target is FR-511's existing detect→revise loop, not a freshly-built gate** — see the FR-511
  relationship below.
- **Build a new mutating revise gate from scratch.** Rejected — FR-511 (Judged-Granted) already
  implements a deterministic detect → one constrained revise → re-validate loop for the
  dead-character-acting class at chapter close. A new gate would duplicate that machinery
  (`false_duplicate`). The correct escalation is to *extend FR-511's validator to consume this FR's
  revived-actor witness*, reusing its one-attempt cap, deterministic-authority acceptance, and typed
  `FinalCutReviseError`.

## Relationship to FR-511 (the existing revise loop, and why this class is *deliberately* unguarded)

FR-511 is **fully implemented** (not merely judged): the deterministic **detect confirmed-dead-acting
→ one constrained revise → re-validate → `FinalCutReviseError`** loop runs in
[`chapter_ops.close_chapter`](examples/dungeon_master/api/chapter_ops.py) (verified L259–320), backed
by `collect_dead_character_prose_violations` / `revise_final_cut_once` /
`post_revise_invariant_failures` and proven by `test_final_cut_revise_cycle.py`. It does *not* catch
the 10035-BC Ch8 Arnulf revival — and the reason is **stronger than a scope miss: the class is
intentionally exempted.**

- **FR-511's `dead_names` is sourced from the *prior* seam packet** (`inherited_seam_packet(doc, cid)`),
  filtered to `existence_state == "confirmed_dead"` — i.e. characters dead **before the chapter
  opened**. A per-turn `cast_exits` death never enters that set.
- **FR-519 B3 *deliberately* exempts within-chapter deaths from the active-role detector.** The source
  comment (chapter_ops.py L259–263) is explicit: "a within-chapter-dead character acts legitimately
  up to their death, so the blanket active-role detector must not raise on them (FR-519 B3); their
  residual is measured warn-only." So the Ch8 Arnulf revival is not an oversight FR-511 missed — it
  falls inside a class FR-519 B3 *consciously chose not to police*, to avoid false positives on
  legitimate dying action.

So this FR is **not** a duplicate of FR-511 and **not** merely filling a forgotten corner — it covers
a class FR-519 B3 intentionally left open, using a different signal (the per-turn `cast_exits` exit +
a warn-only revived-actor residual) that does not reopen the false-positive risk FR-519 B3 was
avoiding. Visibility-not-gate first.

**Pre-committed escalation (with the FR-519 B3 caveat):** if the wording change underperforms against
the witness, the remedy is to feed this witness's revived-actor incidents into **FR-511's existing
detect→revise loop**, reusing its one-attempt cap, deterministic-authority acceptance, and typed
`FinalCutReviseError` — **not** a new gate. But that escalation is not a trivial "extend the
validator": it must distinguish **"acting *after* a recorded `cast_exits` exit turn"** (the revival to
police) from **"legitimate final struggle *up to and including* the exit turn"** (the action FR-519 B3
protects). The `cast_exits` exit-turn index is exactly the discriminator — police only recaps strictly
*after* the turn a name first appears in `cast_exits`.

## Judgement (2026-06-21)

**Verdict: APPROVE WITH CONDITIONS.** Scope is clear, minimal, and routes correctly off FR-553's
falsification (present-but-ignored → wording, not mass). Every structural claim was verified against
code: `cast_exits` per-turn persistence (turn_ops L342), `_chapter_cast_exits` ordered walk
(turn_state L198), `turn_direct.yaml` enumerated continuity scope, FR-511 implementation
(chapter_ops L259–320), FR-519 B3 deliberate within-chapter-death exemption, and `prompt_salience.py`
(189 lines, visibility-not-gate). The FR-511 non-duplication argument holds. **One claim does not
hold as written (C1, blocking); three are under-specified (C2–C4, non-blocking but must be folded in
during enforce).**

**C1 — BLOCKING. The witness's detection method is over-specified; the cited "presence machinery"
cannot do what change #1 claims.** The FR says the witness performs a *"subject-position name match
against the recap text, reusing the deterministic presence machinery from FR-553"*. That machinery is
[`_subject_present_at_open`](examples/dungeon_master/api/prompt_salience.py) — it checks **turn-1's
opening scene only** (`running_scene(doc, cid, 1)`) with a **plain lowercase substring test**
(`subject.lower() in text.lower()`). There is **no per-turn-recap scan and no subject/actor-position
parser anywhere in the harness.** "Arnulf surges up" and "Arnulf's fallen body was carried past" and
"they wept for Arnulf" all contain the substring; only the first is a revival. A bare substring
witness will false-positive on every post-mortem mention, and "subject-position" detection is exactly
the `regex_fourth_exclusion` / `plausible_wrong_answer` trap. **Resolution before enforce — pick one
and write it into change #1 and the AC:**
  - **(a) Honest substring proxy (preferred, posture-consistent).** Drop the "subject-position" claim.
    Define the witness as *"an exited name appears in a strictly-later recap's text at all"*, and
    state plainly that it is a **flag to look, not a verdict** — it will fire on legitimate
    post-mortem references, and that is acceptable under visibility-not-gate. The RED test **must
    include a true-negative fixture** ("Arnulf's body was carried" must NOT count as a revival only if
    you add an exclusion — otherwise it WILL count, and the test must assert that documented
    behaviour) so the false-positive surface is condemned and frozen, not discovered later.
  - **(b) Narrow deterministic heuristic.** Keep an actor-position notion but define it as a **frozen,
    enumerated** rule (e.g. name immediately followed by an active verb from a fixed lexicon), with
    the exclusion set written into the FR. If a fourth special case appears during enforce, that is
    the signal to switch to (a), not to grow the regex.

**C2 — non-blocking. Name the plumbing precedent.** Change #2 threads a new `gone_this_chapter`
variable into the recap. The AC says only "the recap call signature/binding updated where the prompt
is rendered (turn graph)." The exact, already-working precedent is **`protected`**: it is computed at
the turn-invocation site, declared in [turn.yaml](examples/dungeon_master/turn.yaml) `state:`, and
bound in a node's `variables:`. Enforce must follow that path — compute the accumulated exit set at
the invoke site (reusing `_chapter_cast_exits`), add `gone_this_chapter` to `state:`, and bind it in
the `recap` node `variables:`. The prompt clause alone is insufficient; cite `protected` so the
plumbing is not rediscovered.

**C3 — non-blocking. Change #3 is a *lagging* corrector; the FR slightly overstates it.** The turn
graph runs `direct → recap` within one turn, so the director at turn *k* judges the scene from turns
`1..k-1` and **cannot see turn k's own recap**. A revival narrated in turn 5's recap is therefore
only visible to the director at turn **6**, feeding a corrective `instruction` to turn 6 — it does not
"correct the recap on the turn it happens." Keep change #3 (it is a useful one-turn-late steer) but
fix the wording to call it a lagging corrector; the deterministic witness, not the director, is the
authority for the failing turn.

**C4 — non-blocking. The reviewer-drop AC is LLM-nondeterministic; mark it non-gating.** "Show the
LLM reviewer's LIFECYCLE break drop versus baseline" cannot be a blocking test (FR-553 C5 / FR-548
precedent). Keep it as **demo-log visibility evidence** (regenerate, record the trace and
`revived_actor_count`), explicitly non-gating. The only gating regression target is the deterministic
`revived_actor_count` on a fixed fixture (the RED test).

**Authority granted to enforce once C1 is resolved in the FR text (C2–C4 folded into the enforce
diff).** Freeze scope to the three changes as written, minus the over-specified detection claim.
RED-first: the revived-actor witness fixture (true positive **and** the C1 true-negative) before any
prompt change. No new graph, no new LLM call, no mutating gate (escalation to FR-511 stays deferred
per the relationship section). Example-exempt; changelog fragment + diary required.

## Related

- FR-511 (existing chapter-close detect→revise loop for the dead-character class; the pre-committed escalation target — this FR fills its intra-chapter `cast_exits` blind spot)
- FR-553 (parent investigation; the present-but-ignored finding and the `prompt_salience.py` harness this FR extends)
- FR-545 (pairwise allegiance/relational reset witness; owns the carved-out bond-drop class)
- FR-542 `fact_reversal`, FR-538 `seam_entrance` (sibling visibility-not-gate witnesses)
- [examples/dungeon_master/prompts/turn_recap.yaml](examples/dungeon_master/prompts/turn_recap.yaml)
- [examples/dungeon_master/prompts/turn_direct.yaml](examples/dungeon_master/prompts/turn_direct.yaml)
- [examples/dungeon_master/api/prompt_salience.py](examples/dungeon_master/api/prompt_salience.py)
- [examples/dungeon_master/scripts/emit_continuity_witness.py](examples/dungeon_master/scripts/emit_continuity_witness.py)

## Implementation

**Status: Enforced (RED `1ab20a8b` -> GREEN this commit).** All three changes shipped; C1 resolved
to option (a) (possessive-excluded substring proxy + mandatory true-negative); C2-C4 folded.

**What shipped:**

- `examples/dungeon_master/api/prompt_salience.py` -- `revived_actors(story_doc)` + `_revives_in_recap`.
  A *revival* = an exited name (first `cast_exits` declaration at turn `e`) appearing in the recap of a
  turn STRICTLY after `e`, excluding occurrences that are purely possessive (`Name's` / `Name\u2019s`).
  Single frozen exclusion; no verb lexicon, no actor-position parser. Returns
  `{posture, count, incidents:[{chapter, name, exit_turn, revival_turn}]}`; empty when no exits. The
  report gained a terse `revived actors (... FR-554): N` block with per-incident lines.
- `scripts/emit_continuity_witness.py` -- emits `witness["revived_actor"] = revived_actors(story_doc)`.
- `api/turn_ops.py` -- `invoke_turn` computes `gone_this_chapter = ", ".join(_chapter_cast_exits(doc,
  cid, n))` (reusing the existing FR-521 ordered walk -- no duplicate; the union of exits *before*
  turn `n`) and passes it into the turn graph, following the `protected` precedent (C2).
- `turn.yaml` -- `gone_this_chapter: str` added to `state:` and bound on both `direct` and `recap`.
- `prompts/turn_recap.yaml` -- a `GONE THIS CHAPTER` fact-preservation clause: the gone must not act,
  strike, speak, rise, or move; narrate the present reacting to their absence, never the gone acting
  (the direct test of the FR-553 present-but-ignored diagnosis -- salience, not mass).
- `prompts/turn_direct.yaml` -- continuity scope extended by a `revival` class (a *lagging* corrector,
  C3 -- the director sees turn `k` from `1..k-1`, so it flags a revival one turn late, feeding a
  corrective `instruction`); the director also receives `gone_this_chapter` to make the flag actionable.

**The deterministic gauge on real data (10035-BC, the FR-553 book):** the witness reads **10
revived-actor incidents** -- Ch8 Arnulf exited at turn 5 then narrated on stage at turns 6-14 (the
"Arnulf surges up once more" resurrection the reviewer flagged as the LIFECYCLE break), plus Ch3
Arnulf (t5 -> t9). The director itself re-declared the exit at turns 13/14 -- it kept trying to bench a
character the narrator kept reviving. This is the regression number the recap clause must drive toward
zero.

**Tests:** 4 new example-exempt tests (RED `1ab20a8b`): true-positive ("Arnulf surges up" counts),
the mandatory C1 true-negative (possessive-only "Arnulf's fallen body" does NOT count),
empty-without-exits, and report-mentions-revived. Full DM suite **398 passed**; `turn.yaml` lints
clean.

**C4 (non-gating) pending:** the LLM-reviewer LIFECYCLE-break drop requires a live regen with the new
recap clause; that is demo-log visibility evidence, recorded next, never a blocking test. The gating
target is the deterministic `revived_actor` count (10 -> 0).

**Scope held:** the Ch2->Ch3 relational/bond drop stays out (FR-545's pairwise slice); no mutating
gate (escalation to FR-511's revise loop stays deferred per the relationship section). The count
over-counts legitimate non-possessive references (grief, passive "Arnulf pinned") by design -- a flag
to look, never an all-clear (`plausible_wrong_answer` guard).
