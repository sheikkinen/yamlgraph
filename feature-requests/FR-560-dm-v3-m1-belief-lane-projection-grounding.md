# Feature Request: FR-560 DM v3 M1 — belief lane: graduate `api/plot/`, projection, grounding, live exclusion seam

**Priority:** HIGH
**Type:** Feature
**Status:** Judged (2026-06-21)
**Effort:** 3–4 days
**Requested:** 2026-06-21

## Summary

Graduate the proven M0 spike (FR-559) into the production typed island `examples/dungeon_master/api/plot/`,
add the two M1 capabilities the spike deliberately omitted — **plan projection**
(`chapter_cast` / `exclusion_set` / `protected_set`) and the **belief-grounding** narrative check
(`_check_belief_grounding`) — **and wire `exclusion_set` into the live chapter-open director** as an
additive strangler seam through the now-Enforced FR-556 typed accessor. This is milestone **M1** of
[`design-v3-plot-model-implementation.md`](../examples/dungeon_master/docs/design-v3-plot-model-implementation.md)
§7 ("belief lane **on** the `world_state` ledger, strangler-fig"). M0 proved an off-the-shelf planner
can *tell* floodmark; M1 makes the model a real imported contract, exposes the derived sets, **and
lets a validated plan actually steer the prose constraints** — demonstrably, on floodmark, without
the LLM author pass (that is M4).

## Value Statement

DM maintainers get the first **shippable, demonstrable** strangler-fig increment of v3: when a
validated `PlotPlan` is attached to a book, the chapter-open director's `must_exclude` is augmented
by `exclusion_set(plan, chapter)` — so Arnulf is provably barred from the chapter-3 stage and
released at the chapter-6 reveal **by the real director**, computed from the authored plan instead
of reconstructed from prose. A `report` command makes the whole guard human-inspectable at a glance.

## Problem

FR-559 proved the approach in a **standalone, throwaway** spike (J4: `spikes/floodmark_up/schema.py`
is explicitly *not* the production contract, not imported by v2). Three gaps remain before the
belief lane can feed any prose decision:

1. **No production home.** The schema, `build_problem`, and the causal/lifecycle checks live in a
   spike package excluded from the file-size and import-linter gates. Nothing imports them; they
   cannot be depended on.
2. **No projection.** The plan can be *validated* but cannot yet answer the question the prose
   layer actually asks: "at chapter 3, who is presumed-dead-and-not-yet-revealed and therefore
   must stay offstage?" That is `exclusion_set`, and it does not exist.
3. **No belief grounding.** The M0 lifecycle check catches world-truth revival, but nothing yet
   catches an *unearned reveal* — a beat that flips a belief to alive that was never established
   as dead (or a `G` invariant that depends on a belief gap no beat ever closes). The reveal must
   be grounded in a prior opening beat.

## Proposed Solution

A new typed-island package promoted from the spike, two pure additions, one additive live seam, and
a human-inspectable report.

```
examples/dungeon_master/api/plot/          # NEW production package (graduated from the spike)
  __init__.py
  schema.py        # PlotPlan/Function/Fluent/Belief/AffectDelta — graduated, now THE contract (was J4-throwaway)
  up_model.py      # build_problem(plan) -> up.Problem — graduated unchanged (belief reified, J2 done_<id>, J3 chain)
  validate.py      # solve_status (causal, UP) + _check_monotonic_lifecycle + _check_belief_grounding (NEW)
  project.py       # NEW — chapter_cast / exclusion_set / protected_set (pure, over PlotPlan)
  report.py        # NEW — human-inspectable table (protected / per-chapter cast / exclusion / grounding)
```

The spike package `spikes/floodmark_up/` is **deleted**; its floodmark/early-reveal/world-revival
fixtures move to `examples/dungeon_master/tests/fixtures/` (or a test module) so the M0 regression
assertions survive the graduation, now importing from `api/plot/`.

### Projection (`api/plot/project.py`) — pure, design §5 signatures

```python
def chapter_cast(plan: PlotPlan, chapter: int) -> list[str]:
    """Subjects + targets + observers of functions scheduled at `chapter`."""

def exclusion_set(plan: PlotPlan, chapter: int) -> set[str]:
    """Characters the prose must NOT place onstage at `chapter` (non-circular M1 rule, J3):
    `X in exclusion_set(plan, c)` iff the latest belief beat about `alive(X)` at chapter <= c
    sets `held=False` for some observer and no reveal restores `held=True` at chapter <= c.
    Computed from the plan's belief timeline (initial_belief + ordered eff_belief), never from
    the cast (the \"onstage observer\" phrasing was circular). Multi-observer quantifiers are
    out of M1: a single presumed-dead observer suffices to exclude."""

def protected_set(plan: PlotPlan) -> list[str]:
    """The author invariants G — fed to both the director and the final cut."""
```

