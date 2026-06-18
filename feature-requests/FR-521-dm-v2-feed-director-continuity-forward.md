# Feature Request: FR-521 — DM v2: Feed the Director's Continuity Signal Forward

**Priority:** MEDIUM
**Type:** Bug (continuity enforcement gap)
**Status:** **Enforced via S2 roster-drop (2026-06-18)** — S1 (advisory feed-forward) was implemented, witness-falsified (8/16 → 13/16), then **reverted**. J2 (chapter-scoped `missing_presumed_dead` death-point) stands. **S2** (drop a director-exited actor from the running cast via the structured `cast_exits` field) is the enforced fix: the Ch3 witness dropped Arnulf re-flags **8/16 → 0/16**, with Arnulf acting legitimately through his exit turn (t1–t3) then benched (t4–t16). See **S2 Implementation** and **S2 Witness Result**.
**Effort:** ~0.5 day
**Requested:** 2026-06-18

> **Supersedes FR-520** (rejected). FR-520 proposed a new pure
> `positional_memory.py` to *produce* a turn-grained continuity record. The
> gate-open review found that record **already exists** — the director emits a
> per-turn `continuity` judgement — so the fix is wiring, not a new module. This FR
> carries that corrected scope.

## Summary

The DM v2 director already detects intra-chapter continuity breaks **every turn**
(its `continuity` side-channel), but the detection is a dead end: the prior turn's
`continuity`/`steer` flags are recorded on the turn card and never fed into the
next turn's context. So the cast's intent map and the recap for turn N+1 are
generated with **no knowledge** of the warning, re-propose the same break, and the
director re-flags it — an advisory with no feedback loop. Thread the prior turn's
director flags into `running_scene` so turn N+1 is generated knowing them, and
(escalation) drop a repeatedly-flagged actor from the roster using the existing
lifecycle-gate machinery.

## Value Statement

A reader stops seeing a character the chapter has just killed or swept away keep
acting turn after turn — because the warning the director already raises now
actually steers the next turn, instead of being recorded and ignored.

## Problem

The play loop runs each turn as `invoke_turn`: **map** (per-character intents) →
**direct** (the director's structured judgement) → **recap**. The director
(`prompts/turn_direct.yaml`) is instructed to flag, in `continuity`, "a character …
already lost/seized reappearing" and lifecycle breaches; the result is persisted as
`turns[n].direction.continuity` (`turn_ops.invoke_turn`).

But `turn_ops.running_scene(doc, cid, n)` — the single context string handed to
**both** the intent map and the director for turn N — is built from only:
- this chapter's `summary` (the plan),
- the inherited `world_state` (chapter START),
- the last-3 **recaps** (`turns[..].recap.text`),
- the beats block.

It does **not** include the prior turn's `direction.continuity` or `direction.steer`.
The witnessed consequence (10022-BC Ch3, LangSmith-confirmed): the director flagged
Arnulf on **8 of 16 turns** —

> t3: *"Arnulf acts after being swept away and disappeared; he cannot physically
> grab the bank edge or haul himself onto firmer ground."* (also t2, t4, t6, t7,
> t8, t10, t16)

— yet each following turn's intent map, unaware of the flag, had Arnulf act again.
This is the Scripture's `detection_without_enforcement` trap: *"lint without gate =
advisory."* The detection is precise; only the **feedback** is missing.

### Why this is not a new-module problem (FR-520's error)

FR-520's Problem claimed "there is no turn-grained record of who held what at turn N
for the next turn to consult." False: the director **is** that per-turn record. All
three FR-519/FR-520 witnesses (10021-BC ch6 Hagan; 10022-BC ch3 + ch8 Arnulf) are
lifecycle/death-point breaks the director already names. Building a parallel memory
layer to re-derive what the director already extracts would duplicate the signal and
add a second fallible prose→structured boundary for no benefit.

## Judgement (2026-06-18)

Decision: **Granted with amendments; scope frozen.** The diagnosis is correct and
load-bearing-verified: `turn.yaml` feeds the single `scene` string (from
`running_scene`) into **all three** turn nodes — `intents` (the map where the break
originates), `direct`, and `recap` — so threading the prior flags into `scene`
reaches the exact node that re-proposes the break. The root cause
(`detection_without_enforcement`) is real and the fix is wiring, not a module. The
core S1 is approved. Four amendments are frozen before enforcement; S2 is gated.

