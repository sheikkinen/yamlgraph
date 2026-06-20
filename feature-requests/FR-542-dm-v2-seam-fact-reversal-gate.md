# Feature Request: DM v2 Deterministic Seam Fact-Reversal Gate + Close-Boundary Ledger Reconciliation

**Priority:** HIGH (root-cause fix for the resolved-fact reversal + ledger-resurrection class)
**Type:** Bug + Feature
**Status:** Enforced (2026-06-19) — both parts GREEN, 12 tests
**Effort:** ~1.5 days
**Requested:** 2026-06-19

> **Field-naming correction (judge):** the seam_packet model carries `resolved_events`,
> `must_carry_facts`, and **`opening_constraints`** — there is no `forbidden_regressions` field on
> the packet. `chapter_memory["forbidden_regressions"]` is *derived* from `packet["opening_constraints"]`
> at `chapter_ops.py:100`. The implementer must read `forbidden_regressions` from **chapter_memory**,
> not from the seam_packet. (Verified 2026-06-19.)

## Summary

The seam ledger already records `resolved_events`, `must_carry_facts` (seam_packet), and
`forbidden_regressions` (chapter_memory, from `opening_constraints`) at each chapter close — but
they are only **rendered into the prose context**, where a 0.7-temperature sampler can silently
undo them. Two 10029-BC breaks are exactly this advisory-not-gate failure:

