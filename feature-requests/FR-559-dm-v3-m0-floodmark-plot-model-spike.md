# Feature Request: FR-559 DM v3 M0 — floodmark plot-model spike (unified-planning)

**Priority:** HIGH
**Type:** Feature
**Status:** Enforced (2026-06-21)
**Effort:** 1–2 days
**Requested:** 2026-06-21

## Summary

A runnable proof-of-concept that proves an off-the-shelf classical planner can *tell the
floodmark story* — i.e. author the typed `PlotPlan`, compile belief-as-fluent into a
[`unified-planning`](https://github.com/aiplan4eu/unified-planning) problem, and have the solver
prove the presumed-dead arc satisfiable **and** the early-reveal variant unsolvable, before any
DM v2 code is touched. This is milestone **M0** of
[`design-v3-plot-model-implementation.md`](../examples/dungeon_master/docs/design-v3-plot-model-implementation.md)
and the spike behind §10 Q1 of
[`plan-generative-plot-model.md`](../examples/dungeon_master/docs/plan-generative-plot-model.md).

## Value Statement

DM maintainers get empirical proof — from a real solver, not an assertion — that the v3 plot
model retires the active floodmark reveal-timing defect, de-risking the whole v3 spine for the
cost of a self-contained spike.

## Problem

DM v2 reconstructs plot state from generated prose; the floodmark premise ("presumed drowned,
secretly alive") repeatedly breaks because v2 cannot represent *world-truth alive while everyone
believes dead*. The v3 design proposes a typed authored plan validated before prose. That design
is currently **documentation only** — no code proves an existing library can carry the belief
lane and catch the early-reveal class. Without a runnable falsification, the v3 model FR would
commit on faith.

## Proposed Solution

A standalone spike under `examples/dungeon_master/spikes/floodmark_up/` (NOT wired into v2):

```
examples/dungeon_master/spikes/floodmark_up/
  __init__.py
  schema.py        # minimal PlotPlan/Function/Fluent/Belief/AffectDelta (Pydantic) — design §2 subset
  up_model.py      # build_problem(plan) -> up.Problem; belief reified as boolean fluents
  validate.py      # validate_plan(plan): _check_causal_solvable (UP) + _check_monotonic_lifecycle
  floodmark.py     # the floodmark PlotPlan literal (design §4) + an early_reveal variant + a world-revival variant
  run.py           # prints the solved chapter order — the "tell the floodmark story" skeleton
```

Belief-as-fluent is the load-bearing trick: `believes(Clan, alive(Arnulf))` compiles to a plain
boolean fluent `bel_clan_alive_arnulf`, independent of `alive_arnulf`. `F1` sets the belief false
while leaving world-truth true; an "Arnulf onstage at Ch3" action has precondition
`bel_onstage_alive_arnulf` (false until `Fr`), so the planner cannot schedule it.

**Mandatory-step encoding (J2 — load-bearing).** A classical planner does not *fail* on an action
with an unsatisfiable precondition — it simply skips it. So every authored `Function` must be a
*goal-required* step: `build_problem` gives each function a unique `done_<id>` effect and conjoins
every `done_<id>` into the goal `G`. Then an unschedulable beat makes the **goal** unreachable, and
the early-reveal variant is genuinely unsolvable rather than solved-by-skipping. Without this rule
the negative assertion inverts to `True`.

**Chapter ordinal (J3).** "Onstage at Ch3" is a temporal constraint and STRIPS has no clock. The
spike encodes chapter ordinal as a **sequencing-fluent chain** (`chapter_1 → chapter_2 → …`, each
function gated on its chapter marker) and selects an engine that can **prove** unsolvability
(complete mode), recorded in the spike README. The abstract `aries`-vs-`fast-downward` choice is
only free after this spike confirms one works.

**Three-way outcome (J1 — the proof must be a proof).** `is_solvable` returning a bare bool
conflates `UNSOLVABLE_PROVEN` with `TIMEOUT`/`MEMOUT`/no-engine. The spike must distinguish them.

**J1 engine-reality amendment (2026-06-21, approved).** During de-risking, every pip-installable
UP engine on the target machine (`fast-downward`, `fast-downward-opt`, `symk`, `symk-opt`) was
empirically shown to return `UNSOLVABLE_INCOMPLETELY` — NOT `UNSOLVABLE_PROVEN` — for genuinely,
finitely unsolvable problems (mutex-unsolvable and no-producer static goals). Direct Fast Downward
invocation confirms this is not a wrapper artifact: on a statically-unsolvable PDDL the translator
prints `No relaxed solution! Generating unsolvable task...` and the search prints `Completely
explored state space -- no solution!` (a complete proof), yet FD exits `12`
(`SEARCH_UNSOLVED_INCOMPLETE`), never `11` (`SEARCH_UNSOLVABLE`) or `10` (`TRANSLATE_UNSOLVABLE`).
The UP wrapper maps exit 12 → `UNSOLVABLE_INCOMPLETELY`. `aries` (the design's preferred engine)
*hangs* on untimed classical problems. **Conclusion: `UNSOLVABLE_PROVEN` is effectively
unreachable with the available toolchain.**

The approved resolution preserves J1's *intent* (distinguish a real proof from give-up) while
matching engine reality: for a **complete** search config (`fast-downward` with `astar(blind())`)
on a **finite** problem, an `UNSOLVABLE_INCOMPLETELY` returned *without hitting a resource limit*
IS the proof — `TIMEOUT`/`MEMOUT` are distinct statuses and stay excluded. The discriminator:

```python
# validate.py (sketch)
import unified_planning as up
from unified_planning.shortcuts import OneshotPlanner
from unified_planning.engines import PlanGenerationResultStatus as St
from .up_model import build_problem

class NoEngineAvailable(Exception):
    """Raised when no installed engine supports the problem kind — caller SKIPs."""

# A complete search that exhausts a finite state space proves unsolvability, but this FD build
# reports it as UNSOLVABLE_INCOMPLETELY (exit 12), never UNSOLVABLE_PROVEN. Both count as proven.
PROVEN_UNSOLVABLE = (St.UNSOLVABLE_PROVEN, St.UNSOLVABLE_INCOMPLETELY)
GAVE_UP = (St.TIMEOUT, St.MEMOUT, St.INTERNAL_ERROR)

def solve_status(plan) -> St:
    problem = build_problem(plan)            # belief reified; mandatory done_<id> steps (J2)
    try:
        # Pin a complete engine + config so exhaustion is a proof, not a heuristic give-up.
        with OneshotPlanner(name="fast-downward",
                            params={"fast_downward_search_config": "astar(blind())"}) as planner:
            return planner.solve(problem).status
    except up.exceptions.UPNoSuitableEngineAvailableError as e:
        raise NoEngineAvailable(str(e)) from e

# Positive: status in POSITIVE_OUTCOMES.
# Proven negative: status in PROVEN_UNSOLVABLE (complete blind-A* on a finite problem).
#   GAVE_UP (TIMEOUT/MEMOUT/INTERNAL_ERROR) must FAIL the test; no-engine must SKIP.
```

Dependency: add `unified-planning[engines]` as an **optional** install documented in the spike
README; the spike test skips with a clear message if the package/engine is unavailable (the spike
must not break the default `pytest tests/unit/` run or CI install).

## Acceptance Criteria

- [ ] `examples/dungeon_master/spikes/floodmark_up/` exists with the modules above.
- [ ] The floodmark `PlotPlan` literal matches design §4 (F1 belief-only effect, Fr reveal, Ff reconciliation).
- [ ] `build_problem` encodes each function as a **goal-required `done_<id>` step** (J2) and chapter ordinal as a **sequencing-fluent chain** (J3); spike README names the chosen engine and confirms it proves unsolvability.
- [ ] **RED test first** (committed separately, `SKIP=pytest`): `test_floodmark_spike.py` asserting:
  - `solve_status(floodmark) in POSITIVE_OUTCOMES` (presumed-dead arc plans);
  - `solve_status(early_reveal_variant) in PROVEN_UNSOLVABLE` (Arnulf onstage Ch3 is **proven** unrepresentable by a complete blind-A* search — not merely a timeout); see the J1 engine-reality amendment (`UNSOLVABLE_PROVEN` is unreachable with the installed engines; complete-search `UNSOLVABLE_INCOMPLETELY` is the proof);
  - `validate_plan(world_revival_variant)` yields a `lifecycle_violation` flaw (world-truth `alive` after death).
- [ ] `TIMEOUT`/`MEMOUT`/`INTERNAL_ERROR` **fail** the test (J1); only `UPNoSuitableEngineAvailableError` → **skip** with a clear reason.
- [ ] GREEN: `schema.py`/`up_model.py`/`validate.py` make the test pass.
- [ ] `run.py` prints the solved chapter order for the floodmark plan (the realizer's input skeleton).
- [ ] Spike `schema.py` docstring states it is a **throwaway subset**, not the production `api/plot/schema.py` contract, and is not imported by v2 (J4).
- [ ] The test skips gracefully (clear reason) when `unified-planning`/engine is not installed; it does **not** fail the default suite or the CI dependency audit.
- [ ] Example-test conventions: NO `@pytest.mark.req`, NO capability YAML (FR-474 J3).
- [ ] Changelog fragment in `changelog/unreleased/` (`type: feat`, `scope: examples`, no `req:`).
- [ ] Diary reflection entry in `docs/diary/`.

## Alternatives Considered

- **Sabre (Java, GPL-3.0) as the oracle.** Belief-native and benchmarked, but Java — a
  cross-language subprocess dependency in a Python codebase. Kept as an *optional* M0 cross-check
  (FR follow-up), not the primary spike. (Plan §9a.)
- **Hand-written POCL solver from scratch.** Rejected — `unified-planning` already provides causal
  coherence / reachability / threat resolution; re-implementing them is wasted work. We hand-write
  only the narrative invariants (lifecycle, belief grounding, affect closure) the planner can't enforce.
- **pyperplan.** STRIPS-only, no action costs, GPL-3.0, teaching tool — too limited for the
  reachability bound and license-incompatible. (Plan §9a table.)
- **Wire straight into v2.** Rejected for M0 — the spike must falsify the approach in isolation
  before any v2 surface area is committed (design §7 M0 is deliberately standalone).

## Related

- [`design-v3-plot-model-implementation.md`](../examples/dungeon_master/docs/design-v3-plot-model-implementation.md) — M0 row of §7; the validator split in §3.
- [`plan-generative-plot-model.md`](../examples/dungeon_master/docs/plan-generative-plot-model.md) — §9a prior art, §10 Q1 (this FR resolves the spike question).
- FR-556 (typed `StoryDoc`), FR-557 (turn-engine extraction / realizer), FR-558 (gate-on-write) — the v2 contract program M1+ depends on.

## Judgement (2026-06-21)

**Verdict: APPROVE WITH CONDITIONS.** The scope is right, minimal, and correctly standalone: a
falsification spike that commits no v2 surface area is exactly what §10 Q1 needs before the v3
model FR spends real code. The library choice is sound — `unified-planning` is Apache-2.0, pip,
maintained (v1.3.0), and `OneshotPlanner.solve()` genuinely discharges checks 1/5/6. The
belief-as-fluent reification is the correct trick and is the cheapest possible proof of the
belief lane. **But the spike's entire epistemic value is a *proven negative* ("early reveal is
unspellable"), and the proposed mechanics would let that negative pass for the wrong reason.**
Three conditions; two block enforce because they are the difference between a proof and theatre.

**J1 — BLOCKING. A falsification spike must distinguish *proven-unsolvable* from *gave-up*.**
The `is_solvable` sketch returns `status in POSITIVE_OUTCOMES` — so it collapses **four** distinct
outcomes into its `False` branch: `UNSOLVABLE_PROVEN` (the result we want), `TIMEOUT`, `MEMOUT`,
and the `OneshotPlanner` raise when **no engine supports the problem_kind**. Only the first proves
the early-reveal class is unrepresentable; the other three prove only that the planner ran out of
road or was never there. As written, the `is_solvable(early_reveal) is False` assertion could pass
on a 1-second timeout while proving *nothing* — the `plausible_wrong_answer` trap, and fatal here
because the negative IS the deliverable. Pin it: the negative assertion must check
`result.status == PlanGenerationResultStatus.UNSOLVABLE_PROVEN` explicitly; `TIMEOUT`/`MEMOUT`/
`INTERNAL_ERROR` must **fail** the test (the encoding is wrong or too big), and "no engine" must
**skip** (environment), never silently satisfy the negative. The positive assertion stays
`in POSITIVE_OUTCOMES`. Two predicates, not one.

> **J1 engine-reality amendment (2026-06-21, approved during enforce).** Enforcement de-risking
> proved that NO pip-installable UP engine on the target machine emits `UNSOLVABLE_PROVEN`:
> `fast-downward`/`-opt`/`symk`/`symk-opt` all return `UNSOLVABLE_INCOMPLETELY` for finitely
> unsolvable problems (FD exits 12 even when its own log says `Completely explored state space --
> no solution!`), and `aries` hangs on untimed classical problems. The literal
> `status == UNSOLVABLE_PROVEN` check is therefore empirically unsatisfiable. The approved
> amendment keeps J1's discriminating intent intact: with a **complete** engine+config pinned
> (`fast-downward` `astar(blind())`) on the **finite** chapter-chain encoding, the proven-negative
> predicate becomes `status in (UNSOLVABLE_PROVEN, UNSOLVABLE_INCOMPLETELY)`; `TIMEOUT`/`MEMOUT`/
> `INTERNAL_ERROR` still **fail** (distinct statuses, never produced by exhaustion), and no-engine
> still **skips**. This corrects only the enum value the engines actually use for a complete
> proof — it does NOT relax the proof-vs-give-up distinction the Judge guarded.

**J2 — BLOCKING (cheap). Functions must be mandatory goal-required steps, or the negative
inverts.** A classical planner does not *fail* when an action has an unsatisfiable precondition —
it simply **does not use that action**. So if the early-reveal beat is modelled as an ordinary
optional action, the early_reveal problem is *trivially solvable* (the planner just skips the bad
beat) and `is_solvable(early_reveal)` returns **True** — the exact opposite of the asserted
result. The negative only holds if **every authored function must fire**: each `Function`
compiles to an action with a unique `done_<id>` effect, and `G` (the goal) conjoins every
`done_<id>`. Then an unschedulable beat makes the *goal* unreachable → `UNSOLVABLE_PROVEN`. The FR
must state this encoding rule in `up_model.build_problem`; without it the spike measures the wrong
thing.

**J3 — non-blocking, but resolve before coding: the engine is not a free parameter, and neither
is chapter-ordinal encoding.** Two coupled facts the docs currently call "parameterized": (a)
proving `UNSOLVABLE_PROVEN` (J1) requires a **complete** planner/mode — a satisficing heuristic
run may return `UNSOLVABLE_INCOMPLETELY` and never prove it; (b) "onstage at Ch3" is a *temporal*
constraint, and STRIPS has no clock — chapter ordinal must be encoded either as a sequencing-fluent
chain (`chapter_1 → chapter_2 …`, actions gated on the marker) for a classical engine, or natively
in a temporal engine (`aries`). Pick **one concrete default now** (recommend: sequencing-fluent
chain + an engine that proves unsolvability) and record it in the spike README; the abstract
"`aries` vs `fast-downward`" choice in the design §8 deferred list is only free *after* this spike
confirms one works.

**J4 — non-blocking. The spike `schema.py` is throwaway, not the production contract.** Say so in
the module docstring. The eventual `api/plot/schema.py` (design §2) is the real typed island; the
spike's subset must not be imported by v2 or treated as the API, or M0 silently becomes an
un-judged production interface (`framework_costume` via the back door).

**Authority granted to enforce once J1 and J2 are folded into the FR text (J3/J4 into the enforce
diff).** Freeze scope to: the standalone `spikes/floodmark_up/` package; the floodmark plan + two
variants (early-reveal, world-revival); `build_problem` with the mandatory-step encoding (J2);
`is_solvable` returning the typed three-way outcome (J1); the hand-written `_check_monotonic_
lifecycle`; `run.py` printing the solved order. **No v2 wiring, no `api/plot/` modules, no LLM
author pass** — those are M1+. Example-exempt (no `@pytest.mark.req`, no capability YAML);
changelog fragment + diary required. The RED commit is the characterization of the proof itself:
the three assertions (positive solvable, negative `UNSOLVABLE_PROVEN`, lifecycle flaw) committed
failing with `SKIP=pytest` before `build_problem` exists.

## Enforcement (2026-06-21)

**Status: Enforced.** The standalone spike lives at
`examples/dungeon_master/spikes/floodmark_up/` (`schema.py`, `up_model.py`, `validate.py`,
`floodmark.py`, `run.py`, `README.md`). All three acceptance assertions pass:

- `solve_status(floodmark) in POSITIVE_OUTCOMES` → `SOLVED_SATISFICING`;
- `solve_status(early_reveal_variant) in PROVEN_UNSOLVABLE` (complete blind-A* exhaustion);
- `validate_plan(world_revival_variant)` → one `lifecycle_violation`.

`run.py` prints the solved order: `F1` (ch1 villainy) → `Fr` (ch6 reveal) → `Ff` (ch6
reconciliation).

**J1 resolved by amendment (see the engine-reality amendment above).** De-risking proved
`UNSOLVABLE_PROVEN` is unreachable with the installed engines (FD/symk exit 12 →
`UNSOLVABLE_INCOMPLETELY` even on a complete proof; aries hangs). Escalated to the requester and
the amendment was approved before any spike code was written: `PROVEN_UNSOLVABLE =
(UNSOLVABLE_PROVEN, UNSOLVABLE_INCOMPLETELY)` for a complete config on a finite problem;
`GAVE_UP = (TIMEOUT, MEMOUT, INTERNAL_ERROR)` still fails the test; no-engine still skips. The
proof-vs-give-up distinction is preserved; only the enum the engines emit was corrected.

**J2/J3 implemented** in `up_model.build_problem`: each beat compiles to a `done_<id>` effect with
every `done_<id>` conjoined into the goal (mandatory steps); chapter ordinal is a strict
`at_chapter_<n>` sequencing chain whose `advance` actions require every chapter beat done.
**J3 engine of record:** `fast-downward` with `astar(blind())`, recorded in the spike README.
**J4:** `schema.py` docstring states it is a throwaway subset, not the production contract, not
imported by v2.

**Commits (local):** RED `383ddb5a` (characterization, `SKIP=pytest`); GREEN follows with the
package, changelog fragment, and diary entry. Example-exempt (no `@pytest.mark.req`, no capability
YAML). `unified-planning` remains an optional install; the test skips gracefully when absent.
