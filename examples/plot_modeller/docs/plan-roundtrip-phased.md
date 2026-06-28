# Phased Implementation Plan — Round-Trip Walking Skeleton

**Date:** 2026-06-27
**Companion to:** [plan-roundtrip-skeleton.md](plan-roundtrip-skeleton.md) (the build spec) and
[plan-generative-roundtrip.md](plan-generative-roundtrip.md) (the architecture).
**Method:** walking skeleton — each phase produces a **runnable graph** and a **gradeable artifact**.
No phase ends on "it compiles"; every phase ends on a number or a readable output.

**Tracked as feature requests:** P0 → FR-610, P1 → FR-611, P2 → FR-612, P3 → FR-613,
P4 → FR-614, P5 → FR-615 (dependency chain; each FR is the authority gate for its phase).

**Closure-measurement decision (2026-06-28) — option (a), STRUCTURAL over authored briefs.**
The coherence gate (P3) measures the **authored briefs' affect arc** deterministically — it walks
the open/close ops the briefs carry, not the prose. Consequences that bind the chain:
- The metric is **authored-plan closure**, NOT "dangling opens in the book" — that label is wrong
  under (a) and is corrected throughout.
- **P1 must author per-chapter affect open/close ops onto each brief** (the dungeon_master
  `eff_affect` model), or the structural gate has nothing to walk.
- **P4 edits the AUTHORING rule** (reactive chapters may author recognition/naming/decision closes),
  NOT the shared prose classifier `affect_throughline.yaml`. No fork of the shared scorer.
- The **prose-vs-plan** dangling check (the rejected option b — does the generated prose actually
  deliver the authored close?) belongs to **P5**, on the comparison side.

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
| `graphs/roundtrip_skeleton.yaml` | `state:` (premise, genre, cast, briefs, drafts, book, coherence); linear edges + map fan-out stub. The `briefs` carry `scene_type` + `eff_affect` (authored affect ops, decision (a)). |
| Fixture | Reuse the Loom synopsis already used by `interiority_ab` (one genre, one seed). |
| Stub nodes | `derive_cast` and `outline_chapter_briefs` may return a 1-line constant; `assemble_book` concats. |

**Run:** `graph lint` passes; `graph run ... --full` reaches END.
**Gradeable DoD:** the graph executes top-to-bottom and prints a (stub) assembled book. Topology frozen.

---

## Phase 1 — Cast sheets + chapter briefs (the load-bearing object)

**Goal:** real characters and real briefs carrying `scene_type`. This is the phase that earns the plan.

| Build | Reuse | Detail |
|---|---|---|
| `derive_cast` (llm) | `interiority_ab` `derive_cast` + `interiority_sheets.yaml` | synopsis → 2–4 principals → interiority sheets `{name, goal, belief, affect_arc}`. Prompts already exist under `prompts/interiority/`. |
| `outline_chapter_briefs` (llm) | dungeon_master [`chapter_outline.yaml`](../../dungeon_master/prompts/chapter_outline.yaml) | Copy the prompt into `prompts/roundtrip/outline_briefs.yaml`; **add one schema field `scene_type: proactive\|reactive`** and **one rule**: classify each chapter proactive (goal→conflict→disaster, feeling spent in action) vs reactive (reaction→dilemma→decision, feeling resolved internally). Optional `mode`. |
| **Authored affect arc** (per brief) | dungeon_master `eff_affect` model (`docs/v5/genre-plots/*.yaml`) | **Decision (a) dependency:** the outline node must also author per-chapter affect open/close ops `eff_affect: [{op: open\|close, char, kind, (toward)}]` so the P3 structural gate has a plan to walk. Without this the gate measures nothing. |

Brief object emitted per chapter:
`{chapter_id, title, summary, cast, beats[3–6], entry_state, exit_state, scene_type, eff_affect, (mode)}`.

**Run:** full graph; inspect `--full` state for `briefs`.
**Gradeable DoD:** every brief has a non-empty `scene_type` ∈ {proactive, reactive} **and** a
non-empty `eff_affect` op list; cast sheets have all four interiority fields. Eyeball: do the
scene_type labels match the chapter summaries? `scene_type` *correctness* (not just presence) is a
**P4 precondition** — it is re-verified in the P3/P4 Raw Output Reads, since P4 gates its number-move
on `scene_type == reactive` (manual, N=1 genre here).

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
| `coherence_gate` (python tool) | `validators/affects.py` `check_affect_closure` (FR-571) | New leaf reading the **authored briefs' affect arc** (the per-chapter open/close ops P1 authored): run the deterministic pop-walk → report `{authored_dangling_rate, opens, closes, by_scene_type}`. This measures the **plan's** closure, not the prose. Start with this one validator; plan-exists / cast-consistency later. |

