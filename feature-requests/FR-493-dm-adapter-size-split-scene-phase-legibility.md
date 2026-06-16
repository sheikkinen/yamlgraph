# Feature Request: FR-493 — DM Adapter Size-Gate Split & Scene-Phase Legibility

**Priority:** MEDIUM
**Type:** Enhancement (refactor)
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-06-16
**Regime:** FR-474 J3 (DM prototype) — no CAP/REQ/CI-gates/changelog; diary required.

## Summary

Two structural refactors of the DM v2 example, both cohesion-only — **no new
capability, no behaviour change**:

1. **Size-gate split.** `examples/dungeon_master/api/session.py` is **507 lines**,
   over the 450-line ceiling in `CLAUDE.md` — the exact gate the sibling modules
   (`turn_ops`, `chapter_ops`) cite as their own reason to exist. Extract the
   side-effecting expansion cluster (`_expand_roster`, `_expand_chapters`,
   `_close_chapter`, `_compose_special`, `_autodraft`) into a new
   `expansion.py`, leaving `session.py` as the pure HTTP↔doc adapter
   (`weave`/`edit`/`accept`/`navigate` + `_view`/`StageView`).

2. **Scene-phase legibility.** The generation phase the README calls *"scene
   summary + characters via turns and final cut to text"* — the lifecycle
   `{plan, cast, world_state_in} → play turns (map→director→recap) → {final_text,
   world_state_out}` — already exists but is **scattered, unnamed**, across five
   `turn_ops` functions (`running_scene`, `invoke_turn`, `final_cut_context`,
   `invoke_final_cut`, plus the close caller in `chapter_ops`). Group and banner
   them as the explicit **Scene lifecycle** so the phase is legible. Cohesion
   reorganization only — **not** a generic `Scene` primitive (deferred below).

## Value Statement

`session.py` returns under the size gate it is the last DM module to violate, and
the chapter generation lifecycle becomes legible as one named phase — so the next
reader (human or agent) sees the seam the architecture intends instead of
reconstructing it from five call sites.

## Problem

### 1. The adapter violates its own gate

`session.py` is 507 lines. `CLAUDE.md`: *"Module size: Target < 400 lines, max
450 (split into submodules if exceeded)."* `turn_ops.py` and `chapter_ops.py`
both open with a docstring stating they exist *"so `session` stays under the size
gate"* — yet `session` has since drifted back over it. This is a regression
against the authors' own stated constraint (Commandment 8: split modules before
they bloat).

The cleanest seam is already visible in the file: a `── roster expansion
(side-effecting; navigation stays pure) ──` banner already fences off five
methods — `_expand_roster`, `_expand_chapters`, `_close_chapter`,
`_compose_special`, `_autodraft` (~95 lines). They are free functions wearing
method clothes: each takes `(doc, story_dir, …)` and orchestrates the ops
modules; none reads `self` beyond `self._characters`/`self._chapters`/`self._entry`
(pure doc helpers) and `self._invoke_stage`.

### 2. The Scene phase is real but unnamed

The lifecycle is coherent and load-bearing, but no single name or location holds
it. A reader tracing "how does a chapter become text?" must stitch together:

| Function | Module | Lifecycle role |
|----------|--------|----------------|
| `running_scene` | `turn_ops` | build the play context (plan + inherited world_state + history) |
| `invoke_turn` | `turn_ops` | play one turn (map → director → recap) |
| `final_cut_context` | `turn_ops` | assemble the finished arc (beats, climax) |
| `invoke_final_cut` | `turn_ops` | compose the chapter's final text |
| `close_chapter` | `chapter_ops` | derive `world_state_out` + final text |

These are the **two load-bearing generative seams** the live witness exists to
prove (chapter completion judged from the summary; `world_state` threaded
across chapters), but the code does not announce them as one phase.

## Proposed Solution

### Part 1 — `expansion.py` (mechanical extract)

