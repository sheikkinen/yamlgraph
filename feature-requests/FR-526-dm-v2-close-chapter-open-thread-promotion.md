# Feature Request: FR-526 — DM v2: Close-Seam Lifecycle Coherence Invariant (a Planned Return Implies Presumed, Not Confirmed, Death)

**Priority:** MEDIUM
**Type:** Bug (continuity defect, defense-in-depth)
**Status:** **ENFORCED (2026-06-18), behind FR-525.** Re-scoped after the J4
close-seam probe: the original `open_threads`-dict mechanism is **rejected** (schema-
invalid — `open_threads` is `list[str]`), but the probe found a real defect the
original FR missed — `10024-BC` Ch3 committed a self-contradictory `CharacterLifecycle`
row (`existence_state=confirmed_dead` AND `allowed_reappearance_from_chapter=3`). The
enforced fix is a pure, packet-only close-seam coherence invariant on the typed
channel: a non-null reappearance allowance softens `confirmed_dead` to
`missing_presumed_dead`, preserving the authored return intent. See the re-scoped
Judgement and Implementation Status below. The original draft is preserved below the
line as rejected history.
**Effort:** ~0.5 day
**Requested:** 2026-06-18

## Summary (re-scoped)

A close seam can commit a `CharacterLifecycle` row that is *confirmed* dead yet
*allowed* to reappear — the two are contradictory. The close LLM derives the death
from the loss; `_clamp_lifecycle_reappearance_to_plan` sets the reappearance index
from the plan but reconciles only the index, never the state, and nothing else rejects
the pairing. The fix is a pure, packet-only invariant
(`_enforce_reappearance_state_coherence`) normalized at the close seam where the record
is committed (`the_one_law`): when a row carries a non-null
`allowed_reappearance_from_chapter`, soften `confirmed_dead` to `missing_presumed_dead`
(preserving the allowance — the authored return intent). Genuine deaths with no
reappearance allowance are untouched. This is defense-in-depth behind FR-525: FR-525
prevents the same-chapter pack at the partitioner; FR-526 guarantees the loss-chapter
seam commits a *coherent* lifecycle row even in the post-split cross-chapter case.

<details>
<summary>Original proposal (REJECTED — open_threads dict, schema-invalid). Preserved as history.</summary>

## Summary (original, rejected)

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

</details>

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

---

## Judgement — Re-scoped (2026-06-18)

Examined the re-scoped proposal (close-seam lifecycle coherence invariant) against
the live `_clamp_lifecycle_reappearance_to_plan` (`chapter_ops.py:475`, called at
`:716`), the `CharacterLifecycle` schema (`seam_packet.py:52` — the
`Literal["alive","missing_presumed_dead","confirmed_dead"]` enum already admits the
target value), the `confirmed_dead` prose-violation filter (`chapter_ops.py:726`),
and the cross-source equality gate `_enforce_memory_precedence_gate` (`turn_ops.py`).

**The re-scope is sound.** The probe converted the original J3/J4 *assumption* into
*evidence*: a real committed record (`10024-BC` Ch3) carries
`existence_state=confirmed_dead` AND `allowed_reappearance_from_chapter=3` — a
self-contradiction. Residual value over FR-525 is therefore **proven**, not assumed:
FR-525 splits the pack but does not reconcile `existence_state` when a loss-chapter
close writes `confirmed_dead` while a planned return sets a non-null reappearance.

- **J1 — Premise approved; supersedes original J3/J4.** A genuinely incoherent
  lifecycle record exists in a committed artifact. The defect is incoherence, not the
  original FR's imagined *absence* of a forward. The `open_threads`-dict mechanism
  stays dead (schema-invalid, list[str]).

- **J2 — Invariant is semantically sound AND schema-valid.** "A character allowed to
  reappear is not *confirmed* dead, only *presumed* dead" is correct, and
  `missing_presumed_dead` is already a legal enum value — the downgrade stays inside
  the typed channel. No schema change.

