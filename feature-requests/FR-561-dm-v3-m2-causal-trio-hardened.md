# Feature Request: FR-561 DM v3 M2 — causal trio hardened (phantom-reversal + capped reachability + threat)

**Priority:** HIGH
**Type:** Feature
**Status:** Enforced (2026-06-21)
**Effort:** 3–4 days
**Requested:** 2026-06-21

## Summary

Harden the causal half of the validator (design §5 checks **1, 5, 6**) so the planner — not just the
two pure narrative checks — proves the three v2 recognition-gate classes unspellable. M2 makes the
`PlotPlan` causally honest: a `return`/`reveal` with **no authored antecedent** (phantom reversal)
yields `open_condition` (a new pure check); a plan whose total `cost_turns` exceeds a global
`turn_budget` (capped reachability) is proven `UNSOLVABLE` by the engine; and a forced-window causal
threat — a beat scheduled in a chapter **between** a producer and its consumer that **destroys** the
consumed precondition — is proven `UNSOLVABLE` by the *existing* FR-560 encoding (no new machinery),
now witnessed by a fixture. This is milestone **M2** of
[`design-v3-plot-model-implementation.md`](../examples/dungeon_master/docs/design-v3-plot-model-implementation.md)
§7, building on the graduated `api/plot/` from FR-560.

## Value Statement

DM maintainers get the v2 detectors `reversal_pack_gap`, `composition_gap`, and
`unplayable_beat_gap` **collapsed into plan validity** (plan §5): three recognition gates that today
fire (or miss) on generated prose become deterministic pre-prose proofs on the authored plan. A
phantom return is now *impossible to author*, not *caught after the fact* — the floodmark-class
defects retire one tier deeper than M1's belief lane reached.

## Problem

After FR-560, `api/plot/validate.py` has two owners:

- `solve_status` (the UP causal check) currently proves only **reachability of the conjoined
  `done_<id>` goal** — i.e. "can every authored beat fire in *some* order." It does **not** yet model
  (a) the `cost_turns` budget (check 5: capped reachability) or (b) explicit causal-threat
  separation (check 6) beyond what the chapter-chain incidentally enforces.
- The pure checks cover lifecycle + ungrounded-reveal (checks 2, 3).

Three gaps remain before the causal trio matches design §5:

