# Feature Request: FR-534 — DM v2: Project the protected-character set into prose generation

**Priority:** HIGH (closes the lifecycle-resurrection root cause the FR-506→533 arc has been
patching at the wrong boundary)
**Type:** Feature (refactor — one additive edge, no engine rewrite)
**Status:** Judged 2026-06-19 — authority granted for **Phase 1 only**; scope frozen (see
Judgement). Phase 2 (deterministic post-compose check) split to follow-up **FR-535**.
**Effort:** ~1 day
**Requested:** 2026-06-19

## Summary

The FR-533 spike proved that DM v2 already holds a working **plan-over-prose precedence**
(`_enforce_memory_precedence_gate`, precedence `chapter_memory > live_synopsis >
seam_packet`) — but only at **bookkeeping** time (chapter open). Nothing carries that same
precedence into **prose generation**, so the turn director and the final-cut composer can
freely narrate the death of a character the plan is sworn to keep alive (the ch7 Witta
resurrection). The ledger then correctly refuses to record the death, producing a
reader-visible resurrection at the next seam.

This FR adds the one missing edge the spike identified: a deterministic
`protected_characters(doc, cid)` resolver — built from the **same** state extractors the
precedence gate uses — whose output is threaded into **both** the turn director and the
final-cut as a hard *may-not-die* constraint, symmetric to FR-519's existing
*dead_within_chapter* channel. A plan-protected character can then never be killed on the
page, so there is no conflict for any downstream gate or extractor to reconcile.

## Value Statement

DM v2 authors get plan-faithful prose: a character the synopsis needs alive for the rest of
the arc can no longer be narrated dead mid-chapter, eliminating the lifecycle-resurrection
break class at the boundary where the bad prose is *born* rather than where it later
*manifests*.

## Problem

The lifecycle-resurrection class (Witta dies ch7 → argues ch8; the §1 break table in
`continuity-projection-plan.md`) has been fought for the whole FR-506→533 arc as if it were
an **extraction lie** — "the close-time extractor mis-read a death and wrote `alive`." The
FR-533 spike inverted that premise (`continuity-projection-plan.md` §6):

- ch7's composed `text` *does* kill Witta, but **six** structured sources unanimously,
  *plan-faithfully* keep her alive: `world_state.status`, `chapter_memory`,
  `irreversible_facts` ("Witta is alive at the end of the chapter, not dead or swept away"),
  `forbidden_regressions` ("FORBID: Witta is dead"), `seam_packet`, and
  `live_synopsis.character_states`. Witta is the plan-critical ritual-keeper antagonist the
  synopsis needs alive downstream.
- The per-turn ledger is non-monotonic (turn 7 sweeps her off; turns 8–16 keep her alive
  and restrained — an FR-501 no-progress tail). The **final-cut composition** chose the
  dramatic death; the plan chose survival.
- For a plan-protected character the prose death is the **error to prevent**, not the truth
  to record. Ratifying it into the ledger (the §3 "judge forbids alive-when-prose-says-dead"
  step) would contradict the synopsis and break the arc.

**The architectural gap is asymmetry, not absence.** `final_cut_context` already threads a
*dead* constraint into the prompt (FR-519: `dead_before_open`, `dead_within_chapter`). There
is no symmetric *protected / must-not-die* channel, and `invoke_turn` passes no such
constraint to the director at all. Plan-over-prose precedence exists for bookkeeping
(`_enforce_memory_precedence_gate`) but is never consulted when the prose is written. This is
the Scripture's `downstream_fix` → boundary-normalization cure: stop the death at the
generation boundary where it is born, not at the open-gate boundary where it manifests.

**Cross-engine check (`examples/demos/novel_generator`).** The one repo engine that guards
endings via a review gate (`prompts/review/review.yaml`) is instructive by what it *lacks*:
its guard is **LLM-scored, global (whole draft at once), and advisory** (`passed: bool` →
revise-loop). Its beat plan (`beat_id|act|summary|characters|importance`) carries no
lifecycle field, so the reviewer is never told a character was *supposed* to survive — it
could only catch a resurrection by vibe, never deterministically. This confirms two things:
(a) there is **no reusable ending-guard mechanism to borrow** from novel_generator (the
"no rewrite onto novel_generator" stance holds from a fresh angle), and (b) an **LLM review
gate alone is too soft for a hard lifecycle invariant** — guarding a protected character's
life needs a *deterministic, per-character, blocking* check, the inverse of
novel_generator's soft global pass.

## Proposed Solution

