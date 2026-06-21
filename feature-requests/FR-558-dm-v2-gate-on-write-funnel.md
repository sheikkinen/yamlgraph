# Feature Request: DM v2 Gate-on-Write Funnel — bind the chapter-card gate battery to the artifact (Contract C)

**Priority:** MEDIUM (generalizes FR-555 from one boundary to every authoring boundary)
**Type:** Enhancement (refactor — closes a defect *class*, not an incident)
**Status:** Enforced (2026-06-21) -- FR-555 + FR-556 merged first; per-card battery `card_gate.gate_chapter_card` bound to the typed setter (the funnel) and routed through both outline paths; sequence `composition_gap` kept outline-level (J1 arity split). 413 DM tests pass.
**Effort:** ~0.5 day after FR-555 (extract the gate list; bind to the write funnel)
**Requested:** 2026-06-21

> Reference: [`docs/refactoring-plan.md`](../examples/dungeon_master/docs/refactoring-plan.md) §3 Contract C.
> **Sequencing:** FR-555 ships the *minimal* version (gate the reoutline call directly).
> This FR generalizes it so **any** code that writes a chapter card inherits the gates.

## Summary

The chapter-card gate battery (`gap_detectors.reversal_pack_gap`, `unplayable_beat_gap`,
`composition_gap`) is applied **only inside `outline_ops.outline_chapters`**. v2 has a
**second** chapter-authoring boundary — the FR-523 reoutline — and FR-555 patches that one
call site. This FR removes the per-call-site pattern entirely: the gate battery becomes a
named function bound to the **artifact** ("a chapter card is being written"), ideally the
typed setter from Contract A (FR-556), so a future third authoring path cannot reintroduce
the class.

## Value Statement

"Author a chapter card" becomes a single funnel with a single gate battery — the
`detection_without_enforcement` class is retired structurally, so no future authoring path
can silently bypass the gates the way the reoutline did (FR-555).

## Problem

A gate bound to a **call site** cannot guard an artifact written elsewhere. FR-555 proves
the cost: the exact defect `reversal_pack_gap` exists to prevent re-entered through the
ungated reoutline boundary (the 10036-BC Arnulf double/early reveal). Patching that one site
fixes the incident but not the class — a third authoring path (a future autodraft, a manual
edit endpoint, a v3 projection step) would need to remember to call the battery again. The
gate must bind to the act of writing a card, not to a particular writer.

## Proposed Solution

1. **Extract the battery** — a single `gate_chapter_card(card, *, prior_card=None,
   attempt_feedback) -> list[Gap]` (or a `gate_chapter_cards(cards)` for the
   compose/composition check) that runs the three detectors and returns the structured gaps.
   The bounded **detect → feedback retry → raise** discipline (`_OUTLINE_MAX_ATTEMPTS`,
   `_reversal_feedback` / `_unplayable_feedback` / `_composition_feedback`) is the caller's
   loop, shared by both authoring paths.
2. **Bind to the write funnel.** Both `outline_chapters` and `reoutline_chapter_beats`
   (post-FR-555) call the same battery. Once FR-556 lands, the battery is invoked by the
   typed chapter-card **setter** so the gate fires on *any* structural write, not by each
   author explicitly.
3. **No new detectors, no behavior change** to the *passing* path — only the binding point
   moves. A card that passed all three detectors before still commits unchanged.

```python
# gap_detectors.py (or a new gate module)
def gate_chapter_card(card, *, prior_card=None) -> list[Gap]:
    gaps = []
    gaps += reversal_pack_gap(card)["gaps"]
    gaps += unplayable_beat_gap(card)["gaps"]
    if prior_card is not None:
        gaps += composition_gap(prior_card, card)["gaps"]
    return gaps

# chapter_nav typed setter (post-FR-556) — the funnel
def write_chapter_card(doc, cid, card, *, prior_card=None):
    gaps = gate_chapter_card(card, prior_card=prior_card)
    if gaps:
        raise ChapterGateError(cid, gaps)   # caller's retry loop handles feedback
    ... # typed structural write
```

## Acceptance Criteria

- [ ] FR-555 merged first (the minimal reoutline gate); this FR refactors, not re-fixes.
- [ ] `gate_chapter_card` extracted; `outline_chapters` and `reoutline_chapter_beats` both
      call it (no duplicated detector wiring).
