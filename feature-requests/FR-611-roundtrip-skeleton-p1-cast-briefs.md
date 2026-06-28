# Feature Request: Round-trip skeleton P1 — cast sheets + chapter briefs with authored scene_type

**Priority:** HIGH
**Type:** Feature
**Effort:** 1 day
**Requested:** 2026-06-28
**Status:** Judged — Authority GRANTED with corrections (2026-06-28)

## Summary

Replace the P0 stubs for `derive_cast` and `outline_chapter_briefs` with real nodes. The brief
is the load-bearing object: dungeon_master's `chapter_outline` already emits
`{title, summary, beats, cast, entry_state, exit_state}` — this FR adds exactly **one field,
`scene_type`** (authored, `proactive|reactive`), plus optional `mode`. Phase 1 of
[plan-roundtrip-phased.md](../examples/plot_modeller/docs/plan-roundtrip-phased.md).

## Value Statement

`scene_type` becomes an **authored** field on an artifact we write, not a recognition problem —
sidestepping the L4b classifier entirely and putting the affect-dose control axis on the
generative path from day one.

## Judgement (2026-06-28)

**Verdict: Authority GRANTED with corrections.** This is the phase that earns the plan and the
HIGH priority is correct. Authority gate for Phase 1.

**Claims verified.** `dungeon_master/prompts/chapter_outline.yaml` emits exactly
`{title, summary, beats, cast, entry_state, exit_state}` and carries **no** `scene_type` — so
"add exactly one field" is accurate, not a rewrite. The interiority prompts exist under
`prompts/interiority/`. Authoring `scene_type` (vs classifying it back out of prose) genuinely
sidesteps the L4b classifier blocker and puts the affect-dose axis on the generative path for free.

**Correction 1 (PRIMARY).** `scene_type` **authoring quality** is load-bearing for P4 — P4's
number-move is gated on `scene_type == reactive`. If the model mislabels proactive/reactive at
authoring time, P4 measures noise on the wrong chapters. Yet P1 only eyeballs the labels at N=1,
and the independent preservation check (the L4b classifier) is **deferred to P5, after the phase
that depends on it**. Couple this explicitly: the P3 and P4 Raw Output Reads must confirm the
authored `scene_type` is **correct on every reactive sample inspected**, not merely present.
Label correctness is a P4 precondition, not a P5 afterthought.

**Correction 2 (secondary).** The AC names cast fields `{name, goal, belief, affect_arc}`, but the
reused prompt is `interiority_sheets.yaml` (the FR's "author_interiority" does not exist verbatim).
Confirm the four-field sheet shape matches what `interiority_sheets.yaml` actually emits before
wiring; cite the real prompt name.

**Frozen scope.** Real cast (4 interiority fields) + every brief carrying non-empty
`scene_type ∈ {proactive, reactive}`, authored by the outline node, never classified from prose.

## Decision fold (2026-06-28) — closure is STRUCTURAL over authored briefs (option a)

The chain adopts **option (a)**: the P3 gate measures the **authored briefs' affect arc**
deterministically, not the prose. This adds a load-bearing requirement to P1:

- The `outline_chapter_briefs` node must **also author per-chapter affect open/close ops** onto each
  brief — `eff_affect: [{op: open|close, char, kind, (toward)}]` (the dungeon_master
  `docs/v5/genre-plots/*.yaml` `eff_affect` model). Without this the P3 structural gate has no plan
  to walk and measures nothing.
- Resolving **Judge Correction 2**: the reused interiority prompt is `interiority_sheets.yaml`
  (there is no `author_interiority` prompt verbatim); cite the real name when wiring.
- Resolving **Judge Correction 1**: `scene_type` *correctness* (not mere presence) is a **P4
  precondition** — re-verified in the P3/P4 Raw Output Reads, since P4 gates its number-move on
  `scene_type == reactive`. The independent L4b preservation check stays deferred to P5, but label
  correctness is checked by hand on every reactive sample inspected at P3/P4.

## Problem

The interiority A/B falsification showed authored sheets are only *conditionally* valuable — the
value depends on SCENE TYPE (Swain proactive/reactive). For that axis to control generation it
must be *declared* on the brief, not classified back out of finished prose. Recognising
scene_type (an L4b classifier) is a blocker; authoring it is free.

## Proposed Solution

- `derive_cast` (llm): reuse `interiority_ab` `derive_cast` + `interiority_sheets.yaml` → 2–4
  principals with `{name, goal, belief, affect_arc}`. Prompts already under `prompts/interiority/`.
- `outline_chapter_briefs` (llm): copy dungeon_master
  [`chapter_outline.yaml`](../examples/dungeon_master/prompts/chapter_outline.yaml) to
  `prompts/roundtrip/outline_briefs.yaml`; add schema field `scene_type: proactive|reactive`
  and one classification rule (proactive = goal→conflict→disaster, feeling spent in action;
  reactive = reaction→dilemma→decision, feeling resolved internally). Optional `mode`. Also author
  per-chapter `eff_affect: [{op: open|close, char, kind, (toward)}]` (decision (a): the structural
  gate walks these).

Brief object per chapter:
`{chapter_id, title, summary, cast, beats[3–6], entry_state, exit_state, scene_type, eff_affect, (mode)}`.

## Acceptance Criteria

- [ ] Every emitted brief carries non-empty `scene_type ∈ {proactive, reactive}`.
- [ ] Every emitted brief carries a non-empty authored `eff_affect` open/close op list (decision (a)).
- [ ] Cast sheets carry all four interiority fields (name, goal, belief, affect_arc).
- [ ] `scene_type` is authored by the outline node, never classified from prose.
- [ ] Manual check (N=1 genre): scene_type labels match the chapter summaries (correctness, not just presence).
- [ ] Graph still lints and runs end-to-end.

## Alternatives Considered

Classify scene_type from generated prose (L4b on the critical path) — rejected: recognition
problem, and the brief is authored anyway so the label is free.

## Related

- [plan-roundtrip-phased.md](../examples/plot_modeller/docs/plan-roundtrip-phased.md) (P1)
- [plan-scene-typing.md](../examples/plot_modeller/docs/plan-scene-typing.md) (scene_type spec)
- Predecessor: FR-610 (P0). Successor: FR-612 (P2 draft + assemble)