`exclusion_set` is the load-bearing one: Arnulf is excluded at every chapter `c` where his
`believes(Clan, alive(Arnulf))` is false (opened by F1 at ch1) and `c` precedes his reveal `Fr`
(ch6). At `c >= 6` he is no longer excluded. This is computed from the plan's belief timeline, not
inferred from prose.

### Belief-grounding check (`api/plot/validate.py::_check_belief_grounding`)

A narrative invariant the planner cannot enforce (belief and world fluents are independent by
design, so the planner happily flips a belief that was never opened). **M1 is ungrounded-reveal
ONLY** (J2 — the "unclosed belief gap" branch is cut; belief-side closure is M3-adjacent and had no
witness test):

- **Ungrounded reveal:** a function whose `eff_belief` sets `believes(obs, alive(c))=True` is a
  flaw (`ungrounded_reveal`, aligned to design §2's `PlanFlaw` Literal — J1) unless an
  *earlier-ordered* function set the same observer's belief `=False` first (or the initial belief is
  `False`). A reveal must un-tell a secret that was actually told.

`ValidationResult.flaws` gains the `ungrounded_reveal` code alongside the existing
`lifecycle_violation` (the graduated schema carries **only** these two — J4b — not the full design
§2 six-code Literal; the schema grows per milestone). `validate_plan` runs lifecycle +
belief-grounding; the causal `solve_status` stays a separate call (it owns checks 1/5/6, these own
2/3). Projection + grounding are **pure** and do **not** import `unified-planning`.

### Live exclusion seam (`chapter_open.compile_opening_onepager`) — additive strangler-fig

FR-556 is **Enforced**: `chapter_nav` is the typed read owner and `chapter_open.compile_opening_onepager`
already builds `must_exclude` from the reconstructed seam packet. M1 makes that the strangler seam —
**additively, plan-optional, behavior-preserving when no plan is attached**:

- A validated `PlotPlan` may be attached to the doc (a `plot_plan` key, written once at the boundary;
  no LLM author pass — the plan is a fixture or hand-authored at M1). A small `chapter_nav` getter
  `attached_plot_plan(doc) -> PlotPlan | None` is the sole typed read (FR-556 discipline).
- When a plan **is** present, `compile_opening_onepager` unions `exclusion_set(plan, ordinal)` into
  `must_exclude` (de-duped, **before** the existing `must_exclude[:12]` truncation so a late-added
  exclusion is never silently dropped — J3b). Two impedance bridges are pinned:
  - **cid -> ordinal (J3a):** `compile_opening_onepager(doc, cid: str)` keys by chapter-id string;
    `exclusion_set(plan, chapter: int)` keys by integer ordinal. The bridge is the existing
    `chapter_open._chapter_index(doc, cid) -> int` (1-based ordinal from `chapters.order`). The
    seam queries `exclusion_set(plan, _chapter_index(doc, cid))`; the seam test asserts the bridge
    by using a doc whose `chapters.order` makes `_chapter_index` yield 3 and 6.
  - **id -> display name (J3b):** `exclusion_set` returns character ids; `must_exclude` is
    `list[str]`. **M1 is scoped to `id == display_name`** (frozen in the seam docstring); the bare
    character id string is unioned in (e.g. `"Arnulf"`). A later FR introducing a separate display
    name adds the mapping + a witness where `id != display_name`.
- When **absent**, the function is byte-for-byte unchanged — every existing book and the 407 DM
  tests are untouched.
- The seam is **additive only** (it can *add* an exclusion the reconstruction missed; it never removes
  a v2 constraint). This honors design §5's "projection replaces reconstruction" as a *strangler*, not
  a rip-out: v2 stands, the plan tightens it, and the reconstruction path is retired in a later FR once
  the plan is authored for every book (M4).

This makes M1 **demonstrable end-to-end**: attach the floodmark `PlotPlan`, run the real director, and
see `Arnulf` in `must_exclude` at chapter 3 and gone at chapter 6 — through `compile_opening_onepager`,
not a unit test of the pure function.

### Human-inspectable report (`api/plot/report.py`)

