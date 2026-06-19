# Feature Request: FR-536 DM v2 module organization and oversized-file refactor

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged 2026-06-19 — authority granted for **Workstreams A+B+C only**; scope
frozen (see Judgement). Workstream D (folder move) split to follow-up **FR-537**.
**Effort:** ~2-3 days (phased; each extraction is an independent commit)
**Requested:** 2026-06-19

## Summary

The DM v2 `api/` package has drifted into a flat directory of 18 modules that mix
five distinct concerns, with three files now far over the 450-line ceiling
(`turn_ops.py` 1169, `chapter_ops.py` 955, `witness_metrics.py` 772). The
module-size gate only watches `session.py` — the three actual offenders are
unguarded. This FR plans a concern-based folder layout, a TDD-driven split of the
three oversized modules along their internal seams, consolidation of duplicated
chapter-navigation primitives, and a generalized size gate so the drift cannot
recur silently.

## Value Statement

Contributors (and the Chaplain pipeline) get a DM codebase where each module owns
one concern and stays under the size ceiling, so the next continuity feature lands
without first paging through a 1169-line god-module.

## Problem

### Analysis evidence (2026-06-19)

**File size (api/, excluding the detached `purgatory/`):**

| Module | Lines | Over 450? |
|--------|-------|-----------|
| `turn_ops.py` | 1169 | +719 |
| `chapter_ops.py` | 955 | +505 |
| `witness_metrics.py` | 772 | +322 |
| `world_state.py` | 454 | +4 |
| everything else | <=381 | ok |

**radon MI:** `turn_ops.py` is the only file rated **B (11.38)** — every other
module is A. `witness_metrics.py` (29.28) and `chapter_ops.py` (24.12) are the
lowest A's. Low MI tracks exactly the three oversized files.

**radon CC (D-rated blocks, the worst):** `apply_ledger_delta` (D=28,
`world_state.py`), `_post_revise_invariant_failures` (D=28, `chapter_ops.py`),
`_update_live_synopsis` (D=23, `doc_ops.py`), `dead_character_names` (D=21,
`turn_ops.py`), `breadcrumb` (D=21, `tree.py`), `format_world_state` (D=21,
`world_state.py`). High complexity is spread, but concentrates in the big files.

**vulture (min-confidence 70):** clean — no dead code. (No deletion work needed.)

**jscpd:** duplication is low at **0.71%** (6 clones, 41 lines). The notable ones:
- `turn_ops.py [196-204]` vs `[209-217]` (110 tokens) — `inherited_world_state`
  and `inherited_seam_packet` are the same "find previous chapter card" walk.
- `tree.py [252]` vs `turn_ops.py [194]` — the same previous-card lookup again.
- `_previous_chapter_id` is defined **twice** (`turn_ops.py:220` and
  `witness_metrics.py:328`) with diverging signatures (`-> str` vs `-> str | None`).

### The size gate is incomplete

`tests/test_module_size.py` asserts only `session.py <= 450`. The three modules
that actually breach the ceiling have no guard, so they drifted freely. A gate
that watches the one compliant file while ignoring the three offenders is
compliance theatre (`gate_checks_shape_not_substance`).

### Concern tangling

`turn_ops.py` alone carries five concerns: (1) turn-graph invocation/direction,
(2) chapter-open continuity gates, (3) cast/lifecycle filtering, (4) final-cut
composition, (5) chapter-navigation primitives. `chapter_ops.py` carries two
unrelated jobs: prose-continuity detection/revision, and chapter outline/close
lifecycle. The flat `api/` folder gives no signal about which module owns what.

## Proposed Solution

Three independent workstreams, each TDD and independently shippable. **No behaviour
change** — these are pure moves/splits guarded by the existing 271-test DM suite
plus a generalized size gate. Order chosen so the cheapest, highest-leverage guard
lands first.

### Workstream A — Generalize the size gate (do first, cheap)

Replace the single-file assertion in `tests/test_module_size.py` with a parametrized
sweep over every `api/**/*.py` (excluding `purgatory/`), asserting `<= 450`. Land it
with the three known offenders **xfail-listed** so the gate is green immediately and
each subsequent extraction removes one xfail entry — the gate becomes the
RED->GREEN witness for Workstream C. This turns the refactor into a checklist the
CI enforces.