1. **Phantom reversal (check 1, sharpened).** A `return`/`reveal` whose world/belief precondition has
   **no producer** (no earlier beat's effect, not in `I`) must be an `open_condition` flaw. M0/M1
   prove the *belief* precondition case (early-reveal). The *world-truth* antecedent case — "a
   character returns with no authored cause" (plan §3, the `reversal_pack_gap` class) — is not yet a
   distinct, asserted flaw.
2. **Capped reachability (check 5).** `Function.cost_turns` exists in the schema but is **inert** —
   `build_problem` ignores it. A plan whose total `cost_turns` exceeds a global turn budget
   (`unplayable_beat_gap` lineage) is currently spellable. There is no typed budget source on the
   plan to bound against.
3. **Causal threat (check 6).** The current encoding *already* proves the **forced-window** case
   (B between producer A and consumer C, in a strictly-later chapter, clearing a precondition C
   needs) — but this is not yet **witnessed** by a fixture, so the guarantee is incidental rather
   than asserted. (The same-chapter case is *not* a threat: the planner reorders freely.)

## Proposed Solution

Extend the **causal** owner (`up_model.build_problem` + `solve_status`) and add **one pure
structural pre-check** for the phantom-reversal class that does not need the engine. No change to the
M1 pure checks, the projection, or the live seam.

### Check 1 sharpened — phantom-reversal pre-check (`validate._check_causal_antecedent`, pure)

A pure structural check (no UP) that every `pre_world` / `pre_belief` atom of every function is
either in `I` (`initial_world` / `initial_belief`) or produced by an **earlier-ordered** function's
effect. A precondition with no producer is `open_condition`. This is the cheap, engine-free half of
check 1 — it localizes the flaw to the exact function and atom (the planner's "no plan" cannot say
*which* open condition). The UP `solve_status` remains the global coherence proof; this pre-check is
the human-readable localizer, mirroring how M1 split lifecycle/grounding out of the planner.

**`validate_plan` stays pure (J5).** This new check is added *inside* `validate_plan` alongside the
M1 lifecycle/grounding passes; `validate_plan` does **not** call `solve_status`/`build_problem`. The
engine stays optional — checks 5/6 are exercised only through `solve_status` in the gated causal
tests, never through `validate_plan` (so the no-`importorskip` pure path the M1 projection/grounding
tests rely on is preserved).

**Early-reveal is NOT subsumed (J5 corrected during enforcement).** J5 claimed the pure check would
*also* flag `early_reveal_variant.Fonstage` as `open_condition`. That claim is **false** under the
existence-based check this FR specifies: `Fonstage`'s `pre_belief` `believes(Clan, alive(Arnulf))=True`
**is in `initial_belief`** (`held=True`), so it is structurally grounded. Its unsolvability is
*temporal* — `F1` (ch1) flips that belief to `False` before ch3 — which is precisely the planner's
job, not a missing-antecedent (no-producer) flaw. Making the pure check temporal enough to catch this
would re-implement causal coherence and duplicate the engine, violating the design split (check 1 =
engine; checks 2/3/4 = hand-written). So the pure check stays **existence-based** and flags only the
no-producer-ever class; early-reveal remains an **engine** proof. The existing M1 `test_plot_causal`
(early-reveal via `solve_status` PROVEN_UNSOLVABLE) stays green unchanged, and `validate_plan(early_reveal_variant)`
yields **no** `open_condition` flaw.

### Check 5 — capped reachability in `build_problem` (global turn budget, unary counter)

Design §5 defines check 5 as `cost_turns → plan-length bound; no plan within bound ⇒ unreachable` —
a **single global** cap, not a per-chapter one (J2). The schema grows by one typed field on
`PlotPlan`: `turn_budget: int | None = None` (the global plan-length budget; `None` = unbounded, so
the canonical `floodmark` and every M0/M1 fixture are unaffected). When set, `build_problem` encodes
a global **unary-counter** budget: a chain of boolean markers `budget_<k>` (k = budget … 0), each
beat's action consuming `cost_turns` steps down the chain via its precondition/effect, so a plan
whose total `cost_turns` exceeds `turn_budget` cannot reach the conjoined `done_` goal ⇒
`PROVEN_UNSOLVABLE`.

**Unary-counter is the PRIMARY encoding (J4).** The pinned engine is `fast-downward astar(blind())`
(FR-559 J3) — a classical search whose translator does **not** admit numeric (`Int`) fluents, so
numerics would be rejected. The unary-counter boolean chain is therefore the only viable path, not a
fallback. The README records *why* numerics were rejected (FR-559 J3 engine-reality discipline:
assert no encoding the pinned engine cannot run).

### Check 6 — causal-threat: the existing encoding already proves the forced-window case (no `build_problem` change)

The already-enforced `up_model.build_problem` makes a **forced-window** causal threat unsolvable
with no new machinery (J1): a world/belief fluent `p` set `True` by producer A (chapter `a`), set
`False` by threat B (chapter `b`, `a < b < c`), and required `True` by consumer C (chapter `c`) is
*already* unschedulable — C's action precondition `p()` is unsatisfiable after B fires, `p` has no
later producer, and C's `done_` goal is mandatory ⇒ `PROVEN_UNSOLVABLE` today. (The *same-chapter*
case is intentionally **not** a threat: the planner has free intra-chapter ordering and demotes B
after C, so the plan is SOLVABLE — correctly.) M2 therefore adds **no** guard-fluent encoding; it
adds a **forced-window** `threat_variant` fixture that pins B in a chapter strictly between A's and
C's and asserts `PROVEN_UNSOLVABLE` against the current encoding. (Purge: a `protected_<p>` guard
would be redundant in the only case that bites and wrong in the case that doesn't.)

### Flaw codes (schema §2 growth)

`FlawCode` grows from the M1 pair by exactly **one** code: `open_condition` — the only code the new
pure check emits (J3). Capped reachability (check 5) and causal threat (check 6) are proven by the
engine as a `PROVEN_UNSOLVABLE` *status*, **not** emitted as `PlanFlaw`s, so they add no codes. No
`unplayable_beat` code is introduced (it is not in design §2's Literal and nothing would emit it —
FR-560 J4b reaffirmed: no `FlawCode` without an emitter). `PlanFlaw` and `ValidationResult` are
otherwise unchanged.

### Fixtures + report

Three new `PlotPlan` variants beside the floodmark canon (in the test tree, design §4 style):

- `phantom_return_variant` — Arnulf `return`s at ch6 with **no** F1 antecedent (no belief opened,
  no cause) → `open_condition` (pure check).
