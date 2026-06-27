# Phased Implementation Plan — Round-Trip Walking Skeleton

**Date:** 2026-06-27
**Companion to:** [plan-roundtrip-skeleton.md](plan-roundtrip-skeleton.md) (the build spec) and
[plan-generative-roundtrip.md](plan-generative-roundtrip.md) (the architecture).
**Method:** walking skeleton — each phase produces a **runnable graph** and a **gradeable artifact**.
No phase ends on "it compiles"; every phase ends on a number or a readable output.

**Invariants across all phases**
- One graph file: `examples/plot_modeller/graphs/roundtrip_skeleton.yaml`. All flow lives here.
- Run shape (never a Python runner): `set -a; source .env; set +a; PROVIDER=anthropic ANTHROPIC_MODEL=claude-haiku-4-5 .venv/bin/yamlgraph graph run examples/plot_modeller/graphs/roundtrip_skeleton.yaml --var ... --full`
- Writers = haiku; only judge/gate-LLM nodes get `model: claude-sonnet-4-6`.
- Python only in leaf tools under `examples/plot_modeller/nodes/` and `validators/`.
- `scene_type` is **authored** into the brief, never classified on the generative path.
- Smoke test each phase: `.venv/bin/yamlgraph graph lint examples/plot_modeller/graphs/roundtrip_skeleton.yaml`.

---

## Phase 0 — Scaffold + fixture (the dry loop)

**Goal:** a lintable graph that runs premise → assembled stub end-to-end with placeholder nodes, so
the wiring is proven before any node is smart.

| Build | Detail |
|---|---|
| `graphs/roundtrip_skeleton.yaml` | `state:` (premise, genre, cast, briefs, drafts, book, coherence); linear edges + map fan-out stub. |
| Fixture | Reuse the Loom synopsis already used by `interiority_ab` (one genre, one seed). |
| Stub nodes | `derive_cast` and `outline_chapter_briefs` may return a 1-line constant; `assemble_book` concats. |

**Run:** `graph lint` passes; `graph run ... --full` reaches END.
**Gradeable DoD:** the graph executes top-to-bottom and prints a (stub) assembled book. Topology frozen.

---

## Phase 1 — Cast sheets + chapter briefs (the load-bearing object)

**Goal:** real characters and real briefs carrying `scene_type`. This is the phase that earns the plan.

| Build | Reuse | Detail |
|---|---|---|
| `derive_cast` (llm) | `interiority_ab` `derive_cast` + `author_interiority` | synopsis → 2–4 principals → interiority sheets `{name, goal, belief, affect_arc}`. Prompts already exist under `prompts/interiority/`. |
| `outline_chapter_briefs` (llm) | dungeon_master [`chapter_outline.yaml`](../../dungeon_master/prompts/chapter_outline.yaml) | Copy the prompt into `prompts/roundtrip/outline_briefs.yaml`; **add one schema field `scene_type: proactive\|reactive`** and **one rule**: classify each chapter proactive (goal→conflict→disaster, feeling spent in action) vs reactive (reaction→dilemma→decision, feeling resolved internally). Optional `mode`. |

Brief object emitted per chapter:
`{chapter_id, title, summary, cast, beats[3–6], entry_state, exit_state, scene_type, (mode)}`.

**Run:** full graph; inspect `--full` state for `briefs`.
**Gradeable DoD:** every brief has a non-empty `scene_type` ∈ {proactive, reactive}; cast sheets have all
four interiority fields. Eyeball: do the scene_type labels match the chapter summaries? (manual, N=1 genre).

---

## Phase 2 — Draft + deterministic assemble (the first whole story)

**Goal:** one prose draft per chapter, dosed by `scene_type`, concatenated with **no whole-book LLM**.