Move the five expansion methods to module-level functions in a new
`examples/dungeon_master/api/expansion.py`, taking the doc helpers they need as
explicit arguments (or a small `SessionDoc` accessor), mirroring how `turn_ops`
and `chapter_ops` already take `(doc, …)`. `session.py` keeps thin delegating
calls (or calls the functions directly from `accept`/`navigate`/`weave`):

```python
# session.py (after)
from examples.dungeon_master.api import expansion
...
if stage.name == "synopsis":
    await expansion.expand_roster(doc, story_dir, self._characters(doc))
```

Target: `session.py` < 450 lines; `expansion.py` self-contained and unit-visible.
Import-direction unchanged (still Layer-3 adapter glue; no Layer-2 imports added).

### Part 2 — Scene lifecycle banner (cohesion reorg)

Group the five functions under one `── Scene lifecycle ──` banner in `turn_ops`
(the chapter-play owner), with a header docstring naming the phase and its
`{plan, cast, world_state_in} → turns → {final_text, world_state_out}` contract.
No signature changes, no moved logic — only ordering + a documenting banner so
the phase reads as one unit. (`close_chapter` stays in `chapter_ops` as the
adapter-facing entry but its docstring cross-references the Scene lifecycle.)

## Acceptance Criteria

- [ ] `session.py` is **≤ 450 lines** (`wc -l`), with the expansion cluster moved
      to `expansion.py`.
- [ ] `expansion.py` contains `expand_roster`, `expand_chapters`, `close_chapter`,
      `compose_special`, `autodraft` (or equivalently named), each a module-level
      function; `session.py` delegates to them.
- [ ] The five Scene-lifecycle functions in `turn_ops` are grouped under a named
      banner with a phase-contract docstring; no logic changed.
- [ ] **No behaviour change**: the DM test suite (`pytest
      examples/dungeon_master/tests/ --no-cov`) passes unchanged — same count,
      same assertions (tests may update import paths only).
- [ ] `ruff check` + `ruff format` clean; `lint-imports` clean (no new
      cross-layer import); `noqa_coverage --strict` clean.
- [ ] README/architecture updated only if a module name they cite changes
      (the module map in `docs/architecture.md` gains the `expansion.py` row).
- [ ] Diary reflection + Seed.

## Alternatives Considered

- **Split `StageView` + `_view` into `session_view.py` instead.** Also lands
  `session.py` under gate (~110 lines), but the view projection is more tightly
  coupled to `StageView`'s field set than the expansion cluster is to anything in
  `session`. The expansion split has the cleaner seam (it is already banner-fenced
  and `self`-light) and matches the existing `*_ops.py` precedent. Rejected as the
  primary, kept as fallback if the expansion extract proves to leave `session`
  still over gate.
- **A generic `Scene` primitive / `scene_ops.py` with a `Scene` dataclass.**
  Deferred — **`framework_costume` risk** (the codebase's own diary heuristic: a
  generic abstraction with one implementation is an FSM in a DAG costume). A
  chapter is today the *only* Scene instance; build the primitive only when a
  second scene type appears (multiple scenes per chapter, or a non-chapter
  interlude). This FR does cohesion (naming) now, not abstraction.
- **Do nothing.** Leaves the adapter in standing violation of the size gate the
  rest of the example is organized around — the kind of drift Commandment 8
  exists to catch.

## Related

- `examples/dungeon_master/api/session.py` (the 507-line module to split)
- `examples/dungeon_master/api/turn_ops.py` (Scene lifecycle host)
- `examples/dungeon_master/api/chapter_ops.py` (`close_chapter` entry)
- `examples/dungeon_master/docs/architecture.md` (module map to update)
- `CLAUDE.md` — module-size gate; `*_ops.py` extraction precedent
- FR-491 / FR-492 — established the chapter-play + deterministic-Book seams this
  refactor makes legible without changing.