- `overbudget_variant` — beats whose total `cost_turns` exceed an explicit `turn_budget` set on the
  `PlotPlan` (the typed source, J2) → `PROVEN_UNSOLVABLE` via the unary-counter budget.
- `budget_ok_variant` — the same beats under a sufficient `turn_budget` → still `POSITIVE_OUTCOMES`,
  witnessing that the unary-counter only bites when the bound is exceeded.
- `threat_variant` — a **forced-window** threat: B clears a precondition in a chapter strictly
  between producer A's and consumer C's → `PROVEN_UNSOLVABLE` against the **current** encoding (no
  `build_problem` change, J1).

`report.py` gains a causal-health line (the cumulative `cost_turns` vs `turn_budget` and any
open-condition list), so the trio is human-inspectable like the M1 exclusion table.

## Acceptance Criteria

- [ ] **RED test first** (committed separately, `SKIP=pytest`): `test_plot_causal_trio.py` asserting:
  - `validate_plan(phantom_return_variant)` yields one `open_condition` flaw naming the antecedent-less
    function; canonical `floodmark` yields **none** (pure pre-check, no engine);
  - `validate_plan(early_reveal_variant)` yields **no** `open_condition` flaw (J5 corrected: its
    precondition is in `I`, so it is structurally grounded; early-reveal stays an engine proof);
  - `solve_status(overbudget_variant) in PROVEN_UNSOLVABLE` (global `turn_budget` exceeded);
  - `solve_status(budget_ok_variant) in POSITIVE_OUTCOMES` (the same plan under a sufficient
    `turn_budget` still solves — the unary-counter does not over-constrain when within budget);
  - `solve_status(threat_variant) in PROVEN_UNSOLVABLE` (forced-window threat, current encoding);
  - `solve_status(floodmark) in POSITIVE_OUTCOMES` still holds (the budget encoding did not
    over-constrain the canonical plan — `turn_budget=None` leaves it untouched).
- [ ] The M0/M1 regressions still pass: early-reveal `PROVEN_UNSOLVABLE` (via `solve_status`,
  `test_plot_causal` unchanged), world-revival `lifecycle_violation`, ungrounded-reveal
  `ungrounded_reveal`, projection + seam tests green, all 437 DM tests green.
- [ ] GREEN: `_check_causal_antecedent` (pure, inside `validate_plan`) emits `open_condition`;
  `build_problem` encodes the global `turn_budget` unary-counter (check 5); **no `build_problem`
  change for check 6** (the forced-window fixture proves it against the current encoding); `FlawCode`
  grows by `open_condition` only.
- [ ] `PlotPlan.turn_budget: int | None = None` is the typed budget source (schema §2 growth); a
  witness fixture sets it. `validate_plan` does **not** call the engine (stays pure).
- [ ] `cost_turns` is no longer inert — a doc/comment in `build_problem` states the **unary-counter**
  encoding as primary and records why numeric (`Int`) fluents are rejected by the pinned
  `fast-downward astar(blind())` engine (FR-559 J3 engine-reality discipline). (The package has no
  README; the rationale lives in the `build_problem` docstring — minor deviation, in-code is the
  honest equivalent.)
- [ ] `report.py` prints cumulative `cost_turns` vs `turn_budget` and any open-condition list.
- [ ] `unified-planning` stays **optional**: the phantom-reversal pre-check + report run without it;
  only the capped-reachability/threat causal tests `importorskip`.
- [ ] Example-test conventions: NO `@pytest.mark.req`, NO capability YAML (FR-474 J3).
- [ ] Changelog fragment in `changelog/unreleased/` (`type: feat`, `scope: examples`, no `req:`).
- [ ] Diary reflection entry in `docs/diary/`.

## Alternatives Considered

- **Prove phantom-reversal via UP only (no pure pre-check).** Rejected — the planner's "no plan"
  cannot name *which* precondition is open; M1 already established that human-readable localization is
  worth a pure check beside the engine (lifecycle/grounding precedent). The pure pre-check and the UP
  proof are complementary, not redundant.
- **Per-chapter `cost_turns` budget (a `turns_left_chapter_<n>` cap per chapter).** Rejected (J2) —
  design §5 defines check 5 as a **single global** plan-length bound, and no schema field carries a
  per-chapter budget; inventing one referenced an undefined value. M2 adds one typed field
  `PlotPlan.turn_budget: int | None` and bounds the plan's total `cost_turns` against it.