### Workstream B — Consolidate navigation primitives (small, removes the clones)

Lift the chapter-navigation walk into one home (the existing `tree.py` or a new
`chapter_nav.py`):

- one `previous_chapter_card(doc, cid) -> dict` (or id) that
  `inherited_world_state`, `inherited_seam_packet`, and `_previous_chapter_id` all
  call — kills the 110-token clone and the `tree.py`/`turn_ops.py` clone.
- delete the duplicate `_previous_chapter_id` in `witness_metrics.py`; import the
  one canonical definition (reconcile the `-> str` vs `-> str | None` contract — the
  `| None` form is the honest one).

### Workstream C — Split the three oversized modules along their seams

Split by the concern clusters the analysis already surfaced. Proposed targets
(names indicative; final names set during enforcement):

**`turn_ops.py` (1169) ->**
- `turn_ops.py` — turn-graph invocation + direction: `invoke_turn`, `turn_record`,
  `turn_direction`, `turn_intents`, `prior_intents`, `_direction_dict`,
  `_apply_beat_ledger`, `_satisfied_indices`, `_phase_for_count`, `_beats_block`,
  `running_scene`, `_retrieve_turn_ledger`.
- `chapter_open.py` — opening gates + onepager: `_enforce_memory_precedence_gate`,
  `_enforce_lifecycle_gate`, `_compile_opening_onepager`, `_format_opening_onepager`,
  `_opening_source_pointer`, `LifecycleGateError`, `ContinuityMemoryConflictError`.
- `scene_cast.py` — cast/lifecycle filtering: `build_allowed_scene_cast`,
  `_filter_roster_for_lifecycle`, `_drop_within_chapter_exits`,
  `_chapter_cast_exits`, `dead_character_names`, `_possession_facts`.
- `final_cut_ops.py` — composition: `final_cut_context`, `invoke_final_cut`,
  `beat_turn_groups`, `_format_beat_groups`, `_turn_performance_cards`,
  `_cast_order`.

**`chapter_ops.py` (955) ->**
- `chapter_lifecycle.py` — outline/close: `outline_chapters`,
  `reoutline_chapter_beats`, `close_chapter`, `_derive_chapter_memory`,
  `_clamp_lifecycle_reappearance_to_plan`, `_enforce_reappearance_state_coherence`,
  `_planned_reappearance_chapter`, the outline validators, `compose_book_deterministic`.
- `prose_continuity.py` — detection/revision: `detect_dead_character_prose_violations`,
  `detect_object_use_after_loss`, `_post_revise_invariant_failures`,
  `_revise_final_cut_once`, `_safe_lines_preserved_ratio`,
  `_collect_dead_character_prose_violations`, `_log_intra_chapter_continuity`,
  `FinalCutReviseError`.

**`witness_metrics.py` (772) ->**
- `witness_metrics.py` — log/progress/actor metrics: `parse_generation_log_metrics`,
  `parse_story_progress_metrics`, `chapter_actor_flag_metrics` + actor helpers.
- `gap_detectors.py` — seam/beat/reversal/unplayable gap detectors plus their NLP
  token helpers (`_subjects_near`, `_text_has_token`, the token tuples,
  `_PROPER_NAME_RE`).

### Workstream D — Folder layout (optional, do last; highest blast radius)

Group `api/` by concern into sub-packages, re-exporting from the package `__init__`
so external import paths (`examples.dungeon_master.api.X`) can be preserved or
migrated in one sweep:

```
api/
  web/        app.py, session.py, render.py, graph_app.py, routes/
  story/      story_doc.py, doc_ops.py, tree.py, navigation.py, chapter_nav.py
  continuity/ lifecycle_resolver.py, seam_packet.py, world_state.py,
              chapter_open.py, prose_continuity.py, scene_cast.py
  metrics/    witness_metrics.py, gap_detectors.py, cue_metrics.py, chapter_replay.py
  ops/        turn_ops.py, chapter_lifecycle.py, final_cut_ops.py
```