1. **Resolved-fact reversal:** Ch3 secures the food bundle on the ledge ("pulled it fully onto
   the ledge into the shared supply space"); Ch4 reopens it as "sat unclaimed" in the boat. A
   `resolved_events` entry is silently undone.
2. **Ledger resurrection (root cause):** Ch2's close recorded Arnulf `alive, at lower bank`
   **after** the director had already reported a `cast_exit: Arnulf` (swept away). The bad
   state enters at the Ch2→Ch3 seam and manifests three chapters of contradiction later.

This FR does two things at the **close boundary that owns the seam** (`the_one_law` — normalize
where state crosses, not downstream where it surprises): (a) **reconcile** the close-graph's
emitted `world_state` against the director's reported exits so a benched/lost actor cannot be
recorded present-and-alive; and (b) promote the seam facts from **advisory prose to a
deterministic gate** that diffs consecutive chapters' committed ledgers and flags a reversal of
a `resolved_event` / violation of a `forbidden_regression`.

This is the **fact/state-reversal** seam, distinct from FR-538/539 (a character *entering*
without staged prose). FR-539 stages an arrival; this FR stops a *resolved fact* from being
un-resolved and stops the ledger from *resurrecting* an exited actor.

## Value Statement

A fact the story has resolved stays resolved, and an actor the scene has lost is recorded lost —
the food bundle cannot un-secure itself a chapter later, and a swept-away character cannot be
silently logged as still standing on the bank — turning two of the three 10029-BC continuity
breaks from undetectable prose surprises into deterministic, blocked-at-close violations.

## Problem

Global coherence (a fact resolved in Ch3 surviving Ch4; an exit reported in Ch2 reflected in
Ch2's ledger) is a property the *local* turn sampler cannot enforce. Today the only carriers
are:
- the `seam_packet` fields, **rendered into `running_scene`/Final Cut prose** — advisory, soft,
  ignorable by the sampler (FR-534's lesson: a probabilistic constraint is too soft for a hard
  invariant); and
- the close-graph's `world_state` emission, which **does not reconcile against the director's
  `cast_exits`** — so a turn can report an exit and the same chapter's close can still write the
  actor as `alive` (the Arnulf root cause).

`seam_entrance_gap` (FR-538) measures **entrances**; there is no detector for **resolved-fact
reversal** or **exit-vs-ledger contradiction**. The symmetry is missing: we gate entrances'
prose but not facts' persistence.

## Proposed Solution

### A. Close-boundary ledger reconciliation (the bug — fix first; INTERIM)

> **Decision (2026-06-19):** Part A is retained here as the **interim** structural fix. Its
> diagnosis already lives in `examples/dungeon_master/docs/continuity-projection-plan.md` as that
> plan's *step 2 cheap fix*. Part A is the deterministic `cast_exits`-reconciliation variant of
> that step. It ships as **its own RED-first commit**, separate from Part B, and is explicitly
> **superseded** later by the plan's *step 3* write-once projected lifecycle ledger — no
> permanent contract, no compat debt; the supersession path is declared, not implied.

In `chapter_ops.close_chapter` (the async read that derives end-of-chapter `world_state`), after
the close-graph emits its `world_state`, **reconcile** it against the chapter's reported
`cast_exits` (already accumulated by `chapter_open._chapter_cast_exits`, chapter_open.py L196):

- any character the director benched/lost this chapter whose emitted row says `alive`/present is
  corrected to the reported exit status (absent/lost), or the contradiction is raised
  (Commandment 6: no silent fallback) — deterministic, roster-bounded, no LLM (a set intersection).

This normalizes the resurrection at the boundary it enters (Ch2 close), not three chapters
downstream where it manifests as an unstaged "return".

### B. Deterministic fact-reversal gate (promote advisory → blocking)

> **The novel, frozen contribution (judged).** The projection plan is lifecycle-only; it does NOT
> cover arbitrary resolved-fact reversal (the food bundle: secured↔unclaimed). Part B is the
> highest-leverage genuinely-new work and is the load-bearing reason FR-542 exists.

A pure `gap_detectors.fact_reversal_gap(prev_card, card)` that diffs the committed seam ledgers
of consecutive chapters:

- a `resolved_event` from chapter N that chapter N's *successor* contradicts (an enumerated
  reversal: secured↔unclaimed, present↔absent, closed↔reopened — a **closed antonym set**, not
  free-text NLP; sidesteps `regex_fourth_exclusion`);
- a `forbidden_regression` asserted by N that N+1's ledger violates. **Read
  `forbidden_regressions` from `chapter_memory`** (derived from `packet["opening_constraints"]` at
  chapter_ops.py L100) — there is no `forbidden_regressions` field on the seam_packet.

**Frozen scope (judged):** the antonym set is closed (`secured↔unclaimed, present↔absent,
closed↔reopened`); a fourth special case is the `regex_fourth_exclusion` trap → escalate to the
Phase-2 LLM tier, never widen the regex.

Wired as a **close-boundary check** (where both `prev_card["text"]`/ledger are committed —
assert the same "committed not read-back" invariant FR-539 R3 names). On a hit: surface as a
continuity violation in the witness/`continuity_witness.json` (measurement first, FR-538
posture) and — once measured stable — a re-roll or hard gate.

### Phasing

- **Phase 1 (this FR):** A (reconciliation bug fix, deterministic, blocking) + B as a
  **measurement** detector feeding `continuity_witness.json` (visibility-not-gate, FR-522/FR-538
  posture — never silently subtract from the witness).
- **Phase 2 (follow-up):** promote B to a blocking gate / close re-roll once the detector's
  precision is shown on a corpus (the `audit_gate` discipline: a detector without enforcement is
  a post-mortem; earn the gate with evidence first).

## Acceptance Criteria

**Part A (interim lifecycle reconciliation — separate RED-first commit):**
- [ ] `close_chapter` reconciles the emitted `world_state` against the chapter's reported
      `cast_exits`: a benched/lost actor cannot be recorded `alive`/present; contradiction is
      corrected to the exit status or raised. **RED test** reproduces the 10029-BC Ch2
      Arnulf-alive-after-`cast_exit` state and asserts the reconciled ledger marks him absent/lost.
- [ ] Part A cites `continuity-projection-plan.md` and declares itself the interim step-2 fix
      superseded by the plan's step-3 projected ledger (no compat debt).

**Part B (novel fact-reversal gate — the frozen contribution):**
- [ ] `gap_detectors.fact_reversal_gap` flags a `resolved_event` reversal (closed antonym set)
      and a `forbidden_regression` violation between consecutive committed ledgers; roster/
      closed-set bounded, no free-text NLP. Reads `forbidden_regressions` from `chapter_memory`.
- [ ] The food-bundle Ch3→Ch4 reversal fixture is flagged by the detector.
- [ ] The antonym set is frozen to `{secured↔unclaimed, present↔absent, closed↔reopened}`; a
      fourth case escalates to Phase-2 LLM, not a wider regex.
- [ ] `fact_reversal_gap` findings surface in `continuity_witness.json` (measurement); the gate
      never subtracts from the witness gap set (`gate_checks_shape_not_substance`).
- [ ] Gate promotion (re-roll / hard block) is deferred to a Phase-2 follow-up with corpus
      evidence (`audit_gate`); Phase 1 is measurement-only.

**Both:**
- [ ] An empty/absent seam ledger degrades to today's behavior (additive).
- [ ] Unit tests: reconciliation (exit→absent, contradiction→raise, no-exit no-op), detector
      (reversal hit, regression hit, clean pass, closed-set boundary), witness integration.
- [ ] `ARCHITECTURE.md` DM seam doctrine notes the fact/state-reversal seam as deterministic
      close-boundary enforcement, distinct from FR-539 entrance prose and FR-537 cast scope.

## Alternatives Considered

- **Strengthen the prose instruction** ("do not undo resolved events"): rejected — this is
  exactly the advisory-prose path that already fails; FR-534 established a probabilistic gate is
  too soft for a hard invariant. The fix must be deterministic and at the boundary.
- **One mega-gate covering entrances + facts + reconciliation**: rejected — entrances are
  FR-538/539's owned scope (prose staging); conflating them with fact persistence blurs two
  distinct seams and risks `false_duplicate`. This FR is scoped to facts + the
  exit/ledger reconciliation bug.
- **Reconcile in the turn loop instead of at close**: rejected — the exit is *reported* by the
  director mid-chapter but the *ledger* is emitted at close; reconciliation belongs where the
  persisted state is written (the close boundary), the single site the next chapter inherits
  from (`the_one_law`).
- **LLM-judge fact reversals**: deferred to a possible Phase-2 escalation; v1 deterministic
  closed-set detection catches the measured 10029-BC class without a model.

## Related

- [FR-537](FR-537-dm-v2-chapter-scoped-cast.md) — cast scope; the ledger-render scoping it
  deferred (A1) is motivated here by the reconciliation slice
- [FR-538](FR-538-dm-v2-seam-entrance-witness.md) — the witness this detector extends (facts
  alongside entrances)
- [FR-539](FR-539-dm-v2-seam-aware-final-cut.md) — entrance prose staging; orthogonal (this is
  fact persistence + exit reconciliation)
- FR-507 / FR-509 / FR-510 / FR-526 — lifecycle/resurrection family; the reconciliation bug is
  the close-graph half they did not cover
- [chapter_ops.py](../examples/dungeon_master/api/chapter_ops.py) — `close_chapter` world_state
  derivation (reconciliation site)
- [chapter_open.py](../examples/dungeon_master/api/chapter_open.py) — `_chapter_cast_exits`
  (the reported-exit source)
- [seam_entrance.py](../examples/dungeon_master/api/seam_entrance.py) — sibling detector pattern
- [gap_detectors.py](../examples/dungeon_master/api/gap_detectors.py) — `seam_precondition_gap`
  already detects the lethal-seam at **outline** time; part A is the **close-write** half it cannot reach
- [continuity-projection-plan.md](../examples/dungeon_master/docs/continuity-projection-plan.md)
  — **pre-existing design note** that diagnoses the Witta/Arnulf class and stages the fix; part A
  IS its "step 2 cheap fix" (see Judgement)
- `outputs/dungeon-master/10029-BC/review.md` — food-bundle reversal + Arnulf-alive-after-exit
  evidence

## Judgement (2026-06-19) — APPROVED part B; part A CONDITIONAL on de-duplication

**Verified against the codebase:** `seam_packet` carries `resolved_events`/`must_carry_facts`/
`opening_constraints`; `chapter_memory` carries `character_state_deltas` + `forbidden_regressions`;
`chapter_open._chapter_cast_exits` exists (L196) and is already consumed by the roster filter (L276);
`close_chapter` is async (chapter_ops.py L215); `gap_detectors` is the right home. The mechanics are real.

**Major finding — uncited prior art (`research_as_inventory` risk).** A pre-existing design note,
`examples/dungeon_master/docs/continuity-projection-plan.md`, already diagnoses the Witta/Arnulf
resurrection as *"the close-time extractor mis-read a death it had just narrated"* and stages a
four-step fix: (1) witness/investigation RED test over the seam cards; (2) an ebook judge→amend
gate ("death markers in prose forbid `existence_state: alive`"); (3) a write-once monotonic
*projected* lifecycle ledger; (4) replay-summary gate. **Part A of this FR is a structural variant
of that plan's step 2** — it reconciles against the director's `cast_exits` instead of prose
death-markers. This FR must cite that plan and position part A explicitly as its step-2 cheap fix,
NOT as the step-3 re-architecture. Failing to cite it re-derives an existing diagnosis.

**Verdict — SPLIT the FR.**
- **Part B (generic fact-reversal gate — the food bundle): APPROVED, this is the novel, distinct
  contribution.** The projection plan is lifecycle-only and does NOT cover arbitrary resolved-fact
  reversal (secured↔unclaimed). This is the highest-leverage genuinely-new work. Keep it as FR-542.
  Conditions: (a) closed-antonym set is frozen, no fourth special case (`regex_fourth_exclusion`);
  (b) measurement-first into `continuity_witness.json`, never subtracting from the witness gap set
  (`gate_checks_shape_not_substance`); (c) gate promotion deferred to a Phase-2 follow-up with
  corpus evidence (`audit_gate`).
- **Part A (lifecycle close-write reconciliation): MOVE into the FR-507/509/510/526 lineage** under
  `continuity-projection-plan.md`, where its diagnosis already lives. Bundling a known-diagnosed
  lifecycle bug with the novel fact-gate mixes two boundaries (lifecycle vs arbitrary fact) and two
  owners (the projection-plan lineage vs this FR). If kept here, it must (a) cite the plan, (b) be a
  separate commit with its own RED test reproducing the Ch2 Arnulf-alive-after-`cast_exit` state,
  and (c) declare it the *interim* structural fix that the plan's step-3 projection will later
  supersede (no `backward compatibility` debt — state the supersession path).

**Open question for the requester (blocks freeze):** keep part A here as the interim fix, or fold
it into the projection-plan lineage? Part B is frozen and authorized regardless.

## Implementation (2026-06-19) — ENFORCED

Both parts shipped as **two distinct commits** (`mixed_commits_erode_auditability`): Part A is
the interim lifecycle reconciliation, Part B the novel generic gate.

**Part A — close-boundary ledger reconciliation.** Landed in a new leaf
`api/ledger_reconcile.py` (NOT `chapter_ops` as first drafted): `chapter_ops` was at the 449/450
size ceiling, and the reconciliation is a pure, no-LLM, roster-bounded ledger transform with no
dependency on the close graph — a clean FR-536 concern seam. `reconcile_ledger_exits(world_ledger,
exits)` marks any director-benched actor the prose-derived ledger left present as absent
(`_ABSENCE_STATUS_TOKENS` closed literal set; `_RECONCILED_EXIT_STATUS`), returns a new ledger,
never mutates. Wired into `chapter_ops.close_chapter` after the relationships commit. The
cast-exit accrual (`chapter_cast_exits`) **moved from `chapter_open` to `turn_state`** beside its
`turn_direction`/`chapter_turns` dependencies (the same ceiling pressure; the right home all
along). 7 tests (`test_ledger_exit_reconciliation.py`).

**Part B — generic fact-reversal gate.** Landed in a new leaf `api/fact_reversal.py` (NOT
`gap_detectors` as the AC text says — `gap_detectors` is at 449/450). `fact_reversal_gap(prev_card,
card)` diffs prior `resolved_events` vs current facts (→ `resolved_event_reversal`) and prior
`forbidden_regressions` (read from **chapter_memory**, per the field-naming correction) vs current
facts+deltas (→ `forbidden_regression_violation`), requiring the opposite side of the SAME frozen
antonym pair on a shared subject token. Surfaced as a visibility-only `fact_reversal` block in the
continuity witness (`emit_continuity_witness.fact_reversal_summary`, posture
`visibility-not-gate` — honoring `audit_gate`: measure before gating). 5 tests + witness regression
(`test_fact_reversal_gap.py`, 12 total with the witness suite).

**AC deviation:** the AC references `gap_detectors.fact_reversal_gap`; the canonical home is
`fact_reversal.fact_reversal_gap` (size-ceiling split). Part A's home is `ledger_reconcile`, not
`chapter_ops`.