The projection answers plain-language questions, so M1 ships a `report` that renders them as a table
(the M1 analogue of M0's `run.py` chapter-order print):

```
$ python -m examples.dungeon_master.api.plot.report floodmark

PROTECTED (author invariants G): Arnulf
  ch | cast                 | must-NOT-appear (presumed dead, pre-reveal)
  ---+----------------------+--------------------------------------------
   1 | Arnulf               | —
   3 | (none)               | Arnulf        ← floodmark guard active
   6 | Arnulf, Clan, Hilde  | —             ← reveal landed
belief-grounding: OK (every reveal un-tells a secret an earlier beat told)
```

## Acceptance Criteria

- [ ] `examples/dungeon_master/api/plot/` exists with `schema.py`, `up_model.py`, `validate.py`,
      `project.py` (`__init__.py` exporting the public surface).
- [ ] `spikes/floodmark_up/` is **deleted**; the floodmark / early-reveal / world-revival fixtures
      survive in the test tree and import from `api/plot/`.
- [ ] Graduated schema is now a **real contract**: `schema.py` no longer carries the J4 "throwaway"
      docstring; it is imported by `up_model`, `validate`, `project`. It is **not** subject to
      import-linter (`.importlinter` has `root_package = yamlgraph`; `examples/.../api/plot/` is
      outside it — J4a); the gates that **do** apply are file-size (≤450) and `ruff`. `api/plot/`
      stays a **leaf** (imported *by* `chapter_open`, never importing it — J4c).
- [ ] **RED test first** (committed separately, `SKIP=pytest`): `test_plot_projection.py` +
      `test_belief_grounding.py` + `test_plot_exclusion_seam.py` asserting:
  - `exclusion_set(floodmark, 3)` contains `"Arnulf"` (presumed dead, pre-reveal);
  - `exclusion_set(floodmark, 5)` **still** contains `"Arnulf"` (boundary: reveal is ch6, J3);
  - `exclusion_set(floodmark, 6)` does **not** contain `"Arnulf"` (reveal landed);
  - `chapter_cast(floodmark, 6)` contains the reveal's subject + observers;
  - `protected_set(floodmark)` equals the plan's `G` characters;
  - an `ungrounded_reveal_variant` (reveal flips a belief never set false) yields one
    `ungrounded_reveal` flaw; the canonical `floodmark` yields **none**;
  - **the live seam:** a doc whose `chapters.order` yields ordinals 3 and 6 with the floodmark plan
    attached -> `compile_opening_onepager(doc, "3")` `must_exclude` contains `"Arnulf"`;
    `compile_opening_onepager(doc, "6")` does **not**;
  - **behavior-preserving:** a doc with **no** plan attached produces a `must_exclude` byte-identical
    to the pre-FR-560 result (characterization test pins the additive-only contract).
- [ ] The M0 regression assertions still pass against the graduated package: `solve_status(floodmark)
      in POSITIVE_OUTCOMES`, `solve_status(early_reveal_variant) in PROVEN_UNSOLVABLE`,
      `validate_plan(world_revival_variant)` → `lifecycle_violation`.
- [ ] GREEN: `project.py` + `_check_belief_grounding` + the additive seam in `compile_opening_onepager`
      + `chapter_nav.attached_plot_plan` make the new tests pass; the existing 407 DM tests stay green.
- [ ] `report.py` runs (`python -m examples.dungeon_master.api.plot.report floodmark`) and prints the
      protected set, per-chapter cast/exclusion table, and grounding verdict; the report lives under
      `api/plot/` (not `examples/demos/`, so demo-gate does not apply — J4e) and a fixture-asserted
      snapshot test pins the table.
- [ ] `unified-planning` stays an **optional** dependency: projection, grounding, the seam, and the
      report run **without** it (pure, no planner); only the graduated causal tests `importorskip`.
- [ ] Example-test conventions: NO `@pytest.mark.req`, NO capability YAML (FR-474 J3).
- [ ] Changelog fragment in `changelog/unreleased/` (`type: feat`, `scope: examples`, no `req:`).
- [ ] Diary reflection entry in `docs/diary/`.

## Alternatives Considered

- **Keep M1 pure; defer the live seam to a follow-on.** Rejected — FR-556 is now **Enforced**, so the
  typed accessor the seam needs already exists; deferring would make M1 a half-step with no visible
  behavior. The additive, plan-optional seam is low-risk (byte-identical when no plan is attached) and
  is what makes M1 the *demonstrable* floodmark-defect increment design §7 intends.
- **Replace the v2 reconstruction path outright (design §5 "replaces").** Rejected for M1 — every
  current book is prose-first with no attached plan; ripping out reconstruction now would break all 407
  tests and 42 live books. Strangler-fig: the plan *adds* exclusions when present; reconstruction is
  retired only once M4 authors a plan for every book.
- **Keep the spike package and add projection beside it.** Rejected — leaving the schema in
  `spikes/` keeps it outside the file-size and import-linter gates and signals "throwaway" for a
  contract other modules now import (`framework_costume` via the back door). M1 is precisely the
  graduation point.
- **Fold affect-closure into the grounding check.** Rejected — affect (Lehnert plot units) is a
  distinct lane with its own `AffectDelta` open/close semantics; it is M3 (design §7). M1's
  grounding check is belief-only to keep the new surface minimal and the RED test sharp.
- **Compute `exclusion_set` from the UP plan trace instead of the `PlotPlan`.** Rejected — the
  derived sets are a *pure* function of the authored plan's belief timeline; routing them through
  the planner would make a pure query depend on an optional engine for no benefit.

## Related

- [`design-v3-plot-model-implementation.md`](../examples/dungeon_master/docs/design-v3-plot-model-implementation.md)
  — §5 projection signatures, §7 M1 row, §3 validator split.
- FR-559 (M0 spike) — the proven foundation this graduates.
- FR-556 (typed `StoryDoc`) — **Enforced**; provides the `chapter_nav` accessor the live seam reads
  through (`attached_plot_plan` getter + `compile_opening_onepager` union site).
- FR-557 (turn-engine realizer) — consumes the projection at M4, not here.
- FR-558 (gate-on-write) — binds gates to the typed setter; the attached-plan write reuses that seam.

## Judgement (2026-06-21)

**Verdict: APPROVE WITH CONDITIONS.** The scope grew from "pure projection, defer the seam" to
"graduate + project + ground + wire a live, plan-optional director seam + a report" — and the
growth is *justified*: FR-556 is now Enforced, so `chapter_nav` + `compile_opening_onepager` exist
(verified: `chapter_open.py:94`, `must_exclude` assembled at lines 106–109), and an **additive,
byte-identical-when-absent** seam is exactly the demonstrable floodmark increment design §7 names.
The strangler framing is honest (adds exclusions, never removes a v2 constraint; reconstruction
retired only at M4), and keeping `unified-planning` optional for the pure pieces is correct. Four
conditions. **J1, J2, and J3 block enforce**; J4 folds into the diff. The new ones (J3) are not
nitpicks — the single floodmark fixture *hides* two contract gaps that would ship wrong.

**J1 — BLOCKING. The grounding flaw code contradicts the contract it graduates into.** The FR names
the new flaw `ungrounded_belief` (Proposed Solution ×2), but design §2's `PlanFlaw` Literal — the
contract the schema *becomes* ("now THE contract") — declares `ungrounded_reveal`, and the AC even
names the fixture `ungrounded_reveal_variant`. A graduated contract asserting a code the design
contract doesn't define is `intent_drift` on day one. Pick **one**, aligned to design §2:
`ungrounded_reveal`. Make `schema.PlanFlaw.code`, `_check_belief_grounding`, the AC bullet, and the
test all use it. Cheapest bug to kill in the spec.

**J2 — BLOCKING. A production branch with no witness test must not ship (Commandment 7).** The
belief-grounding section specifies **two** behaviours — (a) ungrounded reveal, (b) "unclosed belief
gap (only when `G` demands it)" — but the RED test exercises only (a). Branch (b) merges unexercised
(`detection_without_enforcement`), the speculative surface Purge exists to remove. Resolve in the FR
before enforce: **either** add a RED fixture opening a `G`-demanded belief gap no beat closes (plus
a negative twin), **or** cut (b) from M1. Default: **cut it** — M1's check is sharper as
ungrounded-reveal-only, and (b) is belief-side closure, M3-adjacent. FR text, AC, and tests must
match.

**J3 — BLOCKING. The live seam's two impedance mismatches are untested by the floodmark fixture and
will silently diverge.** The seam is now the headline deliverable, and floodmark hides both gaps
because, for it, every value happens to be the identity:

- **(a) Chapter key mismatch.** `compile_opening_onepager(doc, cid: str)` keys by chapter-**id
  string**; `exclusion_set(plan, chapter: int)` keys by **integer ordinal**. The AC writes
  `compile_opening_onepager(doc, ch3)` as if the director takes an int — it does not. Pin the
  `cid → integer-chapter` bridge in the FR (which `chapter_nav` primitive or card field yields the
  ordinal?) and assert it. Without this the union queries the plan at the wrong chapter or crashes.
- **(b) Entry-shape mismatch.** `must_exclude` is `list[str]` of constraint strings (capped `[:12]`);
  `exclusion_set` returns character **ids**. The FR says "display names". Pin the exact string shape
  unioned in and the id→display-name mapping, and require the union to happen **before** the existing
  `must_exclude[:12]` truncation (so a late-added exclusion is never silently dropped, and the
  byte-identical-when-absent claim still holds). Add one assertion exercising a name where
  `id != display_name`, **or** explicitly scope M1 to `id == display_name` and freeze that
  assumption in the docstring — otherwise the mapping is a hidden `plausible_wrong_answer`.

The behaviour-preserving characterization test (no plan → byte-identical `must_exclude`) is correctly
specified — keep it; it is the contract that makes the seam safe. Also resolve §5-vs-FR wording: the
`exclusion_set` docstring says "every onstage observer", which makes exclusion depend on cast (a
latent circularity). Pin a non-circular M1 rule — *X ∈ exclusion_set(plan, c) iff the latest belief
beat about `alive(X)` at chapter ≤ c sets `held=False` for some observer and no reveal restores it at
chapter ≤ c* — scope multi-observer quantifiers out of M1, and add a boundary assertion
(`exclusion_set(floodmark, 5)` still contains Arnulf), not only the 3/6 endpoints.

**J4 — non-blocking, fold into the diff. Accuracy + island integrity.**
(a) The AC claims the graduated schema becomes "subject to the import-linter layer rules." It does
**not**: `.importlinter` has `root_package = yamlgraph`; `examples/dungeon_master/api/plot/` is
outside it. Real gates that apply: file-size ≤450 and `ruff`. Correct the justification — assert no
gate that will not run.
(b) Graduated `PlanFlaw.code` carries **only** the codes M1 implements (`lifecycle_violation` +
`ungrounded_reveal`), not the full design §2 six-code Literal — declaring codes no check emits is
the same un-witnessed surface J2 guards; the schema grows per milestone.
(c) `api/plot/` must remain a **leaf**: it may be imported *by* `chapter_open`, but must not import
`chapter_open`/`turn_ops`/`seam_entrance` (that reverse edge would couple the typed contract to v2
and break the island). State the one-way seam direction (`chapter_open → api.plot`).
(d) Name the M0 test migration: `tests/test_floodmark_spike.py` imports `spikes.floodmark_up`;
deleting the spike orphans it (`refactor_orphans_secondary`). State the M0 assertions are *re-homed*
onto `api/plot/` imports (rename the module if convenient), so the regression survives the deletion.
(e) `report.py` lives under `api/plot/`, not `examples/demos/`, so the demo-gate does **not** apply;
drop the conditional hedge and require the fixture-asserted snapshot test of the report table.

**Authority granted to enforce once J1, J2, and J3 are folded into the FR text (J4 into the enforce
diff).** Freeze scope to: the graduated `api/plot/` package (`schema`/`up_model`/`validate`/
`project`/`report`/`__init__`); deletion of `spikes/floodmark_up/` with M0 assertions re-homed;
`project.py` with the three design §5 signatures and the pinned non-circular `exclusion_set` rule;
`_check_belief_grounding` as **ungrounded-reveal-only** (J2 default) emitting `ungrounded_reveal`
(J1); the **additive, plan-optional, byte-identical-when-absent** seam in `compile_opening_onepager`
with the pinned cid→ordinal and id→name bridges (J3); `chapter_nav.attached_plot_plan` as the sole
typed read; `report.py`. **No LLM author pass, no reconstruction rip-out, no affect-closure, no
multi-observer belief algebra, no `world_state` ledger rewrite** — those are M3/M4. Example-exempt
(no `@pytest.mark.req`, no capability YAML); `unified-planning` stays optional (projection,
grounding, seam, report run pure — no `importorskip`; only re-homed causal M0 tests gated). RED
commit first (`SKIP=pytest`): `test_plot_projection.py` + `test_belief_grounding.py` +
`test_plot_exclusion_seam.py` (incl. the no-plan characterization) + re-homed M0 assertions,
committed failing before `project.py`/`_check_belief_grounding`/the seam exist. Changelog fragment +
diary required.