**Run:** full graph; the gate prints the coherence report to state.
**Gradeable DoD:** one run yields an `authored_dangling_rate` number split by `scene_type` —
unclosed authored opens / authored opens (denominator pre-registered per split). **This is the
baseline** the next phase must move. It is a *plan-closure* number, not a prose claim (prose-vs-plan
is P5). Record it in the plan's results section.

---

## Phase 4 — First thickening: scene_type-aware close-op (move the number)

**Goal:** the indicted lane. The close-op is proactive-only (action-resolution only) → reactive
chapters dangle by construction. Under decision (a) the bug lives in the **authoring** rule, so we
fix it there — never in the shared prose classifier.

| Build | Detail |
|---|---|
| Baseline (RED) | From Phase 3: record `authored_dangling_rate` on reactive vs proactive chapters. Expect reactive ≫ proactive — the authoring prompt only knows action-resolution closes. |
| Widen the AUTHORING rule | In the roundtrip-local brief/affect-authoring prompt (`prompts/roundtrip/outline_briefs.yaml` or a dedicated affect-authoring node) add a **reactive close branch**: for `scene_type == reactive`, author a close op when a feeling is resolved by recognition/naming/decision. **Do NOT touch the shared `affect_throughline.yaml`** (it baselines the prior affect arc). |
| Re-measure (GREEN = the PAIRED result) | The binding criterion is **both or neither**: reactive `authored_dangling_rate` drops vs Phase 3 (proactive false-closes not inflated) **AND** every new reactive close is witnessed *deliverable in the prose* at the K≥5 raw read. |
| Tautology guard (PRIMARY) | Under decision (a), P4 edits the very rule that authors the metric, so the rate falls **by fiat** — instruct the author to emit reactive closes and the number drops whether or not the prose delivers one. The rate proves **emission, not fidelity**. The prose cross-check is the headline signal, not a parenthetical. Until P5 mechanizes it across all chapters, the K≥5 manual cross-check is the **sole** guard and is HARD, not advisory. |

**Run:** full graph, before/after.
**Gradeable DoD (paired — both or neither):** reactive `authored_dangling_rate` falls measurably vs
the Phase 3 baseline **and** every new reactive close is witnessed deliverable in the prose (K≥5);
proactive rate stable. **A bare rate win is forbidden** — emission without witnessed fidelity is not a
pass. Both results recorded together. P5 mechanizes this cross-check across all chapters; until then
the manual K≥5 read is the sole, HARD guard. (The carried-over "cheapest first move" from
[plan-scene-typing.md](plan-scene-typing.md), now an authoring-rule fix inside the harness instead of
an isolated-layer classifier edit.)

---

## Phase 5 — Deferred: round-trip closure (off the critical path)

Only once Phases 0–4 hold. Not required for the skeleton to be useful.

- **Prose-vs-plan dangling check** (the option (b) P3 deliberately rejected): an affect classifier
  over the generated prose extracts opens/closes and diffs them against the **authored** arc — this
  is where "does the book actually deliver the authored close?" is legitimately measured.
- **L4b classifier** (`scene_type` recognised *back out* of generated prose) — **comparison** side
  only, to check the authored scene_type was preserved. Never on the generative path.
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
P4 scene_type-aware AUTHORING rule  → move the number (RED→GREEN)
P5 round-trip closure (deferred)      → reconstruction is the gold
```

Each arrow is a commit boundary (`chore(plot-modeller): ...`, explicit paths, watcher active).
Stop and read the gate after P3 before deciding whether P4 is still the right lane to thicken.

## Results log (fill as phases land)

| Phase | Date | Artifact / number | Notes |
|---|---|---|---|
| P0 | | lint green | |
| P1 | | briefs w/ scene_type + eff_affect | |
| P2 | | assembled book | |
| P3 | | authored_dangling_rate baseline | proactive __ / reactive __ |
| P4 | | authored_dangling_rate after | reactive ↓ to __ (+ precision check) |