**J1 — S1 must feed a WINDOW of flags, not only turn n−1 (blocker).** The recorded
Ch3 flags land on turns 2,3,4,6,7,8,10,16 — i.e. **t5, t9, t11–15 carried no flag**.
Feeding only `turn_direction(doc, cid, n-1)` means after any clean turn the
constraint **vanishes**, even though the underlying break (Arnulf swept away) is
still true. S1 must carry the flags from the **same last-3-turn window** the recaps
already use (`turns[:n-1][-3:]`), unioned, so a one-turn gap does not drop the
constraint. Cheap, consistent with the existing context window, deterministic.

**J2 — Distinguish episodic flags from monotonic lifecycle facts (scope clarifier).**
A continuity *flag* is episodic (the director may or may not re-raise it any given
turn); a *death/sweep* is monotonic (once true, true for the rest of the chapter).
The windowed-flag feed (J1) handles the episodic signal. The **monotonic** death
fact must ride the chapter-scoped death-point set (the `missing_presumed_dead`
widening), not the episodic flag window — so a character established dead/swept at
turn k is constrained for **every** later turn, not just within a 3-turn shadow.
S1 feeds flags; the death-token widening feeds the durable fact. The redraft must
state both channels and not rely on the flag window alone to carry a death.

**J3 — S2's actor extraction is a NEW fallible boundary the FR claims to avoid
(blocker on S2 only).** The continuity flags are **free-form prose** ("Arnulf acts
after being swept away…"). To "drop the actor flagged ≥K consecutive turns," S2 must
extract *which* roster name the prose refers to — a prose→structured step.
`_filter_roster_for_lifecycle` keys off **structured** seam lifecycle data, not
prose, so S2 cannot simply reuse it without a name-matching layer. Resolve by
**either** (a) restricting S2 to deterministic roster-name substring matching against
the flag text, pinned by a test, **or** (b — preferred) having the director emit the
offending actor as a **structured field** (e.g. `continuity_actors: [name]`)
alongside the prose, so the exclusion keys off structure, not a regex over prose.
S2 is **not** approved until this is pinned; S1 ships without it.

**J4 — Negation-echo guard (test obligation).** The flag text reaches the `recap`
narrator node too (same `scene`). Injecting "do NOT have Arnulf grab the bank" risks
the known LLM negation-echo failure where the forbidden content leaks into prose. The
witness/seam tests must assert the carried-constraint text does **not** appear
verbatim in the rendered recap, and the block must be phrased as a constraint on
*intent selection*, not a narration instruction.

**J5 — The witness is corroboration, not a gate (ratified).** "Re-flag count drops
vs the 8/16 baseline" is an LLM-dependent smoke signal — keep it as evidence, but the
**proof** is the deterministic seam tests (feed-forward present, windowed, absent on
turn 1/no-flags, negation-echo absent). The existing `running_scene` tests are the
regression floor: turn-1 and no-flag output must stay byte-identical to today.

Granted: implement **S1 with J1+J2+J4** now; **S2 gated on J3**. The death-token
widening is chapter-scoped (no bar on a legitimate return). Carry the Ch3
(presumed-dead acts), Ch8 (post-death running turn), and ch6 (legitimate return)
cases as fixtures.

## Proposed Solution

Two changes, smallest first; ship S1 alone and only add S2 if a witness survives it.

### S1 — Feed-forward (the core fix)

In `running_scene`, after the recap history, append the **prior turns'** director
continuity/steer flags (from the same last-3-turn window the recaps use, J1) as an
explicit constraint block, so turn N+1's intent map and director both read them:

```python
# turn_ops.running_scene(doc, cid, n), after `so_far` is built.
# J1: union the flags across the same last-3-turn window as the recaps, not just n-1,
# so a single clean turn does not drop a still-true constraint.
window = range(max(1, n - 3), n)  # prior turns feeding this turn's context
flags: list[str] = []
steers: list[str] = []
for k in window:
    d = turn_direction(doc, cid, k)
    flags.extend(d.get("continuity") or [])
    s = (d.get("steer") or "").strip()
    if s:
        steers.append(s)
flags = list(dict.fromkeys(flags))  # de-dup, preserve order
if flags or steers:
    lines = "\n".join(f"- {f}" for f in flags)
    # J4: phrased as a constraint on what the cast may INTEND, never a narration
    # instruction, so the forbidden text cannot echo into the recap prose.
    scene += (
        "\n\nCONTINUITY CONSTRAINTS CARRIED FROM RECENT TURNS — when choosing this "
        "turn's intents, do NOT have a character repeat a break flagged here:\n"
        f"{lines}"
        + ("\n- STEER: " + "; ".join(steers) if steers else "")
    )
```

No new extraction boundary (the director already extracts), no new module, no
persisted state beyond the existing `direction` side-channel. The **monotonic** death
fact (J2) is carried separately by the chapter-scoped death-token widening below, not
by this episodic window.

### S2 — Escalation (only if S1 leaves a witnessed residual)

When the **same actor** is named in a `continuity` flag for **≥K consecutive
turns** (K to be pinned by the witness; start at 2), deterministically drop that
actor from the turn's roster for the next turn, reusing the existing
`_filter_roster_for_lifecycle` / `build_allowed_scene_cast` path that already
removes lifecycle-gated actors at chapter open. This turns a repeated advisory into
a hard, deterministic exclusion **without** a new module — an existing gate extended
one rung. Enforcement stays **preventive** (the actor is absent from the next turn's
intent map), never raising on an already-generated turn (which would dead-end play,
the reason FR-519 went warn-only).

### Death-token widening (carried from FR-520 evidence #1)

Independently, add `missing_presumed_dead` (and `presumed_dead`) to the lifecycle
states the director and the FR-519 warn-only detector treat as a death-point, so the
Ch3 *presumed-dead → acts* class is recognized — but **chapter-scoped**, so a
legitimate return (Arnulf ch6, the synopsis resurrection) is not barred. This is an
input to the existing director awareness and `dead_character_names`, not a new layer.

## Acceptance Criteria

- [x] `running_scene(doc, cid, n)` includes the union of the prior **3 turns'**
      `direction.continuity` flags (and non-empty `steer`s) as an explicit
      carried-constraint block (J1); absent cleanly when there are none and on
      turn 1. (`_continuity_constraints_block`, `turn_ops.py`)
- [x] Unit test: a flag on turn n−2 with a **clean** turn n−1 still appears in turn
      n's `running_scene` (the windowing fix — guards the t5/t9 gap that the
      n−1-only design would drop). (`test_running_scene_continuity_window_survives_one_clean_turn`)
