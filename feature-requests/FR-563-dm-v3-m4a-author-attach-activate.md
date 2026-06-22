# Feature Request: FR-563 DM v3 M4a — author & attach (activate the plot lane)

**Priority:** HIGH
**Type:** Feature
**Status:** Enforced (2026-06-22)
**Effort:** 3–4 days
**Requested:** 2026-06-21

## Summary

Flip the v3 plot lane from **dormant verification** to **live generation steering**. Today every
FR-559→562 increment proves, projects, and reports continuity, but nothing in book generation ever
attaches a `PlotPlan` — so `chapter_nav.attached_plot_plan(doc)` returns `None` and the FR-560
exclusion seam never fires (verified: the only writer of `doc["plot_plan"]` is a test). M4a adds the
**authoring half**: a `plot_plan.yaml` graph that turns a synopsis into a validator-gated `PlotPlan`,
a tolerant boundary parse (`author.py`), and the **single typed attach point** that writes the
validated plan onto the doc — at which the already-wired exclusion seam comes alive with no further
change to `chapter_open`. (The production driver call that exercises this on every real run is M4b's
load-taking step — see *Value Statement* J2b and *Out of Scope*.)

This is the **first half of milestone M4** of
[`design-v3-plot-model-implementation.md`](../examples/dungeon_master/docs/design-v3-plot-model-implementation.md)
§6a + §7. The **realize half** (§6b, `Function → TurnRequest`) is deferred to a successor (M4b /
FR-564) because it is independently judge-able and is blocked on reconciling a stale design sketch
(see *Out of Scope*).

## Value Statement

DM maintainers get the **machinery** that makes the three-milestone continuity guarantee *applicable*
to a generated book: a synopsis becomes a validated `PlotPlan`, and a single typed attach call is all
that stands between the dormant lane and a live one. The floodmark defect class — a presumed-dead
character wandering onstage before their reveal — stops being something the validator can catch *in
principle* and becomes something the chapter-open director excludes the moment a plan is attached,
because the plan that proves it unspellable is the same plan the director reads.

**Scope honesty (J2b).** M4a builds and *deterministically witnesses* author + parse + attach + seam
activation (every acceptance test attaches the plan explicitly, no live LLM). It does **not** yet wire
the production generation driver to author-and-attach on every real run — that load-taking step lands
with the **M4b end-to-end render** (FR-564), where a real 6-chapter book is generated and measured.
M4a's "(activate the plot lane)" means: deliver the capability and the single additive call that
*makes* activation a one-line driver change, proven live the moment the driver calls it. The strangler
is loaded by M4b; M4a forges the coupling and proves it holds.

## Problem

The lane is fully built but **unreachable from generation**:

- **FR-560** wired `compile_opening_onepager` to union `exclusion_set(plan, ch)` into `must_exclude`
  — but **only when `attached_plot_plan(doc) is not None`**, and it is always `None` in production.
- **FR-559/561/562** built `build_problem`, `solve_status`, and the four pure checks
  (`_check_monotonic_lifecycle`, `_check_belief_grounding`, `_check_causal_antecedent`,
  `_check_affect_closure`) — all gated behind an explicit `PlotPlan` that the generator never creates.

Three things are missing to close the loop:

1. **No authoring graph.** There is no `plot_plan.yaml` and no `author_plot_plan.yaml` prompt, so a
   synopsis never becomes a typed plan. The design §6a sketch exists only on paper.
2. **No boundary parse.** `api/plot/author.py` (design §6a: the tolerant `parse_world_state`-style
   LLM-JSON → `PlotPlan` parse) does not exist. Without it, the schema would trust the provider's
   JSON shape blindly — a boundary violation (Scripture: normalize at the boundary).
3. **No attach point.** Nothing writes the validated plan onto `doc["plot_plan"]`. The seam reads it
   via the FR-556 `chapter_nav.attached_plot_plan` getter, but there is no matching **setter**, so
   the typed-accessor discipline (one owner for the `plot_plan` field) is half-built.

## Proposed Solution

One new graph, one new prompt, one boundary-parse module, one typed setter, one validator tool
wrapper. **No change** to the four checks, the projection, the report, or the live seam logic — M4a
only *feeds* the seam that FR-560 already wired.

