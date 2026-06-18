# Feature Request: FR-526 — DM v2: Close-Chapter Open-Thread Promotion (Forward the Unmet Return, Don't Drop It)

**Priority:** MEDIUM
**Type:** Bug (continuity defect, defense-in-depth)
**Status:** **SENT BACK TO PLAN (2026-06-18).** The proposed mechanism (a dict in
`seam_packet.open_threads`) **contradicts the live schema** — `open_threads` is
`list[str]` and the boundary normalizer drops non-string entries (J1). The correct
forward channel already exists and is load-bearing: `CharacterLifecycle`
(`existence_state=missing_presumed_dead`, `allowed_reappearance_from_chapter`) +
`_clamp_lifecycle_reappearance_to_plan` (J2). Residual value over FR-525 is unproven
and requires a close-seam probe FIRST (J3/J4, `investigation_before_fix`). See
Judgement below. Re-open only after the probe and with the typed channel.
**Effort:** ~1 day
**Requested:** 2026-06-18

## Summary

When a chapter force-closes under the 16-turn cap (FR-501) having played only the
removal half of a death-and-return reversal, `close_chapter` *correctly* commits the
actor terminal (`status='dead'`) — but the chapter's promised **return beat is dropped
on the floor**. This FR makes `close_chapter` detect that dropped promise and **forward
it as a real owed thread**: when a chapter commits an actor terminal AND its own later
beats promised that actor's return, emit the unfulfilled return into
`seam_packet.open_threads` with a `reappear_from` pointing at a later chapter — exactly
the pattern the 16 historically-clean books use (`10023-BC` defers Arnulf to ch6 via
`seam_packet … reappear_from=6`). This converts a phantom promise into an honest,
downstream-honorable thread that FR-523's state-aware re-outline can pick up.

## Value Statement

When a chapter genuinely couldn't play a promised return inside its turn budget, the
return is **carried forward as an owed beat** rather than silently lost — the reader
still gets the reappearance, one chapter later, instead of a contradiction.

## Problem

`close_chapter(doc, cid)` derives `{text, world_state, seam_packet}` from the
inherited ledger + the chapter's *played* recaps. Because it reads only what played,
it has no idea a beat went unfulfilled:

- The play loop force-closes at `n >= 16` (FR-501) after the removal half of a
  reversal. `close_chapter` commits `status='dead'` — *correct* for what played.
- The return beat (`beat[3]` in `10024-BC` Ch3, "Arnulf reappears alive …") never
  played and is **never recorded anywhere**. The seam handoff (`seam_packet`) carries
  `character_lifecycle` and `must_carry` but **no record of the owed return**, so the
  next chapter's re-outline (FR-523) cannot honor it — it only sees a committed death.
- Result: the reappearance the synopsis intended simply vanishes.

**Relationship to FR-525 (the primary fix).** FR-525 prevents the over-pack at the
*outliner* so the reversal is split across chapters up front — the clean cure. FR-526
is **defense-in-depth**: A1 of FR-525 is partly LLM-mediated (constrained re-outline),
so an over-pack can still slip through under a bad roll. When it does, FR-526 ensures
the missed return is *forwarded* rather than *dropped* — degrading gracefully from
"phantom in the same chapter" to "honest owed thread in a later chapter." The two
compose: FR-525 makes over-packs rare; FR-526 makes the residue recoverable.

**The One Law (`the_one_law`).** FR-526 normalizes at the **close boundary** — the
moment the chapter's true played outcome is known and the seam to the next chapter is
authored. The unmet intent is forwarded *as data* (an owed thread), not re-derived
downstream. It does NOT re-weave committed memory (the FR-524 rejection): the actor
stays correctly dead in *this* chapter's ledger; only the *seam* gains an owed-return
thread for a *later* chapter to honor.

### Condemning evidence (shared with FR-525)

`witness_metrics.beat_coverage_gap(doc, cid)` (committed `c6f197a3`) fires on
`10024-BC` Ch3 (Arnulf `dead` vs beat[3] "reappears alive"). FR-526's GREEN target is
**not** to make that witness clean (FR-525 owns prevention) — it is to assert that
*when* a gap exists at close time, the resulting `seam_packet` carries a matching
`open_threads` entry with a `reappear_from`, so the return is recoverable downstream.

