# Feature Request: FR-533 — DM v2: Projection-vs-Emergence Spike (one hand-authored lifecycle ledger)

**Priority:** HIGH (decision-gating — blocks the refactor-vs-rewrite call)
**Type:** Investigation (spike — produces evidence, not production code)
**Status:** **ENFORCED (2026-06-19).** The spike ran; the deterministic precedence gate
(`ContinuityMemoryConflictError`) refused the dead-Witta injection pre-LLM. That refusal
is the finding: it half-inverts the FR's premise (the prose death is the error to
*prevent*, not the truth to *record*) and **strengthens the refactor call**. The vividness
axis is unanswerable via Witta (her correct projected state is *alive*). Fourth
decision-rule branch fired. See Implementation (2026-06-19).
**Effort:** ~0.5 day
**Requested:** 2026-06-18

## Summary

Before committing to the continuity-projection refactor (see
`examples/dungeon_master/docs/continuity-projection-plan.md`), settle the one empirical
question the whole decision turns on: **does projecting the character lifecycle up front
starve the turn generator of the emergent detail that makes its prose good?** This FR
hand-authors a single chapter's lifecycle ledger from `10026-BC`'s own facts, projects the
cast / prose-exclusion from that ledger, runs the **existing, unchanged** turn engine
against it, and compares the resulting prose against the baseline chapter. It builds
nothing reusable: the deliverable is a documented before/after verdict that says *refactor
is safe* or *projection and emergence are entangled*.

## Value Statement

We learn — for the cost of one chapter's generation, not a rewrite — whether authoring
continuity invariants up front is orthogonal to or destructive of the emergent prose
quality, so the refactor/rewrite decision rests on evidence instead of intuition.

## Problem

The projection plan recommends a **refactor** of DM v2 (keep the turn engine + typed seam
schema + reviewer; invert one boundary so lifecycle is authored, not reconstructed). That
recommendation carries exactly one un-tested assumption: that the turn generator's vividness
is independent of the fact that `world_state` is *freshly derived from prior prose* each
chapter. If vividness is actually fed by that reconstruction, then forcing projection turns
DM v2 into `novel_generator` — trading lies (Witta "alive" after drowning) for flatness
(rigid, pre-determined prose). That is the only scenario in which the refactor is the wrong
call, and it is currently unknown. `working_system_inertia` cuts both ways: we must not
refactor *just because* the engine works, and we must not rewrite *just because* projection
is cleaner — only the prose comparison resolves it.

This is the `investigation_before_fix` cure: the bug (reconstruction lies) requires a
design change whose safety is itself uncertain. Split the uncertainty into a cheap spike
that produces the evidence, before any production change is authored.

## Proposed Solution

A throwaway spike harness under `examples/dungeon_master/spikes/` (or `tmp/` if we prefer
it never lands), in four steps:

1. **Extract ground-truth ledger.** From `10026-BC/story.json`, hand-author a *correct*
   single-chapter lifecycle ledger for the seam with the clearest reconstruction lie —
   the **ch7→ch8 Witta death** (ch7 prose narrates the drowning; ch7
   `character_lifecycle` wrongly records `existence_state: "alive"`). The hand-authored
   ledger records what the prose actually established: Witta `existence_state:
   "confirmed_dead"`, `source_chapter: 7`.

2. **Project, do not reconstruct.** Feed ch8's turn engine a cast / prose-exclusion derived
   *from the authored ledger* (Witta excluded as dead) instead of from ch7's reconstructed
   `seam_packet`. Change nothing else — same premise, same turn cap, same prompts, same
   model. Only the source of the lifecycle truth changes.

3. **Run the unchanged turn engine.** Generate ch8 prose under the projected cast.

4. **Compare.** Put the projected-ch8 prose beside baseline-ch8 prose (the one that
   resurrected Witta). Score on two axes:
   - **Continuity** (does Witta stay dead? — the bug we want fixed), via the existing
     reviewer's `Continuity` axis or direct inspection.
   - **Emergence / vividness** (did the prose go flat?), via the reviewer's prose/quality
     axis **and** a human read recorded in the verdict.

### Decision rule the spike feeds

```
IF projected ch8 keeps Witta dead AND prose vividness holds (no flatness regression):
    -> REFACTOR is safe. Invariants and emergence are orthogonal.
       Proceed to author the projection refactor FR on DM v2's existing schema.
ELSE IF Witta stays dead BUT prose goes flat:
    -> Projection and emergence are ENTANGLED.
       The real design question becomes "thinnest ledger that fixes reader-salient
       breaks without strangling emergence" — a harder FR, still on DM v2's schema,
       NOT a novel_generator rewrite.
ELSE (Witta still resurrects under projection):
    -> The lie is not at the close-time boundary alone; re-open root-cause analysis
       before any refactor.
```

## Judgement (2026-06-18 — authority granted, scope sharpened)