### 1. `author.py` — tolerant boundary parse (`api/plot/author.py`, pure)

`parse_plot_plan(raw: dict) -> PlotPlan`, mirroring `parse_world_state`: drop unknown fields,
coerce/normalize known ones (e.g. an out-of-alphabet `FunctionKind` or `WorldPred` is dropped with a
logged warning rather than raising), default empty collections. Never trust the provider's JSON shape
— the LLM output is untrusted external input (Scripture: instruction/provider boundary). Returns a
typed `PlotPlan`; the validator (FR-559→562) then judges its *content*.

### 2. `plot_plan.yaml` graph + `author_plot_plan.yaml` prompt (design §6a)

```yaml
# examples/dungeon_master/plot_plan.yaml
nodes:
  author_plan:
    type: llm
    prompt: author_plot_plan         # output_schema = PlotPlan JSON shape
    state_key: plan_raw
  validate_plan:
    type: python                     # J1: NOT type:tool -- a python node stores the
    tool: plot_validate_plan         #   function's return value DIRECTLY at state_key, so
    state_key: validation            #   validation.ok / validation.flaws exist as written.
    variables:                       #   A type:tool node would wrap output as
      raw: "{state.plan_raw}"         #   {success, result, error} -> validation.result.ok.
  route_validity:
    type: router
    condition: "validation.ok"
    routes: { "true": done, "false": repair_plan }
  repair_plan:
    type: llm
    prompt: author_plot_plan         # re-prompt with validation.flaws in context (bounded)
    state_key: plan_raw
    max_loops: 3
```

The prompt's `output_schema` mirrors the `PlotPlan` JSON shape (`initial_world`, `initial_belief`,
`agents`, `goals`, `functions`, `order`, optional `turn_budget`/`intentional_open`).

**J1 — graph mechanics pinned against the as-built framework.** Three corrections to the design §6a
sketch, all reconciled into the design doc in the same enforce diff (the FR-562 J1 move):

- **Validator is a `python` node, not a `tool` node.** `create_tool_node` / `create_tool_call_node`
  wrap their return in a `{task_id, tool, success, result, error}` envelope, so the router's
  `condition: "validation.ok"` would read a missing key (it would live at `validation.result.ok`).
  `create_python_node` stores the function's return value *directly* at `state_key`, so
  `plot_validate_plan(raw) -> {"ok": bool, "flaws": [...]}` lands as `validation.ok` /
  `validation.flaws` exactly as the router and the repair re-prompt expect. The `tool:` key names the
  registered python callable; `variables:` binds its `raw` arg from `{state.plan_raw}` (graph-root-
  relative resolution).
- **Router shape** uses the framework's real `condition:` + `routes: {"true":…, "false":…}` form
  (confirmed against existing routers), keyed on the boolean `validation.ok`.
- **Bounded in-graph retry is a NEW DM pattern, named as such.** Every v2 DM graph is single-shot;
  v2 retry is Python-driven across two graphs (`chapter_outline.yaml` → `chapter_reoutline.yaml`).
  The `max_loops: 3` `repair_plan` loop is a deliberate, defensible departure (it is a core YAMLGraph
  feature) — *not* "the v2 author-gate-retry pattern." Humans stay out of the inner loop.
- **One consistent name set (J6c):** `plan_raw` (state key) and `plot_validate_plan` (function);
  design §6a's `plan_json` / `plot.validate_plan` are updated to match in the same diff.

### 3. `plot_validate_plan` python-node wrapper

A thin function exposing `parse_plot_plan` + `validate_plan` to the graph: takes `raw` (the LLM
JSON), parses it tolerantly, runs the four pure checks, returns a plain `{"ok": bool, "flaws": [...]}`
dict (consumed directly by the router — J1). Lives in `api/plot/author.py` (or a thin `plot_tools.py`)
and is registered as the graph's python tool.