Workstream D is **gated on D being judged worth its import-churn** (split to FR-537
per J7). B and C deliver the size and cohesion wins; they do change the symbol-access
callsites within the DM package (e.g. `turn_ops.build_allowed_scene_cast` becomes
`scene_cast.build_allowed_scene_cast`), but they do NOT introduce facade re-exports
and they do NOT touch any module's import *prefix* repo-wide. D is listed so the
target shape is explicit, not so it is mandatory.

## Acceptance Criteria

- [ ] `tests/test_module_size.py` sweeps all `api/**/*.py` (excl. `purgatory/`) at
      `<= 450`; no xfail entries remain at the end.
- [ ] `turn_ops.py`, `chapter_ops.py`, `witness_metrics.py`, **and `world_state.py`**
      each `<= 450` lines (world_state is 454 today — trim under Workstream A, J2).
- [ ] `_previous_chapter_id` defined once; the two jscpd previous-card clones gone
      (re-run jscpd shows them removed).
- [ ] The FR-534 `lifecycle_resolver` <-> `turn_ops` lazy-import cycle is dissolved:
      the nav primitives live in a leaf module both can import directly (J4).
- [ ] No facade re-exports left in the emptied modules; symbol-access callsites are
      migrated to the new module (Commandment 8, no compat shims — J3).
- [ ] Full DM suite (271+ tests) green after every extraction commit — each split is
      behaviour-neutral (a move, not a rewrite).
- [ ] `ruff` and `lint-imports` clean; no new `# noqa`.
- [ ] vulture stays clean (no orphaned helpers left behind by the splits).
- [ ] Each extraction is its own commit (one concern per commit) for clean blame/revert.
- [ ] Cyclomatic-complexity reduction is explicitly OUT of scope (J6); no D-rated
      block is rewritten under this FR.

## Alternatives Considered

- **Leave the files oversized, raise the ceiling.** Rejected — the 450 ceiling is
  doctrine (`CLAUDE.md`), and `turn_ops.py`'s B-rated MI shows the size is already
  costing maintainability, not just tripping an arbitrary number.
- **Split purely by line count (mechanical halving).** Rejected — the radon CC/MI
  data and the def-cluster map show natural concern seams; splitting along them
  yields cohesive modules, while halving yields two arbitrary fragments that still
  cross-import everything.
- **Do the folder move (D) first.** Rejected — moving import paths before splitting
  maximizes churn and merge risk; B+C deliver the cohesion and size wins with zero
  import-path change, leaving D as a contained, optional follow-up.
- **Delete `purgatory/`.** Out of scope — README documents it as the intentionally
  detached prototype that components are still mined from; it is self-contained
  (no live code imports it) so it does not affect this refactor.

## Related

- `examples/dungeon_master/api/turn_ops.py`, `chapter_ops.py`, `witness_metrics.py`
  (the three oversized modules)
- `examples/dungeon_master/tests/test_module_size.py` (the gate to generalize)
- `examples/dungeon_master/api/lifecycle_resolver.py` (FR-534 — the precedent: a
  concern lifted out of `turn_ops.py` into its own module)
- `feature-requests/FR-493-*` (the earlier `session.py` -> `doc_ops.py` extraction
  that established the size-gate pattern)
- `CLAUDE.md` "Code Quality Standards" (the 450 ceiling); Scripture Commandment 8
  (kill entropy: split modules before they bloat)
- Diary heuristic `gate_checks_shape_not_substance` (the size gate watching only the
  compliant file)

## Judgement (2026-06-19)

Examined against the code, not the plan's self-description. Premise holds; three
contradictions resolved; scope frozen to A+B+C.

**J1 — Root problem confirmed.** Sizes verified (`turn_ops` 1169, `chapter_ops`
955, `witness_metrics` 772); `turn_ops` is the only B-rated MI file; the size gate
guards only `session.py` while the three offenders drifted unguarded. The
organization problem is real and worth a planned refactor, not ad-hoc trimming.

**J2 — `world_state.py` (454) is a fourth ceiling-breach the FR omitted.**
Workstream A's generalized sweep at `<= 450` will RED on `world_state.py` too. It
is only 4 lines over and does not tangle concerns, so it is trimmed under the
ceiling inside Workstream A (a trim, NOT a split, and NOT an xfail entry — xfail is
reserved for the genuinely-needs-splitting trio). The gate threshold is the
`CLAUDE.md` hard max of 450. AC updated.

