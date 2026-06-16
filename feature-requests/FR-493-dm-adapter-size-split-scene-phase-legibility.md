# Feature Request: FR-493 — DM Adapter Size-Gate Split & Scene-Phase Legibility

**Priority:** MEDIUM
**Type:** Enhancement (refactor)
**Status:** Implemented (2026-06-16) — session.py 508 → 333 lines; doc_ops.py extracted; Scene lifecycle banner added; 76 tests pass.
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

- [x] `session.py` is **< 400 lines** (`wc -l`) — target, not just the 450 max
      (J1) — with the nine-function closed set moved to `doc_ops.py`.
- [x] `doc_ops.py` (J2) contains module-level `entry`, `characters`, `chapters`,
      `invoke_stage`, `expand_roster`, `expand_chapters`, `apply_chapter_close`
      (J3), `compose_stage` (J3), `autodraft` (J3); each a pure `(doc, …)`
      function, no `self`; `session.py` delegates to them.
- [x] No `doc_ops.close_chapter` (J3): the moved write-wrapper is
      `apply_chapter_close`, distinct from `chapter_ops.close_chapter`.
- [x] `test_session_module_under_size_gate` added (J4): RED at 507, GREEN after,
      committed RED (`SKIP=pytest`) then GREEN, separately.
- [x] `test_expand_chapters_is_idempotent` call site updated to
      `doc_ops.expand_chapters` (J4) — the only test touching a moved private.
- [x] The five Scene-lifecycle functions in `turn_ops` are grouped under a named
      banner with a phase-contract docstring (J5); **no function moves modules**.
- [x] **No behaviour change**: `pytest examples/dungeon_master/tests/ --no-cov`
      passes unchanged — same count, same assertions (only the two J4 edits).
- [ ] `ruff check` + `ruff format` clean; `lint-imports` clean (no new
      cross-layer import); `noqa_coverage --strict` clean.
- [ ] `docs/architecture.md` module map gains the `doc_ops.py` row.
- [ ] Diary reflection + Seed.

## Judgement (2026-06-16) — scope frozen

Verified against the code before granting authority. The plan is sound; one
ambiguity it flagged itself ("…or a small `SessionDoc` accessor") is resolved
here, and one latent collision is pinned. Five binding rulings:

### J1 — The shared helpers move *with* the cluster; the seam is acyclic

The plan's "(or a small `SessionDoc` accessor)" is unsound as written: the five
expansion methods call four sibling helpers — `_invoke_stage`, `_entry`,
`_characters`, `_chapters`. Reading each body confirms **all four are
`self`-free** (they use only `doc`, `stage`, `get_app`, `clean_text`, `tree`
constants, and each other). Two consequences:

- Passing `self` into module-level expansion functions would be **Feature Envy**
  (a function taking a session just to reach its private doc helpers) and would
  contradict the cited `*_ops.py` precedent, which uses pure `(doc, …)` args and
  no `self`. **Rejected.**
- Since the helpers are `self`-free, the *minimal change with no new wart* is to
  lift the **closed set of nine functions** to module level together:
  `entry`, `characters`, `chapters`, `invoke_stage` (the doc/graph core) +
  `expand_roster`, `expand_chapters`, `apply_chapter_close`, `compose_stage`,
  `autodraft` (the cluster). `session` imports them; they import nothing from
  `session` → **acyclic** (`session → doc_ops`, one direction).

This leaves `session.py` a genuinely thin adapter with **zero doc-shape logic**,
and overshoots the size *target* (< 400, est. ~345 lines) rather than merely the
450 max — satisfying the gate the FR cites, not just clearing it.

### J2 — Module name is `doc_ops.py`, not `expansion.py`

`expansion.py` is a misnomer once it holds `entry`/`invoke_stage`. Freeze the
name **`doc_ops.py`** — it mirrors the exact `*_ops.py` precedent the FR honors
(sibling to `turn_ops.py`, `chapter_ops.py`) and reads as a peer to `story_doc.py`
(raw file I/O) vs `doc_ops.py` (derived operations over the in-memory doc).

### J3 — Rename on move to kill the `close_chapter` collision

`chapter_ops.close_chapter` (the pure derive) already exists; `session._close_chapter`
(the adapter write-wrapper that calls it) must **not** move as `doc_ops.close_chapter`
— two `close_chapter`s in two modules is a reader trap (`false_duplicate`). Freeze
the moved name as **`doc_ops.apply_chapter_close`** (it records the derived close
onto the card + marks reviewed). `compose_special` → `compose_stage`, `_autodraft`
→ `autodraft` (drop the leading underscore; they are public module functions now).

### J4 — Part 1 gets a real RED→GREEN witness (the size gate as a test)

A pure relocation has no behaviour branch to condemn, so the regression guard is
the unchanged suite. But the *constraint* this FR enforces can itself be a failing
test first (Commandment 10 — codify the lesson so it cannot recur):

- Add `test_session_module_under_size_gate` asserting `session.py` line count
  ≤ 450. It is **RED now (507)** and goes **GREEN** after the extraction — the
  failing-test-first witness this refactor would otherwise lack, and a durable
  guard against re-drift. Commit RED (SKIP=pytest) and GREEN separately.
- Update the one direct-call site: `test_expand_chapters_is_idempotent` calls
  `sess._expand_chapters(doc, story_dir)` → `doc_ops.expand_chapters(doc, story_dir)`.
  This is the *only* test touching a moved private (grep-confirmed); it is a
  call-site change, allowed under "no behaviour change."

### J5 — Part 2 is cosmetic and sequenced after Part 1; the Scene primitive stays deferred

Part 2 (the Scene-lifecycle banner) moves **no function between modules** — only
ordering + a banner + a header docstring in `turn_ops`, with `close_chapter`
remaining in `chapter_ops` cross-referencing it. It lands **after** Part 1 so the
two diffs do not interleave. The generic `Scene` primitive remains **deferred**
(confirmed `framework_costume`: a chapter is the sole Scene instance today).

**Authority granted.** Scope is frozen to: one new module `doc_ops.py` (nine
relocated functions, two renamed per J3), a thinned `session.py` (< 450, target
< 400), the size-gate guard test (J4), the one updated call site (J4), and the
`turn_ops` Scene banner (J5). No new capability, no behaviour change. Anything
beyond this — a `Scene` dataclass, a `scene_ops.py`, a `StageView` split — is out
of scope and returns to Plan.

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