One deterministic resolver + two prompt-context edges + the prompt constraints to honour
them. No new engine, no schema change, no LLM call added. **Per Judgement J2 the resolver
lands in a new module `api/lifecycle_resolver.py`** (not `turn_ops.py`, which is at 1235
lines), and OWNS the three state extractors so precedence has one source of truth.

### 1. `protected_characters(doc, cid)` — the shared resolver (the diary Seed)

A pure function in **`api/lifecycle_resolver.py`** (J2), which also owns the three extractors
(`_state_map_from_memory` / `_state_map_from_synopsis` / `_state_map_from_seam`) and the
precedence ordering, so the resolver and the open-gate can never disagree:

```python
def protected_characters(doc: dict, cid: str) -> dict[str, dict]:
    """Characters the plan requires alive in chapter ``cid`` (and from which chapter).

    Authoritative state by the SAME precedence the open-gate enforces:
    chapter_memory > live_synopsis > seam_packet. A character is *protected* when
    its highest-precedence state is a live/active state AND a plan guard names it
    (forbidden_regressions / irreversible_facts 'X is alive' / synopsis presence).
    Returns {char_id: {"reason": <which guard>, "floor": <reappearance floor|None>}}.
    """
```

- Reuses `_state_map_from_memory` / `_state_map_from_synopsis` / `_state_map_from_seam`
  and the same precedence ordering as `_enforce_memory_precedence_gate` — single source of
  truth for "who is protected."
- `_enforce_memory_precedence_gate` is **refactored to consume this resolver** for its
  alive/dead determination, so the gate and the prose constraint are provably the same set
  (closes the diary Seed: "one resolver called by both the gate and the director").

### 2. Thread the protected set into the turn director (`invoke_turn` → `turn.yaml`)

Add a `protected` variable to the turn graph invocation, formatted as a hard constraint
(symmetric to how the cast/scene are passed). The director prompt gains a clause:
*"The following characters are plan-protected and MUST survive this chapter; you may
imperil, wound, or remove them from the scene, but you may NOT narrate their death."*

### 3. Thread the protected set into the final-cut (`final_cut_context` → `final_cut.yaml`)

Add a `protected_cast` key beside the existing `dead_within_chapter` (FR-519), rendered as
an empty string when nothing applies (same convention). The final-cut prompt gains the
symmetric *may-not-die* hard constraint, so the composition step — the one that actually
chose Witta's death — is bound by the same plan precedence the open-gate enforces.

### 4. (Carried, not new) reappearance floor

The resolver returns `floor` so the same channel can later carry
`allowed_reappearance_from_chapter` (the Arnulf class, §1). This FR **wires the field but
scopes the behaviour to the must-not-die constraint only**; the floor-binding for early
reappearance is left to a follow-up so this FR stays one reversible step (`spec_kill`).

### 5. (Phase 2 — SPLIT to FR-535 by Judgement J5) deterministic post-compose check

> **Struck from FR-534.** The Judge split this to follow-up **FR-535**, gated on evidence the
> Phase 1 prompt constraint is insufficient (TDD: build the backstop only once a failing test
> condemns Phase 1). Retained here as rationale for the split, not as FR-534 scope.

The constraints in steps 2–3 are *prompt-level* — probabilistic, not deterministic. The
novel_generator comparison shows an LLM *reviewer* is too soft for a hard invariant (Problem,
cross-engine check). FR-535 would add a deterministic backstop after final-cut: scan the
composed chapter `text` for death-markers attributed to any `protected_characters` name; on a
hit, reject and regenerate (bounded loop). Per Judgement J6 the detector must be LLM/
YAMLGraph-based, not regex (figurative-language false positives).

### Decision the spike already made

A `novel_generator` rewrite is the wrong move — it would re-pay for the precedence the
ledger already provides (FR-533 verdict, fourth branch). This is the additive-edge refactor
that verdict endorsed.

## Acceptance Criteria

- [ ] `protected_characters(doc, cid)` exists, is pure, and derives its set from the **same**
      precedence extractors as `_enforce_memory_precedence_gate` (verified by a test that the
      two agree on `10026-BC` ch7→ch8: Witta ∈ protected set).
- [ ] `_enforce_memory_precedence_gate` consumes the shared resolver (no duplicated
      precedence logic; one source of truth for protected/alive).
- [ ] `final_cut_context` emits a `protected_cast` key (empty string when none), and
      `final_cut.yaml` carries the symmetric *may-not-die* hard constraint beside the
      existing `dead_within_chapter`.
- [ ] `invoke_turn` threads a `protected` variable into the `turn.yaml` `direct` node and
      the `turn_direct` prompt carries the director-level *may-not-die* constraint.