| Build | Reuse | Detail |
|---|---|---|
| `draft_chapter` (map over `briefs`) | novel_generator [`generate_beat.yaml`](../../demos/novel_generator/prompts/prose/generate_beat.yaml) map node | New prompt `prompts/roundtrip/draft_chapter.yaml`: inputs = brief + the cast sheets for `brief.cast` + a **scene_type affect-dose clause** (proactive → interior sparingly, feeling spent in action; reactive → interior foregrounded, reaction→dilemma→decision). `collect: chapter_drafts`. |
| `assemble_book` (python tool) | dungeon_master Book compose (FR-492, no whole-book LLM) | New leaf in `nodes/tools.py`: ordered concat of `chapter_drafts` by `chapter_id` → `book`. Deterministic. |

**Run:** full graph end-to-end on the Loom synopsis.
**Gradeable DoD:** `book` is a readable multi-chapter draft; reactive chapters visibly carry more
interior than proactive ones (eyeball the dose contrast — this is the whole point of authoring scene_type).

---

## Phase 3 — Coherence gate (the first metric)

**Goal:** the skeleton stops being a demo. It emits **one number** so later thickenings have a target.

| Build | Reuse | Detail |
|---|---|---|
| `coherence_gate` (python tool) | `validators/affects.py` close/open logic | New leaf reading `book` + `briefs`: run the scene_type-aware **affect-closure** check → report `{dangling_open_rate, opens, closes, by_scene_type}`. Start with this one validator; add plan-exists / cast-consistency later. |

**Run:** full graph; the gate prints the coherence report to state.
**Gradeable DoD:** one run yields a `dangling_open_rate` number split by `scene_type`. **This is the
baseline** the next phase must move. Record it in the plan's results section.

---

## Phase 4 — First thickening: scene_type-aware close-op (move the number)

**Goal:** the indicted lane. L7's close-op is proactive-only (action-resolution only) → reactive
chapters dangle. Now we have the loop to fix it *in context*.

| Build | Detail |
|---|---|
| Baseline (RED) | From Phase 3: record `dangling_open_rate` on reactive vs proactive chapters. Expect reactive ≫ proactive. |
| Widen the close-op | In `prompts/affect_throughline.yaml` (or the draft/gate path) add a **reactive close branch**: a feeling resolved by recognition/naming/decision in dialogue/thought **closes** an open, gated on the chapter's authored `scene_type`. |
| Re-measure (GREEN) | Re-run; the reactive dangling-open rate must drop without inflating proactive false-closes. |

**Run:** full graph, before/after.
**Gradeable DoD:** reactive `dangling_open_rate` falls measurably vs the Phase 3 baseline; proactive
rate stable. Numbers recorded. (This is the carried-over "cheapest first move" from
[plan-scene-typing.md](plan-scene-typing.md), now with a harness instead of an isolated layer.)

---

## Phase 5 — Deferred: round-trip closure (off the critical path)

Only once Phases 0–4 hold. Not required for the skeleton to be useful.

- **L4b classifier** (`scene_type` recognised *back out* of generated prose) — built on the
  **comparison** side only, to check the authored scene_type was preserved. Never on the generative path.
- **Synopsis′ reconstruction** — re-derive a synopsis from the typed structure and diff against the
  input (the architecture doc's "reconstruction is the gold").
- Additional gate validators: plan-exists, cast-consistency, entry/exit-state hand-off continuity.

---

## Build order summary

```
P0 wiring (lint green, stub loop)
P1 cast sheets + briefs+scene_type   → first real artifact
P2 map-draft + deterministic assemble → first whole story
P3 coherence gate                     → first number (baseline)
P4 scene_type-aware close-op          → move the number (RED→GREEN)
P5 round-trip closure (deferred)      → reconstruction is the gold
```

Each arrow is a commit boundary (`chore(plot-modeller): ...`, explicit paths, watcher active).
Stop and read the gate after P3 before deciding whether P4 is still the right lane to thicken.

## Results log (fill as phases land)

| Phase | Date | Artifact / number | Notes |
|---|---|---|---|
| P0 | | lint green | |
| P1 | | briefs w/ scene_type | |
| P2 | | assembled book | |
| P3 | | dangling_open_rate baseline | proactive __ / reactive __ |
| P4 | | dangling_open_rate after | reactive ↓ to __ |