- [x] Unit test: given a turn whose `direction.continuity` names an actor, the next
      turn's `running_scene` text contains that flag (the feed-forward seam).
      (`test_running_scene_carries_prior_turn_continuity_flag_forward`)
- [x] Unit test: turn 1 and a turn with no prior flags produce a `running_scene`
      with no continuity-constraint block (no spurious empty section); existing
      `running_scene` tests stay byte-identical (regression floor, J5).
      (`test_running_scene_turn_one_has_no_continuity_constraint_block`,
      `test_running_scene_no_prior_flags_has_no_continuity_constraint_block`)
- [x] Unit test (J4): the carried-constraint block is **intent-scoped, not a
      narration instruction** — the deterministic structural guard against the
      negation-echo (verbatim-recap-absence is the LLM witness, not a unit gate, J5).
      (`test_running_scene_continuity_block_is_intent_scoped_not_narration`)
- [ ] (S2, gated on J3) Unit test: an actor named in a **structured**
      offending-actor field for ≥K consecutive turns is excluded from the next
      turn's roster via the existing lifecycle-filter path; a single/non-consecutive
      flag does not exclude. **Deferred** — J3's structured field does not yet exist;
      not built (no witness demands it).
- [x] `missing_presumed_dead` is treated as a chapter-scoped death-point (J2) by the
      warn-only `dead_character_names` within-lane; the cross-chapter before-open bar
      stays `confirmed_dead`-only, so a return at/after the allowed reappearance
      chapter is not barred (Arnulf ch6 fixture).
      (`test_missing_presumed_dead_routes_to_dead_within_chapter`,
      `test_presumed_dead_inherited_seam_does_not_bar_before_open`)