- [ ] **RED regression first (TDD):** a witness test over a **committed minimal fixture**
      (`examples/dungeon_master/tests/fixtures/`, NOT the gitignored `10026-BC`) proving
      today's gap — ch7 final-cut narrates Witta's death while six sources hold her alive —
      lands and fails before the fix, passes after (the protected constraint is present in
      the assembled final-cut context for Witta).
- [ ] Re-running the FR-533 spike driver (or an equivalent single-chapter re-play) over a
      Floodmark seam shows no protected character narrated dead; record before/after like
      FR-532.
- [ ] No engine rewrite, no schema change, no new LLM node; line budget respected (split a
      resolver module if `turn_ops.py` exceeds the ceiling).
- [ ] Changelog fragment (`type: feat`, scope `dungeon_master`) + Distill diary entry.

## Judgement (2026-06-19 — authority granted for Phase 1 only; scope frozen)

The Judge traced every load-bearing claim through the live code before ruling. The trace
confirmed the root cause but surfaced three facts that **narrow** the scope: a gitignored
fixture, a module already over its line ceiling, and a phase-2 hazard that must not ride on
phase 1. Authority is granted for **Phase 1 only**; Phase 2 is split to a follow-up FR.

- **J1 — Root cause and lever CONFIRMED against code.** The asymmetry is real and exact:
  `final_cut_context` threads `dead_before_open` + `dead_within_chapter` into the prose
  prompt (via `dead_character_names`, FR-519) but emits **no** protected/must-not-die key;
  `invoke_turn` → the `direct` node (`turn_direct` prompt) passes `cast` + `scene` but **no**
  protected constraint. `_enforce_memory_precedence_gate` holds the precedence
  (`chapter_memory > live_synopsis > seam_packet`) at chapter open and nowhere else. The FR's
  thesis — precedence exists for bookkeeping, absent at generation — is verified. Authority
  on the mechanism is granted.

- **J2 — Seam names CORRECTED; module placement is MANDATORY, not optional.** The FR named
  `turn.yaml` as the director-prompt seam. The actual seams are: the **`turn_direct`**
  prompt (`prompts/turn_direct.yaml`) wired through the `direct` node's `variables:` in the
  `turn.yaml` **graph** (`examples/dungeon_master/turn.yaml`), and the **`final_cut`** prompt
  + `final_cut_context()`. Use those. Critically, **`turn_ops.py` is 1235 lines** — already
  ~3× the 450 ceiling — so the resolver MUST NOT land there. Freeze: create
  **`api/lifecycle_resolver.py`** that OWNS the three extractors (`_state_map_from_memory`
  / `_state_map_from_synopsis` / `_state_map_from_seam`), the precedence ordering, and the
  new `protected_characters`; `turn_ops._enforce_memory_precedence_gate` then **imports and
  consumes** them. One source of truth for precedence — duplication is forbidden (Commandment
  8). This also relieves the bloat rather than worsening it. (Example code: import-linter's
  three-layer rule does not apply.)

- **J3 — The witness fixture is GITIGNORED; the RED test must NOT depend on `10026-BC`.**
  `outputs/dungeon-master/10026-BC/story.json` is under a gitignored `outputs/` tree — a
  CI-gate witness test anchored to it would pass locally and vanish in CI (the
  gitignored-output trap; cf. repo memory on gitignored DM outputs). Freeze: extract a
  **minimal committed fixture** under `examples/dungeon_master/tests/fixtures/` containing
  only the rows the resolver needs (ch7 `seam_packet.character_lifecycle` Witta, ch7
  `chapter_memory.character_state_deltas` Witta, `live_synopsis.character_states` Witta, and
  a ch7 `text` carrying the death sentence). The witness asserts against the committed
  fixture, never the live output. The fixture IS the regression's permanent witness.

- **J4 — Membership rule FROZEN to the conjunction.** "Highest-precedence-alive alone"
  over-protects: every momentarily-alive walk-on becomes un-killable, which would forbid
  legitimate deaths — the opposite failure. Freeze: **protected = (highest-precedence state
  is a live/active state) AND (a plan guard names the character)** — where a plan guard is a
  `forbidden_regressions` "X is dead"-class entry, an `irreversible_facts` "X is alive"
  assertion, or a `live_synopsis.character_states` presence. Witta qualifies on all three;
  this is the verified positive case the witness pins. A transient cast member with no plan
  guard is killable.