**J4 — authoring stays engine-free (FR's own recommendation, confirmed).** The wrapper runs **only**
the four pure checks (`validate_plan`). It does **not** call `solve_status`: that needs the optional
`unified-planning[fast-downward]` engine, is slow, and its `UNSOLVABLE_INCOMPLETELY` proof is the
gated *offline* check (FR-559). Keeping it out lets `plot_plan.yaml` run without the optional
dependency installed. (Frozen into scope below.)

### 4. Typed attach point (`chapter_nav.write_plot_plan`, FR-556 discipline)

Add the **setter** that completes the `attached_plot_plan` getter: `write_plot_plan(doc, plan)` is the
one owner of `doc["plot_plan"]`, mirroring `write_chapter_card`. The generation driver calls it once
after the synopsis step, before the first chapter opens. It is *additive*: a run that skips plan
authoring leaves `doc["plot_plan"]` absent and is byte-for-byte unchanged (the FR-560 invariant holds).

**J3 \u2014 the write is gated (FR-558 doctrine).** The architecture binds card validation to the *write
seam, not the writer*: `write_chapter_card` runs its checks and **raises before committing**, "so no
authoring path can persist an un-playable card." `write_plot_plan` follows the same rule \u2014 it runs
`validate_plan(plan)` and raises (e.g. `InvalidPlotPlan`) on any flaw **before** setting
`doc["plot_plan"]`, so the getter's "*validated* `PlotPlan`" contract is un-bypassable even if a future
caller attaches a plan outside the `plot_plan.yaml` graph. The graph's `route_validity` is the *first*
gate (fast, in-loop); the setter is the *last* gate (un-bypassable). `validate_plan` is pure and
engine-free, so the gated write stays fast and dependency-free (consistent with J4).

## Acceptance Criteria (RED first)

RED commit (`SKIP=pytest`) lands failing tests; GREEN makes them pass. Example tests are
requirement-exempt (FR-474 J3): **no** `@pytest.mark.req`, **no** capability YAML.

1. **Tolerant parse drops junk.** `parse_plot_plan({...valid floodmark JSON..., "bogus_field": 1,
   "functions": [{..., "kind": "not_a_kind"}]})` returns a `PlotPlan` with the bogus field dropped
   and the invalid-kind function dropped/normalized — never raises.
2. **Authored plan validates.** A floodmark-shaped JSON parsed by `parse_plot_plan` then run through
   `validate_plan` is `ok` (round-trips the canonical fixture through the boundary).
3. **Attach activates the seam.** After `chapter_nav.write_plot_plan(doc, floodmark)`,
   `compile_opening_onepager(doc, ch3_cid)["must_exclude"]` **contains Arnulf** (the exclusion the
   plan proves), where the same doc *without* the attach does not — the live-seam activation witness.
   (Matches the established `test_plot_exclusion_seam` behavior: Arnulf excluded at ch3, released at
   ch6 — a faithful re-witness through the new setter, not a new seam rule.)
4. **Setter is the sole owner and gates the write (J3).** `write_plot_plan` then `attached_plot_plan`
   round-trips the typed plan; no other module writes `doc["plot_plan"]` (grep-asserted, FR-556
   discipline). **And** `write_plot_plan` of a plan with a validation flaw **raises**
   (`InvalidPlotPlan`) before committing — the FR-558 gate-the-write witness; the doc is left without
   a `plot_plan` key.
5. **Graph lints & routes deterministically (J5).** `yamlgraph graph lint
   examples/dungeon_master/plot_plan.yaml` passes. Routing is witnessed **without a live LLM**: inject
   `plan_raw` directly (`graph run --var-json plan_raw='…'`, or invoke the validator+router subpath) —
   a **valid** floodmark JSON routes to `done`, an **invalid** one routes to `repair_plan`. No API
   key, no `author_plan` call in the test.
6. **Dormant path unchanged.** A doc with no attached plan produces a byte-identical onepager — this
   is the already-green FR-560 `test_seam_is_byte_identical_without_a_plan`; reference it as a
   regression that must stay green (J6a), do not re-assert a duplicate test.

## Fixtures

Reuse `api/plot/floodmark.py` (`floodmark`, variants). Add a `floodmark_json` dict literal (the JSON
the LLM is expected to emit) so the parse/round-trip tests have an authoring-shaped input distinct
from the in-memory `PlotPlan`.

## Out of Scope (deferred to M4b / FR-564 — realize)

- **Production driver wiring (J2b).** The one additive call that runs `plot_plan.yaml` then
  `write_plot_plan(doc, plan)` inside the real generation session — the step that makes the lane live
  *on every book* — lands with the M4b end-to-end render, where a real 6-chapter run exercises and
  measures it. M4a delivers the capability + the deterministic activation witness (AC3); it does not
  claim the production path is wired (see *Value Statement* J2b).
- **`realize.to_turn_request` (design §6b).** Binding each `Function` to the FR-557 turn engine is a
  separate, independently judge-able increment. It is **blocked on a stale design sketch**: §6b shows
  `TurnRequest(cast=, protected=, instruction=, belief_context=, extras={dict})`, but the **as-built
  FR-557** `TurnRequest` is `cast / scene / turn_n / instruction / beats / prior_direction / extras:
  TurnExtras`. M4b must reconcile the sketch to the real signature before coding. Flagged here so the
  judge sees M4a does not depend on it — attaching the plan activates the *exclusion* seam (the
  floodmark defect) without realizing beats through the turn engine.
- **End-to-end 6-chapter witness render.** "Floodmark renders 6 chapters with no continuity break in
  the witness metrics" (§7 M4 acceptance) belongs to M4b, once realize feeds the turn engine.
- **Widening the alphabets (J6b).** `FunctionKind`/`AffectKind`/`WorldPred` stay the floodmark subset;
  grow only when a check needs it (`regex_fourth_exclusion` discipline). Also frozen below.

## Frozen Scope (judgement authority, J1–J6 folded)

Enforce is authorized to land exactly this, and no more:

- **`author.parse_plot_plan(raw: dict) -> PlotPlan`** — pure tolerant boundary parse mirroring
  `parse_world_state`: drop unknown fields, normalize/drop off-alphabet `FunctionKind`/`WorldPred`,
  default empty collections, **never raise**.
- **`plot_validate_plan(raw) -> {"ok": bool, "flaws": [...]}`** — a **`python`-node** wrapper (J1)
  running **only** the four pure checks via `validate_plan`; **no `solve_status`** (J4).
- **`plot_plan.yaml`** graph (`author_plan` llm → `validate_plan` python → `route_validity` router →
  bounded `repair_plan` llm, `max_loops: 3`) + **`author_plot_plan.yaml`** prompt (`output_schema` =
  `PlotPlan` JSON). The in-graph repair loop is named as a **new DM pattern**, not the v2 two-graph
  retry (J1).
- **`chapter_nav.write_plot_plan(doc, plan)`** — the sole owner of `doc["plot_plan"]`, **gated**:
  runs `validate_plan` and raises before committing (J3, FR-558 doctrine).
- **`floodmark_json`** fixture (authoring-shaped JSON) in `api/plot/floodmark.py`.
- **Design §6a reconciliation** in the same diff: node type (`python` not `tool`), name set
  (`plan_raw` / `plot_validate_plan`), and the new-pattern note (J1, J6c).

**Not in scope:** `realize.to_turn_request` (M4b), the production driver call (M4b, J2b), the
end-to-end witness-metrics render (M4b), `solve_status` in the authoring loop (J4), any
`FunctionKind`/`AffectKind`/`WorldPred` growth (J6b), and any change to the four checks, the
projection, the report, or the seam logic. Example-exempt (FR-474 J3): **no** `@pytest.mark.req`,
**no** capability YAML. `unified-planning` stays optional (the graph and checks run pure). RED commit
first (`SKIP=pytest`): ACs 1–6 committed failing before `author.py` / `plot_plan.yaml` /
`write_plot_plan` exist. Changelog fragment + diary required.

## Dependencies

- **FR-560 (Enforced):** the dormant exclusion seam in `compile_opening_onepager`, the
  `attached_plot_plan` getter, `exclusion_set`, `report.py`.
- **FR-561 / FR-562 (Enforced):** the full four-check `validate_plan` the authoring graph gates on.
- **FR-556 (Enforced):** the typed `chapter_nav` accessor discipline the new setter extends.
- **FR-557 (Enforced):** the turn engine — *only* needed by M4b, listed for the successor.

## Risks

- **LLM emits off-alphabet plans.** Mitigated by the tolerant `parse_plot_plan` (criterion 1) plus
  the bounded validator-gated retry — an unparseable/invalid plan is repaired, not crashed on.
- **Activation surprises the v2 path.** Mitigated by the additive-only seam (criterion 3 vs 6): the
  plan can *add* an exclusion the reconstruction missed, never *remove* a v2 constraint, and a
  plan-less run is unchanged. The strangler stays reversible (drop the attach call → fully dormant).
- **Scope creep into realize.** Explicitly fenced to *author + attach*; realize is FR-564.

## Successor

**FR-564 (M4b — realize):** `api/plot/realize.to_turn_request(fn, plan) -> TurnRequest` reconciled to
the real FR-557 signature; end-to-end floodmark render with the witness gap-suite proving no
continuity break. To be drafted after M4a is judged.

---

## Judgement (2026-06-21)

**Verdict: APPROVE WITH CONDITIONS.** The milestone is real, correctly scoped at the seam (M4a =
author+attach, M4b = realize), and its foundation claims hold against the code: `attached_plot_plan`
exists with **no production setter** (the only writer of `doc["plot_plan"]` is `test_plot_exclusion_seam.py`,
grep-confirmed); the FR-560 seam unions `exclusion_set(plan, _chapter_index(...))` into `must_exclude`
*additively, before the `[:12]` truncation*; `parse_world_state` is the exact tolerant-boundary
precedent `author.py` should mirror; and the §6b `TurnRequest` sketch **is** stale (as-built FR-557 is
`cast/scene/turn_n/instruction/beats/prior_direction/extras:TurnExtras`, not the sketch's
`belief_context=/extras={dict}`), so deferring realize to M4b is sound, not a dodge. AC3's "Arnulf
excluded at ch3, released at ch6" is the established behavior — it matches `test_plot_exclusion_seam`
verbatim, so it is a faithful activation witness, not a guess. **Six conditions (J1–J6) must be folded
into the FR body before enforce; authority is granted once they are.**

**J1 — fold. Pin the graph mechanics; the §6a/§6b sketches do not match the as-built framework.**
This is the load-bearing condition. The FR copies the design §6a YAML verbatim, but three of its
assumptions are wrong against the code and would fail the very lint AC5 demands:
- **Result envelope.** A `type: tool` node (`create_tool_node`) and the dynamic `type: tool_call`
  node both wrap their output. `create_tool_call_node` stores `{task_id, tool, success, result, error}`
  at `state_key` — so the router's `condition: "validation.ok"` would read a key that does not exist
  (`ok` lives at `validation.result.ok`, not `validation.ok`). The validator step should be a
  **`type: python` node** (`create_python_node` stores the function's *return value directly* at
  `state_key`), so `plot_validate_plan(plan_raw) -> {"ok": bool, "flaws": [...]}` lands as
  `validation.ok` / `validation.flaws` exactly as the router and the repair re-prompt expect. State
  the node type as `python`, not `tool`, and name the function + its module path (`api/plot/author.py`
  or a thin `plot_tools.py`) so the graph's `python` resolver (graph-root-relative) can find it.
- **Input binding.** The node must receive `plan_raw` — pin how (the `python` node's `variables:` /
  args resolution, e.g. `variables: {raw: "{state.plan_raw}"}`), not leave it implicit.
- **Router shape.** Confirm the router's `route_field`/`routes` form against an existing router (the
  framework keys routing off the node's emitted route value); `condition:` + `routes: {"true":…, "false":…}`
  must be the real supported shape or restated as such. Reconcile the design doc §6a in the **same
  enforce diff** (the FR-562 J1 move): update §6a's node type, the `plot.validate_plan` vs
  `plot_validate_plan` name, and `plan_json` vs `plan_raw` to one consistent set, so spec and code do
  not fork. **Do not introduce an in-graph router-retry loop without acknowledging it is new to DM:**
  every v2 DM graph is single-shot and retry is Python-driven across two graphs
  (`chapter_outline.yaml` → `chapter_reoutline.yaml`). The bounded in-graph `max_loops` repair loop is
  a *defensible* departure (it is a core YAMLGraph feature), but name it as a deliberate new pattern
  in the FR, not as "the v2 author-gate-retry pattern" — that phrasing is inaccurate.

**J2 — fold. Witness production activation, or stop claiming it.** The Value statement says the
guarantee is "actually applied to a generated book" and "the strangler finally takes load," but
**every acceptance criterion attaches the plan by hand** (ACs 3–4 call `write_plot_plan(doc, floodmark)`
directly). Nothing exercises the claimed production path — "the generation driver calls
`write_plot_plan` once after the synopsis step." As written, M4a builds the machinery and leaves the
lane **still dormant in production** (only tests attach), which contradicts the headline. Resolve the
gap honestly by splitting the proof:
- **Machinery** (parse, validate, attach, seam) — witnessed by the deterministic unit ACs (no LLM).
- **Production wiring** — the one additive driver call that runs `plot_plan.yaml` then
  `write_plot_plan` — witnessed by the **demo** (`generate_and_review.sh` → `demo-output.log`,
  demo-gate), *not* a unit test, because authoring needs a live LLM and the suite is API-free. Add an
  AC: "the generation driver attaches an authored plan on a real run, proven by a committed
  `demo-output.log` showing a plan-derived exclusion in a chapter onepager." If you do **not** wire
  the driver in M4a, then say so and soften the Value statement to "build the author+attach machinery;
  driver wiring lands with the M4b end-to-end render" — but do not claim load is taken while no path
  takes it.

**J3 — fold. Decide `write_plot_plan`'s gate, against the FR-558 doctrine.** The architecture is
explicit that the card setter binds its validation **to the write seam, not the writer**
(`write_chapter_card` runs `validate_chapter_card` + `gate_chapter_card` and *raises before
committing*, "so no authoring path can persist an un-playable card"). The FR's `write_plot_plan` is
ungated (a bare `doc["plot_plan"] = plan`), relying on the graph's `route_validity` to have validated
first. That is a real inconsistency with the sibling doctrine the getter's own contract invokes ("the
*validated* PlotPlan"). Choose and record one: **(a)** gate the write — `write_plot_plan` runs
`validate_plan` and raises on flaws, mirroring `write_chapter_card` (recommended: it makes the
"validated" contract un-bypassable and matches FR-558); or **(b)** keep it ungated and justify
explicitly that the plot lane gates in-graph, with a one-line note in the setter docstring pointing at
`route_validity` as the gate. Add the matching AC for whichever is chosen (for (a): "`write_plot_plan`
of a plan with flaws raises").

**J4 — fold (confirm the FR's own recommendation). Keep authoring engine-free.** The FR asks the judge
whether `plot_validate_plan` should also run `solve_status`. **It must not.** `solve_status` needs the
`unified-planning[fast-downward]` engine, is slow, and `UNSOLVABLE_INCOMPLETELY` proofs are the gated
*offline* check (FR-559). Pin into Frozen Scope: the inner authoring loop runs **only the four pure
checks** (`validate_plan`); the causal proof stays the existing offline gate. This keeps `plot_plan.yaml`
runnable without the optional dependency installed.

**J5 — fold. Make AC5 deterministic.** "Graph lints & routes" must not depend on a live LLM. Pin the
harness: lint via `yamlgraph graph lint`; routing via injecting `plan_raw` directly (`graph run
--var-json plan_raw='…'` or invoking the validator+router subpath) with a **valid** floodmark JSON
(→ `done`) and an **invalid** one (→ `repair_plan`), asserting the routed branch — no API key, no
`author_plan` LLM call in the test. State this in the AC so enforce does not reach for an integration
test.

**J6 — fold (minor, tidy in the same pass).** (a) AC6 duplicates the already-green
`test_seam_is_byte_identical_without_a_plan` (FR-560) — reference it as a regression to keep green
rather than re-asserting a new identical test. (b) Restate the alphabet freeze (`FunctionKind`/
`AffectKind`/`WorldPred` stay the floodmark subset) in Frozen Scope, not only in Out of Scope.
(c) Settle the one name set across FR + design + graph + tests: prefer `plan_raw` (state) and
`plot_validate_plan` (function), and update §6a to match.

**Authority granted to enforce once J1–J6 are folded into the FR text.** Freeze scope to: the pure
`author.parse_plot_plan(raw) -> PlotPlan` boundary parse (drop unknowns, normalize off-alphabet,
never raise); the `plot_validate_plan(plan_raw) -> {ok, flaws}` **python**-node wrapper running only
the four pure checks (no `solve_status`); the new `plot_plan.yaml` graph + `author_plot_plan.yaml`
prompt (bounded `max_loops: 3` repair, named as a new DM pattern); the typed `chapter_nav.write_plot_plan`
setter (gate decision per J3); a `floodmark_json` fixture; the deterministic parse/round-trip/attach/
seam/route ACs; and the §6a design reconciliation (J1). Production driver wiring is **either** in scope
with a `demo-output.log` witness (J2a) **or** explicitly deferred with a softened Value statement (J2b).
**No** `realize.to_turn_request` (M4b/FR-564), **no** end-to-end witness-metrics render (M4b), **no**
`solve_status` in the loop (J4), **no** alphabet growth (J6b), **no** change to the four checks /
projection / report / seam logic. Example-exempt (FR-474 J3): **no** `@pytest.mark.req`, **no**
capability YAML. `unified-planning` stays optional. RED commit first (`SKIP=pytest`): the acceptance
tests (parse-drops-junk, authored-plan-validates, attach-activates-seam, setter-sole-owner+gate,
lint+route, byte-identical regression) committed failing before `author.py`/`plot_plan.yaml`/
`write_plot_plan` exist. Changelog fragment + diary required.

---

## Enforcement (2026-06-22)

**RED** `a3f577c2` (`test(examples): FR-563 RED ...`, `SKIP=pytest`): 10 failing tests in
`examples/dungeon_master/tests/test_plot_author.py` (ACs 1–6) plus the `floodmark_json` authoring
fixture in `api/plot/floodmark.py`. **GREEN** (this commit): all 10 pass; full DM suite 461 passed;
`yamlgraph graph lint examples/dungeon_master/plot_plan.yaml` clean.

**Delivered (matches Frozen Scope):**
- `api/plot/author.py` — `parse_plot_plan(raw) -> PlotPlan` (tolerant boundary parse mirroring
  `parse_world_state`: drops unknown fields and off-alphabet functions/atoms, never raises) +
  `plot_validate_plan(state) -> {"validation": {"ok", "flaws"}}` (engine-free, four pure checks).
- `chapter_nav.write_plot_plan(doc, plan)` + `InvalidPlotPlan` — sole gated owner of `doc["plot_plan"]`;
  runs `validate_plan` and raises before committing (J3 = option (a), FR-558 doctrine).
- `plot_plan.yaml` graph + `prompts/author_plot_plan.yaml` prompt — bounded `loop_limits`/`loop_exits`
  author → validate → repair cycle.
- `floodmark_json` fixture; design §6a + §7 M4 reconciled in the same diff.

**Deviations from the J1 sketch (refined during enforce, all within authority — the J1 mandate was
"pin the graph mechanics against the as-built framework"):**
- **Routing is a conditional EDGE, not a `router` node.** J1's fold text still referenced a
  `route_validity` router with `routes: {"true", "false"}`. As-built, a `type: router` node is an
  **LLM classifier** (keys on a schema `route_field`), wrong for a deterministic boolean; and
  `evaluate_condition` **requires a comparison operator** (bare `validation.ok` raises). So the verdict
  lives on plain conditional edges `condition: validation.ok == true / == false` (the five-whys /
  reflexion demo pattern), with the cycle bounded by `loop_limits` + `loop_exits` — exactly the
  "deliberate new DM pattern" J1 asked to be named.
- **`plot_validate_plan` nests its own `validation` key.** A `type: python` node merges a returned
  **dict at the state TOP level** (only non-dict returns go under `state_key`). So the function returns
  `{"validation": {...}}` (not `{ok, flaws}` under a `state_key: validation`) to land at
  `state["validation"]` for the edges. The J1 intent (no tool-wrapper indirection; `validation.ok`
  readable by the route) is preserved; the mechanism is the top-level merge, pinned by the two no-LLM
  routing tests (AC5).
- **Prompt uses prompt-instructed JSON + `parse_json: true`** (the DM house style, e.g.
  `chapter_outline.yaml`), not an `output_schema` block — same effect, consistent with the example.

**J2 = J2b (deferred).** Production driver wiring is not in M4a; the Value Statement was softened at
judge-time and AC3 is the deterministic activation witness. No `examples/demos/` files changed, so the
demo-gate does not apply. **J4** honored: no `solve_status` in the loop; `unified-planning` stays
optional. **J6b** honored: alphabets unchanged.

**Successor:** FR-564 (M4b — `realize.to_turn_request` reconciled to the as-built FR-557 `TurnRequest`,
+ production driver wiring + end-to-end witness render).