- **Encode the budget with numeric (`Int`) fluents.** Rejected (J4) — the pinned
  `fast-downward astar(blind())` classical engine does not admit numeric fluents (FR-559 J3); the
  unary-counter boolean chain is the only viable encoding, so it is primary, not a fallback.
- **Add a `protected_<p>` guard-fluent to encode causal threat (check 6).** Rejected (J1) — the
  existing FR-560 fluent + chapter-chain encoding *already* proves the forced-window threat
  `PROVEN_UNSOLVABLE`, and the same-chapter case is not a threat (the planner reorders freely). The
  guard would be redundant where it bites and wrong where it doesn't. M2 witnesses the existing
  guarantee with a forced-window fixture and changes no `build_problem` code.
- **Defer threat (check 6) to M3.** Rejected — design §7 scopes M2 as the **causal trio** (1, 5, 6);
  since check 6 needs no new code (J1), witnessing it here costs only a fixture and keeps the
  `composition_gap` class covered. Affect closure (check 4) is the genuine M3 boundary.
- **Widen `FunctionKind` / `WorldPred` to cover more story shapes now.** Rejected — out of scope;
  M2 hardens the *causal machinery* on the existing floodmark alphabet. Alphabet growth is an M4
  authoring-surface concern, not a validator-hardening one (`regex_fourth_exclusion` discipline:
  don't widen the closed set opportunistically).

## Related

- [`design-v3-plot-model-implementation.md`](../examples/dungeon_master/docs/design-v3-plot-model-implementation.md)
  — §7 M2 row, §3 validator split.
- [`plan-generative-plot-model.md`](../examples/dungeon_master/docs/plan-generative-plot-model.md)
  — §5 checks 1/5/6, §3 phantom-reversal class, §6 capped-reachability lineage.
- FR-559 (M0 spike) — the `build_problem` belief-as-fluent + chapter-chain encoding M2 extends.
- FR-560 (M1) — the graduated `api/plot/` package, pure-check precedent, and `report.py` this builds on.
- FR-557 (turn-engine realizer) — consumes the validated plan at M4; `cost_turns` budget feeds its
  per-chapter turn allocation.

## Judgement (2026-06-21)

**Verdict: APPROVE WITH CONDITIONS.** The phantom-reversal pure pre-check (check 1 sharpened) is
the strongest, best-justified part of the FR: it is genuinely pure, localizes the open condition the
planner cannot name, and follows the M1 lifecycle/grounding precedent exactly. Keep it as-is. But
the two *causal-engine* extensions (checks 5 and 6) are under-specified in ways the floodmark canon
hides, and one of them may need **no new code at all**. Three conditions block enforce (J1–J3); two
fold into the diff (J4–J5). The blocking ones are not nitpicks — J1 risks shipping speculative
machinery that proves nothing, and J2 references a budget value that has no home in the schema.

**J1 — BLOCKING. Prove check 6 needs new encoding before adding the threat guard, or Purge it.**
The FR proposes a `protected_<p>` guard fluent (A sets it, C requires it, B clears it) to make a
causal threat unsolvable. But the **already-enforced** `up_model.build_problem` makes a cross-chapter
precondition-clobber unsolvable with no new machinery: a world/belief fluent `p` set `True` by A
(chapter `a`), set `False` by B (chapter `b`, `a < b < c`), and required `True` by C (chapter `c`)
is *already* unschedulable — C's action precondition `p()` is unsatisfiable after B fires, `p` has
no later producer, and C's `done_` goal is mandatory ⇒ `PROVEN_UNSOLVABLE` today. So for the
*forced-window* case the guard is **redundant**. For the *same-chapter* case the planner has free
intra-chapter ordering and will simply demote B after C ⇒ the plan is **SOLVABLE**, contradicting
the AC's `solve_status(threat_variant) in PROVEN_UNSOLVABLE`. Either way the proposed guard adds
nothing the AC can witness. Resolve in the FR **before** enforce: exhibit a concrete `threat_variant`
that is **SOLVABLE under the current FR-560 encoding but should be UNSOLVABLE** (proving new
machinery is required), **or** drop the guard-fluent encoding and scope check 6 to "the existing
fluent + chapter-chain encoding already proves forced-window threats; the fixture pins B in a chapter
strictly between A's and C's and asserts `PROVEN_UNSOLVABLE` with no `build_problem` change." Default
recommendation: **the latter** — it is the honest reading, and it shrinks M2 to checks 1 + 5.
(`framework_costume` / Purge: do not add a guard the AC cannot distinguish from the status quo.)

**J2 — BLOCKING. The capped-reachability budget has no source and contradicts design §5.** Design
§5 defines check 5 as `cost_turns → plan-length bound; no plan within bound ⇒ unreachable` — a
**single global** plan-length cap. The FR instead invents a **per-chapter** `turns_left_chapter_<n>`
budget and an `overbudget_chapter_variant` with "`budget=6`" — but neither `PlotPlan` nor `Function`
carries any chapter-budget field (verified: `schema.py` has only `cost_turns: int = 1` per function;
`PlotPlan` has `initial_world/initial_belief/agents/goals/functions/order`). The bound value is
referenced but undefined. Pin in the FR before enforce: (a) **global plan-length vs per-chapter** —
if per-chapter, add the budget as a typed field (e.g. a `chapter_budgets: dict[int, int]` on
`PlotPlan`, schema §2 growth, with a witness) and state it; if global, derive the cap explicitly
(sum of `cost_turns`? a `PlotPlan.turn_budget` field?) and cite design §5's plan-length framing.
(b) **The fixture's bound must come from that pinned source**, not a magic literal in prose. Without
a named, typed budget source, `overbudget_chapter_variant` is untestable.

**J3 — BLOCKING. Do not add a `FlawCode` no check emits (FR-560 J4b, reaffirmed).** The FR says
`FlawCode` grows to add `open_condition` "(and, if the pre-check distinguishes it, `unplayable_beat`
for the budget violation)". Two problems: (i) capped reachability is proven by the **engine** as a
`PROVEN_UNSOLVABLE` *status*, not emitted as a `PlanFlaw` — the AC itself asserts it via
`solve_status(...) in PROVEN_UNSOLVABLE`, so nothing emits a budget flaw; (ii) `unplayable_beat` is
not even in design §2's Literal (`open_condition, lifecycle_violation, ungrounded_reveal,
unclosed_affect, unreachable, causal_threat`). Adding a code with no emitter is the exact
un-witnessed surface M1 J4b forbade. Resolve: **M2 adds only `open_condition`** to `FlawCode` (the
one code the new pure check emits). The budget and threat results stay *statuses*, not flaws. Drop
`unplayable_beat` entirely; if a future milestone wants a pure budget *flaw*, it earns a design-§2
code (`unreachable`) plus a witness then.

**J4 — non-blocking, fold into the diff. Unary-counter is the PRIMARY encoding, not a fallback.**
The FR frames `cost_turns` as "numeric (`Int`) fluents … if the pinned config rejects numerics, fall
back to the unary-counter encoding." The pinned engine is `fast-downward astar(blind())` (FR-559 J3),
a **classical** search whose translator does not admit numeric fluents — numerics *will* be rejected,
so the "fallback" is the only path. Lead with the unary-counter encoding as primary (FR-559 J3
engine-reality discipline); mention numerics only to record why they were rejected. Do not present a
default the pinned engine cannot run (mirror of FR-559 J1: "assert no enum the engines don't emit").

**J5 — non-blocking, fold into the diff. ~~The phantom pure-check subsumes early-reveal~~ —
CORRECTED DURING ENFORCEMENT: it does NOT.** `_check_causal_antecedent` flags any
`pre_belief`/`pre_world` atom not in `I` and not produced earlier. `early_reveal_variant.Fonstage`
(ch3) requires `believes(Clan, alive(Arnulf))=True`, which **is in `initial_belief`** (held=True).
The original J5 claim (that the atom is "produced only by `Fr` (ch6)") ignored that it is in `I`, so
the existence-based check finds it grounded and does **not** flag it. Early-reveal's unsolvability is
*temporal* (F1 flips the belief False before ch3) — the planner's job, not a missing-antecedent flaw.
Making the pure check catch it would re-implement causal coherence and duplicate the engine. So the
pure check stays existence-based; early-reveal remains an **engine** proof (`test_plot_causal`
unchanged), and the witnessed AC asserts `validate_plan(early_reveal_variant)` yields **no**
`open_condition`. The M1 invariant J5 also restated stands: **`validate_plan` stays pure — it does
NOT call `solve_status`/`build_problem`** (the engine stays optional; checks 5/6 are exercised only
through `solve_status` in the gated causal tests). This keeps the no-`importorskip` pure path intact.

<details><summary>Original J5 (superseded — the subsumption claim was false)</summary>

> The phantom pure-check subsumes early-reveal — assert it, don't let it be an accident.
> `_check_causal_antecedent` flags any `pre_belief`/`pre_world` atom not in `I` and not produced
> earlier. `early_reveal_variant.Fonstage` (ch3) requires `believes(Clan, alive(Arnulf))=True`,
> produced only by `Fr` (ch6, later) — so the pure check will also flag early-reveal as
> `open_condition`. [Refuted: the atom is in `I`, so it is grounded; see corrected J5 above.]

</details>

**Authority granted to enforce once J1, J2, and J3 are folded into the FR text (J4, J5 into the
enforce diff).** Freeze scope to: the pure `validate._check_causal_antecedent` emitting
`open_condition` (the one new `FlawCode`); capped reachability via the **unary-counter** encoding in
`build_problem` against a **typed, named budget source** (J2); check 6 **either** demonstrated to
need new machinery by a current-encoding-solvable fixture **or** scoped to the existing
encoding with a forced-window fixture and **no `build_problem` change** (J1 default: the latter);
three fixtures (`phantom_return_variant`, `overbudget_chapter_variant`, and the J1-resolved threat
fixture) beside the floodmark canon; a `report.py` causal-health line. **No `unplayable_beat` code,
no numeric-fluent path, no engine call inside `validate_plan`, no alphabet growth, no affect
closure** (check 4 is M3). Example-exempt (no `@pytest.mark.req`, no capability YAML);
`unified-planning` stays optional (the pure antecedent check + report run without it; only the
capped-reachability/threat causal tests `importorskip`). RED commit first (`SKIP=pytest`):
`test_plot_causal_trio.py` (asserting early-reveal yields **no** `open_condition`, J5 corrected)
committed failing before `_check_causal_antecedent` / the budget encoding exist. Changelog fragment +
diary required.

## Enforcement (2026-06-21)

**Status: Enforced.** RED `db11a65c` → GREEN `<this commit>`. 444 DM tests green (was 437; +7 trio).

What landed, against the frozen scope:

- **J1 (check 6 — no new code).** Confirmed at RED: `threat_variant` (forced-window
  `holds(Ledger)`: A ch1 sets, B ch2 clears, C ch3 requires) was already `PROVEN_UNSOLVABLE` against
  the FR-560 encoding before any GREEN change. `build_problem` threat path is **unchanged**. The pure
  antecedent check does **not** flag C (A is a producer; the clearing is temporal — the engine owns it).
- **J2 (typed global budget).** Added `PlotPlan.turn_budget: int | None = None`. `overbudget_variant`
  (floodmark, budget=2, cost sum=3) → `PROVEN_UNSOLVABLE`; `budget_ok_variant` (budget=3) and
  unbudgeted `floodmark` still solve — the counter only bites when exceeded.
- **J3 (one new code).** `FlawCode` grew by exactly `open_condition`. No `unplayable_beat`. Capped
  reachability/threat surface as a `PROVEN_UNSOLVABLE` *status*, never a `PlanFlaw`.
- **J4 (unary counter primary).** `build_problem` emits `rem_<k>` boolean markers (a beat steps the
  counter down by `cost_turns`; runs out → mandatory `done_` goal unreachable). Numeric `Int` fluents
  documented as rejected by the classical engine in the `build_problem` module docstring. The counter
  is emitted only when `turn_budget is not None`, so unbudgeted floodmark is byte-for-byte the M1
  encoding.
- **J5 (CORRECTED).** The judgement's claimed early-reveal subsumption was **false** — surfaced while
  reading the fixture before writing the check. `early_reveal_variant.Fonstage`'s precondition is in
  `I`, so the existence-based check leaves it grounded; early-reveal stays an engine proof. The FR
  text, AC bullets, and the RED test were corrected to assert **no** `open_condition` for early-reveal.
  `validate_plan` stays pure (no engine call). See the diary
  `diary-2026-06-21-the-judge-was-wrong-and-enforcement-found-it.md`.

Deviation: the `api/plot/` package has no README; the unary-counter / numeric-rejection rationale
lives in the `build_problem` docstring (in-code is the honest equivalent of the FR's "README note").

Files: `api/plot/schema.py` (FlawCode + `turn_budget`), `api/plot/validate.py`
(`_check_causal_antecedent`), `api/plot/up_model.py` (unary-counter budget), `api/plot/floodmark.py`
(three fixtures + `budget_ok_variant`), `api/plot/report.py` (causal-health line),
`tests/test_plot_causal_trio.py` (7 tests).