The Judge traced the lever end-to-end through the live code before granting authority
(`turn_ops.py::_filter_roster_for_lifecycle` → `seam_packet.py::validate_character_lifecycle`).
The trace changed the FR's framing, so the scope is narrowed, not merely approved.

- **J1 — The projection machinery ALREADY EXISTS and ALREADY WORKS; the spike has only ONE
  real unknown.** `validate_character_lifecycle` emits a `state_contradiction_violation`
  for any `confirmed_dead` name in the chapter-open cast, and `_filter_roster_for_lifecycle`
  drops it at turn 1. So when the inherited `seam_packet` tells the truth, ch8's cast is
  projected correctly *today* — no new wiring needed. The bug is purely that ch7's
  close-time extractor wrote `existence_state: "alive"` for a character it had just drowned
  (the reconstruction lie). **Therefore the continuity axis of this spike ("does Witta stay
  dead?") is a near-foregone conclusion** — we know the deterministic gate fires. The spike
  reduces to a single genuine question: **when the turn engine is handed a truthful (dead)
  lifecycle and Witta is removed from ch8's cast, does the prose stay vivid, or does it go
  flat?** That is the orthogonality test, and it is the ONLY uncertain output. The FR's
  two-axis framing is down-weighted accordingly (J4).

- **J2 — The lever is exact and minimal; the FR's hand-wave is replaced by it.** "Feed
  ch8's turn engine a cast projected from the ledger" resolves concretely to: copy
  `10026-BC/story.json`; in the copy, edit chapter 7's `seam_packet.character_lifecycle`
  Witta entry from `existence_state: "alive"` to `"confirmed_dead"` with
  `visibility_mode: "absent"`; clear chapter 8's played turns; re-play chapter 8 from turn
  1 via the existing turn loop. **No production code is touched** — only the input document
  changes. This is the genuine projection, because the existing gate does the exclusion.

- **J3 — A throwaway driver script IS permitted, and MUST be flagged as non-production.**
  Re-playing one chapter from a doc requires a small script that calls the existing
  adapter turn loop (`running_scene`/`invoke_turn`/final cut) over the edited copy. It
  lives in `tmp/` or `examples/dungeon_master/spikes/` and ships nothing reusable. If a
  clean ledger shape emerges, it is recorded as a NOTE for the future refactor FR, **not**
  shipped here. The script is evidence-production, not the feature.

- **J4 — Vividness is the primary axis; the human read is the primary signal.** The
  cross-seam reviewer's quality axis is unreliable on a single out-of-context chapter
  (FR-532's critic is calibrated across seams, not within one). So the **human read is the
  load-bearing vividness signal**; the reviewer axis is secondary corroboration only. The
  continuity axis is demoted to "confirm the gate fired and Witta is absent (expected)."

- **J5 — The verdict is a single-sample DEMO, not a measurement; it must not be
  over-claimed.** LLM generation is non-deterministic: projected-ch8 differs from
  baseline-ch8 in both the seam edit AND sampling noise. One re-play cannot *measure* a
  flatness delta. It can only produce a go/no-go *intuition* strong enough to pick the
  decision-rule branch (`demo_vs_test`: this proves the abstraction is worth pursuing, it
  does not prove a constraint). The written verdict MUST state "single-sample qualitative
  signal" in those words. If the read is ambiguous, the honest outcome is "inconclusive →
  generate 2-3 more projected samples," not a forced verdict.

- **J6 — Example/spike-scoped (FR-474 J3).** NO `@pytest.mark.req`. If any test lands it is
  a smoke assertion that the gate drops a `confirmed_dead` name (a unit confirmation of
  J1, not the spike's deliverable). Changelog `type:chore` (or `docs`) — NO `feat`/`fix`,
  so no changelog-`req:`/diary CI-gate burden beyond the Distill diary entry already
  required by the rite. Single seam only (ch7→ch8 Witta); do NOT touch the Arnulf or
  replay classes — those are fixes, not orthogonality tests.

**Scope frozen:** one hand-edited `story.json` copy (ch7 Witta → `confirmed_dead`/`absent`),
one throwaway re-play of ch8, one written single-sample verdict mapped to the decision
rule, one diary entry. Continuity axis = confirm-the-gate-fired. Vividness axis (human
read primary) = the real question. No production wiring, no schema shipped, no second seam.

## Acceptance Criteria

- [x] A copy of `10026-BC/story.json` has chapter 7's `seam_packet.character_lifecycle`
      Witta entry edited to `existence_state: "confirmed_dead"`, `visibility_mode:
      "absent"` (the truthful projection the close-time extractor failed to write).
- [x] Chapter 8 re-play is driven by the **unchanged** turn engine over the edited copy via
      the existing FR-522 harness (`chapter_replay.replay_chapter`); throwaway driver
      `tmp/fr533_projection_spike.py`, nothing else changed. **Outcome:** the re-play was
      refused by the deterministic precedence gate pre-LLM (see Implementation) — a
      legitimate, more informative result than a prose sample.
- [x] The re-play attempt confirms the deterministic gate's behaviour: the LOW-precedence
      seam edit is overridden by the HIGHER plan-derived sources, so the death cannot be
      injected downstream (the gate already enforces plan-over-prose).
- [~] Vividness comparison: **N/A via Witta** — her correct projected state is *alive* (six
      plan-derived sources + synopsis), so there is no projected-death prose to read.
      Recorded as a verdict, not a forced sample (J5).
- [x] A written verdict — labeled a **single-sample qualitative signal** (J5) — maps the
      result onto the decision rule (fourth branch: premise half-inverted, refactor
      strengthened). Captured in
      `examples/dungeon_master/docs/continuity-projection-plan.md` §6.
- [x] The spike introduces **no reusable production wiring** (driver lives in `tmp/`) and
      **no** `feat`/`fix` surface; the corrected ledger shape is a NOTE for the refactor FR.
- [x] Distill: a diary entry recording the spike outcome and which decision-rule branch fired.

## Implementation (2026-06-19)

- **`tmp/fr533_projection_spike.py`** (throwaway, J3): copies `10026-BC/story.json`, edits
  ch7's `seam_packet` Witta entry to `confirmed_dead`/`absent`, and calls the existing
  FR-522 `chapter_replay.replay_chapter(doc, "8")`. No production code touched.
- **The deterministic precedence gate blocked the re-play pre-LLM.**
  `_enforce_memory_precedence_gate` raised `ContinuityMemoryConflictError`:
  `{name: witta, higher_source: chapter_memory, lower_source: seam_packet, detail: "alive
  conflicts with confirmed_dead"}`. The driver catches it and records the block as the
  outcome (`tmp/fr533-spike-report.md`).
- **The data trace that reframes the premise** (verified against `story.json`):
  - ch7 composed `text` *does* kill Witta ("She vanished into the flood as it seized
    her..."), but the per-turn recaps are non-monotonic — turn 7 sweeps her off, turns
    8–16 keep her alive and restrained (FR-501 no-progress tail). Final-cut composition
    chose death; the turn ledger leaned alive.
  - **Six** structured sources unanimously record Witta `alive`, plan-pulled:
    `world_state.status`, `chapter_memory.character_state_deltas`, `irreversible_facts`
    ("Witta is alive at the end of the chapter, not dead or swept away"),
    `forbidden_regressions` ("FORBID: Witta is dead"), `seam_packet`, and
    `live_synopsis.character_states`. Witta is the plan-critical antagonist the synopsis
    needs alive for the rest of the arc.
- **Verdict (fourth decision-rule branch).** The premise ("correct the seam to dead = the
  truthful projection") is half-inverted: for a plan-protected character the prose death is
  the error to *prevent*, not the truth to *record*. The precedence gate already enforces
  plan-over-prose for **bookkeeping**; the architectural gap is that the same precedence is
  **not fed into prose generation**. This **strengthens the refactor** — the expensive
  asset (typed ledger with working precedence) exists; the fix is one additive edge
  (protected-character set → turn director + final-cut), not an engine rewrite. A
  `novel_generator` rewrite would re-pay for precedence the gate already provides.
- **Scope honoured:** single seam (ch7→ch8 Witta); no Arnulf/replay work; no production
  wiring; `chore`-class change (no changelog fragment / `req:` required, J6).

## Alternatives Considered

- **Skip the spike, just refactor** — rejected; it bets the refactor budget on the
  un-tested orthogonality assumption. The spike costs one chapter; being wrong costs the
  engine.
- **Skip the spike, rewrite on `novel_generator`** — rejected harder; pays to re-derive the
  typed schema DM v2 already owns *and* inherits novel_generator's own flat-prose disease,
  all to import a single property (plan→prose direction) a refactor installs by inverting
  one boundary. (See plan doc §"why rewriting on novel_generator is the seductive wrong
  move.")
- **Spike all three break classes (Witta/Arnulf/replay)** — rejected for this FR; the
  orthogonality question is fully answered by one clean death. The other classes are
  fixes, not orthogonality tests, and belong to the refactor FR.

## Related

- `examples/dungeon_master/docs/continuity-projection-plan.md` (the plan this spike gates —
  §4 staging, §"why this is not just more gates").
- `10026-BC/story.json` (the evidence: ch7 prose vs ch7 `character_lifecycle` Witta lie).
- FR-530 (continuity witness — the measurement this spike reuses for the continuity axis),
  FR-532 (reader-calibrated reviewer — supplies the vividness/quality axis).
- `examples/demos/novel_generator` (pure projection — the engine the *else* branch must
  NOT become), `examples/ebook` (judge→amend gate — borrowed by the eventual refactor).
- Scripture: `investigation_before_fix`, `working_system_inertia`, `constraint_over_code`.