- [ ] RED test: a *new* synthetic authoring path that writes a packed card via the funnel
      raises `ChapterGateError` **without** that path calling any detector explicitly (proves
      the gate is bound to the write, not the writer).
- [ ] The passing path is byte-identical (characterization test on a clean outline).
- [ ] Once FR-556 lands, the battery is invoked from the typed setter; if FR-556 is not yet
      merged, bind to a shared `gate_chapter_card` helper called by both authors.
- [ ] DM suite green; `docs/refactoring-plan.md` Contract C marked done; `docs/architecture.md`
      §5b updated to describe the funnel rather than two call sites.

## Alternatives Considered

- **Stop at FR-555** — rejected; it fixes the incident but leaves the class open for the next
  authoring path. The whole point of Contract C is the class.
- **A lint/CI rule "every card write must call the battery"** — rejected; detection without
  enforcement at the boundary is the very anti-pattern this retires. Bind it in code.
- **Bind only after FR-556** — rejected as the sole option; provide the shared-helper fallback
  so this FR is not hard-blocked on the keystone.

## Related

- [`docs/refactoring-plan.md`](../examples/dungeon_master/docs/refactoring-plan.md) §3 Contract C, §4 sequencing
- FR-555 (the minimal gate-on-reoutline this generalizes)
- FR-556 (Contract A — the typed setter that becomes the funnel)
- FR-525/528/540 (the three detectors being bound)
- [`api/gap_detectors.py`](../examples/dungeon_master/api/gap_detectors.py), [`api/outline_ops.py`](../examples/dungeon_master/api/outline_ops.py)

## Judgement (2026-06-21)