- **J5 — SPLIT: Phase 1 (prompt projection) is FR-534; Phase 2 (deterministic post-compose
  check) becomes a follow-up FR, gated on evidence.** TDD forbids building Phase 2 until a
  failing test condemns Phase 1 as insufficient (Commandment 7: "no bug fixed unless first
  condemned by a failing test"). The `novel_generator` comparison proves a *post-hoc LLM
  reviewer* is too soft — but the Phase 1 constraint is **not** a reviewer; it is an
  instruction at *generation* time (the model writes toward it), which is strictly stronger
  than judging after, and we have **zero** evidence yet that it fails. Build the cheap,
  reversible projection first; measure; only if a protected death still reaches the page does
  Phase 2's deterministic backstop earn its place. Proposed-Solution step 5 and acceptance
  criterion "(Phase 2)" are **struck from FR-534** and migrate to **FR-535 (follow-up)**.

- **J6 — Phase-2 hazard recorded as a constraint ON FR-535 (not this FR).** A death-marker
  scan over composed prose is a regex/NLP surface that WILL false-positive on figurative
  language — ch7's own text ("the valley swallowed the judgment she had called down"), plus
  "as good as dead", "dead silence", "dying light". Per the repo convention "YAMLGraph and
  LLM should be used instead of complex regex logic", FR-535's detector must be an LLM/
  YAMLGraph check, not a regex (`regex_fourth_exclusion` trap pre-empted). Noted here so the
  follow-up inherits the constraint.

- **J7 — Floor field: WIRE the return value, do NOT bind behaviour (criterion 4 stands).**
  `protected_characters` returns `floor` so FR-535/the Arnulf-class follow-up can consume it,
  but FR-534 binds only the must-not-die constraint. Keeps the diff one reversible step
  (`spec_kill`).

- **J8 — Example-scoped (FR-474 J3).** NO `@pytest.mark.req` on the witness test. Changelog
  `type: feat`, scope `dungeon_master`. Diary required (feat + FR-XXX). RED commit (failing
  witness, `SKIP=pytest`) and GREEN commit (fix) separate, per Commandment 7.

**Scope frozen (FR-534 = Phase 1 only):** (1) `api/lifecycle_resolver.py` owning the three
extractors + precedence + `protected_characters` (conjunction rule, J4); (2)
`_enforce_memory_precedence_gate` refactored to consume it (one source of truth); (3)
`final_cut_context` emits `protected_cast` + `final_cut` prompt carries the may-not-die
constraint, symmetric to `dead_within_chapter`; (4) `turn.yaml` `direct` node + `turn_direct`
prompt carry the may-not-die constraint; (5) `floor` returned but unbound; (6) committed
minimal fixture + RED-first witness asserting against it (NOT `10026-BC`). **Out of scope
(→ FR-535):** the deterministic post-compose death-marker check and its regenerate loop,
gated on evidence Phase 1's prompt constraint is insufficient, detector to be LLM-based.

## Alternatives Considered

- **Ratify the prose death into the ledger** (the original §3 plan step / FR-533 premise):
  rejected — for a plan-protected character this contradicts the synopsis and breaks the
  arc. The spike proved the death is the error, not the truth.
- **`novel_generator` rewrite** (project all prose from an authored plan): rejected by the
  FR-533 verdict — re-pays for the typed ledger + precedence DM v2 already has.
- **Deterministic post-compose death-marker rejection only** (no director/final-cut
  constraint): rejected as the *sole* mechanism — it wastes a full compose on every
  protected-death before catching it. FR-534 instead does the cheap prompt constraint first
  (phase 1) and adds the deterministic check as a backstop (phase 2), because the
  novel_generator review-gate comparison proved a probabilistic gate alone is too soft for a
  hard lifecycle invariant. Both, not either.

## Related

- `feature-requests/FR-533-dm-v2-projection-emergence-spike.md` (the spike that inverted the
  premise and endorsed this refactor)
- `examples/dungeon_master/docs/continuity-projection-plan.md` §3, §4 (staging), §6 (verdict)
- `examples/dungeon_master/api/turn_ops.py`: `_enforce_memory_precedence_gate` (precedence
  source of truth), `final_cut_context` / `invoke_final_cut` (FR-519 dead channel — the
  symmetry point), `invoke_turn` (turn director)
- `docs/diary/diary-2026-06-19-the-gate-that-refused-my-fix.md` (Seed: one resolver for both
  the gate and the director)
- FR-519 (dead-within-chapter prose constraint — the existing asymmetric half), FR-510
  (`confirmed_dead`-only exclusion gap), FR-501 (no-progress tail in ch7's turns)