## Proposed Solution

At the end of `close_chapter` (after `world_state` + `seam_packet` are derived), run
a **pure post-derivation check**: for each actor the chapter committed terminal whose
own later beats promised a return (the `beat_coverage_gap` condition), append an owed
thread to `seam_packet.open_threads`.

### Boundary of the change

- **Layer:** logic/planning (`chapter_ops.close_chapter` derivation + `seam_packet`
  shaping). No change to the director, turn loop, the 16-turn cap, or the committed
  `world_state` (the death stays committed — correct).
- **Trigger:** inside `close_chapter`, after the close graph returns, before the pure
  result is handed to the adapter to write.

### Owed-thread shape (J-candidate — reuse the seam_packet contract)

`seam_packet` already carries `open_threads` and a `reappear_from` convention
(`10023-BC`). The promotion appends, e.g.:

```yaml
open_threads:
  - actor: Arnulf
    owed: "reappears alive with a downstream group of refugees"
    reappear_from: <next playable chapter id>   # deterministic: cid + 1
    reason: ledger_terminal_but_beat_promised_return
```

The `reappear_from` target is deterministic (the next chapter in `order`); choosing a
*semantically ideal* later chapter is out of scope (the synopsis already sequences the
return — FR-523's re-outline reads the owed thread and places the bridge beat).

### `chapter_ops` change (pure; the adapter writes)

`close_chapter` stays a pure read returning `{text, world_state, seam_packet}`; the
`seam_packet` it returns simply gains the owed-thread entry. The `doc_ops` adapter
writes the result unchanged (no adapter logic change — the thread rides the existing
`seam_packet` write).

## Acceptance Criteria

> **The deterministic gate is AC-1 (mocked-LLM unit).** Live regen (AC-5) is
> corroboration, not a gate (FR-522 instrument posture).

- [ ] **AC-1 (deterministic gate, mocked LLM).** With the close graph stubbed to
  return a chapter committing an actor terminal while that chapter's beats promised a
  return, `close_chapter`'s returned `seam_packet.open_threads` contains a matching
  owed entry with `actor`, `owed` (the return beat text), and a deterministic
  `reappear_from`. **Negative control (non-vacuous):** a removal-only chapter (no
  return beat) yields **no** owed thread — proving the promotion measures the dropped
  return, not any death.
- [ ] **AC-2 (purity).** `close_chapter` never mutates `doc` (deep-copy equality); the
  owed thread is part of the returned `seam_packet`, written only by the adapter. No
  change to the committed `world_state` (actor stays terminal in this chapter).
- [ ] **AC-3 (idempotence / no duplication).** Re-deriving an already-closed chapter,
  or a chapter that already carries the owed thread, does not duplicate it. A chapter
  whose return beat actually played (actor NOT terminal) emits no owed thread.
- [ ] **AC-4 (downstream honor).** FR-523's `reoutline_chapter_beats` reads the prior
  chapter's `seam_packet` (it already passes `prior_seam_packet`); a fixture shows the
  owed thread reaches the re-outline input so the later chapter *can* author the return
  bridge. (Authoring the bridge is FR-523's job; AC-4 only proves the thread is visible
  downstream, not dropped.)
- [ ] **AC-5 (live corroboration, not a gate).** In a regenerated book where an
  over-pack slips past FR-525, the closed chapter's `seam_packet` carries the owed
  return thread and a later chapter reappears the actor — no permanent disappearance.
- [ ] **AC-6 (no downstream change).** Director, `running_scene`, turn loop, FR-501
  cap, FR-521 roster-drop, and `_clamp_lifecycle_reappearance_to_plan` untouched; tests
  green; `lint-imports` clean.
- [ ] **AC-7 (regime).** Example tests REQ-exempt (FR-474 J3); no CAP/REQ minted;
  changelog fragment `type: fix, scope: examples`, **no** `req:`. Commit subject carries
  `FR-526`; a diary entry accompanies the GREEN commit (diary-gate).
- [ ] `architecture.md` updated: `close_chapter` promotes an unfulfilled return beat
  into `seam_packet.open_threads` as defense-in-depth behind FR-525.

## Alternatives Considered

- **Make this the primary fix (drop FR-525) — REJECTED.** Forwarding the return after
  the over-pack already happened is recovery, not prevention; the chapter still plays a
  truncated arc and force-closes mid-reversal. FR-525 prevents the over-pack at the
  source; FR-526 only catches the residue. Defense-in-depth, not a substitute.
- **Resurrect the actor in this chapter's `world_state` — REJECTED.** The death *did*
  play; rewriting the committed ledger is the FR-524 re-weave error (a plausible-wrong
  past). The owed thread forwards the *unmet intent*, leaving the played past honest.
- **Pick a semantically ideal `reappear_from` via LLM — DEFERRED.** Deterministic
  `cid + 1` suffices; the synopsis already sequences the return and FR-523 places the
  bridge. An LLM-chosen target adds non-determinism for no proven benefit.

## Related

- `examples/dungeon_master/api/chapter_ops.py` — `close_chapter` (the hook point)
- `examples/dungeon_master/api/seam_packet.py` — `open_threads` / `reappear_from` contract
- `examples/dungeon_master/api/witness_metrics.py` — `beat_coverage_gap` (the gap condition)
- `feature-requests/FR-525-dm-v2-outliner-split-gate.md` — the primary prevention fix
- `feature-requests/FR-523-dm-v2-state-aware-chapter-reoutline.md` — reads the owed thread to bridge
- `feature-requests/FR-524-dm-v2-synopsis-summary-reweave.md` — the rejected re-weave + investigation
- `feature-requests/FR-501-*` — the 16-turn cap that creates the dropped-return window

## Judgement (2026-06-18)

Examined against the live `seam_packet.py` schema + normalizer,
`chapter_ops._planned_reappearance_chapter` / `_clamp_lifecycle_reappearance_to_plan`,
`turn_ops` lifecycle validation, and `docs/architecture.md`. The FR is **returned to
Plan** — its mechanism is schema-invalid and its residual value over FR-525 is
unproven.

- **J1 — The proposed mechanism is schema-invalid and self-defeating.** The draft puts
  an owed-return as a DICT `{actor, owed, reappear_from, reason}` into
  `seam_packet.open_threads`. But `SeamPacket.open_threads` is typed `list[str]`, and
  `parse_seam_packet` (the load-bearing boundary normalizer) **drops every non-string
  list entry**. The dict would be silently discarded at the seam — the forward never
  arrives. The FR's own cited evidence is also misread: `10023-BC`'s `reappear_from=6`
  is NOT a field on `open_threads`; it is
  `CharacterLifecycle.allowed_reappearance_from_chapter=6` on a typed lifecycle row.

- **J2 — The correct forward channel already exists and is load-bearing.** "Removed
  now, may reappear from chapter N" is exactly `CharacterLifecycle`:
  `existence_state ∈ {alive, missing_presumed_dead, confirmed_dead}` +
  `allowed_reappearance_from_chapter: int | None`. `_planned_reappearance_chapter`
  scans title/summary/beats for the return signal;
  `_clamp_lifecycle_reappearance_to_plan` raises the allowed chapter to the planned
  one; `turn_ops` validates the lifecycle at chapter-open; `docs/architecture.md`
  documents the `missing_presumed_dead` + `allowed_reappearance_from_chapter: 5`
  forward verbatim. FR-526 reinvents a channel that exists — and reinvents it wrongly.

- **J3 — Residual value over FR-525 is unproven.** FR-525 (frozen, authorized) splits
  the reversal at the partitioner; the removal chapter closes the actor terminal and a
  LATER chapter's summary carries the return, which the J2 machinery already honors.
  FR-526's only legitimate niche is the case where an over-pack SLIPS PAST FR-525's
  bounded-retry gate AND `close_chapter`/`chapter_close.yaml` fails to emit a
  `missing_presumed_dead` + `allowed_reappearance_from_chapter` lifecycle row for the
  removed-but-intended-to-return actor (committing `confirmed_dead`/terminal
  `world_state` with no forward instead). Whether that failure actually occurs is
  **unknown** — never observed, only assumed.

- **J4 — `investigation_before_fix`: build the close-seam probe FIRST.** Before FR-526
  earns any scope, a pure probe over the real `10024-BC` close seam must answer: does
  its committed `character_lifecycle` already carry Arnulf as `missing_presumed_dead`
  with an `allowed_reappearance_from_chapter`? If YES → FR-526 is fully redundant;
  close it. If it carries him as `confirmed_dead` (or a terminal `world_state` status
  with NO lifecycle forward) where the synopsis intends a *presumed*-dead return → THAT
  mis-classification in the close graph's lifecycle derivation is the real defect, and
  the fix is to correct the derivation USING the existing typed `CharacterLifecycle`
  channel — never an `open_threads` dict.

**Verdict:** **Returned to Plan.** Re-open only after the J4 close-seam probe
establishes what `close_chapter` actually emits for a swept-away-but-returning actor,
and only with the typed `CharacterLifecycle` channel. If the probe shows the lifecycle
forward is already emitted, FR-526 is closed as redundant with FR-525 + the existing
machinery. The draft below is preserved as the original proposal; it is **not**
authorized for enforce.

---

## Probe Outcome (J4 close-seam investigation) — RE-SCOPED, not redundant

Pure read-only probe over the real `outputs/dungeon-master/10024-BC/story.json`
(the packed Floodmark book). Committed `seam_packet.character_lifecycle` per chapter:

| Chapter | title | Arnulf lifecycle record (committed) |
|--------|-------|-------------------------------------|
| 3 | "Arnulf Lost and Returned" | `existence_state=confirmed_dead`, `allowed_reappearance_from_chapter=3`, `source_chapter=3` |
| 4-6 | (carry) | `confirmed_dead`, `allowed_reappearance_from_chapter=3` |

**The premise of FR-526 is FALSE.** A lifecycle forward IS emitted — Arnulf carries
`allowed_reappearance_from_chapter=3`. FR-526 assumed *no* forward existed and tried
to manufacture one through `open_threads`; that channel is both schema-invalid (J1:
`open_threads` is `list[str]`) and unnecessary.

**The real defect is an INCOHERENT record, not a missing one.**
`existence_state=confirmed_dead` together with `allowed_reappearance_from_chapter=3`
is self-contradictory: a confirmed-dead actor cannot be allowed to reappear, and a
reappearance "from chapter 3" when the death is *also* committed in chapter 3 is
nonsensical under the turn budget.

**Mechanism, fully traced:**
1. Ch3 packs the loss AND the return into one chapter (the FR-525 root cause).
2. The close LLM derives `existence_state=confirmed_dead` from the loss.
3. `_planned_reappearance_chapter` scans ALL chapters *including the current one*,
   finds Arnulf + a return signal in Ch3's own card, and returns `3`.
4. `_clamp_lifecycle_reappearance_to_plan` writes `allowed_reappearance_from_chapter=3`
   but only clamps the *index* — it never reconciles `existence_state`.
5. No invariant rejects `confirmed_dead` + a non-null reappearance allowance, so the
   incoherent record is committed and carried forward (Ch4-6).

**FR-525 is the correct root-cause cure** (split the pack so loss and return live in
DIFFERENT chapters), but it does NOT by itself guarantee a coherent lifecycle record:
even split, the loss chapter's close LLM may still write `confirmed_dead` while a
*later* planned return sets `allowed_reappearance_from_chapter=<later>` — the same
`confirmed_dead` + reappearance contradiction, merely across chapters.

### Re-scoped FR-526 (defense-in-depth, schema-valid)

A close-seam **coherence invariant** on the typed `CharacterLifecycle` channel
(`the_one_law` — normalize where the record is committed):

> When a planned reappearance exists for a character (`allowed_reappearance_from_chapter`
> is not None), the committed `existence_state` MUST be `missing_presumed_dead`, never
> `confirmed_dead`. A character the plan intends to return is *presumed* dead, not
> *confirmed* dead.

Smallest sufficient change: in `_clamp_lifecycle_reappearance_to_plan`, when `planned`
is not None and `existence_state == confirmed_dead`, downgrade to `missing_presumed_dead`
(the function already holds the planned index; it just stops short of reconciling the
state). Optionally add a close-seam assertion that `confirmed_dead` implies
`allowed_reappearance_from_chapter is None` as a standing invariant.

**Status: returned to Plan with a concrete, schema-valid scope.** The original
`open_threads`-dict draft below remains rejected. Re-open as the coherence-invariant
fix above, condemned first by a witness over the 10024-BC record (RED), behind FR-525.