**J3 — "Zero import-path change" is false; choose true decoupling, not facade
re-exports.** The dominant import style across the package is whole-module
(`from ...api import turn_ops`) with `turn_ops.symbol` access — ~30 such callsites
for `turn_ops` alone (`build_allowed_scene_cast`, `dead_character_names`,
`invoke_final_cut`, the nav primitives), and `chapter_ops.compose_book_deterministic`
(16), `.close_chapter` (13), `.outline_chapters` (7). Splitting therefore *must*
touch callsites. Two options: (a) leave facade re-exports in the emptied module so
`turn_ops.X` keeps resolving, or (b) migrate the callsites to the new module.
Commandment 8 forbids compat shims/adapters, and a re-export hub would leave
`turn_ops` still referencing every split-out symbol (defeating the decoupling).
**Decision: (b)** — migrate callsites within the DM package; they are all
first-party and under the 271-test net. The FR-534 `_state_map_*` re-exports are not
a precedent here: those exist to satisfy a *test identity contract*, not to dodge
callsite churn. The plan's framing is corrected accordingly.

**J4 — Workstream B dissolves the FR-534 circular import (make it an explicit
goal).** `lifecycle_resolver` lazily imports `turn_ops._previous_chapter_id`,
`_chapter_card`, `inherited_seam_packet` *inside functions* purely to break a
cycle. Those are exactly the nav primitives Workstream B consolidates. If they land
in a **leaf** module (`chapter_nav.py`) that imports neither `turn_ops` nor
`lifecycle_resolver`, then `lifecycle_resolver` imports them directly at module
load and the lazy-import dance disappears. This is promoted from incidental to an
acceptance criterion: B must leave no lazy import-cycle workaround behind.

**J5 — The proposed split seams match external usage; approved.** External symbol
imports line up with the clusters: `chapter_ops`'s public face is the lifecycle
cluster (`compose_book_deterministic`, `close_chapter`, `outline_chapters`,
`reoutline_chapter_beats`) plus the prose-continuity detectors used by
`test_dead_character_prose.py`; `turn_ops`'s is `invoke_turn` / `invoke_final_cut`
/ `final_cut_context` / `build_allowed_scene_cast` / `dead_character_names` / the
nav primitives. The target module names in Workstream C are approved as indicative;
final names may be adjusted during enforcement so long as the seams hold.

**J6 — Complexity reduction is OUT of scope.** The D-rated blocks
(`apply_ledger_delta` 28, `_post_revise_invariant_failures` 28,
`_update_live_synopsis` 23, `dead_character_names` 21) are NOT rewritten here. This
FR moves code; it does not re-logic it. Rewriting a hot function while moving it
would void the "behaviour-neutral, suite-green-per-commit" guarantee. A separate FR
may target CC. AC updated to state this explicitly so enforcement cannot scope-creep.

**J7 — Workstream D deferred to FR-537; not authorized now.** The folder move
re-prefixes every `examples.dungeon_master.api.X` import repo-wide (scripts, tests,
sibling modules) and its benefit (visual grouping) is cosmetic beside the size and
cohesion wins of A+B+C. It is split to a follow-up FR, gated on A+B+C landing and
evidence the flat layout still impedes navigation. Authority is withheld for D.

**J8 — Process.** Example-scoped: no `@pytest.mark.req` on the new tests (FR-474
J3). Type `refactor` (skips the changelog + diary CI gates), but a Distill diary
entry is still required by doctrine on completion. The generalized size gate
(Workstream A) is the RED->GREEN witness: it ships green via an xfail list for the
trio, and each subsequent split removes exactly one xfail — the gate mechanically
tracks progress. Re-run jscpd after B and vulture after each split (already AC).
Each extraction is its own commit.

**Verdict: scope frozen to Workstreams A + B + C. Authority granted. Order: A
(generalized gate, incl. world_state trim) -> B (nav consolidation + cycle
dissolution) -> C (the three splits, each its own commit).** Workstream D ->
FR-537.

## Implementation (2026-06-19 — COMPLETE, A+B+C)

**Status: DONE.** All three authorized workstreams landed; DM suite green
(294 tests, zero xfail); ruff/lint-imports/vulture/jscpd clean. Workstream D
remains deferred to FR-537 (untracked draft present, not committed under this FR).