**Verdict: APPROVE WITH CONDITIONS — do not enforce yet (sequence-blocked).** The thesis is correct
and is the right generalization of FR-555: a gate bound to a *call site* cannot guard an artifact
written elsewhere, and binding the battery to the write (ideally Contract A's setter) retires the
`detection_without_enforcement` class structurally. Verified: the three detectors exist and are
applied **only** inside `outline_ops` (`reversal_pack_gap` L105, `unplayable_beat_gap` L151,
`composition_gap` L271), so the second-boundary claim holds. But two conditions gate enforcement.

**Blocking sequence: FR-555 is still `Proposed` (no commit on any branch).** AC #1 of this FR —
"FR-555 merged first; this FR refactors, not re-fixes" — is **unmet**. This FR *generalizes* a fix that
does not yet exist; enforcing it now would mean building the funnel and the minimal reoutline gate in
one breath, collapsing the very RED-first incident proof FR-555 is supposed to carry (the 10036-BC
Ch3 Arnulf early-reveal). **Hold FR-558 until FR-555 is judged, enforced, and merged.** Judge/enforce
FR-555 next; return here after.

**J1 — BLOCKING (design). The `gate_chapter_card(card, prior_card=...)` sketch is wrong:
`composition_gap` is a *sequence* check, not a pairwise-card one.** Live signature is
`composition_gap(chapters: list[dict]) -> dict` — it walks **all adjacent (N, N+1) pairs** of the whole
outline, checking `exit_state`/`entry_state` antonym contradictions across a shared roster subject. It
cannot be expressed as `composition_gap(prior_card, card)` over two cards (the FR's own sketch), and
binding it to a *single-card* setter is a category error: a per-card write does not have the sequence
context composition needs, and re-running whole-outline composition on every single-card write is both
wrong (the card may be mid-edit) and wasteful. **Resolution: split the battery by arity.**
  - **Per-card gates** (`reversal_pack_gap`, `unplayable_beat_gap`) bind to the card write — these *are*
    single-card and fit the funnel.
  - **Sequence gate** (`composition_gap`) stays an **outline-level** gate run when the chapter *set*
    changes (partition, and any reoutline that can alter adjacency), NOT on every card write. Keep it
    where it is (a `gate_chapter_cards(chapters)` over the list), and do not pretend it funnels through
    the per-card setter. The FR half-acknowledges this ("or a `gate_chapter_cards(cards)`") — make it
    explicit and correct the sketch so enforce does not chase a signature that cannot exist.

**J2 — non-blocking. Keep the FR-556 dependency soft, as written.** The fallback ("if FR-556 is not
yet merged, bind to a shared `gate_chapter_card` helper called by both authors") is the right hedge
and keeps this FR from being double-blocked. Good. But note: without Contract A's setter, the
"bound to the write, not the writer" guarantee is only *convention* (both authors must remember the
helper) — the RED test (AC: a synthetic authoring path that writes a packed card via the funnel and
raises **without** calling a detector explicitly) is only truly satisfiable once the setter exists.
Until then the test proves "both *known* authors call the helper," which is weaker. State that honestly
in the AC so the funnel claim is not overstated before FR-556 lands.

**J3 — non-blocking. Preserve the caller's retry loop; only the detector wiring moves.** The bounded
`detect → _reversal_feedback retry → raise` discipline (`_OUTLINE_MAX_ATTEMPTS`) must stay the caller's
loop, shared verbatim by both authoring paths — the extracted `gate_chapter_card` returns gaps, it does
not own the retry. The FR says this; hold it during enforce so the passing path stays byte-identical.

**Decision: APPROVE the design, BLOCK enforcement on (1) FR-555 merge and (2) the J1 arity split
folded into the FR text.** Re-judge readiness after FR-555 ships. When unblocked: RED-first synthetic-
authoring-path test, per-card vs sequence split, soft FR-556 dependency, shared retry loop. Example-
exempt; changelog + diary required.

## Enforcement (2026-06-21)

Unblocked: FR-555 (reoutline reversal gate) and FR-556 (typed setter funnel) both merged locally first.

RED (`test(examples): FR-558 condemn bypassable card-write boundary`,
`examples/dungeon_master/tests/test_gate_on_write_funnel.py`): writing a packed-reversal OR
time-skip-epilogue card through the one typed setter must raise `ChapterGateError` (the test never calls
a detector to decide -- proving the gate rides the write); a clean card commits unchanged;
`gate_chapter_card` returns both detectors' gaps tagged by kind; `reoutline_chapter_beats` rejects an
unplayable final beat too. 4 failed, 1 passed (the clean path already byte-identical via the FR-556 setter).

GREEN:
- **New leaf module `card_gate.py`.** `gap_detectors.py` sits at the 449-line ceiling, and the GATE
  (which composes detectors and raises) is a distinct concern from the pure WITNESSES, so it lives in
  its own module: `ChapterGateError(ValueError)` (carries `cid` + tagged `gaps`) and
  `gate_chapter_card(card) -> list[dict]` (runs `reversal_pack_gap` + `unplayable_beat_gap`, tags each
  gap with `kind`). The sequence gate `composition_gap` is deliberately NOT here (J1 arity split).
- **Bound to the write (the funnel).** `chapter_nav.write_chapter_card` now calls `gate_chapter_card`
  after structural validation and raises `ChapterGateError` before committing. `card_gate` is imported
  LAZILY inside the setter: it composes `gap_detectors`, which imports `chapter_nav`, so a top-level
  import would close a cycle; the gate touches only the cold write path, the read getters stay leaf-pure.
- **Single per-card wiring (J3).** `outline_ops._packed_chapters` / `_unplayable_chapters` and
  `reoutline_chapter_beats` all route per-card detection through `gate_chapter_card` -- the detectors
  are no longer wired directly in `outline_ops` (the import was removed). The bounded
  `detect -> feedback -> retry -> raise` loop stays the CALLER's; the gate returns gaps, it does not own
  the retry. The passing path is byte-identical (same detectors, same order).
- **Generalization with a witness (Commandment 7).** Routing `reoutline_chapter_beats` through the shared
  battery means the FR-555 second authoring boundary now also rejects an unplayable time-skip-epilogue
  final beat, not only a packed reversal. That new production branch gets its own condemning RED test
  (`test_reoutline_rejects_unplayable_final_beat`).

Verification: `examples/dungeon_master/tests/` 413 passed (407 + 6 new funnel tests); ruff clean;
`outline_ops` 393 lines, `card_gate` 68, `chapter_nav` 109, all under the size gate. DM is not under
import-linter; the lazy `chapter_nav -> card_gate` edge keeps the static graph acyclic.
