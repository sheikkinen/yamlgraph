# Feature Request: Round-trip skeleton P1 — cast sheets + chapter briefs with authored scene_type

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-06-28

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

## Problem

The interiority A/B falsification showed authored sheets are only *conditionally* valuable — the
value depends on SCENE TYPE (Swain proactive/reactive). For that axis to control generation it
must be *declared* on the brief, not classified back out of finished prose. Recognising
scene_type (an L4b classifier) is a blocker; authoring it is free.

## Proposed Solution

- `derive_cast` (llm): reuse `interiority_ab` `derive_cast` + `author_interiority` → 2–4
  principals with `{name, goal, belief, affect_arc}`. Prompts already under `prompts/interiority/`.
- `outline_chapter_briefs` (llm): copy dungeon_master
  [`chapter_outline.yaml`](../examples/dungeon_master/prompts/chapter_outline.yaml) to
  `prompts/roundtrip/outline_briefs.yaml`; add schema field `scene_type: proactive|reactive`
  and one classification rule (proactive = goal→conflict→disaster, feeling spent in action;
  reactive = reaction→dilemma→decision, feeling resolved internally). Optional `mode`.

Brief object per chapter:
`{chapter_id, title, summary, cast, beats[3–6], entry_state, exit_state, scene_type, (mode)}`.

## Acceptance Criteria

- [ ] Every emitted brief carries non-empty `scene_type ∈ {proactive, reactive}`.
- [ ] Cast sheets carry all four interiority fields (name, goal, belief, affect_arc).
- [ ] `scene_type` is authored by the outline node, never classified from prose.
- [ ] Manual check (N=1 genre): scene_type labels match the chapter summaries.
- [ ] Graph still lints and runs end-to-end.

## Alternatives Considered

Classify scene_type from generated prose (L4b on the critical path) — rejected: recognition
problem, and the brief is authored anyway so the label is free.

## Related

- [plan-roundtrip-phased.md](../examples/plot_modeller/docs/plan-roundtrip-phased.md) (P1)
- [plan-scene-typing.md](../examples/plot_modeller/docs/plan-scene-typing.md) (scene_type spec)
- Predecessor: FR-610 (P0). Successor: FR-612 (P2 draft + assemble)