- **J3 — Enforce as a PURE, packet-only function; do NOT fold it into the clamp.**
  The coherence rule depends on the packet alone (`allowed is not None` =>
  `existence_state != confirmed_dead`); it does NOT need `doc`. The clamp
  (`_clamp_lifecycle_reappearance_to_plan`) needs `doc` to find the planned index —
  a different concern. Add a separate pure
  `_enforce_reappearance_state_coherence(packet) -> packet` applied at the close seam
  immediately AFTER the clamp (`chapter_ops.py:716`). Single responsibility,
  trivially testable without a doc, normalized where the record enters
  (`the_one_law`).

- **J4 — Direction-of-fix is correct here and coherent with downstream consumers, but
  inherits upstream precision.** Downgrading (keep the reappearance, soften the death)
  is right because the synopsis intends Arnulf's return; clearing the reappearance
  instead would erase authored intent. Beneficial side effect confirming the
  direction: a `missing_presumed_dead` actor drops out of the `confirmed_dead`
  prose-violation filter (`chapter_ops.py:726`), so prose that references the
  returning character is correctly no longer a violation. **BUT** the invariant fires
  on `allowed_reappearance_from_chapter is not None`, and that field can be set by
  `_planned_reappearance_chapter` — a loose name + `_RETURN_SIGNAL` co-occurrence scan,
  the same imprecision class FR-525's witness had to cure with subject-proximity. A
  spurious reappearance allowance would therefore spuriously soften a real death.
  **REQUIRED:** a non-vacuous negative control — a genuinely `confirmed_dead`
  character with `allowed_reappearance_from_chapter = None` stays `confirmed_dead`
  (the downgrade fires ONLY on a non-null allowance). **DEFERRED (not in scope):**
  hardening `_planned_reappearance_chapter` precision — open a follow-up only if
  corroboration shows a spurious downgrade.

- **J5 — `existence_state` coherence ONLY; the same-chapter index incoherence is
  FR-525's.** The probed record is doubly broken: incoherent state (this FR) AND
  `allowed=3, source=3` (reappear in the chapter you vanished — nonsensical under the
  turn budget). The latter is a *packing* artifact that FR-525 prevents at the
  partitioner; do NOT re-litigate the index here. Scope this FR to the state invariant,
  which leaves a coherent record in the post-FR-525 cross-chapter case (loss in K,
  return in M>K). Index reconciliation is explicitly out of scope.

- **J6 — Integration risk: `existence_state` participates in a cross-source equality
  gate.** `_enforce_memory_precedence_gate` (`turn_ops.py`) RAISES
  `ContinuityMemoryConflictError` on seam-vs-synopsis-vs-memory state mismatch. The
  downgrade changes the seam state and could newly trip or newly silence that gate.
  **REQUIRED:** full DM suite green PLUS a targeted assertion that downgrading a
  swept-away-but-returning actor does not introduce a spurious memory-precedence
  conflict (the synopsis-derived state for a presumed-dead returner should align with
  `missing_presumed_dead`, reducing conflicts — verify, don't assume).

- **J7 — Build order (RED first, condemn a REAL record).** RED: a witness/fixture
  mirroring the `10024-BC` Ch3 record (`confirmed_dead` + `allowed_reappearance=3`)
  asserts the incoherence, plus the J4 negative control (allowed=None stays
  confirmed_dead). GREEN: the pure `_enforce_reappearance_state_coherence` reconciles
  it. Corroborate (FR-522 instrument posture, NOT a gate): regenerate a post-FR-525
  book and scan that no committed `character_lifecycle` row carries `confirmed_dead`
  together with a non-null `allowed_reappearance_from_chapter`.

- **J8 — Regime + retitle.** Example tests REQ-exempt (FR-474 J3); no CAP/REQ minted;
  changelog fragment `type: fix, scope: examples`, no `req:`; commit subject carries
  `FR-526`; diary entry accompanies GREEN (diary-gate); `lint-imports` clean (the
  coherence fn is pure layer-3). **RETITLE REQUIRED:** "Close-Chapter Open-Thread
  Promotion" names the dead mechanism. Rewrite the FR head (title, Type, Status,
  Summary, Proposed Solution) to the active scope — *Close-Seam Lifecycle Coherence
  Invariant* — so the document no longer describes the rejected `open_threads` dict as
  its solution. The original draft stays preserved below the line as rejected history.