- [ ] Witness (corroboration, not a gate — J5): re-generate a 10022-BC-class book
      (or replay the Ch3 fixture) and confirm the per-turn Arnulf re-flag count drops
      materially vs. the recorded 8/16 baseline. **Deferred** to a witness run.
- [x] Tests added; `examples/dungeon_master/docs/architecture.md` notes the
      director-continuity feed-forward in the turn-context section.

## Implementation (2026-06-18)

- **S1 feed-forward** (`turn_ops._continuity_constraints_block`): unions the
  trailing 3-turn window's `direction.continuity` flags + non-empty `steer`s
  (de-duped, first-seen order), appended to `running_scene` as a
  `CONTINUITY CONSTRAINTS CARRIED FROM RECENT TURNS` block phrased as a constraint
  on **intent selection** (J4). Empty string when nothing to carry (turn 1 / no
  flags), so all prior `running_scene` tests stay byte-identical (J5).
- **J2 death-point widening** (`turn_ops.dead_character_names`): added
  `_PRESUMED_DEAD_TOKENS = {missing_presumed_dead, presumed_dead}`, unioned into the
  within-chapter status check (`_WITHIN_DEATH_STATUS_TOKENS`) and the close-seam
  existence-state check (`_WITHIN_DEATH_EXISTENCE_STATES`). Chapter-scoped — fed
  only from this chapter's `closed`; the before-open seam bar stays
  `confirmed_dead`-only, protecting the synopsis return (Arnulf ch6).
- 9 new tests; full DM suite 205 passed, ruff + lint-imports clean.

> **S1 reverted (2026-06-18):** the feed-forward block and its 6 unit tests were
> removed after the witness falsified S1 (below). The J2 widening and the replay
> harness were kept. The enforced fix is **S2** — see **S2 Implementation**.

## Witness Result (2026-06-18) — S1 falsified

A single-chapter replay (`scripts/replay_chapter_continuity.py`) re-played
10022-BC **Ch3** ("Arnulf Lost to the Water") with the inherited state (Ch1–Ch2)
held constant, so the only changed variable was S1's feed-forward. The witness was
expected to show the Arnulf re-flag count drop below the recorded **8/16** baseline.
It **rose to 13/16**.

Inspecting the replayed intents explains why and overturns S1's premise:

- **Arnulf is in the cast and acting in all 16 turns of both runs** — "I haul
  myself onto the firmer bank", "I lunge up and grab Reinmar's staff". The
  per-character intent map generates an intent for every roster member; the carried
  advisory block ("do NOT let Arnulf repeat this break") **did not remove him from
  the cast and was simply ignored**. An advisory in the scene is not a gate — only
  dropping the actor from the roster prevents the break. This is
  `detection_without_enforcement` one level deeper: the signal was relocated, no
  mechanism that can *prevent* the break was added.
- **The metric is contaminated.** `running_scene` feeds one `scene` string to all
  three turn nodes (map → direct → recap), so the carried block also lands in the
  **director's** input. The director's `continuity` count — the metric — can now
  echo the warning S1 injected, so the count is no longer an independent measure of
  the underlying break.

**Conclusion.** S1 (advisory feed-forward) is at best inert and at worst
counterproductive + metric-polluting; it does **not** achieve the FR's value
statement. J2 (the chapter-scoped death-point) stands — it is independent and
correct. The witnessed root cause is **roster membership**: the swept-away actor
keeps full agency for the rest of the chapter. The real fix is **S2** — drop the
actor from the next turn's roster once removed — which J2's within-chapter
death-point now supplies the signal for, without needing J3's structured field.

**Recommended next step (decision pending):** revert the S1 feed-forward block (keep
J2 + the replay harness) and reopen as an S2 escalation: feed the within-chapter
death-point into `_filter_roster_for_lifecycle` so a swept-away/presumed-dead actor
is dropped from the cast mid-chapter, turning J2's detection into enforcement.

## S2 Implementation (2026-06-18) — the enforced fix

The S1 advisory block and its 6 unit tests were **reverted**
(`_continuity_constraints_block` removed; `running_scene` restored to byte-identical
pre-FR-521 output). J2 and the replay harness were kept. S2 was then implemented:

- **Structured director channel** (`prompts/turn_direct.yaml`): added a
  `cast_exits` field — the NAMES of rostered characters who have left the scene this
  chapter (killed, drowned, swept away) and must not act again. A character may act
  right up to and including the turn they exit; the director names them once that
  turn. This is the structured authority J3 called for — distinct from the free-text
  `continuity` flag (which only *reports* a break after it has happened). Added to
  the prompt instructions, the JSON contract, and the `output_schema` `required` list.
- **Direction normalisation** (`turn_ops._direction_dict`): carries `cast_exits`
  through as a `list[str]` alongside the other structured fields.
- **Roster enforcement** (`turn_ops._filter_roster_for_lifecycle` +
  `_drop_within_chapter_exits` + `_chapter_cast_exits`): before each turn, union the
  `cast_exits` from every *prior* turn of this chapter (chapter-scoped, accumulated
  so a later clean turn cannot resurrect a benched actor) and drop those roster ids
  (case-insensitive name match) from the cast. Never empties the cast — if everyone
  has exited, the unfiltered roster is kept and the chapter's turn cap closes it.
  This runs on every turn (the seam-gate layer still runs at turn 1).
- 7 new S2 unit tests (roster-drop, accumulation across a clean turn, no-exit
  no-op, never-empty, case-insensitive, `_direction_dict` preserves `cast_exits`);
  full DM suite **204 passed**, ruff + lint-imports clean.

## S2 Witness Result (2026-06-18) — confirmed

The same single-chapter replay re-played 10022-BC **Ch3** with S2 active. Arnulf
re-flags dropped **8/16 (baseline) → 0/16**, and the behaviour is non-degenerate:

| Turn | Arnulf acts | `cast_exits` | continuity flag |
|------|-------------|--------------|-----------------|
| t1–t2 | yes (grabs for Hilde, gets swept) | `[]` | none |
| **t3** | yes (final grab for the bank) | **`['Arnulf']`** | none |
| t4–t16 | **no (dropped from cast)** | `[]` | **none** |

Arnulf keeps full agency through the turn he is swept away, the director names his
exit once, and from the next turn the roster filter removes him — so the intent map
can no longer animate him and the director has nothing to flag. Detection (J2 +
`cast_exits`) became enforcement (the roster drop). Contrast S1's 13/16: the
difference between asking a generator not to and removing the option.

## Alternatives Considered

- **A new `positional_memory.py` (FR-520).** Rejected — duplicates the director's
  existing per-turn `continuity` extraction and adds a second fallible
  prose→structured boundary; no witness demands a possession/position lane.
- **Raise on a continuity break.** Rejected — FR-519 already established warn-only
  for within-chapter breaks because the played arc can legitimately have post-event
  action mid-resolution; a raise dead-ends play (FR-501's runaway lesson inverted).
  S2's roster-drop is preventive, not raising.
- **Final-cut-only enforcement (FR-519 status quo).** Insufficient — 10022-BC Ch8
  proved a clean final cut still leaves the break in the chapter body (running
  turns), so the signal must act during play, not only at close.

## Related

- **`feature-requests/FR-520-*`** — the rejected predecessor (new-module framing).
- `feature-requests/FR-519-*` — Phase 1 final-cut enforcement; this FR extends the
  same lifecycle signal into running turns.
- `feature-requests/FR-479-*` / `FR-481-*` — the director split and its
  `phase`/`continuity`/`steer` side-channel this FR feeds forward.
- `examples/dungeon_master/api/turn_ops.py` — `running_scene` (the feed-forward
  site), `turn_direction` (the prior-turn flags), `_filter_roster_for_lifecycle` /
  `build_allowed_scene_cast` (the S2 exclusion path), `dead_character_names` /
  `_DEAD_STATUS_TOKENS` (the death-token widening).
- `examples/dungeon_master/prompts/turn_direct.yaml` — the director that already
  emits `continuity`.
- Evidence: `outputs/dungeon-master/10022-BC/{story.json,review.md}`,
  `logs/10022-ls2.log` (final_cut inputs), `logs/10022-analysis.log` (ledger);
  director per-turn flags shown in the Ch3 `direction.continuity` dump.