### Commit trail (one concern per commit)

| Workstream | Commit | What |
|------------|--------|------|
| A (RED) | `1fc33301` | Generalize size gate to sweep all `api/**/*.py` at <= 450; trio xfail-listed |
| A (GREEN) | `4020fa21` | Trim `world_state.py` (454) under the ceiling |
| B | `c3bf6051` | Consolidate nav primitives into leaf `chapter_nav.py`; dissolve FR-534 lazy cycle |
| C-1 | `3ee87229` | Split `witness_metrics.py` -> `gap_detectors.py` |
| C-2 | `bb71e6ce` | Split `chapter_ops.py` -> `prose_continuity.py` + `outline_ops.py` |
| C-3 | `b822b936` | Split `turn_ops.py` -> `turn_state.py` + `chapter_open.py` + `final_cut.py` |

### Decisions and deviations

- **Four-way `turn_ops` split, not the three-way the plan sketched.** The plan's
  Workstream C listed `turn_ops` -> `{turn_ops, chapter_open, scene_cast,
  final_cut_ops}`. During enforcement the cast/lifecycle helpers
  (`build_allowed_scene_cast`, `filter_roster_for_lifecycle`,
  `_drop_within_chapter_exits`, `_chapter_cast_exits`) proved to be opening-gate
  concerns, so they merged into `chapter_open.py` rather than a standalone
  `scene_cast.py`; `dead_character_names`/`_possession_facts` moved to `final_cut`
  (their only callers). Net modules: `turn_ops` (play loop), `chapter_open`
  (gate + opening + cast admission), `final_cut` (assembly), and a new **leaf
  `turn_state.py`** (see next). Final names differ from the indicative plan names
  (`final_cut.py` not `final_cut_ops.py`), which J5 explicitly permitted.
- **New leaf `turn_state.py` to break a fresh cycle (J4 generalized).** Play
  (`turn_ops`) imports `chapter_open` for the gate helpers; `chapter_open` needs
  `turn_direction` and other turn/chapter accessors. Had those primitives stayed
  in play, `chapter_open` -> `turn_ops` -> `chapter_open` would cycle. Extracting
  the primitives (chapter/turn accessors, `reset_chapter_for_replay`,
  `CHAPTER_TURN_CAP`, `chapter_should_close`, `climax_turn`, `chapter_beats`) into
  a leaf that imports none of the split trio dissolves it. Verified acyclic:
  `turn_state` (leaf) <- `chapter_open` <- {`turn_ops`, `final_cut`}.
- **Five gate helpers promoted to public (J3 decoupling).** Production play code
  (`invoke_turn`, `running_scene`) imports the gate helpers across the new module
  boundary; private cross-module production imports are a smell, so
  `enforce_memory_precedence_gate`, `compile_opening_onepager`,
  `format_opening_onepager`, `enforce_lifecycle_gate`, and
  `filter_roster_for_lifecycle` dropped their leading underscore.
- **No facade re-exports (J3 honored).** All API + test consumers were migrated to
  the new module homes — `git grep` confirms zero `turn_ops.<moved-symbol>` and
  zero `from ...turn_ops import <moved-symbol>` remain. The sole exception is the
  deliberate `_state_map_*` identity re-exports kept in `turn_ops`, which
  `test_protected_character_projection.py` asserts on by object identity (the same
  FR-534 test-contract exemption J3 named).
- **Test-double retarget.** `test_final_cut_revise_cycle.py` monkeypatched
  `turn_ops.invoke_final_cut`; since `chapter_ops.close_chapter` now calls
  `final_cut.invoke_final_cut` (module-attribute lookup), the patch was retargeted
  to the `final_cut` module so the stub still intercepts.

### Final state

- Module sizes: `turn_state.py` 195, `chapter_open.py` 335, `final_cut.py` 312,
  `turn_ops.py` 332 — all under the 450 ceiling. The `test_module_size.py`
  `_NEEDS_SPLIT` xfail set is now **empty**.
- Gates: `ruff check` clean (one auto-fixed import-order on `turn_ops`);
  `lint-imports` 1 kept / 0 broken; `vulture --min-confidence 80` no findings;
  `jscpd --min-lines 8` 0 clones across the four modules.