**Verdict: APPROVED with the corrections above (J3 pure packet-only function; J4
required negative control; J5 state-only scope; J6 required integration assertion; J8
retitle). Scope frozen — authorized for enforce, BEHIND FR-525.** Enforce against this
frozen scope; deviations return here. The `open_threads`-dict draft remains rejected.

---

## Implementation Status — ENFORCED (2026-06-18)

Built against the frozen re-scoped Judgement; no deviations.

- **RED (`21f473b8`)** — `tests/test_lifecycle_coherence.py` (5 tests) condemns the
  real `10024-BC` Ch3 shape (`confirmed_dead` + `allowed_reappearance_from_chapter=3`)
  against the not-yet-existing pure invariant, with the J4 non-vacuous negative control
  (a genuine `confirmed_dead` + `None` allowance stays confirmed), living/already-presumed
  rows untouched, empty/missing lifecycle no-op, and input purity. RED: 5 failed
  (AttributeError).

- **GREEN (this commit)** —
  - **J3 pure packet-only function**: `_enforce_reappearance_state_coherence(packet)`
    in `chapter_ops.py` — depends on the row alone (no `doc`); when a row carries a
    non-null `allowed_reappearance_from_chapter` and `existence_state == confirmed_dead`,
    softens to `missing_presumed_dead`, preserving the allowance (J4 direction). Returns
    a new packet (purity); rows without an allowance untouched (J4 negative control).
  - **Wiring**: applied at the close seam in `close_chapter` immediately AFTER
    `_clamp_lifecycle_reappearance_to_plan` (single responsibility — clamp owns the
    index, coherence owns the state). `existence_state`-only; the same-chapter index
    incoherence stays FR-525's (J5).
  - **J6 integration** (`tests/test_chapters.py`, +1): an end-to-end `close_chapter`
    test mocks a `confirmed_dead` + planned-return seam and asserts the committed row
    is reconciled to `missing_presumed_dead` (allowance preserved), THEN feeds the
    reconciled seam to `_enforce_memory_precedence_gate(doc, "3", 1)` and asserts no
    spurious `ContinuityMemoryConflictError` — non-vacuous because a synopsis state of
    `missing_presumed_dead` would mismatch (and raise on) a `confirmed_dead` seam; the
    fix makes them align.
  - Full DM suite **244 passed** (+5: 5 unit + the e2e replaces nothing); `lint-imports`
    KEPT (the invariant is pure layer-3); ruff clean.

- **J8 regime + retitle** — FR head retitled to *Close-Seam Lifecycle Coherence
  Invariant*; the rejected `open_threads`-dict draft preserved under a collapsed
  `<details>`. Example tests REQ-exempt (FR-474 J3); no CAP/REQ minted; changelog
  fragment `type: fix, scope: examples`, no `req:`; commit subject carries `FR-526`;
  diary entry accompanies GREEN (diary-gate).

- **Corroboration (FR-522 instrument posture, NOT a gate)** — after a post-FR-525
  regen, scan that no committed `character_lifecycle` row pairs `confirmed_dead` with a
  non-null `allowed_reappearance_from_chapter`. Pending a fresh book generation.

**Status: ENFORCED behind FR-525.** Prevention (FR-525 split at the partitioner) +
record coherence (this invariant at the close seam) together guarantee a loss-chapter
commits a coherent lifecycle row even in the post-split cross-chapter case.
